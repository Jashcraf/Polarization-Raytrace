function [ r ] = MATLABStandaloneApplication3( args )

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

    TheSystem = TheApplication.PrimarySystem;


    % Primary optical system
    TheSystem=TheApplication.PrimarySystem;

    % Name of the file
    teleFile=('D:\Work\OneDrive\University_Arizona\TMT_polarization\TMT_segmented\TMT_segmented_mirror.zmx')
    TheSystem.LoadFile(teleFile,false);

    % Create ray trace data

    TheAnalyses=TheSystem.Analyses;
    pupil_pos=csvread('D:\Work\OneDrive\University_Arizona\TMT_polarization\TMT_segmented\pupil_positions_40000rays.csv');
    px_array=pupil_pos(:,1);
    py_array=pupil_pos(:,2);
    max_rays=length(px_array)

    newWin=TheAnalyses.New_Analysis(ZOSAPI.Analysis.AnalysisIDM.RayTrace);
    
    newWin_Settings=newWin.GetSettings();
    newWin_Settings.Hx=0;
    newWin_Settings.Hy=0;
    for i=1:max_rays
        newWin_Settings.Px=px_array(i);
        newWin_Settings.Py=py_array(i);
        newWin_Settings.Wavelength.SetWavelengthNumber(1);
        newWin_Settings.Field.UseAllFields();
        newWin_Settings.Type=ZOSAPI.Analysis.Settings.Aberrations.RayTraceType.DirectionCosines;
        newWin.ApplyAndWaitForCompletion();

        %Get and Save the Results

        newWin_Results=newWin.GetResults();
        file_name=strcat('D:\Work\OneDrive\University_Arizona\TMT_polarization\TMT_segmented\Ray_trace_40000rays\ray_',int2str(i),'.txt')
        newWin_Results.GetTextFile(file_name)

    end    


    r = [];

end

function app = InitConnection()

import System.Reflection.*;

% Find the installed version of OpticStudio.
zemaxData = winqueryreg('HKEY_CURRENT_USER', 'Software\Zemax', 'ZemaxRoot');
NetHelper = strcat(zemaxData, '\ZOS-API\Libraries\ZOSAPI_NetHelper.dll');
% Note -- uncomment the following line to use a custom NetHelper path
% NetHelper = 'C:\Users\Ramya\Documents\Zemax\ZOS-API\Libraries\ZOSAPI_NetHelper.dll';
% This is the path to OpticStudio
NET.addAssembly(NetHelper);

success = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize();
% Note -- uncomment the following line to use a custom initialization path
% success = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize('C:\Program Files\OpticStudio\');
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
ME = MException('zosapi:HandleError', error);
throw(ME);
end

function  CleanupConnection(TheApplication)
% Note - this will close down the connection.

% If you want to keep the application open, you should skip this step
% and store the instance somewhere instead.
TheApplication.CloseApplication();
end


