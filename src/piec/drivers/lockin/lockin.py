"""
This is an outline for what the lockin.py file should be like.

A lockin is defined as an instrument that has the typical features one expects a lockin to have
"""
from ..instrument import Instrument
class Lockin(Instrument):
    # Initializer / Instance attributes
    channel = ['1'] 
    reference_source = None
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
    def set_reference_source(self, reference_source):
        """
        Sets the reference source for the lockin. Typically this could be internal, external, or a specific channel

        args:
            reference_source (str): the source of the reference signal (e.g., "internal", "external", etc.)
        """
    
    #this is only if the lockin has a reference frequency, some lockins only have a reference source

    def set_reference_frequency(self, frequency):
        """
        Sets the reference frequency for the lockin if applicable (if internal reference)

        args:
            frequency (float): where unit is typically in Hz
        """
    def set_harmonic(self, harmonic):
        """
        Sets the harmonic for the lockin

        args:
            harmonic (int): the harmonic number to lock onto (e.g., 1, 2, 3, etc.)
        """
    def set_phase(self, phase):
        """
        Sets the phase for the lockin

        args:
            phase (float): the phase offset in degrees or radians
        """
    #signal input channel setup
    def set_input_configuration(self, configuration):
        """
        Sets the input configuration for the lockin (single ended, differential, etc.)

        args:
            configuration (str): the input configuration type
        """
    def set_input_coupling(self, coupling):
        """
        Sets the input coupling for the lockin (AC, DC, etc.)

        args:
            coupling (str): the input coupling type (e.g., "AC", "DC")
        """
    def set_sensitivity(self, sensitivity):
        """
        Sets the sensitivity for the lockin

        args:
            sensitivity (float): the sensitivity level for the lockin
        """
    def set_notch_filter(self, notch_filter):
        """
        Sets the notch filter for the lockin (if available)

        args:
            notch_filter (float): the frequency of the notch filter to be set
        """
    #demodulation and low-pass filter setup
    def set_time_constant(self, time_constant):
        """
        Sets the time constant for the lockin defines the cutoff frequency of the low-pass filter

        args:
            time_constant (float): the time constant value in seconds
        """
    def set_filter_slope(self, filter_slope):
        """
        Sets the filter slope for the lockin. Usually in dB/octave or dB/decade

        args:
            filter_slope (float): the slope of the filter in dB/octave or dB/decade
        """
    #data acquisition and output
    def quick_read(self):
        """
        Quick read function that returns the default data (X and Y typically)

        Returns:
            tuple: (X, Y) data from the lockin
        """

    def read_data(self):
        """
        Reads the data from the lockin, For a lockin this is typically X, Y, R and Theta

        Returns:
            dict: A dictionary containing the lockin data with keys 'X', 'Y', 'R', and 'Theta'
        """
    def get_X(self):
        """
        Reads the X data

        Returns:
            float: The X data from the lockin
        """
    def get_Y(self):
        """
        Reads the Y data
        Returns:
            float: The Y data from the lockin
        """
    def get_R(self):
        """
        Reads the R data
        Returns:
            float: The R (magnitude) data from the lockin
        """
    def get_theta(self):
        """
        Reads the Theta (phase)
        Returns:
            float: The Theta (phase) data from the lockin
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
    
    
