Measurements in Piec
====================

The ``piec`` library is designed to streamline various experimental measurements by providing specialized classes for common tasks. These classes typically handle:
* Configuration of necessary instruments (AWGs, oscilloscopes, DMMs, etc.).
* Definition and execution of measurement sequences.
* Acquisition and storage of data.
* Basic data processing and analysis.

General Workflow
----------------
Conducting a measurement with ``piec`` usually follows these steps:
1.  **Initialize Instruments**: Connect to the required instruments using their respective drivers.
2.  **Instantiate Measurement Class**: Create an instance of the desired measurement class (e.g., ``HysteresisLoop``), passing the initialized instrument objects and measurement parameters.
3.  **Configure (Optional)**: Some measurement classes might offer methods to fine-tune instrument settings before running the experiment.
4.  **Run Experiment**: Call a method like ``run_experiment()`` to execute the measurement sequence. This usually includes instrument configuration, waveform application, data capture, and saving.
5.  **Analyze Data**: Utilize built-in analysis methods or export data for external analysis.

Available Measurement Types
---------------------------
Explore the specific measurement types supported by ``piec``:

.. toctree::
   :maxdepth: 1

   measurements/hysteresis
   measurements/pund
   measurements/amr
   measurements/discrete_waveforms_general

The core functionalities for many waveform-based measurements can be found in the :doc:`api_reference/piec.measurement` documentation.