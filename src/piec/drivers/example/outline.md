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


NOTE: For outline, a good idea is to put the minimum args a class can take in the class attributes, with the correct names all instruments must take (then AI can translate to equivelent)


Command name syntax:
if it says set_something() Then it should do a single action
if it says configure_something() Then it should do multiple operations
if it says get_something() Then it should return something


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
NOTE: do NOT assume any of the argument values mentioned in the parent docstring apply to this instrument, take only the paramters from the manual
NOTE: When reading the parent class commands, only listen to the docstring and IGNORE ALL CODE BELOW THE DOCSTRING. That implementation is not guarenteed to work for the driver you are making. Instead we use the docstring of the parent class to get the gist of what we want to do

Part 2:
After we have successfully filled out the parent classes for our specific instrument we now focus on the class attributes we want to add to our instrument. We want to parse the manual and understand the limitations of our instrument and write them into the class attributes. We want to write class attributes for every argument passed in to the functions we wrote with the exception of arguments that take booleon values. Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
where the key of the dictionary is the argument this argument depends on.
THIS IS VERY IMPORTANT: All class attributes should have the same name as the arg it refers too!
When parsing the manual to understand what ranges to choose make sure we take the explicit values they give us associated with the command and not some calculation we make.

As a final check ensure that any write/query/read commands passed to the instrument come from the given manual (if a manual is given)
and prioritize example code over written descriptions if possible.


SECONDARY AI PROMPT (Given to a second AI to check the work of the first)
Given the following driver for an instrument and the given instrument files (manual) check the driver and make note of any discrepencies between the class attributes and the instrument parameters outlined in the manual. Our drivers class attributes are written in such a way that the attribute name MUST match exactly with the name of the argument in one of the driver functions.

1. Ensure all class attributes have the same name as an argument in one of the class methods
2. Ensure the class attribute values match what is in the given instrument manual
3. The given syntax is as follows:
Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']

If there are any discrepencies, and you can find the answer in the manual, make a list of the suggested changes and return what you would want to change, showing the old code, the new code, and the place in the manual you found the discrepancy. Otherwise, if no changes are necessary state that.


TERTIARY AI PROMPT:
You're job is to check the given driver's methods and ensure that ALL commands given to the instrument are valid based on the manual. E.g. go through each command and understand the command sent to the instrument and make sure it matches a valid command (with the correct syntax) from the manual. When looking at the manual prioritize example code to understand what is the correct command to send for the desired functionality. For every discrepency you find make a note of it and return what you would want to change, showing the old code, the new code, and the place in the manual where you found the discrepency. Otherwise, if no changes are necessary state that.



AI Prompt V3:
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

In order to get the functionality requested in the docstring of the parent class USE the manual and ensure that the given command comes from the given manual. When possible match the patterns in the given example code from the manual. The syntax for command names is given by the parent class but assume a set_something command does a single action and a configure_something command calls multiple set_something commands. A get_something command returns data. For all configure_something commands ensure all non-essential args are intiliazed to None (see example code in parent class). General writing guidelines for the functions is to again limit the use of text # comments and focus on the docstring given in the parent class and ensure what is asked there is implemented. If in the case an argument described in the parent class is not supported by the child instrument raise an error. Otherwise do not implement error handling for range checking etc (this will be done later at a global level).
Note, do NOT use \"{}\" for inputting an argument, assume the strings are implied in python

Part 2:
After we have successfully filled out the parent classes for our specific instrument we now focus on the class attributes we want to add to our instrument. Note the class attributes instantiated in the parent class. At minimum we want to fill out the the same class attributes as the parent class. We want to parse the manual and understand the limitations of our instrument and write them into the class attributes. We want to write class attributes for every argument passed in to the functions we wrote with the exception of arguments that take booleon values. Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
where the key of the dictionary is the argument this argument depends on.
THIS IS VERY IMPORTANT: All class attributes should have the same name as the arg it refers too!
When parsing the manual to understand what ranges to choose make sure we take the explicit values they give us associated with the command and not some calculation we make.

As a final check ensure that any write/query/read commands passed to the instrument come from the given manual (if a manual is given)
and prioritize example code over written descriptions if possible.


PART III:
You will notice in the parent class that are some class attributes, we need to make sure that the the class you made takes at minimum the valid arguments listed in the parent class. As an example, assume a parent class called parent has this attribute:

