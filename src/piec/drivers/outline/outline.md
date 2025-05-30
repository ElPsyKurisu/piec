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