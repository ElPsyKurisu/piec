import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from piec.analysis.utilities import *

class DiscreteWaveform:

    def __init__(self, awg, osc, v_div=0.01, voltage_channel:str='1'):
        """
        General waveform parent class.
        
        :param awg: VISA address of the Arbitrary Waveform Generator
        :param osc: VISA address of the Oscilloscope
        :param v_div: volts per division for oscilloscope, make sure you are not clippng!
        :param trigger_amp: V of trigger pulse in V, scope trigger level will be trigger/2
        """
        self.v_div = v_div
        self.awg = awg
        self.osc = osc
        self.voltage_channel = voltage_channel

    def initialize_awg(self):
        self.awg.initialize()
        #self.awg.couple_channels() #should not be needed
        self.awg.configure_impedance(channel='1', source_impedance='50.0', load_impedance='50')
        self.awg.configure_trigger(channel='1', trigger_source='MAN')

    def configure_oscilloscope(self, channel:str = 1, voltage_scale=0.01):
        """
        Configures the Oscilloscope to capture the waveform.
        """
        self.osc.initialize()
        self.osc.configure_timebase(time_base_type='MAIN', reference='CENTer', time_scale=f'{self.length/8}', position=f'{5*(self.length/10)}') #this should be made general
        self.osc.configure_channel(channel=f'{channel}', voltage_scale=f'{voltage_scale}', impedance='FIFT')#set both to 50ohm
        self.osc.configure_trigger_characteristics(trigger_source='EXT', low_voltage_level='0.75', high_voltage_level='0.95', sweep='NORM')
        self.osc.configure_trigger_edge(trigger_source='EXT', input_coupling='DC')

    def configure_awg(self):
        """
        Should be defined in the specific measurment child class
        """
        raise AttributeError("configure_awg() must be defined in the child class specific to a waveform")

    def apply_and_capture_waveform(self):
        """
        Captures the waveform data from the oscilloscope.
        """
        print(f"Capturing waveform of type {self.type} for {self.length} seconds...")  # Wait for the oscilloscope to capture the waveform
        self.osc.initiate()
        self.awg.output_enable('1')
        self.awg.send_software_trigger()
        self.osc.operation_complete_query()
        self.osc.setup_wf(source='CHAN1')
        _, trace_t, trace_v  = self.osc.query_wf()#change
        self.data = pd.DataFrame({"time (s)":trace_t, "voltage (V)": trace_v}) # Retrieve the data from the oscilloscope
        print("Waveform captured.")

    def save_waveform(self, filename):
        """
        Saves the captured waveform data to a file.
        
        :param filename: Path to the file where the waveform will be saved (CSV format).
        """
        if self.data is not None:
            metadata_and_data_to_csv(self.metadata, self.data, filename)
            print(f"Waveform data saved to {filename}")
        else:
            print("No data to save. Capture the waveform first.")
        
    def run_experiment(self, save_path="waveform.csv"):
        """
        Runs the entire experiment by configuring the AWG, capturing the waveform, and saving the data.
        
        :param save_path: Path where the waveform will be saved (default: "waveform.csv")
        """
        self.configure_oscilloscope(voltage_scale=self.v_div)
        self.initialize_awg()
        self.configure_awg()
        self.apply_and_capture_waveform()
        self.save_waveform(save_path)

### SPECIFIC WAVEFORM MEASURMENT CLASSES ###

class HysteresisLoop(DiscreteWaveform):

    type = "HYSTERESIS"
        
    def __init__(self, awg=None, osc=None, v_div=0.1, frequency=1000.0, amplitude=1.0, offset=0.0,
                 n_cycles=2, voltage_channel:str='1', area=1.0e-5, time_offset=1e-8):
        """
        Initializes the HysteresisLoop class.
        
        :param frequency: Frequency of the triangle wave (in Hz)
        :param amplitude: Peak amplitude of the triangle wave (in Volts)
        :param offset: Offset of the triangle wave (in Volts)
        :param n_cycles: number of triangle cycles to run
        :param voltage_channel: which channel to write to/read from, defaults to '1'
        :param area: area of sample capacitor, used for polarization math (in m^2)
        """
        super().__init__(awg, osc, v_div, voltage_channel)
        self.length = 1/frequency

        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.n_cycles = n_cycles
        self.voltage_channel = voltage_channel
        self.metadata = pd.DataFrame(locals(), index=[0])
        del self.metadata['self']
        self.metadata['type'] = self.type
        self.metadata['awg'] = self.awg.idn()
        self.metadata['osc'] = self.osc.idn()
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False

    def configure_awg(self):
        """
        Configures the Arbitrary Waveform Generator (AWG) to output a triangle wave.
        """
        # Set the AWG to generate a triangle wave
        interp_v_array = [0,1,0,-1,0]+([1,0,-1,0]*((self.n_cycles)-1))

        n_points = self.awg.arb_wf_points_range[1]
        dense = interpolate_sparse_to_dense(np.linspace(0,len(interp_v_array),len(interp_v_array)), interp_v_array, total_points=n_points)

        # Check if we are going too fast for the awg
        for v in dense:
            if (v*self.amplitude)/(self.frequency/len(dense)) > self.awg.slew_rate:
                print('WARNING: DEFINED WAVEFORM IS FASTER THAN AWG SLEW RATE')
                break

        invert = self.amplitude < 0 # Check if we want opposite polarity

        self.awg.create_arb_wf(dense)
        self.awg.configure_wf(self.voltage_channel, 'VOLATILE', voltage=f'{abs(self.amplitude)*2}', frequency=f'{self.frequency}', invert=invert) 

