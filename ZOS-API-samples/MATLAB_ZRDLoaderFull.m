function [ r ] = MATLAB_ZRDLoaderFull( args )

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
    
    TheSystem.LoadFile(System.String.Concat(TheApplication.SamplesDir, '\Non-sequential\Miscellaneous\Digital_projector_flys_eye_homogenizer.ZMX'), false);
    
    % decreases rays for example to save time
    TheSystem.SystemData.Units.SourceUnits = ZOSAPI.SystemData.ZemaxSourceUnits.Watts;
    TheSystem.NCE.GetObjectAt(1).ObjectData.NumberOfAnalysisRays = 1e4;
    TheSystem.NCE.GetObjectAt(4).ObjectData.Mirroring = 0;
    TheSystem.NCE.GetObjectAt(7).ObjectData.Polarization = 0;
    TheSystem.NCE.GetObjectAt(7).ObjectData.Mirroring = 0;
    
    zrdFile = 'Digital_projector_flys_eye_homogenizer.ZRD';
    
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

    % 

    ReadZRDFile(TheSystem, System.String.Concat(TheApplication.SamplesDir, '\Non-sequential\Miscellaneous\', zrdFile));
    
    
    TheSystem.SaveAs(System.String.Concat(TheApplication.SamplesDir, '\Non-sequential\Miscellaneous\Digital_projector_flys_eye_homogenizer_ZRDloader.ZMX'));

    r = [];

end

function [] = ReadZRDFile(sys, zrdFile)

    if ~isempty(sys.Tools.CurrentTool)
        sys.Tools.CurrentTool.Close();
    end

    zrdReader = sys.Tools.OpenRayDatabaseReader();
    zrdReader.ZRDFile = zrdFile;
    zrdReader.Filter = '';

    % start processing
    zrdReader.RunAndWaitForCompletion();
    res = zrdReader.GetResults();

    if ~isempty(res)
        ProcessZRD1(res, 10000000);
    end

    zrdReader.Close();

end

function [] = ProcessZRD1(res, maxRays)
    % Use the .NET helper DLL to batch up the rays before processing
    import ZOSAPI.Tools.RayTrace.*;

    % This method assumes the helper dll is in the .m file directory.
    p = mfilename('fullpath');
    [path] = fileparts(p);
    p = strcat(path, '\', 'RayTrace.dll' );
    a = NET.addAssembly(p);
    import BatchRayTrace.*;
    

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


