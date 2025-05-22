Instrument Drivers in Piec
==========================

A core feature of ``piec`` is its abstracted instrument driver model. This system allows for flexible communication with a wide variety of laboratory instruments, aiming to provide a consistent programming interface regardless of the specific instrument model or communication protocol (e.g., SCPI, serial/Arduino, vendor-specific libraries).

Core Concepts
-------------
The driver architecture is built upon a base :class:`~piec.drivers.instrument.Instrument` class. This class requires only an address for initialization.

Specialized base classes may inherit from ``Instrument`` to provide common functionality for certain types of protocols. For example:
* :class:`~piec.drivers.scpi_instrument.SCPI_Instrument`: Provides helper methods for instruments that primarily use Standard Commands for Programmable Instruments (SCPI). This includes common commands like ``*IDN?``, ``*RST``, ``*CLS``.

Specific instrument drivers (e.g., for a particular model of AWG or Oscilloscope) then inherit from one of these base classes and implement the detailed commands and logic required to control that hardware.

Driver Hierarchy and Philosophy
-------------------------------
The design philosophy for drivers in ``piec``, as outlined in the development notes, suggests a layered approach:

1.  **Level 1: Base Instrument Interface** (e.g., :class:`~piec.drivers.instrument.Instrument`)
2.  **Level 2: Communication Protocol / Broad Category** (e.g., :class:`~piec.drivers.scpi_instrument.SCPI_Instrument`, or conceptual groups like `Generator`, `Measurer`)
3.  **Level 3: Generic Instrument Type** (e.g., a generic `Oscilloscope` class that defines common oscilloscope functions)
4.  **Level 4: Specific Instrument Models/Manufacturers** (e.g., ``Keysight81150a``, ``KeysightDSOX3024A``). These implement the generic functions defined at Level 3 using model-specific commands.

This layered approach facilitates code reuse and allows for interchangeable drivers as long as they adhere to the interface defined by a common parent class (e.g., a generic `Oscilloscope` interface).

Using a Specific Driver
-----------------------
To use an instrument driver:
1.  Import the specific driver class from the ``piec.drivers`` module or its submodules (e.g., ``piec.drivers.keysight81150a``).
2.  Instantiate the class with the instrument's VISA address (or other connection identifier).

Example:
.. code-block:: python

   from piec.drivers.keysight81150a import Keysight81150a # Example AWG driver
   # from piec.drivers.some_manufacturer.some_oscilloscope import SomeOscilloscope

   try:
       awg = Keysight81150a('GPIB0::8::INSTR') # Replace with your AWG's address
       print(f"Connected to: {awg.idn()}")
   except Exception as e:
       print(f"Error connecting to AWG: {e}")

Exploring Available Drivers
---------------------------
The best way to explore available drivers is through the API documentation:

.. toctree::
   :maxdepth: 1

   API Reference <api_reference>

Specifically, refer to the :mod:`piec.drivers` section. You can also browse the source code in the ``src/piec/drivers/`` directory of the repository.
The available specific drivers include (but are not limited to):
* :class:`~piec.drivers.keysight81150a.core.Keysight81150a`
* :class:`~piec.drivers.keysightdsox3024a.core.KeysightDSOX3024A`
* :class:`~piec.drivers.sr830.core.SR830` (Lock-in Amplifier)
* :class:`~piec.drivers.edc522.core.EDC522` (Calibrator)
* :class:`~piec.drivers.keithley193a.core.Keithley193A` (DMM)
* :class:`~piec.drivers.arduino.Arduino`
* :class:`~piec.drivers.mccdig.MCCDig` (Digilent/MCC DAQ)

The documentation for these can often be found under their respective modules in the API Reference.