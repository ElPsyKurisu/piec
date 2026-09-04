# Measurement Development Guide

This guide defines the requirements and conventions for adding measurements to
the `piec` library. Following these rules keeps experiment classes, GUIs, saved
data, analysis, virtual operation, and instrument cleanup consistent across the
project.

## 1. The 3-Part Architecture

PIEC measurements have three cooperating parts. Keep their responsibilities
separate.

### Part 1: Measurement class (`src/piec/measurement/`)

The measurement class owns the experimental workflow. It receives initialized
instrument objects, stores parameters, configures instruments, captures data,
runs analysis, saves results, and guarantees safe cleanup.

The measurement class MUST NOT import or manipulate Tkinter/Qt widgets. It must
also be usable directly from a script or notebook without a GUI.

### Part 2: Analysis (`src/piec/analysis/`)

Reusable numerical processing belongs in `piec.analysis`. Measurement classes
may perform light organization of acquired data, but broadly useful fitting,
filtering, physical conversion, and plotting routines SHOULD live in an
analysis module.

Analysis functions MUST accept data and explicit parameters. They MUST NOT
depend on GUI state or open instrument connections.

### Part 3: GUI (`Measurements/<TYPE>/`)

The GUI collects user input, creates instruments and the measurement object,
starts the workflow, and displays results. New desktop GUIs MUST inherit from
`piec.measurement.gui_utils.MeasurementApp` so the project theme, sidebar,
settings, log console, shortcuts, and plot card remain consistent.

> [!IMPORTANT]
> There is currently no universal `Measurement` base class. Reuse an existing
> measurement family only when its hardware workflow fits. Otherwise implement
> the lifecycle in this guide as a standalone class. Do not claim inheritance
> from a base class that does not exist.

## 2. Choosing a Measurement Family

Use the narrowest existing family that genuinely matches the experiment:

- Inherit from `DiscreteWaveform` for an AWG-triggered waveform captured by an
  oscilloscope.
- Inherit from `MagnetoTransport` for its established field/rotation/lock-in
  workflow.
- Use a standalone class for a distinct workflow such as a sourcemeter-controlled
  I-V sweep.

Do not force an experiment into a family merely because it uses one similar
instrument. For portable measurements, depend on the instrument behavior the
experiment needs, not a specific model name.

## 3. Required Class State

Every concrete measurement class MUST expose these attributes:

```python
class ExampleMeasurement:
    mtype = "example"

    def __init__(self, instrument, parameter, save_dir=r"\\scratch"):
        self.instrument = instrument
        self.parameter = parameter
        self.save_dir = save_dir
        self.data = None
        self.metadata = None
        self.filename = None
        self.history = []
        self.abort_requested = False
        self.processed = False
        self._update_metadata()
```

- `mtype`: stable lowercase identifier used in filenames and metadata.
- `data`: acquired or processed `pandas.DataFrame`; `None` before capture.
- `metadata`: one-row `pandas.DataFrame` describing the run.
- `filename`: saved path; `None` until a file is written.
- `history`: metadata snapshots for completed runs when repeated runs are
  supported.
- `abort_requested`: cooperative stop flag for measurements that can run long
  enough to be controlled by a GUI.

Additional products such as `last_cycle`, `cycle_average`, or fitted parameters
SHOULD be explicit attributes rather than hidden globals.

## 4. Constructor Rules

- Accept initialized instrument objects through dependency injection. Do not
  open fixed VISA addresses inside the measurement class.
- Put measurement parameters and their units in the signature and docstring.
- Use project naming conventions such as `frequency`, `amplitude`, `n_cycles`,
  and `save_dir` when those meanings match existing measurements.
- Validate values before enabling hardware.
- Do not perform a measurement, enable an output, or create a file in
  `__init__`.
- Initialize mutable state on the instance, not as a mutable class attribute.
- Virtual and physical instruments must use the same measurement path.

Use the existing instrument-type interfaces whenever they fit. A DAQ acting as
an AWG or oscilloscope should use the existing emulator classes; do not add
measurement-specific methods to the DAQ base interface or virtual DAQ.

## 5. Standard Lifecycle Methods

Measurement method names convey their scope. A complete class SHOULD implement
the following lifecycle, using more specific configuration names where useful.

### `_update_metadata(self)`

Create or refresh the standard one-row metadata DataFrame. It MUST include:

- `mtype`;
- every parameter required to understand or reproduce the measurement;
- units or unit-bearing column names;
- instrument identification strings;
- `timestamp` from `time.time()`;
- a boolean `processed` flag.

