"""
Emulator class to allow a DAQ to function as an Oscilloscope.
"""
import numpy as np
import pandas as pd
from ..oscilloscope.oscilloscope import Oscilloscope
from ..daq.daq import Daq

class DaqAsOscilloscope(Oscilloscope):
    """
    Adapter class that wraps a Daq instance and exposes it as an Oscilloscope.
    """
    
    def __init__(self, daq_instance: Daq, address="EMULATED_SCOPE", **kwargs):
        """
        Initialize the emulator.
        
        args:
            daq_instance (Daq): The underlying DAQ instrument driver instance.
            address (str): Dummy address.
        """
        super().__init__(address, **kwargs)
        self.daq = daq_instance
        
        # Internal state to map Scope params to DAQ params
        self._scope_state = {
            'tdiv': 1e-3, # 1 ms/div
            'vdiv': 1.0,  # 1 V/div
            'x_pos': 0.0,
            'y_pos': 0.0,
            'trigger_level': 0.0,
            'points': 1000
        }
        
    # --- Helper to calculate DAQ parameters ---
    
    def _apply_settings_to_daq(self, channel):
        """
        Translates scope settings (time/div) into DAQ settings (sample rate, num points).
        """
        # Time Base
        # Total time window usually 10 divs
        total_time = self._scope_state['tdiv'] * 10
        num_points = self._scope_state['points']
        
        sample_rate = num_points / total_time
        
        # Configure DAQ AI
        # Range estimate: 8 divs typically vertical? So 8 * vdiv
        v_range = self._scope_state['vdiv'] * 8 
        
        self.daq.configure_AI_channel(channel, range=v_range, sample_rate=sample_rate)

    # --- Vertical ---

    def set_vertical_scale(self, channel, vdiv, y_range=None):
        self._scope_state['vdiv'] = vdiv
        # y_range is optional in base class signature, but usually derived
        
    def set_vertical_position(self, channel, y_position):
        self._scope_state['y_pos'] = y_position
        
    # --- Horizontal ---
    
    def set_horizontal_scale(self, tdiv, x_range=None):
        self._scope_state['tdiv'] = tdiv
        
    def set_horizontal_position(self, x_position):
        self._scope_state['x_pos'] = x_position

    # --- Trigger (Soft Trigger Logic could go here, but DAQ trigger is better) ---
    def set_trigger_level(self, trigger_level):
        self._scope_state['trigger_level'] = trigger_level
        # Ideally push to DAQ hardware trigger if available

    # --- Acquisition ---
    
    def set_acquisition_points(self, acquisition_points):
        self._scope_state['points'] = acquisition_points

    # --- Data Access ---

    def quick_read(self):
        """
        Returns a snapshot (numpy array).
        """
        # Default channel 1 ?
        channel = 1
        self._apply_settings_to_daq(channel)
        
        # Read from DAQ
        raw_data = self.daq.read_AI(channel)
        
        # If raw_data is list, convert
        if isinstance(raw_data, list):
            raw_data = np.array(raw_data)
            
        return raw_data

    def get_data(self):
        """
        Returns a DataFrame with 'Time' and Channel data.
        """
        # Assuming channel 1 for single channel context or managing multiple
        channel = 1
        self._apply_settings_to_daq(channel)
        
        # Perform read
        raw_data = self.daq.read_AI(channel)
        if isinstance(raw_data, list):
            raw_data = np.array(raw_data)
            
        # Verify length
        n = len(raw_data)
        if n == 0:
            return pd.DataFrame()
            
        # Reconstruct Time Axis
        total_time = self._scope_state['tdiv'] * 10
        dt = total_time / n
        t = np.arange(n) * dt + self._scope_state['x_pos'] # Add delay/pos
        
        df = pd.DataFrame({
            "Time": t,
            f"Channel {channel}": raw_data
        })
        return df

