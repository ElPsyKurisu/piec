"""
A secondary is defined as an instrument that neither generates something nor measures something maybe peripheral (I like this one @alex thoughts?)
"""
from ..instrument import Instrument

class Secondary(Instrument):
    """
    Note as a secondary, this need not have any extra functionality than the base instrument class since at this level
    we do not know what this instrument should do.
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
        super().__init__(address)
    # No additional methods are defined as per the class docstring.