Instrument objects, DataFrames, callbacks, threads, and other runtime-only
objects MUST NOT be stored directly in metadata.

### `configure_<instrument>(self)`

Configure one instrument or one hardware role. Examples are
`configure_awg`, `configure_sourcemeter`, and `configure_acquirer`. These
methods SHOULD prepare hardware without starting the experimental stimulus.

### `configure_instruments(self)`

For multi-instrument experiments, call each specific configuration method in a
clear order. Keep the individual methods public so a notebook user can inspect
or execute setup piecewise.

### `capture_data(self, ...)`

Perform acquisition and store a DataFrame in `self.data`. Long-running capture
loops MUST periodically check `abort_requested` or an equivalent stop event.
Streaming measurements MAY accept an update callback, but that callback must
receive plain data/snapshot objects rather than GUI widgets.

### `analyze(self)`

Create processed results or call functions in `piec.analysis`. If no analysis
is needed, preserve the method and report that clearly. Set `processed=True`
only after required processing succeeds.

### `save_data(self)`

Refresh metadata, create a unique path with
`create_measurement_filename`, and write the standard metadata-plus-data CSV
with `metadata_and_data_to_csv`. Do not overwrite an existing run silently.

Waveform-family classes may retain the established name `save_waveform`.

### `run_experiment(self)`

Coordinate the complete public workflow. The normal order is:

1. refresh metadata;
2. configure instruments;
3. capture data;
4. return outputs to a safe state;
5. analyze;
6. save data;
7. append a metadata copy to `history`.

The exact analysis/save order may differ when legacy analysis updates a saved
file, but the final file MUST contain the final metadata and data.

## 6. Hardware Safety and Cleanup

Output cleanup is mandatory, not optional error handling.

- Place output shutdown in a `finally` block around active acquisition.
- Stop or disable the stimulus before stopping feedback/acquisition.
- Electromagnets, high-voltage sources, heaters, and motion systems MUST expose
  a clear safe-state operation.
- Stimulus outputs MUST enter the configured safe state after success, failure,
  or cancellation.
- Cleanup failures must not prevent remaining cleanup operations from running.
- Never assume closing the GUI automatically turns hardware off.
- Validate amplitude, field, current, voltage, frequency, slew rate, and
  geometry-specific limits before enabling output.

If safe shutdown requires a controlled ramp rather than an immediate zero, the
instrument driver or existing instrument emulator owns that implementation.

## 7. DataFrame and Units Contract

- `self.data` MUST be a `pandas.DataFrame` for captured tabular data.
- Columns MUST have stable, descriptive names.
- Existing analysis-compatible names such as `time (s)` may be retained.
  New structured measurements may use separate unit metadata with concise names
  such as `time_s`, but must remain consistent within that measurement family.
- Never label commanded values as measured values. Store both when feedback is
  available, for example `field_command` and `field_measured`.
- Keep raw detector inputs when producing normalized or processed signals.
- Synchronized channels MUST have the same row count and time basis.
- Do not place arrays or nested DataFrames inside individual DataFrame cells.

For streaming measurements, distinguish:

- full acquired data used for saving;
- a bounded raw display window;
- derived views such as a last cycle or cycle average.

## 8. Instrument Identification and Metadata

Call each instrument's `idn()` when available and store the identities
separately.

Metadata SHOULD include calibration identifiers or versions, geometry/output
mappings, requested and actual sample rates, requested and actual frequencies,
and whether a plotted axis uses measured feedback or a command fallback.

Do not store secrets, full connection objects, or non-serializable callables in
metadata.

## 9. GUI Conventions

Every new Tk measurement GUI MUST:

- inherit from `MeasurementApp`;
- call `super().__init__` with a descriptive title and suitable window size;
- place addresses and persistent setup choices in `self.static_frame`;
- place per-run parameters in `self.dynamic_frame`;
- place display choices and safe manual controls in
  `self.plot_config_frame`;
- use `ttk` widgets and existing styles rather than defining an unrelated
  theme;
- instantiate a measurement class and call `run_experiment()`;
- provide the exact `VIRTUAL` option when virtual operation exists;
- keep `if __name__ == "__main__"` startup code at the bottom of the file.

Long-running measurements MUST run outside the Tk event thread. Transfer live
data to the UI thread with a bounded `queue.Queue`, and use `root.after()` to
poll it. Only the Tk thread may modify widgets or draw the Matplotlib canvas.
Do not use partially written CSV files as the primary live-data transport.

