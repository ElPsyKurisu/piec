
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
import inspect
import importlib
from pathlib import Path
import pyvisa
import json
import os

# Define the path for our cache file, right next to this utility script
_CACHE_FILE = Path(__file__).parent / 'registry_cache.json'

def _load_registry_from_cache():
    """Loads the driver registry from a JSON cache file if it exists."""
    if not os.path.exists(_CACHE_FILE):
        return {}
    try:
        with open(_CACHE_FILE, 'r') as f:
            registry_data = json.load(f)
        
        loaded_registry = {}
        for identifier, class_path in registry_data.items():
            try:
                module_name, class_name = class_path.rsplit('.', 1)
                module = importlib.import_module(module_name)
                driver_class = getattr(module, class_name)
                loaded_registry[identifier] = driver_class
            except (ImportError, AttributeError, ValueError):
                # This can happen if a file is moved or a class is renamed
                continue 
        print("--- Loaded driver registry from cache. ---")
        return loaded_registry
    except (IOError, json.JSONDecodeError):
        return {}

def _save_registry_to_cache(registry):
    """Saves the current driver registry to the JSON cache file."""
    serializable_registry = {
        identifier: f"{driver_class.__module__}.{driver_class.__name__}"
        for identifier, driver_class in registry.items()
    }
    try:
        with open(_CACHE_FILE, 'w') as f:
            json.dump(serializable_registry, f, indent=4)
        print(f"--- Saved updated driver registry to {_CACHE_FILE} ---")
    except IOError:
        print(f"Warning: Could not save registry cache to {_CACHE_FILE}")


STATIC_DRIVER_REGISTRY = _load_registry_from_cache()
_dynamic_scan_complete = False

def _dynamic_driver_scan():
    """Dynamically discovers drivers and updates the static registry."""
    global _dynamic_scan_complete
    if _dynamic_scan_complete:
        return
    
    print("--- Running dynamic driver scan... ---")
    drivers_path = Path(__file__).parent
    
    EXCLUDED_DIRS = ['z_old', 'old', '__pycache__', 'outline']
    
    new_drivers_found = False
    for file_path in drivers_path.glob('**/*.py'):
        if any(part in EXCLUDED_DIRS for part in file_path.parts):
            continue  # Skip this file if it's in an excluded directory

        if file_path.name in ('__init__.py', 'instrument.py', 'utilities.py', 'scpi.py'):
            continue
        
        root_package = drivers_path.parent.name
        drivers_package = drivers_path.name
        sub_module_path = '.'.join(file_path.relative_to(drivers_path).parts).replace('.py', '')
        module_path = f"{root_package}.{drivers_package}.{sub_module_path}"

        try:
            module = importlib.import_module(module_path)
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Get the identifier attribute, which can be a string or a list of strings
                identifier_attr = getattr(obj, 'AUTODETECT_ID', getattr(obj, 'idn', getattr(obj, 'model', None)))
                
                # Ensure we have a list to iterate over, whether it's a single string or a list
                if isinstance(identifier_attr, str):
                    identifiers = [identifier_attr] # Treat a single string as a list with one item
                elif isinstance(identifier_attr, list):
                    identifiers = identifier_attr
                else:
                    continue # Skip if it's not a string or a list

                # Loop through all provided identifiers and register the driver for each one
                for identifier in identifiers:
                    if isinstance(identifier, str) and identifier and identifier not in STATIC_DRIVER_REGISTRY:
                        print(f"  -> Discovered new driver: '{identifier}' -> {obj.__name__}")
                        STATIC_DRIVER_REGISTRY[identifier] = obj
                        new_drivers_found = True
        except Exception as e:
            print(f"  [DEBUG] Failed to import or inspect module '{module_path}'. Reason: {e}")
            pass

    if new_drivers_found:
        _save_registry_to_cache(STATIC_DRIVER_REGISTRY)
    else:
        print("--- Dynamic scan complete. No new drivers found. ---")

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
    """
    print(f"\n🔎 Probing instrument at {address}...")
    instrument_id = _probe_scpi(address)

    if not instrument_id:
        print(f"❌ Could not get an ID from the instrument at {address}.")
        return None
        
    print(f"  - VISA ID: '{instrument_id}'")

    driver_class = _find_match_in_registry(instrument_id)

    if not driver_class:
        print("  - Driver not in cached registry. Starting dynamic scan...")
        _dynamic_driver_scan()
        driver_class = _find_match_in_registry(instrument_id)

    if driver_class:
        id_key = next((key for key, val in STATIC_DRIVER_REGISTRY.items() if val == driver_class), None)
        print(f"✅ Match found for '{id_key}'! Initializing driver: {driver_class.__name__}")
        try:
            return driver_class(address=address)
        except Exception as e:
            print(f"  - Error initializing {driver_class.__name__}: {e}")
            return None

    print(f"❌ No matching driver found for the instrument at {address} after full scan.")
    return None

