#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 10:31:55 2021

@author: jashcraft


Unless it was changed, the ZOS raytrace returns a structure as an array with the following items
- 0: Success 
- 1: raynumber
- 2: errCode
- 3: vignetteCode
- 4: z position
- 5: a direction cosine
- 6: b direction cosine
- 7: g direction cosine

As well as the direction cosines of the surface normals. To do a full polarization ray trace we need to

1) Populate the Entrance Pupil with rays for a given field
2) Send the pupil coordinates to the ZOS-API batch raytrace <- Give up and use MATLAB until OS has their stuff together
3) Run the batch ray trace and return
    - vignette code
    - x,y,z position in global coordinates
    - a,b,g directions in global coordinates
    - a,b,g directions of surface normals
    - n1, n2 indicies of the interaction
    - OPTIONAL: if the interaction was a reflection or refraction
4) Compute the PRT matrix for each ray
5) Rotate the PRT matrix into the pupil coordinate system
6) Display a Jones Pupil and Amplitude Response Matrix with P O P P Y
7) OPTIONAL: Convert to a Mueller Point-spread matrix with P O P P Y

Can you do a bunch of cross products at once? seek einsum
"""

# Polarization functions from OPTI - 586
import numpy as np

# INCOMPLETE FUNCTION
def ConvertBatchRayData(fname,n1,n2):

    """
    We have some control over what form this takes, but the preliminary script has to be written in MATLAB I guess
    Ideally, the same ray does not have to be traced multiple times and the data comes as a list of AOI, AOR, and surface normals
    in terms of a global coordinate system
    It is likely unavoidable to loop through surfaces but idk

    The column order of the table is 
    0: xData
    1: yData
    2: zData
    3: lData
    4: mData
    5: nData
    6: l2Data
    7: m2Data
    8: n2Data
    """

    # INSERT SOME TEXT READING SECTION
    rays = np.genfromtxt(fname,skip_header=1,delimiter=',')

    # Position at surface
    xData = rays[:,0]
    yData = rays[:,1]
    zData = rays[:,2]

    # Direction cosines after surface
    lData = rays[:,3]
    mData = rays[:,4]
    nData = rays[:,5]

    # Direction cosines of surface normal
    l2Data = rays[:,6]
    m2Data = rays[:,7]
    n2Data = rays[:,8]

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
    
    # refractive indices - can grab from ZOS-API so I'm leaving these here commented, for now just user inputs
    # n1 = TheSystem.MFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.INDX, toSurface - 1, waveNumber, 0, 0, 0, 0, 0, 0);
    # n2 = TheSystem.MFE.GetOperandValue(ZOSAPI.Editors.MFE.MeritOperandType.INDX, toSurface, waveNumber, 0, 0, 0, 0, 0, 0);
    aoi = np.arcsin(n2/n1 * np.sin(aoe))
    
    # convert to degrees
    # aoi = aoi * 180/np.pi
    # aoe = aoe * 180/np.pi


    #kin = np.array([rays[5],rays[6],rays[7]])
    #kout = np.array([rays[5],rays[6],rays[7]])
    #norm = rays[7]

    return aoi,xData,yData


def FresnelCoefficients(aoi,n1,n2,mode='reflection'):

    # ratio of refractive indices
    n = n2/n1

    if mode == 'reflection':

        rs = (np.cos(aoi) - np.sqrt(n**2 - np.sin(aoi)**2))/(np.cos(aoi) + np.sqrt(n**2 - np.sin(aoi)**2))
        rp = (n**2 * np.cos(aoi) - np.sqrt(n**2 - np.sin(aoi)**2))/(n**2 * np.cos(aoi) + np.sqrt(n**2 - np.sin(aoi)**2))

        return rs,rp

    elif mode == 'transmission':

        ts = (2*np.cos(aoi))/(np.cos(aoi) + np.sqrt(n**2 - np.sin(aoi)**2))
        tp = (2*n*np.cos(aoi))/(n**2 * np.cos(aoi) + np.sqrt(n**2 - np.sin(aoi)**2))

        return ts,tp

def ConstructOrthogonalTransferMatrices(kin,kout,normal):

    # Construct Oin-1 with incident ray, say vectors are row vectors
    sin = np.cross(kin,normal)
    sin /= np.linalg.norm(sin) # normalize the s-vector
    pin = np.cross(kin,sin)
    Oin = np.array([sin,pin,kin])

    sout = sin
    pout = np.cross(kout,sout)
    Oout = np.transpose(np.array([sout,pout,kout]))

    return Oin,Oout

def ConstructPRTMatrix(kin,kout,normal,aoi,n1,n2,mode='reflection'):

    # Compute the Fresnel coefficients for either transmission OR reflection
    fs,fp = FresnelCoefficients(aoi,n1,n2,mode)

    # Compute the orthogonal transfer matrices
    Oin,Oout = ConstructOrthogonalTransferMatrices(kin,kout,normal)

    # Compute the Jones matrix
    J = np.array([[fs,0,0],[0,fp,0],[0,0,1]])

    # Compute the Polarization Ray Tracing Matrix
    Pmat = np.matmul(Oout,np.matmul(J,Oin))

    # This returns the polarization ray tracing matrix but I'm not 100% sure its in the coordinate system of the Jones Pupil

    return Pmat

# This is the function that calls the PRT engine and 
def ComplexTransmission():
    pass

def hLinearPolarizer():
    return np.array([[1,0],[0,0]])

def vLinearPolarizer():
    return np.array([[0,0],[0,1]])

#def 45LinearPolarizer():
#    return np.array([[1,1],[1,1]])/2

#def 135LinearPolarizer():
#    return np.array([[1,-1],[-1,1]])/2

def LHCircularPolarizer():
    return np.array([[1,-1j],[1j,1]])/2

def RHCircularPolarizer():
    return np.array([[1,1j],[-1j,1]])/2

def HWavePlate():
    return np.array([[1,0],[0,-1]])

def QWavePlate():
    return np.array([[1,0],[0,1j]])

def JonesRotate(Jonesmatrix,angle):
    
    rotin = np.array([[np.cos(angle),-np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    rotout = np.array([[np.cos(angle),np.sin(angle)],[-np.sin(angle),np.cos(angle)]])
    
    return rotout@Jonesmatrix@rotin

def PauliSpinMatrix(index):
    """
    Check to make sure these are correct 
    """

    if index == 1:
        return np.array([[1,0],[0,-1]])

    elif index == 2:
        return np.array([[0,1],[1,0]])

    elif index == 3:
        return np.array([[1j,0],[0,-1j]])








