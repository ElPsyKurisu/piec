"""
This is an outline for what the osc.py file should be like.

A osc (oscilloscope) is defined as an instrument that has the typical features on expects an oscilloscope to have
"""
from .measurer import Measurer
class Oscilloscope(Measurer):
    # Initializer / Instance attributes
    """
    All measurers must be able to read some data and give it to the computer
    """

    #These functions make the signal visible and are used on a per channel basis (aka channel independant)
    def toggle_channel(self, channel, on=True):
        """
        Function that toggles the selected channel to on or off (what to display and what to acquire)
        """

    def set_vertical_scale(self, channel, vdiv, range):
        """
        Function that sets the vertical scale in either volts per divison or absolute range
        """
    
    def set_vertical_position(self, channel, position):
        """
        Sets the vertical position of the scale (moves the waveform up and down)
        """
    
    def set_input_coupling(self, channel, coupling):
        """
        Sets the input coupling, e.g. AC, DC, Ground
        """
    
    def set_probe_attenuation(self, channel, probe_attenuation):
        """
        Sets the probe attenuation e.g. 1x, 10x etc
        """
    #Now we move too setting the time_window which is shared ACROSS channels

    def set_horizontal_scale(self, tdiv, range):
        """
        Sets the timebase in either time/division or in absolute range
        """
    def set_horizontal_position(self, position):
        """
        Changes the position (delay) of the timebase
        """

    def configure_horizontal(self, tdiv, range, position):
        """
        Combines into one function
        """
        self.set_horizontal_scale(tdiv, range)
        self.set_horizontal_position(position) #NOTE this is here to show that we dont need to make each function only do like a single thing still tbd

    #Now we can go to triggering

    def set_trigger_source(self, source):
        """
        Decides what the scope should trigger on
        """
    def set_trigger_level(self, level):
        """
        The voltage level the signal must cross to initiate a capture
        """
    def set_trigger_slope(self, slope):
        """
        Changes the trigger from falling, rising etc
        """
    def set_trigger_mode(self, mode):
        """
        Changes the mode from auto, norm, manual, single, etc
        """
    def configure_trigger(self, source, level, slope, mode):
        """
        Combines all the trigger commands into one
        """
        self.set_trigger_source(source)
        self.set_trigger_level(level)
        self.set_trigger_slope(slope)
        self.set_trigger_mode(mode)
    #Time to control acquisition process

    def toggle_acquisition(self, run=True):
        """
        Start or halt the process of capturing data
        """
    def arm(self):
        """
        Tells the scope to get ready to capture the data for the single shot etc
        """
    def configure_data(self, length):
        """
        Configures the scope (ideally in binary) to specific parameters such as length (how much data to capture), etc
        """
    #Time to get the data out NOTE: We already have from the measurer class the quick_read which technically goes under here
    def get_data(self):
        """
        Returns the data depending on how it was configured with the configure_data command
        """
    