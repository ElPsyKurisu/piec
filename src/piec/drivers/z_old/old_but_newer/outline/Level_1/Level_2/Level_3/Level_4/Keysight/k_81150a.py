"""
Driver for the Keysight 81150A Pulse Function Arbitrary Noise Generator.
This class implements the specific functionalities for the 81150A model,
inheriting from generic Awg and Scpi classes.
"""

# Imports assuming standard PIEC file structure:
# 81150a.py in .../Level_4/Keysight/
# awg.py in .../Level_3/
# scpi.py in .../Level_1/
from ...awg import Awg
from .....scpi import Scpi

class Keysight81150a(Awg, Scpi):
    """
    Specific Class for this exact model of awg: Keysight 81150A.
    """

    # Class attributes for parameter restrictions, named after function arguments.
    # Values based on Keysight 81150A User Guide
    
    channel = [1, 2]
    amplitude = (0.01, 5.0) # Vpp into 50 Ohm load from 50 Ohm source
    frequency = { # Hz
        'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6),
        'TRI': (1e-6, 5e6),   'PULS': (1e-6, 120e6), 'USER': (1e-6, 120e6),
        'ARB': (1e-6, 120e6), 'NOIS': None, 'DC': None
    }
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER', 'TRI'] #
    offset = (-2.495, 2.495) # V, absolute max for 50 Ohm load, actual depends on Vpp
    delay = (-100e-9, 100e-9) # s, for SOURce[1|2]:SKEW
    polarity = ["NORM", "INV"] # For OUTPut:POLarity
    source_impedance = [5, 50] # Ohm, for OUTPut[1|2]:IMPedance
    load_impedance = (1.0, 1.0e6) # Ohm, or "INF" for OUTPut[1|2]:LOAD
    
    duty_cycle = (0.01, 99.99) # %, for SQUare or PULSe
    symmetry = (0.0, 100.0) # %, for RAMP
    
    pulse_width = (3.3e-9, None) # Min seconds, max depends on period
    # Max for pulse_width is Period - 3.3ns. This cannot be a static tuple.
    # Storing min value. Validation in method may be more complex.
    
    rise_time = (1.8e-9, None) # Min seconds, for PULSe:TRANsition:LEADing
    fall_time = (1.8e-9, None) # Min seconds, for PULSe:TRANsition:TRAiling
    # Max for transition times depends on pulse width and period.

    arb_data_length = (2, 524288) # Points, for arbitrary waveform data len
    arb_dac_value = (0, 16383) # Range for individual DAC points in arb_data_length data list
    arb_name_max_length = 30 # Max char length for arbitrary waveform segment names (typical)

    trigger_source = ["IMM", "EXT", "BUS", "MAN", "EVEN"] # For ARM[:SEQuence[<n>]]:SOURce
    trigger_level = (-5.0, 5.0) # V, for TRIGger[:SEQuence]:LEVel
    trigger_slope = ["POS", "NEG"] # For TRIGger[:SEQuence]:SLOPe
    trigger_mode = {"AUTO": "ON", "NORMAL": "OFF", "SINGLE": "OFF"} # Maps to INITiate[:SEQuence[<n>]]:CONTinuous

    def __init__(self, address):
        super().__init__(address)
        # Consider adding instrument-specific initialization if needed, e.g., self.reset()

    def output(self, channel: int, on: bool = True):
        """Turns the output of the specified channel ON or OFF. [SCPI: OUTPut[1|2][:STATe]]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        state_cmd = "ON" if on else "OFF"
        self.instrument.write(f"OUTP{channel}:STAT {state_cmd}")

    def set_waveform(self, channel: int, waveform: str):
        """Sets the waveform shape for the specified channel. [SCPI: SOURce[1|2]:FUNCtion[:SHAPe]]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        
        wf_upper = waveform.upper()
        # Basic validation using the class attribute `self.waveform`
        if wf_upper not in self.waveform:
             print(f"Warning: Waveform type '{waveform}' not in pre-defined list {self.waveform}. Sending command directly.")

        scpi_waveform = wf_upper
        if wf_upper == "TRI":
            self.instrument.write(f"SOUR{channel}:FUNC:SHAP RAMP")
            self.set_symmetry(channel, 50.0) # Triangle is RAMP with 50% symmetry
            return
        self.instrument.write(f"SOUR{channel}:FUNC:SHAP {scpi_waveform}")

    def set_frequency(self, channel: int, frequency: float):
        """Sets the frequency for the specified channel. [SCPI: SOURce[1|2]:FREQuency[:CW]]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        # Advanced validation would check self.frequency[current_waveform_type]
        self.instrument.write(f"SOUR{channel}:FREQ {frequency}")

    def set_delay(self, channel: int, delay: float):
        """Sets the channel skew (output delay). [SCPI: SOURce[1|2]:SKEW]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_d, max_d = self.delay # Uses renamed class attribute
        if not (min_d <= delay <= max_d):
            raise ValueError(f"Delay {delay}s out of range {self.delay}s.")
        self.instrument.write(f"SOUR{channel}:SKEW {delay}")

    def set_amplitude(self, channel: int, amplitude: float):
        """Sets the amplitude (Vpp). [SCPI: SOURce[1|2]:VOLTage[:AMPLitude]]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_a, max_a = self.amplitude # Uses renamed class attribute
        if not (min_a <= amplitude <= max_a):
             print(f"Warning: Amplitude {amplitude}Vpp may be out of typical range {self.amplitude}Vpp for 50 Ohm load.")
        self.instrument.write(f"SOUR{channel}:VOLT {amplitude}")

    def set_offset(self, channel: int, offset: float):
        """Sets the DC offset. [SCPI: SOURce[1|2]:VOLTage:OFFSet]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        # Actual valid range depends on amplitude: |Voffset| <= Vmax_peak – Vpp/2
        # min_o, max_o = self.offset # Uses renamed class attribute
        # if not (min_o <= offset <= max_o):
        #     print(f"Warning: Offset {offset}V may be out of absolute range {self.offset}V.")
        self.instrument.write(f"SOUR{channel}:VOLT:OFFS {offset}")

    def set_load_impedance(self, channel: int, load_impedance): # float or "INF"
        """Sets the expected load impedance. [SCPI: OUTPut[1|2]:LOAD]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        impedance_cmd_val = ""
        if isinstance(load_impedance, str) and load_impedance.upper() == "INF":
            impedance_cmd_val = "INF"
        elif isinstance(load_impedance, (int, float)):
            min_l, max_l = self.load_impedance # Uses renamed attribute
            if not (min_l <= load_impedance <= max_l):
                raise ValueError(f"Load impedance {load_impedance} Ohm out of range {self.load_impedance} Ohm.")
            impedance_cmd_val = str(load_impedance)
        else:
            raise TypeError(f"Invalid load_impedance type. Expected float or 'INF'. Got {load_impedance}")
        self.instrument.write(f"OUTP{channel}:LOAD {impedance_cmd_val}")

    def set_source_impedance(self, channel: int, source_impedance: int):
        """Sets the source output impedance. [SCPI: OUTPut[1|2]:IMPedance]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        if source_impedance not in self.source_impedance: # Uses renamed attribute
            raise ValueError(f"Invalid source impedance {source_impedance} Ohm. Allowed: {self.source_impedance} Ohm.")
        self.instrument.write(f"OUTP{channel}:IMP {source_impedance}")

    def set_polarity(self, channel: int, polarity: str):
        """Sets the output polarity. [SCPI: OUTPut[1|2]:POLarity]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        pol_upper = polarity.upper()
        if pol_upper not in self.polarity: # Uses renamed attribute
            raise ValueError(f"Invalid polarity '{polarity}'. Allowed: {self.polarity}")
        self.instrument.write(f"OUTP{channel}:POL {pol_upper}")

    def configure_waveform(self, channel: int, waveform: str, frequency: float = None,
                           delay: float = None, amplitude: float = None, offset: float = None,
                           load_impedance = None, source_impedance: int = None,
                           polarity: str = None):
        """Configures multiple waveform parameters for the specified channel."""
        self.set_waveform(channel, waveform)
        if frequency is not None: self.set_frequency(channel, frequency)
        if delay is not None: self.set_delay(channel, delay)
        if amplitude is not None: self.set_amplitude(channel, amplitude)
        if offset is not None: self.set_offset(channel, offset)
        if load_impedance is not None: self.set_load_impedance(channel, load_impedance)
        if source_impedance is not None: self.set_source_impedance(channel, source_impedance)
        if polarity is not None: self.set_polarity(channel, polarity)

    def set_duty_cycle(self, channel: int, duty_cycle: float):
        """Sets duty cycle for SQUare or PULSe waveforms. [SCPI: FUNC:SQU:DCYC or FUNC:PULS:DCYC]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_dc, max_dc = self.duty_cycle # Uses renamed attribute
        if not (min_dc <= duty_cycle <= max_dc):
            raise ValueError(f"Duty cycle {duty_cycle}% out of range {self.duty_cycle}%.")
        # This function is generic; 81150A has specific commands for SQU and PULS.
        # A robust implementation would query current waveform or require it as a parameter.
        # Defaulting to PULSe command path for simplicity here.
        current_shape = self.instrument.query(f"SOUR{channel}:FUNC:SHAP?").strip().upper()
        if "SQU" in current_shape:
            self.instrument.write(f"SOUR{channel}:FUNC:SQU:DCYC {duty_cycle}")
        elif "PULS" in current_shape:
            self.instrument.write(f"SOUR{channel}:FUNC:PULS:DCYC {duty_cycle}")
        else:
            print(f"Warning: Duty cycle can only be set for SQUare or PULSe. Current: {current_shape}")


    def set_symmetry(self, channel: int, symmetry: float):
        """Sets symmetry for RAMP waveforms. [SCPI: FUNC:RAMP:SYMM]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_s, max_s = self.symmetry # Uses renamed attribute
        if not (min_s <= symmetry <= max_s):
            raise ValueError(f"Symmetry {symmetry}% out of range {self.symmetry}%.")
        self.instrument.write(f"SOUR{channel}:FUNC:RAMP:SYMM {symmetry}")

    def set_pulse_width(self, channel: int, pulse_width: float):
        """Sets pulse width for PULSe waveforms. [SCPI: FUNC:PULS:WIDT]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_pw, _ = self.pulse_width # Uses renamed attribute (min part)
        if pulse_width < min_pw:
             print(f"Warning: Pulse width {pulse_width}s may be below instrument minimum {min_pw}s.")
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:WIDT {pulse_width}")

    def set_pulse_rise_time(self, channel: int, rise_time: float):
        """Sets leading edge transition time for PULSe. [SCPI: FUNC:PULS:TRAN[:LEAD]]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_rt, _ = self.rise_time # Uses renamed attribute (min part)
        if rise_time < min_rt:
            print(f"Warning: Rise time {rise_time}s may be below instrument minimum {min_rt}s.")
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:TRAN:LEAD {rise_time}")

    def set_pulse_fall_time(self, channel: int, fall_time: float):
        """Sets trailing edge transition time for PULSe. [SCPI: FUNC:PULS:TRAN:TRA]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        min_ft, _ = self.fall_time # Uses renamed attribute (min part)
        if fall_time < min_ft:
            print(f"Warning: Fall time {fall_time}s may be below instrument minimum {min_ft}s.")
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:TRAN:TRA {fall_time}")

    def configure_pulse(self, channel: int, pulse_width: float = None,
                        rise_time: float = None, fall_time: float = None,
                        duty_cycle: float = None):
        """Configures parameters specific to PULSe waveforms."""
        # Consider ensuring self.set_waveform(channel, "PULS") is called if not already PULS.
        if pulse_width is not None: self.set_pulse_width(channel, pulse_width)
        if rise_time is not None: self.set_pulse_rise_time(channel, rise_time)
        if fall_time is not None: self.set_pulse_fall_time(channel, fall_time)
        if duty_cycle is not None: self.set_duty_cycle(channel, duty_cycle)


    def create_arb_waveform(self, channel: int, name: str, data: list):
        """
        Defines an arbitrary waveform segment with DAC values (0-16383).
        [SCPI: SOURce[<C>]:DATA:SEGMent:VALues "<name>", <val1>,...] or SOURce[<C>]:DATA:VOLatile for "VOLATILE" name.
       
        """
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        
        min_len, max_len = self.arb_data_length
        if not (min_len <= len(data) <= max_len):
            raise ValueError(f"Number of arb points {len(data)} out of range [{min_len}, {max_len}].")

        if not all(isinstance(p, int) and self.arb_dac_value[0] <= p <= self.arb_dac_value[1] for p in data):
             raise ValueError(f"Arbitrary waveform data points must be integers between {self.arb_dac_value[0]} and {self.arb_dac_value[1]}.")

        data_str = ",".join(map(str, data))

        if name.upper() == "VOLATILE":
            self.instrument.write(f"SOUR{channel}:DATA:VOL {data_str}")
        else:
            if len(name) > self.arb_name_max_length:
                 print(f"Warning: Segment name '{name}' may exceed max length. Truncation possible.")
            self.instrument.write(f"SOUR{channel}:DATA:SEGM:VAL \"{name}\",{data_str}")

    def set_arb_waveform(self, channel: int, name: str):
        """
        Selects a previously defined arbitrary waveform segment.
        [SCPI: SOURce[1|2]:FUNCtion:SHAPe USER; :SOURce[1|2]:FUNCtion:USER "<name>"]
       
        """
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        
        self.instrument.write(f"SOUR{channel}:FUNC:SHAP USER")
        # "VOLATILE" is the default segment for SOUR:DATA:VOL.
        # Selecting it by name might not be needed if DATA:VOL was just used.
        self.instrument.write(f"SOUR{channel}:FUNC:USER \"{name}\"")


    def set_trigger_source(self, channel: int, source: str):
        """Sets ARM trigger source for the channel. [SCPI: ARM[:SEQuence[<n>]]:SOURce]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        src_upper = source.upper()
        if src_upper == "INTERNAL": src_upper = "IMM" # Map generic term
        if src_upper not in self.trigger_source: # Uses renamed attribute
            raise ValueError(f"Invalid trigger source '{source}'. Allowed: {self.trigger_source}")
        self.instrument.write(f"ARM{channel}:SOUR {src_upper}")

    def set_trigger_level(self, channel: int, level: float):
        """Sets system trigger level (for EXT source). [SCPI: TRIGger[:SEQuence]:LEVel]"""
        # 'channel' arg kept for API consistency, but command is system-wide.
        min_tl, max_tl = self.trigger_level # Uses renamed attribute
        if not (min_tl <= level <= max_tl):
            raise ValueError(f"Trigger level {level}V out of range {self.trigger_level}V.")
        self.instrument.write(f"TRIG:LEV {level}")

    def set_trigger_slope(self, channel: int, slope: str):
        """Sets system trigger slope (for EXT source). [SCPI: TRIGger[:SEQuence]:SLOPe]"""
        # 'channel' arg kept for API consistency, command is system-wide.
        slope_upper = slope.upper()
        slope_scpi = ""
        if slope_upper.startswith("RISING"): slope_scpi = "POS"
        elif slope_upper.startswith("FALLING"): slope_scpi = "NEG"
        elif slope_upper in self.trigger_slope: slope_scpi = slope_upper # Uses renamed attribute
        else:
            raise ValueError(f"Invalid trigger slope '{slope}'. Allowed: {self.trigger_slope} or 'RISING'/'FALLING'.")
        self.instrument.write(f"TRIG:SLOP {slope_scpi}")

    def set_trigger_mode(self, channel: int, mode: str):
        """Sets continuous run mode based on triggers. [SCPI: INITiate[:SEQuence[<n>]]:CONTinuous]"""
        if channel not in self.channel:
            raise ValueError(f"Invalid channel {channel}. Allowed: {self.channel}")
        mode_upper = mode.upper()
        if mode_upper not in self.trigger_mode: # Uses renamed attribute (map)
            raise ValueError(f"Invalid trigger mode '{mode}'. Allowed: {list(self.trigger_mode.keys())}")
        
        state_cmd = self.trigger_mode[mode_upper]
        self.instrument.write(f"INIT{channel}:CONT {state_cmd}")

    def configure_trigger(self, channel: int, source: str = None, level: float = None,
                          slope: str = None, mode: str = None):
        """Configures trigger parameters for the channel."""
        if source is not None: self.set_trigger_source(channel, source)
        if level is not None: self.set_trigger_level(channel, level)
        if slope is not None: self.set_trigger_slope(channel, slope)
        if mode is not None: self.set_trigger_mode(channel, mode)