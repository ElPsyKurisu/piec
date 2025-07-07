"""
This is an outline for what the lockin.py file should be like.

A lockin is defined as an instrument that has the typical features one expects a lockin to have
"""
from ..generator import Generator
from ..measurer import Measurer #NOTE Measurer is the main class for lockin
class Lockin(Measurer, Generator):
    # Initializer / Instance attributes
    channel = ['1'] 
    source = None
    frequency = (None, None) 
    harmonic = None
    phase = (None, None) 
    input_configuration = None
    input_coupling = ["AC", "DC"]
    sensitivity = (None, None) 
    notch_filter = (None, None)
    time_constant = (None, None)
    filter_slope = (None, None)


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
    def set_input_configuration(self, configuration):
        """
        Sets the input configuration for the lockin (single ended, differential, etc.)
        """
    def set_input_coupling(self, coupling):
        """
        Sets the input coupling for the lockin (AC, DC, etc.)
        """
    def set_sensitivity(self, sensitivity):
        """
        Sets the sensitivity for the lockin (volts, amps, etc.)
        """
    def set_notch_filter(self, notch_filter):
        """
        Sets the notch filter for the lockin (if available)
        """
    #demodulation and low-pass filter setup
    def set_time_constant(self, time_constant):
        """
        Sets the time constant for the lockin defines the cutoff frequency of the low-pass filter
        """
    def set_filter_slope(self, filter_slope):
        """
        Sets the filter slope for the lockin. Usually in dB/octave or dB/decade
        """
    #data acquisition and output
    def quick_read(self):
        """
        Quick read function that returns the default data (X and Y typically)
        """

    def read_data(self):
        """
        Reads the data from the lockin, For a lockin this is typically X, Y, R and Theta
        """
    def read_X(self):
        """
        Reads the X data 
        """
    def read_Y(self):
        """
        Reads the Y data
        """
    def read_R(self):
        """
        Reads the R data
        """
    def read_theta(self):
        """
        Reads the Theta (phase)
        """
    #auto commands
    def auto_gain(self):
        """
        Automatically sets the gain (sensitivity) based on the input signal
        """
    def auto_phase(self):
        """
        Automatically sets the phase based on the input signal
        """
    
    
