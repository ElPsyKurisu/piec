"""
A measurer is defined as an instrument that measures something (e.g. a voltage/current)
"""
from ..instrument import Instrument

class Measurer(Instrument):
    """
    All measurers must be able to read some data and give it to the computer
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
        super().__init__(address)
    
    def quick_read(self):
        """
        All measures must be able to read something, so therefore we need a method to read the data. It would be very beneficial to
        ensure that all Measurers have a utility command that quickly reads out the data that is displayed (or the current value etc)
        """
        # Using a general SCPI command to read a measurement.
        # Assumes self.instrument.query is available from the Instrument base class.
        return self.instrument.query("READ?")