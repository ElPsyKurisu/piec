"""
This file contains the driver for the EDC Model 522 DC Voltage/Current Calibrator.

This driver is based on the sourcemeter.py outline and the specifications
found in the EDC 522 Operating Manual. Created by Gemini NOTE: Not tested yet, probably doesn't work.
"""

"""
This file contains the driver for the EDC Model 522 DC Voltage/Current Calibrator.

This driver is based on the sourcemeter.py outline and the specifications
found in the EDC 522 Operating Manual. This instrument does NOT use SCPI commands.
"""

import math

# This import assumes that 'sourcemeter.py' is available in the Python path
# or a compatible project structure.
from sourcemeter import Sourcemeter

class EDC522(Sourcemeter):
    """
    Driver for the EDC Model 522 DC Voltage/Current Calibrator.

    This class defines the capabilities of the instrument based on the parent
    Sourcemeter class and the device's manual. It implements the methods
    to control the instrument using its specific 8-character GPIB command set.
    """

    # --- Instrument Capabilities ---

    # The EDC 522 has a single output channel.
    channel = [1]
    source_func = ['VOLT', 'CURR']
    sense_func = ['VOLT', 'CURR', 'RES']
    mode = ['2W', '4W']
    voltage = (-111.1110, 111.1110)
    current = (-0.111111, 0.111111)
    voltage_compliance = (0, 100)
    current_compliance = (0, 0.1)

    _RANGE_MAP = {
        # 'range_char': (max_value, multiplier, function)
        '0': (0.1111110, 1e7, 'VOLT'),  # 100 mV Range
        '1': (11.11110,  1e5, 'VOLT'),  # 10 V Range
        '2': (111.1110,  1e4, 'VOLT'),  # 100 V Range
        '4': (0.0111111, 1e8, 'CURR'),  # 10 mA Range
        '5': (0.1111110, 1e7, 'CURR'),  # 100 mA Range
    }

    def __init__(self, address):
        """
        Initializes the EDC522 instrument driver.
        Sets the instrument to a safe default state (crowbar output).
        """
        super().__init__(address)
        # Initialize internal state variables
        self._source_function = 'VOLT'
        self._range_char = '1'  # Default to 10V range
        self._magnitude_str = "000000"
        self._polarity = '+'    # Stored polarity for when output is on
        self._output_on = False
        self.reset()      # Set instrument to a safe state initially

    # --- SCPI-like Utility Methods ---

    def idn(self):
        """
        Queries the instrument for its identification string.
        This is the EDC 522 equivalent of the SCPI '*IDN?' command.
        Manual Reference: Section 3.4.4.3
        """
        return self.query("ID?")

    def reset(self):
        """
        Resets the instrument to a safe, known state by setting the
        output to a crowbar (short-circuit zero). This is the closest
        equivalent to the SCPI '*RST' command for this instrument.
        """
        self.output(False)

    def clear(self):
        """
        Clears the Service Request (SRQ) status by sending the 'whats wrong'
        query. This is the EDC 522 equivalent of the SCPI '*CLS' command.
        Manual Reference: Section 3.4.4.5
        """
        # Sending '?' clears the SRQ, but it also returns a string.
        # We query and discard the response to clear the status.
        self.query("?")

    def error(self):
        """
        Queries the instrument for the current error status. This will also
        clear the SRQ line. This is the equivalent of 'SYST:ERR?'
        Manual Reference: Section 3.4.4.4
        """
        return self.query("?")

    def wait(self):
        """
        Not implemented. The EDC 522 does not support an equivalent
        to the SCPI '*WAI' command. Operations are synchronous.
        """
        raise NotImplementedError("The EDC 522 does not have a wait command.")

    def self_test(self):
        """
        Not implemented. The EDC 522 does not support a programmable
        self-test equivalent to the SCPI '*TST?' command.
        """
        raise NotImplementedError("The EDC 522 does not support a self-test command.")

    def operation_complete(self):
        """
        Not implemented. The EDC 522 does not support an equivalent
        to the SCPI '*OPC?' command.
        """
        raise NotImplementedError("The EDC 522 does not have an operation complete query.")

    # --- Core Instrument Methods ---

    def _update_output(self):
        """
        Formats and sends the 8-character command string to the instrument
        based on the current internal state.
        Manual Reference: Section 3.4.4, Data Byte String Format
        """
        # Polarity is '0' for crowbar (output off)
        polarity_char = self._polarity if self._output_on else '0'

        # Assemble the 8-character command
        command = f"{polarity_char}{self._magnitude_str}{self._range_char}"
        
        # Ensure command is exactly 8 characters long
        if len(command) != 8:
            raise ValueError(f"Internal error: generated command '{command}' is not 8 characters.")
            
        self.write(command)

    def output(self, on=True):
        """
        Turns the main output of the sourcemeter on or off.
        'off' engages a 'crowbar' or short circuit at the output.
        Manual Reference: Section 3.4.4, Character 1 (Polarity)
        """
        self._output_on = bool(on)
        self._update_output()

    def set_source_function(self, source_func):
        """
        Sets the primary function of the source ('VOLT' or 'CURR').
        Note: This only sets the internal state. The instrument function is
        actually changed when a voltage/current value is set, which selects
        an appropriate range.
        """
        if source_func.upper() not in self.source_func:
            raise ValueError(f"Invalid source function. Must be one of {self.source_func}")
        self._source_function = source_func.upper()

    def _format_and_select_range(self, value, func):
        """
        Internal helper to select the best range and format the magnitude string.
        """
        value_abs = abs(value)
        
        # Find the best range (smallest range that can handle the value)
        best_range = None
        min_max_val = float('inf')

        for r_char, (max_val, _, r_func) in self._RANGE_MAP.items():
            if r_func == func and value_abs <= max_val and max_val < min_max_val:
                best_range = r_char
                min_max_val = max_val

        if best_range is None:
            raise ValueError(f"Value {value} is out of range for function {func}.")
        
        self._range_char = best_range
        _, multiplier, _ = self._MAP[best_range]

        # Calculate and format the 6-digit magnitude string
        magnitude_digits = int(round(value_abs * multiplier))
        
        # The instrument accepts a max magnitude of 1111110 on any range
        if magnitude_digits > 1111110:
             magnitude_digits = 1111110 # Clamp to max
             
        self._magnitude_str = f"{magnitude_digits:06d}"
        if len(self._magnitude_str) > 6:
            self._magnitude_str = self._magnitude_str[-6:] # Truncate if somehow larger

    def set_source_voltage(self, voltage):
        """
        Sets the output level when in voltage source mode.
        This selects the appropriate range and sends the command.
        """
        self.set_source_function('VOLT')
        self._polarity = '+' if voltage >= 0 else '-'
        self._format_and_select_range(voltage, 'VOLT')
        self._update_output()

    def set_source_current(self, current):
        """
        Sets the output level when in current source mode.
        This selects the appropriate range and sends the command.
        """
        self.set_source_function('CURR')
        self._polarity = '+' if current >= 0 else '-'
        self._format_and_select_range(current, 'CURR')
        self._update_output()
        
    def set_voltage_compliance(self, voltage_compliance):
        """
        Not implemented. Voltage compliance is set via an internal hardware
        jumper on the EDC 522 and cannot be programmed remotely.
        Manual Reference: Section 3.6.0
        """
        raise NotImplementedError("Voltage compliance is not programmable on the EDC 522.")

    def set_current_compliance(self, current_compliance):
        """
        Not implemented. Current compliance is fixed at 100 mA in voltage
        mode and is not programmable.
        Manual Reference: Section 1.3.1
        """
        raise NotImplementedError("Current compliance is not programmable on the EDC 522.")
        
    def set_sense_mode(self, mode):
        """
        Not implemented. Sense mode (2W/4W) is a physical wiring
        configuration and cannot be programmed remotely.
        """
        raise NotImplementedError("Sense mode is a physical wiring configuration.")
        
    def set_sense_function(self, sens_func):
        """
        Not implemented. The EDC 522 is a source/calibrator and does not
        have measurement (sense) capabilities.
        """
        raise NotImplementedError("The EDC 522 is a source and cannot sense/measure values.")

    def quick_read(self):
        """
        Not implemented. The EDC 522 is a source and cannot read values.
        """
        raise NotImplementedError("The EDC 522 is a source and cannot read values.")

    def get_voltage(self):
        """
        Not implemented. The EDC 522 is a source and cannot measure voltage.
        """
        raise NotImplementedError("The EDC 522 is a source and cannot measure voltage.")

    def get_current(self):
        """
        Not implemented. The EDC 522 is a source and cannot measure current.
        """
        raise NotImplementedError("The EDC 522 is a source and cannot measure current.")

