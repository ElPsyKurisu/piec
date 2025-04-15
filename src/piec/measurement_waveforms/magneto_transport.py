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
        time.sleep(3)  # Allow time for the field to stabilize
        # Read the actual voltage from the DMM
        actual_voltage = self.dmm.read_voltage()
        actual_field = actual_voltage * self.voltage_callibration #e.g. 0.1V * 10000 = 1000 Oe
        # Check if the field is within a reasonable range
        if abs(actual_field - self.field) > 0.1 * self.field:  # Allow 10% tolerance
            print(f"Warning: Field set to {self.field} Oe, but actual field is {actual_field} Oe")
        else:
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

    def shut_off(self):
        """
        Turns off the field by setting the calibrator to zero volts.
        """
        self.calibrator.set_output(0)  # Set the calibrator output to 0V
        print("Field turned off.")

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
        self.capture_data() # Capture data from the lockin and saves it to self.data and csv
        self.shut_off() #Sets the field to zero
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
        #self.metadata['calibrator'] = self.calibrator.idn()
        self.metadata['arduino'] = self.arduino.idn()
        self.metadata['timestamp'] = time.time()
        self.metadata['processed'] = False
        self.filename = create_measurement_filename(self.save_dir, self.type, self.notes) #create filename now so its blank

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
        #self.lockin.configure_gain_filters(sensitivity='1v/ua') #DO NOT USE AUTO NOTE MAYBE MAKE IT CONFIGURABLE
        print("Lock-in amplifier configured for AMR measurement.")

    def capture_data(self):
        """
        Write function to capture a single data_set and maybe save it to CSV using helper functions
        """

        #need functionality here that loops through what we care about
        # Loop through the angles and capture data at each step
        steps = convert_angle_to_steps(self.angle_step) 
        for angle in range(0, self.total_angle, self.angle_step):
            self.angle = angle
            self.arduino.step(steps, 0)  # Move the stepper motor to the desired angle
            time.sleep(1) # allow time for lockin to stablize
            print("capturing data at angle: ", self.angle)
            # Capture data point from the lockin
            self.capture_data_point()  # Capture data from the lockin
            self.save_data_point()  # Save the captured data to a CSV file
        

    def capture_data_point(self):
        """
        Take a single data point from the lockin at the given angle and field
        overwrites the data attribute with the new data point.
        """
        # Get the X and Y values from the lockin
        x, y = self.lockin.get_X_Y()
        print("x: ", x, "y: ", y)
        # Save the data point to a file or database (not implemented here)
        if self.data is None:
            self.data = pd.DataFrame({"angle": [self.angle], "field": [self.field], "X": [x], "Y": [y]})
        else:
            self.data.loc[len(self.data)] = {"angle": self.angle, "field": self.field, "X": x, "Y": y} #dynamically add new row
        # For now, just print the data point
        print(f"Data point at angle {self.angle} degrees and field {self.field} Oe: X={x}, Y={y}")

    def save_data_point(self):
        """
        Save captured data to CSV file.
        NOTE: NEED TO CHANGE THIS TO BE A DATA POINT AND NOT A WAVEFORM
        Assumes a filename has already been generated.
        Requires successful capture_data_point from lockin and stores in self.data attribute. 
        """
        if self.data is not None and self.filename is not None:
            metadata_and_data_to_csv(self.metadata, self.data, self.filename)
            print(f"Data point saved to {self.filename}")
        else:
            print("No data to save. Capture the data point first.")


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

"""
Psuedo Code to convert into correct format


def setup_amr(dmm, calibrator, arduino, lockin):

def set_field(self, field):
    voltage = convert_field_to_voltage(field)
    calibrator.set_output(voltage)
    #check field is correct by reading the dmm
    actual_voltage = dmm.read_voltage()
    actual_field = convert_voltage_to_field(actual_voltage)
    print("Set field to {}Oe and checked it is at {}Oe".format(field, actual_field))

def configure_lockin(self, lockin):
    '''
    Sets up the lockin to do what we need to do. Mainly output the sine wave at the correct frequnecy and voltage and setup
    the filters as needed etc.
    '''
    lockin.initialize() #sets fresh
    lockin.configure_reference() #sets the right hand side of the lockin
    lockin.configure_gain_filters(sensitivity='auto') #set to auto

def measure(self, lockin):
    lockin.get_X_Y()
    #code to save it somewhere with the data of what angle and field (aka all metadata of expirement)

def set_angle(self, angle):
    steps = convert_angle_to_steps(angle)
    self.arduino.step(0, steps) #order might be wrong, but move to new angle
"""