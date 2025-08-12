"""
This is a temp thing to override ResourceManager
"""

try:
    from pyvisa import ResourceManager
    from mcculw import ul
    from mcculw.enums import InterfaceType
except (FileNotFoundError, ImportError):
    print('Warning, if using digilent please check the readme file and install the required dependencies (UL) or try running pip install mcculw')

class PiecManager():
    """
    Basically Resource Manager that melds MCC digilent stuff into it.
    Allows for getting all resources from both VISA and MCC.
    """
    def __init__(self):
        """Initializes the underlying pyvisa ResourceManager."""
        self.rm = ResourceManager()

    def list_resources(self):
        """
        Runs list_resources() for both VISA and MCC and combines them.
        """
        visa_resources = self.rm.list_resources()
        mcc_resources = []
        try:
            mcc_resources = list_mcc_resources()
        except Exception as e:
            print(f'Warning: Could not list MCCULW resources. Error: {e}')
        
        return tuple(list(visa_resources) + mcc_resources)

    def list_open_resources(self):
        """Lists only the currently opened VISA resources."""
        return self.rm.list_opened_resources()

    def open_resource(self, address, baud_rate=None, **kwargs):
        """
        Opens a resource by address.

        If the address is for an MCCULW device, it uses the ul module.
        For standard VISA resources, it acts as a wrapper for pyvisa's open_resource,
        allowing for an explicit baud_rate argument.

        Args:
            address (str): The resource address string.
            baud_rate (int, optional): The baud rate for serial instruments. Defaults to None.
            **kwargs: Other keyword arguments to pass to pyvisa.open_resource.
        """
        # Check if the device is an MCC/Digilent device
        if 'MCC' in address or 'Digilent' in address:
            # These devices are not opened via VISA, so kwargs are not used.
            return ul.open_device(address)
        else:
            # This is a standard VISA resource.
            # If the user provided a baud_rate, add it to the kwargs dictionary.
            # This gives the explicit argument priority.
            if baud_rate is not None:
                kwargs['baud_rate'] = baud_rate
            
            # Call the original pyvisa function with the (potentially modified) kwargs.
            return self.rm.open_resource(address, **kwargs)

"""
Helper Functions
"""
def list_mcc_resources():
    """Lists all connected MCC DAQ devices."""
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    formatted_list = []
    if devices:
        for device in devices:
            # Create a descriptive string for each device
            device_string = f"{device.product_name} ({device.unique_id}) - Device ADDRESS = {device.product_id}"
            formatted_list.append(device_string)
    return formatted_list
