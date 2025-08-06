"""
Driver for the Keysight 81150A Pulse Function Arbitrary Noise Generator.
This class implements the specific functionalities for the 81150A model,
inheriting from generic Awg and Scpi classes.
"""

# Imports assuming standard PIEC file structure:
# 81150a.py in .../Level_4/Keysight/
# awg.py in .../Level_3/
# scpi.py in .../Level_1/
import numpy as np
from ..outline.Level_1.Level_2.Level_3.awg import Awg
from ..outline.Level_1.scpi import Scpi

class Keysight81150a(Awg, Scpi):
    """
    Specific Class for this exact model of awg: Keysight 81150A. Created by human.
    """

    # Class attributes for parameter restrictions, named after function arguments.
    # Values based on Keysight 81150A User Guide
    
    channel = [1, 2]
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
    amplitude = (0, 5) #V_pp added functionality that switches based on amplifier mode
    offset = amplitude #assume same as amplitude, when amplitude switches so too does offset
    load_impedance = (0.3, 1e6)
    source_impedance = [5, 50]
    polarity = ['NORM', 'INV']
    duty_cycle = (0.0, 100.0)
    symmetry = (0.0, 100.0)
    pulse_width = (4.1e-9,  950000)
    pulse_delay = pulse_width #typically the same
    rise_time = None
    fall_time = rise_time #typically the same
    trigger_source = ['IMM', "INT", "EXT", "MAN"] #[IMM (immediate), INT (internal), EXT (external), MAN (software trigger)]
    trigger_slope = ['POS', 'NEG', 'EITH'] #[POS (positive), NEG (negative), EITH (either)]
    trigger_mode = ["EDGE", "LEV"] #[EDGE (edge), LEV (level)]
    slew_rate = 1.0e9
    arb_data_range = (2, 524288)
    #Parent class methods

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
        if on:
            self.instrument.write(":OUTP{} ON".format(channel))
        else:
            self.instrument.write(":OUTP{} OFF".format(channel))
    
    #Standard waveform configuration functions
    def set_waveform(self, channel, waveform):
        """
        Sets the built_in waveform to be generated on the selected channel.
        args:
            channel (int): The channel to set the waveform on
            waveform (str): The waveform to be generated
        """
        self.instrument.write(":FUNC{} {}".format(channel, waveform))

    def set_frequency(self, channel, frequency):
        """
        Sets the frequency of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the frequency on
            frequency (float): The frequency of the waveform in Hz
        """
        self.instrument.write(":FREQ{} {}".format(channel, frequency))

    def set_amplitude(self, channel, amplitude):
        """
        Sets the amplitude of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the amplitude on
            amplitude (float): The amplitude of the waveform in volts (usually Vpp but use instrument default)
        """
        self.instrument.write(":VOLT{} {}".format(channel, amplitude))

    def set_offset(self, channel, offset):
        """
        Sets the offset of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the offset on
            offset (float): The offset of the waveform in volts
        """
        self.instrument.write(":VOLT{}:OFFS {}".format(channel, offset))

    def set_load_impedance(self, channel, load_impedance):
        """
        Sets the load impedance of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the load impedance on
            load_impedance (float): The load impedance of the waveform in ohms
        """
        self.instrument.write(":OUTP{}:IMP:EXT {}".format(channel, load_impedance))

    def set_polarity(self, channel, polarity):
        """
        Sets the polarity of the waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the polarity on
            polarity (str): The polarity of the waveform
        """
        self.instrument.write(":OUTP{}:POL {}".format(channel, polarity))

    def configure_waveform(self, channel, waveform, frequency=None, amplitude=None, offset=None, load_impedance=None, polarity=None, user_func=None):
        """
        Configures the waveform to be generated on the selected channel. Calls the set_waveform, set_frequency, set_amplitude, set_offset, set_load_impedance, and set_polarity functions to configure the waveform
        NOTE: Add arb waveform to toggle here
        args:
            channel (int): The channel to configure the waveform on
            waveform (str): The waveform to be generated
            frequency (float): The frequency of the waveform in Hz
            amplitude (float): The amplitude of the waveform in volts
            offset (float): The offset of the waveform in volts
            load_impedance (float): The load impedance of the waveform in ohms
            polarity (str): The polarity of the waveform
        """
        if waveform == "user":
            if user_func is not None:
                self.set_arb_waveform(channel, user_func)
            else:
                print("Please input a user_func arg to configure the user defined wave")
        else:
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

    #functions that are specific to waveform types

    #First for square waves
    def set_square_duty_cycle(self, channel, duty_cycle):
        """
        Sets the duty cycle of the square wave to be generated on the selected channel
        args:
            channel (int): The channel to set the duty cycle on
            duty_cycle (float): The duty cycle of the waveform as a percentage (0-100)
        """
        self.instrument.write(":SOUR:FUNC{}:SQU:DCYC {}".format(channel, duty_cycle)) 

    #Now for triangular and ramp waves
    def set_ramp_symmetry(self, channel, symmetry):
        """
        Sets the symmetry of the ramp waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the symmetry on
            symmetry (float): The symmetry of the waveform as a percentage (0-100)
        """
        self.instrument.write(":FUNC{}:RAMP:SYMM {}".format(channel, symmetry))

    #Now for pulses
    def set_pulse_width(self, channel, pulse_width):
        """
        Sets the pulse width of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the pulse width on
            pulse_width (float): The pulse width of the waveform in seconds
        """
        self.instrument.write(":FUNC{}:PULS:WIDT {}".format(channel, pulse_width))

    def set_pulse_rise_time(self, channel, rise_time):
        """
        Sets the rise time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the rise time on
            rise_time (float): The rise time of the waveform in seconds
        """
        self.instrument.write(":PULS:TRAN{} {}".format(channel, rise_time))

    def set_pulse_fall_time(self, channel, fall_time):
        """
        Sets the fall time of the waveform to be generated on the selected channel
        Useful for pulses
        args:
            channel (int): The channel to set the fall time on
            fall_time (float): The fall time of the waveform in seconds
        """
        self.instrument.write(":PULS:TRAN{}:TRA {}".format(channel, fall_time))
    
    def set_pulse_duty_cycle(self, channel, duty_cycle):
        """
        Sets the duty cycle of the pulse to be generated on the selected channel
        args:
            channel (int): The channel to set the duty cycle on
            duty_cycle (float): The duty cycle of the pulse as a percentage (0-100)
        """
        self.instrument.write(":FUNC{}:PULS:DCYC {}".format(channel, duty_cycle))

    def set_pulse_delay(self, channel, pulse_delay):
        """
        Set the pulse delay on the configured channel in units of seconds. Delay is the time between the start of the 
        pulse period and the start of the leading edge of the pulse.
        args:
            channel (int): The channel to set the delay on
            pulse_delay (float): The delay of the waveform in seconds
        """
        self.instrument.write(":PULS:DEL{} {}".format(channel, pulse_delay))

    def configure_pulse(self, channel, pulse_width=None, pulse_delay=None, rise_time=None, fall_time=None, duty_cycle=None):
        """
        Configures the pulse waveform on the selected channel. Calls the set_pulse_width, set_pulse_delay, set_pulse_rise_time, set_pulse_duty_cycle and set_pulse_fall_time functions to configure the pulse waveform
        args:
            channel (int): The channel to configure the pulse waveform on
            pulse_width (float): The pulse width of the waveform in seconds
            pulse_delay (float): The delay of the pulse waveform in seconds
            rise_time (float): The rise time of the waveform in seconds
            fall_time (float): The fall time of the waveform in seconds
            duty_cycle (float): The duty cycle of the pulse as a percentage (0-100)
        """
        self.set_waveform(channel, "PULS") # Ensure waveform is pulse
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

    #Now we move to the arb functions
    def create_arb_waveform(self, channel, name, data):
        """
        Creates an arbitrary waveform to be generated on the selected channel and saves to instrument memory if applicable. If no name is given, it will be generated with a default name. Typically
        corresponding to the volatile memory of the instrument. In the case where the given name already exists, it will prompt the user to overwrite or not.
        For implementing the data transfer, use the most documented version from the manual.
        args:
            channel (int): The channel to create the arbitrary waveform on
            name (str): The name of the arbitrary waveform
            data (list or ndarray): The data points of the arbitrary waveform
        """
        # Scale the waveform data to the valid range See scale_waveform_data
        scaled_data = scale_waveform_data(data)  
        self.instrument.write(":FORM:BORD SWAP")

        self.instrument.write_binary_values(":DATA{}:DAC VOLATILE, ".format(channel), scaled_data, datatype='h') #need h as 2bit bytes see struct module
        if name is not None:
            #first check if has room to copy
            slots_available = self.instrument.query('DATA:NVOLatile:FREE?').strip() #returns a number corresponding to num_slots_free
            if int(slots_available) == 0:
                stored_wfs = self.instrument.query('DATA:NVOLatile:CATalog?').strip() #checks the stored_wfs in voltatile memory
                stored_wfs_list = stored_wfs.replace('"', '').split(',')
                name_to_delete = ask_user_to_select(stored_wfs_list)
                self.instrument.write(":DATA:DEL {}".format(name_to_delete))

            self.instrument.write(":DATA:COPY {}, VOLATILE".format(name))

    def set_arb_waveform(self, channel, name):
        """
        Sets the arbitrary waveform to be generated on the selected channel
        args:
            channel (int): The channel to set the arbitrary waveform on
            name (str): The name of the arbitrary waveform to be set
        """
        self.instrument.write(":FUNC{}:USER {}".format(channel, name)) #makes current USER selected name, but does not switch instrument to it
        self.instrument.write(":FUNC{} USER".format(channel)) #switches instrument to user waveform

    #trigger and sync functions
    def set_trigger_source(self, channel, trigger_source):
        """
        Sets the trigger source for the selected channel
        args:
            channel (int): The channel to set the trigger source on
            trigger_source (str): The trigger source, e.g., 'internal', 'external', 'manual'
        """ 
        conversion = {'IMM': "IMM", "INT": "INT2", "EXT": "EXT", "MAN": "MAN"} #convert commands to instrument specific ones
        self.instrument.write(":ARM:SOUR{} {}".format(channel, conversion[trigger_source]))

    def set_trigger_level(self, channel, trigger_level):
        """
        Sets the trigger level for the selected channel
        args:
            channel (int): The channel to set the trigger level on
            trigger_level (float): The trigger level in volts
        """
        self.instrument.write(":ARM:LEV {}".format(trigger_level))

    def set_trigger_slope(self, channel, trigger_slope):
        """
        Sets the trigger slope for the selected channel
        args:
            channel (int): The channel to set the trigger slope on
            trigger_slope (str): The trigger slope, e.g., 'rising', 'falling'
        """
        self.instrument.write(":ARM:SLOP {}".format(trigger_slope))


    def set_trigger_mode(self, channel, trigger_mode):
        """
        Sets the trigger mode for the selected channel
        args:
            channel (int): The channel to set the trigger mode on
            trigger_mode (str): The trigger mode, e.g., 'EDGE'
        """
        self.instrument.write(":ARM:SENS{} {}".format(channel, trigger_mode))
        
    def configure_trigger(self, channel, trigger_source=None, trigger_level=None, trigger_slope=None, trigger_mode=None):
        """
        Configures the trigger for the selected channel. Calls the set_trigger_source, set_trigger_level, set_trigger_slope, and set_trigger_mode functions to configure the trigger
        args:
            channel (int): The channel to configure the trigger on
            trigger_source (str): The trigger source
            trigger_level (float): The trigger level in volts
            trigger_slope (str): The trigger slope
            trigger_mode (str): The trigger mode
        """
        if trigger_source is None:
            self.set_trigger_source(channel, trigger_source)
        if trigger_level is not None:
            self.set_trigger_level(channel, trigger_level)
        if trigger_slope is not None:
            self.set_trigger_slope(channel, trigger_slope)
        if trigger_mode is not None:
            self.set_trigger_mode(channel, trigger_mode) 

    #additional methods
    def configure_output_amplifier(self, channel: str='1', type: str='HIV'):
        """
        This program configures the output amplifier for either maximum bandwith or amplitude. Taken from EKPY.
        NOTE: If in HIV mode max frequnecy is 50MHz, otherwise you get the full 120MHz
        NOTE: if sending a sin wave above 120MHz max voltage is 3V_pp
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            type (str): Amplifier Type args = [HIV (MAximum Amplitude), HIB (Maximum Bandwith)]
        """
        if type == 'HIV':
            self.amplitude = (0, 10)
            self.frequency = {'func': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
        if type == 'HIB':
            self.amplitude = (0, 5)
            self.frequency = {'func': {'SIN': (1e-6, 5e6), 'SQU': (1e-6, 50e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 50e6), 'pattern': (1e-6, 50e6), 'USER': (1e-6, 50e6)}}
        self.instrument.write("OUTP{}:ROUT {}".format(channel, type))

    #Helper Functions
def scale_waveform_data(data: np.array, preserve_vertical_resolution: bool=False) -> np.array:
        """
        Helper function that scales values to a max of 8191 in such a way that the abs(max) is 8191
        and the rest is uniformly scaled. All VALUES SHOULD BE INTEGERS
        NOTE YOU LOSE RESOLUTION WITH THIS METHOD if preserve_vertical_resoltuion is false, but it preserves the wf shape!
        shuld print estimated lost in  PP VOLTAGE from resolution
        """
        max_abs = np.max(abs(data))
        max_inst = 8191
        scale_factor = None
        if preserve_vertical_resolution:
            scale_factor = max_inst/max_abs
        else:
            while is_integer(scale_factor) is False: #this preserves scaling at the cost of vertical resolution
                if max_inst < 4095:
                    print("CAN NOT PRESERVE WF OVER HALF OF RESOLUTION IS GONE")
                    scale_factor = 8191/max_abs #will not preserve scaling when rounding to ints
                    break
                scale_factor = max_inst/max_abs
                max_inst -= 1
        scaled_data = data*scale_factor
        total = 8191*2 + 1
        loss = 100* (abs(np.max(scaled_data)) + abs(np.min(scaled_data)))/total
        print("Estimated Peak-to-Peak Ratio of targeted value is {:.1f}%".format(loss))
        return scaled_data.astype(np.int32)

def ask_user_to_select(options):
        """
        Helper function to format options to choose taken from help with CHATGPT
        EXAMPLE USAGE:
        # List of options
        options = ['ARB1', 'PV', 'PUND', 'DWM']

        # Ask the user to select an option
        selected_option = ask_user_to_select(options)
        print(f"You selected: {selected_option}")
        1. ARB1
        2. PV
        3. PUND
        4. DWM
        """
        # Display the options
        for i, option in enumerate(options, start=1):
            print(f"{i}. {option}")

        # Ask the user to select an option
        while True:
            try:
                choice = int(input("Enter the number of your choice: "))
                if 1 <= choice <= len(options):
                    return options[choice - 1]
                else:
                    print(f"Please enter a number between 1 and {len(options)}.")
            except ValueError:
                print("Invalid input. Please enter a number.")

def is_integer(n):
        """
        Helper function to check if a number is an intger including stuff like 5.0
        Taken with help from ChatGPT
        """
        if isinstance(n, int):
            return True
        elif isinstance(n, float):
            return n.is_integer()
        else:
            return False