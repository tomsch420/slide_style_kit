"""
Render the lecture's animations with manim, each to a video and a poster image.

Run ``python render_animations.py`` for all animations, or name some, such as ``python
render_animations.py simplex convergence``.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import av
from manim import Scene, tempconfig

from animation_catalogue import Animation
from scenes import (
    ComputationalGraphScene,
    ConvexityScene,
    ConvexSetScene,
    ConvergenceScene,
    CriticalPointsScene,
    FeasibleRegionScene,
    GradientBowlScene,
    GradientDescentProblemsScene,
    GradientDescentSurfaceScene,
    IntegerRoundingScene,
    InteriorPointScene,
    LinearProgramSolutionScene,
    OptimizerComparisonScene,
    QuadraticProgramSolutionScene,
    RobotSetupScene,
    SimplexScene,
    StochasticGradientDescentScene,
)

# %% rendering


@dataclass(kw_only=True)
class AnimationRenderer:
    """
    Renders one animation to its video and poster files.
    """

    animation: Animation
    """
    The animation to render.
    """

    frame_height: float = 8.0
    """
    The height of the visible scene, in manim's units.
    """

    @property
    def scene_class(self) -> type[Scene]:
        """
        The manim scene that draws the animation.
        """
        match self.animation:
            case Animation.ROBOT_SETUP:
                return RobotSetupScene
            case Animation.FEASIBLE_REGION:
                return FeasibleRegionScene
            case Animation.LINEAR_PROGRAM_SOLUTION:
                return LinearProgramSolutionScene
            case Animation.SIMPLEX:
                return SimplexScene
            case Animation.INTERIOR_POINT:
                return InteriorPointScene
            case Animation.GRADIENT_BOWL:
                return GradientBowlScene
            case Animation.CRITICAL_POINTS:
                return CriticalPointsScene
            case Animation.GRADIENT_DESCENT_SURFACE:
                return GradientDescentSurfaceScene
            case Animation.CONVERGENCE:
                return ConvergenceScene
            case Animation.GRADIENT_DESCENT_PROBLEMS:
                return GradientDescentProblemsScene
            case Animation.OPTIMIZER_COMPARISON:
                return OptimizerComparisonScene
            case Animation.INTEGER_ROUNDING:
                return IntegerRoundingScene
            case Animation.QUADRATIC_PROGRAM_SOLUTION:
                return QuadraticProgramSolutionScene
            case Animation.CONVEX_SET:
                return ConvexSetScene
            case Animation.CONVEXITY:
                return ConvexityScene
            case Animation.STOCHASTIC_GRADIENT_DESCENT:
                return StochasticGradientDescentScene
            case Animation.COMPUTATIONAL_GRAPH:
                return ComputationalGraphScene

    def render(self) -> None:
        """
        Render the video into :attr:`Animation.movie` and its last frame into
        :attr:`Animation.poster`.
        """
        video_format = self.animation.video_format
        Animation.directory.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory() as media_directory:
            settings = {
                "pixel_width": video_format.width,
                "pixel_height": video_format.height,
                "frame_height": self.frame_height,
                "frame_width": self.frame_height * video_format.aspect_ratio,
                "frame_rate": self.animation.frame_rate,
                "background_color": "#FFFFFF",
                "media_dir": media_directory,
                "output_file": self.animation.value,
                "disable_caching": True,
                "verbosity": "WARNING",
                "progress_bar": "none",
            }
            with tempconfig(settings):
                scene = self.scene_class()
                scene.render()
                shutil.copyfile(
                    scene.renderer.file_writer.movie_file_path, self.animation.movie
                )
        self.write_poster()

    def write_poster(self) -> None:
        """
        Save the last frame of the rendered video as the poster image.
        """
        with av.open(str(self.animation.movie)) as container:
            last_frame = None
            for frame in container.decode(video=0):
                last_frame = frame
        last_frame.to_image().save(self.animation.poster)


# %% command line


def main() -> None:
    """
    Render the animations named on the command line, or all of them.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "animations", nargs="*", type=Animation, choices=list(Animation)
    )
    animations = parser.parse_args().animations or list(Animation)
    for animation in animations:
        print(f"rendering {animation.value} ...", flush=True)
        AnimationRenderer(animation=animation).render()


if __name__ == "__main__":
    main()
