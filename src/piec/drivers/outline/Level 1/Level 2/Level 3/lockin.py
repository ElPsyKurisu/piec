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
        Sets the reference source for the lockin
        """
    #this is only if the lockin has a reference frequency, some lockins only have a reference source

    def set_reference_frequency(self, frequency):
        """
        Sets the reference frequency for the lockin
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
    
