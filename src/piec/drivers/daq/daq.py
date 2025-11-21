"""
A DAQ (Data Acquisition System) is defined as an instrument capable of converting 
analog physical signals to digital values (Input) and/or digital values to analog signals (Output).
"""
from ..instrument import Instrument 

class Daq(Instrument):
    # --- Class Attributes (Hardware Capabilities) ---
    # Valid integer channel numbers. Empty list [] implies feature not supported.
    ai_channel = [1] 
    ao_channel = [1] 
    dio_channel = [1]
    
    # Supported voltage ranges as (min, max) tuples. 
    # Essential for scaling raw bits to real-world units.
    ai_range = [(None, None)] 
    ao_range = [(None, None)]

    # Supported Analog Input Modes
    # 'SE' = Single-Ended, 'DIFF' = Differential
    ai_mode = ['SE', 'DIFF']
    # Logic directions supported by digital ports
    # 'IN' = Input, 'OUT' = Output, 'INOUT' = Configurable
    dio_direction = ['I', 'O']
    
    """
    The Heart of the DAQ: Reading and Writing.
    All DAQs must be able to perform immediate (software-paced) I/O.
    """

    # --- Analog I/O ---

    def read_analog(self, ai_channel):
        """
        Reads a single float value (voltage) from the specified Analog Input channel.
        This is the fundamental 'Get Data' command.
        args:
            ai_channel (int): The channel to read from
        returns:
            float: The measured value in Volts
        """

    def write_analog(self, ao_channel, value):
        """
        Writes a single float value (voltage) to the specified Analog Output channel.
        This is the fundamental 'Set Output' command.
        args:
            ao_channel (int): The channel to write to
            value (float): The voltage to output
        """

    def set_ai_range(self, ai_channel, ai_range):
        """
        Configures the gain/range for an Analog Input channel. 
        Required because measurement resolution depends on this.
        args:
            ai_channel (int): The channel to configure
            ai_range (tuple): The (min, max) range desired (e.g. (-10, 10))
        """

    def set_ao_range(self, ao_channel, ao_range):
        """
        Configures the output range for an Analog Output channel.
        args:
            a0_channel (int): The channel to configure
            ao_range (tuple): The (min, max) range desired
        """
    
    def set_input_mode(self, ai_mode):
        """
        Configures the Analog Input Mode (Single-Ended vs Differential).
        This changes the physical routing of the input pins. 
        NOTE: Some DAQs have fixed modes and cannot change this.
        
        args:
            ai_mode (str): 'SE' (Single-Ended) or 'DIFF' (Differential)
        """
        # Default implementation for fixed-mode DAQs. 
        # If a child class does not override this, we warn the user but do not crash.
        print(f"Warning: {self.__class__.__name__} does not support switching Input Modes (Fixed hardware).")

    # --- Digital I/O ---

    def read_digital(self, dio_channel):
        """
        Reads the state of a digital channel.
        args:
            dio_channel (int): The channel to read
        returns:
            int: 1 (High) or 0 (Low)
        """

    def write_digital(self, dio_channel, state):
        """
        Sets the state of a digital output channel.
        args:
            dio_channel (int): The channel to write to
            state (int/bool): 1/True for High, 0/False for Low
        """

    def set_dio_direction(self, dio_channel, direction):
        """
        Configures the physics of the digital pin (Input vs Output).
        Essential because writing to an Input pin can damage hardware.
        args:
            dio_channel (int): The channel to configure
            direction (str): 'IN' or 'OUT'
        """

    # --- Configuration Wrappers ---
    #NOTE: These seem useless
    
    def configure_ai(self, ai_channel, ai_range=None):
        """
        Helper to configure an AI channel in one line.
        """
        if ai_range is not None:
            self.set_ai_range(ai_channel, ai_range)

    def configure_ao(self, ao_channel, ao_range=None):
        """
        Helper to configure an AO channel in one line.
        """
        if ao_range is not None:
            self.set_ao_range(ao_channel, ao_range)

    def configure_dio(self, dio_channel, dio_direction=None):
        """
        Helper to configure a DIO channel in one line.
        """
        if dio_direction is not None:
            self.set_dio_direction(dio_channel, dio_direction)