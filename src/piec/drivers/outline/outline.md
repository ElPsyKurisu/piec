The working tree for the outline of PIEC (beta version)

1. Instrument // scpi // digilent etc
2. Generator // Measurer (name WIP) // Other (stepper_motor, need a better name for this like indirect, bystander, secondary)
3. AWG, RF_source, Pulser, Source_meter // Oscilloscope, Lockin, DAQ // Stepper_motor
4. Individual models NOTE: may be good for SCPI commands to make a base SCPI class that has all the reset, clear commands and if SCPI inherits from it as well


Note this is different than before:
1. Instrument
2. SCPI_instrument // Arduino // Digilent 
3. generic instruments
4. specific instruments


NOTE: For file ordering would be nice to have it with depth, not all files in the same directory -> basically use folders and each level correspnds to the working tree level

NOTE: Should also figure out how we want to add additional items to classes. As an example for the oscilloscope.py outline for configuring the trigger there are a few base options
but under the configure_trigger of the keysight scope theres additional stuff like filters and hold_off times -> therefore we require a method for running expirements that simply ignores
the additional commands (not present in the outine) base commands for running expirements. Therfore my code (or Alexs tbh) would still run with a scope that doesnt have that capability
but for a scope that does (and has the driver) written for it it will configure the hold_off time etc.

NOTE: Under Level 4 maybe put each instrument under the manufacturer so they are additional folders but same level in working tree (aka class inheritance)


Command name syntax:
if it says set_something() Then it should do a single action
if it says configure_something() Then it should do multiple operations


AI PROMPT:
This is a prompt for writing the driver for a specific instrument: e.g. Keysight 81150a
Note the place to create the driver is under Level 4 for specific instruments, and all instruments will be a .py file with the model number as the name of the file e.g. 81150a.py under the Keysight folder (the manufacturer name). The goal is to create a robust driver that has two main parts -> all the functionality of the parent classes (at a minimum). If given a manual: Use only functionality derived from the manual (unless the manual does not specifiy the intended function). The syntax for the functions is that if it starts with "set" it does a SINGLE action and a "configure" function calls multiple "set" functions. The second part of the functionality is that for EVERY function argument (besides self and boolean values) we add a class attribute from the manual that restricts the allowed args. As an example take the output command that takes in two arguments (besides self) "channel" and "on". Since on is a boolean value we do not need to add a class attribute for it but channel we do. We take a look at the manual and discover that the Keysight 81150a has two channels. Thus we add a class attribute channel = [1, 2] at the top of the Class. This should be done in retrospect after we finish writing all the parent functionality out. As an example for the keysight81150 a few of them are shown below

class 81150a(Awg):
    """
    Specific Class for this exact model of awg: Keysight 81150A
    """
    #add class attributes here, like max y range etc
    #correct syntax is tuple for ranges, list for limited amount, and dictionaries for nested things...
    channel = [1, 2]
    amplitude = (0, 5) #V_pp
    frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
    waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
    #note that depends if we are in high voltage or high bandwidth mode, if in high bandwidth mode all are 50e6 max freq
    slew_rate = 1.0e9 # V/s
    arb_wf_points_range = (2, 524288)
    source_impedance = [5, 50]
    load_impedance = (0.3, 1e6)

In the case of the 81150a it gets a little more complicated but the general format for the class attributes is that if there is a limited amount the valid args can take use a list of the correct type. If it is a range use a tuple, and if there are specific cases uses a dictionary. An example of this is that the frequnecy ranges (which should be a tuple) depends on the selected waveform, so we nest it as shown.

