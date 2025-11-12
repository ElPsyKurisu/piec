"""
This is the top level instrument that dictates if something is 
scpi, dac, arduino, etc.

This class now includes the AutoCheckMeta framework for
automatic parameter validation.
"""
import functools
import inspect
import time
import re
import json
import os
import numpy as np
import pandas as pd

# Assuming utilities.py exists with PiecManager
# from .utilities import PiecManager

# Placeholder PiecManager if utilities.py is not present
# and to make this file runnable for testing.
try:
    from .utilities import PiecManager
except ImportError:
    print("Warning: Could not import PiecManager. Using placeholder.")
    class PiecManager:
        def open_resource(self, address, **kwargs):
            print(f"PiecManager: Opening {address} with {kwargs}")
            class DummyResource:
                def query(self, q): return f"DUMMY QUERY: {q}"
                def write(self, c): print(f"DUMMY WRITE: {c}")
                def read(self): return ""
            return DummyResource()

# --- Metaclass and Decorator for Auto-Checking ---

def auto_check_params(func):
    """
    Decorator to automatically call self._check_params on a method
    if the instance's `check_params` flag is True.
    Also converts all string arguments to lowercase.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        sig = inspect.signature(func)
        bound_args = sig.bind(self, *args, **kwargs)
        bound_args.apply_defaults()
        
        locals_dict = {k: v for k, v in bound_args.arguments.items() if k != 'self'}
        lower_params = convert_to_lowercase(locals_dict)
        
        if getattr(self, 'check_params', False):
            self._check_params(lower_params)
        
        # Update bound_args with the (potentially modified) lowercase values
        for key, value in lower_params.items():
            if key in bound_args.arguments:
                bound_args.arguments[key] = value

        return func(*bound_args.args, **bound_args.kwargs)
    
    return wrapper

class AutoCheckMeta(type):
    """
    Metaclass to apply the `auto_check_params` decorator to all
    public methods of a class (those not starting with '_').
    """
    def __new__(metacls, name, bases, class_dict):
        new_class_dict = {}
        for attr_name, attr_value in class_dict.items():
            if callable(attr_value) and not attr_name.startswith("_") and attr_name != '__init__':
                attr_value = auto_check_params(attr_value)
            new_class_dict[attr_name] = attr_value
        return super().__new__(metacls, name, bases, new_class_dict)

# --- Virtual Instrument (for testing) ---

class VirtualRMInstrument:
    """
    This class replaces the resource manager object in the virtual case,
    just needs to replace the .write() and .query() methods
    """
    def __init__(self, verbose:bool = False, **kwargs): # Added **kwargs
        self.verbose = verbose
        print('INITIALIZING VIRTUAL RESOURCE MANAGER, VISA NOT CONNECTED')
        current_dir = os.path.dirname(__file__)

        json_path = os.path.join(current_dir, "virtual_scpi_queries.json")
        self.query_dict = {}
        try:
            with open(json_path, "r") as file:
                self.query_dict = json.load(file)
        except FileNotFoundError:
            print(f"Warning: 'virtual_scpi_queries.json' not found at {json_path}.")
            
        # Add default IDN for SR830
        if "*IDN?" not in self.query_dict:
            self.query_dict["*IDN?"] = "Stanford_Research_Systems,SR830,s/n_virtual,ver1.0"
        if "ISRC?" not in self.query_dict:
            self.query_dict["ISRC?"] = "0" # Default to 'A' input

    def query(self, input:str):
        time.sleep(0.01)
        if self.verbose: print('Query recieved: ',input)
        response = self.query_dict.get(input)
        if response is not None: return response
        else:
            print('QUERY: ', input, ' NOT IN virtual_scpi_queries.json')
            return "VIRTUAL QUERY:"+ input

    def write(self, input:str):
        time.sleep(0.01)
        if self.verbose: print('Write recieved: ',input)
    
    def write_binary_values(self, data, scaled_data, datatype='h'):
        time.sleep(0.01)
        if self.verbose: print('Binary write recieved: ', data, scaled_data, datatype)
            
    def query_binary_values(self, query, datatype='h', is_big_endian=True):
        time.sleep(0.01)
        if self.verbose: print('Binary query recieved: ', query)
        return [0.0]

    def query_ascii_values(self, query):
        time.sleep(0.01)
        if self.verbose: print('ASCII query recieved: ', query)
        return [0.0]
        
    def read(self):
        if self.verbose: print('Read recieved')
        return ""

# --- Helper Functions for _check_params ---

def convert_to_lowercase(params):
    return {key: value.lower() if isinstance(value, str) else value for key, value in params.items()}

def is_contained(value, lst):
    if value is None: return True
    my_string = str(value).lower()
    my_list = [str(item).lower() for item in lst]
    return my_string in my_list

def is_value_between(value, num_tuple):
    if value is None: return True
    if type(value) is str: value = float(value)
    if len(num_tuple) != 2: raise ValueError("Tuple must contain exactly two numbers")
    lower_bound = num_tuple[0] if num_tuple[0] is not None else -float('inf')
    upper_bound = num_tuple[1] if num_tuple[1] is not None else float('inf')
    return lower_bound <= value <= upper_bound

def get_matching_keys(dict1, dict2):
    return list(set(dict1.keys()).intersection(dict2.keys()))

def get_class_attributes_from_instance(instance):
    cls = instance.__class__
    attributes = {}
    for base in reversed(cls.__mro__):
        attributes.update({attr: getattr(base, attr) 
                           for attr in base.__dict__ 
                           if not callable(getattr(base, attr)) and not attr.startswith("__")})
    return attributes

def recursive_lower(obj):
    if isinstance(obj, str): return obj.lower()
    if isinstance(obj, list): return [recursive_lower(item) for item in obj]
    if isinstance(obj, tuple): return tuple(recursive_lower(item) for item in obj)
    if isinstance(obj, dict):
        return { (k.lower() if isinstance(k, str) else k): recursive_lower(v)
                  for k, v in obj.items() }
    return obj

def exit_with_error(msg):
    raise ValueError(msg)

# --- Base Instrument Class ---

class Instrument(metaclass=AutoCheckMeta):
    """
    All an instrument is required to have is an address!
    This is the top-level class that provides connection management
    and the automatic parameter-checking framework.
    """
    def __init__(self, address, check_params=False, **kwargs):
        """
        Opens the instrument and enables communication with it.
        
        Args:
            address (str): The VISA/serial address or "VIRTUAL".
            check_params (bool): Toggle for enabling/disabling auto-check.
            **kwargs: Additional arguments for the resource manager 
                      (e.g., baud_rate=9600).
        """
        self.check_params = check_params
        self.virtual = (address.upper() == 'VIRTUAL')
        
        try:
            if self.virtual:
                self.instrument = VirtualRMInstrument(verbose=True, **kwargs)
            else:
                # Use your PiecManager to open the resource
                pm = PiecManager()
                self.instrument = pm.open_resource(address, **kwargs)
        
        except Exception as e:
            print(f"Error initializing instrument at {address}: {e}")
            print("Falling back to VIRTUAL mode.")
            self.instrument = VirtualRMInstrument(verbose=True, **kwargs)
            self.virtual = True

    def idn(self):
        """
        At minimum ANY instrument in PIEC should be able to be id'd.
        This method should be overridden by child classes.
        """
        return "Default IDN function not implemented, please override in subclass"

    def _check_params(self, locals_dict):
        """
        This is the parameter checking function that is called by the decorator.
        It validates function arguments against the class attributes.
        """
        class_attributes = recursive_lower(get_class_attributes_from_instance(self))
        keys_to_check = get_matching_keys(locals_dict, class_attributes)
        
        for key in keys_to_check:
            attribute_value = getattr(self, key)
            if attribute_value is None:
                print(f"Warning: no range-checking defined for \033[1m{key}\033[0m, skipping _check_params")
                continue
            
            attribute_value = recursive_lower(attribute_value)
            input_value = locals_dict[key]
            
            if input_value is None: continue

            if isinstance(attribute_value, tuple):
                if not is_value_between(input_value, attribute_value):
                    exit_with_error(f"Error input value of \033[1m{input_value}\033[0m for arg \033[1m{key}\033[0m is out of acceptable Range \033[1m{attribute_value}\033[0m")
            
            elif isinstance(attribute_value, list):
                if not is_contained(input_value, attribute_value):
                    exit_with_error(f"Error input value of \033[1m{input_value}\033[0m for arg \033[1m{key}\033[0m is not in list of acceptable \033[1m{attribute_value}\033[0m")
            
            elif isinstance(attribute_value, dict):
                dependency_keys = get_matching_keys(locals_dict, attribute_value)
                if len(dependency_keys) != 1:
                    print(f"WARNING: Found {len(dependency_keys)} dependency keys {dependency_keys} for '{key}', skipping checking.")
                    continue
                
                dep_key = dependency_keys[0]
                dep_value = locals_dict[dep_key]
                
                try:
                    valid_range = attribute_value[dep_key][dep_value]
                    if isinstance(valid_range, tuple):
                         if not is_value_between(input_value, valid_range):
                            exit_with_error(f"Error: input value \033[1m{input_value}\033[0m for arg \033[1m{key}\033[0m is out of range \033[1m{valid_range}\033[0m (for {dep_key} = '{dep_value}')")
                    elif isinstance(valid_range, list):
                        if not is_contained(input_value, valid_range):
                            exit_with_error(f"Error: input value \033[1m{input_value}\033[0m for arg \033[1m{key}\033[0m is not in list \033[1m{valid_range}\033[0m (for {dep_key} = '{dep_value}')")
                except KeyError:
                    exit_with_error(f"Error: Invalid dependency value '\033[1m{dep_value}\033[0m' for argument '\033[1m{dep_key}\033[0m'.")
                except Exception as e:
                    print(f"An error occurred during dependent parameter check for '{key}': {e}")