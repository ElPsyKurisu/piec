Measurements
============

The `piec` library facilitates various experimental measurements, primarily managed through specialized classes. These classes help configure instrumentation, define measurement sequences, and process acquired data. The core measurement functionalities can be found within the :doc:`api/piec.measurement_waveforms` API documentation.

The general workflow for conducting a measurement typically involves:
1. Initializing the specific measurement class with instrument objects and parameters.
2. (Optionally) Using class methods to configure the connected instruments.
3. Calling a `run_experiment()` method (or similar) to execute the measurement sequence.
4. Utilizing analysis methods provided by the class or exporting data for external analysis.

Discrete Waveform Measurements
------------------------------

These measurements involve applying custom voltage waveforms using an Arbitrary Waveform Generator (AWG) and capturing the material's response, typically with an oscilloscope. These are primarily based on the :class:`~piec.measurement_waveforms.discrete_waveform.DiscreteWaveform` base class.

Hysteresis Loops
~~~~~~~~~~~~~~~~

Hysteresis loop measurements are crucial for characterizing ferroelectric materials. This involves applying a triangular voltage sweep to the material and measuring the resulting polarization.

*Key Class:* :class:`~piec.measurement_waveforms.discrete_waveform.HysteresisLoop`

**Example:**

.. code-block:: python

   from piec.measurement_waveforms import HysteresisLoop
   # Assuming awg_obj and osc_obj are pre-initialized instrument objects
   # (e.g., using drivers from piec.drivers)

   hyst_experiment = HysteresisLoop(
       awg=awg_obj,
       osc=osc_obj,
       frequency=1000.0,  # Hz
       amplitude=5.0,    # Volts
       n_cycles=3,
       v_div=0.5,        # Oscilloscope Volts/div for response channel
       area=1.0e-9,      # Device area in m^2 (for polarization calc)
       save_dir="path/to/save/data"
   )

   # To run the full experiment (configures instruments, applies waveform, captures, saves, analyzes):
   # hyst_experiment.run_experiment()

   # For more details on parameters and methods:
   # help(HysteresisLoop)
   # Or refer to the API documentation.

PUND Measurements (Three-Pulse PUND)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Positive-Up-Negative-Down (PUND) measurements are used to characterize the switching polarization of ferroelectric materials by applying a specific sequence of voltage pulses. This helps differentiate between switching and non-switching components of polarization.

*Key Class:* :class:`~piec.measurement_waveforms.discrete_waveform.ThreePulsePund`

**Example:**

.. code-block:: python

   from piec.measurement_waveforms import ThreePulsePund
   # Assuming awg_obj and osc_obj are pre-initialized instrument objects

   pund_experiment = ThreePulsePund(
       awg=awg_obj,
       osc=osc_obj,
       reset_amp=5.0,      # Volts for the initial reset pulse
       reset_width=1e-3,   # seconds
       reset_delay=1e-3,   # seconds
       p_u_amp=4.5,        # Amplitude for P and U pulses (Volts)
       p_u_width=0.5e-3,   # Width for P and U pulses (seconds)
       p_u_delay=0.5e-3,   # Delay between P and U pulses (seconds)
       v_div=0.5,          # Oscilloscope Volts/div
       area=1.0e-9,        # Device area in m^2
       save_dir="path/to/save/data"
   )

   # To run the full experiment:
   # pund_experiment.run_experiment()

   # For more details:
   # help(ThreePulsePund)
   # Or refer to the API documentation.
