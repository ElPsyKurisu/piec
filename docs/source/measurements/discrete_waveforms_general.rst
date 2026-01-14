General Discrete Waveform Measurements
======================================

Many experiments in ``piec`` that involve applying specific voltage patterns and capturing responses are built upon the :class:`~piec.measurement.discrete_waveform.DiscreteWaveform` base class.

Overview
--------
The ``DiscreteWaveform`` class provides a foundational structure for experiments that require:
* An Arbitrary Waveform Generator (AWG) to output custom voltage signals.
* An Oscilloscope (OSC) to capture the material's response.

Core Functionality
------------------
Key functionalities provided by ``DiscreteWaveform`` include:
* Initialization of AWG and Oscilloscope.
* Basic configuration for AWG (impedance, trigger source).
* Configuration for Oscilloscope (timebase, channel settings, trigger).
* A standardized ``run_experiment()`` method that orchestrates instrument setup, waveform application, data capture, saving, and analysis.
* Placeholders for ``configure_awg()`` and ``analyze()`` which must be implemented by child classes to define the specific waveform and data processing.

Child Classes
-------------
Specific measurement types like :doc:`hysteresis` and :doc:`pund` are implemented as child classes of ``DiscreteWaveform``. These child classes:
* Define the ``type`` attribute (e.g., "hysteresis", "3pulsepund").
* Implement ``configure_awg()`` to generate the specific voltage waveform required for the measurement.
* Implement ``analyze()`` to call the appropriate analysis functions for the collected data.

API Reference
-------------
* :class:`~piec.measurement.discrete_waveform.DiscreteWaveform`