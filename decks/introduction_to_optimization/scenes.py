"""
The manim scenes of the lecture's animations, drawn from the problems in
:mod:`examples`.
"""

from __future__ import annotations

from enum import StrEnum

import numpy as np
from manim import (
    DEGREES,
    DL,
    DR,
    DOWN,
    LEFT,
    RIGHT,
    UL,
    UP,
    UR,
    Arrow,
    Arrow3D,
    Axes,
    Circle,
    Create,
    DashedLine,
    DashedVMobject,
    DecimalNumber,
    Dot,
    Dot3D,
    FadeIn,
    FadeOut,
    GrowArrow,
    Indicate,
    LaggedStart,
    Line,
    ManimColor,
    MathTex,
    Polygon,
    Rectangle,
    Scene,
    Surface,
    Text,
    ThreeDAxes,
    ThreeDScene,
    Transform,
    ValueTracker,
    VGroup,
    VMobject,
    Write,
    always_redraw,
    config,
    linear,
)

from examples import (
    Adam,
    BarrierObjective,
    BumpyLandscape,
    GradientDescent,
    InteriorPointMethod,
    LevelSet,
    LineFittingLoss,
    LineFittingProblem,
    Momentum,
    MotionCost,
    OneVariableFunction,
    Paraboloid,
    PeaksLandscape,
    SaddleLandscape,
    ShiftedParabola,
    SimplexMethod,
    StochasticGradientDescent,
    StretchedValley,
    SumTimesFactorGraph,
    TwoVariableFunction,
    VelocityControlProblem,
)

# %% style


class PlotColor(StrEnum):
    """
    The colours of the plots, matching the slides.
    """

    INK = "#000000"
    """
    Axes, labels and text.
    """

    STRUCTURE = "#144F78"
    """
    The structure blue of the slides: curves and the first class of samples.
    """

    ALERT = "#8C021F"
    """
    The alert red of the slides: infeasible points and the second class.
    """

    OPTIMUM = "#2E7D32"
    """
    Optimal points.
    """

    PATH = "#C2410C"
    """
    The iterates of an algorithm.
    """

    FEASIBLE = "#DDF0D8"
    """
    The fill of feasible regions.
    """

    INFEASIBLE = "#F6DCE0"
    """
    The fill of infeasible regions.
    """

    CONTOUR = "#7FA7C9"
    """
    Level sets.
    """

    MUTED = "#8A8A8A"
    """
    Context that recedes, such as earlier iterates.
    """

    @property
    def manim_color(self) -> ManimColor:
        """
        The colour as manim takes it.
        """
        return ManimColor(self.value)


class PlotMixin:
    """
    The axes, labels and shapes the 2D scenes share.
    """

    def plot_axes(
        self,
        *,
        x_range: list[float],
        y_range: list[float],
        x_label: str,
        y_label: str,
        margin: float = 0.85,
    ) -> Axes:
        """
        :param x_range: The minimum, maximum and tick step of the horizontal axis.
        :param y_range: The minimum, maximum and tick step of the vertical axis.
        :param x_label: The LaTeX label of the horizontal axis.
        :param y_label: The LaTeX label of the vertical axis.
        :param margin: The free space around the axes, in manim's units.
        :return: Black axes with tick numbers and labels filling the frame.
        """
        axes = Axes(
            x_range=x_range,
            y_range=y_range,
            x_length=config.frame_width - 2 * margin,
            y_length=config.frame_height - 2 * margin,
            tips=False,
            axis_config={"include_numbers": True, "font_size": 26},
        ).shift(0.15 * RIGHT + 0.1 * UP)
        axes.set_color(PlotColor.INK.manim_color)
        labels = axes.get_axis_labels(
            x_label=MathTex(x_label, font_size=34),
            y_label=MathTex(y_label, font_size=34),
        ).set_color(PlotColor.INK.manim_color)
        axes.add(labels)
        return axes

    def caption(self, *, text: str, font_size: float = 30) -> Text:
        """
        :return: *text* at the top of the frame.
        """
        return Text(
            text, font="Liberation Sans", font_size=font_size, color=PlotColor.INK.value
        ).to_edge(UP, buff=0.25)

    def note(self, *, text: str, font_size: float = 24) -> Text:
        """
        :return: *text* in the slides' font, ready to be placed.
        """
        return Text(
            text, font="Liberation Sans", font_size=font_size, color=PlotColor.INK.value
        )

    def polyline(
        self, *, axes: Axes, points: np.ndarray, color: PlotColor, width: float = 3
    ) -> VMobject:
        """
        :return: The points joined by straight segments, in the coordinates of *axes*.
        """
        line = VMobject(stroke_color=color.manim_color, stroke_width=width)
        line.set_points_as_corners([axes.c2p(*point) for point in points])
        return line

    def level_set_curves(
        self,
        *,
        axes: Axes,
        level_sets: list[LevelSet],
        color: PlotColor,
        width: float = 2,
    ) -> VGroup:
        """
        :return: Every curve of every level set, in the coordinates of *axes*.
        """
        return VGroup(
            *[
                self.polyline(axes=axes, points=curve, color=color, width=width)
                for level_set in level_sets
                for curve in level_set.curves
                if len(curve) > 1
            ]
        )

    def clipped_line(
        self,
        *,
        axes: Axes,
        normal: np.ndarray,
        bound: float,
        color: PlotColor,
        width: float = 3,
    ) -> Line | None:
        """
        :return: The part of the line :math:`a \\cdot x = b` inside the axes, or
            ``None`` when the line misses them.
        """
        (x_minimum, x_maximum), (y_minimum, y_maximum) = (
            axes.x_range[:2],
            axes.y_range[:2],
        )
        candidates = []
        if abs(normal[1]) > 1e-12:
            for x in (x_minimum, x_maximum):
                candidates.append((x, (bound - normal[0] * x) / normal[1]))
        if abs(normal[0]) > 1e-12:
            for y in (y_minimum, y_maximum):
                candidates.append(((bound - normal[1] * y) / normal[0], y))
        inside = [
            point
            for point in candidates
            if x_minimum - 1e-9 <= point[0] <= x_maximum + 1e-9
            and y_minimum - 1e-9 <= point[1] <= y_maximum + 1e-9
        ]
        if len(inside) < 2:
            return None
        start, end = min(inside), max(inside)
        return Line(
            axes.c2p(*start),
            axes.c2p(*end),
            color=color.manim_color,
            stroke_width=width,
        )


