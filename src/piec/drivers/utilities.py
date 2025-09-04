
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


"""
This code is the the autodetect driver portion
"""
# drivers/utilities.py

import inspect
import importlib
from pathlib import Path
import pyvisa

# --- 1. Static Registry (Fast Path) ---
# Add your most frequently used drivers here manually.
# The system will automatically add to this dictionary when it discovers new drivers.
#
# from .awg import k_81150a # Example of a manual import
# from .oscilloscope import k_dsox3024a
#
STATIC_DRIVER_REGISTRY = {
    # "81150A": k_81150a.Keysight81150a, # Manually add for top speed
    # "DSO-X 3024A": k_dsox3024a.KeysightDSOX3024A
}

_dynamic_scan_complete = False # A flag to ensure we only scan once

def _dynamic_driver_scan():
    """
    Dynamically discovers all driver classes and updates the static registry.
    This is the "slow path" and should only run when needed.
    """
    global _dynamic_scan_complete
    if _dynamic_scan_complete:
        return

    print("--- Running dynamic driver scan... ---")
    drivers_path = Path(__file__).parent
    
    new_drivers_found = 0
    for file_path in drivers_path.glob('**/*.py'):
        if file_path.name in ('__init__.py', 'instrument.py', 'utilities.py', 'scpi.py'):
            continue

        module_path = '.'.join(file_path.relative_to(drivers_path.parent).parts).replace('.py', '')

        try:
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                identifier = getattr(obj, 'idn', getattr(obj, 'model', None))
                if isinstance(identifier, str) and identifier and identifier not in STATIC_DRIVER_REGISTRY:
                    print(f"  -> Discovered new driver: '{identifier}' -> {obj.__name__}")
                    STATIC_DRIVER_REGISTRY[identifier] = obj # Add to the registry
                    new_drivers_found += 1
        except Exception:
            pass
            
    if new_drivers_found == 0:
        print("--- Dynamic scan complete. No new drivers found. ---")
    else:
        print(f"--- Dynamic scan complete. Added {new_drivers_found} new drivers to registry. ---")

    _dynamic_scan_complete = True


def _probe_scpi(address):
    """Connects via VISA and queries the ID string."""
    try:
        rm = pyvisa.ResourceManager()
        instrument = rm.open_resource(address)
        instrument.timeout = 2000
        identity = instrument.query('*IDN?').strip()
        instrument.close()
        return identity
    except pyvisa.errors.VisaIOError:
        return None

def _find_match_in_registry(instrument_id):
    """Helper function to find a matching driver in the current registry."""
    for id_key, driver_class in STATIC_DRIVER_REGISTRY.items():
        if id_key in instrument_id:
            return driver_class
    return None

def autodetect_instrument(address):
    """
    Detects an instrument using a two-tiered registry system.
    First checks a fast static list, then falls back to a full dynamic scan if needed.
    """
    print(f"\n🔎 Probing instrument at {address}...")
    instrument_id = _probe_scpi(address)

    if not instrument_id:
        print(f"❌ Could not get an ID from the instrument at {address}.")
        return None
        
    print(f"  - VISA ID: '{instrument_id}'")

    # 1. First, check the fast static registry
    driver_class = _find_match_in_registry(instrument_id)

    # 2. If not found, run the dynamic discovery and check again
    if not driver_class:
        print("  - Driver not found in static registry. Starting dynamic scan...")
        _dynamic_driver_scan()
        driver_class = _find_match_in_registry(instrument_id)

    # 3. If a match is found, instantiate and return the driver
    if driver_class:
        id_key = next(key for key, val in STATIC_DRIVER_REGISTRY.items() if val == driver_class)
        print(f"✅ Match found for '{id_key}'! Initializing driver: {driver_class.__name__}")
        try:
            return driver_class(address=address)
        except Exception as e:
            print(f"  - Error initializing {driver_class.__name__}: {e}")
            return None

    print(f"❌ No matching driver found for the instrument at {address} after full scan.")
    return None