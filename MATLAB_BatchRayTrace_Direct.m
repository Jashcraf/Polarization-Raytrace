function [ r ] = MATLAB_BatchRayTrace_Direct( args )

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

    TheSystem = TheApplication.CreateNewSystem(ZOSAPI.SystemType.Sequential);

    % Add your custom code here...
    
    % opens ZMX sample file
    TheSystem.LoadFile(System.String.Concat(TheApplication.SamplesDir, '\Sequential\Objectives\Double Gauss 28 degree field.zmx'), false);
    
    % Set up Batch Ray Trace
    % creates batch raytrace in API
	raytrace = TheSystem.Tools.OpenBatchRayTrace();
    startSurface = 0;
    toSurface = 5;
    max_rays = 101;
    total_rays_in_both_axes = (max_rays) * (max_rays);
    
    % creates batch raytrace in API
    % CreateDirectUnpol performs a batch unpolarized ray trace, using direct x/y/z coordiantes; this is similar to the DDE ray trace command, mode 1.
    RayTraceData = raytrace.CreateDirectUnpol(total_rays_in_both_axes, ZOSAPI.Tools.RayTrace.RaysType.Real, startSurface, toSurface);
    
	% offloads processing to C# dll 
    currentFolder = pwd;
    NET.addAssembly(strcat(currentFolder, '\RayTrace.dll'));
    import BatchRayTrace.*;
    
    % Attach the helper class to the ray database reader
    tic();
    close all;
    
    % Call the function ReadDirectUnpolData from dll
    % The syntax is ReadDirectUnpolData(IBatchRayTrace rt, IRayTraceDirectUnpolData rtt)    
    dataReader = ReadDirectUnpolData(raytrace, RayTraceData);
    
    % The variable dataReader can now use all the functions defined in the DLL
    dataReader.ClearData();
    
    [~, ~, EPD, ~, ~, ~, ~, ~] = TheSystem.LDE.GetPupil();
    waveNumber = 2;

    % create arrays for direct XYZ & LMN values
    % dithered ray pattern on the unit circle
    %[X, Y] = rand_circle(total_rays_in_both_axes, 0, 0, EPD/2);
    % for square grid, uncomment the next 2 lines
    Xi = reshape(bsxfun(@times, linspace(EPD/2, EPD/2, max_rays)', linspace(1, -1, max_rays)), [max_rays^2, 1]);
    Yi = reshape(bsxfun(@times, linspace(1, -1, max_rays)', linspace(EPD/2, EPD/2, max_rays)), [max_rays^2, 1]);
    
    % limits XY to unit circle
    X = Xi(1:total_rays_in_both_axes) .* (sqrt((Xi(1:total_rays_in_both_axes).^2) + Yi(1:total_rays_in_both_axes).^2) <= EPD/2);
    Y = Yi(1:total_rays_in_both_axes) .* (sqrt((Xi(1:total_rays_in_both_axes).^2) + Yi(1:total_rays_in_both_axes).^2) <= EPD/2);

    init_Z = 0;
    init_L = 0;
    init_M = 0;
    init_N = 1;

    Z = ones(total_rays_in_both_axes, 1).*init_Z;
    L = ones(total_rays_in_both_axes, 1).*init_L;
    M = ones(total_rays_in_both_axes, 1).*init_M;
    N = ones(total_rays_in_both_axes, 1).*init_N;

    % converts from matlab arrays to .NET arrays 
    XNet = NET.convertArray(X, 'System.Double');
    YNet = NET.convertArray(Y, 'System.Double');
    ZNet = NET.convertArray(Z, 'System.Double');
    LNet = NET.convertArray(L, 'System.Double');
    MNet = NET.convertArray(M, 'System.Double');
    NNet = NET.convertArray(N, 'System.Double');

    % 
    dataReader.AddRay(waveNumber, XNet, YNet, ZNet, LNet, MNet, NNet);

    % Configure the maximum number of segments to read at one time.
    % Note that this is a tradeoff between speed and memory usage
    % The syntax of InitializeOutput(int maxSegments,bool incRayNumber = true,bool incErrorCode = true,bool incVignetteCode = true,bool incXYZ = true,
    %             bool incLMN = true,bool incL2M2N2 = true, bool incOPD = true,bool incIntensity = true)
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
            x = rayData.X.double;
            y = rayData.Y.double;                                  
        end

        if totalRaysRead >= maxRays
            isFinished = true;
        end    
    end
    
    % always close a connection to ZOSAPI.Tools
    raytrace.Close();
    toc();
    
    % get aperture values
    angle = linspace(0, 2*pi, 360);
    
    x1 = cos(angle);
    y1 = sin(angle);
    
    SDIAx = x1 * TheSystem.LDE.GetSurfaceAt(toSurface).SemiDiameter;
    SDIAy = y1 * TheSystem.LDE.GetSurfaceAt(toSurface).SemiDiameter;
    MCSDx = x1 * TheSystem.LDE.GetSurfaceAt(toSurface).MechanicalSemiDiameter;
    MCSDy = y1 * TheSystem.LDE.GetSurfaceAt(toSurface).MechanicalSemiDiameter;
    
    close all;
    set(gcf, 'OuterPosition',[150, 250, 650, 500]);
    
    hold on;
    h = plot(x, y, '.', 'MarkerSize', 2, 'color', 'blue');
    
    set(gca, 'Position', [-.04, .15, .8, .8]);
    
    plot(SDIAx, SDIAy, '-', 'color', 'green');
    plot(MCSDx, MCSDy, '-', 'color', 'red');
    axis square;
    
    h = legend('Beam Footprint', 'Clear Semi-Diameter', 'Mechanical Semi-Diameter');
    title(strcat('Surface',num2str(toSurface)));
    set(h, 'Position', [0.7, 0.9, .25, 0])

    
    xlabel(['X (', char(TheSystem.SystemData.Units.LensUnits) , ')']);
    ylabel(['Y (', char(TheSystem.SystemData.Units.LensUnits) , ')']);
    daspect([1 1 1]);
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