class VelocityPlotMixin(PlotMixin):
    """
    The plot of the velocity control example's feasible region the LP and QP scenes
    share.
    """

    def velocity_axes(self) -> Axes:
        """
        :return: The axes of the base and arm velocities.
        """
        return self.plot_axes(
            x_range=[0, 12, 2],
            y_range=[0, 30, 5],
            x_label=r"x_1\ \text{(base)}",
            y_label=r"x_2\ \text{(arm)}",
        )

    def constraint_lines(
        self, *, axes: Axes, problem: VelocityControlProblem
    ) -> list[tuple[Line, MathTex]]:
        """
        :return: The boundary and the LaTeX label of every constraint with a positive
            bound.
        """
        labels = [r"x_1 \le 10", r"x_2 \le 25", r"x_1 + \tfrac{1}{2} x_2 \le 15"]
        rows = np.flatnonzero(problem.constraint_bounds > 0)
        lines = []
        for row, label in zip(rows, labels):
            line = self.clipped_line(
                axes=axes,
                normal=problem.constraint_matrix[row],
                bound=problem.constraint_bounds[row],
                color=PlotColor.STRUCTURE,
            )
            tag = MathTex(label, font_size=28, color=PlotColor.STRUCTURE.value)
            lines.append((line, tag))
        return lines

    def feasible_polygon(
        self, *, axes: Axes, problem: VelocityControlProblem
    ) -> Polygon:
        """
        :return: The feasible region of *problem*, filled.
        """
        return Polygon(
            *[axes.c2p(*vertex) for vertex in problem.feasible_vertices],
            fill_color=PlotColor.FEASIBLE.manim_color,
            fill_opacity=0.8,
            stroke_width=0,
        )

    def draw_feasible_region(
        self, *, axes: Axes, problem: VelocityControlProblem
    ) -> None:
        """
        Draw the axes, then each constraint with its label, then the feasible region.
        """
        self.play(Create(axes), run_time=1.2)
        positions = [(11.0, 8.0), (5.0, 26.6), (7.2, 10.5)]
        for (line, tag), position in zip(
            self.constraint_lines(axes=axes, problem=problem), positions
        ):
            tag.move_to(axes.c2p(*position)).set_z_index(3)
            tag.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.85)
            self.play(Create(line), FadeIn(tag), run_time=0.8)
        region = self.feasible_polygon(axes=axes, problem=problem).set_z_index(-1)
        self.play(FadeIn(region), run_time=0.8)

    def speed_text(self, *, value: float) -> str:
        """
        :return: *value* in cm/s with as many decimals as it needs.
        """
        return f"{value:.4g}"


# %% introduction


class FeasibleRegionScene(PlotMixin, Scene):
    """
    The minimum of :math:`f(x) = x^2` moves to the boundary once the constraint
    :math:`x \\ge 1` excludes it.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        axes = self.plot_axes(
            x_range=[-2, 2, 0.5], y_range=[0, 4, 1], x_label="x", y_label="f(x)"
        )
        curve = axes.plot(
            lambda x: x**2, x_range=[-2, 2], color=PlotColor.STRUCTURE.value
        )
        self.play(Create(axes), run_time=1)
        self.play(Create(curve), run_time=1.2)
        position = ValueTracker(-1.6)
        dot = always_redraw(
            lambda: Dot(
                axes.c2p(position.get_value(), position.get_value() ** 2),
                color=PlotColor.PATH.value,
                radius=0.1,
            )
        )
        self.play(FadeIn(dot))
        self.play(position.animate.set_value(0), run_time=1.5)
        unconstrained = self.note(text="unconstrained minimum").next_to(
            axes.c2p(0, 0), UP, buff=0.45
        )
        self.play(FadeIn(unconstrained))
        boundary = DashedLine(
            axes.c2p(1, 0), axes.c2p(1, 4), color=PlotColor.INK.value, dash_length=0.12
        )
        infeasible = Rectangle(
            width=axes.c2p(1, 0)[0] - axes.c2p(-2, 0)[0],
            height=axes.c2p(0, 4)[1] - axes.c2p(0, 0)[1],
            fill_color=PlotColor.INFEASIBLE.manim_color,
            fill_opacity=0.9,
            stroke_width=0,
        ).move_to((axes.c2p(-2, 0) + axes.c2p(1, 4)) / 2)
        infeasible.set_z_index(-1)
        constraint = MathTex(
            r"x \ge 1", font_size=34, color=PlotColor.INK.value
        ).next_to(axes.c2p(1, 4), DOWN + RIGHT, buff=0.15)
        excluded = self.note(text="infeasible", font_size=28).set_color(
            PlotColor.ALERT.value
        )
        excluded.move_to(axes.c2p(-0.5, 3.4))
        self.play(Create(boundary), FadeIn(constraint), run_time=0.8)
        self.play(
            FadeIn(infeasible), FadeIn(excluded), FadeOut(unconstrained), run_time=1
        )
        self.play(position.animate.set_value(1), run_time=1.5)
        optimum = Dot(axes.c2p(1, 1), color=PlotColor.OPTIMUM.value, radius=0.12)
        label = self.note(text="constrained\noptimum").next_to(
            optimum, RIGHT, buff=0.25
        )
        self.play(FadeIn(optimum), FadeIn(label), FadeOut(dot))
        self.wait(1.5)


# %% linear programs


class LinearProgramSolutionScene(VelocityPlotMixin, Scene):
    """
    The line of equal gripper speed moves parallel until it last touches the feasible
    region, at the optimal vertex.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        problem = VelocityControlProblem()
        axes = self.velocity_axes()
        self.draw_feasible_region(axes=axes, problem=problem)
        optimum = problem.linear_optimum
        speed = ValueTracker(0)
        objective = always_redraw(
            lambda: (
                self.clipped_line(
                    axes=axes,
                    normal=problem.gripper_jacobian,
                    bound=max(speed.get_value(), 1e-6),
                    color=PlotColor.PATH,
                    width=4,
                )
                or VMobject()
            )
        )
        readout = VGroup(
            MathTex(r"v = x_1 + x_2 =", font_size=32, color=PlotColor.INK.value),
            DecimalNumber(
                0,
                num_decimal_places=1,
                group_with_commas=False,
                font_size=32,
                color=PlotColor.INK.value,
            ),
        ).arrange(RIGHT)
        readout.to_corner(UR, buff=0.4).shift(0.6 * DOWN)
        readout.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        readout[2].add_updater(lambda number: number.set_value(speed.get_value()))
        self.add(objective)
        self.play(FadeIn(readout))
        for level in range(5, int(optimum.value), 5):
            self.play(speed.animate.set_value(level), run_time=0.45, rate_func=linear)
            self.add(
                self.clipped_line(
                    axes=axes,
                    normal=problem.gripper_jacobian,
                    bound=level,
                    color=PlotColor.CONTOUR,
                    width=2,
                )
            )
        self.play(
            speed.animate.set_value(optimum.value), run_time=0.6, rate_func=linear
        )
        point = Dot(
            axes.c2p(*optimum.point), color=PlotColor.OPTIMUM.value, radius=0.12
        )
        first, second = optimum.point
        label = MathTex(
            rf"x^* = ({self.speed_text(value=first)}, "
            rf"{self.speed_text(value=second)}),\ "
            rf"v = {self.speed_text(value=optimum.value)}",
            font_size=32,
            color=PlotColor.OPTIMUM.value,
        ).next_to(point, DOWN + RIGHT, buff=0.3)
        label.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        self.play(FadeIn(point, scale=2), Write(label))
        self.wait(2)


