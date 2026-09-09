"""
Measurement setup adapters standardizing instrument access across experimental procedures.
"""

from .waveform_reader import WaveformReader, WaveformRecord

__all__ = ["WaveformReader", "WaveformRecord"]
