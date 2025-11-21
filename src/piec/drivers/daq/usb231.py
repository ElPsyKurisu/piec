from ..digilent import Digilent
from .daq import Daq

# Attempt to import necessary enums from mcculw if available
try:
    from mcculw.enums import ULRange, DigitalIODirection, DigitalPortType, AnalogInputMode
except ImportError:
    # These will be handled in virtual mode logic
    ULRange = None
    DigitalIODirection = None
    DigitalPortType = None
    AnalogInputMode = None

class USB231(Digilent, Daq):
    """
    Driver for the Measurement Computing (MCC) USB-231 DAQ device.
    
    Based on Manual:
    - [cite_start]8 Single-Ended Analog Inputs (16-bit, +/- 10V) [cite: 668]
    - [cite_start]2 Analog Outputs (16-bit, +/- 10V) [cite: 677]
    - [cite_start]8 Digital I/O (Bit configurable) [cite: 683]
    """

    # --- Class Attributes ---
    
    AUTODETECT_ID = "USB-231"

    # Default to the safer Differential mode (4 channels) per user request.
    # This will be updated dynamically by set_input_mode().
    ai_channel = [0, 1, 2, 3]

    # [cite_start]Analog Output Channels: 2 channels (indices 0-1) [cite: 677]
    ao_channel = [0, 1]

    # [cite_start]Digital I/O Channels: 8 channels (indices 0-7) [cite: 683]
    dio_channel = [0, 1, 2, 3, 4, 5, 6, 7]

    # [cite_start]Analog Input Range: Fixed at +/- 10V [cite: 668]
    ai_range = [(-10.0, 10.0)]

    # [cite_start]Analog Output Range: Fixed at +/- 10V [cite: 677]
    ao_range = [(-10.0, 10.0)]

    # [cite_start]Analog Input Modes: SE (Single-Ended) or DIFF (Differential) [cite: 668]
    ai_mode = ['SE', 'DIFF']

    # [cite_start]Digital Direction: Configurable as Input ('I') or Output ('O') [cite: 683]
    dio_direction = ['I', 'O']

    def __init__(self, address, **kwargs):
        """
        Initialize the USB-231. 
        Defaults to Differential Mode (Channels 0-3) to match ai_channel default.
        """
        # Initialize the parent Digilent class (handles connection)
        super().__init__(address, **kwargs)

        # Force hardware to match the class default (Differential) on startup
        if not self.virtual:
            self.set_input_mode('DIFF')

    def read_analog(self, ai_channel):
        """
        Reads a float value (voltage) from the specified Analog Input channel.
        [cite_start]Manual Page 10: Software paced mode[cite: 124].
        
        args:
            ai_channel (int): The channel to read from.
        returns:
            float: The measured value in Volts.
        """
        if self.virtual:
            print(f"USB231 [Virt]: Reading Analog Input Ch {ai_channel} (Simulated 0.0V)")
            return 0.0

        # Validation: Ensure the requested channel is valid for the CURRENT mode
        if ai_channel not in self.ai_channel:
            raise ValueError(f"Channel {ai_channel} is not valid in current Input Mode. Available: {self.ai_channel}")

        try:
            # v_in returns the voltage directly. 
            # [cite_start]Range is fixed at +/- 10V (BIP10VOLTS) [cite: 668]
            value = self.ul.v_in(self.board_num, ai_channel, ULRange.BIP10VOLTS)
            return value
        except Exception as e:
            print(f"USB231 Error reading AI{ai_channel}: {e}")
            raise

    def write_analog(self, ao_channel, value):
        """
        Writes a single float value (voltage) to the specified Analog Output channel.
        [cite_start]Manual Page 17: Software paced mode[cite: 489].
        
        args:
            ao_channel (int): The channel to write to (0-1).
            value (float): The voltage to output (+/- 10V).
        """
        if self.virtual:
            print(f"USB231 [Virt]: Writing {value}V to Analog Output Ch {ao_channel}")
            return

        try:
            # v_out writes voltage directly.
            # [cite_start]Range is fixed at +/- 10V [cite: 677]
            self.ul.v_out(self.board_num, ao_channel, ULRange.BIP10VOLTS, value)
        except Exception as e:
            print(f"USB231 Error writing AO{ao_channel}: {e}")
            raise

    def set_input_mode(self, ai_mode):
        """
        Configures the Analog Input Mode and updates self.ai_channel list.
        [cite_start]Manual Page 22: "8 single-ended or 4 differential; software-selectable"[cite: 668].
        
        args:
            ai_mode (str): 'SE' (Single-Ended) or 'DIFF' (Differential).
        """
        mode_str = str(ai_mode).upper()

        if self.virtual:
            print(f"USB231 [Virt]: Input mode set to {mode_str}")
            # Simulate the logic update for virtual mode
            if 'DIFF' in mode_str:
                self.ai_channel = [0, 1, 2, 3]
            elif 'SE' in mode_str or 'SINGLE' in mode_str:
                self.ai_channel = [0, 1, 2, 3, 4, 5, 6, 7]
            return
        
        try:
            if 'DIFF' in mode_str:
                # Differential Mode: Limits to 4 channels (0-3)
                # [cite_start]Pins 0-3 become High, Pins 4-7 become Low inputs [cite: 261]
                self.ul.a_input_mode(self.board_num, AnalogInputMode.DIFFERENTIAL)
                self.ai_channel = [0, 1, 2, 3]
                print(f"USB231: Set to DIFFERENTIAL mode. Available Channels: {self.ai_channel}")
                
            elif 'SE' in mode_str or 'SINGLE' in mode_str:
                # Single-Ended Mode: Enables 8 channels (0-7)
                # [cite_start]All inputs referenced to AGND [cite: 358]
                self.ul.a_input_mode(self.board_num, AnalogInputMode.SINGLE_ENDED)
                self.ai_channel = [0, 1, 2, 3, 4, 5, 6, 7]
                print(f"USB231: Set to SINGLE-ENDED mode. Available Channels: {self.ai_channel}")
                
            else:
                raise ValueError(f"Invalid mode '{ai_mode}'. Use 'SE' or 'DIFF'.")
                
        except Exception as e:
            print(f"USB231 Error setting input mode: {e}")
            raise

    def set_ai_range(self, ai_channel, ai_range):
        """
        Configures the gain/range for an Analog Input channel.
        [cite_start]The USB-231 has a fixed input range of +/- 10V[cite: 668].
        
        args:
            ai_channel (int): The channel to configure.
            ai_range (tuple): The (min, max) range desired.
        """
        if self.virtual:
            print(f"USB231 [Virt]: Setting AI range to {ai_range} (Hardware is Fixed +/-10V)")
            return

        # Check if the requested range is the supported range (-10, 10)
        valid_range = (-10.0, 10.0)
        if ai_range != valid_range:
            print(f"Warning: USB-231 has a fixed AI range of +/- 10V. Requested {ai_range} ignored.")
        
        # No UL command needed; hardware is fixed.

    def set_ao_range(self, ao_channel, ao_range):
        """
        Configures the output range for an Analog Output channel.
        [cite_start]The USB-231 has a fixed output range of +/- 10V[cite: 677].
        
        args:
            ao_channel (int): The channel to configure.
            ao_range (tuple): The (min, max) range desired.
        """
        if self.virtual:
            print(f"USB231 [Virt]: Setting AO range to {ao_range} (Hardware is Fixed +/-10V)")
            return

        valid_range = (-10.0, 10.0)
        if ao_range != valid_range:
            print(f"Warning: USB-231 has a fixed AO range of +/- 10V. Requested {ao_range} ignored.")

    def read_digital(self, dio_channel):
        """
        Reads the state of a single digital channel (DIO0 - DIO7).
        [cite_start]Manual Page 18: "All digital I/O updates and samples are software-paced."[cite: 508].
        
        args:
            dio_channel (int): The channel to read.
        returns:
            int: 1 (High) or 0 (Low).
        """
        if self.virtual:
            print(f"USB231 [Virt]: Reading Digital Ch {dio_channel} (Simulated 0)")
            return 0

        try:
            # [cite_start]USB-231 uses FIRSTPORTA for the 8 DIO bits (Pins 17-24) [cite: 741]
            bit_value = self.ul.d_bit_in(self.board_num, DigitalPortType.FIRSTPORTA, dio_channel)
            return bit_value
        except Exception as e:
            print(f"USB231 Error reading DIO{dio_channel}: {e}")
            raise

    def write_digital(self, dio_channel, state):
        """
        Sets the state of a digital output channel.
        
        args:
            dio_channel (int): The channel to write to.
            state (int/bool): 1/True for High, 0/False for Low.
        """
        if self.virtual:
            print(f"USB231 [Virt]: Writing {state} to Digital Ch {dio_channel}")
            return

        try:
            bit_val = 1 if state else 0
            self.ul.d_bit_out(self.board_num, DigitalPortType.FIRSTPORTA, dio_channel, bit_val)
        except Exception as e:
            print(f"USB231 Error writing DIO{dio_channel}: {e}")
            raise

    def set_dio_direction(self, dio_channel, dio_direction):
        """
        Configures the physics of the digital pin (Input vs Output).
        [cite_start]Manual Page 18: "Each digital I/O line is bit-configurable as input or output."[cite: 505].
        
        args:
            dio_channel (int): The channel to configure.
            dio_direction (str): 'IN' or 'OUT'.
        """
        direction_str = str(dio_direction).upper()
        
        # Map string to UL Enum
        if 'I' in direction_str and 'OUT' not in direction_str:
            ul_dir = DigitalIODirection.IN
            dir_name = "IN"
        else:
            ul_dir = DigitalIODirection.OUT
            dir_name = "OUT"

        if self.virtual:
            print(f"USB231 [Virt]: Configured DIO{dio_channel} as {dir_name}")
            return

        try:
            # d_config_bit configures individual bits
            self.ul.d_config_bit(self.board_num, DigitalPortType.FIRSTPORTA, dio_channel, ul_dir)
        except Exception as e:
            print(f"USB231 Error configuring DIO{dio_channel}: {e}")
            raise