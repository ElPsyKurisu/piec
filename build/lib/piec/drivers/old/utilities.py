"""
This is a temp thing to override ResourceManager
"""

try:
    from pyvisa import ResourceManager
    from mcculw import ul
    from mcculw.enums import InterfaceType
except FileNotFoundError:
    print('Warning, if using digilent please check the readme file and install the required dependencies (UL) or try running pip install mcculw')

class PiecManager():
    """
    Basically Resource Manager that melds MCC digilent stuff into it
    Alllows to get all resources
    """
    def __init__(self):
        self.rm = ResourceManager()

    def list_resources(self):
        """
        Runs list_resources() and then tries to idn each resource
        want what drivers can be used for it as well
        """
        visa = self.rm.list_resources()
        try:
            mcc = list_mcc_resources()
        except:
            print('Warning MCCULW not installed')
            mcc = []
        return tuple(list(visa) + mcc)

    def list_open_resources(self):
        visa = self.rm.list_opened_resources()
        return tuple(list(visa))
        

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

        
        