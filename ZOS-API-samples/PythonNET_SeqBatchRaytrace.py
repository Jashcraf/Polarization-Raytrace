import clr, os, winreg, ctypes, sys
import numpy as np
from System.Runtime.InteropServices import GCHandle, GCHandleType


class PythonStandaloneApplication(object):
    class LicenseException(Exception):
        pass
    class ConnectionException(Exception):
        pass
    class InitializationException(Exception):
        pass
    class SystemNotPresentException(Exception):
        pass

    def __init__(self, path=None):
        # determine location of ZOSAPI_NetHelper.dll & add as reference
        aKey = winreg.OpenKey(winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER), r"Software\Zemax", 0, winreg.KEY_READ)
        zemaxData = winreg.QueryValueEx(aKey, 'ZemaxRoot')
        NetHelper = os.path.join(os.sep, zemaxData[0], r'ZOS-API\Libraries\ZOSAPI_NetHelper.dll')
        winreg.CloseKey(aKey)
        clr.AddReference(NetHelper)
        import ZOSAPI_NetHelper

        # Find the installed version of OpticStudio
        #if len(path) == 0:
        if path is None:
            isInitialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize()
        else:
            # Note -- uncomment the following line to use a custom initialization path
            isInitialized = ZOSAPI_NetHelper.ZOSAPI_Initializer.Initialize(path)

        # determine the ZOS root directory
        if isInitialized:
            dir = ZOSAPI_NetHelper.ZOSAPI_Initializer.GetZemaxDirectory()
        else:
            raise PythonStandaloneApplication.InitializationException("Unable to locate Zemax OpticStudio.  Try using a hard-coded path.")

        # add ZOS-API referencecs
        clr.AddReference(os.path.join(os.sep, dir, "ZOSAPI.dll"))
        print(os.sep)
        clr.AddReference(os.path.join(os.sep, dir, "ZOSAPI_Interfaces.dll"))
        import ZOSAPI

        # create a reference to the API namespace
        self.ZOSAPI = ZOSAPI

        # create a reference to the API namespace
        self.ZOSAPI = ZOSAPI

        # Create the initial connection class
        self.TheConnection = ZOSAPI.ZOSAPI_Connection()

        if self.TheConnection is None:
            raise PythonStandaloneApplication.ConnectionException("Unable to initialize .NET connection to ZOSAPI")

        self.TheApplication = self.TheConnection.CreateNewApplication()
        if self.TheApplication is None:
            raise PythonStandaloneApplication.InitializationException("Unable to acquire ZOSAPI application")

        if self.TheApplication.IsValidLicenseForAPI == False:
            raise PythonStandaloneApplication.LicenseException("License is not valid for ZOSAPI use")

        self.TheSystem = self.TheApplication.PrimarySystem
        if self.TheSystem is None:
            raise PythonStandaloneApplication.SystemNotPresentException("Unable to acquire Primary system")

    def __del__(self):
        if self.TheApplication is not None:
            self.TheApplication.CloseApplication()
            self.TheApplication = None

        self.TheConnection = None

    def OpenFile(self, filepath, saveIfNeeded):
        if self.TheSystem is None:
            raise PythonStandaloneApplication10.SystemNotPresentException("Unable to acquire Primary system")
        self.TheSystem.LoadFile(filepath, saveIfNeeded)

    def CloseFile(self, save):
        if self.TheSystem is None:
            raise PythonStandaloneApplication10.SystemNotPresentException("Unable to acquire Primary system")
        self.TheSystem.Close(save)

    def SamplesDir(self):
        if self.TheApplication is None:
            raise PythonStandaloneApplication10.InitializationException("Unable to acquire ZOSAPI application")

        return self.TheApplication.SamplesDir

    def ExampleConstants(self):
        if self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusType.PremiumEdition:
            return "Premium"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusTypeProfessionalEdition:
            return "Professional"
        elif self.TheApplication.LicenseStatus == self.ZOSAPI.LicenseStatusTypeStandardEdition:
            return "Standard"
        else:
            return "Invalid"

    def DoubleToNumpy(self, data):
        if 'numpy' not in sys.modules:
            print('You have not imported numpy into this file')
            return False
        else:
            src_hndl = GCHandle.Alloc(data, GCHandleType.Pinned)
            try:
                src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()
                cbuf = (ctypes.c_double*len(data)).from_address(src_ptr)
                npData = np.frombuffer(cbuf, dtype=np.float64)
            finally:
                if src_hndl.IsAllocated: src_hndl.Free()
            return npData

    def LongToNumpy(self, data):
        if 'numpy' not in sys.modules:
            print('You have not imported numpy into this file')
            return False
        else:
            src_hndl = GCHandle.Alloc(data, GCHandleType.Pinned)
            try:
                src_ptr = src_hndl.AddrOfPinnedObject().ToInt64()
                cbuf = (ctypes.c_longlong*len(data)).from_address(src_ptr)
                npData = np.frombuffer(cbuf, dtype=np.longlong)
            finally:
                if src_hndl.IsAllocated: src_hndl.Free()
            return npData


