'''
This is for the KEYSIGHT 81150A Arbitrary Waveform Generator and requires the KEYSIGHT I/O Libraries to function. check if true
'''
import numpy as np
import time
from ..instrument import Awg
#yes

class Keysight81150a(Awg):
    """
    Specific Class for this exact model of awg: Keysight 81150A
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    channel = ['1', '2'] #allowable channels ['1', '2']
    voltage = (8.0e-3, 40.0) #V_pp
    frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'ARB': (1e-6, 120e6)}} #where did i get this info?
    func = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    #might be useless since all awgs should have sin, squ, pulse etc maybe not include arb? idk
    slew_rate = 1.0e9 # V/s
    arb_wf_points_range = (2, 524288)

    def __class_specific(self):
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None
