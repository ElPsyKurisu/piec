Adding a Measurement
====================

This page explains how to add a new experiment type to piec. The complete,
normative checklist is maintained in
``src/piec/measurement/MEASUREMENT_DEVELOPER_GUIDE.md``.

Where to put the file
---------------------

Measurements live in ``src/piec/measurement/``. Add your class to an existing module if it
fits a category that already exists (e.g., ``discrete_waveform.py`` for AWG + oscilloscope
experiments), or create a new module for a distinct experiment category:

.. code-block:: text

   src/piec/measurement/
   ├── discrete_waveform.py   # AWG + oscilloscope experiments
   ├── magneto_transport.py   # Magnetotransport experiments
   └── your_category.py       # New module if needed

Choosing the right base class
------------------------------

* Inherit from ``DiscreteWaveform`` if your experiment uses an AWG to apply a waveform and
  an oscilloscope to capture the response.
* Inherit from ``MagnetoTransport`` for experiments involving magnetic fields and transport
  measurements.
* Create a standalone class following the measurement lifecycle guide for experiments that
  do not fit an existing category. There is currently no universal ``Measurement`` base class.

Implementing the required methods
-----------------------------------

Standalone measurement classes should expose the common lifecycle:

``_update_metadata(self)``
   Build the standard one-row metadata table, including parameters, instrument identities,
   timestamp, measurement type, units, and processing state.

``configure_instruments(self)``
   Prepare each instrument without starting the stimulus. Existing families may use a more
   specific method such as ``configure_awg``.

``capture_data(self)``
   Acquire the measurement into ``self.data`` as a pandas DataFrame.

``analyze(self)``
   Read the raw captured data, compute physical quantities, and generate / save plots.
   Call the appropriate function from ``piec.analysis`` if one exists.

``save_data(self)``
   Write the standard metadata-plus-data CSV using the helpers in
   ``piec.analysis.utilities``. Existing waveform classes may use ``save_waveform``.

``run_experiment(self)``
   Coordinate configuration, capture, safe output shutdown, analysis, saving, and history.

Long-running measurements must support cooperative cancellation, and active hardware outputs
must be disabled in a ``finally`` block. See the full development guide for GUI, streaming,
virtual-operation, and testing requirements.

Adding analysis functions
--------------------------

If your measurement requires new analysis code, add it to the appropriate module in
``src/piec/analysis/`` (e.g., ``hysteresis.py``, ``pund.py``), or create a new module.
Document each public function with a docstring that describes arguments, return values, and
units.

Documenting the measurement
-----------------------------

Add a new ``.rst`` file to ``docs/source/measurements/`` following the template of existing
pages (:doc:`../measurements/ferroelectric`, etc.). Then add it to
the ``Measurements`` toctree in ``docs/source/index.rst``.
