"""Opt-in physical availability schedules; never substitute for measured benchmarks."""

import math
from dataclasses import dataclass, replace


class ReplayExhausted(ValueError):
    """No historical delay exists for the next launched computation."""


@dataclass(frozen=True)
class DiagnosticTiming:
    mode: str
    planner: tuple[float, ...]
    codriver: tuple[float, ...]

    def __post_init__(self):
        if self.mode not in ("fixed", "replay"):
            raise ValueError("Diagnostic timing must be fixed or replay")
        for sequence in (self.planner, self.codriver):
            if not sequence or any(not math.isfinite(v) or v < 0 for v in sequence):
                raise ValueError("Finite nonnegative delays required")
            if self.mode == "fixed" and len(sequence) != 1:
                raise ValueError("Fixed timing requires one delay per channel")

    def _delay(self, sequence, index, channel):
        if index < 0:
            raise ValueError("Negative timing index")
        if self.mode == "fixed":
            return sequence[0]
        if index >= len(sequence):
            raise ReplayExhausted(f"{channel} replay exhausted at launch index {index}")
        return sequence[index]

    def planner_delay(self, plan_id):
        # Startup is gated before physical launch; it never consumes a trace entry.
        return self._delay(self.planner, plan_id - 1, "planner")

    def codriver_delay(self, launch_index):
        return self._delay(self.codriver, launch_index, "codriver")

    def perturb(self, index, delta):
        if self.mode != "replay" or not 0 <= index < len(self.planner):
            raise ValueError("A valid replay planner index is required")
        values = list(self.planner)
        values[index] += delta
        return replace(self, planner=tuple(values))
