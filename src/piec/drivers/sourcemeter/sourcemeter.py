"""
This is an outline for what the sourcemeter.py file should be like.

A sourcemeter is defined as an instrument that has the typical features one expects a sourcemeter to have
"""
from ..instrument import Instrument

class Sourcemeter(Instrument):
    # Class attributes defining the "contract" for any implementing class.
    # All sourcemeters must support these basic functions and modes.
    channel = [1]
    source_func = ['VOLT', 'CURR']
    sense_func = ['VOLT', 'CURR', 'RES']
    mode = ['2W', '4W'] #the sense mode
    voltage = (None, None)
    current = (None, None)
    voltage_compliance = (None, None)
    current_compliance = (None, None)
    
    """
    Here we define the MINIMUM required methods for a sourcemeter.
    """
    def __init__(self, address):
        super().__init__(address)

    # --- Core Instrument State Control ---

    def output(self, on=True):
        """
        Turns the main output of the sourcemeter on or off.
        args:
            on (bool): True to enable the output, False to disable it.
        """

    def set_source_function(self, source_func):
        """
        Sets the primary function of the source.
        args:
            source_func (str): The source function, e.g., 'VOLT' or 'CURR'.
        """

    def set_sense_function(self, sens_func):
        """
        Sets the measurement (sense) function.
        args:
            sens_func (str): The measurement function, e.g., 'VOLT', 'CURR', or 'RES'.
        """
        
    def set_sense_mode(self, mode):
        """
        Sets the wiring configuration for sensing.
        args:
            mode (str): The sense mode, '2W' (2-wire) or '4W' (4-wire).
        """

    # --- Source Configuration Methods ---
    
    def set_source_voltage(self, voltage):
        """
        Sets the output level when in voltage source mode.
        args:
            voltage (float): The desired output voltage in Volts.
        """
    
    def set_source_current(self, current):
        """
        Sets the output level when in current source mode.
        args:
            current (float): The desired output current in Amps.
        """

    def set_voltage_compliance(self, voltage_compliance):
        """
        Sets the voltage limit (compliance) when in current source mode.
        args:
            voltage_compliance (float): The maximum voltage allowed in Volts.
        """
    
    def set_current_compliance(self, current_compliance):
        """
        Sets the current limit (compliance) when in voltage source mode.
        args:
            current_compliance (float): The maximum current allowed in Amps.
        """
    
    # --- Convenience Configuration Methods ---

    def configure_voltage_source(self, voltage, current_compliance):
        """
        Configures the sourcemeter to source voltage with a specified compliance current.
        args:
            voltage (float): The voltage to source in Volts.
            current_compliance (float): The current compliance limit in Amps.
        """
        self.set_source_function('VOLT')
        self.set_source_voltage(voltage)
        self.set_current_compliance(current_compliance)

    def configure_current_source(self, current, voltage_compliance):
        """
        Configures the sourcemeter to source current with a specified compliance voltage.
        args:
            current (float): The current to source in Amps.
            voltage_compliance (float): The voltage compliance limit in Volts.
        """
        self.set_source_function('CURR')
        self.set_source_current(current)
        self.set_voltage_compliance(voltage_compliance)

    # --- Measurement (Read) Methods ---

    def quick_read(self):
        """
        Quickly returns the value for the currently configured sense function or whatever is on the screen.
        returns:
            (float): The measured value (Volts, Amps, or Ohms).
        """

    def get_voltage(self):
        """
        Convenience function to specifically measure and return the voltage.
        returns:
            (float): The measured voltage in Volts.
        """

    def get_current(self):
        """
        Convenience function to specifically measure and return the current.
        returns:
            (float): The measured current in Amps.
        """

