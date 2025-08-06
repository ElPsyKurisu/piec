"""
This is an outline for what the lockin.py file should be like.

A lockin is defined as an instrument that has the typical features one expects a lockin to have
"""
from ..generator import Generator
from ..measurer import Measurer #NOTE Measurer is the main class for lockin
class Lockin(Measurer, Generator):
    # Initializer / Instance attributes
    """
    All lockins must be able to lockin to a signal and measure it
    """
    #configure the reference signal
    def set_reference_source(self, source):
        """
        Sets the reference source for the lockin. Typically this could be internal, external, or a specific channel
        """
    #this is only if the lockin has a reference frequency, some lockins only have a reference source

    def set_reference_frequency(self, frequency):
        """
        Sets the reference frequency for the lockin if applicable (if internal reference)
        """
    def set_harmonic(self, harmonic):
        """
        Sets the harmonic for the lockin
        """
    def set_phase(self, phase):
        """
        Sets the phase for the lockin
        """
    #signal input channel setup
    def set_input_configuration(self, channel, configuration):
        """
        Sets the input configuration for the lockin (single ended, differential, etc.)
        """
    def set_input_coupling(self, channel, coupling):
        """
        Sets the input coupling for the lockin (AC, DC, etc.)
        """
    def set_sensitivity(self, channel, sensitivity):
        """
        Sets the sensitivity for the lockin (volts, amps, etc.)
        """
    def set_notch_filter(self, channel, notch_filter):
        """
        Sets the notch filter for the lockin (if available)
        """
    #demodulation and low-pass filter setup
    def set_time_constant(self, channel, time_constant):
        """
        Sets the time constant for the lockin defines the cutoff frequency of the low-pass filter
        """
    def set_filter_slope(self, channel, slope):
        """
        Sets the filter slope for the lockin (e.g., 6 dB/octave, 12 dB/octave)
        """
    #data acquisition and output
    def quick_read(self):
        """
        Quick read function that returns the default data (X and Y typically)
        """
    def read_data(self, channel):
        """
        Reads the data from the specified channel, For a lockin this is typically X, Y, R and Theta
        """
    def read_X(self, channel):
        """
        Reads the X data from the specified channel
        """
    def read_Y(self, channel):
        """
        Reads the Y data from the specified channel
        """
    def read_R(self, channel):
        """
        Reads the R data from the specified channel
        """
    def read_theta(self, channel):
        """
        Reads the Theta (phase) data from the specified channel
        """
    #auto commands
    def auto_gain(self, channel):
        """
        Automatically sets the gain (sensitivity) for the specified channel based on the input signal
        """
    def auto_phase(self, channel):
        """
        Automatically sets the phase for the specified channel based on the input signal
        """
    
    
