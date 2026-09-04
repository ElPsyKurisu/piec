# MOKE Measurement

This folder contains the runnable interface for the general, point-by-point
magneto-optical Kerr effect measurement in `piec.measurement.moke`.

The measurement assumes only:

- a sourcemeter whose direct voltage or current command controls the magnet
  power stage;
- a DMM that reads the photodetector voltage;
- a calibration CSV mapping direct source output to magnetic field.

An optional second DMM can read a gaussmeter's analog voltage output. The GUI
converts that voltage to field with a user-supplied scale and offset and then
plots the measured field. It does not perform closed-loop field control.

## Files

- `MOKE_GUI.py` is the normal graphical interface.
- `MOKE_testing.ipynb` walks through virtual and physical setup.
- `example_calibration.csv` is illustrative only and must not be used as a
  hardware calibration.

## Virtual test

From the repository environment, run:

```powershell
python Measurements/MOKE/MOKE_GUI.py
```

Keep both the sourcemeter and detector DMM set to `VIRTUAL`, leave the field
reader as `NONE`, and use the included example calibration. Click **Run
Measurement**. The graph displays the live raw samples, most recent complete
cycle, and average of completed cycles.

Virtual mode uses the ordinary `MokeMeasurement`, `VirtualSourcemeter`, and
`VirtualDMM`. The GUI wires their source and detector signals through the
separate `HystereticMagneticMaterial` model. There is no virtual MOKE
measurement class.

## Hardware setup

1. Create a calibration CSV with columns
   `source_output,field,output_unit,field_unit,name`.
2. Select the sourcemeter that drives the amplifier or power supply.
3. Select the detector DMM connected to the optical detector output.
4. Select the geometry and the matching calibration file.
5. Enter a source-output minimum and maximum that lie inside that calibration.
6. Enter compliance, maximum ramp step, ramp delay, and dwell time appropriate
   for the real magnet setup.
7. Select a save directory and run the measurement.

The geometry selection is saved as metadata. It does not silently reroute
hardware; choose the appropriate source channel, wiring, and calibration for
the selected geometry.

If a field-reader DMM is selected, enter the gaussmeter conversion as:

```text
field = DMM voltage * field per reader volt + field-reader offset
```

The resulting field units must be the same units declared by the source-field
calibration.

## Safety and controls

The measurement ramps between commands in increments no larger than the
configured maximum output step. Normal completion, cancellation, and errors
all request a ramp to electrical zero followed by source output-off. **Stop and
Zero** requests cooperative cancellation; closing the window during a run
waits for that shutdown path before closing.

Electrical zero is not a degaussing procedure and does not necessarily mean
zero magnetic field. The general GUI cannot infer discharge requirements for a
particular amplifier or electromagnet. Validate the complete setup at low
output and use a setup-specific shutdown callback when zero/off is insufficient.

The full measurement and calibration reference is also available in
`docs/source/measurements/moke.md`.
