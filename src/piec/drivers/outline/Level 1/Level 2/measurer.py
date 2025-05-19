"""
This is an outline for what the measurer.py file should be like.

A measurer is defined as an instrument that measures something (e.g. a voltage/current)
"""
from .instrument import Instrument
class Measurer(Instrument):
    # Initializer / Instance attributes
    """
    All measurers must be able to read some data and give it to the computer
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
    
    def quick_read(self):
        """
        All measures must be able to read something, so therefore we need a method to read the data. It would be very beneficial to
        ensure that all Measurers have a utility command that quickly reads out the data that is displayed (or the current value etc)
        """

    