class SimplexScene(VelocityPlotMixin, Scene):
    """
    The simplex method on the gripper speed LP: from standing still along the edges to
    the optimal vertex, the speed growing with every pivot.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        problem = VelocityControlProblem()
        axes = self.velocity_axes()
        self.draw_feasible_region(axes=axes, problem=problem)
        vertices = SimplexMethod(problem=problem).vertices
        captions = ["Initialization"] + [
            f"Pivot {index}" for index in range(1, len(vertices) - 1)
        ]
        captions.append("Optimal Solution")
        title = self.caption(text=captions[0]).shift(1.4 * RIGHT)
        dot = Dot(axes.c2p(*vertices[0]), color=PlotColor.PATH.value, radius=0.12)
        readout = self.speed_readout(problem=problem, vertex=vertices[0])
        self.play(FadeIn(title), FadeIn(dot), FadeIn(readout))
        self.wait(0.6)
        for index in range(1, len(vertices)):
            edge = Arrow(
                axes.c2p(*vertices[index - 1]),
                axes.c2p(*vertices[index]),
                buff=0.12,
                color=PlotColor.PATH.value,
                stroke_width=5,
                max_tip_length_to_length_ratio=0.12,
            )
            is_last = index == len(vertices) - 1
            self.play(GrowArrow(edge), run_time=1)
            self.play(
                dot.animate.move_to(axes.c2p(*vertices[index])).set_color(
                    PlotColor.OPTIMUM.value if is_last else PlotColor.PATH.value
                ),
                Transform(title, self.caption(text=captions[index]).shift(1.4 * RIGHT)),
                Transform(
                    readout,
                    self.speed_readout(problem=problem, vertex=vertices[index]),
                ),
                run_time=0.9,
            )
            self.wait(0.5)
        self.play(Indicate(dot, color=PlotColor.OPTIMUM.value, scale_factor=1.6))
        self.wait(1.5)

    def speed_readout(
        self, *, problem: VelocityControlProblem, vertex: np.ndarray
    ) -> MathTex:
        """
        :return: The vertex and its gripper speed, in the top right corner.
        """
        speed = float(problem.gripper_speed(points=vertex))
        readout = (
            MathTex(
                rf"x = ({self.speed_text(value=vertex[0])}, "
                rf"{self.speed_text(value=vertex[1])}),\ "
                rf"v = {self.speed_text(value=speed)}",
                font_size=32,
                color=PlotColor.INK.value,
            )
            .to_corner(UR, buff=0.35)
            .shift(0.55 * DOWN)
        )
        readout.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        return readout


class InteriorPointScene(VelocityPlotMixin, Scene):
    """
    The barrier method: as the barrier weakens, its contours shrink towards the optimal
    vertex and the central path follows them from the inside.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        problem = VelocityControlProblem()
        method = InteriorPointMethod(problem=problem)
        axes = self.velocity_axes()
        self.draw_feasible_region(axes=axes, problem=problem)
        path = method.central_path
        shown_steps = [0, 6, 11, 15, 19, 23, len(path) - 1]
        sharpnesses = [0.0, *method.sharpnesses]
        contours = self.barrier_contours(
            axes=axes, problem=problem, sharpness=sharpnesses[0], center=path[0]
        )
        readout = self.sharpness_readout(sharpness=sharpnesses[0])
        dot = Dot(axes.c2p(*path[0]), color=PlotColor.PATH.value, radius=0.1)
        self.play(Create(contours), FadeIn(readout), FadeIn(dot), run_time=1.5)
        for previous, step in zip(shown_steps, shown_steps[1:]):
            trace = self.polyline(
                axes=axes,
                points=path[previous : step + 1],
                color=PlotColor.PATH,
                width=4,
            )
            self.play(
                Transform(
                    contours,
                    self.barrier_contours(
                        axes=axes,
                        problem=problem,
                        sharpness=sharpnesses[step],
                        center=path[step],
                    ),
                ),
                Create(trace),
                dot.animate.move_to(axes.c2p(*path[step])),
                Transform(readout, self.sharpness_readout(sharpness=sharpnesses[step])),
                run_time=1.1,
            )
        optimum = Dot(
            axes.c2p(*problem.linear_optimum.point),
            color=PlotColor.OPTIMUM.value,
            radius=0.13,
        )
        self.play(FadeIn(optimum, scale=2), FadeOut(dot))
        self.wait(1.5)

    def barrier_contours(
        self,
        *,
        axes: Axes,
        problem: VelocityControlProblem,
        sharpness: float,
        center: np.ndarray,
    ) -> VGroup:
        """
        :param center: The minimizer of the barrier objective.
        :return: Dashed level sets of the barrier objective around its minimum.
        """
        barrier = BarrierObjective(problem=problem, sharpness=sharpness)
        lowest = float(barrier.evaluate(points=center))
        level_sets = LevelSet.from_grid(
            function=barrier,
            horizontal_range=(0, 12),
            vertical_range=(0, 30),
            levels=[lowest + offset for offset in (0.4, 1.2, 2.5, 4.5)],
            resolution=260,
        )
        curves = self.level_set_curves(
            axes=axes, level_sets=level_sets, color=PlotColor.INK, width=2
        )
        return VGroup(*[DashedVMobject(curve, num_dashes=40) for curve in curves])

    def sharpness_readout(self, *, sharpness: float) -> MathTex:
        """
        :return: The weight of the objective, in the top right corner.
        """
        readout = (
            MathTex(rf"t = {sharpness:.2f}", font_size=34, color=PlotColor.INK.value)
            .to_corner(UR, buff=0.35)
            .shift(0.55 * DOWN)
        )
        readout.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        return readout


