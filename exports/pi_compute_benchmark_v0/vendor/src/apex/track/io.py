"""CSV centerlines in metres; no vehicle parameters or implicit track widths."""

import csv
from pathlib import Path

from apex.track.centerline import PeriodicCenterline
from apex.track.closed_track import ClosedTrack


def load_centerline_csv(path: str | Path) -> PeriodicCenterline:
    """Read x,y columns; extra named metadata columns are ignored."""
    points = []
    with Path(path).open(newline="", encoding="utf-8-sig") as stream:
        reader = csv.DictReader(stream)
        headers = reader.fieldnames
        if headers is None or len(set(headers)) != len(headers) or not {"x", "y"}.issubset(headers):
            raise ValueError("CSV requires unique column names including x,y")
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Malformed CSV row {line}")
            try:
                points.append([float(row["x"]), float(row["y"])])
            except (ValueError, TypeError) as error:
                raise ValueError(f"Invalid x,y data at CSV row {line}") from error
    return PeriodicCenterline(points)


def load_track_csv(path: str | Path, *, left_width: float, right_width: float) -> ClosedTrack:
    """Load a track with explicitly supplied independent constant half-widths."""
    return ClosedTrack(load_centerline_csv(path), left_width=left_width, right_width=right_width)
