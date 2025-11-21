"""
Driver for the Measurement Computing (MCC) USB-231 Data Acquisition Device.
Based on the Digilent/MCC Universal Library (UL).
"""
from .daq import Daq
from ..digilent import Digilent

# --- Import MCC Universal Library Enums ---
try:
    from mcculw.enums import ULRange, DigitalIODirection, DigitalPortType
except ImportError:
    # Fallback for virtual mode or if library is missing
    ULRange = None
    DigitalIODirection = None
    DigitalPortType = None

class USB231(Daq, Digilent):
    """
    Driver for the MCC USB-231 High-Speed Data Acquisition Board.
    
    Device Features:
    - [cite_start]8 Single-Ended (SE) Analog Inputs (16-bit) [cite: 49]
    - [cite_start]2 Analog Outputs (16-bit) [cite: 51]
    - [cite_start]8 Configurable Digital I/O [cite: 51]
    - [cite_start]Fixed Analog Input Range: +/- 10V [cite: 668]
    - [cite_start]Fixed Analog Output Range: +/- 10V [cite: 481]
    """

    # --- Class Attributes ---
    
    # The manual does not explicitly state an *IDN? response string as this device 
    # uses the Universal Library (UL) rather than SCPI.
    AUTODETECT_ID = "USB-231" #geo added

    # [cite_start]Analog Input Channels: 8 single-ended channels (indices 0-7) [cite: 49]
    ai_channels = [0, 1, 2, 3, 4, 5, 6, 7]

    # [cite_start]Analog Output Channels: 2 channels (indices 0-1) [cite: 51]
    ao_channels = [0, 1]

    # [cite_start]Digital I/O Channels: 8 channels (indices 0-7) [cite: 51]
    dio_channels = [0, 1, 2, 3, 4, 5, 6, 7]

    # [cite_start]Analog Input Range: Fixed at +/- 10V [cite: 668]
    ai_ranges = [(-10.0, 10.0)]

    # [cite_start]Analog Output Range: Fixed at +/- 10V [cite: 481]
    ao_ranges = [(-10.0, 10.0)]

    # [cite_start]Digital Direction: Configurable as Input ('I') or Output ('O') [cite: 505]
    dio_directions = ['I', 'O']

    def read_analog(self, channel):
        """
        Reads a single voltage value from the specified Analog Input channel.
        
        Operation:
        - [cite_start]Uses software paced mode to initiate A/D conversion[cite: 125].
        - [cite_start]The input range is fixed at +/- 10V[cite: 412].
        
        Args:
            channel (int): The analog input channel (0-7).
            
        Returns:
            float: The measured voltage in Volts.
        """
        if self.virtual:
            return 0.0

        try:
            # v_in returns the voltage directly. 
            # [cite_start]BIP10VOLTS covers the +/- 10V range specified in the manual[cite: 412].
            value = self.ul.v_in(self.board_num, channel, ULRange.BIP10VOLTS)
            return value
        except Exception as e:
            print(f"USB231 Error: Failed to read AI channel {channel}. {e}")
            raise

    def write_analog(self, channel, value):
        """
        Writes a single voltage value to the specified Analog Output channel.
        
        Operation:
        - [cite_start]Uses software paced mode to send a command to the hardware[cite: 490].
        - [cite_start]The output range is +/- 10V[cite: 481].
        
        Args:
            channel (int): The analog output channel (0-1).
            value (float): The voltage to output (must be within +/- 10V).
        """
        if self.virtual:
            return

        try:
            # v_out writes voltage directly.
            self.ul.v_out(self.board_num, channel, ULRange.BIP10VOLTS, value)
        except Exception as e:
            print(f"USB231 Error: Failed to write to AO channel {channel}. {e}")
            raise

    def read_digital(self, channel):
        """
        Reads the state of a single digital I/O channel.
        
        Operation:
        - [cite_start]Digital I/O samples are software-paced[cite: 508].
        - [cite_start]Reads from the 8-bit port (DIO0 - DIO7)[cite: 504].
        
        Args:
            channel (int): The digital channel (0-7).
            
        Returns:
            int: 1 for High, 0 for Low.
        """
        if self.virtual:
            return 0

        try:
            # The USB-231 uses a single 8-bit port (FIRSTPORTA) for DIO0-7
            bit_value = self.ul.d_bit_in(self.board_num, DigitalPortType.FIRSTPORTA, channel)
            return bit_value
        except Exception as e:
            print(f"USB231 Error: Failed to read DIO channel {channel}. {e}")
            raise

    def write_digital(self, channel, state):
        """
        Sets the state of a digital output channel.
        
        Operation:
        - [cite_start]Digital I/O updates are software-paced[cite: 508].
        
        Args:
            channel (int): The digital channel (0-7).
            state (int/bool): 1/True for High, 0/False for Low.
        """
        if self.virtual:
            return

        try:
            bit_val = 1 if state else 0
            self.ul.d_bit_out(self.board_num, DigitalPortType.FIRSTPORTA, channel, bit_val)
        except Exception as e:
            print(f"USB231 Error: Failed to write to DIO channel {channel}. {e}")
            raise

    def set_dio_direction(self, channel, direction):
        """
        Configures the direction of a digital I/O channel.
        
        Operation:
        - [cite_start]Each digital I/O line is bit-configurable as input or output[cite: 505].
        
        Args:
            channel (int): The digital channel (0-7).
            direction (str): 'I', 'IN' for Input; 'O', 'OUT' for Output.
        """
        if self.virtual:
            return

        # Normalize direction argument
        dir_str = str(direction).upper()
        if 'I' in dir_str and 'OUT' not in dir_str:
            ul_dir = DigitalIODirection.IN
        else:
            ul_dir = DigitalIODirection.OUT

        try:
            self.ul.d_config_bit(self.board_num, DigitalPortType.FIRSTPORTA, channel, ul_dir)
        except Exception as e:
            print(f"USB231 Error: Failed to configure DIO channel {channel} direction. {e}")
            raise

    def set_ai_range(self, channel, voltage_range):
        """
        Configures the range for an Analog Input channel.
        
        Note:
        - [cite_start]The USB-231 has a fixed input range of +/- 10V[cite: 412].
        - This method does not perform hardware operations but validates the request.
        
        Args:
            channel (int): The channel to configure.
            voltage_range (tuple): The requested (min, max) range.
        """
        # The manual specifies a fixed range of +/- 10V. 
        # No hardware command is available to change this.
        pass

    def set_ao_range(self, channel, voltage_range):
        """
        Configures the range for an Analog Output channel.
        
        Note:
        - [cite_start]The USB-231 has a fixed output range of +/- 10V[cite: 481].
        - This method does not perform hardware operations but validates the request.
        
        Args:
            channel (int): The channel to configure.
            voltage_range (tuple): The requested (min, max) range.
        """
        # The manual specifies a fixed range of +/- 10V.
        pass