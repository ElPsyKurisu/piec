"""
This is the outline for what the 81150a.py file should be like.

Note that we can use the Scpi class to handle all the scpi commands since in the manual it is stated that the 81150a supports SCPI commands.

"""

from ...awg import Awg
from .....scpi import Scpi
class Keysight81150a(Awg, Scpi):
    # Initializer / Instance attributes
    """
    The Keysight 81150a is an arbitrary waveform generator that can generate a wide range of waveforms.
    It is capable of generating waveforms with high precision and accuracy.
    """
    
