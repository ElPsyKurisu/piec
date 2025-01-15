"""
Set's up the digilent instrument class that uses wrappers to the mcculw library
Realistically this should be setup like the SCPI classes and then you have subclasses for the DAQ model.
However it seems that mcculw does a good job of autodetecting abiltiies so may just be worth it to have a single one that just uses the paramters 
from the original probe to the instrument in the __init__ file


"""
try:
    from mcculw import ul
    from mcculw.enums import InterfaceType
    from mcculw.device_info import DaqDeviceInfo
except FileNotFoundError:
    raise FileNotFoundError('Please check the readme file and install the required dependencies (UL) or try running pip install mcculw')
import numpy as np



from instrument import Instrument

class MCC_DAQ(Instrument):
    """
    Custom Class for using an MCC DAQ NOTE: Currently relies on only one MCC DAQ being plugged in at a time. If not I need to
    manually set up ones, or use the list of the ones it finds and select accordingly
    """

    def __init__(self, address=None):
        """
        ao_info holds all information related to the analog output
        ai_info holds all information related to the analog input
        """
        if address is None:
            dev_id_list = []
        else:
            dev_id_list = [address]
        self.ao_info, self.ai_info = config_device(dev_id_list=address) 

    def idn(self):
        """
        Queries the instrument for its ID

        """
        return self.instrument.query("*IDN?")

    def v_in(self, board_num, channel):
        '''
        Wrapper for UL.v_in.
        '''
        ul_range = self.ai_info.supported_ranges[0]
        value = ul.v_in(board_num, channel, ul_range)
        return value

    def v_out(self, board_num, channel, data_value):
        '''
        Wrapper for UL.v_out, dont change ul_range
        '''
        ul_range = self.ao_info.supported_ranges[0]
        ul.v_out(board_num, channel, ul_range, data_value)

    def release_device(board_num):
        '''
        Wrapper for ul.release_daq_device
        '''
        ul.release_daq_device(board_num)

"""
Custom Helper Functions
"""

def config_device(use_device_detection=True, dev_id_list=[],
                         board_num=0):
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
        #ao_range = ao_info.supported_ranges[0] Leave to explain how to get range
        low_chan = 0
        high_chan = min(3, ao_info.num_chans - 1)
        num_chans = high_chan - low_chan + 1
    except Exception as e:
        print('\n', e)
    return ai_info, ao_info

'''
Helper Functions taken directly from mcculw examples library
'''

def config_first_detected_device(board_num, dev_id_list=None):
    """Adds the first available device to the UL.  If a types_list is specified,
    the first available device in the types list will be add to the UL.

    Parameters
    ----------
    board_num : int
        The board number to assign to the board when configuring the device.

    dev_id_list : list[int], optional
        A list of product IDs used to filter the results. Default is None.
        See UL documentation for device IDs.
    """
    ul.ignore_instacal()
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


