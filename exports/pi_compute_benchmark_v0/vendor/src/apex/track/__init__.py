"""Closed-circuit track geometry, CSV input, and independent race-progress utilities."""

from apex.track.closed_track import ClosedTrack
from apex.track.io import load_track_csv

__all__ = ["ClosedTrack", "load_track_csv"]
