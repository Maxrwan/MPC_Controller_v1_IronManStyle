"""Owned immutable local records. These are not physical permissions or wire messages."""

from dataclasses import dataclass


def freeze(value):
    if isinstance(value, dict):
        return tuple((k, freeze(v)) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return tuple(freeze(v) for v in value)
    if hasattr(value, "tolist"):
        return freeze(value.tolist())
    return value


@dataclass(frozen=True)
class Feedback:
    sample_id: int
    time: float
    state: tuple
    clock: str = "local-simulation"

    def __post_init__(self):
        object.__setattr__(self, "state", tuple(self.state))


@dataclass(frozen=True)
class Prepared:
    session: str
    request_id: int
    plan_id: int
    packet: object | None
    release_time: float
    diagnostics: tuple


@dataclass(frozen=True)
class Output:
    status: str
    session: str
    time: float | None
    reasons: tuple[str, ...] = ()
    command: tuple[float, float] | None = None
    proposal_id: int | None = None
    plan_id: int | None = None
    sample_id: int | None = None
    stage: str = "proposal"
    requested: tuple | None = None

    def __post_init__(self):
        from math import isfinite

        if self.status == "VALID_NOMINAL":
            if self.command is None or len(self.command) != 2:
                raise ValueError("Valid nominal output requires a two-vector")
            command = tuple(float(v) for v in self.command)
            if not all(isfinite(v) for v in command):
                raise ValueError("Nonfinite output")
            object.__setattr__(self, "command", command)
        elif self.command is not None:
            raise ValueError("Nonvalid status cannot carry a command")


@dataclass(frozen=True)
class Event:
    sequence: int
    session: str
    operation: str
    time: float | None
    status: str
    reasons: tuple
    details: tuple = ()
