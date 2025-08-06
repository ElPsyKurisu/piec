import numpy as np

from ..virtual_instrument import VirtualInstrument
from .awg import Awg
from ..scpi import Scpi

class VirtualAwg(VirtualInstrument, Awg, Scpi):
    """
    Virtual version of the Keysight81150a AWG for simulation/testing.
    Stores state internally and generates synthetic output.
    """
    channel = [1, 2]
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    amplitude = (0, 5)
    offset = amplitude
    polarity = ['NORM', 'INV']
    duty_cycle = (0.0, 100.0)
    symmetry = (0.0, 100.0)
    pulse_width = (4.1e-9, 950000)
    pulse_delay = pulse_width
    trigger_source = ['IMM', 'INT', 'EXT', 'MAN']
    trigger_slope = ['POS', 'NEG', 'EITH']
    trigger_mode = ['EDGE', 'LEV']

    arb_dac_value = (0, 16383) # Range for individual DAC points in arb_data_length data list
    arb_data_length = (2, 1000) # Points, for arbitrary waveform data len

    def __init__(self, address='123'):
        VirtualInstrument.__init__(self, address=address)

        self.instrument = self
        
        self.state = {
            'output': {ch: False for ch in self.channel},
            'waveform': {ch: 'SIN' for ch in self.channel},
            'frequency': {ch: 1e3 for ch in self.channel},
            'amplitude': {ch: 1.0 for ch in self.channel},
            'offset': {ch: 0.0 for ch in self.channel},
            'source_impedance': {ch: 5 for ch in self.channel},
            'load_impedance': {ch: 50.0 for ch in self.channel},
            'polarity': {ch: 'NORM' for ch in self.channel},
            'duty_cycle': {ch: 50.0 for ch in self.channel},
            'symmetry': {ch: 50.0 for ch in self.channel},
            'pulse_width': {ch: 1e-6 for ch in self.channel},
            'pulse_delay': {ch: 0.0 for ch in self.channel},
            'trigger_source': {ch: 'IMM' for ch in self.channel},
            'trigger_level': {ch: 0.0 for ch in self.channel},
            'trigger_slope': {ch: 'POS' for ch in self.channel},
            'trigger_mode': {ch: 'EDGE' for ch in self.channel},
            'arb_waveform': {ch: None for ch in self.channel},
            'acquisition_channel': 1,  # Default acquisition channel
        }
       
    
    def idn(self):
        return "Virtual AWG"
    def send_software_trigger(self):
        self.write('*TRG')
    def write(self, command):
        if command == '*TRG':
            
            v = self.get_waveform(self.state['acquisition_channel'])
            
            freq = self.state['frequency'][self.state['acquisition_channel']]
            duration = 1.0 / freq  # one period
            t = np.linspace(0, duration, len(v))
            print("Applying waveform to virtual sample...")
           
            self.sample.apply_waveform(v, t)
        else: 
            pass
        # Simulate writing a command to the instrument
        
    def set_source_impedance(self, channel, source_impedance):
        self.state['source_impedance'][channel] = source_impedance
    def output(self, channel, on=True):
        self.state['output'][channel] = on

    def set_waveform(self, channel, waveform):
        self.state['waveform'][channel] = waveform

    def set_frequency(self, channel, frequency):
        self.state['frequency'][channel] = frequency

    def set_amplitude(self, channel, amplitude):
        self.state['amplitude'][channel] = amplitude
        self.state['arb_waveform'][channel]=self.state['arb_waveform'][channel]*self.state['amplitude'][channel]/2

    def set_offset(self, channel, offset):
        self.state['offset'][channel] = offset

    def set_load_impedance(self, channel, load_impedance):
        self.state['load_impedance'][channel] = load_impedance

    def set_polarity(self, channel, polarity):
        self.state['polarity'][channel] = polarity

    def configure_wf(self, channel, waveform, frequency=None, amplitude=None, offset=None, load_impedance=None, polarity=None, user_func=None):
        self.set_waveform(channel, waveform)
        if frequency is not None:
            self.set_frequency(channel, frequency)
        if amplitude is not None:
            self.set_amplitude(channel, amplitude)
        if offset is not None:
            self.set_offset(channel, offset)
        if load_impedance is not None:
            self.set_load_impedance(channel, load_impedance)
        if polarity is not None:
            self.set_polarity(channel, polarity)
        if waveform == 'USER' and user_func is not None:
            self.state['arb_waveform'][channel] = np.array(user_func)

    def set_square_duty_cycle(self, channel, duty_cycle):
        self.state['duty_cycle'][channel] = duty_cycle

    def set_ramp_symmetry(self, channel, symmetry):
        self.state['symmetry'][channel] = symmetry

    def set_pulse_width(self, channel, pulse_width):
        self.state['pulse_width'][channel] = pulse_width

    def set_pulse_rise_time(self, channel, rise_time):
        # Not simulated
        pass

    def set_pulse_fall_time(self, channel, fall_time):
        # Not simulated
        pass

    def set_pulse_duty_cycle(self, channel, duty_cycle):
        self.state['duty_cycle'][channel] = duty_cycle

    def set_pulse_delay(self, channel, pulse_delay):
        self.state['pulse_delay'][channel] = pulse_delay

    def configure_pulse(self, channel, pulse_width=None, pulse_delay=None, rise_time=None, fall_time=None, duty_cycle=None):
        self.set_waveform(channel, 'PULS')
        if pulse_delay is not None:
            self.set_pulse_delay(channel, pulse_delay)
        if pulse_width is not None:
            self.set_pulse_width(channel, pulse_width)
        if rise_time is not None:
            self.set_pulse_rise_time(channel, rise_time)
        if fall_time is not None:
            self.set_pulse_fall_time(channel, fall_time)
        if duty_cycle is not None:
            self.set_pulse_duty_cycle(channel, duty_cycle)

    def create_arb_waveform(self, channel, name, data):
        # Store the arbitrary waveform in state
        scaled_dac_data = data
        min_dac, max_dac = self.arb_dac_value
        voltage_data = []
        for val in scaled_dac_data:
            
            voltage_data.append(( (2 * (val - min_dac)) / (max_dac - min_dac) ) - 1)
    
        self.state['arb_waveform'][channel] = np.array(voltage_data)

    def set_arb_waveform(self, channel, name):
        # For simulation, just mark the waveform as selected
        self.state['waveform'][channel] = 'USER'
        

    def set_trigger_source(self, channel, source):
        self.state['trigger_source'][channel] = source

    def set_trigger_level(self, channel, level):
        self.state['trigger_level'][channel] = level

    def set_trigger_slope(self, channel, slope):
        self.state['trigger_slope'][channel] = slope

    def set_trigger_mode(self, channel, mode):
        self.state['trigger_mode'][channel] = mode

    def configure_trigger(self, channel, trigger_source=None, trigger_level=None, trigger_slope=None, trigger_mode=None):
        if trigger_source is not None:
            self.set_trigger_source(channel, trigger_source)
        if trigger_level is not None:
            self.set_trigger_level(channel, trigger_level)
        if trigger_slope is not None:
            self.set_trigger_slope(channel, trigger_slope)
        if trigger_mode is not None:
            self.set_trigger_mode(channel, trigger_mode)

    def configure_output_amplifier(self, channel='1', type='HIV'):
        # Simulate amplifier config by changing amplitude range
        if type == 'HIV':
            self.amplitude = (0, 10)
        elif type == 'HIB':
            self.amplitude = (0, 5)

    def get_waveform(self, channel):
        # Generate a synthetic waveform based on current settings
        print("Getting waveform for channel:", channel)
        wf = self.state['waveform'][channel]
        amp = self.state['amplitude'][channel]
        freq = self.state['frequency'][channel]
        offset = self.state['offset'][channel]
        t = np.linspace(0, 1, self.arb_data_length[1])
        
        
        if wf == 'SIN':
            v = amp * np.sin(2 * np.pi * freq * t) + offset
        elif wf == 'SQU':
            v = amp * np.sign(np.sin(2 * np.pi * freq * t)) + offset
        elif wf == 'RAMP':
            v = amp * (2 * (t * freq % 1) - 1) + offset
        elif wf == 'PULS':
            duty = self.state['duty_cycle'][channel] / 100.0
            v = amp * (np.mod(t * freq, 1) < duty) + offset
        elif wf == 'NOIS':
            v = amp * np.random.randn(self.arb_data_length) + offset
        elif wf == 'DC':
            v = np.ones(self.arb_data_length) * offset
        elif wf == 'USER' and self.state['arb_waveform'][channel] is not None:
            
            data = self.state['arb_waveform'][channel]
            print(99999999999999999)
            print(data)
            print(data[1])
            print(max(data))
            print(min(data))
            print(data[-0])
            v = np.interp(np.linspace(0, len(data)-1, self.arb_data_length[1]), np.arange(len(data)), data)
        else:
            v = np.zeros(self.arb_data_length)
        
        return v