# %% unconstrained optimization in 3D


class SurfaceMixin:
    """
    The 3D axes and surfaces the 3D scenes share.
    """

    def surface(
        self,
        *,
        axes: ThreeDAxes,
        function: TwoVariableFunction,
        domain: tuple[float, float],
        height_scale: float = 1.0,
        resolution: int = 32,
    ) -> Surface:
        """
        :return: The graph of *function* over the square *domain*, coloured by height
            from blue through green and yellow to red.
        """
        surface = Surface(
            lambda u, v: axes.c2p(
                u, v, height_scale * float(function.evaluate(points=np.array([u, v])))
            ),
            u_range=list(domain),
            v_range=list(domain),
            resolution=(resolution, resolution),
            fill_opacity=0.9,
            stroke_width=0.3,
            stroke_color=ManimColor("#FFFFFF"),
        )
        heights = [axes.z_range[0], axes.z_range[1]]
        surface.set_fill_by_value(
            axes=axes,
            colorscale=[
                (ManimColor("#1F4E9C"), heights[0]),
                (ManimColor("#3FA34D"), heights[0] + 0.45 * (heights[1] - heights[0])),
                (ManimColor("#F2C230"), heights[0] + 0.7 * (heights[1] - heights[0])),
                (ManimColor("#C0392B"), heights[1]),
            ],
            axis=2,
        )
        return surface

    def surface_point(
        self,
        *,
        axes: ThreeDAxes,
        function: TwoVariableFunction,
        point: np.ndarray,
        height_scale: float = 1.0,
        lift: float = 0.0,
    ) -> np.ndarray:
        """
        :return: The scene position of the graph above *point*, raised by *lift*.
        """
        height = height_scale * float(function.evaluate(points=np.asarray(point)))
        return axes.c2p(point[0], point[1], height + lift)


class GradientBowlScene(SurfaceMixin, ThreeDScene):
    """
    The gradient of a convex bowl points uphill; its negative points to the minimum.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = Paraboloid()
        axes = ThreeDAxes(
            x_range=[-2, 2, 1],
            y_range=[-2, 2, 1],
            z_range=[0, 8, 2],
            x_length=6,
            y_length=6,
            z_length=4,
        ).set_color(PlotColor.INK.manim_color)
        self.set_camera_orientation(phi=68 * DEGREES, theta=-55 * DEGREES, zoom=0.62)
        surface = self.surface(
            axes=axes, function=function, domain=(-2, 2), resolution=22
        ).set_fill(opacity=0.55)
        self.play(Create(axes), run_time=1)
        self.play(FadeIn(surface), run_time=1.5)
        self.begin_ambient_camera_rotation(rate=0.12)
        points = [np.array([1.2, 0.8]), np.array([-1.3, 0.9]), np.array([0.4, -1.4])]
        legend = VGroup(
            MathTex(r"\nabla f(x)", font_size=36, color=PlotColor.ALERT.value),
            MathTex(r"-\nabla f(x)", font_size=36, color=PlotColor.STRUCTURE.value),
        ).arrange(DOWN, aligned_edge=LEFT)
        legend.to_corner(UL, buff=0.4)
        self.add_fixed_in_frame_mobjects(legend)
        self.play(FadeIn(legend))
        for point in points:
            gradient = function.gradient(point=point)
            direction = 0.6 * gradient / np.linalg.norm(gradient)
            on_surface = self.surface_point(axes=axes, function=function, point=point)
            dot = Dot3D(on_surface, color=PlotColor.INK.value, radius=0.07)
            base = axes.c2p(point[0], point[1], 0)
            uphill = Arrow3D(
                base,
                axes.c2p(*(point + direction), 0),
                color=PlotColor.ALERT.value,
            )
            downhill = Arrow3D(
                base,
                axes.c2p(*(point - direction), 0),
                color=PlotColor.STRUCTURE.value,
            )
            drop = DashedLine(on_surface, base, color=PlotColor.MUTED.value)
            self.play(FadeIn(dot), Create(drop), run_time=0.6)
            self.play(Create(uphill), Create(downhill), run_time=1)
        self.wait(2.5)
        self.stop_ambient_camera_rotation()


class CriticalPointsScene(SurfaceMixin, ThreeDScene):
    """
    The critical points of the peaks function, where the gradient vanishes: minima,
    saddle points and maxima.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = PeaksLandscape()
        scale = 0.25
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-2, 2.2, 1],
            x_length=6.5,
            y_length=6.5,
            z_length=3.6,
        ).set_color(PlotColor.INK.manim_color)
        self.set_camera_orientation(phi=48 * DEGREES, theta=-70 * DEGREES, zoom=0.85)
        surface = self.surface(
            axes=axes,
            function=function,
            domain=(-3, 3),
            height_scale=scale,
            resolution=26,
        )
        self.play(FadeIn(surface), run_time=1.5)
        self.begin_ambient_camera_rotation(rate=0.1)
        points = function.critical_points()
        lowest = min(points, key=lambda point: point.value)
        kinds = [
            ("minimum", PlotColor.STRUCTURE, lambda point: point.is_minimum),
            ("saddle point", PlotColor.PATH, lambda point: point.is_saddle),
            (
                "maximum",
                PlotColor.ALERT,
                lambda point: not point.is_minimum and not point.is_saddle,
            ),
        ]
        legend = VGroup()
        for name, color, belongs in kinds:
            dots = VGroup(
                *[
                    Dot3D(
                        self.surface_point(
                            axes=axes,
                            function=function,
                            point=point.position,
                            height_scale=scale,
                            lift=0.15,
                        ),
                        color=color.value,
                        radius=0.13,
                    )
                    for point in points
                    if belongs(point)
                ]
            )
            entry = VGroup(
                Dot(color=color.value, radius=0.1),
                Text(
                    name,
                    font="Liberation Sans",
                    font_size=26,
                    color=PlotColor.INK.value,
                ),
            ).arrange(RIGHT, buff=0.2)
            legend.add(entry)
            legend.arrange(DOWN, aligned_edge=LEFT).to_corner(UL, buff=0.4)
            self.add_fixed_in_frame_mobjects(entry)
            self.play(
                LaggedStart(*[FadeIn(dot, scale=2) for dot in dots]), FadeIn(entry)
            )
        note = MathTex(
            r"\nabla f(x^\star) = 0", font_size=40, color=PlotColor.INK.value
        )
        note.to_corner(UR, buff=0.4)
        self.add_fixed_in_frame_mobjects(note)
        self.play(Write(note))
        highlight = Dot3D(
            self.surface_point(
                axes=axes,
                function=function,
                point=lowest.position,
                height_scale=scale,
                lift=0.3,
            ),
            color=PlotColor.OPTIMUM.value,
            radius=0.18,
        )
        label = Text(
            "global minimum",
            font="Liberation Sans",
            font_size=26,
            color=PlotColor.OPTIMUM.value,
        ).next_to(legend, DOWN, aligned_edge=LEFT, buff=0.3)
        self.add_fixed_in_frame_mobjects(label)
        self.play(FadeIn(highlight, scale=2), FadeIn(label))
        self.wait(2.5)
        self.stop_ambient_camera_rotation()


