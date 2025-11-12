"""
Driver for the Stanford Research Systems SR830 DSP Lock-In Amplifier.

This class inherits from the base Lockin class and SCPI class
and fills in the instrument-specific attributes and methods based
on the SR830 manual.
"""
#NOTE: Keeping version 2 to test against 1, since both are different
# We assume lockin.py and scpi.py are in the same directory
# or otherwise available on the python path.
try:
    from .lockin import Lockin
    from ..scpi import SCPI
except ImportError:
    try:
        from lockin import Lockin
        from scpi import SCPI
    except ImportError:
        print("Could not import parent classes 'Lockin' and 'SCPI'.")
        print("Please ensure lockin.py and scpi.py are in the same directory or Python path.")
        # Define dummy classes for testing/linting if imports fail
        class SCPI:
            def __init__(self, *args, **kwargs): pass
            def write(self, cmd): print(f"DUMMY WRITE: {cmd}")
            def query(self, cmd): print(f"DUMMY QUERY: {cmd}"); return "0,0,0,0"
        class Instrument:
            pass
        class Lockin(Instrument):
            pass


class SRS830(Lockin, SCPI):
    """
    Driver for the SRS830 Lock-In Amplifier.
    
    Implements the methods defined in the parent Lockin class
    using SR830-specific SCPI commands.
    """

    # --- Class Attributes (from previous step) ---

    channel = [1]
    input_coupling = ["AC", "DC"]
    reference_source = ["internal", "external"]
    frequency = {
        'reference_source': {
            'internal': (0.001, 102000.0),
            'external': (0.001, 102000.0)
        }
    }
    harmonic = (1, 19999)
    phase = (-360.0, 729.99)
    input_configuration = ["A", "A-B", "I (1M)", "I (100M)"]

    _sensitivity_v = [
        2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9,
        1e-6, 2e-6, 5e-6, 10e-6, 20e-6, 50e-6, 100e-6, 200e-6, 500e-6,
        1e-3, 2e-3, 5e-3, 10e-3, 20e-3, 50e-3, 100e-3, 200e-3, 500e-3, 1.0
    ]
    _sensitivity_i = [
        2e-15, 5e-15, 10e-15, 20e-15, 50e-15, 100e-15, 200e-15, 500e-15,
        1e-12, 2e-12, 5e-12, 10e-12, 20e-12, 50e-12, 100e-12, 200e-12, 500e-12,
        1e-9, 2e-9, 5e-9, 10e-9, 20e-9, 50e-9, 100e-9, 200e-9, 500e-9, 1e-6
    ]
    
    sensitivity = {
        'input_configuration': {
            "A": _sensitivity_v,
            "A-B": _sensitivity_v,
            "I (1M)": _sensitivity_i,
            "I (100M)": _sensitivity_i
        }
    }
    notch_filter = ["Out", "Line", "2xLine", "Both"]
    time_constant = [
        10e-6, 30e-6, 100e-6, 300e-6,
        1e-3, 3e-3, 10e-3, 30e-3, 100e-3, 300e-3,
        1.0, 3.0, 10.0, 30.0,
        100.0, 300.0,
        1e3, 3e3, 10e3, 30e3
    ]
    filter_slope = [6, 12, 18, 24]

    # --- Constructor & Value Maps ---

    def __init__(self, *args, **kwargs):
        """
        Initializes the SR830 driver.
        """
        super().__init__(*args, **kwargs)
        
        # Store current state for dependent settings (e.g., sensitivity)
        # We query the instrument for its current state upon init.
        # Default to 'A' if query fails.
        try:
            config_idx = int(self.query("ISRC?"))
            self._current_input_config = self.input_configuration[config_idx]
        except Exception:
            self._current_input_config = "A" # Default
            print("Warning: Could not query initial input config. Defaulting to 'A'.")

        # Create maps for convenient string-to-int conversion
        self._ref_src_map = {s.lower(): i for i, s in enumerate(self.reference_source, 0)}
        self._ref_src_map_inv = {i: s for s, i in self._ref_src_map.items()} # 0: ext, 1: int
        
        self._in_config_map = {s: i for i, s in enumerate(self.input_configuration, 0)}
        self._in_config_map_inv = {i: s for s, i in self._in_config_map.items()}

        self._in_couple_map = {s.lower(): i for i, s in enumerate(self.input_coupling, 0)}
        self._in_couple_map_inv = {i: s for s, i in self._in_couple_map.items()} # 0: AC, 1: DC

        self._notch_map = {s.lower(): i for i, s in enumerate(self.notch_filter, 0)}
        self._notch_map_inv = {i: s for s, i in self._notch_map.items()}

        self._slope_map = {val: i for i, val in enumerate(self.filter_slope, 0)}
        self._slope_map_inv = {i: val for val, i in self._slope_map.items()}

        self._tc_map = {val: i for i, val in enumerate(self.time_constant, 0)}
        self._tc_map_inv = {i: val for val, i in self._tc_map.items()}

        self._sens_v_map = {val: i for i, val in enumerate(self._sensitivity_v, 0)}
        self._sens_i_map = {val: i for i, val in enumerate(self._sensitivity_i, 0)}


    # --- Method Implementations ---

    def set_reference_source(self, reference_source: str):
        """
        Sets the reference source for the lockin. (Internal or External)
        SCPI Command: FMOD {i} (0=Ext, 1=Int)
        """
        ref_str = reference_source.lower().strip()
        if ref_str not in self._ref_src_map:
            raise ValueError(f"Invalid reference_source. Must be one of: {self.reference_source}")
        
        i = self._ref_src_map[ref_str]
        self.write(f"FMOD {i}")

    def set_reference_frequency(self, frequency: float):
        """
        Sets the reference frequency for the lockin (if internal reference).
        SCPI Command: FREQ {f}
        """
        # Note: Instrument only accepts this command if FMOD is Internal
        min_f, max_f = self.frequency['reference_source']['internal']
        if not (min_f <= frequency <= max_f):
            raise ValueError(f"Frequency {frequency} Hz out of range ({min_f} Hz to {max_f} Hz)")
            
        self.write(f"FREQ {frequency}")

    def set_harmonic(self, harmonic: int):
        """
        Sets the detection harmonic.
        SCPI Command: HARM {i}
        """
        min_h, max_h = self.harmonic
        if not (min_h <= harmonic <= max_h):
             raise ValueError(f"Harmonic {harmonic} out of range ({min_h} to {max_h})")
        
        # Add check for (f * i <= 102kHz) ?
        # This requires querying the frequency, which adds overhead.
        # We will trust the user or let the instrument handle the error.
        self.write(f"HARM {harmonic}")

    def set_phase(self, phase: float):
        """
        Sets the reference phase shift.
        SCPI Command: PHAS {x}
        """
        min_p, max_p = self.phase
        if not (min_p <= phase <= max_p):
            print(f"Warning: Phase {phase} is outside manual's explicit range {self.phase}. "
                  "Instrument will wrap it.")
        
        self.write(f"PHAS {phase}")

    def set_input_configuration(self, configuration: str):
        """
        Sets the input configuration (A, A-B, I (1M), I (100M)).
        SCPI Command: ISRC {i}
        """
        if configuration not in self._in_config_map:
            raise ValueError(f"Invalid configuration. Must be one of: {self.input_configuration}")
        
        i = self._in_config_map[configuration]
        self.write(f"ISRC {i}")
        self._current_input_config = configuration # Update internal state

    def set_input_coupling(self, coupling: str):
        """
        Sets the input coupling (AC or DC).
        SCPI Command: ICPL {i} (0=AC, 1=DC)
        """
        coup_str = coupling.lower().strip()
        if coup_str not in self._in_couple_map:
            raise ValueError(f"Invalid coupling. Must be one of: {self.input_coupling}")
            
        i = self._in_couple_map[coup_str]
        self.write(f"ICPL {i}")

    def set_sensitivity(self, sensitivity: float):
        """
        Sets the sensitivity.
        SCPI Command: SENS {i}
        """
        if self._current_input_config.startswith("I"):
            # Current input
            sens_map = self._sens_i_map
            valid_vals = self._sensitivity_i
        else:
            # Voltage input
            sens_map = self._sens_v_map
            valid_vals = self._sensitivity_v
            
        if sensitivity not in sens_map:
            raise ValueError(f"Invalid sensitivity value {sensitivity} for current input config "
                             f"'{self._current_input_config}'. "
                             f"Valid values are: {valid_vals}")
        
        i = sens_map[sensitivity]
        self.write(f"SENS {i}")

    def set_notch_filter(self, notch_filter: str):
        """
        Sets the line notch filter mode.
        SCPI Command: ILIN {i}
        """
        notch_str = notch_filter.lower().strip()
        if notch_str not in self._notch_map:
            raise ValueError(f"Invalid notch_filter. Must be one of: {self.notch_filter}")
        
        i = self._notch_map[notch_str]
        self.write(f"ILIN {i}")

    def set_time_constant(self, time_constant: float):
        """
        Sets the low pass filter time constant.
        SCPI Command: OFLT {i}
        """
        if time_constant not in self._tc_map:
            raise ValueError(f"Invalid time_constant. Must be one of: {self.time_constant}")
            
        i = self._tc_map[time_constant]
        self.write(f"OFLT {i}")

    def set_filter_slope(self, filter_slope: int):
        """
        Sets the low pass filter slope (6, 12, 18, or 24 dB/oct).
        SCPI Command: OFSL {i}
        """
        if filter_slope not in self._slope_map:
            raise ValueError(f"Invalid filter_slope. Must be one of: {self.filter_slope}")
            
        i = self._slope_map[filter_slope]
        self.write(f"OFSL {i}")

    # --- Data Acquisition ---

    def quick_read(self) -> tuple[float, float]:
        """
        Quick read function that returns (X, Y) data.
        Uses SNAP? for a concurrent measurement.
        SCPI Command: SNAP? 1,2
        """
        try:
            response = self.query("SNAP? 1,2")
            x_str, y_str = response.split(',')
            return (float(x_str), float(y_str))
        except Exception as e:
            print(f"Error in quick_read: {e}. Response: '{response}'")
            return (0.0, 0.0)

    def read_data(self) -> dict[str, float]:
        """
        Reads X, Y, R, and Theta concurrently.
        SCPI Command: SNAP? 1,2,3,4
        """
        try:
            response = self.query("SNAP? 1,2,3,4")
            x_str, y_str, r_str, t_str = response.split(',')
            return {
                'X': float(x_str),
                'Y': float(y_str),
                'R': float(r_str),
                'Theta': float(t_str)
            }
        except Exception as e:
            print(f"Error in read_data: {e}. Response: '{response}'")
            return {'X': 0.0, 'Y': 0.0, 'R': 0.0, 'Theta': 0.0}

    def get_X(self) -> float:
        """
        Reads the X data.
        SCPI Command: OUTP? 1
        """
        return float(self.query("OUTP? 1"))

    def get_Y(self) -> float:
        """
        Reads the Y data.
        SCPI Command: OUTP? 2
        """
        return float(self.query("OUTP? 2"))

    def get_R(self) -> float:
        """
        Reads the R (magnitude) data.
        SCPI Command: OUTP? 3
        """
        return float(self.query("OUTP? 3"))

    def get_theta(self) -> float:
        """
        Reads the Theta (phase) data.
        SCPI Command: OUTP? 4
        """
        return float(self.query("OUTP? 4"))

    # --- Auto Functions ---

    def auto_gain(self):
        """
        Automatically sets the gain (sensitivity).
        SCPI Command: AGAN
        """
        self.write("AGAN")

    def auto_phase(self):
        """
        Automatically sets the reference phase to 0.
        SCPI Command: APHS
        """
        self.write("APHS")