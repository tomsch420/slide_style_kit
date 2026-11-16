"""
The optimization problems behind the lecture's examples, solved numerically.

The slides take their numbers from here and the animations their geometry, so both stay
consistent with each other and reproducible.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property

import contourpy
import numpy as np
from scipy.optimize import linprog, minimize
from typing_extensions import Self

from exceptions import SolverFailure

# %% points and polylines


@dataclass(kw_only=True, frozen=True)
class Optimum:
    """
    The solution of an optimization problem.
    """

    point: tuple[float, ...]
    """
    The optimal values of the decision variables.
    """

    value: float
    """
    The objective value at :attr:`point`.
    """


@dataclass(kw_only=True)
class LevelSet:
    """
    The curves on which a function of two variables takes one value.
    """

    level: float
    """
    The function value along the curves.
    """

    curves: list[np.ndarray]
    """
    The curves, each an array of points with one row per point.
    """

    @classmethod
    def from_grid(
        cls,
        *,
        function: TwoVariableFunction,
        horizontal_range: tuple[float, float],
        vertical_range: tuple[float, float],
        levels: list[float],
        resolution: int = 200,
    ) -> list[Self]:
        """
        :param function: The function whose level sets are traced.
        :param horizontal_range: The interval of the first variable.
        :param vertical_range: The interval of the second variable.
        :param levels: The function values to trace.
        :param resolution: The number of grid points along each axis.
        :return: The level set of each value in *levels*.
        """
        horizontal = np.linspace(*horizontal_range, resolution)
        vertical = np.linspace(*vertical_range, resolution)
        grid_x, grid_y = np.meshgrid(horizontal, vertical)
        values = function.evaluate(points=np.stack([grid_x, grid_y], axis=-1))
        generator = contourpy.contour_generator(grid_x, grid_y, values)
        return [
            cls(
                level=level,
                curves=[np.asarray(line) for line in generator.lines(level)],
            )
            for level in levels
        ]


# %% functions of two variables


@dataclass(kw_only=True)
class TwoVariableFunction(ABC):
    """
    A smooth function of two variables with its gradient.
    """

    @abstractmethod
    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        """
        :param points: Points along the last axis, of shape ``(..., 2)``.
        :return: The function value at each point, of shape ``(...)``.
        """

    @abstractmethod
    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        """
        :param point: One point of shape ``(2,)``.
        :return: The gradient at *point*.
        """


@dataclass(kw_only=True)
class Paraboloid(TwoVariableFunction):
    """
    The convex bowl :math:`f(x, y) = x^2 + y^2`.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        return np.sum(points**2, axis=-1)

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        return 2 * point


@dataclass(kw_only=True)
class SaddleLandscape(TwoVariableFunction):
    """
    :math:`f(x, y) = x y e^{-(x^2 + y^2)/2}`: two hills and two valleys around a
    saddle point.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        x, y = points[..., 0], points[..., 1]
        return x * y * np.exp(-(x**2 + y**2) / 2)

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        x, y = point
        envelope = np.exp(-(x**2 + y**2) / 2)
        return np.array([y * (1 - x**2) * envelope, x * (1 - y**2) * envelope])


@dataclass(kw_only=True)
class PeaksLandscape(TwoVariableFunction):
    """
    The classic *peaks* test function, with several maxima, minima and saddle points.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        x, y = points[..., 0], points[..., 1]
        return (
            3 * (1 - x) ** 2 * np.exp(-(x**2) - (y + 1) ** 2)
            - 10 * (x / 5 - x**3 - y**5) * np.exp(-(x**2) - y**2)
            - np.exp(-((x + 1) ** 2) - y**2) / 3
        )

    def gradient(self, *, point: np.ndarray, step: float = 1e-6) -> np.ndarray:
        """
        :param point: One point of shape ``(2,)``.
        :param step: The step of the central difference quotient.
        :return: The gradient at *point*, by central differences.
        """
        offsets = np.eye(2) * step
        forward = self.evaluate(points=point + offsets)
        backward = self.evaluate(points=point - offsets)
        return (forward - backward) / (2 * step)

    def critical_points(
        self, *, search_range: tuple[float, float] = (-3, 3), starts_per_axis: int = 13
    ) -> list[CriticalPoint]:
        """
        :param search_range: The interval of both variables the search starts from.
        :param starts_per_axis: The number of starting points along each axis.
        :return: Every critical point found inside the search range, each once.
        """
        found: list[CriticalPoint] = []
        starts = np.linspace(*search_range, starts_per_axis)
        for start in np.array(np.meshgrid(starts, starts)).reshape(2, -1).T:
            result = minimize(
                lambda point: float(np.sum(self.gradient(point=point) ** 2)),
                start,
                method="BFGS",
                options={"gtol": 1e-12},
            )
            if np.sum(self.gradient(point=result.x) ** 2) > 1e-10:
                continue
            if np.any(np.abs(result.x) > max(np.abs(search_range))):
                continue
            if any(np.linalg.norm(result.x - point.position) < 1e-3 for point in found):
                continue
            found.append(CriticalPoint.from_function(function=self, position=result.x))
        return found


