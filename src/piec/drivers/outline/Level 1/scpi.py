"""
This is an outline for what the scpi.py file should be like
"""

"""
This is the top level instrument that dictates if something is scpi, dac, arduino, etc.
"""
from .instrument import Instrument
class Scpi(Instrument):
    # Initializer / Instance attributes
    """
    All SCPI instruments must allow for all base SCPI commands to work!
    This is taken from scpi-99 standard and includes the IEEE Mandated Commands
    https://www.ivifoundation.org/downloads/SCPI/scpi-99.pdf
    """
    def __init__(self, address):
        """
        Opens the instrument and enables communication with it. In the case of SCPI, this is usually done over GPIB if possible, or USB, or Ethernet.
        The address is usually a string that represents the connection method and the address of the instrument (e.g. 'GPIB::1::INSTR', 'USB0::0x1234::0x5678::INSTR', etc.)
        Uses the built in PiecManager to handle the connection and communication with the instrument.
        """

    def idn(self):
        """
        Calls the *IDN? command to get the identification of the instrument. By default this should format the return string for better
        readability, but this can be overridden by the user if they want the raw string.
        """
    def reset(self):
        """
        Calls the *RST command to reset the instrument to its default state.
        This is useful for clearing any settings or configurations that may have been set previously.
        """
    def clear(self):
        """
        Calls the *CLS command to clear the instrument's status and error queue.
        This is useful for clearing any errors or messages that may have been generated by the instrument.
        """
    def error(self):
        """
        Calls the *ESR? command to get the instrument's error status register.
        This is useful for checking if there are any errors that need to be addressed.
        """
    def wait(self):
        """
        Calls the *WAI command to wait for the instrument to complete any pending operations.
        This is useful for ensuring that the instrument is ready before sending any further commands.
        """
    def self_test(self):
        """
        Calls the *TST? command to perform a self-test on the instrument.
        This is useful for checking if the instrument is functioning properly.
        """
    def operation_complete(self):
        """
        Calls the *OPC? command to check if the instrument has completed its last operation.
        This is useful for ensuring that the instrument is ready before sending any further commands.
        """
    
    #Utility Commadns
    def iniitialize(self):
        """
        Calls reset and clear commands to initialize the instrument.
        This is useful for ensuring that the instrument is in a known state before performing any operations.
        """
    