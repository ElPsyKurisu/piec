Usage
=====

.. _installation:

Installation
------------

To use piec, first install it using pip:

.. code-block:: console

   (.venv) $ pip install piec

Then if using GPIB to communicate installInstall NI 488.2 Drivers from
https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#544048

NOTE: If using digilient drivers then optional install of UL is required:
http://www.mccdaq.com/swdownload

----------------

To connect to an instrument we use pyvisa. If the instrument address is unknown we can 
use pyvisa to identify the detected addresses:

>>> from pyvisa import ResourceManager
>>> rm = ResourceManager()
>>> rm.list_resources()
('GPIB0::7::INSTR',
 'GPIB0::8::INSTR',
 'USB0::0x0958::0x17A7::MY62080068::0::INSTR')

you can use the ``piec.drivers`` class to import either a generic or specific instruemnt:

For example, if the awg's GPIB address is set to 8 and we are using the specific
driver for the Keysight81150a then:

>>> import piec as pc
>>> from pc.drivers.keysight81150a import Keysight81150a
>>> awg = Keysight81150a('GPIB0::8::INSTR')
>>> awg.idn()
'Agilent Technologies,81150A,MY53821602,3.0.0.0-4.6\n'