So the goal is to go through the manual and find the correct commands to send to the instrument to fill out the desired functionality. then based on the manual fill out the class attributes if you can. If you do not find a class attribute set it to None. One last design consideration is that for EVERY configure command, initialize all non-essential arguments to none. E.g. 
def configure_waveform(self, channel, waveform, frequency=None, delay=None, amplitude=None, offset=None, load_impedance=None, source_impedance=None, polarity=None):
        """
        Configures the waveform to be generated on the selected channel. Calls the set_waveform, set_frequency, set_delay, set_amplitude, set_offset, set_load_impedance, set_source_impedance and set_polarity functions to configure the waveform
        args:
            channel (int): The channel to configure the waveform on
            waveform (str): The waveform to be generated
            frequency (float): The frequency of the waveform in Hz
            delay (float): The delay of the waveform in seconds
            amplitude (float): The amplitude of the waveform in volts
            offset (float): The offset of the waveform in volts
            load_impedance (float): The load impedance of the waveform in ohms
            source_impedance (float): The source impedance of the waveform in ohms
            polarity (str): The polarity of the waveform
        """

Will need to check if param is not None before calling the function


"holder"
"""
Driver for the Keysight DSOx3024a oscilloscope.
This class implements the specific functionalities for the DSOx3024a model,
inheriting from generic Oscilloscope and Scpi classes.
"""


from ...oscilloscope import Oscilloscope
from .....scpi import Scpi

class Dsox3024a(Oscilloscope, Scpi):
    """
    Specific Class for this exact model of scope: Keysight DSOX3024a.
    """

    # Class attributes for parameter restrictions, named after function arguments.

As a final check ensure that any write/query/read commands past to the instrument come from the given manual (if a manual is given)

might be good to also make a seperate testing file that tests that the commands work as expected. Thus if we make a command that creates an arb waveform we can cehck if it exists by quering the instrument for the arb valuies defined


AI Prompt V2:
class_name = ________
parent_classes = ______
attached_files = ______

You are tasked with creating an instrument specific python driver for the package piec according to the following syntax. Inside the piec package (which is attached) please note that under the drivers subpackage there exists an outline split into 4 Levels. Read and understand the outline.md file to get the gist of how the package should operate. We are operating in the Level_4 regime in this symbolic representation. Please check existing drivers for the import syntax from the outline (e.g.) piec.drivers.Keysight k_81150a.py to import the relevant parent classes. (e.g. if we wish to import the awg from the outline we would write from ..outline.Level_1.Level_2.Level_3.awg import Awg) Our driver has two main parts and the workflow should go as follows:

Part 1: For every parent class functionality we should explicitly overwrite the functions according to the given manual in the attached_files with the exception of Level_1 classes (e.g. scpi.py). We do not want to use ANY text comments using # and instead should rely on a robust docstring in the given psuedo_code:

def function(self, arg1, arg2, arg3):
    """
    This function does something (brief general description)
    args:
        arg1 (argtype): Description
        arg2 (argtype): Description
        arg3 (argtype): Description
    returns
        something (return type) Description

In order to get the functionality requested in the docstring of the parent class USE the manual and ensure that the given command comes from the given manual. When possible match the patterns in the given example code from the manual. The syntax for command names is given by the parent class but assume a set_something command does a single action and a configure_something command calls multiple set_something commands. For all configure_something commands ensure all non-essential args are intiliazed to None (see example code in parent class). General writing guidelines for the functions is to again limit the use of text # comments and focus on the docstring given in the parent class and ensure what is asked there is implemented. If in the case an argument described in the parent class is not supported by the child instrument raise an error. Otherwise do not implement error handling for range checking etc (this will be done later at a global level).
Note, do NOT use \"{}\" for inputting an argument, assume the strings are implied in python

Part 2:
After we have successfully filled out the parent classes for our specific instrument we now focus on the class attributes we want to add to our instrument. We want to parse the manual and understand the limitations of our instrument and write them into the class attributes. We want to write class attributes for every argument passed in to the functions we wrote with the exception of arguments that take booleon values. Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
where the key of the dictionary is the argument this argument depends on.
THIS IS VERY IMPORTANT: All class attributes should have the same name as the arg it refers too!

As a final check ensure that any write/query/read commands passed to the instrument come from the given manual (if a manual is given)
and prioritize example code over written descriptions if possible.


