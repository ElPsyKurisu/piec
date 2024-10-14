import numpy as np
import time
import pandas as pd

class DiscreteWaveform:
    def __init__(self, awg, osc, v_div=0.01):
        """
        General waveform parent class.
        
        :param awg: VISA address of the Arbitrary Waveform Generator
        :param osc: VISA address of the Oscilloscope
        :param trigger_amp: V of trigger pulse in V, scope trigger level will be trigger/2
        """
        self.type = None
        self.length = None

        self.awg = awg
        self.osc = osc
        self.data = None

    def configure_trigger(self):
        self.awg.initialize()
        self.awg.couple_channels()
        self.awg.configure_impedance(channel='1', source_impedance='50.0', load_impedance='50')
        self.awg.configure_trigger(channel='1', source='MAN')

    def configure_oscilloscope(self, channel:str = 1, voltage_scale=0.01):
        """
        Configures the Oscilloscope to capture the waveform.
        """
        self.osc.initialize()
        self.osc.configure_timebase(time_base_type='MAIN', reference='CENTer', scale=f'{self.length}', position=f'{5*self.length}')
        self.osc.configure_channel(channel=channel, vertical_scale=voltage_scale, impedance='FIFT')#set both to 50ohm
        #NOTE changing the position now to 5* the timebase to hopefully get the full signal
        self.osc.configure_trigger_characteristics(trigger_source='EXT', low_voltage_level='0.75', high_voltage_level='0.95', sweep='NORM')
        self.osc.configure_trigger_edge(trigger_source='EXT', input_coupling='DC')
        print("Oscilloscope configured.")

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
        self.awg.send_software_trigger()
        time.sleep(0.2)
        metadata, trace_t, trace_v  = self.osc.query_wf()#change
        self.data = pd.Dataframe({"time (s)":trace_t, "voltage (V)": trace_v}) # Retrieve the data from the oscilloscope
        print("Waveform captured.")

    def save_waveform(self, filename):
        """
        Saves the captured waveform data to a file.
        
        :param filename: Path to the file where the waveform will be saved (CSV format).
        """
        if self.data is not None:
            self.data.to_csv(filename)
            print(f"Waveform data saved to {filename}")
        else:
            print("No data to save. Capture the waveform first.")

    def run_experiment(self, save_path="waveform.csv"):
        """
        Runs the entire experiment by configuring the AWG, capturing the waveform, and saving the data.
        
        :param save_path: Path where the waveform will be saved (default: "waveform.csv")
        """
        self.configure_awg()
        self.configure_trigger()
        self.configure_oscilloscope(voltage_scale=v_div)
        self.apply_and_capture_waveform()
        self.save_waveform(save_path)

### ARBITRARY WAVEFORM CONVINIENCE FUNCTIONS ###

def interpolate_sparse_to_dense(x_sparse, y_sparse, total_points=100):
    """
    Transform sparse arrays of x and y coordinates into a dense array of y coordinates
    linearly interpolated over N=total_points evenly-spaced x values.
    
    Parameters:
    - x_sparse (array-like): Sparse array of x coordinates.
    - y_sparse (array-like): Sparse array of y coordinates.
    - total_points (int): Number of interpolated points between each pair of coordinates.
    
    Returns:
    - y_dense (numpy array): Dense array of linearly interpolated y coordinates.
    """
    y_dense = []

    # Iterate through each pair of adjacent sparse points
    for i in range(len(x_sparse) - 1):
        # Get the start and end points
        x_start, x_end = x_sparse[i], x_sparse[i + 1]
        y_start, y_end = y_sparse[i], y_sparse[i + 1]
        
        # Generate interpolated points between y_start and y_end
        n_to_interpolate = int(((x_sparse[i + 1]-x_sparse[i])/max(x_sparse))*total_points)
        y_interp = np.linspace(y_start, y_end, n_to_interpolate, endpoint=False)
        
        # Append the interpolated points
        y_dense.extend(y_interp)

    #add on duplicate points at the end to ensure array length == total_points (make up for int rounding error)
    while len(y_dense) < total_points:
        y_dense.append(y_dense[-1])

    return np.array(y_dense)

### SPECIFIC WAVEFORM MEASURMENT CLASSES ###

