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
    voltage_range = (-100, 100) #volts
    current_range = (-.1, .1) #amps


    def idn(self):
        """Query the instrument identity."""
        self.instrument.write("ID?")
        return self.instrument.read()

    def query_error(self):
        """Query the instrument for any error messages."""
        self.instrument.write("?")
        return self.instrument.read()
     

    def set_output(self, value, mode="voltage", opt=False):
        """
        Formats a current or voltage value into an 8-character string for instrument control.
        Automatically determines the appropriate range.

        Args:
            value (float or int): The value to send to the instrument.
            mode (str, optional): "voltage" or "current" or "crowbar". Defaults to "voltage".
            opt (bool, optional): Is only TRUE if high voltage option is connected. Enables the 1000V range

        Returns:
            str: An 8-character command string, or None if input is invalid or value is out of range.
        """
        if opt:
            self.voltage_range = (-1000, 1000)
        if mode not in ("voltage", "current", "crowbar"):
            return None
        if mode == "crowbar":
            self.instrument.write("00000000") #puts it in crowbar mode
        if value == 0:
            self.instrument.write("+0000000") #defaults to positive mode
            return
        if value == "-0":
            self.instrument.write("-0000000") #negative negative mode
            return

        polarity = "+" if value > 0 else "-"
        abs_value = abs(value)

        if mode == "voltage":
            if abs_value >max(self.voltage_range):
                raise ValueError("Voltage value out of range")
            ranges = [0.1, 10, 100, 1000]
            range_chars = "0123"
            max_values = [0.9999999, 10, 100, 1000]  # Slightly higher max values
        elif mode == "current":
            if abs_value >max(self.current_range):
                raise ValueError("Current value out of range")
            ranges = [0.01, 0.1]
            range_chars = "45"
            max_values = [0.00999999, 0.1]  # Slightly higher max values
        else:
            return None
        #NOTE, want it to defaault to lowest possible range if possible. therefore iterate bottom up
        for i, r in enumerate(ranges):
            if abs_value <= max_values[i]:  # Check against max value for the range
                scaled = abs_value / r 
                best_range_index = i
                scaled_value = scaled
                break
        else:  # No suitable range was found
            return None

        digits_str = "{:06.0f}".format(scaled_value * 1000000)

        # J handling:
        J_vals = [100e-3, 10, 100, 1000]
        if abs_value in J_vals:
            digits_str = "J00000"
        command = f"{polarity}{digits_str}{range_chars[best_range_index]}"
        print(command)
        self.instrument.write(command)

#helper func
import re

def extract_number(input_string):
    # Use regular expression to find the number in the string
    match = re.search(r'[+-]?\d+\.\d+E[+-]?\d+', input_string)
    if match:
        return match.group(0)
    else:
        return None
    
"""
Old function to allow for the range 10 and 11.1111 values

def format_instrument_command(value, data_type="voltage"):
    '''Formats a value into an 8-character instrument command string.'''

    if data_type not in ("voltage", "current"):
        return None

    if value == 0:
        return "00000000"

    polarity = "+" if value > 0 else "-"
    abs_value = abs(value)

    if data_type == "voltage":
        ranges = [0.1, 10, 100, 1000]
        range_chars = "0123"
        max_values = [0.9999999, 11.11111, 111.1111, 1111.111]  # Slightly higher max values
    elif data_type == "current":
        ranges = [0.01, 0.1]
        range_chars = "45"
        max_values = [0.00999999, 0.1111111]  # Slightly higher max values
    else:
        return None

    for i, r in enumerate(ranges):
        if abs_value <= max_values[i]:  # Check against max value for the range
            scaled = abs_value / r
            best_range_index = i
            scaled_value = scaled
            break
    else:  # No suitable range was found
        return None

    digits_str = "{:06.0f}".format(scaled_value * 100000)

    # J handling:
    if best_range_index == 1 and scaled_value == 10:  # Exactly 10V
        digits_str = "J00000"
    elif best_range_index == 1 and 1 <= scaled_value < 10: # 1V to 9.99999V in 10V range
        digits = []
        for digit in str(int(scaled_value * 100000)):
            if digit == '1':
                digits.append('J')
            else:
                digits.append(digit)
        digits_str = "".join(digits).zfill(6)

    return f"{polarity}{digits_str}{range_chars[best_range_index]}"

"""