@dataclass(kw_only=True)
class CriticalPoint:
    """
    A point where the gradient of a function vanishes.
    """

    position: np.ndarray
    """
    The location of the point.
    """

    value: float
    """
    The function value at the point.
    """

    hessian_eigenvalues: np.ndarray
    """
    The eigenvalues of the Hessian at the point, ascending.
    """

    @classmethod
    def from_function(
        cls, *, function: TwoVariableFunction, position: np.ndarray, step: float = 1e-4
    ) -> Self:
        """
        :param function: The function the point is critical for.
        :param position: The location of the point.
        :param step: The step of the difference quotient of the Hessian.
        :return: The point, with the Hessian estimated by differences of the gradient.
        """
        hessian = np.column_stack(
            [
                (
                    function.gradient(point=position + offset)
                    - function.gradient(point=position - offset)
                )
                / (2 * step)
                for offset in np.eye(2) * step
            ]
        )
        return cls(
            position=position,
            value=float(function.evaluate(points=position)),
            hessian_eigenvalues=np.linalg.eigvalsh((hessian + hessian.T) / 2),
        )

    @property
    def is_minimum(self) -> bool:
        """
        Whether the function curves upward in every direction.
        """
        return bool(np.all(self.hessian_eigenvalues > 0))

    @property
    def is_saddle(self) -> bool:
        """
        Whether the function curves upward in one direction and downward in another.
        """
        return bool(self.hessian_eigenvalues[0] < 0 < self.hessian_eigenvalues[-1])


