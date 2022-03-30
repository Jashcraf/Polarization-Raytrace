import numpy as np
import matplotlib.pyplot as plt
import polutils as pol

# Test the PRT Computation
n1 = 1.4358 + 1j*9.4953 # Aluminum
n2 = 1
pth = '/Users/jashcraft/Desktop/prt-data/test_prt_data_'

files = [pth+'primary.txt',pth+'secondary.txt',pth+'folding.txt']

aoi,x,y,kin,kout,norm = pol.ConvertBatchRayData(files[0],n1,n2,mode='reflection')

Pmat = np.zeros([3,3,kin.shape[1]],dtype='complex128')
Jmat = np.zeros([3,3,kin.shape[1]],dtype='complex128')
Pmatlist = []

for path in files:

    aoi,x,y,kin,kout,norm = pol.ConvertBatchRayData(path,n1,n2,mode='reflection')
    ts,tp = pol.FresnelCoefficients(aoi,n1,n2)

    for i in range(kin.shape[1]):

        Pmat[:,:,i],Jmat[:,:,i] = pol.ConstructPRTMatrix(
        kin[:,i],
        kout[:,i],
        norm[:,i],
        aoi[i],
        n1,
        n2,
        mode='reflection')

    # try a list of arrays
    Pmatlist.append(Pmat)

P1 = Pmatlist[0]
P2 = Pmatlist[1]
P3 = Pmatlist[2]

Pmat = np.zeros([3,3,kin.shape[1]],dtype='complex128')

for lmn in range(Pmat.shape[2]):
    Pmat[:,:,lmn] = P3[:,:,lmn] @ P2[:,:,lmn] @ P1[:,:,lmn]

fig,axs = plt.subplots(figsize=[9,9],nrows=3,ncols=3)
plt.suptitle('|PRT Matrix| for Surface in Webb Parabola')
for j in range(3):
    for k in range(3):
        ax = axs[j,k]
        ax.set_title('P{j}{k}'.format(j=j,k=k))
        sca = ax.scatter(x,y,c=np.abs(Pmat[j,k,:]))
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(False)
        fig.colorbar(sca,ax=ax)
plt.show()

fig,axs = plt.subplots(figsize=[9,9],nrows=3,ncols=3)
plt.suptitle('Arg(PRT Matrix) for Surface in Webb Parabola')
for j in range(3):
    for k in range(3):
        ax = axs[j,k]
        ax.set_title('P{j}{k}'.format(j=j,k=k))
        sca = ax.scatter(x,y,c=np.angle(Pmat[j,k,:]))
        ax.axes.xaxis.set_visible(False)
        ax.axes.yaxis.set_visible(False)
        fig.colorbar(sca,ax=ax)
plt.show()

    # if path == files[0]:
    #     Pmat1 = Pmat
    #     Jmat1 = Jmat

    # elif path == files[1]:
    #     Pmat2 = Pmat
    #     Jmat2 = Jmat

    # elif path == files[2]:
    #     Pmat3 = Pmat
    #     Jmat3 = Jmat

