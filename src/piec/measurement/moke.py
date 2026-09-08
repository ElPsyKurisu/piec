"""Point-by-point MOKE using a calibrated source and a voltage-reading DMM."""

from dataclasses import dataclass
import json
import threading
import time

import numpy as np
import pandas as pd

from piec.analysis.field_calibration import FieldCalibration
from piec.analysis.utilities import create_measurement_filename, metadata_and_data_to_csv


@dataclass(frozen=True)
class MokeSnapshot:
    raw: pd.DataFrame
    last_cycle: pd.DataFrame
    cycle_average: pd.DataFrame
    completed_cycles: int
    field_column: str = ""


class MokeMeasurement:
    """Apply direct source settings and record raw detector voltage.

    Follows the standalone ``IVSweep`` lifecycle, not ``DiscreteWaveform``.
    ``output_values`` is one complete ordered cycle in the calibration's V or A
    units. The calibration includes everything downstream of the sourcemeter;
    no amplifier gain, gaussmeter, AWG, or oscilloscope is assumed.

    Optional ``field_reader()`` returns one measured field value at each settled
    setpoint. ``field_reader_unit`` must explicitly match the calibration field
    unit. It selects measured field for plotting but never adjusts the source
    or rewrites calibration. The setup owns gaussmeter configuration and any
    conversion from its analog voltage output. ``field_reader_name`` identifies
    that readout in saved metadata.

    ``compliance`` is amperes when sourcing volts, or volts when sourcing amps.
    ``max_output_step`` bounds each programmed ramp increment in source units;
    ``ramp_delay`` and ``dwell_time`` are seconds. These software ramps are not
    hardware-timed. The default cleanup ramps the command to electrical zero
    and disables the output. Supply ``safe_shutdown(source)`` instead when the
    magnet setup requires a different shutdown/discharge procedure. Zero
    electrical output does not imply zero field or a demagnetized sample.

    ``source_channel=None`` uses the driver's default channel. ``geometry`` is
    a metadata label: the caller supplies the appropriate source/calibration.
    Instruments must be idle and exclusively owned by this measurement.
    """

    mtype = "moke"

    def __init__(
        self, sourcemeter, dmm, calibration, output_values, *,
        compliance, max_output_step, dwell_time=0.1, ramp_delay=0.01,
        n_cycles=1, average_cycles=10, raw_window_points=1000,
        source_channel=None, geometry="unspecified", safe_shutdown=None,
        field_reader=None, field_reader_unit=None, field_reader_name="",
        save_dir=r"\\scratch",
    ):
        if not isinstance(calibration, FieldCalibration):
            raise TypeError("calibration must be a FieldCalibration")
        outputs = np.asarray(output_values, dtype=float)
        if outputs.ndim != 1 or len(outputs) < 3 or not np.isfinite(outputs).all():
            raise ValueError("output_values must contain at least three finite settings")
        if outputs[0] != outputs[-1] or np.ptp(outputs) == 0:
            raise ValueError("output_values must describe a nonconstant, closed cycle")
        calibration.field_at_output(outputs)  # Validate before touching hardware.
        for name, value in (("compliance", compliance), ("max_output_step", max_output_step)):
            if not np.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be positive and finite")
        for name, value in (("dwell_time", dwell_time), ("ramp_delay", ramp_delay)):
            if not np.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be nonnegative and finite")
        for name, value in (
            ("n_cycles", n_cycles), ("average_cycles", average_cycles),
            ("raw_window_points", raw_window_points),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if safe_shutdown is not None and not callable(safe_shutdown):
            raise TypeError("safe_shutdown must be callable")
        if field_reader is not None:
            if not callable(field_reader):
                raise TypeError("field_reader must be a callable returning magnetic field")
            if field_reader_unit != calibration.field_unit:
                raise ValueError("field_reader_unit must explicitly match calibration.field_unit")
        elif field_reader_unit is not None or field_reader_name:
            raise ValueError("field reader units/name require a field_reader")
        self.sourcemeter = sourcemeter
        self.dmm = dmm
        self.field_reader = field_reader
        self.field_reader_unit = field_reader_unit
        self.field_reader_name = str(field_reader_name or "external field reader") if field_reader is not None else ""
        # Snapshot the supplied table: editing another table cannot alter a run.
        self.calibration = FieldCalibration(**calibration.to_dict())
        self.output_values = outputs.copy()
        self.compliance = float(compliance)
        self.max_output_step = float(max_output_step)
        self.dwell_time = float(dwell_time)
        self.ramp_delay = float(ramp_delay)
        self.n_cycles = int(n_cycles)
        self.average_cycles = int(average_cycles)
        self.raw_window_points = int(raw_window_points)
        self.source_channel = source_channel
        self.geometry = str(geometry)
        self.safe_shutdown = safe_shutdown
        self.save_dir = save_dir
        self.history = []
        self.abort_requested = False
        self._stop = threading.Event()
        self._configured = False
        self._last_output = 0.0
        self._reset_data()
        self.data = None
        self._validate_source_limits(np.r_[outputs, 0.0])
        limit_name = "current_compliance" if calibration.output_unit == "V" else "voltage_compliance"
        limit_bounds = getattr(sourcemeter, limit_name, (None, None))
        if limit_bounds[1] is not None and self.compliance > limit_bounds[1]:
            raise ValueError(f"compliance exceeds the driver's {limit_name} limit")
        self._update_metadata()

    @property
    def output_column(self):
        return "source_output"

    @property
    def field_column(self):
        """Selected field axis for raw, last-cycle, and averaged plots."""
        return self.measured_field_column if self.field_reader is not None else self.calibrated_field_column

    @property
    def calibrated_field_column(self):
        return "field_calibrated"

    @property
    def measured_field_column(self):
        return "field_measured"

    @property
    def column_units(self):
        units = {
            "time": "s",
            "cycle": None,
            "point": None,
            "direction": None,
            "source_output": self.calibration.output_unit,
            "field_calibrated": self.calibration.field_unit,
            "detector_voltage": "V",
        }
        if self.field_reader is not None:
            units["field_measured"] = self.calibration.field_unit
            units["field_time"] = "s"
        return units

    @property
    def column_units_json(self):
        return json.dumps(self.column_units, sort_keys=True, separators=(",", ":"))

    def _reset_data(self):
        self.data = pd.DataFrame()
        self.raw_data = pd.DataFrame()
        self.last_cycle = pd.DataFrame()
        self.cycle_average = pd.DataFrame()
        self.completed_cycles = 0
        self.processed = False
        self.filename = None
        self._cycles = []
        self._timestamp = time.time()

    def _update_metadata(self):
        self.metadata = pd.DataFrame([{
            "measurement_schema": "moke",
            "measurement_schema_version": 1,
            "column_units_json": self.column_units_json,
            "mtype": self.mtype, "geometry": self.geometry,
            "sourcemeter": self.sourcemeter.idn(), "dmm": self.dmm.idn(),
            "source_channel": self.source_channel,
            "calibration": json.dumps(self.calibration.to_dict()),
            "output_values": json.dumps(self.output_values.tolist()),
            "output_unit": self.calibration.output_unit,
            "field_unit": self.calibration.field_unit,
            "field_basis": "measured field" if self.field_reader is not None else "calibrated source command; not a field measurement",
            "plot_field_column": self.field_column,
            "field_reader": self.field_reader_name,
            "field_reader_unit": self.field_reader_unit,
            "field_acquisition": "sequential after detector read" if self.field_reader is not None else "none",
            "compliance": self.compliance,
            "compliance_unit": "A" if self.calibration.output_unit == "V" else "V",
            "max_output_step": self.max_output_step,
            "dwell_time": self.dwell_time, "ramp_delay": self.ramp_delay,
            "n_cycles": self.n_cycles, "completed_cycles": self.completed_cycles,
            "average_cycles": self.average_cycles, "raw_window_points": self.raw_window_points,
            "timestamp": self._timestamp, "processed": self.processed,
            "aborted": self.abort_requested,
            "shutdown_policy": "custom" if self.safe_shutdown else "ramp to electrical zero, output off",
        }])

    def _source_call(self, method, **kwargs):
        if self.source_channel is not None:
            kwargs["channel"] = self.source_channel
        return getattr(self.sourcemeter, method)(**kwargs)

    def _validate_source_limits(self, outputs):
        name = "voltage" if self.calibration.output_unit == "V" else "current"
        bounds = getattr(self.sourcemeter, name, (None, None))
        if bounds[0] is not None and np.any(np.asarray(outputs) < bounds[0]):
            raise ValueError(f"source output is below the driver's {name} limit")
        if bounds[1] is not None and np.any(np.asarray(outputs) > bounds[1]):
            raise ValueError(f"source output exceeds the driver's {name} limit")

    def configure_sourcemeter(self):
        """Prepare electrical zero and compliance with output disabled."""
        self._configured = False
        self._source_call("output", on=False)
        if self.calibration.output_unit == "V":
            self._source_call("configure_voltage_source", voltage=0.0, current_compliance=self.compliance)
        else:
            self._source_call("configure_current_source", current=0.0, voltage_compliance=self.compliance)
        self._last_output = 0.0
        self._configured = True

    def configure_dmm(self):
        """Select DC voltage sensing without enabling any detector stimulus."""
        self.dmm.set_sense_function(sense_func="VOLT")
        self.dmm.set_measurement_coupling(coupling="DC")

    def configure_instruments(self):
        self.configure_sourcemeter()
        self.configure_dmm()

    def _ramp_output(self, target, interruptible=True):
        count = max(1, int(np.ceil(abs(target - self._last_output) / self.max_output_step)))
        for value in np.linspace(self._last_output, target, count + 1)[1:]:
            if interruptible and self._stop.is_set():
                return False
            if self.calibration.output_unit == "V":
                self._source_call("set_source_voltage", voltage=float(value))
            else:
                self._source_call("set_source_current", current=float(value))
            self._last_output = float(value)
            if interruptible:
                if self._stop.wait(self.ramp_delay):
                    return False
            else:
                time.sleep(self.ramp_delay)
        return True

    def set_output(self, output):
        """Program a direct source setting; does not enable the output."""
        if not self._configured:
            raise RuntimeError("configure the sourcemeter before setting output")
        if not np.isscalar(output):
            raise ValueError("output must be a scalar")
        self.calibration.field_at_output(output)
        self._validate_source_limits([output])
        return self._ramp_output(float(output))

    def set_field(self, field):
        """Program the calibrated source setting for a requested field."""
        return self.set_output(self.calibration.output_at_field(field))

    def request_stop(self):
        self.abort_requested = True
        self._stop.set()

    def shut_off(self):
        """Apply the setup's shutdown policy, even after an acquisition error."""
        try:
            if self.safe_shutdown is not None:
                self.safe_shutdown(self.sourcemeter)
            else:
                try:
                    if self._configured:
                        self._ramp_output(0.0, interruptible=False)
                finally:
                    self._source_call("output", on=False)
        finally:
            self._configured = False

    def snapshot(self):
        return MokeSnapshot(
            self.raw_data.copy(), self.last_cycle.copy(),
            self.cycle_average.copy(), self.completed_cycles, self.field_column,
        )

    def _read_measured_field(self):
        value = self.field_reader()
        if isinstance(value, (bool, np.bool_)) or not np.isscalar(value):
            raise ValueError("field_reader must return a finite scalar field value")
        try:
            value = float(value)
        except (ValueError, TypeError) as error:
            raise ValueError("field_reader must return a finite scalar field value") from error
        if not np.isfinite(value):
            raise ValueError("field_reader returned a non-finite field value")
        return value

    def capture_data(self, on_update=None):
        """Acquire repeated cycles; update raw data after every DMM reading."""
        if not self._configured:
            raise RuntimeError("configure instruments before capture_data")
        self._reset_data()
        rows = []
        started = time.monotonic()
        fields = self.calibration.field_at_output(self.output_values)
        directions = np.sign(np.r_[fields[1] - fields[0], np.diff(fields)])
        try:
            if not self._stop.is_set():
                self._source_call("output", on=True)
            for cycle in range(self.n_cycles):
                for point, output in enumerate(self.output_values):
                    if self.abort_requested or self._stop.is_set():
                        return self.data
                    if not self.set_output(output) or self._stop.wait(self.dwell_time):
                        return self.data
                    voltage = float(self.dmm.get_voltage())
                    if not np.isfinite(voltage):
                        raise ValueError("DMM returned a non-finite detector voltage")
                    row = {
                        "time": time.monotonic() - started,
                        "cycle": cycle, "point": point, "direction": directions[point],
                        self.output_column: output, self.calibrated_field_column: fields[point],
                        "detector_voltage": voltage,
                    }
                    if self.field_reader is not None:
                        row[self.measured_field_column] = self._read_measured_field()
                        row["field_time"] = time.monotonic() - started
                    rows.append(row)
                    self.data = pd.DataFrame(rows)
                    self.raw_data = self.data.tail(self.raw_window_points).copy()
                    if point == len(self.output_values) - 1:
                        self.last_cycle = self.data.tail(len(self.output_values)).copy()
                        self.completed_cycles += 1
                        self._cycles.append(self.last_cycle)
                        self._cycles = self._cycles[-self.average_cycles:]
                        self.cycle_average = self.last_cycle[
                            ["point", "direction", self.output_column, self.calibrated_field_column]
                        ].reset_index(drop=True)
                        average_columns = ["detector_voltage"]
                        if self.field_reader is not None:
                            average_columns.append(self.measured_field_column)
                        for column in average_columns:
                            self.cycle_average[column] = np.mean(
                                [frame[column].to_numpy() for frame in self._cycles], axis=0
                            )
                        self.cycle_average["cycles_averaged"] = len(self._cycles)
                    if on_update is not None:
                        on_update(self.snapshot())
        finally:
            self.shut_off()
        return self.data

    def analyze(self):
        """Retain raw detector volts; cycle averages are computed during capture."""
        self.processed = self.data is not None and not self.data.empty
        self._update_metadata()

    def save_data(self):
        if self.data is None or self.data.empty:
            raise RuntimeError("no MOKE data to save")
        self._update_metadata()
        self.filename = create_measurement_filename(self.save_dir, self.mtype)
        metadata_and_data_to_csv(self.metadata, self.data, self.filename)
        return self.filename

    def run_experiment(self, on_update=None, save=True):
        """Configure, acquire, shut down, organize, save, and record history."""
        self.abort_requested = False
        self._stop.clear()
        self._reset_data()
        print("Running calibrated source/DMM MOKE measurement...")
        try:
            self.configure_instruments()
        except BaseException:
            self.shut_off()
            raise
        self.capture_data(on_update=on_update)
        self.analyze()
        if save and not self.data.empty:
            self.save_data()
        self._update_history()
        print(f"MOKE acquisition ended: {self.completed_cycles} complete cycle(s).")
        return self.data

    def _update_history(self):
        self.history.append(self.metadata.copy())
