import numpy as np

def InteriorMatrixP(nj,thj,dj,wl):

    # Describes the matrix for the jth interface in the coating stack
    B = 2*np.pi*dj*np.cos(thj)/wl

    return np.array([[np.cos(B),-1j*np.sin(B)*np.cos(thj)/nj],
                     [-1j*np.sin(B)/np.cos(thj),np.cos(B)]])

def InteriorMatrixS(nj,thj,dj,wl):

    # Describes the matrix for the jth interface in the coating stack
    B = 2*np.pi*dj*np.cos(thj)/wl

    return np.array([[np.cos(thj),-1j*np.sin(B)/(np.cos(thj)*nj)],
                     [-1j*np.sin(B)*np.cos(thj),np.cos(B)]])


def ComputeEffectiveFresnelCoefficients(n_list,th_list,d_list,wl):
    # First element needs to be the medium the Osys is in, typically vacuum; n = 1

    # The P-Polarization State
    if n_list.shape[-1] != th_list.shape[-1]:
        print('ERROR: Index list and Angle list are not of the same shape')

    Mjp = np.array([[n_list[0],th_list[0]],
                    [n_list[0],th_list[0]]])
    
    Mjs = np.array([[n_list[0]*np.cos(th_list[0]), 1],
                    [n_list[0]*np.cos(th_list[0]),-1])

    for ijk in range(1,n_list.shape[-1]-1):

        Mjp = Mjp @ InteriorMatrixP(n_list[ijk],th_list[ijk],d_list[ijk],wl)
        Mjs = Mjs @ InteriorMatrixS(n_list[ijk],th_list[ijk],d_list[ijk],wl)

    Mnp = Mjp @ np.array([[np.cos(th_list[-1]),0],[n_list[-1],0]])
    Mns = Mjs @ np.array([[1,0],[n_list[-1]*np.cos(th_list[-1]),0]])

    Ap = (1/(2*n_list[0]*np.cos(th_list[0]))) * Mnp
    As = (1/(2*n_list[0]*np.cos(th_list[0]))) * Mns

    ts = 1/As[0,0]
    rs = As[1,0]/As[0,0]
    tp = 1/Ap[0,0]
    rp = Ap[1,0]/Ap[0,0]

    return ts,tp,rs,rp



    