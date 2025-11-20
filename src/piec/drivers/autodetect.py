import re
import json
import importlib
import inspect
from pathlib import Path
from .utilities import PiecManager
from .scpi import Scpi
from .digilent import Digilent

# Check for MCC Library
try:
    from mcculw import ul
    from mcculw.enums import InterfaceType
    MCC_AVAILABLE = True
except ImportError:
    MCC_AVAILABLE = False
    ul = None

MCC_REGEX = re.compile(r'Device ADDRESS = (\S+)')

def _get_registry_path():
    """Returns absolute path to registry_cache.json."""
    return Path(__file__).parent / "registry_cache.json"

def _load_registry_cache():
    try:
        with open(_get_registry_path(), "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def _save_registry_cache(registry):
    try:
        with open(_get_registry_path(), "w") as f:
            json.dump(registry, f, indent=4)
    except Exception as e:
        print(f"Warning: Could not save registry. {e}")

def _import_class_from_path(class_path):
    try:
        module_path, class_name = class_path.rsplit('.', 1)
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except Exception as e:
        print(f"Error importing {class_path}: {e}")
        return None

def _dynamic_driver_scan():
    """Scans drivers folder for AUTODETECT_ID."""
    print("  -> Scanning local drivers for match...")
    drivers_path = Path(__file__).parent
    found_registry = {}
    
    for file_path in drivers_path.glob('**/*.py'):
        if any(x in file_path.parts for x in ['__pycache__', 'z_old', 'old']):
            continue
            
        try:
            rel_path = file_path.relative_to(drivers_path.parent.parent) 
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
        except Exception:
            continue

    return found_registry

def _setup_mcc_device(target_identifier=None, board_num=0):
    if not MCC_AVAILABLE or ul is None: return False
    ul.ignore_instacal()
    devices = ul.get_daq_device_inventory(InterfaceType.ANY)
    if not devices: return False

    target_device = devices[0] 
    if target_identifier:
        t_str = str(target_identifier)
        for dev in devices:
            if t_str in dev.product_name or t_str in dev.unique_id or t_str == str(dev.product_id):
                target_device = dev
                break
    
    try:
        ul.create_daq_device(board_num, target_device)
        print(f"Digilent: Configured {target_device.product_name} as Board {board_num}")
        return True
    except Exception as e:
        print(f"Digilent Config Error: {e}")
        return False

def _safe_close(instrument):
    """Attempts to close the instrument safely without crashing."""
    if instrument is None:
        return
    try:
        # 1. Try the class method (if it exists)
        if hasattr(instrument, 'close'):
            instrument.close()
        # 2. Try the underlying pyvisa object (your preferred style)
        elif hasattr(instrument, 'instrument') and hasattr(instrument.instrument, 'close'):
             instrument.instrument.close()
    except Exception:
        # If it fails, we just pass as requested
        pass

def autodetect(address=None, **kwargs):
    # 1. MCC Logic
    is_mcc = (address is None) or (MCC_AVAILABLE and "::" not in str(address))
    if is_mcc and MCC_AVAILABLE:
        if _setup_mcc_device(address, 0):
            return Digilent(address=0, **kwargs)
        elif address is None:
            print("No MCC devices found.")
            return None

    # 2. SCPI Logic
    if address:
        print(f"Autodetect: Probing {address}...")
        temp_inst = None
        idn = ""
        try:
            temp_inst = Scpi(address=address)
            # Using .instrument.query() as you requested
            idn = temp_inst.instrument.query("*IDN?").strip() 
            _safe_close(temp_inst) # Close safely before returning
            print(f"  -> IDN: {idn}")
        except Exception as e:
            print(f"  -> Connection failed: {e}")
            _safe_close(temp_inst)
            return None

        # Registry Lookup
        registry = _load_registry_cache()
        match = next((v for k, v in registry.items() if k in idn), None)
        
        # Dynamic Fallback
        if not match:
            new_reg = _dynamic_driver_scan()
            registry.update(new_reg)
            _save_registry_cache(registry)
            match = next((v for k, v in registry.items() if k in idn), None)

        if match:
            print(f"  -> Loading driver: {match}")
            cls = _import_class_from_path(match)
            if cls: return cls(address=address, **kwargs)

        print("  -> Using generic SCPI driver.")
        return Scpi(address=address, **kwargs)
    
    return None

connect_instrument = autodetect