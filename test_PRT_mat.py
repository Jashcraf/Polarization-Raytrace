import numpy as np
import matplotlib.pyplot as plt
import polutils as pol

# Test the PRT Computation
n1 = 1.4358 + 1j*9.4953 # Aluminum
n2 = 1
pth = '/Users/jashcraft/Desktop/prt-data/test_prt_data.txt'

aoi,x,y,kin,kout,norm = pol.ConvertBatchRayData(pth,n1,n2)
ts,tp = pol.FresnelCoefficients(aoi,n1,n2)
Pmat = np.zeros([3,3,kin.shape[1]])

for i in range(kin.shape[1]):

    Pmat[:,:,i] = pol.ConstructPRTMatrix(
        kin[:,i],
        kout[:,i],
        norm[:,i],
        aoi[i],
        n1,
        n2,
        mode='transmission')


fig,axs = plt.subplots(figsize=[9,9],nrows=3,ncols=3)
plt.suptitle('PRT Matrix for Surface in dbl gauss lens')
for j in range(3):
    for k in range(3):
        ax = axs[j,k]
        ax.set_title('P{j}{k}'.format(j=j,k=k))
        sca = ax.scatter(x,y,c=Pmat[j,k,:])
        fig.colorbar(sca,ax=ax)
plt.show()



