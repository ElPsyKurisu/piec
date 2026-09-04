"""A small stateful magnetic material model, independent of instruments."""

import numpy as np


class HystereticMagneticMaterial:
    """Qualitative hysteresis using an ensemble of symmetric switching domains.

    Each domain switches up at its positive threshold and down at its negative
    threshold, retaining its state between them. This produces major loops,
    remanence, and history-dependent partial reversals. It is a demonstration
    model, not a quantitative micromagnetic or magnet power-supply model.

    All field parameters must use the same units as the supplied field.
    Magnetization is normalized to [-1, 1]. Optical gain and voltage offset
    belong to the simulated detector/setup, not this material.
    """

    def __init__(self, coercive_field=50.0, switching_width=10.0, domains=201):
        if not np.isfinite(coercive_field) or coercive_field <= 0:
            raise ValueError("coercive_field must be positive and finite")
        if not np.isfinite(switching_width) or not 0 <= switching_width < coercive_field:
            raise ValueError("switching_width must be nonnegative and below coercive_field")
        if isinstance(domains, bool) or not isinstance(domains, (int, np.integer)) or domains < 1:
            raise ValueError("domains must be a positive integer")
        self._thresholds = np.linspace(
            coercive_field - switching_width, coercive_field + switching_width, domains
        ) if domains > 1 else np.array([coercive_field])
        self.reset()

    def reset(self, polarity=-1):
        """Start at zero field with all domains in the chosen magnetic state."""
        if polarity not in (-1, 1):
            raise ValueError("polarity must be -1 or 1")
        self._states = np.full(len(self._thresholds), polarity, dtype=float)
        self.current_field = 0.0

    @property
    def magnetization(self):
        return float(np.mean(self._states))

    def apply_field(self, field):
        """Apply one field value and return the resulting magnetization."""
        if not np.isscalar(field) or not np.isfinite(field):
            raise ValueError("field must be a finite scalar")
        self.current_field = float(field)
        self._states[field >= self._thresholds] = 1.0
        self._states[field <= -self._thresholds] = -1.0
        return self.magnetization

    def response(self, fields):
        """Apply an ordered field history, preserving state between calls."""
        fields = np.asarray(fields, dtype=float)
        if fields.ndim != 1 or not np.isfinite(fields).all():
            raise ValueError("fields must be a finite one-dimensional sequence")
        return np.array([self.apply_field(field) for field in fields])