class ThreePulsePund(DiscreteWaveform):

    type = "3PP"

    def __init__(self, awg=None, osc=None, v_div=0.1,
                 reset_amp=1, reset_width=1e-3, reset_delay=1e-3,
                 p_u_amp=1, p_u_width=1e-3, p_u_delay=1e-3,
                 offset=0, voltage_channel:str='1', area=1e-5, time_offset=1e-8):
        """
        Initializes the ThreePulsePund class.
        
        :param reset_amp: amplitude of reset pulse, polarity is polarity of P and u pulses x(-1) (in Volts)
        :param reset_width: width of reset pulse (in s)
        :param reset_delay: delay between reset pulse and p pulse (in s)
        :param p_u_amp: amplitude of p and u pulses (in Volts)
        :param p_u_width: width of p and u pulses (in s)
        :param p_u_delay: delay between p pulse and u pulse (in s)
        :param offset: Offset of the PUND waveform (in Volts)
        """
        super().__init__(awg, osc, v_div, voltage_channel)
        self.reset_amp = reset_amp
        self.reset_width = reset_width
        self.reset_delay = reset_delay
        self.p_u_amp = p_u_amp
        self.p_u_width = p_u_width
        self.p_u_delay = p_u_delay
        self.offset = offset
        self.length = (reset_width+(reset_delay)+(2*p_u_width)+(2*p_u_delay))
        self.metadata = pd.DataFrame(locals(), index=[0])
        del self.metadata['self']
        self.metadata['type'] = self.type
        self.metadata['awg'] = self.awg.idn()
        self.metadata['osc'] = self.osc.idn()
        self.metadata['length'] = self.length
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False

    def configure_awg(self):
        """
        Configures the Arbitrary Waveform Generator (AWG) to output a triangle wave.
        """
        # calculate time steps for voltage trace
        times = [0, self.reset_width, self.reset_delay, self.p_u_width, self.p_u_delay, self.p_u_width, self.p_u_delay,]
        sum_times = [sum(times[:i+1]) for i, t in enumerate(times)]
        # calculate full amplitude of pulse profile and fractional amps of pulses
        amplitude = abs(self.reset_amp) + abs(self.p_u_amp)
        frac_reset_amp = self.reset_amp/amplitude
        frac_p_u_amp = self.p_u_amp/amplitude
        
        polarity = np.sign(self.p_u_amp)

        # specify sparse t and v coordinates which define PUND pulse train
        sparse_t = np.array([sum_times[0], sum_times[1], sum_times[1], sum_times[2], sum_times[2], sum_times[3], sum_times[3],
                                sum_times[4], sum_times[4], sum_times[5], sum_times[5], sum_times[6],])
        sparse_v = np.array([-frac_reset_amp, -frac_reset_amp, 0, 0, frac_p_u_amp, frac_p_u_amp, 0, 0,
                             frac_p_u_amp, frac_p_u_amp, 0, 0,]) * polarity
        
        n_points = self.awg.arb_wf_points_range[1] # n points to use is max

        # densify the array, rise/fall times of pulses will be equal to the awg resolution
        dense_v = interpolate_sparse_to_dense(sparse_t, sparse_v, total_points=n_points)
        # write to awg
        self.awg.create_arb_wf(dense_v)
        self.awg.configure_wf(self.voltage_channel, 'VOLATILE', voltage=f'{abs(amplitude)}', frequency=f'{1/self.length}')
        print("AWG configured for a PUND pulse.")

    

# Example usage:
# experiment = HysteresisLoop(keysight81150a("GPIB::10::INSTR"), keysightdsox3024a("GPIB::1::INSTR"))
# experiment.run_experiment(save_path="pad1_hysteresis_data.csv")

