"""
This is a temp thing to override ResourceManager
"""

from pyvisa import ResourceManager
try:
    from mcculw import ul
    from mcculw.enums import InterfaceType
except FileNotFoundError:
    raise FileNotFoundError('Please check the readme file and install the required dependencies (UL) or try running pip install mcculw')

class PiecManager(ResourceManager):
    """
    Basically Resource Manager that melds MCC digilent stuff into it
    """
    def list_resources(self, query = "?*::INSTR"):
        one = super().list_resources(query)
        two = list_mcc_resources()
        return tuple(list(one) + two)
        

"""
Helper Functions
"""
def list_mcc_resources():
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    formatted_list = []
    if devices:
        #print('Found', len(devices), 'MCC DAQ device(s):')
        for device in devices:
            formatted_list.append(str(device.product_name) + ' (' + str(device.unique_id) + ') - '+ 'Device ADDRESS = '+ str(device.product_id))
    return formatted_list

        
        