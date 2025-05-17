"""
This is an outline for what the secondary.py file should be like. NOTE: name is tbd

A secondary is defined as an instrument that neither generates something nor measures something maybe peripheral (I like this one @alex thoughts?)
"""
from .instrument import Instrument
class Secondary(Instrument):
    # Initializer / Instance attributes
    """
    Note as a secondary, this need not have any extra functionality than the base instrument class since at this level
    we do not know what this instrument should do.
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
    
    

    