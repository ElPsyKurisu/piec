
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

# Note the '.' before 'instrument'. This is a relative import.
from .instrument import Instrument

def build_driver_registry():
    """
    Dynamically discovers all driver classes within the 'drivers' package
    and builds a registry mapping their ID_STRING to the class itself.
    """
    driver_registry = {}
    # __file__ is the path to this file (utilities.py)
    # .parent gives us the path to the 'drivers' directory
    drivers_path = Path(__file__).parent

    # 1. Walk through all .py files in the drivers subdirectories
    for file_path in drivers_path.glob('**/*.py'):
        # Skip special files
        if file_path.name in ('__init__.py', 'instrument.py', 'utilities.py'):
            continue

        # 2. Convert file path to a module path for importing
        # e.g., .../drivers/oscilloscope/tek.py -> drivers.oscilloscope.tek
        relative_path = file_path.relative_to(drivers_path)
        module_name = '.'.join(relative_path.parts).replace('.py', '')
        module_path = f"drivers.{module_name}"

        try:
            # 3. Dynamically import the module
            module = importlib.import_module(module_path)

            # 4. Inspect the module for valid driver classes
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Instrument) and obj is not Instrument and obj.ID_STRING:
                    print(f"Found driver: '{obj.ID_STRING}' -> {obj.__name__}")
                    driver_registry[obj.ID_STRING] = obj

        except ImportError as e:
            print(f"Could not import module {module_path}: {e}")

    return driver_registry

# --- The autodetect function now lives here ---

# Build the registry once when this module is first imported.
DRIVER_REGISTRY = build_driver_registry()

def _probe_scpi(address):
    """Probes for a SCPI device and returns its ID string and VISA resource."""
    try:
        rm = pyvisa.ResourceManager()
        instrument = rm.open_resource(address)
        instrument.timeout = 2000 # 2-second timeout
        identity = instrument.query('*IDN?').strip()
        return identity, instrument
    except pyvisa.errors.VisaIOError:
        return None, None

def autodetect_instrument(address):
    """
    Automatically detects and initializes an instrument at the given address.
    """
    print(f"\n🔎 Attempting to autodetect instrument at {address}...")

    # For now, we only have a SCPI probe. You could add more probes here.
    instrument_id, visa_resource = _probe_scpi(address)

    if instrument_id and visa_resource:
        print(f"  - Received ID: '{instrument_id}'")
        
        # Look for a matching driver in our dynamically built registry
        for id_key, driver_class in DRIVER_REGISTRY.items():
            if instrument_id.startswith(id_key):
                print(f"✅ Match found! Initializing driver: {driver_class.__name__}")
                # Check if the driver is an SCPI instrument to pass the VISA resource
                if issubclass(driver_class, SCPIInstrument):
                    return driver_class(address, visa_resource)
                else:
                    visa_resource.close() # Close if not used
                    return driver_class(address)
    
    print(f"❌ No matching driver found for instrument at {address}.")
    if visa_resource:
        visa_resource.close()
    return None