"""
This is the top level instrument that dictates if something is scpi, dac, arduino, etc.
"""
from pyvisa import ResourceManager

class Instrument:
    # Initializer / Instance attributes
    """
    All an instrument is required to have is an address! For now this will be split into 3 categories. SCPI, ARDUINO, and DIGILENT (MCCULW)
    Since a hypothetical instrument could have no idn commands or etc
    """
    def __init__(self, address):
        rm = ResourceManager()
        self.instrument = rm.open_resource(address)