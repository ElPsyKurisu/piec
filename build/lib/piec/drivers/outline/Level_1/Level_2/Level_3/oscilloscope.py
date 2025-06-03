"""
This is an outline for what the osc.py file should be like.

A osc (oscilloscope) is defined as an instrument that has the typical features on expects an oscilloscope to have
"""
from ..measurer import Measurer
class Oscilloscope(Measurer):
    # Initializer / Instance attributes
    """
    All measurers must be able to read some data and give it to the computer
    """

    #These functions make the signal visible and are used on a per channel basis (aka channel dependant)
    def toggle_channel(self, channel, on=True):
        """
        Function that toggles the selected channel to on or off (what to display and what to acquire)
        args:
            channel (int): The channel to toggle
            on (bool): True to turn on, False to turn off
        """

    def set_vertical_scale(self, channel, vdiv, range):
        """
        Function that sets the vertical scale in either volts per divison or absolute range
        args:
            channel (int): The channel to set the vertical scale on
            vdiv (float): The volts per division setting
            range (float): The absolute range in volts
        """
    
    def set_vertical_position(self, channel, position):
        """
        Sets the vertical position of the scale (moves the waveform up and down)
        args:
            channel (int): The channel to set the vertical position on
            position (float): The vertical position in volts
        """
    
    def set_input_coupling(self, channel, coupling):
        """
        Sets the input coupling, e.g. AC, DC, Ground
        args:
            channel (int): The channel to set the input coupling on
            coupling (str): The input coupling type, e.g. 'AC', 'DC', 'GND'
        """
    
    def set_probe_attenuation(self, channel, probe_attenuation):
        """
        Sets the probe attenuation e.g. 1x, 10x etc
        args:
            channel (int): The channel to set the probe attenuation on
            probe_attenuation (int): The probe attenuation factor, e.g. 1 for 1x, 10 for 10x
        """
    #Now we move too setting the time_window which is shared ACROSS channels

    def set_horizontal_scale(self, tdiv, range):
        """
        Sets the timebase in either time/division or in absolute range
        args:
            tdiv (float): The time per division setting
            range (float): The absolute time range in seconds
        """
    def set_horizontal_position(self, position):
        """
        Changes the position (delay) of the timebase
        args:
            position (float): The horizontal position in seconds
        """

    def configure_horizontal(self, tdiv, range, position):
        """
        Combines into one function calls set_horizontal_scale and set_horizontal_position
        args:
            tdiv (float): The time per division setting
            range (float): The absolute time range in seconds
            position (float): The horizontal position in seconds
        """
        

    #Now we can go to triggering

    def set_trigger_source(self, source):
        """
        Decides what the scope should trigger on
        args:
            source (str): The trigger source, e.g. 'CH1', 'CH2', 'EXT', 'INT'
        """
    def set_trigger_level(self, level):
        """
        The voltage level the signal must cross to initiate a capture
        args:
            level (float): The trigger level in volts
        """
    def set_trigger_slope(self, slope):
        """
        Changes the trigger from falling, rising etc
        args:
            slope (str): The trigger slope, e.g. 'rising', 'falling'
        """
    def set_trigger_mode(self, mode):
        """
        Changes the mode from auto, norm, manual, single, etc
        args:
            mode (str): The trigger mode, e.g. 'auto', 'normal', 'single'
        """
    def configure_trigger(self, source, level, slope, mode):
        """
        Combines all the trigger commands into one, calls set_trigger_source, set_trigger_level, set_trigger_slope, and set_trigger_mode
        args:
            source (str): The trigger source, e.g. 'CH1', 'CH2', 'EXT', 'INT'
            level (float): The trigger level in volts
            slope (str): The trigger slope, e.g. 'rising', 'falling'
            mode (str): The trigger mode, e.g. 'auto', 'normal', 'single'
        """

    #Time to control acquisition process

    def toggle_acquisition(self, run=True):
        """
        Start or halt the process of capturing data
        args:
            run (bool): True to start acquisition, False to halt it
        """
    def arm(self):
        """
        Tells the scope to get ready to capture the data for the single shot etc
        """
    def configure_data(self, length):
        """
        Configures the scope (ideally in binary) to specific parameters such as length (how much data to capture), etc
        args:
            length (int): The number of data points to capture
        """
    #Time to get the data out NOTE: We already have from the measurer class the quick_read which technically goes under here
    def quick_read(self):
        """
        Quick read function that returns the default data in a quick way (ideally in binary). Typically this should be used to get a snapshot of the current waveform (e.g. the current display).
        
        args:
            None
        Returns:
            data (Dataframe): Returns the data in a quick way, typically in binary format.
        """
    def get_data(self):
        """
        Returns the data depending on how it was configured with the configure_data command.
        Returns the data in a structured format, typically in a Pandas DataFrame that dispalys the time and voltage values in a structured way across all captured channels.
        args:
            None
        Returns:
            data (Dataframe): Returns the data in a stuctured format, in a Pandas DataFrame or similar structure.
        """
    