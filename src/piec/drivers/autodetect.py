import re
import json
import importlib
import inspect
import os
from pathlib import Path
from .utilities import PiecManager
from .scpi import Scpi
from .digilent import Digilent

# Try importing MCCULW for the setup logic
try:
    from mcculw import ul
    from mcculw.enums import InterfaceType
    MCC_AVAILABLE = True
except ImportError:
    MCC_AVAILABLE = False
    ul = None

# --- Regex to find MCC devices ---
MCC_REGEX = re.compile(r'Device ADDRESS = (\S+)')

# --- Helper Functions ---

def _get_registry_path():
    """Returns the absolute path to the registry_cache.json file."""
    return Path(__file__).parent / "registry_cache.json"

def _load_registry_cache():
    """Loads the driver registry from the JSON file using absolute paths."""
    json_path = _get_registry_path()
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_registry_cache(registry):
    """Saves the registry to the JSON file."""
    json_path = _get_registry_path()
    try:
        with open(json_path, "w") as f:
            json.dump(registry, f, indent=4)
            print(f"Updated driver registry at: {json_path}")
    except Exception as e:
        print(f"Warning: Could not save registry cache. {e}")

def _import_class_from_path(class_path):
    """Dynamically imports a class from a dot-notation string."""
    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        print(f"Error importing class '{class_path}': {e}")
        return None

def _dynamic_driver_scan():
    """
    Scans the 'piec.drivers' package for classes with an 'AUTODETECT_ID'.
    """
    print("  -> Registry lookup failed. Running dynamic scan of driver files...")
    drivers_path = Path(__file__).parent
    found_registry = {}
    
    # Walk through all python files in the drivers directory
    for file_path in drivers_path.glob('**/*.py'):
        if any(x in file_path.parts for x in ['__pycache__', 'z_old', 'old']):
            continue
            
        try:
            # FIX: Calculate module path correctly relative to 'src' container
            # drivers_path.parent.parent should be the folder containing 'piec' package
            # e.g., .../src/
            
            # We find the path relative to the package root
            rel_path = file_path.relative_to(drivers_path.parent.parent) 
            
            # Convert file path to module string (e.g. piec.drivers.scope.k_dsox)
            # BUG FIX: Removed manual "piec." prefix as rel_path includes it
            module_str = ".".join(rel_path.with_suffix('').parts)
            
            module = importlib.import_module(module_str)
            
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if hasattr(obj, 'AUTODETECT_ID') and obj.__module__ == module.__name__:
                    idn_ids = getattr(obj, 'AUTODETECT_ID')
                    full_class_path = f"{obj.__module__}.{obj.__name__}"
                    
                    if isinstance(idn_ids, list):
                        for i in idn_ids:
                            found_registry[i] = full_class_path
                    else:
                        found_registry[idn_ids] = full_class_path
                        
        except (ImportError, ValueError, Exception) as e:
            # Optionally print errors if you need to debug specific files
            # print(f"Skipping {file_path.name}: {e}")
            continue

    return found_registry

def _setup_mcc_device(target_identifier=None, board_num=0):
    """
    Active MCC Configuration Logic.
    """
    if not MCC_AVAILABLE or ul is None:
        return False

    ul.ignore_instacal()
    
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices:
        return False

    target_device = None

    if target_identifier is None:
        print(f"MCC Auto-detect: Found {len(devices)} device(s). Selecting first: {devices[0].product_name}")
        target_device = devices[0]
    else:
        target_str = str(target_identifier)
        for device in devices:
            if (target_str in device.product_name or 
                target_str in device.unique_id or
                target_str == str(device.product_id)):
                target_device = device
                break
    
    if target_device:
        try:
            ul.create_daq_device(board_num, target_device)
            print(f"MCC Auto-detect: Configured {target_device.product_name} ({target_device.unique_id}) as Board {board_num}.")
            return True
        except Exception as e:
            print(f"Error configuring MCC device: {e}")
            return False
    
    return False

# --- Main Autodetect Function ---

def autodetect(address=None, **kwargs):
    """
    Automatically detects and connects to an instrument.
    
    Args:
        address (str, optional): 
            - If None: Scans for the first available MCC DAQ.
            - For MCC: Product ID or name (e.g. "1608").
            - For SCPI: VISA resource string (e.g. "USB0::...").
        **kwargs: Arguments passed to the driver class.
                  
    Returns:
        Instrument object (Digilent or Scpi subclass).
    """
    
    # --- 1. MCC / Digilent Detection Strategy ---
    is_mcc_likely = (address is None) or (MCC_AVAILABLE and "::" not in str(address))
    
    if is_mcc_likely and MCC_AVAILABLE:
        success = _setup_mcc_device(target_identifier=address, board_num=0)
        if success:
            return Digilent(address=0, **kwargs)
        elif address is None:
            print("No MCC devices found during auto-scan.")
            return None

    # --- 2. SCPI / VISA Detection Strategy ---
    if address:
        print(f"Autodetect: Probing SCPI device at {address}...")
        
        idn_string = None
        temp_inst = None
        try:
            temp_inst = Scpi(address=address)
            idn_string = temp_inst.query("*IDN?").strip()
            temp_inst.close()
            print(f"  -> Device responded: {idn_string}")
        except Exception as e:
            print(f"  -> Error communicating with device: {e}")
            if temp_inst: temp_inst.close()
            return None

        # B. Load Registry and Look for Match
        registry = _load_registry_cache()
        matched_class_path = None
        
        for key, path in registry.items():
            if key in idn_string:
                matched_class_path = path
                break
        
        # C. If no match, Run Dynamic Scan
        if not matched_class_path:
            new_registry = _dynamic_driver_scan()
            registry.update(new_registry)
            _save_registry_cache(registry)
            
            for key, path in registry.items():
                if key in idn_string:
                    matched_class_path = path
                    break

        # D. Instantiate Driver
        if matched_class_path:
            print(f"  -> Found specific driver: {matched_class_path}")
            DriverClass = _import_class_from_path(matched_class_path)
            if DriverClass:
                return DriverClass(address=address, **kwargs)
        
        # E. Fallback
        print("  -> No specific driver found. Returning generic SCPI instrument.")
        return Scpi(address=address, **kwargs)
    
    return None

connect_instrument = autodetect