class GradientDescentSurfaceScene(SurfaceMixin, ThreeDScene):
    """
    Gradient descent slides from a hillside into the nearest valley, each step against
    the gradient.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = SaddleLandscape()
        scale = 4.0
        axes = ThreeDAxes(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
            z_range=[-1.6, 1.6, 0.5],
            x_length=6.5,
            y_length=6.5,
            z_length=3.2,
        ).set_color(PlotColor.INK.manim_color)
        self.set_camera_orientation(phi=60 * DEGREES, theta=-35 * DEGREES, zoom=0.72)
        surface = self.surface(
            axes=axes,
            function=function,
            domain=(-3, 3),
            height_scale=scale,
            resolution=26,
        )
        self.play(FadeIn(surface), run_time=1.5)
        iterates = GradientDescent(learning_rate=0.4).iterates(
            function=function, start=np.array([1.3, 0.25]), iterations=40
        )
        positions = [
            self.surface_point(
                axes=axes, function=function, point=point, height_scale=scale, lift=0.15
            )
            for point in iterates
        ]
        update = MathTex(
            r"x_{k+1} = x_k - \alpha \nabla f(x_k)",
            font_size=38,
            color=PlotColor.INK.value,
        ).to_corner(UL, buff=0.4)
        self.add_fixed_in_frame_mobjects(update)
        self.play(Write(update))
        self.begin_ambient_camera_rotation(rate=0.08)
        dot = Dot3D(positions[0], color=PlotColor.INK.value, radius=0.1)
        self.play(FadeIn(dot, scale=2))
        path = VMobject(stroke_color=PlotColor.INK.manim_color, stroke_width=5)
        path.set_points_as_corners(positions)
        self.play(Create(path), run_time=3, rate_func=linear)
        self.play(dot.animate.move_to(positions[-1]), run_time=0.6)
        self.play(Indicate(dot, color=PlotColor.OPTIMUM.value, scale_factor=1.8))
        self.wait(2)
        self.stop_ambient_camera_rotation()


# %% unconstrained optimization in 2D


class ConvergenceScene(PlotMixin, Scene):
    """
    Gradient descent on a parabola: big steps where the slope is steep, ever smaller
    steps as the gradient vanishes at the minimum.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = ShiftedParabola()
        iterates = function.descent_iterates(start=0.3, learning_rate=0.9, iterations=8)
        axes = self.plot_axes(
            x_range=[0, 8, 1], y_range=[0, 5, 1], x_label="x", y_label="f(x)"
        )
        curve = axes.plot(
            lambda x: float(function.evaluate(x=np.array(x))),
            x_range=[0, 8],
            color=PlotColor.STRUCTURE.value,
        )
        self.play(Create(axes), Create(curve), run_time=1.5)
        readout = self.gradient_readout(function=function, x=iterates[0])
        dots = VGroup()
        for index, x in enumerate(iterates):
            point = axes.c2p(x, float(function.evaluate(x=np.array(x))))
            dot = Dot(point, color=PlotColor.PATH.value, radius=0.09)
            tick = Line(
                axes.c2p(x, 0) + 0.12 * UP,
                axes.c2p(x, 0) + 0.12 * DOWN,
                color=PlotColor.PATH.value,
                stroke_width=3,
            )
            if index == 0:
                self.play(FadeIn(dot, scale=2), Create(tick), FadeIn(readout))
            else:
                previous = dots[-1].get_center()
                step = Arrow(
                    previous,
                    point,
                    buff=0.08,
                    color=PlotColor.PATH.value,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.25,
                    path_arc=-0.6,
                )
                self.play(
                    GrowArrow(step),
                    FadeIn(dot),
                    Create(tick),
                    Transform(readout, self.gradient_readout(function=function, x=x)),
                    run_time=0.8,
                )
            dots.add(dot)
        self.play(Indicate(dots[-1], color=PlotColor.OPTIMUM.value, scale_factor=1.8))
        self.wait(1.5)

    def gradient_readout(self, *, function: ShiftedParabola, x: float) -> MathTex:
        """
        :return: The magnitude of the gradient at *x*, in the top right corner.
        """
        readout = MathTex(
            rf"\|\nabla f(x_k)\| = {abs(function.derivative(x=x)):.3f}",
            font_size=34,
            color=PlotColor.INK.value,
        ).to_corner(UR, buff=0.4)
        readout.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        return readout


