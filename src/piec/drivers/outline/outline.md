The working tree for the outline of PIEC (beta version)

1. Instrument
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