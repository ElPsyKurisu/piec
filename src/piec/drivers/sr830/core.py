'''
This is for the KEYSIGHT 81150A Arbitrary Waveform Generator and requires the KEYSIGHT I/O Libraries to function. check if true
'''
import numpy as np
import time
from ..scpi_instrument import Lockin
#yes

class Sr830(Lockin):
    """
    Specific Class for this exact model of lockin: Stanford Research Systems SR830
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    #Should be overriden
    channel = ['1','2']
    voltage = (4e-3, 5) 
    frequency = (1e-3, 102e3)
    phase = (-360.00,729.99) #notice instruemnt rounds to 0.01 for you and will convert to +-180 e.g. PHAS 541.0 command will set the phase to -179.00°
    harmonic = (1,19999)
    trig = ["sin", "rising", "falling"] #type of trig allowed from reference input ["sin", "rising", "falling"]
    sensitivity = ['2nv/fa', '5nv/fa', '10nv/fa', '20nv/fa', '50nv/fa', '100nv/fa','200nv/fa', '500nv/fa', '1uv/pa', '2uv/pa', '5uv/pa', '10uv/pa','20uv/pa', '50uv/pa', '100uv/pa', '200uv/pa', '500uv/pa','1mv/na', '2mv/na', '5mv/na', '10mv/na', '20mv/na', '50mv/na', '100mv/na', '200mv/na', '500mv/na', '1v/ua'] #note this is gonna be a long list ['2nv/fa', '5nv/fa', '10nv/fa', '20nv/fa', '50nv/fa', '100nv/fa','200nv/fa', '500nv/fa', '1uv/pa', '2uv/pa', '5uv/pa', '10uv/pa','20uv/pa', '50uv/pa', '100uv/pa', '200uv/pa', '500uv/pa','1mv/na', '2mv/na', '5mv/na', '10mv/na', '20mv/na', '50mv/na', '100mv/na', '200mv/na', '500mv/na', '1v/ua']
    reserve_mode = ["high", "norm", "low"]
    time_constant = ['10us', '30us', '100us', '300us', '1ms', '3ms', '10ms', '30ms', '100ms', '300ms', '1s', '3s', '10s', '30s', '100s', '300s', '1ks', '3ks', '10ks', '30ks']
    lp_filter_slope = ['6','12','18','24']
    display = ['primary', 'secondary', 'noise', 'auxA', 'auxB']
    ratio = ['none', 'auxA', 'auxB']
    display_output = ['display', 'primary']
    display_expand_what = ['x', 'y', 'r']
    display_output_offset= (-105.00, 105.00)
    display_output_expand= ['1', '10', '100']

    def __class_specific(self): 
        """
        Place to define instrument specific stuff. Ideally never needed if Parent class is robust enough and instead
        we just define class attributes as above
        """
        return None