class HysteresisLoop(DiscreteWaveform):
    def __init__(self, awg=None, osc=None, frequency=1000, amplitude=1, offset=0, n_cycles=2, voltage_channel:str='1'):
        """
        Initializes the HysteresisLoop class.
        
        :param frequency: Frequency of the triangle wave (in Hz)
        :param amplitude: Peak amplitude of the triangle wave (in Volts)
        :param offset: Offset of the triangle wave (in Volts)
        :param n_cycles: number of triangle cycles to run
        """
        super().__init__(awg=awg, osc=osc)
        self.type = "HYSTERESIS"
        self.length = 1/frequency

        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.n_cycles = n_cycles
        self.voltage_channel = voltage_channel

    def configure_awg(self):
        """
        Configures the Arbitrary Waveform Generator (AWG) to output a triangle wave.
        """
        # Set the AWG to generate a triangle wave
        interp_voltage_array = [0,1,0,-1,0]+([1,0,-1,0]*((self.n_cycles)-1))

        self.awg.create_arb_wf(interp_voltage_array, 'PV')
        self.awg.configure_arb_wf(self.voltage_channel, 'PV', gain=f'{self.amplitude*2}', freq=f'{self.frequency}') 

class PUNDPulse(DiscreteWaveform):
    def __init__(self, reset_amp=1, reset_width=1e-3, reset_delay=1e-3, p_u_amp=1, p_u_width=1e-3, p_u_delay=1e-3, offset=0,):
        """
        Initializes the PUNDPulse class.
        
        :param reset_amp: amplitude of reset pulse, polarity is polarity of P and u pulses x(-1) (in Volts)
        :param reset_width: width of reset pulse (in s)
        :param reset_delay: delay between reset pulse and p pulse (in s)
        :param p_u_amp: amplitude of p and u pulses, polarity is polarity of P and u pulses x(-1) (in Volts)
        :param p_u_width: width of p and u pulses (in s)
        :param p_u_delay: delay between p pulse and u pulse (in s)
        :param offset: Offset of the PUND waveform (in Volts)
        """
        self.reset_amp = reset_amp
        self.reset_width = reset_width
        self.reset_delay = reset_delay
        self.p_u_amp = p_u_amp
        self.p_u_width = p_u_width
        self.p_u_delay = p_u_delay
        self.offset = offset

    def configure_awg(self):
        """
        Configures the Arbitrary Waveform Generator (AWG) to output a triangle wave.
        """
        # calculate time steps for voltage trace
        times = [0, self.reset_width, self.reset_delay, self.p_u_width, self.p_u_delay, self.p_u_width, self.p_u_delay,]
        sum_times = [sum(times[:i+1]) for i, t in enumerate(times)]
        # calculate full amplitude of pulse profile and fractional amps of pulses
        amplitude = self.reset_amp + self.p_u_amp
        frac_reset_amp = amplitude/self.reset_amp
        frac_p_u_amp = amplitude/self.p_u_amp

        polarity = 1
        if self.p_u_amp < 0:
            polarity = -1
        
        # specify sparse t and v coordinates which define PUND pulse train
        sparse_t = np.array([0, sum_times[0], sum_times[0], sum_times[1], sum_times[1], sum_times[2], sum_times[2],
                                sum_times[3], sum_times[3], sum_times[4], sum_times[4], sum_times[5],])
        sparse_v = np.array([-frac_reset_amp, -frac_reset_amp, 0, 0, frac_p_u_amp, frac_p_u_amp, 0, 0,
                             frac_p_u_amp, frac_p_u_amp, 0, 0,]) * polarity
        
        # densify the array, rise/fall times of pulses will be equal to the awg resolution
        dense_v = interpolate_sparse_to_dense(sparse_t, sparse_v, total_points=sum_times[-1]/self.awg.resolution)
        
        # write to awg
        self.awg.create_arb_wf(dense_v, 'PUND')
        self.awg.configure_arb_wf(self.voltage_channel, 'PUND', gain=f'{amplitude}', freq=f'{sum_times[-1]}')
        print("AWG configured for a PUND pulse.")

    

# Example usage:
# experiment = HysteresisLoop(keysight81150a("GPIB::10::INSTR"), keysightdsox3024a("GPIB::1::INSTR"))
# experiment.run_experiment(save_path="pad1_hysteresis_data.csv")