@dataclass(kw_only=True)
class StretchedValley(TwoVariableFunction):
    """
    An ill-conditioned quadratic :math:`f(x, y) = (x^2 + \\kappa y^2) / 2`, a long
    narrow valley along the first axis.
    """

    condition_number: float = 20
    """
    The ratio :math:`\\kappa` of the curvatures across and along the valley.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        x, y = points[..., 0], points[..., 1]
        return (x**2 + self.condition_number * y**2) / 2

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        return np.array([point[0], self.condition_number * point[1]])


# %% descent methods


@dataclass(kw_only=True)
class DescentMethod(ABC):
    """
    An iterative method that minimizes a function by following its gradient.
    """

    learning_rate: float
    """
    The step size :math:`\\alpha`.
    """

    @abstractmethod
    def step(self, *, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        """
        :param point: The current iterate.
        :param gradient: The gradient at *point*.
        :return: The next iterate.
        """

    def iterates(
        self, *, function: TwoVariableFunction, start: np.ndarray, iterations: int
    ) -> np.ndarray:
        """
        :return: The start followed by *iterations* iterates, one per row.
        """
        points = [np.asarray(start, dtype=float)]
        for _ in range(iterations):
            gradient = function.gradient(point=points[-1])
            points.append(self.step(point=points[-1], gradient=gradient))
        return np.array(points)


@dataclass(kw_only=True)
class GradientDescent(DescentMethod):
    """
    :math:`x_{k+1} = x_k - \\alpha \\nabla f(x_k)`.
    """

    def step(self, *, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        return point - self.learning_rate * gradient


@dataclass(kw_only=True)
class Momentum(DescentMethod):
    """
    Gradient descent on a moving average of past steps,
    :math:`v_{k+1} = \\beta v_k - \\alpha \\nabla f(x_k)`.
    """

    decay: float = 0.8
    """
    The weight :math:`\\beta` of the previous velocity.
    """

    velocity: np.ndarray = field(default_factory=lambda: np.zeros(2))
    """
    The current velocity :math:`v_k`.
    """

    def step(self, *, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        self.velocity = self.decay * self.velocity - self.learning_rate * gradient
        return point + self.velocity


@dataclass(kw_only=True)
class Adam(DescentMethod):
    """
    Adam: momentum on the gradient, scaled per coordinate by the root of a moving
    average of the squared gradient.
    """

    first_moment_decay: float = 0.9
    """
    The decay of the moving average of the gradient.
    """

    second_moment_decay: float = 0.999
    """
    The decay of the moving average of the squared gradient.
    """

    epsilon: float = 1e-8
    """
    The constant that keeps the scaling finite where the gradient vanishes.
    """

    first_moment: np.ndarray = field(default_factory=lambda: np.zeros(2))
    """
    The moving average of the gradient.
    """

    second_moment: np.ndarray = field(default_factory=lambda: np.zeros(2))
    """
    The moving average of the squared gradient.
    """

    step_count: int = 0
    """
    The number of steps taken, for the bias correction.
    """

    def step(self, *, point: np.ndarray, gradient: np.ndarray) -> np.ndarray:
        self.step_count += 1
        self.first_moment = (
            self.first_moment_decay * self.first_moment
            + (1 - self.first_moment_decay) * gradient
        )
        self.second_moment = (
            self.second_moment_decay * self.second_moment
            + (1 - self.second_moment_decay) * gradient**2
        )
        corrected_first = self.first_moment / (
            1 - self.first_moment_decay**self.step_count
        )
        corrected_second = self.second_moment / (
            1 - self.second_moment_decay**self.step_count
        )
        return point - self.learning_rate * corrected_first / (
            np.sqrt(corrected_second) + self.epsilon
        )


# %% functions of one variable


@dataclass(kw_only=True)
class OneVariableFunction(ABC):
    """
    A smooth function of one variable with its derivative.
    """

    @abstractmethod
    def evaluate(self, *, x: np.ndarray) -> np.ndarray:
        """
        :return: The function value at every entry of *x*.
        """

    @abstractmethod
    def derivative(self, *, x: float) -> float:
        """
        :return: The derivative at *x*.
        """

    def descent_iterates(
        self, *, start: float, learning_rate: float, iterations: int
    ) -> np.ndarray:
        """
        :return: The start followed by *iterations* gradient descent iterates.
        """
        points = [start]
        for _ in range(iterations):
            points.append(points[-1] - learning_rate * self.derivative(x=points[-1]))
        return np.array(points)


@dataclass(kw_only=True)
class ShiftedParabola(OneVariableFunction):
    """
    :math:`f(x) = a (x - m)^2 + c`, with its minimum at :math:`m`.
    """

    curvature: float = 0.25
    """
    The coefficient :math:`a`.
    """

    minimum_position: float = 4.0
    """
    The position :math:`m` of the minimum.
    """

    minimum_value: float = 0.5
    """
    The value :math:`c` at the minimum.
    """

    def evaluate(self, *, x: np.ndarray) -> np.ndarray:
        return self.curvature * (x - self.minimum_position) ** 2 + self.minimum_value

    def derivative(self, *, x: float) -> float:
        return 2 * self.curvature * (x - self.minimum_position)


@dataclass(kw_only=True)
class BumpyLandscape(OneVariableFunction):
    """
    A shallow local minimum, a deep global minimum and an almost flat plateau.
    """

    plateau_slope: float = 0.003
    """
    The slope of the plateau, small enough that gradient descent barely moves on it.
    """

    def evaluate(self, *, x: np.ndarray) -> np.ndarray:
        return (
            1.8
            - 0.55 * np.exp(-(((x - 1.2) / 0.35) ** 2))
            - 1.5 * np.exp(-(((x - 3.6) / 0.7) ** 2))
            + self.plateau_slope * x
        )

    def derivative(self, *, x: float, step: float = 1e-6) -> float:
        """
        :param x: The position.
        :param step: The step of the central difference quotient.
        :return: The derivative at *x*, by central differences.
        """
        return float(
            (self.evaluate(x=np.array(x + step)) - self.evaluate(x=np.array(x - step)))
            / (2 * step)
        )


# %% velocity control example


@dataclass(kw_only=True)
class VelocityControlProblem:
    """
    A two-joint version of the quadratic program a constraint-based controller such as
    Giskard solves every control cycle: choose the velocities :math:`x` of a mobile base
    and an arm so that the gripper approaches a cup at a desired speed, within the joint
    limits :math:`Gx \\le g`.
    """

    joint_weights: np.ndarray = field(default_factory=lambda: np.array([2.0, 1.0]))
    """
    The cost :math:`w_i` per squared velocity of each joint; moving the base costs more.
    """

    gripper_jacobian: np.ndarray = field(default_factory=lambda: np.array([1.0, 1.0]))
    """
    The gripper speed :math:`J x` each joint velocity contributes.
    """

    goal_weight: float = 10.0
    """
    The cost :math:`w_s` per squared deviation from the desired gripper speed.
    """

    desired_gripper_speed: float = 30.0
    """
    The gripper speed :math:`v^*` the goal asks for, in cm/s.
    """

    constraint_matrix: np.ndarray = field(
        default_factory=lambda: np.array(
            [[1.0, 0.0], [0.0, 1.0], [1.0, 0.5], [-1.0, 0.0], [0.0, -1.0]]
        )
    )
    """
    The left-hand sides :math:`G` of the base limit, the arm limit, the elbow's collision
    avoidance and the two lower limits, one row each.
    """

    constraint_bounds: np.ndarray = field(
        default_factory=lambda: np.array([10.0, 25.0, 15.0, 0.0, 0.0])
    )
    """
    The right-hand sides :math:`g` of the constraints, in cm/s.
    """

    constraint_names: list[str] = field(
        default_factory=lambda: ["base", "arm", "elbow", "base forward", "arm forward"]
    )
    """
    The part of the robot each constraint limits, one per row of :math:`G`.
    """

    @property
    def quadratic_cost_matrix(self) -> np.ndarray:
        """
        The matrix :math:`Q = \\mathrm{diag}(w) + w_s J^T J` of the cost.
        """
        return np.diag(self.joint_weights) + self.goal_weight * np.outer(
            self.gripper_jacobian, self.gripper_jacobian
        )

    @property
    def linear_cost(self) -> np.ndarray:
        """
        The vector :math:`c = -w_s v^* J^T` of the cost.
        """
        return -self.goal_weight * self.desired_gripper_speed * self.gripper_jacobian

    @property
    def constant_cost(self) -> float:
        """
        The constant :math:`\\frac{1}{2} w_s {v^*}^2` of the cost.
        """
        return self.goal_weight * self.desired_gripper_speed**2 / 2

    def gripper_speed(self, *, points: np.ndarray) -> np.ndarray:
        """
        :return: The gripper speed :math:`J x` at each point.
        """
        return points @ self.gripper_jacobian

    def cost(self, *, points: np.ndarray) -> np.ndarray:
        """
        :return: The cost :math:`\\frac{1}{2} \\sum_i w_i x_i^2 + \\frac{1}{2} w_s
            (J x - v^*)^2` at each point.
        """
        quadratic = np.einsum(
            "...i,ij,...j->...", points, self.quadratic_cost_matrix, points
        )
        return quadratic / 2 + points @ self.linear_cost + self.constant_cost

    def cost_gradient(self, *, point: np.ndarray) -> np.ndarray:
        """
        :return: The gradient :math:`Q x + c` of the cost at *point*.
        """
        return self.quadratic_cost_matrix @ point + self.linear_cost

    @cached_property
    def linear_optimum(self) -> Optimum:
        """
        The velocities that maximize the gripper speed, ignoring the motion cost.
        """
        result = linprog(
            -self.gripper_jacobian,
            A_ub=self.constraint_matrix,
            b_ub=self.constraint_bounds,
            bounds=[(None, None)] * 2,
        )
        return Optimum(point=tuple(result.x), value=-float(result.fun))

    @cached_property
    def unconstrained_minimum(self) -> Optimum:
        """
        The velocities that minimize the cost when no constraint applies.
        """
        point = np.linalg.solve(self.quadratic_cost_matrix, -self.linear_cost)
        return Optimum(point=tuple(point), value=float(self.cost(points=point)))

    @cached_property
    def quadratic_optimum(self) -> Optimum:
        """
        The velocities that minimize the cost within the constraints.
        """
        result = minimize(
            lambda point: float(self.cost(points=point)),
            np.zeros(2),
            jac=lambda point: self.cost_gradient(point=point),
            constraints=[
                {
                    "type": "ineq",
                    "fun": lambda point: (
                        self.constraint_bounds - self.constraint_matrix @ point
                    ),
                    "jac": lambda point: -self.constraint_matrix,
                }
            ],
            method="SLSQP",
            options={"ftol": 1e-12},
        )
        if not result.success:
            raise SolverFailure(solver="SLSQP", message=result.message)
        return Optimum(point=tuple(result.x), value=float(result.fun))

    def lagrange_multipliers(
        self, *, point: np.ndarray, tolerance: float = 1e-6
    ) -> np.ndarray:
        """
        :param point: A candidate optimum of the quadratic program.
        :param tolerance: The slack below which a constraint counts as active.
        :return: The multiplier of every constraint that balances the cost gradient at
            *point*; zero for the inactive constraints.
        """
        active = np.abs(self.constraint_matrix @ point - self.constraint_bounds) < (
            tolerance
        )
        multipliers = np.zeros(len(self.constraint_bounds))
        multipliers[active] = np.linalg.lstsq(
            self.constraint_matrix[active].T,
            -self.cost_gradient(point=point),
            rcond=None,
        )[0]
        return multipliers

    @cached_property
    def feasible_vertices(self) -> np.ndarray:
        """
        The corners of the feasible polygon, counterclockwise, one per row.
        """
        vertices = []
        row_count = len(self.constraint_bounds)
        for first in range(row_count):
            for second in range(first + 1, row_count):
                rows = self.constraint_matrix[[first, second]]
                if abs(np.linalg.det(rows)) < 1e-12:
                    continue
                corner = np.linalg.solve(rows, self.constraint_bounds[[first, second]])
                if np.all(
                    self.constraint_matrix @ corner <= self.constraint_bounds + 1e-9
                ):
                    vertices.append(corner)
        vertices = np.unique(np.round(vertices, 9), axis=0)
        center = vertices.mean(axis=0)
        angles = np.arctan2(*(vertices - center).T[::-1])
        return vertices[np.argsort(angles)]


@dataclass(kw_only=True)
class MotionCost(TwoVariableFunction):
    """
    The cost of the velocity control problem as a function of the joint velocities.
    """

    problem: VelocityControlProblem
    """
    The problem whose cost is evaluated.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        return self.problem.cost(points=points)

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        return self.problem.cost_gradient(point=point)


