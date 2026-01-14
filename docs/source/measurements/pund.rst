PUND Measurements
=================

Positive-Up-Negative-Down (PUND) measurements are a crucial technique for characterizing the switchable polarization in ferroelectric materials. This method helps to differentiate the true ferroelectric switching current from non-switching contributions like leakage current and linear dielectric capacitance.

Theoretical Background
----------------------
A typical PUND sequence involves a series of voltage pulses:
1.  **Reset Pulse**: A pulse (often opposite to the first measurement pulse or a saturating pulse) to set the material into a known polarization state.
2.  **Positive (P) Pulse**: A pulse that switches the polarization. The current measured includes switching, capacitance, and leakage.
3.  **Up (U) Pulse**: An identical pulse to (P) applied shortly after. Since the material is already switched (ideally), the current measured primarily reflects non-switching components (capacitance, leakage).
4.  **Negative (N) Pulse**: A pulse opposite to (P) that switches polarization back.
5.  **Down (D) Pulse**: An identical pulse to (N) applied shortly after, measuring non-switching components in the opposite direction.

The switchable polarization is then calculated by subtracting the charge measured during the 'Up' pulse from the 'Positive' pulse (P-U), and similarly for (N-D). The ``piec`` library currently implements a three-pulse PUND (Reset, P, U).

Using ``piec`` for Three-Pulse PUND Measurements
-------------------------------------------------
The :class:`~piec.measurement.discrete_waveform.ThreePulsePund` class is used for these measurements.

**Example:**

.. code-block:: python

   from piec.measurement import ThreePulsePund
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
       save_dir="path/to/save/data",
       auto_timeshift=True
   )

   # To run the full experiment:
   # pund_experiment.run_experiment()

   # For more details:
   # help(ThreePulsePund)
   # Or refer to the API documentation.

Key Parameters
--------------
Key parameters for ``ThreePulsePund`` include:
* ``reset_amp``, ``reset_width``, ``reset_delay``: Amplitude (V), width (s), and delay (s) for the initial reset pulse.
* ``p_u_amp``, ``p_u_width``, ``p_u_delay``: Amplitude (V), width (s), and delay (s) for the P (Positive) and U (Up) measurement pulses.
* ``area`` (float): Device area in m² for polarization calculation.
* ``auto_timeshift`` (bool): If true, attempts to auto-detect the time offset by finding the first peak in the voltage response.

Analysis
--------
The ``analyze()`` method calls :func:`~piec.analysis.pund.process_raw_3pp` for data processing. This function:
* Calculates current and polarization from the raw oscilloscope data.
* Segments the data corresponding to P, U, and reset pulses.
* Calculates differential polarization (dP) values (e.g., P^ - P*).
* Generates and optionally saves plots of dP vs. time and current response with applied voltage.

API Reference
-------------
* :class:`~piec.measurement.discrete_waveform.ThreePulsePund`
* :func:`~piec.analysis.pund.process_raw_3pp`