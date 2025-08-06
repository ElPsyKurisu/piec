"""
This is an outline for what the puler.py file should be like.

A pulser is defined as an instrument that has the typical features one expects a pulser to have
"""
from ..generator import Generator
class Pulser(Generator):
    # Initializer / Instance attributes
    """
    All Pulsers must be able to generate a pulse. Assumes 50Ohm output impedance unless otherwise specified.
    """
    #Core Pulse timging parameters
    def set_period(self, period):
        """
        Sets the period of the pulse
        """
    def set_frequency(self, frequency):
        """
        Sets the frequency of the pulse, This can simply call set_pulse_period with conversion or vice versa
        """
    def set_width(self, width):
        """
        Sets the width of the pulse
        """
    def set_delay(self, delay):
        """
        Sets the delay before the pulse starts
        """
    def set_rise_time(self, rise_time):
        """
        Sets the rise time of the pulse
        """
    def set_fall_time(self, fall_time):
        """
        Sets the fall time of the pulse
        """
    #Core Pulse level parameters
    def set_high_level(self, high_level):
        """
        Sets the high level of the pulse
        """
    def set_low_level(self, low_level):
        """
        Sets the low level of the pulse
        """
    def set_offset(self, offset):
        """
        Sets the offset of the pulse
        """
    #Core Pulse output parameters
    def output(self, channel, on=True):
        """
        Turns the pulse output on or off for the specified channel
        """
    #triggering and mode
    def set_trigger_source(self, source):
        """
        Sets the trigger source for the pulse (e.g., internal, external, manual)
        """
    def set_trigger_mode(self, mode):
        """
        Sets the trigger mode for the pulse (e.g., single, continuous, burst)
        """
    #if the pulser has a burst mode
    def set_burst_count(self, count):
        """
        Sets the number of pulses in a burst
        """
    #basic pulse output functions
    def set_polarity(self, polarity):
        """
        Sets the polarity of the pulse output (e.g., normal, inverted)
        """
    