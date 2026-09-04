# Measurement Waveforms

This directory contains classes for managing discrete waveform generation, measurement coordination, and data capture. It abstracts the complexity of synchronizing Arbitrary Waveform Generators (AWG), Oscilloscopes, Lock-in Amplifiers, and other instruments into reusable experiments.

See [`MEASUREMENT_DEVELOPER_GUIDE.md`](MEASUREMENT_DEVELOPER_GUIDE.md) for the required lifecycle, metadata, safety, GUI, virtual-operation, and testing conventions for new measurements.

## Directory Structure

- **`discrete_waveform.py`**: Contains the `DiscreteWaveform` base class and specific implementations:
    -   `HysteresisLoop`: For ferroelectric hysteresis measurements using triangular waveforms.
    -   `ThreePulsePund`: For PUND (Positive-Up-Negative-Down) switching measurements.
- **`magneto_transport.py`**: Contains `MagnetoTransport` and `AMR` (Anisotropic Magnetoresistance) classes for controlling magnets, stepper motors, and lock-in amplifiers.
- **`amr.py`**: Provides the dedicated public import path for the AMR classes.
- **`moke.py`**: A standalone, point-by-point sourcemeter/DMM MOKE measurement
  with an injected direct-output field calibration and live cycle data.

## Usage

### Hysteresis Measurement

Use `HysteresisLoop` to coordinate an AWG and Oscilloscope for capturing PE loops.

```python
from piec.measurement.discrete_waveform import HysteresisLoop
from piec.drivers.oscilloscope.k_dsox3024a import KeysightDSOX3024a
from piec.drivers.awg.k_33500B import Keysight33500B

# Initialize instruments (drivers usually defined in piec.drivers)
scope = KeysightDSOX3024a('USB0::...')
awg = Keysight33500B('USB0::...')

# Create experiment
experiment = HysteresisLoop(
    awg=awg, 
    osc=scope, 
    frequency=1000, 
    amplitude=5.0, 
    save_dir=r'C:\Data'
)

# Run the full sequence: configure -> capture -> save -> analyze
experiment.run_experiment()
```

### Magneto-Transport (AMR)

Use `AMR` to control field and angle for magnetoresistance measurements.

```python
from piec.measurement.magneto_transport import AMR

# Initialize required instruments...
# experiment = AMR(dmm=dmm, calibrator=calib, arduino=stepper, lockin=lockin, field=1000)
# experiment.run_experiment()
```

## Creating New Experiments

Follow [`MEASUREMENT_DEVELOPER_GUIDE.md`](MEASUREMENT_DEVELOPER_GUIDE.md). Inherit from `DiscreteWaveform` only when its AWG/oscilloscope workflow actually fits the new experiment.
