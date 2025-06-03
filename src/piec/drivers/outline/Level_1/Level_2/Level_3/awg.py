"""
An awg (arbitrary waveform generator) is defined as an instrument that has the typical features on expects an awg to have
"""
from ..generator import Generator

class Awg(Generator):
    # Initializer / Instance attributes
    """
    All awgs must be able to generate an arbitrary waveform and output it to the selected channel
    """
    def __init__(self, address):
        super().__init__(address)

    #core output channel control functions

    def output(self, channel, on=True):
        """
        All awgs must be able to output something, so therefore we need a method to turn the output on for the selected channel.
        args:
            channel (int): The channel to output on
            on (bool): Whether to turn the output on or off
        """
        state = "ON" if on else "OFF"
        self.instrument.write(f"OUTP{channel}:STAT {state}")
    
    #Standard waveform configuration functions
    def set_waveform(self, channel, waveform):
        """
        Sets the waveform to be generated on the selected channel either built in or user defined
        args:
            channel (int): The channel to set the waveform on
            waveform (str): The waveform to be generated, e.g., 'sine', 'square', 'triangle', 'ramp', 'pulse', 'arb'
        """
        # SCPI equivalents: SIN, SQU, TRI, RAMP, PULS, ARB (or USER)
        waveform_scpi = waveform.upper()
        if waveform_scpi == "SINE":
            waveform_scpi = "SIN"
        elif waveform_scpi == "SQUARE":
            waveform_scpi = "SQU"
        elif waveform_scpi == "TRIANGLE":
            waveform_scpi = "TRI"
        # RAMP, PULS, ARB are often direct.
        self.instrument.write(f"SOUR{channel}:FUNC:SHAP {waveform_scpi}")

    def set_frequency(self, channel, frequency):
        """
        Sets the frequency of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the frequency on
            frequency (float): The frequency of the waveform in Hz
        """
        self.instrument.write(f"SOUR{channel}:FREQ {frequency}")

    def set_delay(self, channel, delay):
        """
        Sets the delay of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the delay on
            delay (float): The delay of the waveform in seconds
        """
        # General waveform delay command (may be device-specific)
        # Common for pulses: SOUR{channel}:PULS:DEL {delay}
        # Or as a phase offset (requires frequency context): SOUR{channel}:PHAS {delay_degrees}
        # Using a common command for pulse delay, assuming it can apply more generally or for specific waveforms.
        # Some instruments might have a SOUR{channel}:DELay {delay} command.
        self.instrument.write(f"SOUR{channel}:PULS:DEL {delay}") # More specific to pulse, check instrument for general delay

    def set_amplitude(self, channel, amplitude):
        """
        Sets the amplitude of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the amplitude on
            amplitude (float): The amplitude of the waveform in volts
        """
        # Typically Vpp for AWGs, but could be RMS. Docstring says "in volts".
        self.instrument.write(f"SOUR{channel}:VOLT {amplitude}")

    def set_offset(self, channel, offset):
        """
        Sets the offset of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the offset on
            offset (float): The offset of the waveform in volts
        """
        self.instrument.write(f"SOUR{channel}:VOLT:OFFS {offset}")

    def set_load_impedance(self, channel, load_impedance):
        """
        Sets the load impedance of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the load impedance on
            load_impedance (float): The load impedance of the waveform in ohms
        """
        # For high impedance, often "INF" or a very large number.
        if isinstance(load_impedance, str) and load_impedance.upper() == "HIGHZ":
            impedance_val = "INF"
        elif load_impedance == float('inf'):
            impedance_val = "INF"
        else:
            impedance_val = str(load_impedance)
        self.instrument.write(f"OUTP{channel}:LOAD {impedance_val}")

    def set_source_impedance(self, channel, source_impedance):
        """
        Sets the source impedance of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the source impedance on
            source_impedance (float): The source impedance of the waveform in ohms
        """
        # Setting source impedance is uncommon; it's usually a fixed characteristic.
        # This command is speculative and highly device-dependent.
        # OUTPut[<n>]:IMPedance:INTernal <value> is a possible SCPI form if supported.
        if isinstance(source_impedance, str) and source_impedance.upper() == "HIGHZ":
            impedance_val = "INF" # Or specific keyword if instrument supports variable internal Z
        elif source_impedance == float('inf'):
            impedance_val = "INF"
        else:
            impedance_val = str(source_impedance)
        self.instrument.write(f"OUTP{channel}:IMP:INT {impedance_val}") # Highly device-specific

    def set_polarity(self, channel, polarity):
        """
        Sets the polarity of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the polarity on
            polarity (str): The polarity of the waveform, e.g., 'positive', 'negative'
        """
        pol_scpi = "NORM" if polarity.lower() == "positive" else "INV"
        self.instrument.write(f"OUTP{channel}:POL {pol_scpi}")

    def configure_waveform(self, channel, waveform, frequency=None, delay=None, amplitude=None, offset=None, load_impedance=None, source_impedance=None, polarity=None):
        """
        Configures the waveform to be generated on the selected channel. Calls the set_waveform, set_frequency, set_delay, set_amplitude, set_offset, set_load_impedance, set_source_impedance and set_polarity functions to configure the waveform
        args:
            channel (int): The channel to configure the waveform on
            waveform (str): The waveform to be generated
            frequency (float): The frequency of the waveform in Hz
            delay (float): The delay of the waveform in seconds
            amplitude (float): The amplitude of the waveform in volts
            offset (float): The offset of the waveform in volts
            load_impedance (float): The load impedance of the waveform in ohms
            source_impedance (float): The source impedance of the waveform in ohms
            polarity (str): The polarity of the waveform
        """
        self.set_waveform(channel, waveform)
        if frequency is not None:
            self.set_frequency(channel, frequency)
        # Note: set_delay might depend on frequency if implemented via phase.
        # If using SOUR:PULS:DEL or SOUR:DELay, it's direct.
        if delay is not None:
            self.set_delay(channel, delay)
        if amplitude is not None:
            self.set_amplitude(channel, amplitude)
        if offset is not None:
            self.set_offset(channel, offset)
        if load_impedance is not None:
            self.set_load_impedance(channel, load_impedance)
        if source_impedance is not None:
            # Some instruments may not support source impedance setting, check if supported
            # If not supported, this function can be skipped or raise an error.
            self.set_source_impedance(channel, source_impedance) # If supported
        if polarity is not None:
            # Polarity is often a feature of the output stage, not the waveform itself.
            # If polarity is not supported, this function can be skipped or raise an error.
            self.set_polarity(channel, polarity)

    #functions that are specific to waveform types

    #First for square waves
    def set_duty_cycle(self, channel, duty_cycle):
        """
        Sets the duty cycle of the waveform to be generated on the selected channel
        Useful for square waves
        args:
            channel (int): The channel to set the duty cycle on
            duty_cycle (float): The duty cycle of the waveform as a percentage (0-100)
        """
        self.instrument.write(f"SOUR{channel}:FUNC:SQU:DCYC {duty_cycle}")

    #Now for triangular and ramp waves
    def set_symmetry(self, channel, symmetry):
        """
        Sets the symmetry of the waveform to be generated on the selected channel
        Useful for triangular and ramp waves
        args:
            channel (int): The channel to set the symmetry on
            symmetry (float): The symmetry of the waveform as a percentage (0-100)
        """
        self.instrument.write(f"SOUR{channel}:FUNC:RAMP:SYMM {symmetry}") # Also applies to TRI

    #Now for pulses
    def set_pulse_width(self, channel, pulse_width):
        """
        Sets the pulse width of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the pulse width on
            pulse_width (float): The pulse width of the waveform in seconds
        """
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:WIDT {pulse_width}")

    def set_pulse_rise_time(self, channel, rise_time):
        """
        Sets the rise time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the rise time on
            rise_time (float): The rise time of the waveform in seconds
        """
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:TRAN:LEAD {rise_time}") # Or just TRAN for some

    def set_pulse_fall_time(self, channel, fall_time):
        """
        Sets the fall time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the fall time on
            fall_time (float): The fall time of the waveform in seconds
        """
        self.instrument.write(f"SOUR{channel}:FUNC:PULS:TRAN:TRA {fall_time}") # Or just TRAN:TRAIL

    def configure_pulse(self, channel, pulse_width, rise_time, fall_time):
        """
        Configures the pulse waveform on the selected channel. Calls the set_pulse_width, set_pulse_rise_time, and set_pulse_fall_time functions to configure the pulse waveform
        args:
            channel (int): The channel to configure the pulse waveform on
            pulse_width (float): The pulse width of the waveform in seconds
            rise_time (float): The rise time of the waveform in seconds
            fall_time (float): The fall time of the waveform in seconds
        """
        self.set_waveform(channel, "PULS") # Ensure waveform is pulse
        self.set_pulse_width(channel, pulse_width)
        self.set_pulse_rise_time(channel, rise_time)
        self.set_pulse_fall_time(channel, fall_time)

    #Now we move to the arb functions
    def create_arb_waveform(self, channel, name, data):
        """
        Creates an arbitrary waveform to be generated on the selected channel and saves to instrument memory if applicable. If no name is given, it will be generated with a default name. Typically
        corresponding to the volatile memory of the instrument. In the case where the given name already exists, it will prompt the user to overwrite or not.
        args:
            channel (int): The channel to create the arbitrary waveform on
            name (str): The name of the arbitrary waveform
            data (list or ndarray): The data points of the arbitrary waveform
        """
        # SCPI for arb data can be complex (binary block, specific formats).
        # Assuming data points are normalized float values sent as a comma-separated string.
        # The "prompt user" logic is application-level, not directly SCPI.
        # SOURce[<n>]:DATA:VOLatile <data_points_string> for volatile memory
        # SOURce[<n>]:TRACe:DATA# <name>,<points> or MMEM:STOR:TRAC <name>,<points> for named storage
        # Simplified approach: DATA:ARB <name>,<points_string> (some instruments)
        # Or, define and then select:
        # DATA:DEF EMEM, <name> (Define in non-volatile if supported, or VOLATILE for temp)
        # TRAC:DATA <name>, <comma_separated_data_points>
        # For direct volatile data:
        data_string = ",".join(map(str, data))
        if name.lower() == "volatile": # Convention for volatile memory
             self.instrument.write(f"SOUR{channel}:DATA:VOL {data_string}")
        else:
            # This sequence is common: define, then load data, then optionally save
            # This example directly loads data to a named segment, specific commands vary
            self.instrument.write(f"SOUR{channel}:TRAC:DATA# \"{name}\",{data_string}") # Example, syntax varies

    def set_arb_waveform(self, channel, name):
        """
        Sets the arbitrary waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the arbitrary waveform on
            name (str): The name of the arbitrary waveform to be set
        """
        # SOURce[<n>]:FUNCtion:SHAPe USER
        # SOURce[<n>]:FUNCtion:USER <name>
        # Some instruments allow: SOURce[<n>]:FUNCtion ARB,"<name>" or USER,"<name>"
        self.instrument.write(f"SOUR{channel}:FUNC:SHAP USER")
        self.instrument.write(f"SOUR{channel}:FUNC:USER \"{name}\"") # Or ARB depending on instrument
    
    #modulation functions
    #skip for now, not needed yet

    #burst and sweep functions
    #skip for now, not needed yet

    #trigger and sync functions
    def set_trigger_source(self, channel, source):
        """
        Sets the trigger source for the selected channel
        args:
            channel (int): The channel to set the trigger source on
            source (str): The trigger source, e.g., 'internal', 'external', 'manual'
        """
        # SCPI: TRIGger[<n>]:SOURce {IMMediate|INTernal|EXTernal|BUS|MANual}
        # Channel specific trigger source may not always exist, could be system-wide
        # Using TRIG:SOUR for simplicity, assuming channel context or system-wide.
        source_scpi = source.upper()
        if source_scpi == "INTERNAL": source_scpi = "INT" # Common abbreviation
        if source_scpi == "EXTERNAL": source_scpi = "EXT" # Common abbreviation
        self.instrument.write(f"TRIG{channel}:SOUR {source_scpi}") # Or just TRIG:SOUR

    def set_trigger_level(self, channel, level):
        """
        Sets the trigger level for the selected channel
        args:
            channel (int): The channel to set the trigger level on
            level (float): The trigger level in volts
        """
        # Typically for external trigger source
        self.instrument.write(f"TRIG{channel}:LEV {level}") # Or just TRIG:LEV

    def set_trigger_slope(self, channel, slope):
        """
        Sets the trigger slope for the selected channel
        args:
            channel (int): The channel to set the trigger slope on
            slope (str): The trigger slope, e.g., 'rising', 'falling'
        """
        # SCPI: POSitive | NEGative | EITHer
        slope_scpi = "POS" if slope.lower() == "rising" else "NEG"
        self.instrument.write(f"TRIG{channel}:SLOP {slope_scpi}") # Or just TRIG:SLOP

    def set_trigger_mode(self, channel, mode):
        """
        Sets the trigger mode for the selected channel
        args:
            channel (int): The channel to set the trigger mode on
            mode (str): The trigger mode, e.g., 'auto', 'normal', 'single'
        """
        # Trigger modes like 'auto', 'normal', 'single' are more common for oscilloscopes.
        # For AWGs, this could relate to how it reacts to triggers (e.g., burst mode, gate mode, or continuous run)
        # A simple mapping could be:
        # 'auto' -> continuous run, trigger re-arms: INIT:CONT ON
        # 'normal'/'single' -> trigger initiates action, then stops/re-arms: INIT:CONT OFF
        # This is a simplification. Specific modes like TRIGgered, GATed, etc., are instrument-dependent.
        if mode.lower() == "auto":
            self.instrument.write(f"INIT{channel}:CONT ON") # Continuous on trigger
        elif mode.lower() == "normal" or mode.lower() == "single":
            self.instrument.write(f"INIT{channel}:CONT OFF") # Single event per trigger
            if mode.lower() == "single": # For single, ensure it's armed and awaits one trigger
                self.instrument.write(f"INIT{channel}:IMM") # Arm for next trigger if it's a one-shot system command
                                                       # Or ABORt; INIT:IMM for some systems to ensure one shot.
                                                       # This part is highly instrument specific.

    def configure_trigger(self, channel, source, level, slope, mode):
        """
        Configures the trigger for the selected channel. Calls the set_trigger_source, set_trigger_level, set_trigger_slope, and set_trigger_mode functions to configure the trigger
        args:
            channel (int): The channel to configure the trigger on
            source (str): The trigger source
            level (float): The trigger level in volts
            slope (str): The trigger slope
            mode (str): The trigger mode
        """
        self.set_trigger_source(channel, source)
        if source.lower() == "external": # Level and slope usually for external trigger
            self.set_trigger_level(channel, level)
            self.set_trigger_slope(channel, slope)
        self.set_trigger_mode(channel, mode) # Mode setting might be more complex

    #maybe impedance for trigger as well? But maybe some wont have this