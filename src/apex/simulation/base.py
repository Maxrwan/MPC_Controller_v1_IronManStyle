"""Action-driven simulation contract, compatible with a future RL adapter."""

from dataclasses import dataclass, field
from typing import Protocol

from apex.state import Vector


@dataclass(frozen=True)
class StepResult:
    observation: Vector
    terminated: bool = False
    truncated: bool = False
    reward: float | None = None
    info: dict[str, object] = field(default_factory=dict)


class Simulation(Protocol):
    def reset(self, initial_state: Vector) -> Vector:
        """Reset and return the observation; stochastic seed API is future work."""
        ...

    def step(self, action: Vector) -> StepResult:
        """Advance one configured interval; lap crossings never end an episode.

        Future implementations must validate complete vehicle parameters first.
        Termination means a specified terminal condition; truncation means an
        external horizon or limit. No terminal conditions or reward are defined yet.
        """
        ...
