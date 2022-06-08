import zosapi
from System import Enum, Int32, Double, Array
import numpy as np

def ZemaxTraceToSurface(nrays,pth,surf):
    """Traces to a single surface in Zemax OpticStudio Standalone API.

    Parameters
    ----------
    nrays : int
        how many rays across the pupil that are traced
    pth : str
        full file path from C: to your lens file
    surf : int
        surface to trace to in ZOS lens file

    Returns
    -------
    _type_
        _description_
    """
    # Some User Imports
    nrays = 11
    parent = 'C:/Users/jaren/Desktop/Polarization-Raytrace/'
    filename = parent+'Hubble_Test.zmx'
    wave = 1
    Px = np.linspace(-1,1,nrays)
    Py = np.linspace(-1,1,nrays)
    Hx = np.zeros(Px.shape)
    Hy = np.zeros(Px.shape)
    # Px,Py = np.meshgrid(Px,Py)

    # add the raytrace.dll from the current directory
    import clr, os
    dll = os.path.join(os.path.dirname(os.path.realpath(__file__)), r'RayTrace.dll')
    # dll = 'RayTrace.dll'
    # dll = r'C:\Users\Michael\Documents\Temp\KA-01651-Matlab-DLL\12114-Matlab DLL\RayTrace.dll';

    clr.AddReference(dll)

    # import the raytrace namespace
    import BatchRayTrace

    # load the double gauss
    zos = zosapi.App()
    TheSystem = zos.TheSystem
    ZOSAPI = zos.ZOSAPI
    TheSystem.LoadFile(filename, False)

    # check to make sure the file was loaded
    if TheSystem.LDE.NumberOfSurfaces < 4:
        print('did not load the file properly')
        exit()

    # run a sequential ray trace
    maxrays = nrays;        # let's trace the 4 marginal rays
    tool = TheSystem.Tools.OpenBatchRayTrace()
    normUnpol = tool.CreateNormUnpol(maxrays, ZOSAPI.Tools.RayTrace.RaysType.Real, TheSystem.LDE.NumberOfSurfaces - 1)

    # pass raytracer to dll
    reader = BatchRayTrace.ReadNormUnpolData(tool, normUnpol)
    reader.ClearData()

    # initialize the output (the number of indices in the output array is maxseg*maxseg
    maxseg = 4
    rays = reader.InitializeOutput(maxseg)

    # add the 4 full field marginal rays
    import numpy as np
    reader.AddRay(wave, 
        Hx, 
        Hy, 
        Px, 
        Py, Enum.Parse(ZOSAPI.Tools.RayTrace.OPDMode, 'None'))

    # read the segments (array length is maxsegs * max segs)
    isfinished = False
    while not isfinished:
        segments = reader.ReadNextBlock(rays)
        if segments == 0:
            isfinished = True

    # always close your tools
    tool.Close()

    # return the rays
    return rays.X,rays.Y,rays.Z,rays.L,rays.M,rays.N,rays.l2,rays.m2,rays.n2