Stop buttons SHOULD request cooperative cancellation. Safety-critical zero/off
controls SHOULD remain directly available and window close handling MUST
request stop and safe shutdown.

## 10. Virtual Operation

Every new workflow SHOULD have a virtual path that exercises the same
measurement class and GUI controls as physical hardware.

- Simulate instrument behavior behind the same interface used by hardware.
- Virtual behavior belongs in virtual instrument drivers and shared simulation
  models, never in a separate virtual measurement class.
- Keep experiment-specific physics and calibration in separate simulation models
  and setup configuration, not hard-coded into general-purpose virtual drivers.
- Simulated data SHOULD resemble the shape and columns of real acquisition.
- Make noise optional or seedable so tests are deterministic.
- Virtual timing MAY be disabled in tests but SHOULD approximate real-time
  streaming in the GUI.
- Do not place `if virtual` branches throughout numerical processing.
- The GUI selects virtual instrument drivers in the same places it selects
  physical drivers, then instantiates the ordinary measurement class.

## 11. Tests

New measurements MUST include automated tests covering, as applicable:

- constructor validation and initial `data`/`filename` state;
- instrument configuration order;
- expected data columns and row counts;
- metadata values and instrument identities;
- standard CSV write/read round trip;
- cancellation and finite completion;
- cleanup and safe-state behavior when acquisition raises;
- virtual execution;
- processing across arbitrary stream chunk boundaries;
- importability of the GUI module without starting `mainloop()`.

Use fake instruments for precise call-order assertions and virtual instruments
for end-to-end behavior. Hardware-connected tests must be opt-in and clearly
marked.

## 12. Repository Structure

Use the following layout:

```text
piec/
  src/piec/measurement/
    your_measurement.py
  src/piec/analysis/
    your_analysis.py          # when reusable analysis is needed
  tests/
    test_your_measurement.py
  Measurements/
    YOUR_MEASUREMENT/
      YOUR_MEASUREMENT_GUI.py
      your_measurement.md
  docs/source/measurements/
    your_measurement.md
```

Export stable public classes from `piec.measurement` when a package-level import
is useful. Add the documentation page to the Measurements toctree in
`docs/source/index.rst`.

## 13. Minimal Standalone Template

```python
import time
import pandas as pd

from piec.analysis.utilities import (
    create_measurement_filename,
    metadata_and_data_to_csv,
)


class ExampleMeasurement:
    mtype = "example"

    def __init__(self, instrument, parameter, save_dir=r"\\scratch"):
        self.instrument = instrument
        self.parameter = parameter
        self.save_dir = save_dir
        self.data = None
        self.filename = None
        self.history = []
        self.abort_requested = False
        self._update_metadata()

    def _update_metadata(self):
        self.metadata = pd.DataFrame({
            "mtype": [self.mtype],
            "parameter": [self.parameter],
            "instrument": [self.instrument.idn()],
            "timestamp": [time.time()],
            "processed": [self.processed],
        })

    def configure_instrument(self):
        pass

    def capture_data(self):
        self.data = pd.DataFrame()

    def analyze(self):
        if self.data is not None:
            self.processed = True
            self.metadata.loc[0, "processed"] = self.processed

    def save_data(self):
        self._update_metadata()
        self.filename = create_measurement_filename(
            self.save_dir, self.mtype
        )
        metadata_and_data_to_csv(self.metadata, self.data, self.filename)

    def run_experiment(self):
        self.configure_instrument()
        try:
            self.capture_data()
        finally:
            self.instrument.output(on=False)
        self.analyze()
        self.save_data()
        self.history.append(self.metadata.copy())
```

## 14. Review Checklist

Before submitting a measurement, verify:

- [ ] The class runs without its GUI.
- [ ] Instruments are injected rather than hard-coded.
- [ ] Constructor parameters and units are documented.
- [ ] `data`, `metadata`, `filename`, and `mtype` exist.
- [ ] `run_experiment()` exposes the complete workflow.
- [ ] Outputs enter a safe state in `finally`.
- [ ] Raw and measured values are not mislabeled.
- [ ] The standard CSV can be read back successfully.
- [ ] The GUI inherits `MeasurementApp` and uses the shared styles.
- [ ] Live GUI updates occur only on the UI thread.
- [ ] A virtual or fake-instrument path is tested.
- [ ] The full test suite passes.
- [ ] The measurement documentation is in the toctree.
