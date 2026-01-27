import re
import json
import importlib
import inspect
from pathlib import Path
from .utilities import PiecManager
from .scpi import Scpi

# Check for Digilent Library

from .digilent import Digilent


# Check for MCC Library
try:
    from mcculw import ul
    from mcculw.enums import InterfaceType
    MCC_AVAILABLE = True
except:
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

def _resolve_type_string(name):
    """
    Resolves a simple string like 'lockin' to the corresponding abstract/base Instrument class
    by dynamically scanning the 'drivers' directory.
    
    Logic:
    1. Look for a folder named {name} in drivers/
    2. Import piec.drivers.{name}.{name}
    3. Look for class {Name} (title case) in that module.
    """
    name = name.lower()
    
    # Special alias mappings if folder name differs from standard 'name/name.py' 
    # or if we want aliases like 'scope' -> 'oscilloscope'
    aliases = {
        'scope': 'oscilloscope',
    }
    name = aliases.get(name, name)

    drivers_path = Path(__file__).parent
    target_dir = drivers_path / name
    
    # Ignored directories
    if name in ['z_old', 'example', 'emulators', '__pycache__']:
        return None

    if target_dir.is_dir() and (target_dir / f"{name}.py").exists():
        try:
            # Construct module path: piec.drivers.{name}.{name}
            module_str = f"piec.drivers.{name}.{name}"
            module = importlib.import_module(module_str)
            
            # Look for TitleCase class, e.g. "lockin" -> "Lockin"
            # We can also search case-insensitive if needed.
            target_class_name = name.title()
            
            # Special case for acronyms if needed, or iterate all classes in module
            # checking for one that matches name (ignoring case)
            for cls_name, cls_obj in inspect.getmembers(module, inspect.isclass):
                if cls_name.lower() == name.lower():
                     return cls_obj
            
            # Fallback for standard Title Case if strict match failed
            return getattr(module, target_class_name, None)

        except (ImportError, AttributeError) as e:
            print(f"Autodetect: Found folder '{name}' but failed to load driver/class. {e}")
            return None

    return None

def _dynamic_driver_scan(verbose=False):
    """Scans drivers folder for AUTODETECT_ID."""
    if verbose:
        print("  -> Scanning local drivers for match...")
    drivers_path = Path(__file__).parent
    found_registry = {}
    
    for file_path in drivers_path.glob('**/*.py'):
        if any(x in file_path.parts for x in ['__pycache__', 'z_old', 'old', 'example']):
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

def _setup_mcc_device(target_identifier=None, board_num=0, verbose=False):
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
        if verbose:
            print(f"Digilent: Configured {target_device.product_name} as Board {board_num}")
        return target_device.product_name
    except Exception as e:
        if verbose:
            print(f"Digilent Config Error: {e}")
        return None

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