attributte = ["arg1", "arg2"]

Let's assume the child class from the manual lists that attributte can take more than just the attributtes listed. We should keep the args in the attribute but can add the extra ones afterwards, so we are left with
attributte = ["arg1", "arg2", "new_arg1", "new_arg2"]

Next step is the more difficult one. Let us say the parent class wants the argument "arg1" to be valid, but in our instrument manual the command to be passed through to the instrument is actually "different_arg1" that does the intended result of "arg1" in the parent class, we need to ensure that our instrument class method takes "arg1", but it gets translated to the correct argument to be passed to the instrument (e.g. self.instrument.write("different_arg1")) when given "arg1".


SECONDARY AI PROMPT (Given to a second AI to check the work of the first)
Given the following driver for an instrument and the given instrument files (manual) check the driver and make note of any discrepencies between the class attributes and the instrument parameters outlined in the manual. Our drivers class attributes are written in such a way that the attribute name MUST match exactly with the name of the argument in one of the driver functions.

1. Ensure all class attributes have the same name as an argument in one of the class methods
2. Ensure the class attribute values match what is in the given instrument manual
3. The given syntax is as follows:
Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']

If there are any discrepencies, and you can find the answer in the manual, make a list of the suggested changes and return what you would want to change, showing the old code, the new code, and the place in the manual you found the discrepancy. Otherwise, if no changes are necessary state that.


TERTIARY AI PROMPT:
Your job is to check the given driver's methods and ensure that ALL commands given to the instrument are valid based on the manual. E.g. go through each command and understand the command sent to the instrument and make sure it matches a valid command (with the correct syntax) from the manual. When looking at the manual prioritize example code to understand what is the correct command to send for the desired functionality. Furthermore, check the parent class and ensure that ALL parent class methods are overwritten correctly and no new extraneous class have been added. For every discrepency you find make a note of it and return what you would want to change, showing the old code, the new code, and the place in the manual where you found the discrepency. Otherwise, if no changes are necessary state that.

QUATERNARY AI PROMPT:
Your job is to check if the given arguments in the class attributes are valid commands when inputted in the class methods. As an example say I have a class attribute for attribbute1 = [arg1, arg2] and inside a class method I write self.instrument.write(f"Command{arg1}") but according to the manual it is not a valid command string, then try to figure out where the issue is and make a note of what you would change, showing the old code, the new code, and the place in the manual where you found the discrepency.

QUINARY AI PROMPT:
Your job is to look at the previous prompts, and implement them if told to do them. Understand the message below dictating what to implement or not based on the previous responses:
____

SENARY AI PROMPT:
Your job is to look at the completed driver and create a testing jupyter notebook. In the starting cell try to connect to the instrument using the piec formulation:
from piec.drivers.manufacturer.instrument import Instrument 
from piec.drivers.utilities import PiecManager

pm = PiecManager()
pm.list_resources()

#new cell
test_instrument = Instrument("Address") #leave this as is and the technician will run the cell and figure out the address is

#new cell
Start with a .idn() call to ensure we have the correct instrument

#new cell
logic to call the function as well as the expected output. The technician will be able to determine if it matches or not

...

Basically the job of this notebook is to walk the technician through testing to make sure the driver works. Make it as thorough as need be. And remember that the technician is running the cells sequentially from top to bottom, so a .reset() call may be in order between cells



AI Prompt V4:
class_name = ________
parent_classes = ______
attached_files = ______

You are tasked with creating an instrument specific python driver for the package piec according to the following syntax. Inside the piec package (which is attached) please note that under the drivers subpackage there exists an outline split into 4 Levels. Read and understand the outline.md file to get the gist of how the package should operate. We are operating in the Level_4 regime in this symbolic representation. Please check existing drivers for the import syntax from the outline (e.g.) piec.drivers.Keysight k_81150a.py to import the relevant parent classes. (e.g. if we wish to import the awg from the outline we would write from ..outline.Level_1.Level_2.Level_3.awg import Awg) Our driver has two main parts and the workflow should go as follows:

Part 1: For the given parent classes (except for the special case of level 1 classes e.g. scpi), our job is to overwrite all functions listed in the class (make sure to follow the function explicitly). For information how to actually complete the role of the function look for the given manual in the attached files. We do not want to use ANY text comments using # and instead should rely on a robust docstring in the given psuedo_code:

