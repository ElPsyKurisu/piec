"""Tests for the runnable MOKE GUI helpers and notebook."""

import importlib.util
import json
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pandas as pd

from piec.analysis.field_calibration import FieldCalibration
from piec.drivers.dmm.virtual_dmm import VirtualDMM
from piec.drivers.sourcemeter.virtual_sourcemeter import VirtualSourcemeter
from piec.measurement.moke import MokeMeasurement, MokeSnapshot


ROOT = Path(__file__).resolve().parents[1]
GUI_PATH = ROOT / "Measurements" / "MOKE" / "MOKE_GUI.py"
NOTEBOOK_PATH = ROOT / "Measurements" / "MOKE" / "MOKE_testing.ipynb"


def _load_gui_module():
    spec = importlib.util.spec_from_file_location("piec_moke_gui", GUI_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_moke_gui_imports_without_starting_tk_mainloop():
    module = _load_gui_module()
    assert module.MokeMeasurementApp.__name__ == "MokeMeasurementApp"


def test_moke_gui_output_cycle_is_closed_and_has_requested_size():
    cycle = _load_gui_module().make_output_cycle(-2, 3, 21)
    assert len(cycle) == 21
    assert cycle[0] == cycle[-1] == -2
    assert cycle.max() == 3


def test_gui_virtual_setup_runs_the_normal_measurement_and_generates_a_loop():
    module = _load_gui_module()
    calibration = FieldCalibration([(-5, -500), (0, 0), (5, 500)])
    source = VirtualSourcemeter("VIRTUAL")
    detector = VirtualDMM("VIRTUAL")
    module.connect_virtual_detector(
        source, detector, calibration, noise=0.0, seed=0
    )
    outputs = module.make_output_cycle(-5, 5, 41)
    measurement = MokeMeasurement(
        sourcemeter=source,
        dmm=detector,
        calibration=calibration,
        output_values=outputs,
        compliance=0.01,
        max_output_step=1.0,
        dwell_time=0.0,
        ramp_delay=0.0,
        n_cycles=2,
        average_cycles=2,
    )

    data = measurement.run_experiment(save=False)

    assert measurement.completed_cycles == 2
    assert len(data) == 2 * len(outputs)
    assert np.ptp(data["detector_voltage"]) > 0.03
    assert source.state["output_on"] is False


def test_moke_gui_plot_snapshot_labels_combine_plain_name_and_unit():
    module = _load_gui_module()
    mock_app = Mock()
    mock_app.show_raw.get.return_value = True
    mock_app.show_last.get.return_value = True
    mock_app.show_average.get.return_value = True
    mock_app.geometry_entry.get.return_value = "in-plane"
    mock_app.ax.lines = []

    calibration = FieldCalibration([(-5, -500), (0, 0), (5, 500)], field_unit="Oe")
    source = VirtualSourcemeter("VIRTUAL")
    detector = VirtualDMM("VIRTUAL")
    meas = MokeMeasurement(
        sourcemeter=source, dmm=detector, calibration=calibration,
        output_values=[-5, 0, 5, 0, -5], compliance=0.01, max_output_step=5.0,
        dwell_time=0.0, ramp_delay=0.0,
    )
    mock_app.experiment = meas

    # 1. Calibrated field mode
    snap_cal = MokeSnapshot(
        raw=pd.DataFrame({"field_calibrated": [0.0], "detector_voltage": [0.5]}),
        last_cycle=pd.DataFrame(),
        cycle_average=pd.DataFrame(),
        completed_cycles=0,
        field_column="field_calibrated",
    )
    module.MokeMeasurementApp._plot_snapshot(mock_app, snap_cal)
    mock_app.ax.set_xlabel.assert_called_once_with("field_calibrated (Oe)")
    mock_app.ax.set_ylabel.assert_called_once_with("detector_voltage (V)")

    # 2. Measured field mode
    meas.field_reader = lambda: 50.0
    meas.field_reader_unit = "Oe"
    snap_meas = MokeSnapshot(
        raw=pd.DataFrame({"field_measured": [50.0], "detector_voltage": [0.5]}),
        last_cycle=pd.DataFrame(),
        cycle_average=pd.DataFrame(),
        completed_cycles=0,
        field_column="field_measured",
    )
    mock_app.ax.reset_mock()
    module.MokeMeasurementApp._plot_snapshot(mock_app, snap_meas)
    mock_app.ax.set_xlabel.assert_called_once_with("field_measured (Oe)")
    mock_app.ax.set_ylabel.assert_called_once_with("detector_voltage (V)")


def test_moke_notebook_code_cells_compile():
    notebook = json.loads(NOTEBOOK_PATH.read_text(encoding="utf-8"))
    for index, cell in enumerate(notebook["cells"]):
        if cell.get("cell_type") == "code":
            compile(
                "".join(cell.get("source", [])),
                f"{NOTEBOOK_PATH}:cell-{index}",
                "exec",
            )
