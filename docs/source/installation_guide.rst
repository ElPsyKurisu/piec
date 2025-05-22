Installation Guide
==================

.. _installation:

Installing Piec
---------------
To use piec, first install it using pip:

.. code-block:: console

   (.venv) $ pip install piec

Dependencies and Drivers
------------------------
Depending on your instrumentation and how you connect to them, you might need additional drivers:

* **GPIB Communication**: If using GPIB to communicate, install NI 488.2 Drivers from the `National Instruments website <https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#544048>`_.
* **Digilent Drivers**: If using Digilent devices, optional installation of Universal Library (UL) for Linux may be required: `MCC DAQ <http://www.mccdaq.com/swdownload>`_.

Connecting to an Instrument
---------------------------
``piec`` uses `pyvisa` to communicate with instruments. If you don't know your instrument's address, you can list available resources:

.. code-block:: python

   from pyvisa import ResourceManager
   rm = ResourceManager()
   print(rm.list_resources())
   # Example Output: ('GPIB0::7::INSTR', 'USB0::0x0958::0x17A7::MY62080068::0::INSTR')

You can then use a specific driver from ``piec.drivers``:

.. code-block:: python

   # Assuming you have a Keysight 81150A AWG at GPIB address 8
   from piec.drivers.keysight81150a import Keysight81150a # Note: Ensure correct import path based on your driver structure
   
   awg_address = 'GPIB0::8::INSTR' # Replace with your actual instrument address
   try:
       awg = Keysight81150a(awg_address)
       print(f"Successfully connected to: {awg.idn()}") #
   except Exception as e:
       print(f"Could not connect to AWG at {awg_address}: {e}")

For more on drivers, see :doc:`drivers_overview`.