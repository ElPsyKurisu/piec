"""
Virtual Keithley 2400 SourceMeter Module

This module provides a virtual implementation of the Keithley 2400 SourceMeter
for simulation and testing purposes. It mimics the behavior of a physical
instrument by maintaining internal state and generating simulated measurements.
"""

import numpy as np

from ..virtual_instrument import VirtualInstrument
from .sourcemeter import Sourcemeter
from ..scpi import Scpi


class VirtualKeithley2400(VirtualInstrument, Sourcemeter, Scpi):
    """
    Virtual version of the Keithley 2400 SourceMeter for simulation/testing.

    This class stores state internally and generates synthetic measurement data.
    It follows the same interface as the real Keithley2400 driver, allowing
    seamless switching between virtual and physical instruments.

    """

    channel = [1]
    source_func = ['VOLT', 'CURR']
    sense_func = ['VOLT', 'CURR', 'RES']
    sense_mode = ['2W', '4W']
    voltage = (-210, 210)  # Volts
    current = (-1.05, 1.05)  # Amps
    voltage_compliance = (-210, 210)
    current_compliance = (-1.05, 1.05)

    def __init__(self, address='VIRTUAL'):
        """
        Initialize the virtual Keithley 2400 with default settings.

        Args:
            address (str): Virtual address for the instrument (default: 'VIRTUAL')
        """
        VirtualInstrument.__init__(self, address=address)

        self.instrument = self

        # Internal state dictionary to track all instrument settings
        self.state = {
            'output_on': False,

            'source_func': 'VOLT', 
            'source_voltage': 0.0,  # Volts
            'source_current': 0.0,  # Amps

            'sense_func': 'VOLT', 
            'sense_mode': '2W',  

            'voltage_compliance': 210.0,  # Volts
            'current_compliance': 1.05,  # Amps

            # Simulated load 
            'load_resistance': 1000.0,  # Ohms 
        }

        # Noise parameters for realistic measurements
        self._voltage_noise = 1e-4  
        self._current_noise = 1e-7 
        self._resistance_noise = 0.01  

    def idn(self):
        """
        Get the identification string of the virtual sourcemeter.

        Returns:
            str: Identification string mimicking real Keithley 2400 format
        """
        return "Virtual Keithley 2400"

    # --- Minimal SCPI Interface for Virtual Mode ---

    def write(self, command):
        """
        This method parses common Keithley 2400 SCPI commands and updates
        the internal state accordingly. Unrecognized commands are ignored.

        Args:
            command (str): SCPI command string to process
        """
        cmd = command.upper().strip()

        # Output control
        if ':OUTP' in cmd:
            self.state['output_on'] = 'ON' in cmd

        # Source function
        elif ':SOUR:FUNC' in cmd:
            if 'VOLT' in cmd:
                self.state['source_func'] = 'VOLT'
            elif 'CURR' in cmd:
                self.state['source_func'] = 'CURR'

        # Source voltage level
        elif ':SOUR:VOLT:LEV' in cmd:
            try:
                value = self._extract_value(cmd)
                self.state['source_voltage'] = np.clip(value, *self.voltage)
            except ValueError:
                pass

        # Source current level
        elif ':SOUR:CURR:LEV' in cmd:
            try:
                value = self._extract_value(cmd)
                self.state['source_current'] = np.clip(value, *self.current)
            except ValueError:
                pass

        # Sense function
        elif ':SENS:FUNC' in cmd:
            if 'VOLT' in cmd:
                self.state['sense_func'] = 'VOLT'
            elif 'CURR' in cmd:
                self.state['sense_func'] = 'CURR'
            elif 'RES' in cmd:
                self.state['sense_func'] = 'RES'

        # Voltage compliance 
        elif ':SENS:VOLT:PROT' in cmd:
            try:
                value = self._extract_value(cmd)
                self.state['voltage_compliance'] = np.clip(value, *self.voltage_compliance)
            except ValueError:
                pass

        # Current compliance
        elif ':SENS:CURR:PROT' in cmd:
            try:
                value = self._extract_value(cmd)
                self.state['current_compliance'] = np.clip(value, *self.current_compliance)
            except ValueError:
                pass

        # Remote sensing (4-wire mode)
        elif ':SYST:RSEN' in cmd:
            self.state['sense_mode'] = '4W' if 'ON' in cmd else '2W'

        # Reset command
        elif cmd == '*RST':
            self.reset()

        # Clear command 
        elif cmd == '*CLS':
            pass

    def query(self, command):
        """
        This method handles common Keithley 2400 SCPI queries and returns
        appropriate responses including simulated measurement data.

        Args:
            command (str): SCPI query command string

        Returns:
            str: Response string appropriate for the query
        """
        cmd = command.upper().strip()

        # Standard SCPI queries
        if cmd == '*IDN?':
            return self.idn()
        elif cmd == '*ESR?':
            return '0'
        elif cmd == '*OPC?':
            return '1'

        # Read measurement - returns "voltage,current,resistance,time,status"
        elif ':READ?' in cmd:
            return self._generate_measurement_string()

        # Query source voltage
        elif ':SOUR:VOLT:LEV?' in cmd:
            return str(self.state['source_voltage'])

        # Query source current
        elif ':SOUR:CURR:LEV?' in cmd:
            return str(self.state['source_current'])

        # Query output state
        elif ':OUTP?' in cmd:
            return '1' if self.state['output_on'] else '0'

        # Default empty response
        return ''

    def _extract_value(self, command):
        """
        Extract a numeric value from a SCPI command string.

        Args:
            command (str): SCPI command containing a numeric value

        Returns:
            float: Extracted numeric value
        """
        # Split by common delimiters and find the last numeric part
        parts = command.replace(':', ' ').replace(',', ' ').split()
        for part in reversed(parts):
            try:
                return float(part)
            except ValueError:
                continue
        raise ValueError(f"No numeric value found in command: {command}")

    def _generate_measurement_string(self):
        """
        The Keithley 2400 returns data in the format:
        "voltage,current,resistance,time,status"

        This method simulates realistic measurements based on current
        source settings and a virtual load resistance.

        Returns:
            str: Comma-separated measurement values
        """
        voltage, current, resistance = self._simulate_measurement()
        time_stamp = 0.0  # Simulated timestamp
        status = 0  # No error status

        return f"{voltage:.6E},{current:.6E},{resistance:.6E},{time_stamp:.6E},{status}"

    def _simulate_measurement(self):
        """
        The simulation uses Ohm's law with the configured source values
        and a virtual load resistance. Gaussian noise is added for realism.

        Returns:
            tuple: (voltage, current, resistance) measurements
        """
        R_load = self.state['load_resistance']

        if not self.state['output_on']:
            # Output is off - return near-zero values with some noise
            voltage = np.random.normal(0, self._voltage_noise)
            current = np.random.normal(0, self._current_noise)
            resistance = float('inf')
        elif self.state['source_func'] == 'VOLT':
            # Sourcing voltage - calculate current through load
            V_source = self.state['source_voltage']
            I_calc = V_source / R_load

            # Check compliance
            I_compliance = self.state['current_compliance']
            if abs(I_calc) > abs(I_compliance):
                # In compliance - limit current, adjust voltage
                current = np.sign(I_calc) * abs(I_compliance)
                voltage = current * R_load
            else:
                voltage = V_source
                current = I_calc

            # Add noise
            voltage += np.random.normal(0, self._voltage_noise)
            current += np.random.normal(0, self._current_noise)
            resistance = voltage / current if current != 0 else float('inf')

        else:  # source_func == 'CURR'
            # Sourcing current - calculate voltage across load
            I_source = self.state['source_current']
            V_calc = I_source * R_load

            # Check compliance
            V_compliance = self.state['voltage_compliance']
            if abs(V_calc) > abs(V_compliance):
                # In compliance - limit voltage, adjust current
                voltage = np.sign(V_calc) * abs(V_compliance)
                current = voltage / R_load
            else:
                current = I_source
                voltage = V_calc

            # Add noise
            voltage += np.random.normal(0, self._voltage_noise)
            current += np.random.normal(0, self._current_noise)
            resistance = voltage / current if current != 0 else float('inf')

        # Add resistance noise (percentage-based)
        if resistance != float('inf'):
            resistance *= (1 + np.random.normal(0, self._resistance_noise))

        return voltage, current, resistance

    # --- Core Instrument State Control ---

    def output(self, on=True):
        """
        Turn the main output of the sourcemeter on or off.

        Args:
            on (bool): True to enable the output, False to disable it
        """
        self.state['output_on'] = on

    def set_source_function(self, source_func):
        """
        Set the primary function of the source.

        Args:
            source_func (str): The source function, 'VOLT' or 'CURR'
        """
        self.state['source_func'] = source_func.upper()

    def set_sense_function(self, sense_func):
        """
        Set the measurement (sense) function.

        Args:
            sense_func (str): The measurement function, 'VOLT', 'CURR', or 'RES'
        """
        self.state['sense_func'] = sense_func.upper()

    def set_sense_mode(self, sense_mode):
        """
        Set the wiring configuration for sensing.

        Args:
            sense_mode (str): The sense mode, '2W' (2-wire) or '4W' (4-wire)
        """
        self.state['sense_mode'] = sense_mode.upper()

    # --- Source Configuration Methods ---

    def set_source_voltage(self, voltage):
        """
        Set the output level when in voltage source mode.

        Args:
            voltage (float): The desired output voltage in Volts
        """
        self.state['source_voltage'] = np.clip(voltage, *self.voltage)

    def set_source_current(self, current):
        """
        Set the output level when in current source mode.

        Args:
            current (float): The desired output current in Amps
        """
        self.state['source_current'] = np.clip(current, *self.current)

    def set_voltage_compliance(self, voltage_compliance):
        """
        Set the voltage limit (compliance) when in current source mode.

        Args:
            voltage_compliance (float): The maximum voltage allowed in Volts
        """
        self.state['voltage_compliance'] = voltage_compliance

    def set_current_compliance(self, current_compliance):
        """
        Set the current limit (compliance) when in voltage source mode.

        Args:
            current_compliance (float): The maximum current allowed in Amps
        """
        self.state['current_compliance'] = current_compliance

    # --- Convenience Configuration Methods ---

    def configure_voltage_source(self, voltage, current_compliance):
        """
        Configure the sourcemeter to source voltage with a specified compliance.

        Args:
            voltage (float): The voltage to source in Volts
            current_compliance (float): The current compliance limit in Amps
        """
        self.set_source_function('VOLT')
        self.set_source_voltage(voltage)
        self.set_current_compliance(current_compliance)

    def configure_current_source(self, current, voltage_compliance):
        """
        Configure the sourcemeter to source current with a specified compliance.

        Args:
            current (float): The current to source in Amps
            voltage_compliance (float): The voltage compliance limit in Volts
        """
        self.set_source_function('CURR')
        self.set_source_current(current)
        self.set_voltage_compliance(voltage_compliance)

    # --- Measurement (Read) Methods ---

    def quick_read(self):
        """
        Quickly return the value for the currently configured sense function.

        Returns:
            float: The measured value (Volts, Amps, or Ohms depending on sense_func)
        """
        voltage, current, resistance = self._simulate_measurement()

        sense = self.state['sense_func']
        if sense == 'VOLT':
            return voltage
        elif sense == 'CURR':
            return current
        elif sense == 'RES':
            return resistance
        return voltage  # Default to voltage

    def get_voltage(self):
        """
        Measure and return the voltage.

        Returns:
            float: The measured voltage in Volts
        """
        self.state['sense_func'] = 'VOLT'
        voltage, _, _ = self._simulate_measurement()
        return voltage

    def get_current(self):
        """
        Measure and return the current.

        Returns:
            float: The measured current in Amps
        """
        self.state['sense_func'] = 'CURR'
        _, current, _ = self._simulate_measurement()
        return current

    def get_resistance(self):
        """
        Measure and return the resistance.

        Returns:
            float: The measured resistance in Ohms
        """
        self.state['sense_func'] = 'RES'
        _, _, resistance = self._simulate_measurement()
        return resistance

    # --- Utility Methods ---

    def reset(self):
        """
        Reset the virtual sourcemeter to default settings.
        """
        self.__init__(address='VIRTUAL')

    def clear(self):
        """
        Clear status (no-op in virtual mode).
        """
        pass

    def set_load_resistance(self, resistance):
        """
        Set the simulated load resistance for realistic measurements.

        This is a virtual-only method that allows you to configure what
        load the virtual instrument "sees" for simulation purposes.

        Args:
            resistance (float): Load resistance in Ohms
        """
        self.state['load_resistance'] = resistance

    def get_state(self):
        """
        Get a copy of the current instrument state.

        This is a virtual-only method useful for debugging and testing.

        Returns:
            dict: Copy of the internal state dictionary
        """
        return self.state.copy()
