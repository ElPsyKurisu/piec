import numpy as np
import time
import pandas as pd
import matplotlib.pyplot as plt
from piec.analysis.utilities import *


class MagnetoTransport:
    """
    Parent class for managing all magneto transport measurements

    Provides core functionality for configuring the magnet, stepper motor.
    capturing waveforms, saving data, and running analysis on captured waveforms. Designed
    to be subclassed for specific measurement types. NOTE: leaves subclasses to introduce additional instrumentation

    Attributes:
        :dmm (visa.Resource): DMM instrument object (required)
        :calibrator (visa.Resource) calibrator instrument object (required)
        :arduino (visa.Resource): Arduino Custom Stepper Object (required)
        :lockin (visa.Resource): AWG instrument object (required)
        :field (float): Desired Magnetic field in units of Oersted (depnds on manual setting of the analog field-feedback guassmeter)
        :angle (float): Angle in degrees to orient the motor at
        :save_dir (str): Directory path for data storage
        :filename (str): Name of saved data file
        :data (pd.DataFrame): Captured waveform data (time and voltage)
        :metadata (pd.DataFrame): Measurement parameters and metadata
    """

    def __init__(self, dmm, calibrator, arduino, lockin,  field, save_dir=r'\\scratch', voltage_callibration=10000):
        """Initialize core waveform measurement system.

        Args:
            :dmm: VISA address or initialized dmm object
            :calibrator: VISA address or initialized calibrator object
            :arduino: VISA address or initialized arduino object
            :field: field to bring the magnet too
            :angle: Angle to bring the platform too
            :save_dir: Data storage directory path (default network scratch)
            :voltage_callibration: Voltage calibration factor for field conversion in units of 1V is equal to input value
        """

        self.dmm = dmm
        self.calibrator = calibrator
        self.arduino = arduino
        self.lockin = lockin
        self.field = field
        self.save_dir = save_dir
        self.filename = None
        self.voltage_callibration = voltage_callibration #1V == 10000 Oe, but depends on hardware settings
        self.data = None
        #self._initialize() #checks communication

    def initialize(self):
        """
        Ensure proper connection along all base instruments
        Namely, dmm, calibrator, and arduino. Runs in the __init__ function
        
        """
        try:
            self.dmm.idn()
            self.calibrator.idn()
            self.arduino.idn()
            self.lockin.idn()
            print("All instruments working nominally")
        except:
            print("Error communicating with instruments")
        self.set_field() # Set the field using the calibrator

    def set_field(self):
        """
        Set the magnetic field using the calibrator.

        """
        voltage = self.field/self.voltage_callibration #e.g. want 1000 Oe so 1000/10000 = 0.1V
        # Set the field using the calibrator
        self.calibrator.set_output(voltage)
        # Check field is correct by reading the DMM
        time.sleep(1)  # Allow time for the field to stabilize
        # Read the actual voltage from the DMM
        actual_voltage = self.dmm.read_voltage()
        actual_field = actual_voltage * self.voltage_callibration #e.g. 0.1V * 10000 = 1000 Oe
        # Check if the field is within a reasonable range
        print(f"Set field to {self.field} Oe and checked it is at {actual_field} Oe")

    def configure_lockin(self):
        """
        Placeholder for measurement specific lockin configuration.
        
        Raises:
            :AttributeError: If not implemented in child class
        """
        raise AttributeError("configure_lockin() must be defined in the child class specific to measurement")

    def capture_data(self):
        """
        Placeholder for measurement specific data capture.

        Raise:
            :AttributeError: If not implemented in child class
        """
        raise AttributeError("capture_data() must be defined in the child class specific to measurement")   

    def apply_and_capture_waveform(self):
        """
        Execute waveform generation and data acquisition sequence.
        
        Coordinates instrument triggering, captures time-voltage data from oscilloscope,
        and stores results in self.data attribute (pandas DataFrame object). Includes instrument synchronization.
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

    def save_waveform(self):
        """
        Save captured waveform data to CSV file.
        
        Uses meaurement type and notes to generate filename.
        Requires successful waveform capture prior to calling (self.data must not be None).
        """
        if self.data is not None:
            self.filename = create_measurement_filename(self.save_dir, self.type, self.notes)
            metadata_and_data_to_csv(self.metadata, self.data, self.filename)
            print(f"Waveform data saved to {self.filename}")
        else:
            print("No data to save. Capture the waveform first.")

    def analyze(self):
        """
        Placeholder for measurement-specific analysis.
        
        Intended for post-processing of captured data. Child classes should
        implement analysis routines for their specific measurement type.
        """
        if self.data is not None:
            print(f"Analysis method not defined. Not changing {self.filename}")
        else:
            print("No data to analyze. Capture the waveform first.")
        
    def run_experiment(self):
        """
        Execute complete measurement workflow.
        
        Standard sequence:
        1. Initialize instruments and set initial parameters
        2. Configure lock-in amplifier
        3. capture data
        4. Save results
        5. Perform analysis
        """
        self.initialize() #checks communication and sets default params
        self.configure_lockin()
        self.capture_data() # Capture data from the lockin and saves it to self.data
        self.save_data() # Save the captured data to a CSV file NOTE: this should be done each time...
        self.analyze()

### SPECIFIC WAVEFORM MEASURMENT CLASSES ###
class AMR(MagnetoTransport):
    """
    Performs the AMR measurement using the lockin amplifier and the stepper motor.

    Attributes:
        :type (str): Measurement type identifier ('amr')
        :angle_step (float): Step size for angle in degrees
        :total_angle (float): Total angle to rotate in degrees
        :amplitude (float): Peak voltage amplitude in volts
        :frequency (float): Excitation frequency in Hz
    """
    type = 'amr'

    def __init__(self, dmm=None, calibrator=None, arduino=None, lockin=None, field=None, angle_step=15, total_angle=360,
                 amplitude=1.0, frequency=10, save_dir=r'\scratch', voltage_callibration=10000):
        """
        Initialize AMR measurement parameters.

        Specializes MagnetoTransport for AMR measurements.

        Attributes:
            :dmm (visa.Resource): DMM instrument object (required)
            :calibrator (visa.Resource): Calibrator instrument object (required)
            :arduino (visa.Resource): Arduino Custom Stepper Object (required)
            :lockin (visa.Resource): Lock-in amplifier object (required)
            :field (float): Desired magnetic field in Oe (required)
            :angle_step (float): Step size for angle in degrees (default: 15)
            :total_angle (float): Total angle to rotate in degrees (default: 360)
            :amplitude (float): Peak voltage amplitude in volts (default: 1.0)
            :frequency (float): Excitation frequency in Hz (default: 10)
            :save_dir (str): Directory path for data storage (default: '\\scratch')
            :voltage_callibration (float): Voltage calibration factor for field conversion (default: 10000)
        """

        super().__init__(dmm, calibrator, arduino, lockin, field, save_dir, voltage_callibration)
        self.angle_step = angle_step
        self.total_angle = total_angle
        self.amplitude = amplitude
        self.frequency = frequency
        self.notes = str(amplitude).replace('.', 'p')+'V_'+str(int(frequency))+'Hz' #i got nothing
        self.metadata = pd.DataFrame(locals(), index=[0])
        del self.metadata['self']
        self.metadata['type'] = self.type
        self.metadata['lockin'] = self.lockin.idn()
        self.metadata['dmm'] = self.dmm.idn()
        self.metadata['calibrator'] = self.calibrator.idn()
        self.metadata['arduino'] = self.arduino.idn()
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False

    def analyze(self):
        """
        Process hysteresis data and calculate polarization parameters.
        
        Performs time alignment, integration for polarization calculation,
        and generates hysteresis loop plots. Results appended to CSV.
        """
        if self.data is not None:
            #process_raw_hyst(self.filename, show_plots=self.show_plots, save_plots=self.save_plots, auto_timeshift=self.auto_timeshift)
            print(f"Analysis succeeded, updated {self.filename}")
        else:
            print("No data to analyze. Capture the waveform first.")
    
    def configure_lockin(self):
        """
        Configure lock-in amplifier for AMR measurement.
        
        Sets reference frequency, sensitivity, and filter settings.
        """
        self.lockin.initialize() #sets fresh
        #configure the internal oscillator to the right frequency and amplitude
        self.lockin.configure_reference(voltage=self.amplitude, frequency=self.frequency)
        #set gain to auto
        self.lockin.configure_gain_filters(sensitivity='auto') #set to auto
        print("Lock-in amplifier configured for AMR measurement.")

    def capture_data(self):
        """
        Write function to capture a single data_set and maybe save it to CSV using helper functions
        """

        #need functionality here that loops through what we care about
        # Loop through the angles and capture data at each step
        for angle in range(0, self.total_angle, self.angle_step):
            self.angle = angle
            steps = convert_angle_to_steps(angle)
            self.arduino.step(0, steps)  # Move the stepper motor to the desired angle
            time.sleep(1) # allow time for lockin to stablize
            self.capture_data_point()  # Capture data from the lockin
            self.save_data_point()  # Save the captured data to a CSV file
        
        # Move the stepper motor to the next angle

    def capture_data_point(self):
        """
        Take a single data point from the lockin at the given angle and field
        """
        # Get the X and Y values from the lockin
        x, y = self.lockin.get_X_Y()
        # Save the data point to a file or database (not implemented here)
        self.data = pd.DataFrame({"angle": [self.angle], "field": [self.field], "X": [x], "Y": [y]})
        # For now, just print the data point
        print(f"Data point at angle {self.angle} degrees and field {self.field} Oe: X={x}, Y={y}")

    def save_data_point(self):
        """
        Save captured data to CSV file.
        NOTE: NEED TO CHANGE THIS TO BE A DATA POINT AND NOT A WAVEFORM
        Uses measurement type and notes to generate filename.
        Requires successful capture_data_point from lockin and stores in self.data attribute.
        """
        if self.data is not None:
            self.filename = create_measurement_filename(self.save_dir, self.type, self.notes)
            metadata_and_data_to_csv(self.metadata, self.data, self.filename)
            print(f"Data point saved to {self.filename}")
        else:
            print("No data to save. Capture the data point first.")

class AMR(MagnetoTransport):
    """
    Hysteresis loop measurement using triangular excitation waveform.
    
    Specializes DiscreteWaveform for ferroelectric hysteresis measurements.
    Generates bipolar triangle waves and analyzes polarization-voltage loops.

    Attributes:
        :type (str): Measurement type identifier ('hysteresis')
        :frequency (float): Excitation frequency in Hz
        :amplitude (float): Peak voltage amplitude in volts
        :n_cycles (int): Number of waveform cycles to capture
        :area (float): Capacitor area for polarization calculation (m²)
        :show_plots (bool): Display interactive plots flag
        :save_plots (bool): Save plot images flag
    """

    type = "amr"

    def __init__(self, awg=None, osc=None, v_div=0.1, frequency=1000.0, amplitude=1.0, offset=0.0,
                 n_cycles=2, voltage_channel:str='1', area=1.0e-5, time_offset=1e-8,
                 show_plots=False, save_plots=True, auto_timeshift=False,
                 save_dir=r'\\scratch'):
        """
        Initialize hysteresis measurement parameters.

        Args:
            :frequency: Triangle wave frequency (1-1000 Hz typical)
            :amplitude: Peak-to-peak voltage amplitude (V)
            :offset: DC voltage offset (V)
            :n_cycles: Number of complete bipolar cycles
            :area: Device capacitor area for polarization calc (m²)
            :time_offset: Manual trigger-capture time alignment (s)
            :show_plots: Show matplotlib plots post analysis?
            :save_plots: Save analysis plots to disk?
            :auto_timeshift: Try to automatically determine t0 of captured waveform - t0 of trigger waveform?
        """
        
        super().__init__(awg, osc, v_div, voltage_channel, save_dir)
        self.length = 1/frequency

        self.frequency = frequency
        self.amplitude = amplitude
        self.offset = offset
        self.n_cycles = n_cycles
        self.voltage_channel = voltage_channel
        self.show_plots = show_plots
        self.save_plots = save_plots
        self.auto_timeshift = auto_timeshift
        self.notes = str(amplitude).replace('.', 'p')+'V_'+str(int(frequency))+'Hz'
        self.metadata = pd.DataFrame(locals(), index=[0])
        del self.metadata['self']
        self.metadata['type'] = self.type
        self.metadata['awg'] = self.awg.idn()
        self.metadata['osc'] = self.osc.idn()
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False

    def analyze(self):
        """
        Process hysteresis data and calculate polarization parameters.
        
        Performs time alignment, integration for polarization calculation,
        and generates hysteresis loop plots. Results appended to CSV.
        """
        if self.data is not None:
            process_raw_hyst(self.filename, show_plots=self.show_plots, save_plots=self.save_plots, auto_timeshift=self.auto_timeshift)
            print(f"Analysis succeeded, updated {self.filename}")
        else:
            print("No data to analyze. Capture the waveform first.")

    def configure_awg(self):
        """
        Generate AWG triangle waveform for hysteresis measurement.
        
        Creates multi-cycle bipolar triangle wave with specified parameters.
        Automatically checks against AWG slew rate limitations.
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
        self.awg.configure_wf(self.voltage_channel, 'USER', voltage=f'{abs(self.amplitude)*2}', offset=f'{self.offset}', frequency=f'{self.frequency}', invert=invert) 

