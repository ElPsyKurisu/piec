"""
Set's up the digilent instrument class that uses wrappers to the mcculw library
Realistically this should be setup like the SCPI classes and then you have subclasses for the DAQ model.
However it seems that mcculw does a good job of autodetecting abiltiies so may just be worth it to have a single one that just uses the paramters 
from the original probe to the instrument in the __init__ file


"""
from piec.analysis.utilities import interpolate_sparse_to_dense

try:
    from mcculw import ul
    from mcculw.enums import InterfaceType, BoardInfo, ScanOptions, InfoType, FunctionType
    from mcculw.device_info import DaqDeviceInfo
    from ctypes import cast, POINTER, c_double
except FileNotFoundError:
    raise FileNotFoundError('Please check the readme file and install the required dependencies (UL) or try running pip install mcculw')
from typing import Union
import numpy as np



from instrument import Instrument

class MCC_DAQ(Instrument):
    """
    Custom Class for using an MCC DAQ NOTE: Currently relies on only one MCC DAQ being plugged in at a time. If not I need to
    manually set up ones, or use the list of the ones it finds and select accordingly
    """

    def __init__(self, address=None):
        """
        NOTE In this case address is the dev_id which can be found via config device?
        ao_info holds all information related to the analog output
        ai_info holds all information related to the analog input
        """
        if address is None:
            dev_id_list = []
        else:
            dev_id_list = [address]
        self.ao_info, self.ai_info, self.board_num = config_device(dev_id_list=dev_id_list)
        self.max_sampling_rate_in = ul.get_config(InfoType.BOARDINFO, self.board_num, 0, BoardInfo.ADMAXRATE)
        self.max_sampling_rate_out = 5000
        #used to store data maybe make a new class for this
        self.data = None
        self.memhandle = None
        self.data_len = None

    def idn(self):
        """
        Queries the instrument for its ID

        """
        return ul.get_board_name(self.board_num) #all boards will be initiatied via 0, need to check that two can exist simulatensly

    def v_in(self, channel):
        '''
        Wrapper for UL.v_in.
        '''
        ul_range = self.ai_info.supported_ranges[0]
        value = ul.v_in(self.board_num, channel, ul_range)
        return value

    def v_out(self, channel, data_value):
        '''
        Wrapper for UL.v_out
        '''
        ul_range = self.ao_info.supported_ranges[0]
        ul.v_out(self.board_num, channel, ul_range, data_value)

    def release_device(self):
        '''
        Wrapper for ul.release_daq_device
        '''
        ul.release_daq_device(self.board_num)

    """
    BELOW ARE FAKE AWG COMMANDS, UNSURE HOW TO STRUCTURE
    """
    def create_arb_wf(self, data: Union[np.array, list], name=None, channel='0'):
        """
        Fake method to use MCC_DAQ as an awg Basically saves the data in python memory
        then is passed through to the configure_wf
        Basically just holds the data to pass into the next function where the math is
        NOTE: Ensures data is scaled to a max value of 1
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): MCC DAQ
            data (ndarray or list): Data to be converted to wf
            name (str): Name of waveform, must start with A-Z
            channel (str): What channel to put the volatile WF on
        """
        #need to make sure its scaled between -1 and 1 unless greater than zero
        self.data_len = len(data)
        abs_max_val = np.max(np.abs(data))
        scaled_data = data/abs_max_val
        self.data = scaled_data
    
    def configure_wf(self, channel: str='1', func: str='SIN', voltage: str='1.0', offset: str='0.00', frequency: str='1e3', duty_cycle='50',
                      num_cycles=None, invert: bool=False):
        """
        This function configures the named func with the given parameters. Works on both user defined and built-in functions
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): MCC DAQ
            channel (str): Desired Channel to configure
            func (str): The function name ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
            voltage (str): The V_pp of the waveform in volts
            offset (str): The voltage offset in units of volts
            frequency (str): the frequency in units of Hz for the arbitrary waveform
            duty_cycle (str): duty_cycle defined as 100* pulse_width / Period ranges from 0-100, (cant actually do 0 or 100 but in between is fine)
            num_cycles (str): number of cycles by default set to None which means continous NOTE only works under BURST mode, not implememnted
            invert (bool): Inverts the waveform by flipping the polarity
        """
        built_in_list = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC']
        if func in built_in_list:
            self._configure_built_in_wf(channel, func, frequency, voltage, offset, duty_cycle)
        else:
            self._configure_arb_wf(channel, func, voltage, offset, frequency, invert)
        if self.data is None:
            num_points = 5000
            pass
            #raise ValueError("No valid waveform defined need to change so built in work (fake built in)")
        '''
        """
        scan_options = (ScanOptions.BACKGROUND |
                        ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)
        ao_range = self.ao_info.supported_ranges[0]
        max_sampling_rate = ul.get_config(InfoType.BOARDINFO, self.board_num, 0, BoardInfo.ADMAXRATE) #returns int of max sample rate
        #NOTE there is no function to get  max output analog rate. currently 5k is the max
        max_sampling_rate = 5000
        """
        freq = float(frequency)
        amplitude = float(voltage)/2

        
        #memhandle = ul.scaled_win_buf_alloc(num_points)
        #data_array = cast(memhandle, POINTER(c_double))
        if func == "SIN":
            """
            Creates a memhandle that holds the sine wave as we want it in ctypes
            """
            self.memhandle = ul.scaled_win_buf_alloc(self.max_sampling_rate_out)
            num_points = self.max_sampling_rate_out
            data_array = cast(self.memhandle, POINTER(c_double))
            y_offset = 0
            for i in range(num_points):
                value = amplitude*np.sin(2*np.pi*freq*i/self.max_sampling_rate_out) + y_offset
                data_array[i] = value
        #actual output
        #low chan and high chan should be the same and is just the channel number so it only outputs on 1 channel
        """
        ul.a_out_scan(self.board_num, int(channel), int(channel),
                          num_points, max_sampling_rate, ao_range, memhandle,
                          scan_options) #technically this should not be called here, should be called on enable_output
        """
        '''
    def _configure_built_in_wf(self, channel: str='1', func='SIN', frequency='1e3', voltage='1', offset='0', duty_cycle='50', invert: bool=False):
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
        self.data_len = self.max_sampling_rate_out #sets to max so it works
        num_points = self.data_len
        self.memhandle = ul.scaled_win_buf_alloc(num_points)
        data_array = cast(self.memhandle, POINTER(c_double))
        amplitude = float(voltage)/2 #converts to V_pp unsure how it works for assymetrical stuff
        freq = float(frequency)
        y_offset = float(offset)
        if func == "SIN":
            for i in range(num_points):
                value = amplitude*np.sin(2*np.pi*freq*i/num_points) + y_offset
                data_array[i] = value
        if func == "RAMP":
            freq = int(freq)
            y_arr = [0,1,0,-1]*freq +[0] #doulbes it 
            x_arr = np.linspace(0, len(y_arr), len(y_arr))
            #frequnecy is 1 hz if we use max_sampling rate_out
            new_data = interpolate_sparse_to_dense(x_arr, y_arr, self.max_sampling_rate_out)
            for i in range(num_points):
                value = amplitude*new_data[i] + y_offset
                data_array[i] = value
        """
        self.instrument.write(":SOUR:FUNC{} {}".format(channel, func)) 
        self.instrument.write(":SOUR:FREQ{} {}".format(channel, frequency))
        self.instrument.write(":VOLT{}:OFFS {}".format(channel, offset))
        self.instrument.write(":VOLT{} {}".format(channel, voltage))
        if func.lower() == 'squ' or func.lower() == 'square':
            self.instrument.write(":SOUR:FUNC{}:SQU:DCYC {}".format(channel, duty_cycle)) 
        if func.lower() == 'pulse' or func.lower() == 'puls':
            self.instrument.write(":SOUR:FUNC{}:PULS:DCYC {}".format(channel, duty_cycle))
        if invert:
            self.instrument.write(":OUTP{}:POL INV".format(channel))
        else:
            self.instrument.write(":OUTP{}:POL NORM".format(channel))
        """

    def _configure_arb_wf(self, channel: str='1', name='VOLATILE', voltage: str='1.0', offset: str='0.00', frequency: str='1000', invert: bool=False):
        """
        This program configures arbitrary waveform already saved on the instrument. Adapted from EKPY.
        Name is useless for the digilent series. But could implement that the name is saved in memory so that you can store multiple etc
        then can delete shit via the ul.freewinbuffer, but thats for later 
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): Keysight 81150A
            channel (str): Desired Channel to configure accepted params are [1,2]
            name (str): The Arbitrary Waveform name as saved on the instrument, by default VOLATILE
            voltage (str): The V_pp of the waveform in volts
            offset (str): The voltage offset in units of volts
            frequency (str): the frequency in units of Hz for the arbitrary waveform
            invert (bool): Inverts the waveform by flipping the polarity
        """
        amplitude = float(voltage) / 2
        y_offset = float(offset)
        freq = float(frequency) #this is basically supposed to equal the rate 5000/num_points
        if invert:
            self.data = -1*self.data
        num_points = self.data_len
        self.memhandle = ul.scaled_win_buf_alloc(num_points)
        num_points = self.data_len
        data_array = cast(self.memhandle, POINTER(c_double))
        y_offset = 0
        for i in range(num_points):
            value = amplitude*self.data[i] + y_offset
            data_array[i] = value


        """
        dict_to_check = locals()
        dict_to_check['func'] = 'USER' #this is useless i want to make sure frequency is good tho for arb waveform
        self._check_params(dict_to_check)
        if self.slew_rate is not None:
            points = self.instrument.query(":DATA:ATTR:POIN? {}".format(name)).strip()
            if (float(voltage))/(float(frequency)/float(points)) > self.slew_rate:
                    print('WARNING: DEFINED WAVEFORM IS FASTER THAN AWG SLEW RATE')
        self.instrument.write(":FUNC{}:USER {}".format(channel, name)) #makes current USER selected name, but does not switch instrument to it
        self.instrument.write(":FUNC{} USER".format(channel)) #switches instrument to user waveform
        self.instrument.write(":VOLT{} {}".format(channel, voltage))
        self.instrument.write(":FREQ{} {}".format(channel, frequency))
        self.instrument.write(":VOLT{}:OFFS {}".format(channel, offset))
        if invert:
            self.instrument.write(":OUTP{}:POL INV".format(channel))
        else:
            self.instrument.write(":OUTP{}:POL NORM".format(channel))
        """

    def output_enable(self, channel: str='0', on=True):
        """
        This program toggles the selected output. 
        CURRENTLY ONLY USED IF YOU SET UP A WAVEFORM

        NOTE: For this to work properly we need to change hella.
        add a self.data as the memhandle how it works in testing atm
        args:
            self (pyvisa.resources.gpib.GPIBInstrument): MCC DAQ
            channel (str): Desired Channel to configure accepted params are [0,1, etc]
            on (boolean): True for on, False for off
        """
        scan_options = (ScanOptions.BACKGROUND |
                        ScanOptions.CONTINUOUS | ScanOptions.SCALEDATA)
        if on:
            ul.a_out_scan(self.board_num, int(channel), int(channel),
                          num_points=self.data_len, rate=self.max_sampling_rate_out, 
                          ul_range=self.ao_info.supported_ranges[0], memhandle=self.memhandle,
                          options=scan_options)
        else:
            ul.stop_background(0, FunctionType.AOFUNCTION)