def function(self, arg1, arg2, arg3):
    """
    This function does something (brief general description)
    args:
        arg1 (argtype): Description
        arg2 (argtype): Description
        arg3 (argtype): Description
    returns
        something (return type) Description

In order to get the functionality requested in the docstring of the parent class USE the manual and ensure that the given command comes from the given manual. When possible match the patterns in the given example code from the manual. The syntax for command names is given by the parent class but assume a set_something command does a single action and a configure_something command calls multiple set_something commands. A get_something (or read_something) command returns data. For all configure_something commands ensure all non-essential args are intiliazed to None (see example code in parent class). General writing guidelines for the functions is to again limit the use of text # comments and focus on the docstring given in the parent class and ensure what is asked there is implemented. If in the case an argument described in the parent class is not supported by the child instrument raise an error. Otherwise do not implement error handling for range checking etc (this will be done later at a global level).
Note, do NOT use \"{}\" for inputting an argument, assume the strings are implied in python

Part 2:
After we have successfully filled out the parent classes for our specific instrument we now focus on the class attributes we want to add to our instrument. Note the class attributes instantiated in the parent class. At minimum we want to fill out the the same class attributes as the parent class. We want to parse the manual and understand the limitations of our instrument and write them into the class attributes. We want to write class attributes for every argument passed in to the functions we wrote with the exception of arguments that take booleon values. Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
where the key of the dictionary is the argument this argument depends on.
THIS IS VERY IMPORTANT: All class attributes should have the same name as the arg it refers too!
When parsing the manual to understand what ranges to choose make sure we take the explicit values they give us associated with the command and not some calculation we make.

As a final check ensure that any write/query/read commands passed to the instrument come from the given manual (if a manual is given)
and prioritize example code over written descriptions if possible.


PART III:
You will notice in the parent class that are some class attributes, we need to make sure that the the class you made takes at minimum the valid arguments listed in the parent class. As an example, assume a parent class called parent has this attribute:

attributte = ["arg1", "arg2"]

Let's assume the child class from the manual lists that attributte can take more than just the attributtes listed. We should keep the args in the attribute but can add the extra ones afterwards, so we are left with
attributte = ["arg1", "arg2", "new_arg1", "new_arg2"]

Next step is the more difficult one. Let us say the parent class wants the argument "arg1" to be valid, but in our instrument manual the command to be passed through to the instrument is actually "different_arg1" that does the intended result of "arg1" in the parent class, we need to ensure that our instrument class method takes "arg1", but it gets translated to the correct argument to be passed to the instrument (e.g. self.instrument.write("different_arg1")) when given "arg1".


SECONDARY AI PROMPT (Given to a second AI to check the work of the first)
Given the following driver for an instrument and the given instrument files (manual) check the driver and make note of any discrepencies between the class attributes and the instrument parameters outlined in the manual. Our drivers class attributes are written in such a way that the attribute name MUST match exactly with the name of the argument in one of the driver functions.

1. Ensure all class attributes have the same name as an argument in one of the class methods
2. Ensure the class attribute values match what is in the given instrument manual
3. The given syntax is as follows:
Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']

If there are any discrepencies, and you can find the answer in the manual, make a list of the suggested changes and return what you would want to change, showing the old code, the new code, and the place in the manual you found the discrepancy. Otherwise, if no changes are necessary state that.


TERTIARY AI PROMPT:
Your job is to check the given driver's methods and ensure that ALL commands given to the instrument are valid based on the manual. E.g. go through each command and understand the command sent to the instrument and make sure it matches a valid command (with the correct syntax) from the manual. When looking at the manual prioritize example code to understand what is the correct command to send for the desired functionality. Furthermore, check the parent class and ensure that ALL parent class methods are overwritten correctly and no new extraneous class have been added. For every discrepency you find make a note of it and return what you would want to change, showing the old code, the new code, and the place in the manual where you found the discrepency. Otherwise, if no changes are necessary state that.

QUATERNARY AI PROMPT:
Your job is to check if the given arguments in the class attributes are valid commands when inputted in the class methods. As an example say I have a class attribute for attribbute1 = [arg1, arg2] and inside a class method I write self.instrument.write(f"Command{arg1}") but according to the manual it is not a valid command string, then try to figure out where the issue is and make a note of what you would change, showing the old code, the new code, and the place in the manual where you found the discrepency.

QUINARY AI PROMPT:
Your job is to look at the previous prompts, and implement them if told to do them. Understand the message below dictating what to implement or not based on the previous responses:
____

SENARY AI PROMPT:
Your job is to look at the completed driver and create a testing jupyter notebook. In the starting cell try to connect to the instrument using the piec formulation:
from piec.drivers.manufacturer.instrument import Instrument 
from piec.drivers.utilities import PiecManager

pm = PiecManager()
pm.list_resources()

#new cell
test_instrument = Instrument("Address") #leave this as is and the technician will run the cell and figure out the address is

#new cell
Start with a .idn() call to ensure we have the correct instrument

#new cell
logic to call the function as well as the expected output. The technician will be able to determine if it matches or not

...

Basically the job of this notebook is to walk the technician through testing to make sure the driver works. Make it as thorough as need be. And remember that the technician is running the cells sequentially from top to bottom, so a .reset() call may be in order between cells

#This assumes a new method, where we do not attach the repo and only the parent class, so will need some python script to do it for us
#it should also make the template to hold the data. Aka need to make file called generate template
#typical attached files: scpi.py (if scpi), parent.py, manual.pdf
AI Prompt V5:
class_name = ________
parent_classes = ______
attached_files = ______

You are tasked with creating a driver based on the outline given as well as the manual attached. Your job is ONLY to fill out the driver classes and rename the appropiate parts. Based on the given .py file; first fill out the class attributes with regards to the manual. The syntax for class attributes is as follows:
Follow this syntax:
1. If the argument takes a limited number of values (e.g. channel) we write this in a list of the argtype (e.g. channel = [1,2])
2. If the argument takes a range of values (e.g voltage) we write this as a tuple of the appropiate type (e.g. amplitude = (0,5))
3. If the argument depends on another argument (e.g. frequency in the case of an AWG) we write this as a dictionary of the nested appropiate types (e.g. point 1 and 2 above) As an example if an awg has different frequency ranges for different waveforms (the argument frequency depends on the argument waveform) we write it as follows:
frequency = {'waveform': {'SIN': (1e-6, 240e6), 'SQU': (1e-6, 120e6), 'RAMP': (1e-6, 5e6), 'PULS': (1e-6, 120e6), 'pattern': (1e-6, 120e6), 'USER': (1e-6, 120e6)}}
waveform = ['SIN', 'SQU', 'RAMP', 'PULS', 'NOIS', 'DC', 'USER']
In addition to the attributes from the outline, you MUST add a new class attribute AUTODETECT_ID at the top of the class attributes section. To find its value, you must search the attached manual for the *IDN? (Identify or equivalent) command. Find the example response string. The value for AUTODETECT_ID MUST be the unique model identifier substring from that response (e.g., if the response is "KEYSIGHT,81150A,...", the ID is "81150A"; if it's "Stanford_Research_Systems,SR830,...", the ID is "SR830"). If the manual does not provide an example *IDN? response, you MUST set AUTODETECT_ID = None.

Please note that the given outline for the driver (the .py file) already may have some values filled out (e.g. some values are not None). In this case, the outline file (attached .py file) dictates what allowed arguments must be supported. An excellent example for this is that instruments that support channel arguments must accept the argument '1' (int format). Say some manual only accepts 'A' or 'B' then some logic must be taken in the driver side to map the argument 1 to a valid argument the instrument can take. If for example the parent class mentions a class attribute the specific instrument you are asked to implement does not have simply make it pass through (e.g. do nothing). An example again could be the channel argument. Let's say our instrument only has one port on it and thus only one channel so the developer never wrote any logic to switch channels. Simply allow the pass through of the argument channel=1 but make it do nothing.

Ok now try to fill out the driver classes and be sure too take programming examples from the manual if possible and do not assume anything that is not in the manual. Note, if the given prompt included SCPI as the parent class but the instrument (based on the manual) does not implement SCPI please try to create new commands that follow the exact same naming convention as the given SCPI parent class but with the correct implementation based on the driver, else raise a non_implemented error (and say its not supported)