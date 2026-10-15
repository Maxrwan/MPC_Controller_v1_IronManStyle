"""Immutable reviewed VIS-1 case definitions; no arbitrary experiment arguments."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

BASE = "d55d7b299217d6b62efc90cb525c2493224a7cca"
PATTERN = (0.035, 0.055, 0.045, 0.025)
HISTORY_SIZE = 8001
FLOOR = 2**30
HEADROOM = int(1.5 * 2**30)


@dataclass(frozen=True)
class Case:
    name: str
    architecture: str
    phase: str
    duration: float
    repetition: int = 0

    @property
    def offset(self):
        return 0.07 if self.architecture == "C70" else None


CASES = (
    Case("parity_A", "A", "parity", 2.0),
    Case("parity_C70", "C70", "parity", 2.0),
    Case("controlled_A", "A", "controlled", 80.0),
    Case("controlled_C70", "C70", "controlled", 80.0),
    Case("measured_A_1", "A", "measured", 80.0, 1),
    Case("measured_C70_1", "C70", "measured", 80.0, 1),
    Case("measured_C70_2", "C70", "measured", 80.0, 2),
    Case("measured_A_2", "A", "measured", 80.0, 2),
)


def case_named(name):
    return next(c for c in CASES if c.name == name)


def availability(case):
    from apex.simulation.asynchronous import AsyncConfig
    from apex.simulation.diagnostic_timing import DiagnosticTiming

    sim = AsyncConfig(
        duration=case.duration,
        laps=2,
        latency_mode="measured" if case.phase == "measured" else "injected",
        codriver_delay=0.005,
        fixed_handoff_offset=case.offset,
    )
    timing = None
    if case.phase != "measured":
        timing = DiagnosticTiming(
            "replay",
            tuple(PATTERN[i % len(PATTERN)] for i in range(HISTORY_SIZE)),
            (0.005,) * HISTORY_SIZE,
        )
    return sim, timing


def source_hashes():
    files = [
        *Path("src").rglob("*.py"),
        *Path("scripts").rglob("*.py"),
        *Path("tests").rglob("*.py"),
        Path("pyproject.toml"),
        Path("uv.lock"),
    ]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
