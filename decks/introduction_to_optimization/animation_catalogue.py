"""
The animations of the lecture and the files they are rendered to.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path

from krrood.ormatic.utils import classproperty

# %% video formats


@dataclass(frozen=True)
class VideoFormatSize:
    """
    The size of the frames of a video, in pixels.
    """

    width: int
    """
    The width of every frame.
    """

    height: int
    """
    The height of every frame.
    """


class VideoFormat(VideoFormatSize, Enum):
    """
    The frame sizes the animations are rendered at.
    """

    WIDE = 1280, 800
    """
    16:10, for plots that are wider than tall.
    """

    STANDARD = 1200, 900
    """
    4:3.
    """

    SQUARE = 960, 960
    """
    1:1.
    """

    @property
    def aspect_ratio(self) -> float:
        """
        The width of a frame divided by its height.
        """
        return self.width / self.height


# %% animations


class Animation(StrEnum):
    """
    The animations of the lecture, by the stem of their files.
    """

    FEASIBLE_REGION = "feasible_region"
    """
    The constrained minimum of a parabola.
    """

    LINEAR_PROGRAM_SOLUTION = "linear_program_solution"
    """
    The line of equal gripper speed sweeping to the optimal vertex of the LP.
    """

    SIMPLEX = "simplex"
    """
    The simplex method walking along the edges of the gripper speed LP.
    """

    INTERIOR_POINT = "interior_point"
    """
    The central path of the barrier method through shrinking barrier contours.
    """

    GRADIENT_BOWL = "gradient_bowl"
    """
    Gradients and negative gradients on a convex bowl.
    """

    CRITICAL_POINTS = "critical_points"
    """
    The minima, saddle points and maxima of the peaks function.
    """

    GRADIENT_DESCENT_SURFACE = "gradient_descent_surface"
    """
    Gradient descent sliding from a hillside into a valley.
    """

    CONVERGENCE = "convergence"
    """
    Gradient descent steps shrinking as the gradient vanishes.
    """

    GRADIENT_DESCENT_PROBLEMS = "gradient_descent_problems"
    """
    Gradient descent stuck in a local minimum and crawling over a plateau.
    """

    OPTIMIZER_COMPARISON = "optimizer_comparison"
    """
    Gradient descent, momentum and Adam in a narrow valley.
    """

    QUADRATIC_PROGRAM_SOLUTION = "quadratic_program_solution"
    """
    The cost contours of the velocity QP growing until they touch the feasible region.
    """

    CONVEXITY = "convexity"
    """
    A chord above a convex function and below a non-convex one.
    """

    STOCHASTIC_GRADIENT_DESCENT = "stochastic_gradient_descent"
    """
    Gradient descent and minibatch gradient descent on the loss of a line fit.
    """

    COMPUTATIONAL_GRAPH = "computational_graph"
    """
    The forward and backward pass through the graph of :math:`(a + b) b`.
    """

    @classproperty
    def directory(cls) -> Path:
        """
        The directory the rendered animations are stored in.
        """
        return Path(__file__).parent / "animations"

    @property
    def movie(self) -> Path:
        """
        The rendered video.
        """
        return Animation.directory / f"{self.value}.mp4"

    @property
    def poster(self) -> Path:
        """
        The last frame of the video, for formats that cannot play it.
        """
        return Animation.directory / f"{self.value}.png"

    @property
    def frame_rate(self) -> int:
        """
        The frames per second of the video; lower for the 3D scenes, whose frames are
        slow to draw.
        """
        match self:
            case (
                Animation.GRADIENT_BOWL
                | Animation.CRITICAL_POINTS
                | Animation.GRADIENT_DESCENT_SURFACE
            ):
                return 24
            case _:
                return 30

    @property
    def video_format(self) -> VideoFormat:
        """
        The frame size the animation is rendered at.
        """
        match self:
            case (
                Animation.SIMPLEX
                | Animation.GRADIENT_DESCENT_SURFACE
                | Animation.CONVERGENCE
            ):
                return VideoFormat.SQUARE
            case (
                Animation.FEASIBLE_REGION
                | Animation.CRITICAL_POINTS
                | Animation.OPTIMIZER_COMPARISON
                | Animation.STOCHASTIC_GRADIENT_DESCENT
            ):
                return VideoFormat.STANDARD
            case _:
                return VideoFormat.WIDE
