"""
This is an outline for what the instrument.py file should be like
"""

"""
This is the top level instrument that dictates if something is scpi, dac, arduino, etc.
"""
#good
class Instrument:
    # Initializer / Instance attributes
    """
    All an instrument is required to have is an address! For now this will be split into 3 categories. SCPI, ARDUINO, and DIGILENT (MCCULW)
    Since a hypothetical instrument could have no idn commands or etc
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it.
        """

    def idn(self):
        """
        At minimum ANY instrument in PIEC should be able to be id'd For custom instruments may require
        python to handle it if a built in low level command is not available.
        """