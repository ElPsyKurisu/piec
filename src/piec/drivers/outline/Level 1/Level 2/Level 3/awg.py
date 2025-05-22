"""
This is an outline for what the osc.py file should be like.

A osc (oscilloscope) is defined as an instrument that has the typical features on expects an oscilloscope to have
"""
from ..generator import Generator
class Awg(Generator):
    # Initializer / Instance attributes
    """
    All awgs must be able to generate an arbitrary waveform and output it to the selected channel
    """

    #core output channel control functions
    def select_channel(self, channel, on=True):
        """
        Function that toggles the selected channel to on or off (what to display and what to acquire)
        """

    def output(self, channel, on=True):
        """
        All awgs must be able to output something, so therefore we need a method to turn the output on for the selected channel
        """
    
    #Standard waveform configuration functions
    def set_waveform(self, channel, waveform):
        """
        Sets the waveform to be generated on the selected channel either built in or user defined
        """
    def set_frequency(self, channel, frequency):
        """
        Sets the frequency of the waveform to be generated on the selected channel
        """
    def set_delay(self, channel, delay):
        """
        Sets the delay of the waveform to be generated on the selected channel
        """
    def set_amplitude(self, channel, amplitude):
        """
        Sets the amplitude of the waveform to be generated on the selected channel
        """
    def set_offset(self, channel, offset):
        """
        Sets the offset of the waveform to be generated on the selected channel
        """
    def set_load_impedance(self, channel, load_impedance):
        """
        Sets the load impedance of the waveform to be generated on the selected channel
        """
    def set_source_impedance(self, channel, source_impedance):
        """
        Sets the source impedance of the waveform to be generated on the selected channel
        """
    def set_polarity(self, channel, polarity):
        """
        Sets the polarity of the waveform to be generated on the selected channel
        """

    #functions that are specific to waveform types

    #First for square waves
    def set_duty_cycle(self, channel, duty_cycle):
        """
        Sets the duty cycle of the waveform to be generated on the selected channel
        Useful for square waves
        """
    #Now for triangular and ramp waves
    def set_symmetry(self, channel, symmetry):
        """
        Sets the symmetry of the waveform to be generated on the selected channel
        Useful for triangular and ramp waves
        """
    #Now for pulses
    def set_pulse_width(self, channel, pulse_width):
        """
        Sets the pulse width of the waveform to be generated on the selected channel
        Useful for pulses
        """
    def set_pulse_rise_time(self, channel, rise_time):
        """
        Sets the rise time of the waveform to be generated on the selected channel
        Useful for pulses
        """
    def set_pulse_fall_time(self, channel, fall_time):
        """
        Sets the fall time of the waveform to be generated on the selected channel
        Useful for pulses
        """

    #Now we move to the arb functions
    def create_arb_waveform(self, channel, waveform):
        """
        Creates an arbitrary waveform to be generated on the selected channel
        """
    def set_arb_waveform(self, channel, waveform):
        """
        Sets the arbitrary waveform to be generated on the selected channel
        """
    
    #modulation functions
    #skip for now, not needed yet

    #burst and sweep functions
    #skip for now, not needed yet

    #trigger and sync functions
    def set_trigger_source(self, channel, source):
        """
        Sets the trigger source for the selected channel
        """
    def set_trigger_level(self, channel, level):
        """
        Sets the trigger level for the selected channel
        """
    def set_trigger_slope(self, channel, slope):
        """
        Sets the trigger slope for the selected channel
        """
    def set_trigger_mode(self, channel, mode):
        """
        Sets the trigger mode for the selected channel
        """
    #maybe impedance for trigger as well? But maybe some wont have this
    

