"""
Virtual Oscilloscope class that mimics the Keysight DSOX3024a interface for testing and simulation purposes.
"""
import numpy as np
import pandas as pd

from .oscilloscope import Oscilloscope
from ..scpi import Scpi


# Import VirtualInstrument and VirtualSample from new file
from ..virtual_instrument import VirtualInstrument

class VirtualScope(VirtualInstrument, Oscilloscope, Scpi):
    """
    Virtual version of the KeysightDSOX3024a oscilloscope for simulation/testing.
    Stores state internally and generates synthetic data.
    """
    channel = [1, 2, 3, 4]
    vdiv = (0.001, 5.0)
    y_range = (0.008, 40.0)
    y_position = (-40.0, 40.0)
    input_coupling = ["AC", "DC"]
    probe_attenuation = (0.001, 10000.0)
    tdiv = (0.000000002, 50.0)
    x_range = (0.00000002, 500.0)
    x_position = (-500.0, 500.0)
    trigger_source = ["CHAN1", "CHAN2", "CHAN3", "CHAN4", "EXT", "LINE", "WGEN"]
    trigger_level = (-6.0, 6.0)
    trigger_slope = ["POS", "NEG", "EITH", "ALT"]
    trigger_mode = ["EDGE"]
    trigger_sweep = ["AUTO", "NORM"]
    acquisition_mode = ["NORM", "AVER", "HRES", "PEAK"]
    acquisition_points = (100, 1000)

    def __init__(self, address='abc'):
        VirtualInstrument.__init__(self, address=address)

        self.state = {
            'channels_on': {ch: True for ch in self.channel},
            'vdiv': {ch: 1.0 for ch in self.channel},
            'y_range': {ch: 8.0 for ch in self.channel},
            'y_position': {ch: 0.0 for ch in self.channel},
            'input_coupling': {ch: 'DC' for ch in self.channel},
            'probe_attenuation': {ch: 1.0 for ch in self.channel},
            'tdiv': 1e-3,
            'x_range': 8e-3,
            'x_position': 0.0,
            'trigger_source': 'CHAN1',
            'trigger_level': 0.0,
            'trigger_slope': 'POS',
            'trigger_mode': 'EDGE',
            'trigger_sweep': 'AUTO',
            'acquisition_mode': 'NORM',
            'acquisition_channel': 1,
            'running': False,
            'armed': False
        }

    def idn(self):
        return "Virtual Oscilloscope"
    
    def autoscale(self):
        # Simulate autoscale by resetting to defaults
        self.__init__()

    def toggle_channel(self, channel, on=True):
        self.state['channels_on'][channel] = on

    def set_vertical_scale(self, channel, vdiv=None, y_range=None):
        if vdiv is not None:
            self.state['vdiv'][channel] = vdiv
        if y_range is not None:
            self.state['y_range'][channel] = y_range

    def set_vertical_position(self, channel, y_position):
        self.state['y_position'][channel] = y_position

    def set_input_coupling(self, channel, input_coupling):
        self.state['input_coupling'][channel] = input_coupling

    def set_probe_attenuation(self, channel, probe_attenuation):
        self.state['probe_attenuation'][channel] = probe_attenuation

    def set_horizontal_scale(self, tdiv=None, x_range=None):
        if tdiv is not None:
            self.state['tdiv'] = tdiv
        if x_range is not None:
            self.state['x_range'] = x_range

    def set_horizontal_position(self, x_position):
        self.state['x_position'] = x_position

    def configure_horizontal(self, tdiv=None, x_range=None, x_position=None):
        self.set_horizontal_scale(tdiv, x_range)
        if x_position is not None:
            self.set_horizontal_position(x_position)

    def set_trigger_source(self, trigger_source):
        self.state['trigger_source'] = trigger_source

    def set_trigger_level(self, trigger_level):
        self.state['trigger_level'] = trigger_level

    def set_trigger_slope(self, trigger_slope):
        self.state['trigger_slope'] = trigger_slope

    def set_trigger_mode(self, trigger_mode):
        self.state['trigger_mode'] = trigger_mode

    def set_trigger_sweep(self, trigger_sweep):
        self.state['trigger_sweep'] = trigger_sweep

    def configure_trigger(self, trigger_source=None, trigger_level=None, trigger_slope=None, trigger_mode=None):
        if trigger_source is not None:
            self.set_trigger_source(trigger_source)
        if trigger_level is not None:
            self.set_trigger_level(trigger_level)
        if trigger_slope is not None:
            self.set_trigger_slope(trigger_slope)
        if trigger_mode is not None:
            self.set_trigger_mode(trigger_mode)

    def toggle_acquisition(self, run=True):
        self.state['running'] = run 

    def get_data(self):

        voltages, times = self.sample.get_voltage_response()
        
        return pd.DataFrame({'Time': times, 'Voltage': voltages})

    def arm(self):
        self.state['armed'] = True

    def set_acquisition(self):
        # No-op for virtual, could set a flag
        pass

    def set_acquisition_channel(self, channel):
        self.state['acquisition_channel'] = channel

    def set_acquisition_mode(self, acquisition_mode):
        self.state['acquisition_mode'] = acquisition_mode


    def configure_acquisition(self, channel=None, acquisition_mode=None, acquisition_points=None):
        if channel is not None:
            self.set_acquisition_channel(channel)
        if acquisition_mode is not None:
            self.set_acquisition_mode(acquisition_mode)
        if acquisition_points is not None:
            self.set_acquisition_points(acquisition_points)

    def quick_read(self):
        # Generate a synthetic waveform (e.g., sine wave)
        points = self.acquisition_points[1]
        t = np.linspace(0, self.state['x_range'], points)
        freq = 1.0 / (self.state['x_range'] if self.state['x_range'] else 1e-3)
        v = np.sin(2 * np.pi * freq * t) * self.state['vdiv'][self.state['acquisition_channel']] * 2
        return v.astype(np.uint8)
