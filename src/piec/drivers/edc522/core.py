'''
This is for the EDC Model 522 NOTE: Does not take SCPI commands
'''
import numpy as np
from piec.drivers.instrument import Instrument
#yes

class EDC522(Instrument):
    """
    Specific Class for exact model of Model 522. Currently only supports a single read out funciton
    """
    voltage_range = (-111.111, 111.111) #volts
    current_range = (-.111111, .111111) #amps


    def idn(self):
        """Query the instrument identity."""
        self.device.write("ID?")
        return self.device.read()

    def query_error(self):
        """Query the instrument for any error messages."""
        self.device.write("?")
        return self.device.read()

    def set_output(self, value, mode="voltage"):
        """
        Configures the ouput of the EDC 522 to a valid output

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            value (str): Desired output value (either current or voltage)
            mode (str): mode args = [voltage, current]
        """

        if mode == "voltage":
            self.set_voltage(value)
        elif mode == "current":
            self.set_current(value)
        else:
            raise ValueError("Invalid mode. Must be 'voltage' or 'current'")        

        def set_current(self, current):
            """
            Set the output voltage.

            :param voltage: Desired output voltage in volts.
            """
            if not (-.111111 <= current <= .111111):
                raise ValueError("Current out of range (-.111111V to .111111V)")
            
            sign = "+" if current >= 0 else "-"
            abs_current = abs(current)
            
            # Convert voltage to six-character string
            magnitude = f"{abs_current:06.3f}".replace(".", "")

            # Select range based on voltage
            if abs_current <= 10e-3:
                range_code = "4"
            elif abs_current <= 100e-3:
                range_code = "5"

            command = f"{sign}{magnitude}{range_code}"
            self.device.write(command)

    def set_voltage(self, voltage):
        """
        Set the output voltage.

        :param voltage: Desired output voltage in volts.
        """
        if not (-111.111 <= voltage <= 111.111):
            raise ValueError("Voltage out of range (-111.111V to 111.111V)")
        
        sign = "+" if voltage >= 0 else "-"
        abs_voltage = abs(voltage)
        
        #NOTE hiding J functionality used instead of 10 
        #example would be "+JJJJJJ1" would send 11.111V
        # Convert voltage to six-character string
        magnitude = f"{abs_voltage:06.3f}".replace(".", "")

        # Select range based on voltage
        if abs_voltage <= 0.1:
            range_code = "0"
        elif abs_voltage <= 10:
            range_code = "1"
        else:
            range_code = "2"

        command = f"{sign}{magnitude}{range_code}"
        self.device.write(command)

#helper func
import re

def extract_number(input_string):
    # Use regular expression to find the number in the string
    match = re.search(r'[+-]?\d+\.\d+E[+-]?\d+', input_string)
    if match:
        return match.group(0)
    else:
        return None