"""
Custom Helper Functions
"""

def is_device_connected(board_num):
    try:
        # Try to get the board name to check if the device is connected
        board_name = ul.get_board_name(board_num)
        print(f"Device connected at board number {board_num}: {board_name}")
        return True
    except Exception as e:
        print(f"No device connected at board number {board_num}")
        return False

def config_device(use_device_detection=True, dev_id_list=[]):
    '''
    Configures the device and returns the accepted params from the device
    args:
        use_device_detection (bool): True or False
        dev_id_list (list) List of ints that refer to the device ID's
    returns:
        ai_info (obj) Information about analog inputs
        ao_info (obj) Information about analog outputs


    '''   
    # By default, the example detects and displays all available devices and
    # selects the first device listed. Use the dev_id_list variable to filter
    # detected devices by device ID (see UL documentation for device IDs).
    # If use_device_detection is set to False, the board_num variable needs to
    # match the desired board number configured with Instacal.
    max_devices = 5
    board_num = 0
    while board_num < max_devices:
        if not is_device_connected(board_num):
            break
        board_num += 1
        if board_num >= max_devices:
            raise Exception("WARNING OVER THE HARDCODED LIMIT OF MAX DEVICES OR SOME UNRECOVERABLE ERROR OCCURRED")


    try:

        if use_device_detection:

            config_first_detected_device(board_num, dev_id_list)

        daq_dev_info = DaqDeviceInfo(board_num)
        if not daq_dev_info.supports_analog_output:
            raise Exception('Error: The DAQ device does not support '
                            'analog output')

        print('\nActive DAQ device: ', daq_dev_info.product_name, ' (',
              daq_dev_info.unique_id, ')\n', sep='')

        ao_info = daq_dev_info.get_ao_info()
        ai_info = daq_dev_info.get_ai_info()
        #max_sampling_rate = daq_dev_info.g
        #ao_range = ao_info.supported_ranges[0] Leave to explain how to get range
        low_chan = 0
        high_chan = min(3, ao_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1
    except Exception as e:
        print('\n', e)
    return ai_info, ao_info, board_num

def make_sin_wave(freq):
    max_sampling_rate = 5000 #returns int of max sample rate
    num_points = 1000
    memhandle = ul.scaled_win_buf_alloc(num_points)
    data_array = cast(memhandle, POINTER(c_double))
    meow = []
    y_offset = 0
    amplitude = 5
    for i in range(num_points):
        value = amplitude*np.sin(2*np.pi*freq*i/max_sampling_rate) + y_offset
        data_array[i] = value
        meow.append(value)


'''
Helper Functions taken directly from mcculw examples library
'''

def config_first_detected_device(board_num, dev_id_list=None):
    """Adds the first available device to the UL.  If a types_list is specified,
    the first available device in the types list will be add to the UL.
    NOTE: Edited to allow for multiple devices to be connected

    Parameters
    ----------
    board_num : int
        The board number to assign to the board when configuring the device.

    dev_id_list : list[int], optional
        A list of product IDs used to filter the results. Default is None.
        See UL documentation for device IDs.
    """
    if board_num == 0:
        ul.ignore_instacal() #aka on first run we ignore instacal, then subsequnetly we dont want to override the config file
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        raise Exception('Error: No DAQ devices found')

    print('Found', len(devices), 'DAQ device(s):')
    for device in devices:
        print('  ', device.product_name, ' (', device.unique_id, ') - ',
              'Device ID = ', device.product_id, sep='')

    device = devices[0]
    if dev_id_list:
        device = next((device for device in devices
                       if device.product_id in dev_id_list), None)
        if not device:
            err_str = 'Error: No DAQ device found in device ID list: '
            err_str += ','.join(str(dev_id) for dev_id in dev_id_list)
            raise Exception(err_str)

    # Add the first DAQ device to the UL with the specified board number
    ul.create_daq_device(board_num, device)


def add_example_data(board_num, data_array, ao_range, num_chans, rate,
                     points_per_channel):
    # Calculate frequencies that will work well with the size of the array
    frequencies = []
    for channel_num in range(num_chans):
        frequencies.append(
            (channel_num + 1) / (points_per_channel / rate) * 10)

    # Calculate an amplitude and y-offset for the signal
    # to fill the analog output range
    amplitude = (ao_range.range_max - ao_range.range_min) / 2
    y_offset = (amplitude + ao_range.range_min) / 2

    # Fill the array with sine wave data at the calculated frequencies.
    # Note that since we are using the SCALEDATA option, the values
    # added to data_array are the actual voltage values that the device
    # will output
    data_index = 0
    for point_num in range(points_per_channel):
        for channel_num in range(num_chans):
            freq = frequencies[channel_num]
            value = amplitude * np.sin(2 * np.pi * freq * point_num / rate) + y_offset
            raw_value = ul.from_eng_units(board_num, ao_range, value)
            data_array[data_index] = raw_value
            data_index += 1

    return frequencies

def add_data(data, board_num, data_array, ao_range, num_chans, rate, points_per_channel):
    """
    My version of add_example_data
    """
    #data should be a np array or a list that is the arb waveform
    # Calculate frequencies that will work well with the size of the array
    frequencies = []
    for channel_num in range(num_chans):
        frequencies.append(
            (channel_num + 1) / (points_per_channel / rate) * 10)

    # Calculate an amplitude and y-offset for the signal
    # to fill the analog output range
    amplitude = (ao_range.range_max - ao_range.range_min) / 2
    y_offset = (amplitude + ao_range.range_min) / 2

    # Fill the array with sine wave data at the calculated frequencies.
    # Note that since we are using the SCALEDATA option, the values
    # added to data_array are the actual voltage values that the device
    # will output
    data_index = 0
    for point_num in range(points_per_channel):
        for channel_num in range(num_chans):
            freq = frequencies[channel_num]
            value = amplitude * np.sin(2 * np.pi * freq * point_num / rate) + y_offset
            raw_value = ul.from_eng_units(board_num, ao_range, value)
            data_array[data_index] = raw_value
            data_index += 1

    return frequencies
