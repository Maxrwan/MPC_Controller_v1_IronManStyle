"""Backend-neutral solve contract; problem encoding is defined by future adapters."""

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class SolverResult:
    success: bool
    status: str
    solution: object | None = None
    statistics: dict = field(default_factory=dict)


class Solver(Protocol):
    def solve(self, problem: object) -> SolverResult:
        """Solve an adapter-supported problem; no backend dependency here."""
        ...


@dataclass(frozen=True)
class NLPRequest:
    """Backend-neutral numeric initial guess and NLP parameter vector."""

    initial: object
    parameters: object
