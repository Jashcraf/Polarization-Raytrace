import zosapi
from System import Enum, Int32, Double, Array
import numpy as np

def ZOSRayData(nrays,pth,surf,n1,n2,mode='reflection',show_rays=False):

    xData,yData,zData,lData,mData,nData,l2Data,m2Data,n2Data = ZemaxTraceToSurface(nrays,pth,surf)

    # Sometimes nan values are returned, can we just filter them?
    # xData = xData[yData != 0]
    # zData = zData[yData != 0] # using the y data is intentional, apparently the z data 
    #                           # is less prone to producing zero values

    # lData = lData[yData != 0]
    # nData = nData[yData != 0]
    # mData = mData[yData != 0]
    
    # l2Data = l2Data[yData != 0]
    # n2Data = n2Data[yData != 0]
    # m2Data = m2Data[yData != 0]
    # yData = yData[yData != 0]

    # Which one is the most restrictive?
    # print(xData.shape)
    # print(yData.shape)
    # print(zData.shape)
    # print(lData.shape)
    # print(mData.shape)
    # print(nData.shape)
    # print(l2Data.shape)
    # print(m2Data.shape)
    # print(n2Data.shape)

    if show_rays == True:
        import matplotlib.pyplot as plt
        plt.figure(figsize=[15,5])
        plt.subplot(131)
        plt.xlabel('X Data')
        plt.ylabel('y Data')
        plt.scatter(xData,yData)
        plt.subplot(132)
        plt.xlabel('L Data')
        plt.ylabel('M Data')
        plt.scatter(lData,mData)
        plt.subplot(133)
        plt.xlabel('L2 Data')
        plt.ylabel('M2 Data')
        plt.scatter(l2Data,m2Data)
        plt.show()

     # normal vector
    norm = -np.array([l2Data,m2Data,n2Data])
    norm /= np.sqrt(l2Data**2 + m2Data**2 + n2Data**2)
    # print(norm)
    total_rays_in_both_axes = xData.shape[0]

    # convert to angles of incidence
    # calculates angle of exitance from direction cosine
    # the LMN direction cosines are for AFTER refraction
    # need to calculate via Snell's Law the angle of incidence
    numerator = (lData*l2Data + mData*m2Data + nData*n2Data)
    denominator = ((lData**2 + mData**2 + nData**2)**0.5)*(l2Data**2 + m2Data**2 + n2Data**2)**0.5
    aoe_data = np.arccos(numerator/denominator)
    aoe = aoe_data - (aoe_data[0:total_rays_in_both_axes] > np.pi/2) * np.pi
    aoe = np.abs(aoe)
    aoi = np.arcsin(n2/n1 * np.sin(aoe))

    # Compute kin with Snell's Law: https://en.wikipedia.org/wiki/Snell%27s_law#Vector_form
    kout = np.array([lData,mData,nData])
    kout /= np.sqrt(lData**2 + mData**2 + nData**2)

    if mode == 'transmission':
        kin = np.cos(np.arcsin(n2*np.sin(np.arccos(kout))/n1))
    elif mode == 'reflection':
        kin = kout - 2*np.cos(aoi)*norm

    return aoi,xData,yData,kin,kout,norm


def ZemaxTraceToSurface(nrays,pth,surf):
    import numpy as np
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
    filename = pth
    wave = 1
    x = np.linspace(-1,1,nrays)
    y = np.linspace(-1,1,nrays)
    x,y = np.meshgrid(x,y)
    X = np.ravel(x)
    Y = np.ravel(y)
    Px = np.ravel(x)
    Py = np.ravel(y)
    # Px = Px[X**2 + Y**2 <= 1]
    # Py = Py[X**2 + Y**2 <= 1]

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

    if surf > TheSystem.LDE.NumberOfSurfaces:
        print('surf is greater than number of surfaces, setting to last surface')
        surf = TheSystem.LDE.NumberOfSurfaces

    # run a sequential ray trace
    maxrays = Px.shape[0];        # let's trace the 4 marginal rays
    tool = TheSystem.Tools.OpenBatchRayTrace()
    normUnpol = tool.CreateNormUnpol(maxrays, ZOSAPI.Tools.RayTrace.RaysType.Real, surf)

    # pass raytracer to dll
    reader = BatchRayTrace.ReadNormUnpolData(tool, normUnpol)
    reader.ClearData()

    # initialize the output (the number of indices in the output array is maxseg*maxseg
    maxseg = nrays
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

    # convert to numpy arrays
    xData = np.array(list(rays.X))
    yData = np.array(list(rays.Y))
    zData = np.array(list(rays.Z))

    lData = np.array(list(rays.L))
    mData = np.array(list(rays.M))
    nData = np.array(list(rays.N))

    l2Data = np.array(list(rays.l2))
    m2Data = np.array(list(rays.m2))
    n2Data = np.array(list(rays.n2))

    # always close your tools
    tool.Close()

    # return the rays
    return xData,yData,zData,lData,mData,nData,l2Data,m2Data,n2Data