class ThreePulsePund(DiscreteWaveform):
    """
    PUND (Positive-Up-Negative-Down) pulse measurement system.
    
    Implements 3-pulse sequence for ferroelectric capacitor characterization:
    Reset + Positive (P) + Up (U) (arbitrary polarity) pulses with delay intervals.
    Measures difference in switching currents between P and U pulse responses to
    calculate remanent polarization.

    Attributes:
        :type (str): Measurement type identifier ('3pulsepund')
        :reset_amp (float): Reset pulse amplitude (V)
        :p_u_amp (float): Measurement pulse amplitude (V)
        :reset_width (float): Reset pulse duration (s)
        :p_u_width (float): Measurement pulse duration (s)
    """
    type = "3pulsepund"

    def __init__(self, awg=None, osc=None, v_div=0.1,
                 reset_amp=1, reset_width=1e-3, reset_delay=1e-3,
                 p_u_amp=1, p_u_width=1e-3, p_u_delay=1e-3,
                 offset=0, voltage_channel:str='1', area=1e-5, time_offset=1e-8,
                 show_plots=False, save_plots=True, auto_timeshift=True,
                 save_dir=r'\\scratch'):
        """Initialize PUND pulse parameters.

        Args:
            :reset_amp: Reset pulse amplitude (V)
            :reset_width: Reset pulse duration (s)
            :reset_delay: Post-reset delay (s)
            :p_u_amp: Measurement pulse amplitude (V)
            :p_u_width: Measurement pulse duration (s)
            :p_u_delay: Inter-pulse delay (s)
            :area: Capacitor area for polarization calc (m²)
            :time_offset: Manual trigger-capture time alignment (s)
            :show_plots: Show matplotlib plots post analysis?
            :save_plots: Save analysis plots to disk?
            :auto_timeshift: Try to automatically determine t0 of captured waveform - t0 of trigger waveform?
        """

        super().__init__(awg, osc, v_div, voltage_channel, save_dir)
        self.reset_amp = reset_amp
        self.reset_width = reset_width
        self.reset_delay = reset_delay
        self.p_u_amp = p_u_amp
        self.p_u_width = p_u_width
        self.p_u_delay = p_u_delay
        self.offset = offset
        self.show_plots = show_plots
        self.save_plots = save_plots
        self.auto_timeshift = auto_timeshift
        self.length = (reset_width+(reset_delay)+(2*p_u_width)+(2*p_u_delay))
        self.notes = str(reset_amp).replace('.', 'p')+'Vres_'+str(p_u_amp).replace('.', 'p')+'Vpu'
        self.metadata = pd.DataFrame(locals(), index=[0])
        del self.metadata['self']
        self.metadata['type'] = self.type
        self.metadata['awg'] = self.awg.idn()
        self.metadata['osc'] = self.osc.idn()
        self.metadata['length'] = self.length
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False

    def analyze(self):
        """
        Analyze PUND data to calculate switching polarization.
        
        Processes current transients, integrates charge, and calculates
        switched charge values. Generates time-domain and polarization plots.
        """
        if self.data is not None:
            process_raw_3pp(self.filename, show_plots=self.show_plots, save_plots=self.save_plots, auto_timeshift=self.auto_timeshift)
            print(f"Analysis succeeded, updated {self.filename}")
        else:
            print("No data to analyze. Capture the waveform first.")

    def configure_awg(self):
        """
        Generate PUND pulse waveform for AWG output.
        
        Constructs pulse sequence with specified amplitudes and timing.
        Automatically scales pulses to AWG voltage range and handles
        polarity inversion when needed.
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
        sparse_v = np.array([-abs(frac_reset_amp), -abs(frac_reset_amp), 0, 0, abs(frac_p_u_amp), abs(frac_p_u_amp), 0, 0,
                             abs(frac_p_u_amp), abs(frac_p_u_amp), 0, 0,]) * polarity
        
        n_points = self.awg.arb_wf_points_range[1] # n points to use is max

        # densify the array, rise/fall times of pulses will be equal to the awg resolution
        dense_v = interpolate_sparse_to_dense(sparse_t, sparse_v, total_points=n_points)
        # write to awg
        self.awg.create_arb_wf(dense_v)
        self.awg.configure_wf(self.voltage_channel, 'USER', offset=f'{self.offset}', voltage=f'{abs(amplitude)}', frequency=f'{1/self.length}')
        print("AWG configured for a PUND pulse.")

    

# Example usage:
# experiment = HysteresisLoop(keysight81150a("GPIB::10::INSTR"), keysightdsox3024a("GPIB::1::INSTR"))
# experiment.run_experiment(save_path="pad1_hysteresis_data.csv")
# NOTE Docstrings written with help from DeepSeekR1 LLM

"""
Helper Functions Below
"""

def convert_steps_to_angle(steps, steps_per_revolution=200) -> float:
    """
    Helper function to convert the steps to an angle

    ars:
        steps (int) number of steps to be converted
        steps_per_revolution (int) Number of steps for one complete revolution
    """
    angle = float(steps*360/steps_per_revolution)
    return angle

def convert_angle_to_steps(angle, steps_per_revolution=200) -> int:
    """
    Helper function to convert an angle to steps

    args:
        angle (float) Desired angle
        steps_per_revolution (int) Number of steps for one complete revolution
    """
    steps = int(angle*steps_per_revolution/360)
    return steps

def convert_field_to_voltage(field):
    """
    Convert the field to voltage using the calibrator. This is a psuedo code function and needs to be implemented
    with the correct conversion factor.
    Currently 1V == 10000 Oe, but depends on hardware settings

    args:
        field (float) Desired field in Oe
    """
    # This is a placeholder for the actual conversion logic
    voltage = field * 0.1  # Example conversion factor, replace with actual logic
    return voltage

def convert_voltage_to_field(field)

"""
Psuedo Code to convert into correct format
"""

def setup_amr(dmm, calibrator, arduino, lockin):

def set_field(self, field):
    voltage = convert_field_to_voltage(field)
    calibrator.set_output(voltage)
    #check field is correct by reading the dmm
    actual_voltage = dmm.read_voltage()
    actual_field = convert_voltage_to_field(actual_voltage)
    print("Set field to {}Oe and checked it is at {}Oe".format(field, actual_field))

def configure_lockin(self, lockin):
    """
    Sets up the lockin to do what we need to do. Mainly output the sine wave at the correct frequnecy and voltage and setup
    the filters as needed etc.
    """
    lockin.initialize() #sets fresh
    lockin.configure_reference() #sets the right hand side of the lockin
    lockin.configure_gain_filters(sensitivity='auto') #set to auto

def measure(self, lockin):
    lockin.get_X_Y()
    #code to save it somewhere with the data of what angle and field (aka all metadata of expirement)

def set_angle(self, angle):
    steps = convert_angle_to_steps(angle)
    self.arduino.step(0, steps) #order might be wrong, but move to new angle
