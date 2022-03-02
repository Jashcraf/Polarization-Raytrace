#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Oct 27 10:31:55 2021

@author: jashcraft
"""

# Polarization functions from OPTI - 586
import numpy as np

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






