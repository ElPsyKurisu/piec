'''
This is for the KEYSIGHT 81150A Arbitrary Waveform Generator and requires the KEYSIGHT I/O Libraries to function. check if true
'''
import numpy as np
import time
from piec.drivers.instrument import Instrument
import pyvisa

class Keithley193a(Instrument):
    """
    Specific Class for exact model of DMM. Currently only supports a single read out funciton
    """
    def idn(self):
        """
        Queries the instrument for its ID SHOULD BE OVERRIDDEN AS NECESSARY
        """
        start_time = time.time()
        try:
            while True:
                # Check if 5 seconds have passed
                if time.time() - start_time > 5:
                    raise pyvisa.errors.VisaIOError(pyvisa.constants.VI_ERROR_TMO)

                if self.read_voltage() is not None:
                    return "Custom Keithley193a Object at {}".format(self.instrument.resource_name)
                
        except pyvisa.errors.VisaIOError as e: 
            if e.error_code == pyvisa.constants.VI_ERROR_TMO:
                print("Timeout error occurred while waiting for the Keithley.")
                return "Not connected"
    def read_voltage(self):
        """
        Reads the voltage from the DMM and returns a string
        """
        string = self.instrument.query('MEAS:VOLT:DC?') #note any query gives this
        return extract_number(string)
#helper func
import re

def extract_number(input_string):
    # Use regular expression to find the number in the string
    match = re.search(r'[+-]?\d+\.\d+E[+-]?\d+', input_string)
    if match:
        return match.group(0)
    else:
        return None
