"""Read-only native-sample inspection. Viewer clocks never advance a physical model."""

from dataclasses import dataclass
from itertools import combinations
from math import isfinite

from tools.apex_workbench import engineering_views as views
from tools.apex_workbench import storage

MAX_RUNS = 4  # Presentation/resource bound, not a scientific validity criterion.
TIME_SOURCES = ("states.csv", "controls.csv", "diagnostics.csv", "trajectory_xy.csv")


@dataclass
class Snapshot:
    run: object
    data: views.Inspection
    epoch: tuple

    def current(self):
        if not views.comparison_current({"presentation_epoch": self.epoch}):
            return False
        try:
            for name in self.data.manifest:
                storage.artifact_bytes(self.run.directory, name)
        except (OSError, ValueError, RuntimeError):
            return False
        return views.comparison_current({"presentation_epoch": self.epoch})


def load(run):
    before = views.comparison_epoch((run,))
    data = views.inspect(run)
    if not data.valid:
        raise storage.IntegrityError(data.error or "Evidence unavailable")
    request = data.request
    effective = request["effective"]
    profile = (
        effective.get("grid_id", "original")
        + "/"
        + request.get("execution_context", {}).get("role", "adapter")
    )
    if (
        request.get("run_id", run.run_id) != run.run_id
        or request["adapter"] != run.adapter
        or effective.get("case_id", "") != run.case
        or profile != run.profile
    ):
        raise storage.IntegrityError("Catalog identity/profile changed; refresh before inspection")
    for name in TIME_SOURCES:
        frame = data.frames.get(name)
        if frame is not None and not frame.empty:
            values = tuple(float(t) for t in frame.time)
            if any(not isfinite(t) for t in values) or any(
                b <= a for a, b in zip(values, values[1:])
            ):
                raise storage.IntegrityError("Invalid native timebase: " + name)
    if "states.csv" in data.frames and "trajectory_xy.csv" in data.frames:
        if tuple(data.frames["states.csv"].time) != tuple(data.frames["trajectory_xy.csv"].time):
            raise storage.IntegrityError("Stored XY/state sample timebases differ")
    snapshot = Snapshot(run, data, before)
    if not snapshot.current():
        raise storage.IntegrityError("Evidence changed during snapshot read")
    return snapshot


def supports_replay(snapshot):
    from apex.state import CONTROL_NAMES, CONTROL_UNITS, STATE_NAMES, STATE_UNITS

    data = snapshot.data
    return not (
        data.request.get("record_version") != 2
        or data.contract.get("schema") != "apex-workbench-telemetry/1"
        or data.contract.get("time_unit") != "s"
        or data.contract.get("xy_unit") != "m"
        or data.contract.get("state_names") != list(STATE_NAMES)
        or data.contract.get("state_units") != list(STATE_UNITS)
        or data.contract.get("control_names") != list(CONTROL_NAMES)
        or data.contract.get("control_units") != list(CONTROL_UNITS)
    )


def times(snapshot):
    data = snapshot.data
    if not supports_replay(snapshot):
        raise storage.IntegrityError(
            "Recorded replay profile unsupported; native raw inspection only"
        )
    frame = data.frames.get("states.csv")
    if frame is None or frame.empty:
        raise storage.IntegrityError("State timebase unavailable")
    values = tuple(float(t) for t in frame.time)
    if any(not isfinite(t) for t in values) or any(b <= a for a, b in zip(values, values[1:])):
        raise storage.IntegrityError("State timebase is not finite and strictly increasing")
    return values


def sample(snapshot, source, selected_time):
    """Exact timestamp only. No interpolation, tolerance, previous-row hold or inferred XY."""
    frame = snapshot.data.frames.get(source)
    result = {
        "source": source,
        "selected_time_s": selected_time,
        "available": False,
        "sample_index": None,
        "timestamp_s": None,
        "values": {},
    }
    if frame is None or frame.empty or "time" not in frame:
        return {**result, "meaning": "channel source unavailable"}
    matches = frame.index[frame.time == selected_time].tolist()
    if len(matches) != 1:
        if (
            source == "controls.csv"
            and snapshot.data.request["adapter"] == "dynamic_lab"
            and snapshot.data.summary.get("horizon_reached")
            and selected_time == times(snapshot)[-1]
        ):
            return {**result, "meaning": "terminal state: no applied-control interval"}
        outside = selected_time < frame.time.iloc[0] or selected_time > frame.time.iloc[-1]
        return {
            **result,
            "meaning": "out of retained coverage"
            if outside
            else "no exact recorded sample; no interpolation/hold",
        }
    index = matches[0]
    row = frame.loc[index].to_dict()
    meaning = "native recorded row"
    if source == "states.csv":
        meaning = "state sample; input aliases are not a second applied-control record"
    elif source == "controls.csv":
        state_times = times(snapshot)
        later = [t for t in state_times if t > selected_time]
        if snapshot.data.request["adapter"] == "dynamic_lab" and later:
            meaning = (
                f"applied control row; declared ZOH interval [{selected_time!r}, {later[0]!r}) s"
            )
        else:
            meaning = "recorded control row; no completed interval inferred"
    elif source == "diagnostics.csv":
        terminal = selected_time == times(snapshot)[-1]
        if snapshot.data.request["adapter"] == "dynamic_lab" and terminal:
            meaning = (
                "terminal informational diagnostics; last held command, no terminal interval"
                if snapshot.data.summary.get("horizon_reached")
                else "partial last retained/attempted diagnostics; interval completion unknown"
            )
        else:
            meaning = "sample diagnostics; not an interval or physical measurement"
    elif source == "trajectory_xy.csv":
        meaning = "stored XY sample [m]; no coordinate reconstruction"
    return {
        **result,
        "available": True,
        "sample_index": int(index),
        "timestamp_s": float(row.pop("time")),
        "values": row,
        "meaning": meaning,
    }


def matrix(runs, qualification_record=None):
    if not 2 <= len(runs) <= MAX_RUNS or len({r.key for r in runs}) != len(runs):
        raise storage.IntegrityError("Select two to four distinct catalog executions")
    before = views.comparison_epoch(runs, qualification_record)
    pairs = [
        {
            "left": i,
            "right": j,
            "decision": views.compare(runs[i], runs[j], qualification_record=qualification_record),
        }
        for i, j in combinations(range(len(runs)), 2)
    ]
    snapshots = [load(run) for run in runs]
    if before != views.comparison_epoch(runs, qualification_record) or not all(
        views.comparison_current(pair["decision"]) for pair in pairs
    ):
        raise storage.IntegrityError("Evidence/qualification changed across pairwise comparison")
    return snapshots, pairs


def step(index, length, count):
    if type(index) is not int or type(count) is not int or length < 1:
        raise ValueError("Invalid recorded cursor")
    return min(length - 1, max(0, index + count))


def tick(state, length, now, *, samples_per_tick=1):
    """One bounded viewer advance per elapsed tick; no catch-up or model clock semantics."""
    result = dict(state)
    if result["playing"] and now - result["last_tick"] >= 1.0:
        result["index"] = step(result["index"], length, samples_per_tick)
        result["last_tick"] = now
        if result["index"] == length - 1:
            result["playing"] = False
    return result
