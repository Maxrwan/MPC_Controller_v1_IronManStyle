"""Load deterministic track geometry independently of reference generation."""

import hashlib
import json
from pathlib import Path

from apex.track import ClosedTrack


def load_track(path):
    path = Path(path)
    data = json.loads(path.read_text())
    track = ClosedTrack.from_waypoints(
        data["control_points_m"], left_width=data["left_width_m"], right_width=data["right_width_m"]
    )
    return track, data, hashlib.sha256(path.read_bytes()).hexdigest()
