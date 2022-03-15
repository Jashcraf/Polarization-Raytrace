function [ r ] = MATLAB_BatchRayTrace_Ex22_Performance_Comparison( args )

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
        r = BeginApplication(TheApplication);
        CleanupConnection(TheApplication);
    catch err
        CleanupConnection(TheApplication);
        rethrow(err);
    end
end
end




function [r] = BeginApplication(TheApplication)

    import ZOSAPI.*;

    TheSystem = TheApplication.CreateNewSystem(ZOSAPI.SystemType.Sequential);

    % Add your custom code here...
    
    % opens ZMX sample file
    TheSystem.LoadFile(System.String.Concat(TheApplication.SamplesDir, '\Sequential\Objectives\Double Gauss 28 degree field.zmx'), false);
    
    % Set up Batch Ray Trace
    % creates batch raytrace in API
	raytrace = TheSystem.Tools.OpenBatchRayTrace();
    nsur = TheSystem.LDE.NumberOfSurfaces - 1;
    max_rays = 101;
    total_rays_in_both_axes = (max_rays) * (max_rays);
    
    % creates batch raytrace in API
    RayTraceData = raytrace.CreateNormUnpol(total_rays_in_both_axes, ZOSAPI.Tools.RayTrace.RaysType.Real, nsur);
    
	% offloads processing to C# dll
    NET.addAssembly(strcat(pwd, '\RayTrace.dll'));
    import BatchRayTrace.*;
    
    tic();
    color_ary = {'blue', 'green', 'red', 'gold', 'pink', 'cyan', 'purple', 'teal'};
    close all;
    set(gcf, 'OuterPosition',[0, 250, 1500, 500]);
    
    % loops through all fields and wavelengths
    for field = 1:3
        subplot(1, 3, double(field));
        hold on;
        for wave = 1:3
            % Attach the helper class to the ray database reader
            dataReader = ReadNormUnpolData(raytrace, RayTraceData);

            dataReader.ClearData();
            
            x_field = 0;
            switch(field)
                case 1
                    y_field = 0;
                case 2
                    y_field = 0.7;
                case 3
                    y_field = 1;
            end
            
            % creates array of field (Hx/Hy) and pupil (Px/Py) coordinates
            Hx = ones(total_rays_in_both_axes, 1).*x_field;
            Hy = ones(total_rays_in_both_axes, 1).*y_field;

            % dithered ray pattern on the unit circle
            [Px, Py] = rand_circle(total_rays_in_both_axes);

            % converts from matlab arrays to .NET arrays 
            HxNet = NET.convertArray(Hx, 'System.Double');
            HyNet = NET.convertArray(Hy, 'System.Double');
            PxNet = NET.convertArray(Px, 'System.Double');
            PyNet = NET.convertArray(Py, 'System.Double');
            
            % add rays to batch ray trace
            dataReader.AddRay(wave, HxNet, HyNet, PxNet, PyNet, ZOSAPI.Tools.RayTrace.OPDMode.None);

            % Configure the maximum number of segments to read at one time.
            % Note that this is a tradeoff between speed and memory usage
            rayData = dataReader.InitializeOutput(max_rays);
            isFinished = false;
            totalRaysRead = 0;
            maxRays = 0;

            while ~isFinished
                % fill the next block of data
                readSegments = dataReader.ReadNextBlock(rayData);

                if readSegments == 0
                    isFinished = true;
                else
                    % Note - MATLAB arrays are 1-based, however .NET arrays are 0-based, so we have to be carefull...
                    maxRays = max(rayData.rayNumber.double);
                    xData = rayData.X.double;
                    yData = rayData.Y.double;
                end

                if totalRaysRead >= maxRays
                    isFinished = true;
                end    
            end

            % plots ray on current subplot
            if maxRays > 0
                x = xData(1:maxRays);
                y = yData(1:maxRays);

                plot(x, y, '.', 'MarkerSize', 4, 'color', char(color_ary(wave)));    
                axis square;
            end
        end
        daspect([1 1 1]);
    end
    raytrace.Close();
    
    toc();
    disp(['Total Rays: ', num2str(maxRays)]);
    r = [];

end

function [X,Y] = rand_circle(N,x,y,r)
    % from user 'Loginatorist' on www.mathworks.com
    % Generates N random points in a circle.
    % RAND_CIRC(N) generates N random points in the unit circle at (0,0).
    % RAND_CIRC(N,x,y,r) generates N random points in a circle with radius r 
    % and center at (x,y).
    if nargin<2
       x = 0;
       y = 0;
       r = 1;
    end
    Ns = round(1.28*N + 2.5*sqrt(N) + 100); % 4/pi = 1.2732
    X = rand(Ns,1)*(2*r) - r;
    Y = rand(Ns,1)*(2*r) - r;
    I = find(sqrt(X.^2 + Y.^2)<=r);
    X = X(I(1:N)) + x;
    Y = Y(I(1:N)) + y;
end


function app = InitConnection()

import System.Reflection.*;

% Find the installed version of OpticStudio.
zemaxData = winqueryreg('HKEY_CURRENT_USER', 'Software\Zemax', 'ZemaxRoot');
NetHelper = strcat(zemaxData, '\ZOS-API\Libraries\ZOSAPI_NetHelper.dll');
% Note -- uncomment the following line to use a custom NetHelper path
% NetHelper = '@{NETHELP}';
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


