'''
This is for the Lecroix SDA 6020
'''
import numpy as np
import time
from ..scpi_instrument import Scope
#yes

class SDA6020(Scope):
    """
    Specific Class for this exact model of awg: Keysight 81150A
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    channel = ['1', '2'] #allowable channels ['1', '2']
    voltage = (0, 5) #V_pp add functionality that swithches voltage depending on mode
    frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
    func = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    #might be useless since all awgs should have sin, squ, pulse etc maybe not include arb? idk
    #note that depends if we are in high voltage or high bandwidth mode, if in high bandwidth mode all are 50e6 max freq
    slew_rate = 1.0e9 # V/s
    arb_wf_points_range = (2, 524288)
    source_impedance = ['5', '50']
    load_impedance = (0.3, 1e6)

    def __init__(self, address, check_params=False): #sets the check_params true by default, since we want at this layer to be as safe as possible
        super().__init__(address, check_params)

    def query_wf(self, channel: str = 'C1'):
        self.instrument.write(f"{channel}:WF? DAT1") 
        binary_data_with_header = self.instrument.read_raw()
        return binary_data_with_header

    def __class_specific(self):
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None