class GradientDescentProblemsScene(PlotMixin, Scene):
    """
    Two runs of gradient descent on a bumpy cost: one is trapped in a local minimum, the
    other barely moves on a plateau, both missing the global minimum.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = BumpyLandscape()
        axes = self.plot_axes(
            x_range=[0, 10, 1],
            y_range=[0, 2.2, 0.5],
            x_label=r"\text{parameter}",
            y_label=r"\text{cost}",
        )
        curve = axes.plot(
            lambda x: float(function.evaluate(x=np.array(x))),
            x_range=[0, 10],
            color=PlotColor.STRUCTURE.value,
        )
        self.play(Create(axes), Create(curve), run_time=1.5)
        global_minimum = 3.6
        marker = Dot(
            axes.c2p(
                global_minimum, float(function.evaluate(x=np.array(global_minimum)))
            ),
            color=PlotColor.OPTIMUM.value,
            radius=0.1,
        )
        self.play(
            FadeIn(marker),
            FadeIn(
                self.note(text="global minimum")
                .set_color(PlotColor.OPTIMUM.value)
                .next_to(marker, DOWN, buff=0.25)
            ),
        )
        runs = [
            (
                function.descent_iterates(start=0.4, learning_rate=0.08, iterations=60),
                "local minimum",
            ),
            (
                function.descent_iterates(start=9.2, learning_rate=0.08, iterations=60),
                "plateau",
            ),
        ]
        progress = ValueTracker(0)
        balls = [
            always_redraw(
                lambda iterates=iterates: Dot(
                    axes.c2p(
                        *self.interpolated(
                            function=function,
                            iterates=iterates,
                            progress=progress.get_value(),
                        )
                    ),
                    color=PlotColor.PATH.value,
                    radius=0.12,
                )
            )
            for iterates, _ in runs
        ]
        self.play(*[FadeIn(ball) for ball in balls])
        self.play(progress.animate.set_value(60), run_time=6, rate_func=linear)
        for iterates, name in runs:
            final = iterates[-1]
            slope = abs(function.derivative(x=final))
            label = self.note(
                text=f"stuck: {name}\n|f\u2032(x)| = {slope:.3f}", font_size=22
            ).set_color(PlotColor.ALERT.value)
            label.next_to(
                axes.c2p(final, float(function.evaluate(x=np.array(final)))),
                UP,
                buff=0.35,
            )
            self.play(FadeIn(label), run_time=0.6)
        self.wait(1.5)

    def interpolated(
        self, *, function: BumpyLandscape, iterates: np.ndarray, progress: float
    ) -> tuple[float, float]:
        """
        :return: The point on the curve between the iterates around *progress*.
        """
        index = min(int(progress), len(iterates) - 2)
        fraction = progress - index
        x = (1 - fraction) * iterates[index] + fraction * iterates[index + 1]
        return x, float(function.evaluate(x=np.array(x)))


class OptimizerComparisonScene(PlotMixin, Scene):
    """
    Gradient descent zig-zags down a narrow valley; momentum and Adam take a straighter
    route to the minimum.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        function = StretchedValley()
        axes = self.plot_axes(
            x_range=[-10, 2, 2], y_range=[-3, 3, 1], x_label="x_1", y_label="x_2"
        )
        levels = [0.5 * 2**exponent for exponent in range(0, 8)]
        contours = self.level_set_curves(
            axes=axes,
            level_sets=LevelSet.from_grid(
                function=function,
                horizontal_range=(-10, 2),
                vertical_range=(-3, 3),
                levels=levels,
            ),
            color=PlotColor.CONTOUR,
        )
        self.play(Create(axes), Create(contours), run_time=1.5)
        start = np.array([-9.0, 2.5])
        methods = [
            ("gradient descent", PlotColor.ALERT, GradientDescent(learning_rate=0.09)),
            ("momentum", PlotColor.PATH, Momentum(learning_rate=0.03)),
            ("Adam", PlotColor.STRUCTURE, Adam(learning_rate=0.3)),
        ]
        legend = VGroup(
            *[
                VGroup(
                    Line(0.3 * LEFT, 0.3 * RIGHT, color=color.value, stroke_width=5),
                    self.note(text=name, font_size=26),
                ).arrange(RIGHT, buff=0.2)
                for name, color, _ in methods
            ]
        ).arrange(DOWN, aligned_edge=LEFT)
        legend.to_corner(DL, buff=0.35).shift(1.1 * RIGHT + 0.5 * UP)
        legend.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        self.play(FadeIn(legend))
        paths = [
            self.polyline(
                axes=axes,
                points=method.iterates(function=function, start=start, iterations=60),
                color=color,
                width=3.5,
            )
            for _, color, method in methods
        ]
        self.play(
            FadeIn(Dot(axes.c2p(*start), color=PlotColor.INK.value, radius=0.09)),
            FadeIn(Dot(axes.c2p(0, 0), color=PlotColor.OPTIMUM.value, radius=0.11)),
        )
        self.play(*[Create(path) for path in paths], run_time=6, rate_func=linear)
        self.wait(1.5)


# %% quadratic programs


