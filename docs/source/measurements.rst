Measurements
=====

do later add modules

Overview
------------

Their are currently two ways to use piec with varying user experiences.
Firstly, we can you use the :doc:`notebook` to run the code in a jupyter notebook.
Secondly, we can use the :doc:`gui` to run the code in a gui.

Single Pulse Waveform Measurment
------------

Single Pulse Waveform Measurments are measurments performed by applying one custom waveform through a sample with an 
Arbitrary Waveform Generator (AWG) and measuring the current response via an oscilloscope (scope) measuring the voltage across a 50Ohm
termination to ground. These measurments are handled by measurement objects in the :doc:`piec.measurement_waveforms` module.