if __name__ == '__main__':
    zos = PythonStandaloneApplication()

    # load local variables
    ZOSAPI = zos.ZOSAPI
    TheApplication = zos.TheApplication
    TheSystem = zos.TheSystem

    # DLLs and namespaces
    clr.AddReference(os.path.join(os.sep, os.path.dirname(os.path.realpath(__file__)), r'RayTrace.dll'))
    import BatchRayTrace
    import ZOSAPI.Tools.RayTrace
    from ZOSAPI import *

    # load sample fly's eye example
    #zmxFile = os.path.join(os.sep, TheApplication.SamplesDir, r"Non-sequential\Miscellaneous\Digital_projector_flys_eye_homogenizer.zmx")
    zmxFile = os.path.join(os.sep, TheApplication.SamplesDir, r"\Sequential\Objectives\Double Gauss 28 degree field.zmx")
    TheSystem.LoadFile(zmxFile, False)

    raytrace = TheSystem.Tools.OpenBatchRayTrace()
    nsur = TheSystem.LDE.NumberOfSurfaces - 1
    max_rays = 101
    total_rays_in_both_axes = (max_rays) * (max_rays)

    # % creates batch raytrace in API
    # % Performs a batch unpolarized ray trace, using normalized pupil coordiantes; this is similar to the DDE ray trace command, mode 0.
    RayTraceData = raytrace.CreateNormUnpol(total_rays_in_both_axes, ZOSAPI.Tools.RayTrace.RaysType.Real, nsur)
    
    NET.addAssembly(pwd+'\RayTrace.dll'); #% Where does NET come from?
    import BatchRayTrace
    wave = 1
    dataReader = ReadNormUnpolData(raytrace, RayTraceData)
    dataReader.ClearData()
    x_field = 0
    y_field = 0

    Hx = np.ones(total_rays_in_both_axes, 1)*x_field
    Hy = np.ones(total_rays_in_both_axes, 1)*y_field

    px = np.linspace(-1,1,max_rays)
    px,py = np.meshgrid(px,px)

    Px = np.ravel(px)#np.reshape(bsxfun(@times, linspace(1, 1, max_rays)', linspace(-1, 1, max_rays)), [max_rays^2, 1]);
    Py = np.ravel(py)#np.reshape(bsxfun(@times, linspace(1, -1, max_rays)', linspace(1, 1, max_rays)), [max_rays^2, 1]);

    # Px = Pxi1:total_rays_in_both_axes) .* (sqrt((Pxi(1:total_rays_in_both_axes).^2) + Pyi(1:total_rays_in_both_axes).^2) <= 1);
    # Py = Pyi(1:total_rays_in_both_axes) .* (sqrt((Pxi(1:total_rays_in_both_axes).^2) + Pyi(1:total_rays_in_both_axes).^2) <= 1);

    # converts from matlab arrays to .NET arrays
    HxNet = NET.convertArray(Hx, 'System.Double')
    HyNet = NET.convertArray(Hy, 'System.Double')
    PxNet = NET.convertArray(Px, 'System.Double')
    PyNet = NET.convertArray(Py, 'System.Double')
    dataReader.AddRay(wave, HxNet, HyNet, PxNet, PyNet, ZOSAPI.Tools.RayTrace.OPDMode)
    rayData = dataReader.InitializeOutput(max_rays)
    isFinished = False
    totalRaysRead = 0
    maxRays = 0

    while isFinished == False:

        readSegments = dataReader.ReadNextBlock(rayData);

        if readSegments == 0:
            isFinished = True

        else:

            maxRays = max(rayData.rayNumber.double)
            xData = rayData.X.double
            yData = rayData.Y.double

        if totalRaysRead >= maxRays:
            isFinished = True

        if maxRays > 0:
            x = xData[0:maxRays]
            y = yData[0:maxRays]

    raytrace.close()




    

    # need to have another buffer-to-numpy conversion for the 'long' arrays being passed back from the DLL
    # the following is the output structure from the ZRDOutput class
    #   long[] RayNumber
    #   long[] Waveincrementer
    #   long[] SegmentNumber
    #   double[] WlUM

    #   long[] Level
    #   long[] Parent
    #   long[] HitObject
    #   long[] HitFace
    #   long[] InsideOf
    #   long[] Status
    #   long[] xybin
    #   long[] lmbin
    #   double[] X
    #   double[] Y
    #   double[] Z
    #   double[] L
    #   double[] M
    #   double[] N
    #   double[] Exr
    #   double[] Exi
    #   double[] Eyr
    #   double[] Eyi
    #   double[] Ezr
    #   double[] Ezi
    #   double[] Intensity
    #   double[] PathLen
    #   double[] xNorm
    #   double[] yNorm
    #   double[] zNorm
    #   double[] index
    #   double[] startingPhase
    #   double[] phaseOf
    #   double[] phaseAt

    while isFinished == False and zrdData is not None:
        readSegments = dataReader.ReadNextBlock(zrdData);
        if readSegments == 0:
            isFinished = True;
        else:
            totalSegRead = totalSegRead + readSegments;
            totalRaysRead = np.max(zos.LongToNumpy(zrdData.RayNumber))

            # retreive whatever data is needed
            intensityData = zos.DoubleToNumpy(zrdData.Intensity)
            hitObjectData = zos.LongToNumpy(zrdData.HitObject);

            pow4 = pow4 + np.sum(np.multiply(hitObjectData[1:readSegments] == 4, intensityData[1:readSegments]))
            pow7 = pow7 + np.sum(np.multiply(hitObjectData[1:readSegments] == 7, intensityData[1:readSegments]))

        if totalRaysRead >= maxSegments:
            isFinished = True


    # cannot close the ZRD tool until all the data is parsed
    zrdReader.Close();

    print('Rays read:         %i' % totalRaysRead);
    print('Segments read:     %i' % totalSegRead);
    print('Power on Det 4:    %i' % pow4);
    print('Power on Det 7:    %i' % pow7);

    # This will clean up the connection to OpticStudio.
    # Note that it closes down the server instance of OpticStudio, so you for maximum performance do not do
    # this until you need to.
    del zos
    zos = None
