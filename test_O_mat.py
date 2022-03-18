import numpy as np
import polutils as pol

# x-polarized
kin = np.array([0,0,1])
n = np.array([0,1/np.sqrt(2),1/np.sqrt(2)])
kout = np.array([0,1,0])

sin = np.cross(kin,n)
sin /= np.linalg.norm(sin)
sout = np.cross(kout,n)
sout /= np.linalg.norm(sout)
pin = np.cross(kin,sin)
pout = np.cross(kout,sout)

print('sin test = ', sin==np.array([-1,0,0]))
print('sout test = ', sout==np.array([1,0,0]))

print('pin test = ', pin==np.array([0,-1,0]))
print('pout test = ', pout==np.array([0,0,-1]))

print('kin test = ', kin==np.array([0,0,1]))
print('kout test = ', kout==np.array([0,1,0]))

Oinv,Oout = pol.ConstructOrthogonalTransferMatrices(kin,kout,n)
oinv = np.array([sin,pin,kin])
oout = np.transpose(np.array([sout,pout,kout]))
print(oinv)
print(oout)
print('Oinv test = ',Oinv)
print('Oout test = ',Oout)