@dataclass(kw_only=True)
class GripperSpeed(TwoVariableFunction):
    """
    The gripper speed :math:`J x` of the velocity control problem, the objective of its
    LP.
    """

    problem: VelocityControlProblem
    """
    The problem whose gripper speed is evaluated.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        return self.problem.gripper_speed(points=points)

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        return self.problem.gripper_jacobian


@dataclass(kw_only=True)
class QualityBand:
    """
    The part of the feasible region where a function lies between two values.
    """

    lower: float
    """
    The smallest function value in the band.
    """

    upper: float
    """
    The largest function value in the band.
    """

    polygons: list[np.ndarray]
    """
    The outlines of the band, each an array of points with one row per point.
    """

    @classmethod
    def from_grid(
        cls,
        *,
        function: TwoVariableFunction,
        problem: VelocityControlProblem,
        horizontal_range: tuple[float, float],
        vertical_range: tuple[float, float],
        band_count: int = 8,
        resolution: int = 300,
    ) -> list[Self]:
        """
        :param function: The function whose values the bands divide.
        :param problem: The problem whose feasible region the bands fill.
        :param horizontal_range: The interval of the first variable.
        :param vertical_range: The interval of the second variable.
        :param band_count: The number of bands, each covering an equal share of the
            feasible region.
        :param resolution: The number of grid points along each axis.
        :return: The bands, ordered by increasing function value.
        """
        horizontal = np.linspace(*horizontal_range, resolution)
        vertical = np.linspace(*vertical_range, resolution)
        grid_x, grid_y = np.meshgrid(horizontal, vertical)
        points = np.stack([grid_x, grid_y], axis=-1)
        values = function.evaluate(points=points)
        feasible = np.all(
            points @ problem.constraint_matrix.T <= problem.constraint_bounds + 1e-9,
            axis=-1,
        )
        levels = np.quantile(values[feasible], np.linspace(0, 1, band_count + 1))
        generator = contourpy.contour_generator(
            grid_x,
            grid_y,
            np.ma.masked_array(values, mask=~feasible),
            fill_type=contourpy.FillType.OuterOffset,
        )
        bands = []
        for lower, upper in zip(levels, levels[1:]):
            outlines, offsets = generator.filled(lower, upper)
            bands.append(
                cls(
                    lower=float(lower),
                    upper=float(upper),
                    polygons=[
                        outline[offset[0] : offset[1]]
                        for outline, offset in zip(outlines, offsets)
                    ],
                )
            )
        return bands


# %% linear program solvers


@dataclass(kw_only=True)
class SimplexMethod:
    """
    The primal simplex method on a tableau, maximizing the gripper speed and entering
    the variable with the largest reduced gain (Dantzig's rule).
    """

    problem: VelocityControlProblem
    """
    The problem to solve; its rows with a positive bound are the tableau's constraints,
    the others are the non-negativity of the variables.
    """

    @cached_property
    def vertices(self) -> list[np.ndarray]:
        """
        The vertex of every basic feasible solution visited, from the origin to the
        optimum.
        """
        rows = self.problem.constraint_bounds > 0
        matrix = self.problem.constraint_matrix[rows]
        constraint_count, variable_count = matrix.shape
        tableau = np.zeros(
            (constraint_count + 1, variable_count + constraint_count + 1)
        )
        tableau[:constraint_count, :variable_count] = matrix
        tableau[:constraint_count, variable_count:-1] = np.eye(constraint_count)
        tableau[:constraint_count, -1] = self.problem.constraint_bounds[rows]
        tableau[-1, :variable_count] = -self.problem.gripper_jacobian
        basis = list(range(variable_count, variable_count + constraint_count))
        visited = [
            self.basic_solution(tableau=tableau, basis=basis, size=variable_count)
        ]
        while np.min(tableau[-1, :-1]) < -1e-12:
            entering = int(np.argmin(tableau[-1, :-1]))
            column = tableau[:constraint_count, entering]
            ratios = np.where(
                column > 1e-12, tableau[:constraint_count, -1] / column, np.inf
            )
            leaving = int(np.argmin(ratios))
            tableau[leaving] /= tableau[leaving, entering]
            for row in range(constraint_count + 1):
                if row != leaving:
                    tableau[row] -= tableau[row, entering] * tableau[leaving]
            basis[leaving] = entering
            visited.append(
                self.basic_solution(tableau=tableau, basis=basis, size=variable_count)
            )
        return visited

    def basic_solution(
        self, *, tableau: np.ndarray, basis: list[int], size: int
    ) -> np.ndarray:
        """
        :return: The values of the first *size* variables in the tableau's basic
            solution.
        """
        solution = np.zeros(size)
        for row, variable in enumerate(basis):
            if variable < size:
                solution[variable] = tableau[row, -1]
        return solution


@dataclass(kw_only=True)
class BarrierObjective(TwoVariableFunction):
    """
    The log-barrier objective
    :math:`\\phi_t(x) = -t\\, J x - \\sum_i \\log(g_i - G_i x)` of the gripper speed LP,
    infinite outside the feasible region.
    """

    problem: VelocityControlProblem
    """
    The linear program.
    """

    sharpness: float
    """
    The weight :math:`t` of the objective; larger values weaken the barrier.
    """

    def slacks(self, *, points: np.ndarray) -> np.ndarray:
        """
        :return: The slack :math:`g_i - G_i x` of every constraint at each point.
        """
        return (
            self.problem.constraint_bounds - points @ self.problem.constraint_matrix.T
        )

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        slacks = self.slacks(points=points)
        barrier = -np.sum(np.log(np.where(slacks > 0, slacks, np.nan)), axis=-1)
        return -self.sharpness * self.problem.gripper_speed(points=points) + barrier

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        slacks = self.slacks(points=point)
        return (
            -self.sharpness * self.problem.gripper_jacobian
            + self.problem.constraint_matrix.T @ (1 / slacks)
        )

    def hessian(self, *, point: np.ndarray) -> np.ndarray:
        """
        :return: The Hessian of the barrier at *point*.
        """
        slacks = self.slacks(points=point)
        matrix = self.problem.constraint_matrix
        return matrix.T @ np.diag(1 / slacks**2) @ matrix

    def minimizer(self, *, start: np.ndarray, iterations: int = 50) -> np.ndarray:
        """
        :param start: A point strictly inside the feasible region.
        :return: The minimizer of the barrier objective, by damped Newton steps.
        """
        point = np.asarray(start, dtype=float)
        for _ in range(iterations):
            direction = -np.linalg.solve(
                self.hessian(point=point), self.gradient(point=point)
            )
            step = 1.0
            while np.any(self.slacks(points=point + step * direction) <= 0) or (
                self.evaluate(points=point + step * direction)
                > self.evaluate(points=point)
            ):
                step /= 2
            point = point + step * direction
            if np.linalg.norm(step * direction) < 1e-10:
                break
        return point


@dataclass(kw_only=True)
class InteriorPointMethod:
    """
    The barrier method: minimize :math:`\\phi_t` for growing :math:`t`, each time
    starting from the previous minimizer.
    """

    problem: VelocityControlProblem
    """
    The linear program.
    """

    sharpnesses: list[float] = field(
        default_factory=lambda: list(np.geomspace(1e-2, 100.0, 28))
    )
    """
    The weights :math:`t` of the objective, in the order they are used.
    """

    start: np.ndarray = field(default_factory=lambda: np.array([3.0, 5.0]))
    """
    A point strictly inside the feasible region to start from.
    """

    def barrier(self, *, sharpness: float) -> BarrierObjective:
        """
        :return: The barrier objective with weight *sharpness*.
        """
        return BarrierObjective(problem=self.problem, sharpness=sharpness)

    @cached_property
    def central_path(self) -> np.ndarray:
        """
        The analytic center followed by the minimizer for every weight, one per row.
        """
        points = [self.barrier(sharpness=0.0).minimizer(start=self.start)]
        for sharpness in self.sharpnesses:
            points.append(self.barrier(sharpness=sharpness).minimizer(start=points[-1]))
        return np.array(points)


# %% stochastic gradient descent


@dataclass(kw_only=True)
class LineFittingProblem:
    """
    Fitting a line :math:`y = \\theta_1 x + \\theta_2` to seeded noisy samples by least
    squares, the loss being the mean of one squared error per sample.
    """

    seed: int = 3
    """
    The seed of the random samples.
    """

    sample_count: int = 200
    """
    The number of samples.
    """

    true_parameters: tuple[float, float] = (1.5, -1.0)
    """
    The slope and intercept the samples are drawn around.
    """

    noise: float = 0.5
    """
    The standard deviation of the noise on every sample.
    """

    @cached_property
    def inputs(self) -> np.ndarray:
        """
        The inputs :math:`x_j`, uniform in :math:`[-2, 2]`.
        """
        return np.random.default_rng(self.seed).uniform(-2, 2, self.sample_count)

    @cached_property
    def targets(self) -> np.ndarray:
        """
        The targets :math:`y_j` on the true line plus Gaussian noise.
        """
        generator = np.random.default_rng(self.seed + 1)
        slope, intercept = self.true_parameters
        return (
            slope * self.inputs
            + intercept
            + generator.normal(0, self.noise, self.sample_count)
        )

    def minibatch_gradient(
        self, *, point: np.ndarray, indices: np.ndarray
    ) -> np.ndarray:
        """
        :return: The gradient at *point* of the mean squared error over the samples
            *indices*.
        """
        residuals = point[0] * self.inputs[indices] + point[1] - self.targets[indices]
        return np.array([np.mean(residuals * self.inputs[indices]), np.mean(residuals)])


@dataclass(kw_only=True)
class LineFittingLoss(TwoVariableFunction):
    """
    Half the mean squared error of a line fitting problem as a function of the slope and
    the intercept.
    """

    problem: LineFittingProblem
    """
    The samples the loss is computed over.
    """

    def evaluate(self, *, points: np.ndarray) -> np.ndarray:
        predictions = points[..., 0, None] * self.problem.inputs + points[..., 1, None]
        return np.mean((predictions - self.problem.targets) ** 2, axis=-1) / 2

    def gradient(self, *, point: np.ndarray) -> np.ndarray:
        return self.problem.minibatch_gradient(
            point=point, indices=np.arange(self.problem.sample_count)
        )


@dataclass(kw_only=True)
class StochasticGradientDescent:
    """
    Gradient descent that follows the gradient of a random minibatch of samples instead
    of the gradient of the whole loss.
    """

    learning_rate: float
    """
    The step size :math:`\\alpha`.
    """

    batch_size: int
    """
    The number of samples per gradient estimate.
    """

    seed: int = 0
    """
    The seed of the minibatch draws.
    """

    def iterates(
        self, *, problem: LineFittingProblem, start: np.ndarray, iterations: int
    ) -> np.ndarray:
        """
        :return: The start followed by *iterations* iterates, one per row.
        """
        generator = np.random.default_rng(self.seed)
        points = [np.asarray(start, dtype=float)]
        for _ in range(iterations):
            indices = generator.choice(
                problem.sample_count, self.batch_size, replace=False
            )
            gradient = problem.minibatch_gradient(point=points[-1], indices=indices)
            points.append(points[-1] - self.learning_rate * gradient)
        return np.array(points)


# %% computational graphs


@dataclass(kw_only=True, eq=False)
class GraphNode(ABC):
    """
    A node of a computational graph: an input or a primitive operation on the values of
    other nodes, with the adjoint :math:`\\bar v = \\partial f / \\partial v` that
    backpropagation accumulates into it.
    """

    label: str
    """
    The name of the node's value, such as ``a`` or ``sum``.
    """

    adjoint: float = 0.0
    """
    The derivative of the graph's output with respect to this node's value.
    """

    @property
    @abstractmethod
    def operands(self) -> list[GraphNode]:
        """
        The nodes whose values this node combines.
        """

    @property
    @abstractmethod
    def value(self) -> float:
        """
        The value the forward pass computes for this node.
        """

    @property
    @abstractmethod
    def local_derivatives(self) -> list[float]:
        """
        The derivative of :attr:`value` with respect to each of :attr:`operands`.
        """

    def nodes_in_evaluation_order(self) -> list[GraphNode]:
        """
        :return: Every node this node depends on, each after its operands, ending with
            this node.
        """
        ordered: list[GraphNode] = []
        for operand in self.operands:
            ordered.extend(
                node
                for node in operand.nodes_in_evaluation_order()
                if node not in ordered
            )
        return [*ordered, self]

    def backpropagate(self) -> list[GraphNode]:
        """
        Set the adjoint of every node in the graph below this output node.

        :return: The nodes in the order the backward pass visits them.
        """
        backward = self.nodes_in_evaluation_order()[::-1]
        for node in backward:
            node.adjoint = 0.0
        self.adjoint = 1.0
        for node in backward:
            for operand, derivative in zip(node.operands, node.local_derivatives):
                operand.adjoint += node.adjoint * derivative
        return backward


@dataclass(kw_only=True, eq=False)
class InputNode(GraphNode):
    """
    A variable of the function, given a value.
    """

    input_value: float
    """
    The value of the variable.
    """

    @property
    def operands(self) -> list[GraphNode]:
        return []

    @property
    def value(self) -> float:
        return self.input_value

    @property
    def local_derivatives(self) -> list[float]:
        return []


@dataclass(kw_only=True, eq=False)
class SumNode(GraphNode):
    """
    The sum of two nodes.
    """

    left: GraphNode
    """
    The first summand.
    """

    right: GraphNode
    """
    The second summand.
    """

    @property
    def operands(self) -> list[GraphNode]:
        return [self.left, self.right]

    @property
    def value(self) -> float:
        return self.left.value + self.right.value

    @property
    def local_derivatives(self) -> list[float]:
        return [1.0, 1.0]


@dataclass(kw_only=True, eq=False)
class ProductNode(GraphNode):
    """
    The product of two nodes.
    """

    left: GraphNode
    """
    The first factor.
    """

    right: GraphNode
    """
    The second factor.
    """

    @property
    def operands(self) -> list[GraphNode]:
        return [self.left, self.right]

    @property
    def value(self) -> float:
        return self.left.value * self.right.value

    @property
    def local_derivatives(self) -> list[float]:
        return [self.right.value, self.left.value]


@dataclass(kw_only=True)
class SumTimesFactorGraph:
    """
    The computational graph of :math:`f(a, b) = (a + b) \\cdot b`, in which :math:`b`
    reaches the output along two paths.
    """

    first_input: float = 2.0
    """
    The value of :math:`a`.
    """

    second_input: float = 3.0
    """
    The value of :math:`b`.
    """

    @cached_property
    def output(self) -> ProductNode:
        """
        The output node :math:`f = \\mathrm{sum} \\cdot b` with :math:`\\mathrm{sum} = a + b`,
        backpropagated.
        """
        first = InputNode(label="a", input_value=self.first_input)
        second = InputNode(label="b", input_value=self.second_input)
        total = SumNode(label="sum", left=first, right=second)
        output = ProductNode(label="f", left=total, right=second)
        output.backpropagate()
        return output

    @property
    def nodes(self) -> dict[str, GraphNode]:
        """
        The nodes of the graph by their label.
        """
        return {node.label: node for node in self.output.nodes_in_evaluation_order()}


# %% maximum likelihood


class GraspOutcome(StrEnum):
    """
    The outcomes of a grasp attempt.
    """

    SUCCESS = "success"
    """
    The object is in the gripper.
    """

    SLIPPED = "slipped"
    """
    The object was lifted but slipped out.
    """

    MISSED = "missed"
    """
    The gripper closed next to the object.
    """


@dataclass(kw_only=True)
class GraspRecord:
    """
    How often each outcome occurred over the logged grasp attempts, and the categorical
    distribution that makes these counts most likely.
    """

    counts: dict[GraspOutcome, int] = field(
        default_factory=lambda: {
            GraspOutcome.SUCCESS: 14,
            GraspOutcome.SLIPPED: 4,
            GraspOutcome.MISSED: 2,
        }
    )
    """
    The number of attempts with each outcome.
    """

    @property
    def attempt_count(self) -> int:
        """
        The number :math:`N` of attempts.
        """
        return sum(self.counts.values())

    @cached_property
    def maximum_likelihood_estimate(self) -> dict[GraspOutcome, float]:
        """
        The probabilities :math:`p` maximizing :math:`\\sum_k n_k \\log p_k` subject to
        :math:`\\sum_k p_k = 1`, solved numerically.
        """
        counts = np.array(list(self.counts.values()), dtype=float)
        result = minimize(
            lambda probabilities: -float(counts @ np.log(probabilities)),
            np.full(len(counts), 1 / len(counts)),
            jac=lambda probabilities: -counts / probabilities,
            constraints=[
                {"type": "eq", "fun": lambda probabilities: np.sum(probabilities) - 1}
            ],
            bounds=[(1e-9, 1)] * len(counts),
            method="SLSQP",
            options={"ftol": 1e-14},
        )
        if not result.success:
            raise SolverFailure(solver="SLSQP", message=result.message)
        return dict(zip(self.counts, result.x))
