from subprocess import NORMAL_PRIORITY_CLASS
import numpy as np
import zosapi
from System import Enum, Int32, Double, Array
import clr, os

wave = 1
Hx = 0
Hy = 0
Px = np.linspace(-1,1,nrays)
Py = np.linspace(-1,1,nrays)
Px,Py = np.meshgrid(Px,Py)

dll = os.path.join(os.path.dirname(os.path.realpath(__file__)),r'Raytrace.dll')
clr.AddReference(dll)

import BatchRayTrace

zos = zosapi.App()
TheSystem = zos.TheSystem
ZOSAPI = zos.ZOSAPI

TheSystem.LoadFile(filename,False)

if TheSystem.LDE.NumberOfSurfaces < 4:
    print('did not load file')
    exit()

# Run a Raytrace
max_rays = nrays 
total_rays = nrays**2

# Run Batch Raytrace
tool = TheSystem.Tools.OpenBatchRayTrace()
normUnpol = tool.CreateNormUnpol(max_rays,ZOSAPI.Tools.RayTrace.RaysType.Real,TheSystem.LDE.NumberOfSurfaces-1)

# pass raytracer to dll
reader = BatchRayTrace.ReadNormUnpolData(tool,normUnpol)
reader.ClearData()

# Initialize Output
# maxseg is the number of indices in the output array, which is maxseg * maxseg
# Check that this is the correct syntax
rays = reader.InitializeOutput(maxseg)
reader.AddRay(wave,
              Hx,
              Hy,
              Px,
              Py,
              Enum.Parse(ZOSAPI.Tools.RayTrace.OPDMode,'None'))

isfinished = False
while not isfinished:
    segments = reader.ReadNextBlock(rays)
    if segments == 0:
        isfinished = True

print(list(rays.X))
print(list(rays.Y))

tool.close()