def autodetect(address=None, verbose=False, required_type=None, **kwargs):
    """
    Automatically detects and connects to an instrument.
    
    Args:
        address: Can be:
            - A VISA address string (e.g., "USB0::...")
            - An MCC identifier string or int (e.g., "0")
            - A Python Class (e.g., Lockin, Awg) -> performs checking scan
            - None -> defaults to scanning for MCC devices (legacy behavior)
        verbose (bool): If True, prints detailed scanning progress. Default False.
        required_type (type): Optional class type to filter results.
        **kwargs: Passed to the driver constructor.
    """
    # 0. Check if address is actually a Class or a known Type String
    target_class = None
    if isinstance(address, type):
        target_class = address
    elif isinstance(address, str) and "::" not in address:
        # Attempt to resolve string alias (e.g. "lockin")
        target_class = _resolve_type_string(address)

    if target_class:
        if verbose:
            print(f"Autodetect: Scanning for instrument of type {target_class.__name__}...")
        
        pm = PiecManager()
        resources = pm.list_resources()
        
        for res_address in resources:
            if verbose:
                print(f"  -> Checking {res_address}...")
            try:
                # Recursively call autodetect with the specific address
                # Capture print output? No, let it print.
                # Pass specific target class as required_type to optimize recursive scan
                inst = autodetect(address=res_address, verbose=verbose, required_type=target_class, **kwargs)
                
                if inst and isinstance(inst, target_class):
                    if required_type and not isinstance(inst, required_type):
                        _safe_close(inst)
                    else:
                        if verbose:
                            print(f"  -> MATCH: {res_address} is a {target_class.__name__}!")
                        return inst
                
                elif inst:
                    # Not the right type, close it
                    _safe_close(inst)
            except Exception as e:
                if verbose:
                    print(f"  -> Failed to check {res_address}: {e}")
                pass
        
        if verbose:
            print(f"No instrument of type {target_class.__name__} found.")
        return None

    # 1. MCC Logic
    is_mcc = (address is None) or (MCC_AVAILABLE and "::" not in str(address))
    if is_mcc and MCC_AVAILABLE:
        # If passed a long description string from list_resources, 
        # try to extract the useful part or let _setup_mcc_device handle it.
        # _setup_mcc_device does loose matching "in dev.product_name" etc.
        
        # Capture the product name returned by setup
        product_name = _setup_mcc_device(address, 0, verbose=verbose)
        
        if product_name:
            # OPTIMIZED LOGIC: Check registry for specific driver
            registry = _load_registry_cache()
            
            # Lookup using the product name (simulating IDN)
            match = next((v for k, v in registry.items() if k in product_name), None)

            if not match:
                new_reg = _dynamic_driver_scan(verbose=verbose)
                registry.update(new_reg)
                _save_registry_cache(registry)
                match = next((v for k, v in registry.items() if k in product_name), None)

            if match:
                if verbose:
                    print(f"  -> Loading MCC driver: {match}")
                cls = _import_class_from_path(match)
                
                # OPTIMIZATION: Check type BEFORE instantiation
                if cls and required_type and not issubclass(cls, required_type):
                    return None

                if cls: 
                    return cls(address=0, verbose=verbose, **kwargs)
            
            # Fallback to generic Digilent if no specific driver found
            # But strictly check type if required!
            if required_type and not issubclass(Digilent, required_type):
                 return None

            return Digilent(address=0, verbose=verbose, **kwargs)

        elif address is None:
            # Only print if this was an explicit None call, 
            # otherwise it might be a loop check
            # print("No MCC devices found.") 
            pass
        elif is_mcc and "::" not in str(address):
             # If it looked like MCC but failed setup, return None (don't fall through to SCPI)
             return None

    # 2. SCPI Logic
    if address and "::" in str(address):
        if verbose:
            print(f"Autodetect: Probing {address}...")
        temp_inst = None
        idn = ""
        try:
            temp_inst = Scpi(address=address)
            # Using .instrument.query() as you requested
            idn = temp_inst.instrument.query("*IDN?").strip() 
            _safe_close(temp_inst) # Close safely before returning
            if verbose:
                print(f"  -> IDN: {idn}")
        except Exception as e:
            if verbose:
                print(f"  -> Connection failed: {e}")
            _safe_close(temp_inst)
            return None

        # Registry Lookup
        registry = _load_registry_cache()
        match = next((v for k, v in registry.items() if k in idn), None)
        
        # Dynamic Fallback
        if not match:
            new_reg = _dynamic_driver_scan(verbose=verbose)
            registry.update(new_reg)
            _save_registry_cache(registry)
            match = next((v for k, v in registry.items() if k in idn), None)

        if match:
            if verbose:
                print(f"  -> Loading driver: {match}")
            cls = _import_class_from_path(match)
            
            # OPTIMIZATION: Check type BEFORE instantiation
            if cls and required_type and not issubclass(cls, required_type):
                return None
                
            if cls:
                print(f"Autodetect: Loaded {match} for instrument at {address}")
                return cls(address=address, verbose=verbose, **kwargs)

        # OPTIMIZATION: Check type BEFORE instantiation of generic SCPI
        if required_type and not issubclass(Scpi, required_type):
             return None

        print(f"Autodetect: connected to generic SCPI instrument at {address}")
        return Scpi(address=address, verbose=verbose, **kwargs)
    
    return None

connect_instrument = autodetect