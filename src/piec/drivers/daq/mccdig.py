from ..digilent import Digilent
from .daq import Daq

# Import necessary constants from mcculw if available.
# The Digilent parent class handles the library check, but we need the enums for implementation.
try:
    from mcculw.enums import ULRange, DigitalIODirection, DigitalPortType, AnalogInputMode
except ImportError:
    # Mocks for documentation/virtual purposes if library is missing
    class ULRange:
        BIP10VOLTS = 1
    class DigitalIODirection:
        IN = 1
        OUT = 2
    class DigitalPortType:
        AUXPORT = 1
    class AnalogInputMode:
        SINGLE_ENDED = 1
        DIFFERENTIAL = 2

class USB231(Daq, Digilent):
    """
    Driver for the Measurement Computing (MCC) USB-231 Data Acquisition Device.
    
    Specifications sourced from the USB-231 User's Guide.
    """

    # --- Class Attributes ---
    
    # The USB-231 User's Guide does not list any SCPI commands or an *IDN? response 
    # [cite_start]as it uses the Universal Library[cite: 8].
    AUTODETECT_ID = None

    # Analog Input Attributes
    # [cite_start]"Eight single-ended (SE) or four differential (DIFF) 16-bit analog inputs" [cite: 49]
    # We list 0-7 to support Single-Ended mode.
    AI_channels = [0, 1, 2, 3, 4, 5, 6, 7]
    
    # [cite_start]"The input voltage range is ±10 V." [cite: 372]
    AI_ranges = [(-10.0, 10.0)]
    
    # [cite_start]"50 kS/s maximum sample rate" [cite: 50]
    # Note: This is an aggregate rate.
    AI_sample_rate = (0, 50000)

    # Analog Output Attributes
    # [cite_start]"Two analog outputs (AOUT0 and AOUT1)" [cite: 51]
    AO_channels = [0, 1]
    
    # [cite_start]"The AO range is ±10 V." [cite: 481]
    AO_ranges = [(-10.0, 10.0)]
    
    # [cite_start]"5 kS/s simultaneous update rate per channel maximum" [cite: 51]
    AO_sample_rate = (0, 5000)

    # Digital I/O Attributes
    # [cite_start]"Eight individually configurable digital I/O channels" [cite: 51]
    # [cite_start]"DIO0 through DIO7" [cite: 504]
    DIO_channels = [0, 1, 2, 3, 4, 5, 6, 7]
    
    # [cite_start]"Each digital I/O line is bit-configurable as input or output." [cite: 505]
    DIO_modes = ['INPUT', 'OUTPUT']

    def __init__(self, address, board_num=0, check_params=False, **kwargs):
        super().__init__(address, board_num, check_params, **kwargs)
        
        # Internal state tracking
        self._ai_channel = 0
        self._ao_channel = 0
        self._dio_channel = 0
        
        # [cite_start]Default to Single-Ended mode as it offers 8 channels [cite: 49]
        if not self.virtual:
            try:
                self.ul.a_input_mode(self.board_num, AnalogInputMode.SINGLE_ENDED)
            except Exception:
                pass

    # --- Analog Input Functions ---

    def set_AI_channel(self, channel):
        """
        Sets the Analog input channel for data acquisition.
        
        Args:
            [cite_start]channel (int): Channel index (0-7 for SE, 0-3 for DIFF)[cite: 49].
        """
        if channel in self.AI_channels:
            self._ai_channel = int(channel)
        else:
            raise ValueError(f"Invalid AI channel: {channel}. Must be in {self.AI_channels}")

    def set_AI_range(self, channel, range_val):
        """
        Sets the range for the Analog input channel.
        
        [cite_start]The USB-231 has a fixed input range of ±10 V[cite: 412].
        """
        # Hardware is fixed, so we just validate.
        expected_range = (-10.0, 10.0)
        if range_val != expected_range:
            print(f"Warning: USB-231 range is fixed at {expected_range} V. Request for {range_val} ignored.")
            
    def set_AI_sample_rate(self, channel, sample_rate):
        """
        Sets the sample rate for the Analog input channel.
        
        [cite_start]Max aggregate rate is 50 kS/s[cite: 50].
        """
        # This primarily applies to hardware paced scans. 
        # For single point acquisition (software paced), this setting is stored but not immediately used.
        if not (self.AI_sample_rate[0] <= sample_rate <= self.AI_sample_rate[1]):
            raise ValueError(f"Sample rate {sample_rate} out of bounds {self.AI_sample_rate}.")
        # Implementation for scan setup would occur in a scan-specific method (not defined in generic Daq).

    def configure_AI_channel(self, channel, range_val, sample_rate):
        """
        Calls the set_AI_channel, set_AI_range, and set_AI_sample_rate functions.
        """
        self.set_AI_channel(channel)
        self.set_AI_range(channel, range_val)
        self.set_AI_sample_rate(channel, sample_rate)

    # --- Analog Output Functions ---

    def set_AO_channel(self, channel):
        """
        Sets the Analog output channel for data output.
        
        Args:
            [cite_start]channel (int): 0 (AOUT0) or 1 (AOUT1)[cite: 168].
        """
        if channel in self.AO_channels:
            self._ao_channel = int(channel)
        else:
            raise ValueError(f"Invalid AO channel: {channel}. Must be in {self.AO_channels}")

    def set_AO_range(self, channel, range_val):
        """
        Sets the range for the Analog output channel.
        
        [cite_start]The USB-231 has a fixed output range of ±10 V[cite: 481].
        """
        expected_range = (-10.0, 10.0)
        if range_val != expected_range:
            print(f"Warning: USB-231 output range is fixed at {expected_range} V. Request for {range_val} ignored.")

    def set_AO_sample_rate(self, channel, sample_rate):
        """
        Sets the sample rate for the Analog output channel.
        
        [cite_start]Max 5 kS/s simultaneous per channel[cite: 51].
        """
        if not (self.AO_sample_rate[0] <= sample_rate <= self.AO_sample_rate[1]):
            raise ValueError(f"Sample rate {sample_rate} out of bounds {self.AO_sample_rate}.")

    def configure_AO_channel(self, channel, range_val, sample_rate):
        """
        Calls the set_AO_channel, set_AO_range, and set_AO_sample_rate functions.
        """
        self.set_AO_channel(channel)
        self.set_AO_range(channel, range_val)
        self.set_AO_sample_rate(channel, sample_rate)

    # --- Digital I/O Functions ---
    
    # [cite_start]The USB-231 has "Eight individually configurable digital I/O channels"[cite: 51].
    # Therefore, separate DI/DO lists are less relevant; we use the shared DIO logic.

    def set_DIO_channel(self, channel):
        """
        Sets the Digital input/output channel.
        
        Args:
            [cite_start]channel (int): 0-7[cite: 504].
        """
        if channel in self.DIO_channels:
            self._dio_channel = int(channel)
        else:
            raise ValueError(f"Invalid DIO channel: {channel}. Must be in {self.DIO_channels}")

    def set_DIO_mode(self, channel, mode):
        """
        Sets the mode for the Digital input/output channel (input or output).
        
        [cite_start]"Each digital I/O line is bit-configurable as input or output"[cite: 505].
        """
        if self.virtual: return

        direction = DigitalIODirection.IN
        if str(mode).upper() == 'OUTPUT':
            direction = DigitalIODirection.OUT
        elif str(mode).upper() != 'INPUT':
             raise ValueError(f"Invalid mode: {mode}. Must be 'INPUT' or 'OUTPUT'.")

        # Configure the specific bit using AUXPORT (standard for MCC DIO)
        try:
            self.ul.d_config_bit(self.board_num, DigitalPortType.AUXPORT, int(channel), direction)
        except Exception as e:
            print(f"Error configuring DIO bit {channel}: {e}")

    def set_DIO_sample_rate(self, channel, sample_rate):
        """
        Sets the sample rate for the Digital input/output channel.
        
        [cite_start]"All digital I/O updates and samples are software-paced."[cite: 508].
        """
        # Since it is software paced, the sample rate variable doesn't configure hardware timing.
        pass

    def configure_DIO_channel(self, channel, mode, sample_rate):
        """
        Calls the set_DIO_channel, set_DIO_mode, and set_DIO_sample_rate functions.
        """
        self.set_DIO_channel(channel)
        self.set_DIO_mode(channel, mode)
        self.set_DIO_sample_rate(channel, sample_rate)

    # --- Digital Input Only Wrappers ---
    def set_DI_channel(self, channel):
        self.set_DIO_channel(channel)
        self.set_DIO_mode(channel, 'INPUT')

    def set_DI_sample_rate(self, channel, sample_rate):
        self.set_DIO_sample_rate(channel, sample_rate)

    def configure_DI_channel(self, channel, sample_rate):
        self.configure_DIO_channel(channel, 'INPUT', sample_rate)

    # --- Digital Output Only Wrappers ---
    def set_DO_channel(self, channel):
        self.set_DIO_channel(channel)
        self.set_DIO_mode(channel, 'OUTPUT')

    def set_DO_sample_rate(self, channel, sample_rate):
        self.set_DIO_sample_rate(channel, sample_rate)

    def configure_DO_channel(self, channel, sample_rate):
        self.configure_DIO_channel(channel, 'OUTPUT', sample_rate)


    # --- Data Acquisition Functions ---

    def quick_read(self):
        """
        Quick read function that returns the default data (off of whatever is the default channel).
        Default behavior: Read Analog Input on current channel.
        """
        return self.read_AI(self._ai_channel)

    def read_data(self, channel):
        """
        Reads the data from the specified channel.
        
        If channel is in AI_channels, performs an AI read. 
        Logic differentiates based on usage, but since channels overlap (0-7), 
        this defaults to AI unless a DI-specific method is called.
        """
        return self.read_AI(channel)

    def read_AI(self, channel=None):
        """
        Reads the Analog input data from the specified channel.
        
        [cite_start]Acquires one analog sample (software paced mode)[cite: 124].
        """
        target_ch = int(channel) if channel is not None else self._ai_channel
        
        if self.virtual:
            return 0.0

        try:
            # v_in returns the voltage directly.
            # [cite_start]Range is fixed to ±10 V (BIP10VOLTS)[cite: 372].
            value = self.ul.v_in(self.board_num, target_ch, ULRange.BIP10VOLTS)
            return value
        except Exception as e:
            print(f"Error reading AI Channel {target_ch}: {e}")
            return float('nan')

    def read_DI(self, channel=None):
        """
        Reads the Digital input data from the specified channel.
        """
        target_ch = int(channel) if channel is not None else self._dio_channel
        
        if self.virtual:
            return 0

        try:
            # Read specific bit from AUXPORT
            value = self.ul.d_bit_in(self.board_num, DigitalPortType.AUXPORT, target_ch)
            return value
        except Exception as e:
            print(f"Error reading DI Channel {target_ch}: {e}")
            return 0

    # --- Output Functions ---

    def output(self, channel, on=True):
        """
        Turns the output on or off for the specified channel.
        
        For USB-231, this applies to Digital Output channels (0-7).
        """
        if self.virtual:
            print(f"USB231 [Virtual]: Output Ch {channel} -> {on}")
            return

        try:
            # Map boolean to bit value
            bit_val = 1 if on else 0
            # Write bit to AUXPORT
            self.ul.d_bit_out(self.board_num, DigitalPortType.AUXPORT, int(channel), bit_val)
        except Exception as e:
            print(f"Error setting Output Channel {channel}: {e}")

    # --- Custom Analog Output Write (Not in Daq outline but required for functionality) ---
    # The Daq outline 'output' function is boolean (On/Off). 
    # To support Analog Output voltage writing, we implement a specific method matching the class conventions.

    def write_AO(self, channel, voltage):
        """
        Writes a specific voltage to an Analog Output channel.
        
        Args:
            [cite_start]channel (int): 0 or 1[cite: 51].
            [cite_start]voltage (float): Value between -10.0 and 10.0[cite: 481].
        """
        if channel not in self.AO_channels:
            raise ValueError(f"Invalid AO channel: {channel}")
            
        if self.virtual:
            print(f"USB231 [Virtual]: Analog Write Ch {channel} -> {voltage} V")
            return

        # Enforce range limits
        if voltage > 10.0: voltage = 10.0
        if voltage < -10.0: voltage = -10.0

        try:
            # [cite_start]"Software-paced generations... typically used for writing a single value out"[cite: 492].
            self.ul.v_out(self.board_num, int(channel), ULRange.BIP10VOLTS, voltage)
        except Exception as e:
            print(f"Error writing AO Channel {channel}: {e}")