class QuadraticProgramSolutionScene(VelocityPlotMixin, Scene):
    """
    The contours of the motion cost grow from the unconstrained minimum until one
    touches the feasible region, at the constrained optimum on the elbow's edge.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        problem = VelocityControlProblem()
        axes = self.velocity_axes()
        self.draw_feasible_region(axes=axes, problem=problem)
        unconstrained = problem.unconstrained_minimum
        optimum = problem.quadratic_optimum
        linear_optimum = problem.linear_optimum
        comparison = Dot(
            axes.c2p(*linear_optimum.point), color=PlotColor.MUTED.value, radius=0.1
        )
        comparison_label = (
            self.note(text="LP optimum", font_size=24)
            .set_color(PlotColor.MUTED.value)
            .next_to(comparison, LEFT, buff=0.2)
        )
        self.play(FadeIn(comparison), FadeIn(comparison_label))
        center = Dot(
            axes.c2p(*unconstrained.point), color=PlotColor.INK.value, radius=0.09
        )
        center_label = self.note(text="unconstrained\nminimum", font_size=22).next_to(
            center, DOWN, buff=0.2
        )
        center_label.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        center_label.set_z_index(3)
        self.play(FadeIn(center), FadeIn(center_label))
        cost = MotionCost(problem=problem)
        increase = optimum.value - unconstrained.value
        for fraction in (0.15, 0.35, 0.6, 0.85, 1.0):
            touching = fraction == 1.0
            curves = self.level_set_curves(
                axes=axes,
                level_sets=LevelSet.from_grid(
                    function=cost,
                    horizontal_range=(0, 12),
                    vertical_range=(0, 30),
                    levels=[unconstrained.value + fraction * increase],
                    resolution=300,
                ),
                color=PlotColor.PATH if touching else PlotColor.CONTOUR,
                width=4 if touching else 2,
            )
            self.play(Create(curves), run_time=0.8)
        point = Dot(
            axes.c2p(*optimum.point), color=PlotColor.OPTIMUM.value, radius=0.12
        )
        first, second = optimum.point
        label = MathTex(
            rf"x^* = ({self.speed_text(value=first)}, "
            rf"{self.speed_text(value=second)})",
            font_size=32,
            color=PlotColor.OPTIMUM.value,
        ).next_to(point, DOWN + RIGHT, buff=0.3)
        label.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        self.play(FadeIn(point, scale=2), Write(label))
        self.wait(2)


# %% convexity


class ConvexityScene(PlotMixin, Scene):
    """
    A chord sweeping over a convex function always stays above the graph; over a non-
    convex function it dips below the bump between two minima.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        width = config.frame_width / 2 - 0.9
        height = config.frame_height - 2.4
        examples = [
            (ShiftedParabola(), [0, 8, 2], [0, 5, 1], "convex", (1.0, 7.0), (2.5, 5.5)),
            (
                BumpyLandscape(),
                [0, 6, 1],
                [0, 2.2, 0.5],
                "not convex",
                (0.4, 2.0),
                (1.2, 3.6),
            ),
        ]
        for column, (function, x_range, y_range, title, start, end) in enumerate(
            examples
        ):
            axes = Axes(
                x_range=x_range,
                y_range=y_range,
                x_length=width,
                y_length=height,
                tips=False,
                axis_config={"include_numbers": True, "font_size": 22},
            ).set_color(PlotColor.INK.manim_color)
            axes.move_to((column - 0.5) * config.frame_width / 2 * RIGHT + 0.3 * DOWN)
            heading = self.note(text=title, font_size=30).next_to(axes, UP, buff=0.3)
            curve = axes.plot(
                lambda x, function=function: float(function.evaluate(x=np.array(x))),
                x_range=x_range[:2],
                color=PlotColor.STRUCTURE.value,
            )
            self.play(Create(axes), FadeIn(heading), Create(curve), run_time=1.2)
            left, right = ValueTracker(start[0]), ValueTracker(start[1])
            chord = always_redraw(
                lambda axes=axes, function=function, left=left, right=right: self.chord(
                    axes=axes,
                    function=function,
                    left=left.get_value(),
                    right=right.get_value(),
                )
            )
            self.play(FadeIn(chord))
            self.play(
                left.animate.set_value(end[0]),
                right.animate.set_value(end[1]),
                run_time=2.5,
            )
            if column == 1:
                middle = (end[0] + end[1]) / 2
                warning = (
                    self.note(text="chord below the graph", font_size=24)
                    .set_color(PlotColor.ALERT.value)
                    .next_to(
                        axes.c2p(middle, float(function.evaluate(x=np.array(middle)))),
                        UP,
                        buff=0.3,
                    )
                )
                self.play(FadeIn(warning))
        self.wait(2)

    def chord(
        self, *, axes: Axes, function: OneVariableFunction, left: float, right: float
    ) -> VGroup:
        """
        :return: The segment between the graph points above *left* and *right*, with
            its end points.
        """
        ends = [
            axes.c2p(x, float(function.evaluate(x=np.array(x)))) for x in (left, right)
        ]
        return VGroup(
            Line(*ends, color=PlotColor.PATH.value, stroke_width=4),
            *[Dot(end, color=PlotColor.PATH.value, radius=0.08) for end in ends],
        )


