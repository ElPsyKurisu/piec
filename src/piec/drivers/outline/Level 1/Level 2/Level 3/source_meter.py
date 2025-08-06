"""
This is an outline for what a sourcemeter.py file should be like.

A sourcemeter is defined as an instrument that can source voltage or current
and simultaneously measure voltage, current, and/or resistance.
"""
from ..measurer import Measurer

class SourceMeter(Measurer):
    """
    The SourceMeter class defines the interface for a generic source-measure unit (SMU).
    It inherits from the base Measurer class.
    """

    # Output/Source Configuration
    def toggle_output(self, on=True):
        """
        Toggles the output state of the source to be on or off.
        :param on: Boolean value to turn the output on (True) or off (False).
        """

    def set_source_function(self, function:str='voltage'):
        """
        Sets the source function, e.g., 'voltage' or 'current'.
        :param function: A string representing the source ('voltage' or 'current') to be set.
        """

    def set_source_level(self, level:float=0.0):
        """
        Sets the output level for the selected source function (e.g., 1.5 for 1.5V or 100e-6 for 100uA).
        :param level: Numeric value representing the output level for the source function.
        """

    def set_source_range(self, source_range='auto'):
        """
        Sets the source range. Can be set to 'auto' or a specific numeric value.
        :param source_range: A string 'auto' or a numeric value representing the source range.
        """

    def set_source_compliance(self, compliance=0.01):
        """
        Sets the compliance (protection limit) for the source. If sourcing voltage,
        this sets the current limit. If sourcing current, this sets the voltage limit.
        :pararm compliance: Numeric value representing the compliance limit for the source.
        """

    def configure_source(self, function='voltage', level=0.0, source_range='auto', compliance=0.01,):
        """
        Combines several source configuration commands into a single function.
        :param function: A string representing the source function ('voltage' or 'current').
        :param level: Numeric value representing the output level for the source function.
        :param compliance: Numeric value representing the compliance limit for the source.
        :param source_range: A string 'auto' or a numeric value representing the source range.
        """
        self.set_source_function(function)
        self.set_source_range(source_range)
        self.set_source_level(level)
        self.set_source_compliance(compliance)

    # Measurement/Sense Configuration
    def set_measure_function(self, function='current'):
        """
        Sets the measurement function, e.g., 'voltage', 'current', or 'resistance'.
        :param function: A string representing the measurement function to be set.
        """

    def set_measure_range(self, measure_range):
        """
        Sets the measurement range. Can be set to 'auto' or a specific numeric value.
        """

    def set_nplc(self, nplc):
        """
        Sets the integration time for a measurement in terms of Number of Power Line Cycles (NPLC).
        A higher value increases accuracy and noise reduction but slows down measurement speed.
        """
    
    def set_terminals(self, terminals):
        """
        Sets the measurement terminals, e.g. 'front' or 'rear', '2-wire' or '4-wire'.
        4-wire sensing is typically used for accurate low-resistance measurements.
        """

    def configure_sense(self, function, measure_range='auto', nplc=1):
        """
        Combines several measurement configuration commands into a single function.
        """
        self.set_measure_function(function)
        self.set_measure_range(measure_range)
        self.set_nplc(nplc)

    # --- Data Acquisition ---
    def quick_read(self):
        """
        Inherited from Measurer. Performs a single measurement with the current
        instrument configuration and returns the measured value.
        """

    def measure(self):
        """
        An alias for the quick_read() method for improved readability in context.
        """

