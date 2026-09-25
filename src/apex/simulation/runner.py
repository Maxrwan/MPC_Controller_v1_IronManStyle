"""Controller-neutral fixed-rate simulation with explicit limits and failure records."""

import csv
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from apex.control.base import Controller
from apex.models.base import DynamicsModel
from apex.models.errors import FrenetGeometryError, ModelValidationError
from apex.simulation.timing import LatencyConfig, run_timed
from apex.state import CONTROL_NAMES, STATE_NAMES, Vector, control_vector, state_vector
from apex.state import StateIndex as S
from apex.track.base import Track
from apex.track.progress import lap_index, wrap_progress


@dataclass(frozen=True)
class RunConfig:
    duration: float = 80.0
    target_laps: int | None = None
    dt_plant: float = 0.005
    dt_control: float = 0.01
    stop_on_boundary: bool = False
    latency: LatencyConfig | None = None

    def __post_init__(self):
        for value in (self.duration, self.dt_plant, self.dt_control):
            if not np.isfinite(value) or value <= 0:
                raise ValueError("Duration and timesteps must be positive finite")
        if self.dt_control < self.dt_plant:
            raise ValueError("Control period must be at least one plant step")
        ratios = [self.duration / self.dt_plant]
        if self.latency is None:
            ratios.append(self.dt_control / self.dt_plant)
        for ratio in ratios:
            if ratio < 1 or not np.isclose(ratio, round(ratio), rtol=0, atol=1e-9):
                raise ValueError("Control period and duration must be integer plant-step multiples")
        if self.target_laps is not None and (
            isinstance(self.target_laps, bool)
            or not isinstance(self.target_laps, int)
            or self.target_laps <= 0
        ):
            raise ValueError("target_laps must be a positive integer or None")


@dataclass
class RunResult:
    states: list[dict]
    controls: list[dict]
    stop_reason: str
    failure: str | None = None
    events: list[dict] = field(default_factory=list)
    predictions: list[dict] = field(default_factory=list)
    timing: dict = field(default_factory=dict)

    def write_csv(self, directory: str | Path):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        for filename, rows in (
            ("states.csv", self.states),
            ("controls.csv", self.controls),
            ("solver_events.csv", self.events),
        ):
            if rows:
                with (directory / filename).open("w", newline="", encoding="utf-8") as stream:
                    writer = csv.DictWriter(
                        stream, fieldnames=list(dict.fromkeys(key for row in rows for key in row))
                    )
                    writer.writeheader()
                    writer.writerows(rows)
        if self.predictions:
            with (directory / "predictions.jsonl").open("w") as stream:
                for prediction in self.predictions:
                    stream.write(
                        json.dumps(prediction, default=lambda x: np.asarray(x).tolist()) + "\n"
                    )


class SimulationRunner:
    """Hold commands between integer control ticks; laps never reset state.

    Optional reset and diagnostic callbacks avoid adding baseline-specific methods to
    the Controller protocol. Without reset_controller the caller owns controller reset.
    State rows contain the input applied on the following interval; final input is
    informational. Failed steps retain the last valid state and an explicit failure.
    """

    def __init__(
        self,
        model: DynamicsModel,
        controller: Controller,
        track: Track,
        config: RunConfig = RunConfig(),
        *,
        controller_diagnostics: Callable[[], Mapping[str, object]] | None = None,
        reset_controller: Callable[[], None] | None = None,
        finalize_control: Callable | None = None,
        prediction_diagnostics: Callable | None = None,
        initial_control: Vector | None = None,
    ):
        self.model, self.controller, self.track, self.config = model, controller, track, config
        self.controller_diagnostics = controller_diagnostics
        self.reset_controller = reset_controller
        self.finalize_control = finalize_control
        self.prediction_diagnostics = prediction_diagnostics
        self.initial_control = control_vector(
            np.zeros(2) if initial_control is None else initial_control
        )
        self.state: Vector | None = None

    def _row(self, time, control):
        x = self.state
        geometry = self.track.sample(wrap_progress(x[S.S_ABS], self.track.length))
        return {
            "time": time,
            **dict(zip(STATE_NAMES, map(float, x))),
            "lap_index": lap_index(x[S.S_ABS], self.track.length),
            "track_s": geometry.track_s,
            "curvature": geometry.curvature,
            "left_width": geometry.left_width,
            "right_width": geometry.right_width,
            "boundary_violation": not -geometry.right_width <= x[S.E_Y] <= geometry.left_width,
            **dict(zip(CONTROL_NAMES, map(float, control))),
        }

    def run(self, initial_state: Vector) -> RunResult:
        if self.config.latency is not None:
            return run_timed(self, initial_state)
        if self.finalize_control is not None:
            raise ValueError("Application callback requires explicit latency mode (including zero)")
        self.state = state_vector(initial_state)
        if self.reset_controller is not None:
            self.reset_controller()
        config = self.config
        stride = round(config.dt_control / config.dt_plant)
        steps = round(config.duration / config.dt_plant)
        target = (
            self.state[S.S_ABS] + config.target_laps * self.track.length
            if config.target_laps is not None
            else np.inf
        )
        states, controls = [], []
        action = np.zeros(2)
        reason, failure = "duration", None
        for step in range(steps + 1):
            time = step * config.dt_plant
            at_target = self.state[S.S_ABS] >= target
            terminal = step == steps or at_target
            if not terminal and step % stride == 0:
                action = control_vector(
                    self.controller.compute_control(
                        self.state.copy(), {"time": time, "dt": config.dt_control}
                    )
                )
                diagnostics = (
                    dict(self.controller_diagnostics())
                    if self.controller_diagnostics is not None
                    else {}
                )
                controls.append(
                    {**diagnostics, "time": time, **dict(zip(CONTROL_NAMES, map(float, action)))}
                )
            row = self._row(time, action)
            states.append(row)
            if row["boundary_violation"] and config.stop_on_boundary:
                reason = "boundary_violation"
                break
            if terminal:
                reason = "target_laps" if at_target else "duration"
                break
            try:
                self.state = state_vector(
                    self.model.step(self.state.copy(), action.copy(), config.dt_plant)
                )
            except (ModelValidationError, FrenetGeometryError) as error:
                reason, failure = "model_validity_failure", f"{type(error).__name__}: {error}"
                break
        return RunResult(states, controls, reason, failure)
