
import unittest
import numpy as np
import sys
import os

# Ensure we can import from src
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
print(f"Added {src_path} to sys.path")

from piec.drivers.daq.daq import Daq
from piec.drivers.emulators.daq_to_awg import DaqAsAwg
from piec.drivers.emulators.daq_to_oscilloscope import DaqAsOscilloscope

class MockDaq(Daq):
    def __init__(self):
        # Bypass Instrument init for mock
        self.output_state = {}
        self.ao_data = {}
        self.ai_data = {}
        self.ao_config = {}
        self.ai_config = {}

    def output(self, channel, on=True):
        self.output_state[channel] = on
        print(f"MockDaq: Output {channel} set to {on}")

    def write_AO(self, channel, data):
        self.ao_data[channel] = data
        print(f"MockDaq: Wrote {len(data)} points to AO {channel}")

    def configure_AO_channel(self, channel, range, sample_rate):
        self.ao_config[channel] = {'range': range, 'sample_rate': sample_rate}
        print(f"MockDaq: Configured AO {channel} with SR {sample_rate}")

    def configure_AI_channel(self, channel, range, sample_rate):
        self.ai_config[channel] = {'range': range, 'sample_rate': sample_rate}
        print(f"MockDaq: Configured AI {channel} with SR {sample_rate}")

    def read_AI(self, channel):
        # Return some dummy data based on config
        points = 100 # default
        if channel in self.ai_config:
            # Maybe implied from sample rate * time??
            # For this test, we just return a fixed array
            pass
        return np.random.rand(100)
        
    def write_DO(self, channel, data):
        pass

class TestEmulators(unittest.TestCase):
    def test_daq_as_awg(self):
        print("\n--- Testing DaqAsAwg ---")
        mock_daq = MockDaq()
        awg = DaqAsAwg(mock_daq)
        
        # Configure
        awg.set_frequency(1, 1000)
        awg.set_amplitude(1, 2.0) # 2Vpp -> 1V peak
        awg.set_waveform(1, 'SIN')
        
        # Output On
        awg.output(1, True)
        
        # Check Mock
        self.assertIn(1, mock_daq.ao_data)
        data = mock_daq.ao_data[1]
        self.assertEqual(len(data), 1000) # 1MS/s / 1kHz = 1000 points
        self.assertAlmostEqual(np.max(data), 1.0, places=4)
        self.assertAlmostEqual(np.min(data), -1.0, places=4)
        
        print("DaqAsAwg Test Passed")

    def test_daq_as_scope(self):
        print("\n--- Testing DaqAsOscilloscope ---")
        mock_daq = MockDaq()
        scope = DaqAsOscilloscope(mock_daq)
        
        # Configure
        scope.set_horizontal_scale(0.001) # 1ms/div -> 10ms total
        scope.set_acquisition_points(1000) # 1000 points -> 100kS/s
        
        # Get Data
        df = scope.get_data()
        print("Columns:", df.columns)
        self.assertIn('Time', df.columns)
        self.assertIn('Channel 1', df.columns)
        self.assertEqual(len(df), 100) # Mock returns 100 points fixed
        
        # Check if DAQ was configured correctly
        self.assertIn(1, mock_daq.ai_config)
        # Expected SR: 1000 pts / 10ms = 100 kS/s = 100000.0
        self.assertAlmostEqual(mock_daq.ai_config[1]['sample_rate'], 100000.0)
        
        print("DaqAsOscilloscope Test Passed")

if __name__ == '__main__':
    unittest.main()
