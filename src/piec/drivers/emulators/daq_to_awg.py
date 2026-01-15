"""
Emulator class to allow a DAQ to function as an AWG.
"""
import numpy as np
from ..awg.awg import Awg
from ..daq.daq import Daq

class DaqAsAwg(Awg):
    """
    Adapter class that wraps a Daq instance and exposes it as an Awg.
    
    This allows a DAQ to be used in scripts that expect an AWG, by
    synthesizing standard waveforms (SIN, SQU, etc.) into data arrays
    that the DAQ can write to its analog outputs.
    """
    
    def __init__(self, daq_instance: Daq, address="EMULATED", **kwargs):
        """
        Initialize the emulator.
        
        args:
            daq_instance (Daq): The underlying DAQ instrument driver instance.
            address (str): Dummy address, defaults to "EMULATED".
        """
        # We don't call super().__init__ because we don't want to open a new connection.
        # instead we just assign the daq_instance to self.instrument (conceptually)
        # But Awg inherits from Instrument which handles connection. 
        # So we might need to bypass Instrument.__init__ or just let it be virtual.
        # easier approach: We are an Instrument, but our "instrument" handle is the daq.
        
        # However, to play nice with the hierarchy, we can initialize as a VIRTUAL instrument
        # so check_params and such still work if we want them to.
        super().__init__(address, **kwargs)
        
        self.daq = daq_instance
        
        # State tracking for waveform parameters
        self._wav_params = {} # Key: channel, Value: dict of params
        
        # Default sample rate - this is CRITICAL for synthesizing waveforms
        # Ideally this comes from the DAQ or is configured. 
        # For now, we'll default to something reasonable or ask the DAQ (if implemented)
        # We'll assume a property or method exists, or default to 1MS/s
        self.sample_rate = 1e6 
        
    def _get_params(self, channel):
        if channel not in self._wav_params:
            self._wav_params[channel] = {
                'waveform': 'SIN',
                'frequency': 1000.0,
                'amplitude': 1.0,
                'offset': 0.0,
                'phase': 0.0,
                'duty_cycle': 50.0,
                'symmetry': 50.0, # for ramp
                'pulse_width': None
            }
        return self._wav_params[channel]

    def set_sample_rate(self, sample_rate):
        """Sets the synthesis sample rate in Hz"""
        self.sample_rate = sample_rate

    # --- Standard AWG Implementation ---

    def output(self, channel, on=True):
        """
        Starts or stops the generation.
        Argument 'on' turns output on (True) or off (False).
        """
        if on:
            # Synthesize and write
            data = self._synthesize_waveform(channel)
            # Write to DAQ
            # We assume DAQ has set_AO_sample_rate or similar.
            # Ideally we configure the DAQ channel first
            self.daq.configure_AO_channel(channel, range=10, sample_rate=self.sample_rate) # Range 10 is a guess/default
            self.daq.write_AO(channel, data)
            
            # Check if DAQ has an output enable
            try:
                self.daq.output(channel, True)
            except:
                pass # DAQ might not have explicit output enable
        else:
            try:
                self.daq.output(channel, False)
            except:
                pass
            # Also maybe write 0s?
            # self.daq.write_AO(channel, [0]*100)

    def set_waveform(self, channel, waveform):
        params = self._get_params(channel)
        params['waveform'] = waveform

    def set_frequency(self, channel, frequency):
        params = self._get_params(channel)
        params['frequency'] = frequency
        
    def set_amplitude(self, channel, amplitude):
        params = self._get_params(channel)
        params['amplitude'] = amplitude
        
    def set_offset(self, channel, offset):
        params = self._get_params(channel)
        params['offset'] = offset

    # --- Waveform Type Specifics ---

    def set_square_duty_cycle(self, channel, duty_cycle):
        params = self._get_params(channel)
        params['duty_cycle'] = duty_cycle

    def set_ramp_symmetry(self, channel, symmetry):
        params = self._get_params(channel)
        params['symmetry'] = symmetry

    # --- Synthesis ---

    def _synthesize_waveform(self, channel):
        """
        Generates the array of voltage values based on current settings.
        Returns a numpy array.
        """
        params = self._get_params(channel)
        freq = params['frequency']
        amp = params['amplitude'] # Vpp usually in AWGs, or Amplitude? AWG base says Vpp usually.
        # Let's assume Amplitude means Vpp for consistency with many drivers, or Vpeak?
        # Standard: Amplitude usually Vpp. So Peak is Amp/2.
        # CHECK awg.py docstring: "amplitude (float): ... (usually Vpp but use instrument default)"
        
        peak = amp / 2.0
        offset = params['offset']
        wf_type = params['waveform'].upper()
        
        # Generate one period or a stream? 
        # Typically DAQs want a buffer. If continuous, we might need N periods.
        # Let's generate 1 second worth of data or at least 1 period.
        # For efficiency, let's try to match 1000 points or something reasonable, 
        # or enough for 1 period if frequency is high.
        
        # Actually, to be safe, let's generate exactly 1 period if possible, 
        # or a large buffer if the DAQ loops it.
        # Let's assume the DAQ loops the buffer (common in functional generation mode).
        
        # Points per period = SampleRate / Frequency
        points_per_period = int(self.sample_rate / freq)
        if points_per_period < 10:
            points_per_period = 10 # Minimum resolution safeguard
        
        t = np.linspace(0, 1/freq, points_per_period, endpoint=False)
        
        if wf_type == 'SIN':
            y = peak * np.sin(2 * np.pi * freq * t)
        elif wf_type == 'SQU':
            from scipy import signal
            dc = params['duty_cycle'] / 100.0
            y = peak * signal.square(2 * np.pi * freq * t, duty=dc)
        elif wf_type == 'RAMP':
            from scipy import signal
            sym = params['symmetry'] / 100.0
            # Sawtooth in scipy: width=1 is rising ramp (symmetry 100?), width=0 is falling?
            # standard: symmetry 50% = triangle. 
            y = peak * signal.sawtooth(2 * np.pi * freq * t, width=sym)
        elif wf_type == 'DC':
            y = np.full_like(t, offset) # Just offset
            return y # Return early as we don't add offset again
        else:
            # Default to sine
            y = peak * np.sin(2 * np.pi * freq * t)
            
        return y + offset
