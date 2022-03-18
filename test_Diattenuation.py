import numpy as np
import polutils as pol
import matplotlib.pyplot as plt

# Compute the diattenuation from Fresnel Coefficients
# Test the PRT Computation
n1 = 1.4358 + 1j*9.4953 # Aluminum
n2 = 1
pth = '/Users/jashcraft/Desktop/prt-data/Webb_Parabola_ray_data.txt'
# aoi,xData,yData,kin,kout,norm
aoi,x,y,kin,kout,norm = pol.ConvertBatchRayData(pth,n1,n2,mode='reflection')
ts,tp = pol.FresnelCoefficients(aoi,n1,n2)
Pmat = np.zeros([3,3,kin.shape[1]],dtype='complex128')
Jmat = np.zeros([3,3,kin.shape[1]],dtype='complex128')
D_svd = []
D_jones = []

for i in range(kin.shape[1]):

    Pstg,Jstg = pol.ConstructPRTMatrix(
        kin[:,i],
        kout[:,i],
        norm[:,i],
        aoi[i],
        n1,
        n2,
        mode='reflection')

    # Compute diattenuation from SVD
    sv = np.linalg.svd(Pstg,compute_uv=False) # returning 3 sv's and all are nonzero
    D_svd.append((np.abs(sv[0])**2 - np.abs(sv[1])**2)/(np.abs(sv[0])**2 + np.abs(sv[1])**2))
    D_jones.append((np.abs(Jstg[0,0])**2 - np.abs(Jstg[1,1])**2)/(np.abs(Jstg[0,0])**2 + np.abs(Jstg[1,1])**2))
    Pmat[:,:,i] = Pstg
    Jmat[:,:,i] = Jstg

D_fresnel = (np.abs(ts)**2 - np.abs(tp)**2)/(np.abs(ts)**2 + np.abs(tp)**2)
D_svd = np.array(D_svd)
D_jones = np.array(D_jones)

plt.figure(figsize=[21,7])
plt.suptitle('Diattenuation computed 3 ways')
plt.subplot(131)
plt.scatter(x,y,c=D_fresnel)
plt.title('Fresnel Coefficients')
plt.colorbar()

plt.subplot(132)
plt.scatter(x,y,c=D_svd)
plt.title('SVD of PRT Matrix')
plt.colorbar()

plt.subplot(133)
plt.scatter(x,y,c=D_jones)
plt.title('Jones Matrix Diagonals')
plt.colorbar()
plt.show()