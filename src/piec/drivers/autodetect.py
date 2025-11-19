# In a new file, e.g., 'autodetect.py'
import re
import json
import importlib
from .utilities import PiecManager
from .scpi import Scpi
from .digilent import Digilent

# --- Regex to find MCC devices ---
MCC_REGEX = re.compile(r'Device ADDRESS = (\S+)')

# --- Helper Functions (same as before) ---

def _load_registry_cache(json_path="registry_cache.json"):
    """Loads the SCPI driver registry from your JSON file."""
    try:
        with open(json_path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: '{json_path}' not found. SCPI autodetect will fail.")
        return {}
    except json.JSONDecodeError:
        print(f"Error: Could not parse '{json_path}'.")
        return {}

def _import_class_from_path(class_path):
    """Dynamically imports a class from a dot-notation string."""
    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        print(f"Error importing class '{class_path}': {e}")
        return None

def _find_driver_in_registry(idn_string, registry):
    """Finds the correct driver class path from the registry."""
    for idn_key, class_path in registry.items():
        if idn_key in idn_string:
            return class_path
    return None

# --- The Main Connection Function (Corrected) ---

def connect_instrument(address, registry_path="registry_cache.json", **kwargs):
    """
    Connects to a single instrument using its partial or full address.
    
    This function automatically determines if the device is an
    MCC or SCPI instrument and returns the correct driver instance.
    
    Args:
        address (str): The address of the instrument.
                       - For SCPI: "GPIB0::10::INSTR"
                       - For MCC: The Product ID, e.g., "10141"
        registry_path (str): Path to your 'registry_cache.json' file.
        **kwargs: Additional arguments to pass to the driver.
                  
    Returns:
        An initialized driver instance (e.g., MCC_DAQ, KeysightDSOX3024a)
        or a generic Scpi instance if no specific driver is found.
    """
    pm = PiecManager()
    all_resources = pm.list_resources()

    # --- 1. Find the full resource string & identify all MCC devices ---
    full_resource_string = None
    all_mcc_resources = []
    
    for res in all_resources:
        if MCC_REGEX.search(res):
            all_mcc_resources.append(res)
        if address in res:
            full_resource_string = res
            
    if not full_resource_string:
        full_resource_string = address # Assume full VISA address

    # --- 2. Check if it's an MCC device ---
    mcc_match = MCC_REGEX.search(full_resource_string)
    
    if mcc_match:
        try:
            # It's an MCC device. We bypass the JSON registry.
            product_id = mcc_match.group(1)
            
            # --- THIS IS THE FIX ---
            # Find the device's index in the list of all MCC devices
            # This index (0, 1, 2...) is the board_num.
            board_num = all_mcc_resources.index(full_resource_string)
            
            print(f"Connecting to MCC device (PID: {product_id}) on auto-assigned board {board_num}...")
            # We use the explicitly imported MCC_DAQ class
            return Digilent(address=product_id, board_num=board_num, **kwargs)
        
        except ValueError:
            print(f"Error: MCC device {address} found but couldn't be indexed.")
            return None
        except Exception as e:
            print(f"Error connecting to MCC device {address}: {e}")
            return None

    # --- 3. If not MCC, assume SCPI/VISA ---
    # (This logic remains the same)
    print(f"Connecting to SCPI device at {full_resource_string}...")
    temp_inst = None
    try:
        registry = _load_registry_cache(registry_path)
        temp_inst = Scpi(address=full_resource_string)
        idn_string = temp_inst.query("*IDN?").strip()
        temp_inst.close() 
        
        print(f"  -> IDN: {idn_string}")
        class_path = _find_driver_in_registry(idn_string, registry)
        
        if class_path:
            DriverClass = _import_class_from_path(class_path)
            if DriverClass:
                print(f"  -> Found specific driver: {class_path}")
                return DriverClass(address=full_resource_string, **kwargs)

        print("  -> WARNING: No specific driver found in registry.")
        print("     Returning a generic 'Scpi' instance.")
        return Scpi(address=full_resource_string, **kwargs)
        
    except Exception as e:
        print(f"Error connecting to SCPI device {full_resource_string}: {e}")
        if temp_inst:
            temp_inst.close()
        return None