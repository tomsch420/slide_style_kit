"""
The errors raised while computing the lecture's examples.
"""

from __future__ import annotations

from dataclasses import dataclass

from krrood.exceptions import DataclassException

# %% solvers


@dataclass(kw_only=True)
class SolverFailure(DataclassException):
    """
    Raised when a numerical solver stops without reaching an optimum.
    """

    solver: str
    """
    The name of the solver.
    """

    message: str
    """
    The reason the solver gave for stopping.
    """

    def error_message(self) -> str:
        return f"{self.solver} stopped without an optimum: {self.message}"

    def suggest_correction(self) -> str:
        return "Raise the iteration limit or loosen the tolerance of the solver."