class ConvexSetScene(PlotMixin, Scene):
    """
    The segment between two points of a convex set stays inside it as the points move;
    in a non-convex set it leaves the set.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        panel_size = min(config.frame_width / 2 - 1.2, config.frame_height - 2.2)
        robot = VelocityControlProblem()
        robot_vertices = robot.feasible_vertices / robot.feasible_vertices.max(axis=0)
        shapes = [
            (
                "convex",
                robot_vertices,
                ((0.15, 0.1), (0.8, 0.3)),
                ((0.1, 0.9), (0.9, 0.1)),
            ),
            (
                "not convex",
                np.array(
                    [[0, 0], [1, 0], [1, 0.4], [0.4, 0.4], [0.4, 1], [0, 1]],
                    dtype=float,
                ),
                ((0.2, 0.15), (0.8, 0.2)),
                ((0.2, 0.85), (0.85, 0.25)),
            ),
        ]
        for column, (title, vertices, start, end) in enumerate(shapes):
            center = (column - 0.5) * config.frame_width / 2 * RIGHT + 0.3 * DOWN
            corner = center - panel_size / 2 * (RIGHT + UP)

            def place(point: np.ndarray, corner: np.ndarray = corner) -> np.ndarray:
                """
                :return: The scene position of *point* in the unit square of the panel.
                """
                return corner + panel_size * (point[0] * RIGHT + point[1] * UP)

            region = Polygon(
                *[place(vertex) for vertex in vertices],
                fill_color=PlotColor.FEASIBLE.manim_color,
                fill_opacity=0.9,
                stroke_color=PlotColor.STRUCTURE.manim_color,
                stroke_width=3,
            )
            heading = self.note(text=title, font_size=30).next_to(region, UP, buff=0.3)
            self.play(FadeIn(region), FadeIn(heading), run_time=1)
            first = [ValueTracker(value) for value in start[0]]
            second = [ValueTracker(value) for value in start[1]]
            segment = always_redraw(
                lambda first=first, second=second, place=place: VGroup(
                    Line(
                        place(np.array([tracker.get_value() for tracker in first])),
                        place(np.array([tracker.get_value() for tracker in second])),
                        color=PlotColor.PATH.value,
                        stroke_width=4,
                    ),
                    *[
                        Dot(
                            place(np.array([tracker.get_value() for tracker in end])),
                            color=PlotColor.INK.value,
                            radius=0.08,
                        )
                        for end in (first, second)
                    ],
                )
            )
            self.play(FadeIn(segment))
            self.play(
                *[
                    tracker.animate.set_value(value)
                    for trackers, targets in ((first, end[0]), (second, end[1]))
                    for tracker, value in zip(trackers, targets)
                ],
                run_time=2.5,
            )
            if column == 1:
                warning = (
                    self.note(text="segment leaves the set", font_size=24)
                    .set_color(PlotColor.ALERT.value)
                    .move_to(place(np.array([0.72, 0.9])))
                )
                self.play(FadeIn(warning))
        self.wait(2)


# %% stochastic gradient descent


class StochasticGradientDescentScene(PlotMixin, Scene):
    """
    On the loss of a line fit, gradient descent on all samples walks smoothly to the
    minimum while minibatch gradients take a cheaper, noisy path to its neighbourhood.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        problem = LineFittingProblem()
        loss = LineFittingLoss(problem=problem)
        horizontal_range, vertical_range = (-1.0, 3.0), (-3.0, 2.0)
        axes = self.plot_axes(
            x_range=[*horizontal_range, 1],
            y_range=[*vertical_range, 1],
            x_label=r"\theta_1\ \text{(slope)}",
            y_label=r"\theta_2\ \text{(intercept)}",
        )
        contours = self.level_set_curves(
            axes=axes,
            level_sets=LevelSet.from_grid(
                function=loss,
                horizontal_range=horizontal_range,
                vertical_range=vertical_range,
                levels=[0.15 * 1.6**exponent for exponent in range(9)],
            ),
            color=PlotColor.CONTOUR,
        )
        self.play(Create(axes), Create(contours), run_time=1.5)
        start = np.array([-0.5, 1.5])
        iterations = 60
        runs = [
            (
                "gradient descent: all 200 samples per step",
                PlotColor.ALERT,
                GradientDescent(learning_rate=0.3).iterates(
                    function=loss, start=start, iterations=iterations
                ),
            ),
            (
                "SGD: 8 random samples per step",
                PlotColor.STRUCTURE,
                StochasticGradientDescent(learning_rate=0.3, batch_size=8).iterates(
                    problem=problem, start=start, iterations=iterations
                ),
            ),
        ]
        legend = VGroup(
            *[
                VGroup(
                    Line(0.3 * LEFT, 0.3 * RIGHT, color=color.value, stroke_width=5),
                    self.note(text=name, font_size=24),
                ).arrange(RIGHT, buff=0.2)
                for name, color, _ in runs
            ]
        ).arrange(DOWN, aligned_edge=LEFT)
        legend.to_corner(UR, buff=0.35).shift(0.3 * DOWN)
        legend.add_background_rectangle(color=ManimColor("#FFFFFF"), opacity=0.9)
        minimum = np.polyfit(problem.inputs, problem.targets, 1)
        self.play(
            FadeIn(legend),
            FadeIn(Dot(axes.c2p(*start), color=PlotColor.INK.value, radius=0.09)),
            FadeIn(Dot(axes.c2p(*minimum), color=PlotColor.OPTIMUM.value, radius=0.11)),
        )
        paths = [
            self.polyline(axes=axes, points=iterates, color=color, width=3.5)
            for _, color, iterates in runs
        ]
        self.play(*[Create(path) for path in paths], run_time=6, rate_func=linear)
        self.wait(1.5)


# %% computational graphs


class ComputationalGraphScene(PlotMixin, Scene):
    """
    The forward pass computes the values of :math:`f(a, b) = (a + b) b` node by node;
    the backward pass sends the adjoints back, summing them where :math:`b` branches.
    """

    def construct(self) -> None:
        """
        Unlike :meth:`manim.Scene.construct`, play the animation the class describes.
        """
        graph = SumTimesFactorGraph()
        nodes = graph.nodes
        positions = {
            "a": 4.5 * LEFT + 1.6 * UP,
            "b": 4.5 * LEFT + 1.6 * DOWN,
            "c": 0.6 * LEFT + 1.0 * UP,
            "f": 3.6 * RIGHT + 0.2 * DOWN,
        }
        symbols = {"a": "a", "b": "b", "c": "+", "f": r"\times"}
        circles = {
            label: VGroup(
                Circle(radius=0.55, color=PlotColor.INK.value, stroke_width=3),
                MathTex(symbols[label], font_size=44, color=PlotColor.INK.value),
            ).move_to(position)
            for label, position in positions.items()
        }
        edges = [
            Arrow(
                circles[operand.label].get_center(),
                circles[node.label].get_center(),
                buff=0.6,
                color=PlotColor.MUTED.value,
                stroke_width=4,
                max_tip_length_to_length_ratio=0.08,
            )
            for node in nodes.values()
            for operand in node.operands
        ]
        title = self.caption(text="Forward pass: values")
        self.play(
            FadeIn(title),
            *[FadeIn(circle) for circle in circles.values()],
            *[GrowArrow(edge) for edge in edges],
            run_time=1.5,
        )
        names = {"a": "a", "b": "b", "c": "c = a + b", "f": "f = c \\cdot b"}
        for label, node in nodes.items():
            value = MathTex(
                rf"{names[label]} = {node.value:g}",
                font_size=34,
                color=PlotColor.STRUCTURE.value,
            ).next_to(circles[label], UP, buff=0.2)
            self.play(FadeIn(value, shift=0.2 * UP), run_time=0.7)
        self.wait(0.6)
        self.play(Transform(title, self.caption(text="Backward pass: adjoints")))
        contributions: dict[str, list[float]] = {label: [] for label in nodes}
        contributions["f"].append(1.0)
        for node in reversed(list(nodes.values())):
            self.show_adjoint(
                label=node.label,
                terms=contributions[node.label],
                circle=circles[node.label],
            )
            adjoint = sum(contributions[node.label])
            for operand, derivative in zip(node.operands, node.local_derivatives):
                contributions[operand.label].append(adjoint * derivative)
        self.wait(2)

    def show_adjoint(
        self,
        *,
        label: str,
        terms: list[float],
        circle: VGroup,
    ) -> None:
        """
        Write the adjoint of the node *label* below its *circle* as the sum of the
        *terms* its consumers sent back.
        """
        total = f"{sum(terms):g}"
        expression = total
        if len(terms) > 1:
            expression = " + ".join(f"{term:g}" for term in terms) + f" = {total}"
        text = MathTex(
            rf"\bar {label} = {expression}",
            font_size=34,
            color=PlotColor.ALERT.value,
        ).next_to(circle, DOWN, buff=0.2)
        self.play(FadeIn(text, shift=0.2 * DOWN), run_time=0.8)
