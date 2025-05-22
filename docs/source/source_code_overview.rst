Source Code Overview
====================

The ``piec`` library is organized into several key Python packages and modules, each responsible for different aspects of its functionality. Understanding this structure can be helpful for both using and contributing to the library.

Core Packages
-------------

* **:py:mod:`piec.drivers`**:
    This package contains the instrument driver framework. It includes base classes like :class:`~piec.drivers.instrument.Instrument` and :class:`~piec.drivers.scpi_instrument.SCPI_Instrument`, as well as specific drivers for various pieces of laboratory equipment (e.g., AWGs, oscilloscopes, DMMs, lock-in amplifiers). For more details, see the :doc:`drivers_overview` and the :mod:`piec.drivers` API documentation.

* **:py:mod:`piec.measurement_waveforms`**:
    This package implements the classes responsible for carrying out specific experimental measurements. Examples include :class:`~piec.measurement_waveforms.discrete_waveform.HysteresisLoop`, :class:`~piec.measurement_waveforms.discrete_waveform.ThreePulsePund`, and :class:`~piec.measurement_waveforms.magneto_transport.AMR`. These classes typically orchestrate instrument control, data acquisition, and basic analysis. Refer to the :doc:`measurements_overview` and the :mod:`piec.measurement_waveforms` API documentation.

* **:py:mod:`piec.analysis`**:
    Contains modules and functions for processing and analyzing the data collected from experiments. For instance, :mod:`~piec.analysis.hysteresis` for hysteresis loop analysis and :mod:`~piec.analysis.pund` for PUND data processing.

* **:py:mod:`piec.guis`**:
    This directory holds the source code for any Graphical User Interfaces (GUIs) provided with ``piec``. See :doc:`gui_guide`.

* **:py:mod:`piec.notebooks`** (if notebooks are part of the source package, otherwise refer to top-level notebooks directory):
    Contains Jupyter notebooks with examples, tutorials, and demonstrations of ``piec`` functionalities. See :doc:`notebook_examples`.


Navigating the API
------------------
For a comprehensive, automatically generated reference of all public modules, classes, and functions, please consult the :doc:`api_reference`.

The main package structure is also reflected in the toctree of the API documentation:

.. toctree::
   :maxdepth: 1

   API Docs for piec.analysis <api_generated/piec.analysis>
   API Docs for piec.drivers <api_generated/piec.drivers>
   API Docs for piec.guis <api_generated/piec.guis>
   API Docs for piec.measurement_waveforms <api_generated/piec.measurement_waveforms>
   API Docs for piec.notebooks <api_generated/piec.notebooks>