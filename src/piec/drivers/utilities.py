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