import numpy as np
import pytest

from apex.track.io import load_centerline_csv, load_track_csv
from apex.track.synthetic import circle_waypoints


@pytest.mark.parametrize("duplicate", [False, True])
def test_csv_loader(tmp_path, duplicate):
    points = circle_waypoints(5, count=16)
    if duplicate:
        points = np.vstack([points, points[0]])
    path = tmp_path / "track.csv"
    path.write_text("x,y,label\n" + "\n".join(f"{x},{y},test" for x, y in points))
    track = load_track_csv(path, left_width=0.4, right_width=0.8)
    assert len(track.centerline.waypoints) == 16
    assert track.sample(0).x == pytest.approx(5)
    assert track.left_width(0) == 0.4
    assert track.right_width(0) == 0.8


@pytest.mark.parametrize(
    "contents",
    [
        "",
        "a,b\n1,2",
        "x,x,y\n1,2,3",
        "x,y\n0,0\n1,0\n0,1",
        "x,y\n0,0\n1,0\n2,0\n3,0",
        "x,y\n0,0\n1,0\n1,1\nnan,1",
        "x,y\n0,0\n1,0\n1,1\n0,inf",
        "x,y\n0,0\n1,0\n1,1\nbad,1",
        "x,y\n0,0\n1,0\n1,1\n0",
        "x,y\n0,0\n1,0\n1,1\n0,1,extra",
        "x,y\n0,0\n1,0\n1,0\n0,1",
    ],
)
def test_invalid_csv(tmp_path, contents):
    path = tmp_path / "bad.csv"
    path.write_text(contents)
    with pytest.raises(ValueError):
        load_centerline_csv(path)
