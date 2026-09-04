"""Calibration from a source's direct electrical output to magnetic field."""

import numpy as np
import pandas as pd


class FieldCalibration:
    """Piecewise-linear lookup of measured ``(source_output, field)`` pairs.

    ``output_unit`` is ``V`` or ``A`` at the sourcemeter terminals, not a
    downstream amplifier output. Amplifier gain is already included in the
    measured pairs. Field units are explicit and are never converted silently.
    Extrapolation is deliberately unsupported.
    """

    def __init__(self, points, output_unit="V", field_unit="Oe", name=""):
        values = np.asarray(points, dtype=float)
        if values.ndim != 2 or values.shape[1] != 2 or len(values) < 2:
            raise ValueError("provide at least two (source_output, field) pairs")
        if not np.isfinite(values).all():
            raise ValueError("calibration points must be finite")
        if output_unit not in ("V", "A"):
            raise ValueError("output_unit must be V or A")
        if not isinstance(field_unit, str) or not field_unit.strip():
            raise ValueError("field_unit must be a non-empty unit label")
        values = values[np.argsort(values[:, 0])].copy()
        if np.any(np.diff(values[:, 0]) <= 0):
            raise ValueError("each source output must have exactly one field value")
        self._points = values
        self.output_unit = output_unit
        self.field_unit = field_unit
        self.name = str(name)

    @property
    def points(self):
        """A copy of the original calibration pairs, sorted by source output."""
        return self._points.copy()

    @property
    def output_range(self):
        return tuple(self._points[[0, -1], 0])

    def field_at_output(self, output):
        """Estimate field from the direct source setting (scalar or array)."""
        return self._interpolate(output, self._points[:, 0], self._points[:, 1])

    def output_at_field(self, field):
        """Find a source setting; reject a non-unique inverse calibration."""
        delta = np.diff(self._points[:, 1])
        if not (np.all(delta > 0) or np.all(delta < 0)):
            raise ValueError("field must be strictly monotonic to invert calibration")
        points = self._points if delta[0] > 0 else self._points[::-1]
        return self._interpolate(field, points[:, 1], points[:, 0])

    @staticmethod
    def _interpolate(values, x, y):
        values = np.asarray(values, dtype=float)
        if not np.isfinite(values).all():
            raise ValueError("requested values must be finite")
        if np.any(values < x[0]) or np.any(values > x[-1]):
            raise ValueError("requested value is outside the calibrated range")
        result = np.interp(values, x, y)
        return float(result) if values.ndim == 0 else result

    def to_dict(self):
        """Serializable calibration, including units and the original pairs."""
        return {
            "points": self._points.tolist(),
            "output_unit": self.output_unit,
            "field_unit": self.field_unit,
            "name": self.name,
        }

    def save_csv(self, path, overwrite=False):
        """Save a portable calibration table; existing files are protected."""
        frame = pd.DataFrame(self._points, columns=["source_output", "field"])
        frame["output_unit"] = self.output_unit
        frame["field_unit"] = self.field_unit
        frame["name"] = self.name
        frame.to_csv(path, index=False, mode="w" if overwrite else "x")

    @classmethod
    def load_csv(cls, path):
        """Load a table written by ``save_csv`` or assembled manually."""
        frame = pd.read_csv(path, keep_default_na=False)
        required = {"source_output", "field", "output_unit", "field_unit"}
        if not required.issubset(frame.columns):
            raise ValueError(f"calibration CSV requires columns {sorted(required)}")
        if "name" not in frame:
            frame["name"] = ""
        for column in ("output_unit", "field_unit", "name"):
            if frame[column].nunique(dropna=False) != 1:
                raise ValueError(f"calibration CSV must have one consistent {column}")
        return cls(
            frame[["source_output", "field"]].to_numpy(),
            output_unit=frame["output_unit"].iloc[0],
            field_unit=frame["field_unit"].iloc[0],
            name=frame["name"].iloc[0],
        )
