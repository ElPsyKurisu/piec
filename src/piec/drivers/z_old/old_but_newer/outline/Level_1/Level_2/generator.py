"""
A generator is defined as an instrument that generates something (e.g. a voltage/current)
"""
from ..instrument import Instrument

class Generator(Instrument):
    """
    All generators must be able to output something
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. Still communication method agnostic at this level
        """
        super().__init__(address)
    
    def output(self, channel, on=True):
        """
        All Generators must be able to output something, so therefore we need a method to turn the output on.
        """
        state = "ON" if on else "OFF"
        # Using a common SCPI format for controlling output state per channel.
        # Assumes self.instrument.write is available from the Instrument base class.
        self.instrument.write(f"OUTP{channel}:STAT {state}")