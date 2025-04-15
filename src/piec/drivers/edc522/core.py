'''
This is for the EDC Model 522 NOTE: Does not take SCPI commands
'''
import numpy as np
import math
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
     
# ... (keep the rest of your EDC522 class definition above this) ...

    def set_output(self, value, mode="voltage", opt=False):
        """
        Formats and sends a command to set the instrument's output voltage or current.
        Automatically determines the appropriate range.
        Uses 'J00000' for digits if the value is exactly the maximum of a nominal range.

        Args:
            value (float or int): The desired output value (Volts or Amps).
            mode (str, optional): "voltage", "current", or "crowbar". Defaults to "voltage".
            opt (bool, optional): If True, enables the 1000V range capability. Defaults to False.

        Returns:
            str: The 8-character command string sent to the instrument.

        Raises:
            ValueError: If mode is invalid, or value is out of the instrument's overall range.
            TypeError: If value is not a numeric type (int or float).
        """
        # --- Define NOMINAL Ranges and Limits ---
        voltage_ranges_all = [
            (0.1, '0'), (10.0, '1'), (100.0, '2'), (1000.0, '3')
        ]
        current_ranges_all = [
            (0.01, '4'), (0.1, '5')
        ]

        # Filter ranges based on 'opt'
        if opt:
            voltage_ranges = voltage_ranges_all
            voltage_range_limits = (-1000.0, 1000.0)
        else:
            voltage_ranges = [r for r in voltage_ranges_all if r[1] in ('0', '1', '2')]
            voltage_range_limits = (-100.0, 100.0)

        current_ranges = current_ranges_all
        current_range_limits = (-0.1, 0.1)

        # Sort ranges by max value (ascending)
        voltage_ranges.sort(key=lambda x: x[0])
        current_ranges.sort(key=lambda x: x[0])

        # --- Input Validation / Crowbar / Mode Validation / Zero Handling ---
        if not isinstance(value, (int, float)):
            raise TypeError(f"Input value must be numeric (int or float), got {type(value)}")

        if mode == "crowbar":
            command = "00000000"
            self.instrument.write(command)
            return command

        if mode not in ("voltage", "current"):
            raise ValueError(f"Invalid mode: '{mode}'. Must be 'voltage', 'current', or 'crowbar'.")

        if abs(value) < 1e-12: # Use tolerance for floating point zero
            polarity = "+"
            zero_range_char = voltage_ranges[0][1] if mode == "voltage" else current_ranges[0][1]
            # Use J000000 for exactly 0.0 on the lowest range? Or 000000? Let's stick to 000000 for zero.
            command = f"{polarity}000000{zero_range_char}"
            self.instrument.write(command)
            return command

        # --- Polarity / Abs Value ---
        polarity = "+" if value > 0 else "-"
        abs_value = abs(float(value))

        # --- Select Appropriate Ranges List ---
        if mode == "voltage":
            ranges_to_check = voltage_ranges
            min_limit, max_limit = voltage_range_limits
            unit = "Voltage"
        else: # mode == "current"
            ranges_to_check = current_ranges
            min_limit, max_limit = current_range_limits
            unit = "Current"

        # --- Check Overall Limits (Nominal) ---
        if not (min_limit <= value <= max_limit + 1e-9):
             raise ValueError(f"{unit} value {value} is out of the instrument's range ({min_limit} to {max_limit} with opt={opt})")

        # --- Find Range and Handle 'J' Code ---
        selected_range_max = None
        selected_range_char = None
        digits_str = None # Initialize digits_str
        processed = False
        epsilon = 1e-9 # Tolerance for float comparison

        for i, (r_max, r_char) in enumerate(ranges_to_check):
            # Check if value is exactly the maximum for this range
            is_exact_max = abs(abs_value - r_max) < epsilon

            if is_exact_max:
                # Use 'J' code and THIS range's character
                selected_range_char = r_char
                digits_str = "J00000"
                # print(f"Debug: Value {abs_value} is exact max of range {i}. Using 'J' code with range char '{selected_range_char}'") # Optional Debug
                processed = True
                break # Found exact match, process done

            # If not exact max, check if value fits strictly within this range
            elif abs_value < r_max - epsilon:
                # Value fits here, calculate digits normally below
                selected_range_max = r_max
                selected_range_char = r_char
                # print(f"Debug: Value {abs_value} fits in range {i} (max={r_max}). Using normal digits.") # Optional Debug
                processed = True
                break # Found the range, process done

        # If loop finishes, value must be > last range max (but within overall limit)
        if not processed:
             # Assign the highest available range for normal calculation
             range_index = len(ranges_to_check) - 1
             selected_range_max = ranges_to_check[range_index][0]
             selected_range_char = ranges_to_check[range_index][1]
             # print(f"Debug: Value {abs_value} assigned highest range {range_index} after loop.") # Optional Debug
             processed = True # Mark as processed for safety check

        # Safety check
        if not processed or selected_range_char is None:
             raise RuntimeError(f"Internal Error: Could not determine range or digits for {abs_value}.")

        # --- Calculate Digits IF NOT using 'J' code ---
        if digits_str is None: # Check if 'J' code was assigned above
            if selected_range_max is None: # Safety check
                 raise RuntimeError(f"Internal Error: selected_range_max not set for normal digit calculation.")

            if selected_range_max == 0:
                scaled_for_digits = 0.0
            else:
                # Scale according to the selected nominal range max
                scaled_for_digits = (abs_value / selected_range_max) * 1000000.0

            digits_int = int(round(scaled_for_digits))

            # Clamp values >= 1,000,000 to 999,999
            if digits_int >= 1000000:
                digits_int = 999999
            elif digits_int < 0: # Safeguard
                digits_int = 0

            digits_str = "{:06d}".format(digits_int) # Format normally calculated digits

        # --- Construct Command ---
        command = f"{polarity}{digits_str}{selected_range_char}"

        # --- Send Command ---
        # print(f"Input: {value}, Mode: {mode} -> Command: {command}") # Final Debug print
        self.instrument.write(command)
        return command

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

