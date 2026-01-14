Hysteresis Loop Measurements
============================

Hysteresis loop measurements are fundamental for characterizing ferroelectric materials. This technique involves applying a time-varying electric field (typically a triangular voltage sweep) to the material and measuring the resulting electric polarization.

Theoretical Background
----------------------
A ferroelectric hysteresis loop (P-E or P-V loop) illustrates the non-linear relationship between polarization (P) and applied electric field (E). Key characteristics include:
* **Remanent Polarization (P_r)**: The polarization remaining when the applied field is reduced to zero.
* **Coercive Field (E_c or V_c)**: The magnitude of the reverse field required to bring the polarization to zero.
* **Saturation Polarization (P_s)**: The maximum polarization achievable under a strong applied field.
The shape and parameters of the hysteresis loop provide insights into the material's ferroelectric quality, switching behavior, and potential for memory applications.

Using ``piec`` for Hysteresis Measurements
-----------------------------------------
The :class:`~piec.measurement.discrete_waveform.HysteresisLoop` class is used to perform these measurements.

**Example:**

.. code-block:: python

   from piec.measurement import HysteresisLoop
   # Assuming awg_obj and osc_obj are pre-initialized instrument objects
   # (e.g., using drivers from piec.drivers like Keysight81150a, KeysightDSOX3024A)
   # awg_obj = Keysight81150a('GPIB0::AWG_ADDRESS::INSTR')
   # osc_obj = KeysightDSOX3024A('GPIB0::OSC_ADDRESS::INSTR')

   hyst_experiment = HysteresisLoop(
       awg=awg_obj,
       osc=osc_obj,
       frequency=1000.0,  # Hz
       amplitude=5.0,    # Volts
       n_cycles=3,       # Number of waveform cycles
       v_div=0.5,        # Oscilloscope Volts/div for response channel
       area=1.0e-9,      # Device area in m^2 (for polarization calculation)
       save_dir="path/to/save/data",
       show_plots=True,
       save_plots=True
   )

   # To run the full experiment (configures instruments, applies waveform, captures, saves, analyzes):
   # hyst_experiment.run_experiment()

   # For more details on parameters and methods:
   # help(HysteresisLoop)
   # Or refer to the API documentation.

Key Parameters
--------------
The ``HysteresisLoop`` class takes several parameters during initialization. Some important ones include:
* ``awg``: An initialized AWG instrument object.
* ``osc``: An initialized Oscilloscope instrument object.
* ``frequency`` (float): The frequency of the triangular excitation waveform in Hz.
* ``amplitude`` (float): The peak voltage amplitude of the waveform in Volts.
* ``n_cycles`` (int): The number of triangular waveform cycles to generate and capture.
* ``area`` (float): The area of the device under test in m², used for polarization calculation.
* ``save_dir`` (str): Directory path for saving the measurement data.
* ``auto_timeshift`` (bool): If true, attempts to auto-detect the time offset of data.

Analysis
--------
The ``analyze()`` method, called as part of ``run_experiment()``, uses the :func:`~piec.analysis.hysteresis.process_raw_hyst` function to process the captured data. This function:
* Calculates current (in A) and polarization (in µC/cm²).
* Can perform automatic time offset correction.
* Generates and optionally saves plots of the P-V loop, I-V loop, and time traces of polarization and applied voltage.

API Reference
-------------
* :class:`~piec.measurement.discrete_waveform.HysteresisLoop`
* :func:`~piec.analysis.hysteresis.process_raw_hyst`