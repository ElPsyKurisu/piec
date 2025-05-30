"""
This is an outline for what the generator.py file should be like.

A generator is defined as an instrument that generates something (e.g. a voltage/current)
"""
from ..instrument import Instrument
class Generator(Instrument):
    # Initializer / Instance attributes
    """
    All generators must be able to output something
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
    
    def output(self, channel, on=True):
        """
        All Generators must be able to output something, so therefore we need a method to turn the output on.
        """

    