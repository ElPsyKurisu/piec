"""
This file contains the PiecManager, a resource manager
that can find both VISA and MCC (Digilent) devices.
"""

try:
    from pyvisa import ResourceManager
    from mcculw import ul
    from mcculw.enums import InterfaceType
except ImportError:
    print('Warning: Missing pyvisa or mcculw. Install dependencies.')
    # Define placeholders if needed for CI/testing
    class ResourceManager:
        def list_resources(self): return ()
        def list_opened_resources(self): return ()
    ul = None
    InterfaceType = None

class PiecManager():
    """
    Manages and lists all instrument resources,
    melding MCC Digilent devices with standard VISA devices.
    """
    def __init__(self):
        self.rm = ResourceManager()

    def list_resources(self):
        """
        Gets all VISA resources and all MCC resources
        and returns them as a single combined tuple.
        """
        visa = ()
        try:
            visa = self.rm.list_resources()
        except Exception as e:
            print(f"Warning: Could not list VISA resources. {e}")
            
        mcc = []
        try:
            mcc = list_mcc_resources()
        except Exception as e:
            print(f"Warning: Could not list MCC resources. {e}")
            
        return tuple(list(visa) + mcc)

    def list_open_resources(self):
        """Lists only the opened VISA resources."""
        try:
            return tuple(self.rm.list_opened_resources())
        except Exception as e:
            print(f"Warning: Could not list open resources. {e}")
            return ()
        
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
    """
    Finds all connected MCC DAQ devices.
    """
    if ul is None:
        return [] # mcculw not imported
        
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    formatted_list = []
    if devices:
        for device in devices:
            # This format is parsed by autodetect.py
            formatted_list.append(
                f'{device.product_name} ({device.unique_id}) - Device ADDRESS = {device.product_id}'
            )
    return formatted_list