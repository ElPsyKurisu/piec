"""
A DAQ (Data Acquisition System) is defined as an instrument capable of converting 
analog physical signals to digital values (Input) and/or digital values to analog signals (Output).
"""
from ..instrument import Instrument 

class Daq(Instrument):
    # --- Class Attributes (Hardware Capabilities) ---
    # Valid integer channel numbers. Empty list [] implies feature not supported.
    ai_channels = [1] 
    ao_channels = [1] 
    dio_channels = [1]
    
    # Supported voltage ranges as (min, max) tuples. 
    # Essential for scaling raw bits to real-world units.
    ai_ranges = [(None, None)] 
    ao_ranges = [(None, None)]
    
    # Logic directions supported by digital ports
    # 'IN' = Input, 'OUT' = Output, 'INOUT' = Configurable
    dio_directions = ['I', 'O']
    
    """
    The Heart of the DAQ: Reading and Writing.
    All DAQs must be able to perform immediate (software-paced) I/O.
    """

    # --- Analog I/O ---

    def read_analog(self, channel):
        """
        Reads a single float value (voltage) from the specified Analog Input channel.
        This is the fundamental 'Get Data' command.
        args:
            channel (int): The channel to read from
        returns:
            float: The measured value in Volts
        """

    def write_analog(self, channel, value):
        """
        Writes a single float value (voltage) to the specified Analog Output channel.
        This is the fundamental 'Set Output' command.
        args:
            channel (int): The channel to write to
            value (float): The voltage to output
        """

    def set_ai_range(self, channel, voltage_range):
        """
        Configures the gain/range for an Analog Input channel. 
        Required because measurement resolution depends on this.
        args:
            channel (int): The channel to configure
            voltage_range (tuple): The (min, max) range desired (e.g. (-10, 10))
        """

    def set_ao_range(self, channel, voltage_range):
        """
        Configures the output range for an Analog Output channel.
        args:
            channel (int): The channel to configure
            voltage_range (tuple): The (min, max) range desired
        """

    # --- Digital I/O ---

    def read_digital(self, channel):
        """
        Reads the state of a digital channel.
        args:
            channel (int): The channel to read
        returns:
            int: 1 (High) or 0 (Low)
        """

    def write_digital(self, channel, state):
        """
        Sets the state of a digital output channel.
        args:
            channel (int): The channel to write to
            state (int/bool): 1/True for High, 0/False for Low
        """

    def set_dio_direction(self, channel, direction):
        """
        Configures the physics of the digital pin (Input vs Output).
        Essential because writing to an Input pin can damage hardware.
        args:
            channel (int): The channel to configure
            direction (str): 'IN' or 'OUT'
        """

    # --- Configuration Wrappers ---
    
    def configure_ai(self, channel, voltage_range=None):
        """
        Helper to configure an AI channel in one line.
        """
        if voltage_range is not None:
            self.set_ai_range(channel, voltage_range)

    def configure_ao(self, channel, voltage_range=None):
        """
        Helper to configure an AO channel in one line.
        """
        if voltage_range is not None:
            self.set_ao_range(channel, voltage_range)

    def configure_dio(self, channel, direction=None):
        """
        Helper to configure a DIO channel in one line.
        """
        if direction is not None:
            self.set_dio_direction(channel, direction)