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
    time_base_type = ['MAIN', 'WINDow', 'WIND', 'XY', 'ROLL'] #added WIND so either WIND or WINDOW is allowed
    channel = ['1', '2', '3', '4']
    
    def __init__(self, address, check_params=True): #sets the check_params true by default, since we want at this layer to be as safe as possible
        super().__init__(address, check_params)

    def __class_specific(self):
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None

    def setup(self, channel: str = '1', voltage_range: str = '16', voltage_offset: str = '1', delay: str = '100e-6', time_range: str = '1e-3', autoscale=True):
        """
        Override default params here by ovverriding class Scope funtions
        """
        return super().setup(channel, voltage_range, voltage_offset, delay, time_range, autoscale)



