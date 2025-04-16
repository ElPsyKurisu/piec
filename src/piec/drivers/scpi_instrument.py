"""
Set's up the scpi instrument class that all scpi instruments will inherit basic functionlity from to be followed by sub classes (e.g. scope, wavegen)
"""
from typing import Union
import numpy as np
import pandas as pd
from pyvisa import ResourceManager
import pyvisa
import time
import re
import json
import os
from piec.drivers.instrument import Instrument

"""
Code added to help support self._check_params, with help from ChatGPT
"""
import functools
import inspect

def auto_check_params(func):
    """
    This was taken with help from ChatGPT. Used to call self._check_params first whenever
    a function is called if the class boolean flag check_params=True. Note, it also has a secondary
    function that intercepts all arguments given to a function and converts them to lowercase.
    This is done to ensure that our logic can be case-insensitive and when writing functions we ALWAYS
    write things using lowercase.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        # Bind the passed arguments to the function's signature.
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        
        # Convert all bound arguments to lowercase as needed.
        lower_params = convert_to_lowercase(bound_args.arguments)
        
        # If check_params is enabled, call your parameter-checking function.
        if getattr(self, 'check_params', False):
            self._check_params(lower_params)
        
        # Reconstruct the arguments in the correct order.
        new_args = []
        for param in sig.parameters:
            new_args.append(lower_params[param])
        
        # Call the original function with the lowercased arguments.
        return func(*new_args)
    
    return wrapper

class AutoCheckMeta(type):
    def __new__(metacls, name, bases, class_dict):
        new_class_dict = {}
        for attr_name, attr_value in class_dict.items():
            # Skip decoration for init func, and any internal functions.
            if callable(attr_value) and not attr_name.startswith("_"): 
                attr_value = auto_check_params(attr_value)
            new_class_dict[attr_name] = attr_value
        return super().__new__(metacls, name, bases, new_class_dict)

"""
self._check_params support code complete
"""

class VirtualRMInstrument:
    """
    This class replaces the resource manager object in the virtual case,
    just needs to replace the .write() and .query() methods
    """
    def __init__(self, verbose:bool = False):
        self.verbose = verbose
        print('INITIALIZING VIRTUAL RESOURCE MANAGER, VISA NOT CONNECTED')
        current_dir = os.path.dirname(__file__)

        # Construct the full path to the virtual query JSON file
        json_path = os.path.join(current_dir, "virtual_scpi_queries.json")

        # Load the JSON file
        with open(json_path, "r") as file:
            self.query_dict = json.load(file)

    def query(self, input:str):
        time.sleep(0.01)
        if self.verbose:
            print('Query recieved: ',input)
        try:
            return self.query_dict[input]
        except:
            print('QUERY: ', input, ' NOT IN virtual_scpi_queries.json')
            return "VIRTUAL QUERY:"+ input


    def write(self, input:str):
        time.sleep(0.01)
        if self.verbose:
            print('Write recieved: ',input)
    
    def write_binary_values(self, data, scaled_data, datatype='h'):
        time.sleep(0.01)
        if self.verbose:
            print('Binary write recieved: ', data, scaled_data, datatype)

# Define a class
class SCPI_Instrument(Instrument, metaclass=AutoCheckMeta):
    # Initializer / Instance attributes
    def __init__(self, address, check_params=False):
        rm = ResourceManager()
        if address == 'VIRTUAL':
            self.instrument = VirtualRMInstrument() # initiate instrument in virtual mode
        else:
            self.instrument = rm.open_resource(address) #comment out to debug without VISA connection
        self.virtual = (address=='VIRTUAL')
        self.check_params = check_params

    def _debug(self, **args):
        """
        Debugging Function for _check_params not intended for actual code use, REQUIRES self.instrument above to be commented out
        """
        self._check_params(locals()['args']) #only need this here since i did **args

    # Generic Methods all instruments should have
    def idn(self):
        """
        Queries the instrument for its ID

        """
        return self.instrument.query("*IDN?")


    def reset(self):
        """
        Resets the instrument to its default parameters
        """
        self.instrument.write("*RST")

    def initialize(self):
        """
        Resets the instrument and clears the registry
        """
        self.instrument.write("*RST")
        self.instrument.write("*CLS")

    def operation_complete_query(self):
        """
        Asks the instrument if the operation is complete by sending the *OPC query
        Returns a 1 if complete
        Note that using the *OPC? query holds the I/O bus until the instrument commands have been completed. 
        It may not be acceptable to hold the GPIB bus when you are controlling multiple instruments. In those cases
        use the *OPC bit in the Standard Event register and implement some form of status reporting system. An example
        using the *OPC bit is provided in the Using SRQ Events section.
        """
        response = self.instrument.query("*OPC?")
        return response.strip()

    def read_output(self) -> list:
        """
        This simply sees if there is anything to read and returns an empty list of nothing to read
        """
        try:
            data = self.instrument.read()
            if data == '':
                return []
            else:
                return data
        except pyvisa.errors.VisaIOError:
            return []

    def check_errors(self):
        """
        Returns a list of errors or None if there are no errors
        Technically not an IEEE Mandated command but all instruments for our purposes should use this.
        With help from ChatGPT
        """
        errors = []
        start_time = time.time()
        while True:
            current_time = time.time()
            if current_time - start_time > 5:
                break
            error = self.instrument.query('SYST:ERR?')
            if check_error_string(error):
                break
            errors.append(error)
        if len(errors) == 0:
            errors = None
        return errors


    def print_specs(self):
        """
        Function that lists all class attributes for the instrument. NOTE: May not work in virtual case
        """
        spec_dict = get_class_attributes_from_instance(self)
        for key in spec_dict:
            if spec_dict[key] != type(dict):
                print(key, ':', spec_dict[key])
            else:
                key_dict = getattr(self, key) #this is a dict that the key is the type e.g. list or dict
                key_dict_key = list(key_dict.keys())[0]
                key_dict_key_value = key_dict[key_dict_key]
                print(key, ':', key_dict_key_value)
            
    def _check_params(self, locals_dict):
        """
        Want to check class attributes and arguments from the function are in acceptable ranges. Uses .locals() to get all arguments and checks
        against all class attributes and ensures if they match the range is valid NOTE: locals_dict is always lower
        Added recursive_lower to ensure that if we have a class attribute like temp = ['one', 'two'] its the same as ['OnE', 'TWO'] etc
        """
        class_attributes = recursive_lower(get_class_attributes_from_instance(self))
        keys_to_check = get_matching_keys(locals_dict, class_attributes)
        for key in keys_to_check:
            attribute_value = recursive_lower(getattr(self, key)) #allowed types are strings, tuples, lists, and dicts
            if attribute_value is None:
                print("Warning no range-checking defined for \033[1m{}\033[0m, skipping _check_params".format(key)) #makes bold text
                continue
            input_value = locals_dict[key]
            if input_value is None:
                continue #skips checking for placeholder values
            if type(attribute_value) == tuple:
                if not is_value_between(input_value, attribute_value): #will error need to make key values correct
                    exit_with_error("Error input value of \033[1m{}\033[0m for arg \033[1m{}\033[0m is out of acceptable Range \033[1m{}\033[0m".format(input_value, key, attribute_value))
            if type(attribute_value) == list:
                if not is_contained(input_value, attribute_value): #checks if the input value is in the allowed list
                    exit_with_error("Error input value of \033[1m{}\033[0m for arg \033[1m{}\033[0m is not in list of acceptable \033[1m{}\033[0m".format(input_value, key, attribute_value))
            if type(attribute_value) == dict:
                #need helper function here
                attribute_key = get_matching_keys(locals_dict, attribute_value) #this is the first key in the class attribute dict
                if len(attribute_key) != 1:
                    print("WARNING found {} keys instead of 1, skipping {} checking".format(len(attribute_key), key))
                else: #assumes input is range btw, since no other reason for using a dict i believe. WIll update if changes
                    local_value = locals_dict[attribute_key[0]] #this is the value
                    attribute_sub_dict = attribute_value[attribute_key[0]]
                    if not is_value_between(input_value, attribute_sub_dict[local_value]):
                        exit_with_error("Error input value of \033[1m{}\033[0m for arg \033[1m{}\033[0m is out of acceptable Range \033[1m{}\033[0m".format(input_value, attribute_key, attribute_sub_dict[local_value]))

class Scope(SCPI_Instrument):
    """
    Sub-class of Instrument to hold the general methods used by scopes. For Now defaulted to DSOX3024a, but can always ovveride certain SCOPE functions
    """
    #Should be overriden
    #Screen stuff
    voltage_range = None #entire screen range
    voltage_scale = None #units per division
    reference = None
    time_range = None   
    time_scale = None
    time_base_type = None
    time_reference = None
    acquire_type = None
    impedance = None
    #trigger attributes
    trigger_source = None
    trigger_type = None
    trigger_sweep = None
    trigger_input_coupling = None
    trigger_edge_slope = None
    trigger_filter_type = None
    #idk
    channel = None
    source = None

    def autoscale(self):
        """
        Function that autoscales the instrument.
        """
        self.instrument.write(":AUToscale") 

    def configure_acquire_type(self, acquire_type = None):
        """
        NOTE: I'm not sure where this function should fit under so for now it is seperate.
        args:
            acquire_type (str): Type to acquire data with, note NORM is probably best ['NORM', 'HRES', 'PEAK']
        """
        if acquire_type is not None:
            self.instrument.write(":ACQuire:TYPE {}".format(acquire_type))

    def configure_timebase(self, time_base_type=None, position=None,
                       time_reference=None, time_range=None, time_scale=None, vernier=None):
        """Configures the timebase of the oscilliscope. Adapted from EKPY program 'Configure Timebase (Basic)'
        Should call initialize first.

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            time_base_type (str): Allowed values are 'MAIN', 'WINDow', 'XY', and 'ROLL', note must use main for data acquisition
            position (str): The position in the scope, [0.0] is a good default This is actually the delay on the scope (moves in time right and left) max value depends on time/div settings
            time_reference (str): The reference of where to start position
            time_range (str): The x range of the scope min is 20ns, max is 500s
            time_scale (str): The x scale of the scope in units of s/div min is 2ns, max is 50s
            vernier (boolean): Enables Vernier scale
        """
        if time_base_type is not None:
            self.instrument.write("TIM:MODE {}".format(time_base_type))
        if position is not None:
            self.instrument.write("TIM:POS {}".format(position))
        if time_range is not None:
            self.instrument.write("TIM:RANG {}".format(time_range))
        if time_reference is not None:
            self.instrument.write("TIM:REF {}".format(time_reference))
        if time_scale is not None:
            self.instrument.write("TIM:SCAL {}".format(time_scale))
        if vernier is not None:
            if vernier:
                self.instrument.write("TIM:VERN ON")
            else:
                self.instrument.write("TIM:VERN OFF")

    def configure_channel(self, channel: str='1', voltage_scale: str=None, voltage_range: str=None,
                              voltage_offset: str=None, coupling: str=None, probe_attenuation: str=None, 
                              impedance: str=None, display_channel=None):
        """Sets up the voltage measurement on the desired channel with the desired paramaters. Adapted from
        EKPY. 

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            channel (str): Desired channel allowed values are 1,2,3,4
            voltage_scale (str): The vertical scale in units of v/div
            voltage_range (str): The verticale scale range min: 8mv, max: 40V
            voltage_offset (str): The offset for the vertical scale in units of volts
            coupling (str): 'AC' or 'DC' values allowed
            probe_attenuation (str): Multiplicative factor to attenuate signal to stil be able to read, max is most likely 10:1
            impedance (str): Configures if we are in high impedance mode or impedance match. Allowed factors are 'ONEM' for 1 M Ohm and 'FIFT' for 50 Ohm
            display_channel (boolean): Toggles the display of the channel
        """
        if voltage_scale is not None:
            self.instrument.write("CHAN{}:SCAL {}".format(channel, voltage_scale))
        if voltage_range is not None:
            self.instrument.write("CHAN{}:RANG {}".format(channel, voltage_range))
        if voltage_offset is not None:
            self.instrument.write("CHAN{}:OFFS {}".format(channel, voltage_offset))
        if coupling is not None:
            self.instrument.write("CHAN{}:COUP {}".format(channel, coupling))
        if probe_attenuation is not None:
            self.instrument.write("CHAN{}:PROB {}".format(channel, probe_attenuation))
        if impedance is not None:
            self.instrument.write("CHAN{}:IMP {}".format(channel, impedance))
        if display_channel is not None:
            if display_channel:
                self.instrument.write("CHAN{}:DISP ON".format(channel))
            else:
                self.instrument.write("CHAN{}:DISP OFF".format(channel))
    
    def configure_trigger_characteristics(self, trigger_type: str=None, trigger_holdoff_time: str=None, trigger_low_level: str=None,
                                      trigger_high_level: str=None, trigger_source: str=None, trigger_sweep: str=None,
                                       enable_high_freq_filter=None, enable_noise_filter=None):
        """Configures the trigger characteristics Taken from EKPY. 'Configures the basic settings of the trigger.'
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            trigger_type (str): Trigger type, accepted params are: [EDGE (Edge), GLIT (Glitch), PATT (Pattern), TV (TV), EBUR (Edge Burst), RUNT (Runt), NFC (Setup Hold), TRAN (Transition), SBUS1 (Serial Bus 1), SBUS2 (Serial Bus 2), USB (USB), DEL (Delay), OR (OR), NFC (Near Field Communication)]
            trigger_holdoff_time (str): Additional Delay in units of sec before re-arming trigger circuit
            trigger_low_level (str): The low trigger voltage level units of volts
            trigger_high_level (str): The high trigger voltage level units of volts
            trigger_source (str): Desired channel to trigger on allowed values are [CHAN1,CHAN2,CHAN3,CHAN4, EXT (there are more)]
            trigger_sweep (str): Allowed values are [AUTO (automatic), NORM (Normal)]
            enable_high_freq_filter (boolean): Toggles the high frequency filter
            enable_noise_filter (boolean): Toggles the noise filter
        """
        if trigger_type is not None:
            self.instrument.write(":TRIG:MODE {}".format(trigger_type))
        if enable_high_freq_filter is not None:
            if enable_high_freq_filter:
                self.instrument.write(":TRIG:HFR ON")
            else:
                self.instrument.write(":TRIG:HFR OFF")
        if trigger_holdoff_time is not None:
            self.instrument.write(":TRIG:HOLD {}".format(trigger_holdoff_time))
        if trigger_source is not None and trigger_low_level or trigger_high_level is not None:
            if trigger_high_level is not None:
                self.instrument.write(":TRIG:LEV:HIGH {}, {}".format(trigger_high_level, trigger_source))
            if trigger_low_level is not None:
                self.instrument.write(":TRIG:LEV:LOW {}, {}".format(trigger_low_level, trigger_source))
        else:
            print("WARNING \033trigger_source\033 has not been set, allowed args are {}".format(self.trigger_source))
        if trigger_sweep is not None:
            self.instrument.write(":TRIG:SWE {}".format(trigger_sweep))
        if enable_noise_filter is not None:
            if enable_noise_filter:
                self.instrument.write(":TRIG:NREJ ON")
            else:
                self.instrument.write(":TRIG:NREJ OFF")

    def configure_trigger_edge(self, trigger_source: str='CHAN1', trigger_input_coupling: str='AC', trigger_edge_slope: str='POS', 
                           trigger_level: str='0', trigger_filter_type: str='OFF'):
        """Configures the trigger characteristics Taken from EKPY. 'Configures the basic settings of the trigger.'
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            trigger_source (str): Desired channel/source to trigger on allowed values are: [CHAN1,CHAN2,CHAN3,CHAN4,DIG0,DIG1 (there are more)]
            trigger_input_coupling (str): Allowed values = [AC, DC, LFR (Low Frequency Coupling)]
            trigger_edge_slope (str): Allowed values = [POS, NEG, EITH (either), ALT (alternate)]
            trigger_level (str): Trigger level in volts
            trigger_filter_type (str): Allowed values = [OFF, LFR (High-pass filter), HFR (Low-pass filter)] Note: Low Frequency reject == High-pass
        """
        if trigger_source is not None:
            self.instrument.write(":TRIG:SOUR {}".format(trigger_source))
        if trigger_input_coupling is not None:
            self.instrument.write(":TRIG:COUP {}".format(trigger_input_coupling))
        if trigger_level is not None:
            self.instrument.write(":TRIG:LEV {}".format(trigger_level))
        if trigger_filter_type is not None:
            self.instrument.write(":TRIG:REJ {}".format(trigger_filter_type))
        if trigger_edge_slope is not None:
            self.instrument.write(":TRIG:SLOP {}".format(trigger_edge_slope))

    def initiate(self):
        """
        The :DIGitize command is a specialized RUN command. It causes the instrument 
    to acquire waveforms according to the settings of the :ACQuire commands 
    subsystem. When the acquisition is complete, the instrument is stopped.
    If no argument is given, :DIGitize acquires the channels currently displayed. If no 
    channels are displayed, all channels are acquired.

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
        """
        self.instrument.write(":DIG")
        self.instrument.write("*CLS")
    
    """
    NOTE: GOT UP TO HERE FOR CLEANING UP SCOPE
    """

    def setup_wf(self, source: str='CHAN1', byte_order: str='MSBF', format: str='byte', points: str='1000', 
             points_mode: str='NORMal', unsigned: str='OFF'):
        """Sets up the waveform with averaging or not and of a specified format/count
        NOTE: Default args here work with default args of query_wf 
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            source (str): Desired channel allowed values are [CHAN1, CHAN2, CHAN3, CHAN4, FUNC, SBUS1, etc]
            byte_order (str): Either MSBF (most significant byte first) or LSBF (least significant byte first)
            format (str): Format of data allowed args are [ASCii (floating point), WORD (16bit two-bytes), BYTE (8-bit)]
            points (str): Number of data points for the waveform to return allowed args are [100,250,500,1000] for NORM or up to [8000000] for MAX or RAW
            points_mode (str): Mode for points allowed args are [NORM (normal), MAX (maximum), RAW]
            unsigned (str): Allows to switch between unsigned and signed integers [OFF (signed), ON (unsigned)]
        """
        if source is not None:
            self.instrument.write(":WAVeform:SOURce {}".format(source))
        else:
            print("WARNING no source defined")
        if byte_order is not None:
            self.instrument.write(":WAVeform:BYTeorder {}".format(byte_order))
        if format is not None:
            self.instrument.write(":WAVeform:FORMat {}".format(format))
        if points_mode is not None:
            self.instrument.write(":WAVeform:POINts:MODE {}".format(points_mode))
        if points is not None:
            self.instrument.write(":WAVeform:POINts {}".format(points))
        if unsigned is not None:
            self.instrument.write(":WAVeform:UNSigned {}".format(unsigned))

    def query_wf(self, byte_order: str='MSBF', unsigned: str='OFF'):
        """Returns the specified channels waveform with averaging or not and of a specified format/count, call
        setup_wf first to intialize it correctly. This function only calls queries. First calls preamble to get
        data format. Then parses data and converts data to usable format.
        GET_PREAMBLE - The preamble block contains all of the current
        ' WAVEFORM settings. It is returned in the form <preamble_block><NL>
        ' where <preamble_block> is:
        ' FORMAT : int16-0= BYTE, 1 = WORD, 4 = ASCII.
        ' TYPE : int16-0= NORMAL, 1 = PEAK DETECT, 2 = AVERAGE
        ' POINTS : int32 - number of data points transferred.
        ' COUNT : int32 - 1 and is always 1.
        ' XINCREMENT : float64 - time difference between data points.
        ' XORIGIN : float64 - always the first data point in memory.
        ' XREFERENCE : int32 - specifies the data point associated with
        ' x-origin.
        ' YINCREMENT : float32 - voltage diff between data points.
        ' YORIGIN : float32 - value is the voltage at center screen.
        ' YREFERENCE : int32 - specifies the data point where y-origin
        ' occurs 

        First it calls operation complete to ensure its finished taking data
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight DSOX3024a
            byte_order (str): Either MSBF (most significant byte first) or LSBF (least significant byte first)
            unsigned (str): Allows to switch between unsigned and signed integers [OFF (signed), ON (unsigned)]

        returns:
            preamble_dict (dict) Dictionary with all params labeled. (MetaData)
            time (list): Python list with all the scaled time (x_data array)
            wfm (list): Python list with all the scaled y_values (y_data array) 
        """
        check = self.operation_complete_query() #add error handling if not returns 1
        if check != '1':
            exit_with_error("Scope Not Ready: Operation Complete Query Failed")
        preamble = self.instrument.query(":WAVeform:PREamble?")
        preamble1 = preamble.split()
        preamble_list = preamble1[0].split(',')
        preamble_dict = {
        'format': np.int16(preamble_list[0]),
        'type': np.int16(preamble_list[1]),
        'points': np.int32(preamble_list[2]),
        'count': np.int32(preamble_list[3]),
        'x_increment': np.float64(preamble_list[4]),
        'x_origin': np.float64(preamble_list[5]),
        'x_reference': np.int32(preamble_list[6]),
        'y_increment': np.float32(preamble_list[7]),
        'y_origin': np.float32(preamble_list[8]),
        'y_reference': np.int32(preamble_list[9]),
        }
        if byte_order == 'msbf':
            is_big_endian = True
        if byte_order == 'lsbf':
            is_big_endian = False
        if unsigned == 'off':
            is_unsigned = False
        if unsigned == 'on':
            is_unsigned = True
        if self.virtual:
            data_df = pd.read_csv(os.path.join(os.path.dirname(__file__), "virtual_osc_trace.csv"))
            time = data_df['time (s)'].values
            wfm = data_df['voltage (V)'].values
        else:
            if preamble_dict["format"] == 0 and not is_unsigned:
                data = self.instrument.query_binary_values("WAVeform:DATA?", datatype='b', is_big_endian=is_big_endian)
            if preamble_dict["format"] == 0 and is_unsigned:
                data = self.instrument.query_binary_values("WAVeform:DATA?", datatype='B', is_big_endian=is_big_endian)
            if preamble_dict["format"] == 1 and not is_unsigned:
                data = self.instrument.query_binary_values("WAVeform:DATA?", datatype='h', is_big_endian=is_big_endian)
            if preamble_dict["format"] == 1 and is_unsigned:
                data = self.instrument.query_binary_values("WAVeform:DATA?", datatype='H', is_big_endian=is_big_endian)
            if preamble_dict["format"] == 4:
                data = self.instrument.query_ascii_values("WAVeform:DATA?")
            time = []
            wfm = []
            for t in range(preamble_dict["points"]):
                time.append((t* preamble_dict["x_increment"]) + preamble_dict["x_origin"])
            for d in data:
                wfm.append((d * preamble_dict["y_increment"]) + preamble_dict["y_origin"])
        return preamble_dict, time, wfm


class Awg(SCPI_Instrument):
    """
    Sub-class of Instrument to hold the general methods used by an awg. For Now defaulted to keysight81150a, but can always ovveride certain SCOPE functions
    """
    #Should be overriden
    channel = None
    voltage = None
    frequency = None
    func = None #might be useless since all awgs should have sin, squ, pulse etc
    slew_rate = None #1V/ns
    source_impedance = None
    load_impedance = None

    def configure_impedance(self, channel: str='1', source_impedance: str='50', load_impedance: str='50.0'):
        """
        This program configures the output and input impedance of the wavegen. Taken from EKPY.
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            source_impedance (str): The desired source impedance in units of Ohms, allowed args are [5, 50]
            load_impedance (str): The desired load impedance in units of Ohms, allowed args are [0.3 to 1E6]

        """
        self.instrument.write(":OUTP{}:IMP {}".format(channel, source_impedance))
        self.instrument.write(":OUTP{}:IMP:EXT {}".format(channel, load_impedance))

    def configure_trigger(self, channel: str='1', trigger_source: str='IMM', mode: str='EDGE', slope: str='POS'):
        """
        This program configures the trigger. Taken from EKPY.
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            trigger_source (str): Trigger source allowed args = [IMM (immediate), INT2 (internal), EXT (external), MAN (software trigger)]
            mode (str): The type of triggering allowed args = [EDGE (edge), LEV (level)]
            slope (str): The slope of triggering allowed args = [POS (positive), NEG (negative), EIT (either)]
        """ 
        self.instrument.write(":ARM:SOUR{} {}".format(channel, trigger_source))
        self.instrument.write(":ARM:SENS{} {}".format(channel, mode))
        self.instrument.write(":ARM:SLOP {}".format(slope))

    def create_arb_wf(self, data: Union[np.array, list], name=None, channel='1'):
        """
        NOTE: DOES NOT SCALE HORIZONTALLY YET-> aka wont fill out to 524288 points
        This program creates an arbitrary waveform within the limitations of the
        Keysight 81150A which has a limit of 2 - 524288 data points. In order to send data
        in accordance with the 488.2 block format which looks like #ABC, where '#' marks the start
        of the data flow and 'A' refers to the number of digits in the byte count, 'B' refers to the
        byte count and 'C' refers to the actual data in binary. The data is first scaled between
        -8191 to 8191 in accordance to our instrument. Adapted from EKPY (note their arrays
        contain 10,000 elements). 
        Note: Will NOT save waveform in non-volatile memory if all the user available slots are
        filled (There are 4 allowed at 1 time plus 1 in volatile memory).

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            data (ndarray or list): Data to be converted to wf
            name (str): Name of waveform, must start with A-Z
            channel (str): What channel to put the volatile WF on
        """  
        # Ensure data is a numpy array
        data = np.array(data)
        #check length of data is valid
        self._check_params({"arb_wf_points_range":len(data)}) #add extra item to check, so we have to manually call self._check_params here

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

    def create_arb_wf_legacy(self, data, name=None):
        """
        NOTE THIS IS SUPERCEDED BY THE BINARY INTERPRETATION
        This program creates an arbitrary waveform using the slow non binary format, see create_arbitrary_wf_binary for more info
        NOTE: Will NOT save waveform in non-volatile memory, unless a name is given.
        NOTE: Will NOT save waveform in non-volatile memory if all the user available slots are
        filled (There are 4 allowed at 1 time plus 1 in volatile memory).
        Also for 10k points it is quite slow, allow for like 3 seconds to send the data. Will need to rewrite the binary version
        if we want speed

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            data (ndarray or list): Data to be converted to wf
            name (str): Name of waveform, must start with A-Z
        """
        data_string = ""
        for i in range(len(data)):
            data_string += str(data[i]) +','
        data_string = data_string[:-1] #remove last comma
        self.instrument.write(":DATA VOLATILE, {}".format(data_string))
        if name is not None:
            self.instrument.write(":DATA:COPY {}, VOLATILE".format(name))


    def configure_wf(self, channel: str='1', func: str=None, voltage: str=None, offset: str=None, frequency: str=None, duty_cycle=None,
                      num_cycles=None, invert: bool=None, user_func: str="VOLATILE"):
        """
        This function configures the named func with the given parameters. Works on both user defined and built-in functions
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            func (str): The function name as saved on the instrument
            voltage (str): The V_pp of the waveform in volts
            offset (str): The voltage offset in units of volts
            frequency (str): the frequency in units of Hz for the arbitrary waveform
            duty_cycle (str): duty_cycle defined as 100* pulse_width / Period ranges from 0-100, (cant actually do 0 or 100 but in between is fine)
            num_cycles (str): number of cycles by default set to None which means continous NOTE only works under BURST mode, not implememnted
            invert (bool): Inverts the waveform by flipping the polarity
            user_func (str): name of the user defined function as saved on the instrument.
        """
        #might need to rewrite check_params here
        #self._check_params(locals()) #this wont work for user defined functions...
        #user_funcs = self.instrument.query(":DATA:CAT?")
        #user_funcs_list = user_funcs.replace('"', '').split(',')
        if func is None:
            raise Warning("Warning no func is decided, please input a valid function such as \033{}\033".format(self.func)) #will this error if self.func is None? should check
        if func == 'user':
            self._configure_arb_wf(channel, user_func, voltage, offset, frequency, invert)
        else: #assumes built in
            self._configure_built_in_wf(channel, func, frequency, voltage, offset, duty_cycle)


    def _configure_built_in_wf(self, channel: str='1', func=None, frequency=None, voltage=None, offset=None, duty_cycle=None, invert: bool=False):
        """
        Decides what built-in wf to send - by default sin

        args:
            self (pyvisa.resources.ENET-Serial INSTR): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            func (str): Desired output function, allowed args are [SIN (sinusoid), SQU (square), RAMP, PULSe, NOISe, DC, USER (arb)]
            frequency (str): frequency in Hz (have not added suffix funcitonaility yet)
            voltage (str): The V_pp of the waveform in volts
            offset (str): DC offset for waveform in volts
            duty_cycle (str): duty_cycle defined as 100* pulse_width / Period ranges from 0-100, (cant actually do 0 or 100 but in between is fine)
            num_cycles (str): number of cycles by default set to None which means continous NOTE only works under BURST mode, not implememnted
            invert (bool): Inverts the waveform by flipping the polarity
        """
        if func is None:
            raise Warning("Warning no func is decided, please input a valid function such as \033{}\033".format(self.func))
        else:
            self.instrument.write(":SOUR:FUNC{} {}".format(channel, func))
        if frequency is not None:
            self.instrument.write(":SOUR:FREQ{} {}".format(channel, frequency))
        if offset is not None:
            self.instrument.write(":VOLT{}:OFFS {}".format(channel, offset))
        if voltage is not None:
            self.instrument.write(":VOLT{} {}".format(channel, voltage))
        if func == 'squ':
            self.instrument.write(":SOUR:FUNC{}:SQU:DCYC {}".format(channel, duty_cycle)) 
        if func == 'puls':
            self.instrument.write(":SOUR:FUNC{}:PULS:DCYC {}".format(channel, duty_cycle))
        if invert is not None:
            if invert:
                self.instrument.write(":OUTP{}:POL INV".format(channel))
            else:
                self.instrument.write(":OUTP{}:POL NORM".format(channel))

    def _configure_arb_wf(self, channel: str='1', name='VOLATILE', voltage: str=None, offset: str=None, frequency: str=None, invert: bool=None):
        """
        This program configures arbitrary waveform already saved on the instrument. Adapted from EKPY. 
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            name (str): The Arbitrary Waveform name as saved on the instrument, by default VOLATILE
            voltage (str): The V_pp of the waveform in volts
            offset (str): The voltage offset in units of volts
            frequency (str): the frequency in units of Hz for the arbitrary waveform
            invert (bool): Inverts the waveform by flipping the polarity
        """
        if self.slew_rate is not None:
            try:
                points = self.instrument.query(":DATA:ATTR:POIN? {}".format(name)).strip() #seems like trouble
                if (float(voltage))/(float(frequency)/float(points)) > self.slew_rate:
                        print('WARNING: DEFINED WAVEFORM IS FASTER THAN AWG SLEW RATE')
            except:
                print("WARNING COULD NOT CHECK IF DEFINED WAVEFORM IS FASTER THAN AWG SLEW RATE")
        self.instrument.write(":FUNC{}:USER {}".format(channel, name)) #makes current USER selected name, but does not switch instrument to it
        self.instrument.write(":FUNC{} USER".format(channel)) #switches instrument to user waveform
        if voltage is not None:
            self.instrument.write(":VOLT{} {}".format(channel, voltage))
        if frequency is not None:
            self.instrument.write(":FREQ{} {}".format(channel, frequency))
        if offset is not None:
            self.instrument.write(":VOLT{}:OFFS {}".format(channel, offset))
        if invert is not None:
            if invert:
                self.instrument.write(":OUTP{}:POL INV".format(channel))
            else:
                self.instrument.write(":OUTP{}:POL NORM".format(channel))


    def output_enable(self, channel: str='1', on=True):
        """
        This program toggles the selected output. Taken from EKPY. 
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            on (boolean): True for on, False for off
        """
        if on:
            self.instrument.write(":OUTP{} ON".format(channel))
        else:
            self.instrument.write(":OUTP{} OFF".format(channel))

    def display_enable(self, on=True):
        """
        This program toggles the display On or OFF, it is recommended for programming speed to disale the display
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            on (boolean): True for display on, False for off
        """
        if on:
            self.instrument.write("DISP ON")
        else:
            self.instrument.write("DISP OFF")

    def send_software_trigger(self):
        """
        This program sends the software trigger. Taken from EKPY. 
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
        """
        self.instrument.write(":TRIG")

    def stop(self):
        """Stop the awg.

        args:
            self (pyvisa.resources.ENET-Serial INSTR): Keysight 81150A
        """
        if self.channel is not None:
            for i in self.channel:
                self.output_enable(i, False) #sets all listed channels to false
        else:
            #Using generic code
            print("Warning, using generic AWG class will default to turning off only channel 1")
            self.output_enable('1', False) 
        
    def couple_channels(self, master_channel ='1', on=True):
        """
        In the Channel Coupling mode, the frequency and phase of both the 
        channels are locked. Locking the output frequency and phase of both 
        channels does have a noticeable effect on most of the major modes of 
        operation. Therefore, as a result of coupling, the output function, and all other 
        parameters like, burst, sweep, and modulation are also kept identical on 
        both channels. NOTE: Copies all values of master_channel onto other channels

        args:
            self (pyvisa.resources.ENET-Serial INSTR): Keysight 81150A
            master_channel (str): Allowed args are ["1", "2", etc] based on num of instrument channels
            on (Boolean): True for on and False for off, toggles channel coupling
            
        """
        if on:
            self.instrument.write(":TRACK:CHAN{} ON".format(master_channel))
        else:
            self.instrument.write(":TRACK:CHAN{} OFF".format(master_channel))


class Lockin(SCPI_Instrument):
    """
    Sub-class of Instrument to hold the general methods used by a lockin. For Now defaulted to SRS830, but can always ovveride certain lockin funcs
    """
    #Should be overriden
    channel = None #['1','2'] allowed channels
    voltage = None #(4e-3, 5) SRS 830 values
    frequency = None
    phase = None #(-360.00,729.99) notice instruemnt rounds to 0.01 for you and will convert to +-180 e.g. PHAS 541.0 command will set the phase to -179.00°
    harmonic = None #(1,19999)
    trig = None #type of trig allowed from reference input ["sin", "rising", "falling"]
    sensitivity = None #note this is gonna be a long list ['2nv/fa', '5nv/fa', '10nv/fa', '20nv/fa', '50nv/fa', '100nv/fa','200nv/fa', '500nv/fa', '1uv/pa', '2uv/pa', '5uv/pa', '10uv/pa','20uv/pa', '50uv/pa', '100uv/pa', '200uv/pa', '500uv/pa','1mv/na', '2mv/na', '5mv/na', '10mv/na', '20mv/na', '50mv/na', '100mv/na', '200mv/na', '500mv/na', '1v/ua']
    reserve_mode = None #["high", "norm", "low"]
    time_constant = None #['10us', '30us', '100us', '300us', '1ms', '3ms', '10ms', '30ms', '100ms', '300ms', '1s', '3s', '10s', '30s', '100s', '300s', '1ks', '3ks', '10ks', '30ks']
    lp_filter_slope = None #['6','12','18','24']
    display = None #['primary', 'secondary', 'noise', 'auxA', 'auxB']
    ratio = None #['none', 'auxA', 'auxB']
    display_output = None #['display', 'primary']
    display_expand_what = None #['x', 'y', 'r']
    display_output_offset=None #(-105.00, 105.00)
    display_output_expand=None #['1', '10', '100']

    """
    NOTE: Should i just make sensitivty a range and so is time constant, and then you just pick the nearest one. I think I should offer both options ideally, basically if not in list
    then it defaults to finding the nearest one, always in SI units
    NOTE also everything should have a default value of None so you only change what you want to change, and leave rest default
    """

    def configure_internal_oscillator(self, voltage, frequency):
        """
        NOTE: This function is redundant as configure_reference covers all of it
        Function that configures the internal oscillator (based on the front panel of the SRS 830)
        NOTE: Configures the "Reference" part of the SRS 830 which deals with the interal oscillator

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830
            voltage (str): Desired amplitude of signal in units of volts
            frequency (str): Desired frequnecy of signal in units of Hz
        """
        self.instrument.write("slvl {}".format(voltage))
        self.instrument.write("freq {}".format(frequency))

    
    def configure_reference(self, voltage=None, frequency=None, source=None, trig=None, phase=None, harmonic=None):
        """
        Function that configures the reference part of lockin

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830
            voltage (str): Desired amplitude of signal in units of volts
            frequency (str): Desired frequency of signal in units of Hz, requires source to be set to internal
            source (str): Configures the reference source allowed args are [internal, external]
            trig (str): Configures the reference input mode. Allowed args are ["sin", "rising", "falling"] "The reference input can be a sine wave (rising zero crossing detected) or a TTL pulse or square wave (rising or falling edge). The input impedance is 1 MΩ AC coupled (>1 Hz) for the sine input. For low frequencies (<1Hz), it is necessary to use a TTL reference signal. The TTL input provides the best overall performance and should be used whenever possible."
            phase (str): Configures the phase_shift of the reference in degrees
            harmonic (str): Selects the desired harmonic 
        """
        if voltage is not None:
            self.instrument.write("slvl {}".format(voltage))
        if source == 'internal':
            self.instrument.write("fmod 1")
        if frequency is not None:
            self.instrument.write("freq {}".format(frequency)) #requires internal reference to be selected, otherwise it is dictated by external source
        if source == 'external':
            self.instrument.write("fmod 0")
        if trig == 'sin':
            self.instrument.write("rslp 0")
        if trig == "rising":
            self.instrument.write("rslp 1")
        if trig == "falling":
            self.instrument.write("rslp 2")
        if phase is not None:
            self.instrument.write("phas {}".format(phase))
        if harmonic is not None:
            self.instrument.write("harm {}".format(harmonic))
        
    def configure_gain_filters(self, sensitivity=None, reserve_mode=None, time_constant=None, lp_filter_slope=None, sync=None):
        """
        This is set to configure the left side of the srs 830 aka time_constant, filters, gain, etc

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830
            sensitivty (str): Sets the sensitivity range of the channels NOTE: either give value or set to auto in units of V/A
            reserve_mode (str): Toggles between ["high", "norm", "low"]
            time_constant (str): Sets the time constant in units of s
            lp_filter_slope (str): in units of dB/oct ['6','12','18','24']
            sync (str): "on" for synchronous filter on (below 200 Hz harmonic*reference_freq) "off" for off 
        """
        if sensitivity is not None:
            if sensitivity == 'auto':
                self.instrument.write("agan")
            elif self.sensitivity is not None: #ensures that properly formatted sensitivty list exists
                self.instrument.write("sens {}".format(self.sensitivity.index(sensitivity))) #note assumes the index of the list corresponds to the correct instrument code as it does in the SRS 830
            else:
                print("Warning cannot set the specified sensitivity try to autogain")
        if reserve_mode is not None:
            if self.reserve_mode is not None:
                self.instrument.write("rmod {}".format(self.reserve_mode.index(reserve_mode)))
            else:
                print("Warning cannot set the specified reserve mode, no reserve mode list")
        if time_constant is not None:
            if self.time_constant is not None:
                self.instrument.write("oflt {}".format(self.time_constant.index(time_constant)))
            else:
                print("Warning cannot set the specified time_constant, no time_constant list")
        if lp_filter_slope is not None:
            if self.lp_filter_slope is not None:
                self.instrument.write("ofsl {}".format(self.lp_filter_slope.index(lp_filter_slope)))
            else:
                print("Warning cannot set the specified lp_filter_slope, no lp_filter_slope list")
        if sync is not None:
            if sync == "on":
                self.instrument.write("sync 1")
            if sync == 'off':
                self.instrument.write("sync 0")

    def configure_display_outputs(self, channel=None, display=None, ratio=None, display_output=None, display_output_offset=None, display_output_expand=None, display_expand_what=None):
        """
        Configures the channel displays and what are output by them

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830
            channel (str): Desired channel to configure
            display (str): Desired param to display e.g. [primary, secondary, noise, AuxinA, AuxinB] Note for channel 2, X->Y R->Theta, etc but still pass in X for Y e.g. configure_display_outputs(2,X) will configure channel 2 to display Y
            ratio (str): ratio to scale display param by [none, auxA, auxB] 
            display_output (str): What to output via the bnc [display, primary]
            display_output_offset (str): Output offset, requires exand as well in units of percent (-105.00 ≤ x ≤ 105.00)
            display_output_expand (str): factor to expand by [1, 10, 100]
            display_expand_what (str): What to expand [x, y, r] NOTE: R is only available on Chn1, X and Y on both
        """
        if display is not None:
            if ratio == None:
                ratio = 'none'
            self.instrument.write("ddef {},{},{}".format(channel, self.display.index(display), self.ratio.index(ratio))) #note channel does not use index scheme
        if display_output is not None:
            self.instrument.write("fpop {},{}".format(channel, self.display_output.index(display_output)))
        if display_expand_what is not None:
            if display_output_offset is not None:
                if display_output_offset == 'auto':
                    self.instrument.write("aoff {}".format(self.display_expand_what.index(display_expand_what)+1)) #need to add 1 because for this it starts at 1 for X, 2 for Y, 3 for R
                if display_output_expand == None:
                    display_output_expand = "1"
                self.instrument.write("oexp {},{},{}".format(self.display_expand_what.index(display_expand_what)+1, display_output_offset, self.display_output_expand.index(display_output_expand))) #formats to 2 decimal places
        

    def measure_params(self, param_list):
        """
        Function that returns the requested params
        NOTE:
        The values of X and Y are recorded at a single instant. The values of R
        and θ are also recorded at a single instant. Thus reading X,Y OR R,θ
        yields a coherent snapshot of the output signal. If X,Y,R and θ are all
        read, then the values of X,Y are recorded approximately 10µs apart from
        R,θ. Thus, the values of X and Y may not yield the exact values of R and
        θ from a single SNAP? query. Call get_X_Y or get_R_theta intead if speed is priority.

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830
            param_list (list): List of requested params with mapping as follows (for SRS830): [(input, output): (1,X), (2,Y), (3,R), (4,Theta), (5, AUX In1), (6, AUX In2), (7, AUX In3), (8, AUX In4), (9, REF freq), (10,Ch1 Display), (11, Ch2 Display)]
        returns:
            (list): Returns float values if possible of selected params
        """
        params = ",".join(map(str, param_list))
        return_list = self.instrument.query('SNAP? {}'.format(params)).split('\n')[0].split(',')
        return_vals = []
        for i in return_list:
            try:
                return_vals.append(float(i))
            except:
                print("warning couldn't convert to float, raw data is preserved instead")
                return_vals.append(i)
        return return_vals
    
    def get_X_Y(self):
        """
        Get X and Y (Measure). Calls self.measure_params to specifically get X_Y. Adapted from EKPY.

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830

        returns:
            (list): X, Y
        """
        return self.measure_params([1,2])
        

    def get_R_theta(self):
        """Get R and Theta. (Measure). Calls self.measure_params to specifically get R_Theta. Adapted from EKPY

        args:
            self (pyvisa.resources.gpib.GPIBInstrument): SRS830

        returns:
            (list): R, Theta

        """
        return self.measure_params([3,4])



class DMM(SCPI_Instrument):
    """
    Sub-class of Instrument to hold the general methods used by a DMM.
    This implementation is based on Keithley 2400 commands. [cite: 1]
    """
    # Potential class attributes for parameter checking (optional, add ranges/lists as needed)
    nplc_range = (0.01, 10)
    voltage_range_config = (-210.0, 210.0) # For range setting in config
    current_range_config = None # Add appropriate range if needed
    resistance_range_config = None # Add appropriate range if needed
    voltage_compliance_range = None # Add appropriate range if needed
    current_compliance_range = None # Add appropriate range if needed
    current_amplitude_range = None # Add appropriate range if needed
    voltage_amplitude_range = None # Add appropriate range if needed


    def set_resistance_mode_manual(self):
        """Sets the mode to manual resistance OHMs.
        """
        self.instrument.write(":SENS:RES:MODe MAN")

    def set_source_current_amplitude(self, amplitude: float = 0.0001):
        """Sets the current source amplitude.

        Args:
            amplitude (float): Current amplitude in Amps (default: 0.0001 A).
        """
        # Optional parameter check (uncomment and define range above if needed)
        # self._check_params(locals())
        self.instrument.write(':SOUR:CURR:LEV:IMM:AMPL {}'.format(amplitude))

    def set_current_compliance(self, compliance: float = .01):
        """Sets the current compliance limit when sourcing voltage.

        Args:
            compliance (float): Current compliance in Amps (default: 0.01 A).
        """
        # Optional parameter check (uncomment and define range above if needed)
        # self._check_params(locals())
        self.instrument.write(':SENS:CURR:DC:PROT:LEV {}'.format(compliance))

    def set_voltage_compliance(self, compliance: float = 2.1):
        """Sets the voltage compliance limit when sourcing current.

        Args:
            compliance (float): Voltage compliance in Volts (default: 2.1 V).
        """
        # Optional parameter check (uncomment and define range above if needed)
        # self._check_params(locals())
        self.instrument.write(':SENS:VOLT:DC:PROT:LEV {}'.format(compliance))

    def config_measure_voltage(self, nplc: float = 1, voltage: float = 21.0, auto_range: bool = True):
        """ Configures the measurement of voltage.

        Args:
            nplc (float or int): Number of power line cycles (NPLC) from 0.01 to 10 (default: 1).
            voltage (float): Upper limit of voltage in Volts, used if auto_range is False (default: 21.0 V).
            auto_range (bool): Enables auto_range if True (default), else uses the set voltage range.
        """
        # Optional parameter check (uncomment and define ranges above if needed)
        # self._check_params(locals())
        self.instrument.write(":SENS:FUNC 'VOLT';"
                              ":SENS:VOLT:NPLC %f;:FORM:ELEM VOLT;" % nplc)
        if auto_range:
            self.instrument.write(":SENS:VOLT:RANG:AUTO 1;")
        else:
            self.instrument.write(":SENS:VOLT:RANG %g" % voltage)

    def config_measure_current(self, nplc: float = 1, current: float = .01, auto_range: bool = True):
        """ Configures the measurement of current.

        Args:
            nplc (float or int): Number of power line cycles (NPLC) from 0.01 to 10 (default: 1).
            current (float): Upper limit of current in Amps, used if auto_range is False (default: 0.01 A).
            auto_range (bool): Enables auto_range if True (default), else uses the set current range.
        """
        # Optional parameter check (uncomment and define ranges above if needed)
        # self._check_params(locals())
        self.instrument.write(":SENS:FUNC 'CURR';"
                              ":SENS:CURR:NPLC %f;:FORM:ELEM CURR;" % nplc)
        if auto_range:
            self.instrument.write(":SENS:CURR:RANG:AUTO 1;")
        else:
            self.instrument.write(":SENS:CURR:RANG %g" % current)

    def config_measure_resistance(self, nplc: float = 1, resistance_range: float = 21e6, auto_range: bool = True):
        """ Configures the measurement of resistance.

        Args:
            nplc (float or int): Number of power line cycles (NPLC) from 0.01 to 10 (default: 1).
            resistance_range (float): Upper limit of resistance in Ohms, used if auto_range is False (default: 21 MOhm).
                                      Note: K2400 uses specific range values, this sets the closest range >= the value.
            auto_range (bool): Enables auto_range if True (default), else uses the set resistance range.
        """
        # Optional parameter check (uncomment and define ranges above if needed)
        # self._check_params(locals())
        self.instrument.write(":SENS:FUNC 'RES';"
                              ":SENS:RES:NPLC %f;:FORM:ELEM RES;" % nplc)
        if auto_range:
            self.instrument.write(":SENS:RES:RANG:AUTO 1;")
        else:
            # K2400 resistance range is set by value, not index.
            # Using %g format for floating point representation.
            self.instrument.write(":SENS:RES:RANG %g" % resistance_range)

    def enable_source(self):
        """Turns on the output source (voltage or current).
        """
        self.instrument.write('OUTPUT ON')

    def disable_source(self):
        """Turns off the output source (voltage or current).
        """
        self.instrument.write('OUTPUT OFF')

    def read(self) -> str:
        """Initiates a measurement based on current config and reads the value.

        Returns:
            str: The measurement result as a string.
        """
        # The :READ? command implicitly triggers an acquisition based on setup.
        return self.instrument.query(":READ?").strip() # Use strip() like in operation_complete_query

    def config_voltage_pulse(self, nplc: float = .01, amplitude: float = 5):
        """Configures the instrument for a single voltage pulse using a 2-point sweep.
           Note: Call enable_source() and read() afterwards to execute the pulse.

        Args:
            nplc (float): Power line cycles for integration (controls pulse width, default 0.01).
            amplitude (float): Voltage amplitude of the pulse in Volts (default: 5 V).
        """
        # Optional parameter check (uncomment and define ranges above if needed)
        # self._check_params(locals())
        # Using f-string for multi-line command clarity
        command = f"""*RST
        :SENS:FUNC:CONC OFF
        :SOUR:FUNC VOLT
        :SOUR:VOLT:MODE SWE
        :SOURce:SWEep:POINts 2
        :SOURce:VOLTage:STARt {amplitude}
        :SOURce:VOLTage:STOP 0
        :SENS:VOLT:NPLCycles {nplc}
        :TRIG:COUN 2
        :TRIG:DELay 0
        :SOUR:DEL 0
        """
        # Send commands one by one or as a block if VISA driver supports it well
        # Sending line by line might be safer for some setups
        for line in command.strip().split('\n'):
             self.instrument.write(line.strip())

    # Example of replacing the original configure method or adding a specific one
    def configure_dc_voltage_measure(self, nplc: float = 1, auto_range: bool = True):
         """Simplified config for basic DC Voltage measurement."""
         self.config_measure_voltage(nplc=nplc, auto_range=auto_range)


# Make sure the rest of your SCPI_Instrument class and helpers are defined above this.
# You would replace the existing DMM class definition [cite: 173] in temp34.txt with this updated version.


"""
Helper Functions Below
"""
"""
NOTE I WILL NOT BE USING THIS SINCE DRIVERS SHOULDNT WORRY ABOUT EASE OF USE, CAN IMPLEMENT AT HIGHER LVL
"""
# Mapping for SI time units
# us = microsecond, ms = millisecond, s = second, ks = kilosecond
TIME_MULTIPLIERS = {
    'us': 1e-6,
    'ms': 1e-3,
    's': 1,
    'ks': 1e3,
}

def convert_time_str(time_str):
    """
    Converts a time constant string (e.g. "10us", "1ms", "30ks")
    into its value in seconds.
    """
    # Find where the digits end and letters begin.
    # This works if the time_str is in a valid format (e.g. "10us", "1ms")
    num_part = ''
    unit_part = ''
    for ch in time_str:
        if ch.isdigit() or ch == '.':
            num_part += ch
        else:
            unit_part += ch
    
    if not num_part or unit_part not in TIME_MULTIPLIERS:
        raise ValueError(f"Invalid time string format: {time_str}")
    
    return float(num_part) * TIME_MULTIPLIERS[unit_part]

def find_nearest_time(input_time, time_constants_list):
    """
    Given an input time in seconds, this function finds and returns the time constant
    from the list that is numerically closest to the input time.
    
    Parameters:
        input_time (float): Time in seconds.
        time_constants_list (list): List of time constant strings.
    
    Returns:
        The time constant string closest to the input time.
    """
    # Convert all constants to their numeric values (in seconds)
    numeric_constants = [(tc, convert_time_str(tc)) for tc in time_constants_list]
    
    # Find the time constant with the smallest absolute difference from the input_time
    nearest = min(numeric_constants, key=lambda item: abs(item[1] - input_time))
    return nearest[0]



def convert_to_lowercase(params):
    """
    Helper function to ensure that all params are lowercase
    inside the func call, but doesn't modify None type values.
    >>> locals().update(convert_to_lowercase(locals()))
    """
    return {key: value.lower() if isinstance(value, str) else value for key, value in params.items()}




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



def is_contained(value, lst):
    """
    Helper Function that checks if a string is contained within a list and ignores case sensitivity
    """
    my_string = value.lower()
    my_list = [item.lower() for item in lst]
    return my_string in my_list


def is_value_between(value, num_tuple):
    """
    Helper function that checks if the value is between allowed ranges, taken with help from ChatGPT
    """
    if value is None:
        return True
    if type(value) is str:
        value = float(value)
    if len(num_tuple) != 2:
        raise ValueError("Tuple must contain exactly two numbers")
    return num_tuple[0] <= value <= num_tuple[1]


def get_matching_keys(dict1, dict2):
    """ 
    Find the intersection of keys from both dictionaries, taken from ChatGPT
    """
    matching_keys = set(dict1.keys()).intersection(dict2.keys())
    return list(matching_keys)

def get_class_attributes_from_instance(instance):
    """
    Helper Function to get the class attributes from an instance.
    It retrieves class attributes starting from the base classes and
    then overrides them with attributes from child classes.
    """
    cls = instance.__class__
    attributes = {}
    # Iterate in reverse MRO so that child class attributes override base class ones.
    for base in reversed(cls.__mro__):
        attributes.update({attr: getattr(base, attr) 
                           for attr in base.__dict__ 
                           if not callable(getattr(base, attr)) and not attr.startswith("__")})
    return attributes


def find_first_number(input_string):
    # Define a regular expression pattern to match one or more digits
    pattern = r'\d+'
    
    # Search for the pattern in the input string
    match = re.search(pattern, input_string)
    
    # If a match is found, return the matched number
    if match:
        return match.group()
    else:
        return None

def check_error_string(error_string):
    """
    Helper Function that checks if the error str matches either a 0 or No error
    returns true if no error
    """
    # Convert the string to lowercase for case-insensitive comparison
    lower_string = error_string.lower()
    error_code = find_first_number(lower_string)
    # Check if the string contains '0' or 'no error' after a comma
    if error_code == "0" or "no error" in lower_string:
        return True
    else:
        return False

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

def recursive_lower(obj):
    """
    Recursively lowercases strings within common data structures.
    Non-string objects or numbers are returned as is.
    """
    if isinstance(obj, str):
        return obj.lower()
    elif isinstance(obj, list):
        return [recursive_lower(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(recursive_lower(item) for item in obj)
    elif isinstance(obj, dict):
        return { (k.lower() if isinstance(k, str) else k): recursive_lower(v)
                 for k, v in obj.items() }
    else:
        return obj


'''
Helper functions for awg class:
'''
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


"""
Error handling: maybe make a seperate python file to take care of error handling 

Also good idea to add option to suppress warnings, aka no print statements instead call warning function that has param that can be suppressed
"""

def exit_with_error(msg):
    """
    Function to raise error message that provides faster feedback
    """
    raise ValueError(msg)
