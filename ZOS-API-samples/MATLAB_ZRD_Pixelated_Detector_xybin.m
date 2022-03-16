function [ r ] = MATLAB_ZRD_Pixelated_Detector_xybin( args )

if ~exist('args', 'var')
    args = [];
end

% Initialize the OpticStudio connection
TheApplication = InitConnection();
if isempty(TheApplication)
    % failed to initialize a connection
    r = [];
else
    try
        r = BeginApplication(TheApplication, args);
        CleanupConnection(TheApplication);
    catch err
        CleanupConnection(TheApplication);
        rethrow(err);
    end
end
end



function [r] = BeginApplication(TheApplication, args)

    import ZOSAPI.*;

    TheSystem = TheApplication.CreateNewSystem(ZOSAPI.SystemType.NonSequential);

    % Add your custom code here...
    
    
    % Create basic system
    o1 = TheSystem.NCE.GetObjectAt(1);
    o2 = TheSystem.NCE.InsertNewObjectAt(2);
    o3 = TheSystem.NCE.InsertNewObjectAt(3);
    
    o1.ChangeType(o1.GetObjectTypeSettings(ZOSAPI.Editors.NCE.ObjectType.SourceRectangle));
    o2_settings = o2.GetObjectTypeSettings(ZOSAPI.Editors.NCE.ObjectType.Slide);
    o2_settings.FileName1 = 'LETTERF.BMP';
    o2.ChangeType(o2_settings);
    o3.ChangeType(o3.GetObjectTypeSettings(ZOSAPI.Editors.NCE.ObjectType.DetectorRectangle));
    
    o1.ZPosition = -1;
    o1.ObjectData.NumberOfAnalysisRays = 1e4;
    o1.ObjectData.XHalfWidth = 5;
    o1.ObjectData.YHalfWidth = 5;
    
    o2.ObjectData.XFullWidth = 10;
    
    o3.ZPosition = 0.06;
    o3.ObjectData.XHalfWidth = 5;
    o3.ObjectData.YHalfWidth = 5;
    o3.ObjectData.NumberXPixels = 250;
    o3.ObjectData.NumberYPixels = 250;
    
    % need to save first to get local path for ZRD file
    % creates a new API directory
    apiPath = System.String.Concat(TheApplication.SamplesDir, '\API\Matlab');
    if (exist(char(apiPath)) == 0) mkdir(char(apiPath)); end;
    TheSystem.SaveAs(System.String.Concat(TheApplication.SamplesDir, '\API\Matlab\ZRD_PixelatedDetector_xybin.zmx'))
    
    zrdFile = 'ZRD_PixelatedDetector_xybin.ZRD';
    
    %{
    TheSystem.LoadFile('c:\temp\nsc.zmx', false);
    
    
    % decreases rays for example to save time
    
    x
    %}
    % Run a ray trace & save ZRD data
    NSCRayTrace = TheSystem.Tools.OpenNSCRayTrace();
    NSCRayTrace.SplitNSCRays = false;
    NSCRayTrace.ScatterNSCRays = true;
    NSCRayTrace.UsePolarization = false;
    NSCRayTrace.IgnoreErrors = true;
    NSCRayTrace.SaveRays = true;
    NSCRayTrace.SaveRaysFile = zrdFile;  % Saves to same directory as lens file
    NSCRayTrace.ClearDetectors(0);
    NSCRayTrace.RunAndWaitForCompletion();
    NSCRayTrace.Close();
    
    
    % runs Ray Database Tool
    % ZOS should only have 1 opened tool at a time 
    if ~isempty(TheSystem.Tools.CurrentTool)
        TheSystem.Tools.CurrentTool.Close();
    end
    zrdReader = TheSystem.Tools.OpenRayDatabaseReader();
    zrdReader.ZRDFile = strcat(fileparts(char(TheSystem.SystemFile)), '\', zrdFile);
    zrdReader.Filter = '';
    zrdReader.RunAndWaitForCompletion();
    zrdResult = zrdReader.GetResults();
    
    % offloads processing to C# dll
    if ~isempty(zrdResult)
        % offloads processing to C# dll 
        NET.addAssembly(strcat(pwd, '\RayTrace.dll'));
        import BatchRayTrace.*;
        
        maxSegmentsToRead = 1e7;
        
        dataReader = ReadZRDData(zrdResult);
        zrdData = dataReader.InitializeOutput(maxSegmentsToRead);
        
        tic();
        
        isFinished = false;
        xpixels = o3.ObjectData.NumberXPixels;
        ypixels = o3.ObjectData.NumberYPixels;
        
        x_width = o3.ObjectData.XHalfWidth * 2 / 10;
        y_width = o3.ObjectData.YHalfWidth * 2 / 10;

        while ~isFinished
            % fill the next block of data
            currentSegments = dataReader.ReadNextBlock(zrdData);
            if currentSegments == 0
                isFinished = true;
            else
                readSegments = currentSegments;
                % Note - MATLAB arrays are 1-based, however .NET arrays are 0-based, so we have to be carefull...
                % retrieve whatever data is needed
                totalRaysRead = int32(zrdData.RayNumber(readSegments-1));
                
                xybin = zrdData.xybin.double;
                intensity = zrdData.Intensity.double;
                hitObject = zrdData.HitObject.double;
                
                
            end

            if totalRaysRead >= maxSegmentsToRead
                isFinished = true;
            end    
        end
        
        
        totalHits = sum(hitObject(1:readSegments) == 0);
        xyIntensity = (xybin(1:readSegments) > 0) .* intensity(1:readSegments);

        % remove non-zero values
        xybin(xybin == 0) = [];
        xyIntensity(xyIntensity == 0) = [];

        det = [xybin; xyIntensity];                

        % bin & sum common pixels
        [G, aa] = findgroups(det(1, :));
        pixels = [aa ; splitapply(@sum, det(2, :), G)];

        % place summed xybin pixels into zero-padded array
        detector = zeros(1, xpixels * ypixels);
        detector(pixels(1, :)) = pixels(2, :);

        final_detector = flipud(rot90(reshape(detector, [xpixels, ypixels])));
        flux_sum = sum(sum(final_detector));
        final_detector = final_detector .* (double(xpixels * ypixels) / (x_width * y_width));

        toc();
        
        disp(['Total Hits: ', num2str(totalHits)]);
        disp(['Total Power:  ', num2str(flux_sum)]);
        disp(['Total Rays:   ', num2str(totalRaysRead)]);
        disp(['Total segs:   ', num2str(readSegments)]);

        imagesc(final_detector);

        axis xy;
        colorbar;
        axis equal tight;
        colormap('jet');
        
        
        
    end
    
    % always close ZOS tools after you're done with them
    zrdReader.Close();
    
    
    

    r = [];

end


function [] = ProcessZRD1(res, maxRays)
    tic();

    % Attach the helper class to the ray database reader
    dataReader = ReadZRDData(res);
    % Configure the maximum number of segments to read at one time.
    % Note that this is a tradeoff between speed and memory usage
    maxSeg = 10000000;
    zrdData = dataReader.InitializeOutput(maxSeg);

    isFinished = false;
    totalSegRead = 0;
    totalRaysRead = 0;
    pow4 = 0.0;
    pow7 = 0.0;

    while ~isFinished
        % fill the next block of data
        readSegments = dataReader.ReadNextBlock(zrdData);
        if readSegments == 0
            isFinished = true;
        else
            totalSegRead = totalSegRead + readSegments;
            % Note - MATLAB arrays are 1-based, however .NET arrays are 0-based, so we have to be carefull...
            totalRaysRead = int32(zrdData.RayNumber(readSegments-1));

            % retrieve whatever data is needed
            intensityData = transpose(zrdData.Intensity.double);
            hitObjectData = transpose(zrdData.HitObject.double);
            
            %xData = zrdData.X.double; 
            pow4 = pow4 + sum((hitObjectData(1:readSegments) == 4) .* intensityData(1:readSegments));
            pow7 = pow7 + sum((hitObjectData(1:readSegments) == 7) .* intensityData(1:readSegments));
        end

        if totalRaysRead >= maxRays
            isFinished = true;
        end    
    end
    toc();
    
    disp(['Rays read: ', num2str(totalRaysRead)]);
    disp(['Segments read: ', num2str(totalSegRead)]);
    disp(['Power on Detector 4: ', num2str(pow4)]);
    disp(['Power on Detector 7: ', num2str(pow7)]);

end

function app = InitConnection()

import System.Reflection.*;

% Find the installed version of OpticStudio.
zemaxData = winqueryreg('HKEY_CURRENT_USER', 'Software\Zemax', 'ZemaxRoot');
NetHelper = strcat(zemaxData, '\ZOS-API\Libraries\ZOSAPI_NetHelper.dll');
% Note -- uncomment the following line to use a custom NetHelper path
% NetHelper = 'C:\Users\Documents\Zemax\ZOS-API\Libraries\ZOSAPI_NetHelper.dll';
NET.addAssembly(NetHelper);

success = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize();
% Note -- uncomment the following line to use a custom initialization path
% success = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize('C:\Program Files\Zemax OpticStudio\');
if success == 1
    LogMessage(strcat('Found OpticStudio at: ', char(ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory())));
else
    app = [];
    return;
end

% Now load the ZOS-API assemblies
NET.addAssembly(AssemblyName('ZOSAPI_Interfaces'));
NET.addAssembly(AssemblyName('ZOSAPI'));

% Create the initial connection class
TheConnection = ZOSAPI.ZOSAPI_Connection();

% Attempt to create a Standalone connection

% NOTE - if this fails with a message like 'Unable to load one or more of
% the requested types', it is usually caused by try to connect to a 32-bit
% version of OpticStudio from a 64-bit version of MATLAB (or vice-versa).
% This is an issue with how MATLAB interfaces with .NET, and the only
% current workaround is to use 32- or 64-bit versions of both applications.
app = TheConnection.CreateNewApplication();
if isempty(app)
   HandleError('An unknown connection error occurred!');
end
if ~app.IsValidLicenseForAPI
    HandleError('License check failed!');
    app = [];
end

end

function LogMessage(msg)
disp(msg);
end

function HandleError(error)
ME = MXException(error);
throw(ME);
end

function  CleanupConnection(TheApplication)
% Note - this will close down the connection.

% If you want to keep the application open, you should skip this step
% and store the instance somewhere instead.
TheApplication.CloseApplication();
end


