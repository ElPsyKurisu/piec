"""
Keithley 2400 Series SourceMeter implementation.
        
This module implements the Sourcemeter interface for the Keithley 2400
SourceMeter instrument using SCPI commands.
"""
from .sourcemeter import Sourcemeter
from ..scpi import Scpi

class Keithley2400(Sourcemeter, Scpi):
    # Class attributes defining the "contract" for any implementing class.
    AUTODETECT_ID = "MODEL 2400"  # Identifier string for the instrument
    # All sourcemeters must support these basic functions and modes.
    channel = [1]
    source_func = ['VOLT', 'CURR']
    sense_func = ['VOLT', 'CURR', 'RES']
    sense_mode = ['2W', '4W']
    voltage = (-210, 210) #check (volts)
    current = (-1.05, 1.05) # amps
    voltage_compliance = (-210, 210)
    current_compliance = (-1.05, 1.05)
 

    # --- Core Instrument State Control ---

    def output(self, on=True):
        """
        Turns the main output of the sourcemeter on or off.
        args:
            on (bool): True to enable the output, False to disable it.
        """
        state = "ON" if on else "OFF"
        self.instrument.write(f":OUTP {state}")

    def set_source_function(self, source_func):
        """
        Sets the primary function of the source.
        args:
            source_func (str): The source function, e.g., 'VOLT' or 'CURR'.
        """
        self.instrument.write(f":SOUR:FUNC {source_func.upper()}")

    def set_sense_function(self, sense_func):
        """
        Sets the measurement (sense) function.
        args:
            sense_func (str): The measurement function, e.g., 'VOLT', 'CURR', or 'RES'.
        """
        func_map = {
        'VOLT': 'VOLTage',
        'CURR': 'CURRent',
        'RES': 'RESistance'
        }
        scpi_func = func_map.get(sense_func.upper(), sense_func.upper())
        self.instrument.write(f':SENS:FUNC "{scpi_func}"')
        
    def set_sense_mode(self, sense_mode):
        """
        Sets the wiring configuration for sensing.
        args:
            sens_mode (str): The sense mode, '2W' (2-wire) or '4W' (4-wire).
        
        4W means remote sensing set to ON, 2W means OFF
        """
        state = "ON" if sense_mode.upper() == '4W' else "OFF"
        self.instrument.write(f":SYST:RSEN {state}")

    # --- Source Configuration Methods ---
    
    def set_source_voltage(self, voltage):
        """
        Sets the output level when in voltage source mode.
        args:
            voltage (float): The desired output voltage in Volts.
        """
        self.instrument.write(f":SOUR:VOLT:LEV {voltage}")
    
    def set_source_current(self, current):
        """
        Sets the output level when in current source mode.
        args:
            current (float): The desired output current in Amps.
        """
        self.instrument.write(f":SOUR:CURR:LEV {current}")

    def set_voltage_compliance(self, voltage_compliance):
        """
        Sets the voltage limit (compliance) when in current source mode.
        args:
            voltage_compliance (float): The maximum voltage allowed in Volts.
        """
        self.instrument.write(f":SENS:VOLT:PROT {voltage_compliance}")
    
    def set_current_compliance(self, current_compliance):
        """
        Sets the current limit (compliance) when in voltage source mode.
        args:
            current_compliance (float): The maximum current allowed in Amps.
        """
        self.instrument.write(f":SENS:CURR:PROT {current_compliance}")

    
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
        response = self.instrument.query(":READ?")
        # response returns "voltage,current,resistance,time,status"
        values = response.split(',')
        return float(values[0])

    def get_voltage(self):
        """
        Convenience function to specifically measure and return the voltage.
        returns:
            (float): The measured voltage in Volts.
        """
        self.instrument.write(':SENS:FUNC "VOLT"')
        response = self.instrument.query(":READ?")
        values = response.split(',')
        return float(values[0])

    def get_current(self):
        """
        Convenience function to specifically measure and return the current.
        returns:
            (float): The measured current in Amps.
        """
        self.instrument.write(':SENS:FUNC "CURR"')
        response = self.instrument.query(":READ?")
        # Current is the second returned element
        values = response.split(',')
        return float(values[1])
    def get_resistance(self):
        """
        Convenience function to measure and return resistance.        
        Returns:
            float: The measured resistance in Ohms.
        """
        self.instrument.write(':SENS:FUNC "RES"')
        response = self.instrument.query(":READ?")
        # Resistance is the third element
        values = response.split(',')
        return float(values[2])
