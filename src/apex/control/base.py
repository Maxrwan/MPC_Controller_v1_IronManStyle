"""Controller-neutral action selection interface."""

from collections.abc import Mapping
from typing import Protocol

from apex.state import Vector


class Controller(Protocol):
    def compute_control(self, state: Vector, context: Mapping[str, object]) -> Vector:
        """Return [delta, a_cmd] from an estimated state and supplied context.

        Context can later contain references, track, predictions, and constraints.
        Its detailed schema is deliberately deferred.
        """
        ...
