'''
This is for the KEYSIGHT DSOX3024a Oscilloscope and requires the KEYSIGHT I/O Libraries to function.
'''
import numpy as np
import time
from ..scpi_instrument import Scope
#yes

class Dsox3024a(Scope):
    """
    Specific Class for this exact model of scope: Keysight DSOX3024a
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    voltage_range = (8e-3, 40)
    voltage_scale = (8e-4, 4)
    time_range = (2e-8, 500)
    time_scale = (2e-9, 50)
    time_base_type = ['main', 'wind', 'xy', 'roll'] #added WIND so either WIND or WINDOW is allowed
    channel = ['1', '2', '3', '4']
    acquire_type = ['norm', 'hres', 'peak']
    
    def __init__(self, address, check_params=True): #sets the check_params true by default, since we want at this layer to be as safe as possible
        super().__init__(address, check_params)

    def __class_specific(self):
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None




