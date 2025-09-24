"""
This is an outline for a generic Digital Multimeter (DMM) driver class.

A DMM is defined as an instrument that performs measurements but does not
source power. It inherits from a base Instrument class.
"""

from ..instrument import Instrument

class DMM(Instrument):
    """
    Parent class for Digital Multimeters.
    
    This class defines the minimum required methods and attributes for a DMM driver.
    It focuses solely on measurement functions.
    """
    # --- Class Attributes ---
    # Defines the "contract" for any DMM driver that inherits from this class.
    
    channel = [1]
    
    # A generic set of base measurement functions common to most DMMs.
    # Specific drivers should override/extend this list.
    sense_func = ['VOLT', 'CURR', 'RES', 'DIOD', 'CONT', 'CAP']
    
    # Supported signal modes for voltage and current measurements.
    measurement_mode = ['DC', 'AC']

    # Supported wiring modes for resistance measurements.
    wire_mode = ['2W', '4W']
    
    # Placeholder for min/max measurement ranges.
    sense_range = (None, None)
    
    def __init__(self, address):
        """
        Initializes communication with the DMM.
        """
        super().__init__(address)

    # --- Core Measurement Configuration ---

    def set_sense_function(self, sens_func):
        """
        Sets the base measurement function of the DMM.
        Args:
            sens_func (str): The measurement function, e.g., 'VOLT', 'CURR', 'RES'.
        """
        raise NotImplementedError

    def set_measurement_mode(self, mode):
        """
        Sets the signal mode for the current function (e.g., AC or DC).
        This is typically applicable only for VOLT and CURR functions.
        Args:
            mode (str): The signal mode, e.g., 'AC' or 'DC'.
        """
        raise NotImplementedError

    def set_wire_mode(self, mode):
        """
        Sets the wiring configuration for resistance measurements.
        Args:
            mode (str): The wire mode, '2W' (2-wire) or '4W' (4-wire).
        """
        raise NotImplementedError

    def set_sense_range(self, range_val=None, auto=True):
        """
        Sets the measurement range for the current sense function.
        Args:
            range_val (float, optional): The fixed range value. Defaults to None.
            auto (bool): If True, enables autorange. If False, a fixed range is used.
        """
        raise NotImplementedError

    def set_integration_time(self, nplc=1):
        """
        Sets the measurement integration time in Number of Power Line Cycles (NPLC).
        A higher NPLC value increases accuracy and noise rejection but slows down
        the measurement speed.
        Args:
            nplc (float): The number of power line cycles (e.g., 0.1, 1, 10, 100).
        """
        raise NotImplementedError

    # --- Measurement (Read) Methods ---

    def quick_read(self):
        """
        Triggers and returns a single measurement for the currently configured function.
        Returns:
            (float): The measured value.
        """
        raise NotImplementedError

    def get_voltage(self, ac=False):
        """
        Convenience function to measure and return a voltage reading.
        Args:
            ac (bool): If True, configures for an AC voltage measurement. 
                         If False (default), configures for DC voltage.
        Returns:
            (float): The measured voltage in Volts.
        """
        raise NotImplementedError

    def get_current(self, ac=False):
        """
        Convenience function to measure and return a current reading.
        Args:
            ac (bool): If True, configures for an AC current measurement. 
                         If False (default), configures for DC current.
        Returns:
            (float): The measured current in Amps.
        """
        raise NotImplementedError

    def get_resistance(self, four_wire=False):
        """
        Convenience function to measure and return a resistance reading.
        Args:
            four_wire (bool): If True, performs a 4-wire measurement. 
                              If False (default), performs a 2-wire measurement.
        Returns:
            (float): The measured resistance in Ohms.
        """
        raise NotImplementedError

