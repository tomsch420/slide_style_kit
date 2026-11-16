"""
The lecture *Optimization* of Advanced Methods of AI: unconstrained and constrained
optimization, computational graphs and the QP behind Giskard's motions.

Run this module to write ``introduction_to_optimization.pptx`` and ``.pdf`` next to it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

import numpy as np

from slide_style_kit.assets import Asset
from slide_style_kit.components import CodeBlock, TakeAway
from slide_style_kit.deck import Deck, PageDecoration
from slide_style_kit.elements import Formula, Paragraph, Table, TextFrame, Video
from slide_style_kit.geometry import Position, Rectangle
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer
from slide_style_kit.slides import (
    BulletSlide,
    ContentSlide,
    Person,
    Slide,
    TableOfContentsEntry,
    TableOfContentsSlide,
    TitleSlide,
)
from slide_style_kit.style import Alignment, BulletLevel

from animation_catalogue import Animation
from examples import (
    Adam,
    GraspRecord,
    Optimum,
    SumTimesFactorGraph,
    VelocityControlProblem,
)

# %% sections


class Section(StrEnum):
    """
    The sections of the lecture, as the footer navigation names them.
    """

    INTRODUCTION = "Introduction"
    """
    What optimization is, the course block and the running example.
    """

    UNCONSTRAINED = "Unconstrained"
    """
    Gradients, critical points and convexity.
    """

    GRADIENT_METHODS = "Gradient Methods"
    """
    Gradient descent, momentum, stochastic gradient descent and Adam.
    """

    COMPUTATIONAL_GRAPHS = "Computational Graphs"
    """
    Computational graphs and automatic differentiation.
    """

    CONSTRAINED = "Constrained"
    """
    Linear and quadratic programs, the KKT conditions and Giskard's QP.
    """

    LIKELIHOOD = "Likelihood"
    """
    Fitting models by maximizing their likelihood, and the summary.
    """


class Snippet(StrEnum):
    """
    The code snippets shown on the slides, by file name.
    """

    BACKPROPAGATION = "backpropagation.py"
    """
    Reverse-mode differentiation of :math:`(a + b) b` in PyTorch.
    """

    @property
    def path(self) -> Path:
        """
        The file holding the snippet.
        """
        return Path(__file__).parent / "snippets" / self.value


# %% lecture


@dataclass(kw_only=True)
class IntroductionToOptimization:
    """
    The slides of the lecture, section by section.
    """

    formula_font_size: float = 20
    """
    The font size of displayed formulas, in points.
    """

    footer_section_spacing: float = 1.9
    """
    The distance between neighbouring section names in the footer, in inch; wider than
    the default so that six sections do not touch.
    """

    robot: VelocityControlProblem = field(default_factory=VelocityControlProblem)
    """
    The two-joint velocity control problem the LP and QP slides solve.
    """

    graph: SumTimesFactorGraph = field(default_factory=SumTimesFactorGraph)
    """
    The computational graph the backpropagation slides walk through.
    """

    grasps: GraspRecord = field(default_factory=GraspRecord)
    """
    The grasp outcomes the constrained maximum likelihood slide estimates from.
    """

    adam: Adam = field(default_factory=lambda: Adam(learning_rate=0.001))
    """
    Adam with its default step size and decays, whose values the Adam slides state.
    """

    def deck(self) -> Deck:
        """
        :return: The whole lecture.
        """
        return Deck(
            title="Advanced Methods of AI - Optimization",
            author="Tom Schierenbeck",
            sections=list(Section),
            decoration=PageDecoration(section_spacing=self.footer_section_spacing),
            slides=[
                *self.introduction_slides(),
                *self.unconstrained_slides(),
                *self.gradient_method_slides(),
                *self.computational_graph_slides(),
                *self.constrained_slides(),
                *self.likelihood_slides(),
            ],
        )

    # %% building blocks

    def heading(self, *, text: str, space_after: float = 4) -> Paragraph:
        """
        :return: A bold paragraph introducing the paragraphs below it.
        """
        return Paragraph(text=text, bold=True, space_after=space_after)

    def display(
        self,
        *,
        latex: str,
        top: float,
        height: float = 0.6,
        left: float = 0.45,
        width: float = 12.4,
        font_size: float | None = None,
        alignment: Alignment = Alignment.CENTER,
    ) -> Formula:
        """
        :return: The LaTeX formula *latex* set into the given area.
        """
        return Formula(
            latex=latex,
            area=Rectangle(left=left, top=top, width=width, height=height),
            font_size=font_size or self.formula_font_size,
            alignment=alignment,
        )

    def number(self, *, value: float) -> str:
        """
        :return: *value* with as many decimals as it needs and a typographic minus.
        """
        return f"{value:.4g}".replace("-", "−")

    def latex_number(self, *, value: float) -> str:
        """
        :return: *value* with as many decimals as it needs, as LaTeX.
        """
        return f"{value:.4g}"

    def latex_matrix(self, *, values: np.ndarray) -> str:
        """
        :return: The matrix, or the column vector, *values* as a LaTeX ``bmatrix``.
        """
        rows = values if values.ndim == 2 else values[:, None]
        body = r" \\ ".join(
            " & ".join(self.latex_number(value=entry) for entry in row) for row in rows
        )
        return rf"\begin{{bmatrix}} {body} \end{{bmatrix}}"

    def latex_inequality(self, *, coefficients: np.ndarray, bound: float) -> str:
        """
        :return: :math:`a^T x \\le b` for the two joint velocities, as LaTeX.
        """
        terms = [
            variable
            if coefficient == 1
            else f"{self.latex_number(value=coefficient)}\\,{variable}"
            for coefficient, variable in zip(coefficients, ["x_1", "x_2"])
            if coefficient != 0
        ]
        return f"{' + '.join(terms)} \\le {self.latex_number(value=bound)}"

    def point_text(self, *, optimum: Optimum) -> str:
        """
        :return: The point of *optimum* as text, such as ``(2.5, 25)``.
        """
        first, second = optimum.point
        return f"({self.number(value=first)}, {self.number(value=second)})"

    def video(
        self,
        *,
        animation: Animation,
        position: Position,
        width: float | None = None,
        height: float | None = None,
    ) -> Video:
        """
        :return: The rendered *animation*, sized like its poster image.
        """
        return Video(
            path=animation.poster,
            movie=animation.movie,
            position=position,
            width=width,
            height=height,
        )

    def text_box(
        self,
        *,
        area: Rectangle,
        paragraphs: list[Paragraph],
        font_size: float = 17,
    ) -> TextFrame:
        """
        :return: The *paragraphs* set into *area*.
        """
        return TextFrame(area=area, paragraphs=paragraphs, font_size=font_size)

    def line(self, *, text: str, top: float, font_size: float = 17) -> TextFrame:
        """
        :return: One paragraph across the slide, starting at *top*.
        """
        return self.text_box(
            area=Rectangle(left=0.45, top=top, width=12.4, height=0.45),
            paragraphs=[Paragraph(text=text, space_after=0)],
            font_size=font_size,
        )

    def contents(self, *, highlighted_section: Section | None = None) -> Slide:
        """
        :return: The table of contents with *highlighted_section* not faded.
        """
        entries = [
            TableOfContentsEntry(
                text="What Is Optimization?",
                section=Section.INTRODUCTION,
                subentries=["Running Example: Giskard"],
            ),
            TableOfContentsEntry(
                text="Unconstrained Optimization",
                section=Section.UNCONSTRAINED,
                subentries=["Gradients, Critical Points, Convexity"],
            ),
            TableOfContentsEntry(
                text="Gradient Methods",
                section=Section.GRADIENT_METHODS,
                subentries=["Gradient Descent, Momentum, SGD, Adam"],
            ),
            TableOfContentsEntry(
                text="Computational Graphs", section=Section.COMPUTATIONAL_GRAPHS
            ),
            TableOfContentsEntry(
                text="Constrained Optimization",
                section=Section.CONSTRAINED,
                subentries=["Linear Programs, Quadratic Programs, KKT"],
            ),
            TableOfContentsEntry(
                text="Outlook: Maximum Likelihood", section=Section.LIKELIHOOD
            ),
        ]
        return TableOfContentsSlide(
            entries=entries,
            highlighted_section=highlighted_section,
            space_between_entries=10,
            font_size=20,
            subentry_font_size=16,
        )

    def robot_constraints_latex(self) -> str:
        """
        :return: :math:`Gx \\le g` of the robot with both matrices written out.
        """
        return (
            rf"Gx \le g, \quad G = "
            rf"{self.latex_matrix(values=self.robot.constraint_matrix)}, \quad g = "
            rf"{self.latex_matrix(values=self.robot.constraint_bounds)}"
        )

    # %% introduction

    def introduction_slides(self) -> list[Slide]:
        """
        :return: The title, the learning goals, the course context, the running example
            and what optimization is.
        """
        return [
            TitleSlide(
                course="Advanced Methods of AI (WiSe 2026/2027)",
                title="Optimization",
                people=[
                    Person(name="Prof. Michael Beetz"),
                    Person(name="Tom Schierenbeck", role="lecturer"),
                ],
                place="Bremen, Germany",
                date="19th of November 2026",
                image=Asset.ROBOT_SKETCH,
            ),
            BulletSlide(
                title="Learning Goals",
                section=Section.INTRODUCTION,
                text_area=Rectangle(left=0.45, top=1.4, width=12.4, height=5.3),
                font_size=18,
                paragraphs=[
                    Paragraph(text="After this lecture you can …", space_after=12),
                    *[
                        Paragraph(text=f"{index}. {goal}", indent=0.3, space_after=8)
                        for index, goal in enumerate(
                            [
                                "write a problem as objective, decision variables and "
                                "constraints, and tell convex from non-convex problems,",
                                "test a function for convexity and explain why it makes "
                                "every local minimum global,",
                                "run gradient descent and explain step size, momentum, "
                                "SGD and Adam,",
                                "compute a gradient by hand with the backward pass "
                                "through a computational graph,",
                                "solve small linear and quadratic programs geometrically "
                                "and check optimality with the KKT conditions,",
                                "read the quadratic program Giskard solves to move the "
                                "robot,",
                                "state maximum likelihood estimation as an optimization "
                                "problem.",
                            ],
                            start=1,
                        )
                    ],
                ],
            ),
            ContentSlide(
                title="Where We Left Off",
                section=Section.INTRODUCTION,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.5, width=6.0, height=4.6),
                        paragraphs=[
                            self.heading(text="Last weeks: KR&R", space_after=8),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Knowledge as symbols: a statement is true or false",
                                    "Reasoning: what follows from a knowledge base "
                                    "(resolution, SLD, Datalog)",
                                    "Constraint logic programming: constraints over "
                                    "{a:numbers} in rule bodies – announced for "
                                    "today",
                                ],
                                space_after=8,
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=6.9, top=1.5, width=6.0, height=4.6),
                        paragraphs=[
                            self.heading(text="Today: Optimization", space_after=8),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Infinitely many candidates, each with a score: "
                                    "find the {a:best} one",
                                    "Lecture 01: the performance measure scores state "
                                    "and action – optimization picks the action",
                                    "Lecture 02: how does Giskard turn “grasp the "
                                    "cup” into joint velocities?",
                                ],
                                space_after=8,
                            ),
                        ],
                    ),
                    TakeAway(text="Last weeks: what follows. Today: what is best."),
                ],
            ),
            ContentSlide(
                title="The Next Four Weeks",
                section=Section.INTRODUCTION,
                items=[
                    *[
                        self.text_box(
                            area=Rectangle(
                                left=0.45 + index * 3.15,
                                top=1.7,
                                width=2.95,
                                height=4.3,
                            ),
                            paragraphs=[
                                Paragraph(
                                    text=f"{{s:{topic}}}", font_size=18, space_after=2
                                ),
                                Paragraph(text=date, space_after=12),
                                Paragraph(text=question),
                            ],
                            font_size=16,
                        )
                        for index, (topic, date, question) in enumerate(
                            [
                                (
                                    "Optimization",
                                    "Thu 19.11.",
                                    "How do we find the best parameters or actions?",
                                ),
                                (
                                    "Data-Intensive Systems",
                                    "Thu 26.11.",
                                    "How do we handle the data we learn from?",
                                ),
                                (
                                    "Uncertainty",
                                    "Thu 03.12.",
                                    "How do we reason with incomplete knowledge – "
                                    "and fit models by {a:maximizing their "
                                    "likelihood}?",
                                ),
                                (
                                    "Causality",
                                    "Thu 10.12.",
                                    "What changes when we act instead of observe?",
                                ),
                            ]
                        )
                    ],
                    TakeAway(
                        text="Today's tools – gradients, constraints, KKT – "
                        "are what the next lectures optimize with."
                    ),
                ],
            ),
            self.contents(),
            *self.running_example_slides(),
            *self.problem_definition_slides(),
        ]

    def running_example_slides(self) -> list[Slide]:
        """
        :return: Giskard's QP and the two-joint version of it the lecture solves.
        """
        robot = self.robot
        base_limit, arm_limit, elbow_limit = robot.constraint_bounds[:3]
        elbow_share = robot.constraint_matrix[2, 1]
        return [
            BulletSlide(
                title="Running Example: Giskard Moves the Arm",
                section=Section.INTRODUCTION,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    Paragraph(
                        text="In CRAM, {b:Giskard} turns motion goals into joint "
                        "velocities (lecture 02). Every control cycle it solves one "
                        "{a:quadratic program (QP)}:",
                        space_after=10,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Decision variables:} the velocities of the joints",
                            "{b:Goals} (“gripper to the cup”) become {i:soft} "
                            "constraints: violating them costs",
                            "{b:Joint limits} and {b:collision avoidance} are {i:hard} "
                            "constraints",
                            Paragraph(
                                text="{b:Objective:} small, smooth motions plus small "
                                "goal violations",
                                level=BulletLevel.FIRST,
                                space_after=16,
                            ),
                        ],
                        space_after=6,
                    ),
                    Paragraph(
                        text="The real QP has hundreds of variables and constraints. "
                        "Today we build and solve a version with {a:two joints} – "
                        "small enough to draw."
                    ),
                ],
                take_away="By the end of today you can read and solve the problem "
                "behind Giskard's motions.",
            ),
            ContentSlide(
                title="The Toy Robot",
                section=Section.INTRODUCTION,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.0),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Two joints: x₁ = velocity of the {a:base}, "
                                "x₂ = velocity of the {a:arm}, both in cm/s",
                                "The gripper moves forward at x₁ + x₂, the "
                                "elbow at x₁ + "
                                f"{self.number(value=elbow_share)} x₂",
                            ],
                            space_after=6,
                        ),
                    ),
                    Table(
                        position=Position(x=0.9, y=2.5),
                        column_widths=[2.6, 3.2, 5.9],
                        rows=[
                            ["Constraint", "Formula", "Meaning"],
                            [
                                "Base limit",
                                f"x₁ ≤ {self.number(value=base_limit)}",
                                "the base is slow",
                            ],
                            [
                                "Arm limit",
                                f"x₂ ≤ {self.number(value=arm_limit)}",
                                "the arm is faster",
                            ],
                            [
                                "Collision avoidance",
                                f"x₁ + {self.number(value=elbow_share)} x₂ "
                                f"≤ {self.number(value=elbow_limit)}",
                                "the elbow approaches a shelf at most "
                                f"{self.number(value=elbow_limit)} cm/s",
                            ],
                            [
                                "Forward only",
                                "x₁ ≥ 0,  x₂ ≥ 0",
                                "no joint moves away from the cup",
                            ],
                            [
                                "Goal (soft)",
                                "x₁ + x₂ ≈ "
                                f"{self.number(value=robot.desired_gripper_speed)}",
                                "the gripper should approach the cup at "
                                f"{self.number(value=robot.desired_gripper_speed)} "
                                "cm/s",
                            ],
                        ],
                        row_height=0.5,
                        font_size=15,
                    ),
                    TakeAway(
                        text="Two decision variables: every problem today can be drawn "
                        "in the plane."
                    ),
                ],
            ),
        ]

    def problem_definition_slides(self) -> list[Slide]:
        """
        :return: The slides defining optimization problems and their types.
        """
        return [
            ContentSlide(
                title="What Is Optimization?",
                section=Section.INTRODUCTION,
                items=[
                    self.line(
                        text="Choose the {a:decision variables} x that minimize an "
                        "{a:objective} f, within the {a:feasible region} C:",
                        top=1.25,
                        font_size=18,
                    ),
                    self.display(
                        latex=r"\min_{x}\ f(x) \quad \text{s.t.} \quad x \in C",
                        top=1.8,
                    ),
                    self.video(
                        animation=Animation.FEASIBLE_REGION,
                        position=Position(x=0.6, y=2.6),
                        width=4.2,
                    ),
                    TextFrame(
                        area=Rectangle(left=0.6, top=5.75, width=5.4, height=0.45),
                        paragraphs=[
                            Paragraph(
                                text="s.t. = “subject to”; C = all points "
                                "that satisfy the constraints.",
                                space_after=0,
                            )
                        ],
                        font_size=13,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.3, top=2.7, width=6.6, height=3.5),
                        paragraphs=[
                            self.heading(text="Examples:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{b:Robot:} joint velocities that reach the goal "
                                    "within the limits",
                                    "{b:Learning:} parameters that minimize a loss or "
                                    "maximize a likelihood (→ Uncertainty)",
                                    "{b:Agent:} the action with the best performance "
                                    "measure (lecture 01)",
                                ],
                                space_after=8,
                            ),
                        ],
                        font_size=18,
                    ),
                    TakeAway(
                        text="Optimization: the best point of the feasible region."
                    ),
                ],
            ),
            ContentSlide(
                title="Constrained Optimization Problems",
                section=Section.INTRODUCTION,
                items=[
                    self.line(
                        text="The general form of an optimization problem:",
                        top=1.4,
                        font_size=18,
                    ),
                    self.display(
                        latex=r"\begin{aligned} \min_{x \in \mathbb{R}^n}\ & f(x) \\ "
                        r"\text{s.t.}\ & g_i(x) \le 0, \quad i = 1, \dots, m \\ "
                        r"& h_j(x) = 0, \quad j = 1, \dots, p \end{aligned}",
                        top=2.1,
                        height=1.6,
                        left=0.45,
                        width=5.6,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.3, top=2.1, width=6.6, height=2.0),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "f is the {a:objective function}",
                                "x are the n {a:decision variables}",
                                "each gᵢ is an {a:inequality constraint}",
                                "each h{y:ⱼ} is an {a:equality constraint}",
                            ],
                            space_after=6,
                        ),
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.4, width=12.4, height=0.8),
                        paragraphs=[
                            Paragraph(
                                text="{b:Maximizing} f is minimizing −f. The "
                                "robot's LP maximizes; everything else today minimizes.",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    TakeAway(
                        text="Objective, decision variables, constraints: the "
                        "vocabulary for the rest of today."
                    ),
                ],
            ),
            ContentSlide(
                title="Types of Optimization Problems",
                section=Section.INTRODUCTION,
                items=[
                    Table(
                        position=Position(x=2.4, y=1.5),
                        column_widths=[2.4, 6.4],
                        rows=[
                            ["Problem", "Form"],
                            ["{a:Unconstrained}", "no constraints at all"],
                            ["{a:Constrained}", "inequality and equality constraints"],
                            ["{a:Linear (LP)}", "objective linear, constraints linear"],
                            [
                                "{a:Quadratic (QP)}",
                                "objective quadratic, constraints linear",
                            ],
                            [
                                "{a:Convex}",
                                "feasible set and objective convex: every local "
                                "minimum is global",
                            ],
                            ["{a:Non-convex}", "harder, many local minima"],
                        ],
                        row_height=0.38,
                        font_size=15,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.4, width=12.4, height=1.8),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Today: unconstrained problems and gradients first, "
                                "then linear and quadratic programs",
                                "Training a neural network: unconstrained, non-convex",
                                "Giskard's QP: constrained, convex",
                            ],
                            space_after=6,
                        ),
                    ),
                    TakeAway(text="Convexity decides how hard a problem is."),
                ],
            ),
        ]

    # %% unconstrained optimization

    def unconstrained_slides(self) -> list[Slide]:
        """
        :return: The section on gradients, critical points and convexity.
        """
        return [
            self.contents(highlighted_section=Section.UNCONSTRAINED),
            *self.gradient_slides(),
            *self.convexity_slides(),
            *self.quadratic_function_slides(),
        ]

    def gradient_slides(self) -> list[Slide]:
        """
        :return: The slides on smooth functions, gradients and critical points.
        """
        return [
            ContentSlide(
                title="Smooth Functions and the Gradient",
                section=Section.UNCONSTRAINED,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.7),
                        paragraphs=[
                            self.heading(text="Smooth functions:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    Paragraph(
                                        text="f has a derivative everywhere, and it "
                                        "changes continuously.",
                                        level=BulletLevel.FIRST,
                                        space_after=14,
                                    ),
                                ],
                                space_after=4,
                            ),
                            self.heading(
                                text="The gradient collects all partial derivatives "
                                "of f:"
                            ),
                        ],
                    ),
                    self.display(
                        latex=r"\nabla f(x) = \begin{bmatrix} \partial f / \partial "
                        r"x_1 \\ \vdots \\ \partial f / \partial x_n \end{bmatrix}",
                        top=3.0,
                        height=1.4,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.6, width=12.4, height=1.4),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Entry i: how fast f changes when only xᵢ moves.",
                                "Together: the direction in which f grows fastest.",
                            ],
                            space_after=6,
                        ),
                    ),
                    TakeAway(text="The gradient is the local map of the landscape."),
                ],
            ),
            ContentSlide(
                title="Geometric Meaning of the Gradient",
                section=Section.UNCONSTRAINED,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.25, width=12.4, height=1.0),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{y:∇}f(x) points in the direction of the {a:steepest "
                                "increase} of f.",
                                "Moving in the opposite direction makes f decrease "
                                "fastest.",
                            ],
                            space_after=4,
                        ),
                    ),
                    self.video(
                        animation=Animation.GRADIENT_BOWL,
                        position=Position(x=3.9, y=2.3),
                        width=5.6,
                    ),
                    TakeAway(text="To minimize f, move along −{y:∇}f."),
                ],
            ),
            BulletSlide(
                title="Critical Points: Where the Gradient Is Zero",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=7.6, height=1.0),
                font_size=17,
                paragraphs=[
                    Paragraph(
                        text="At a minimum of a smooth function without constraints, "
                        "no direction goes downhill, so",
                        space_after=0,
                    ),
                ],
                items=[
                    self.display(
                        latex=r"\nabla f(x^*) = 0", top=2.3, left=0.45, width=7.6
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=3.1, width=7.6, height=3.1),
                        paragraphs=[
                            Paragraph(
                                text="Points with zero gradient are {a:critical "
                                "points}. Three kinds:",
                                space_after=6,
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{b:minimum:} curves upward in every direction",
                                    "{b:maximum:} curves downward in every direction",
                                    "{b:saddle point:} up in one direction, down in "
                                    "another",
                                ],
                                space_after=4,
                            ),
                            Paragraph(
                                text="The second derivatives (the {a:Hessian} "
                                "{y:∇}²f) tell them apart."
                            ),
                        ],
                    ),
                    self.video(
                        animation=Animation.CRITICAL_POINTS,
                        position=Position(x=8.2, y=1.9),
                        width=4.6,
                    ),
                ],
                take_away="Zero gradient is necessary for a minimum, not sufficient "
                "– unless f is convex.",
            ),
        ]

    def convexity_slides(self) -> list[Slide]:
        """
        :return: The slides defining and testing convexity, and why it matters.
        """
        return [
            ContentSlide(
                title="Convex Sets",
                section=Section.UNCONSTRAINED,
                items=[
                    self.line(
                        text="A set C is {a:convex} if the segment between any two of "
                        "its points stays inside C:",
                        top=1.3,
                    ),
                    self.display(
                        latex=r"\theta x + (1 - \theta) y \in C \quad \text{for all } "
                        r"x, y \in C \text{ and } \theta \in [0, 1]",
                        top=1.85,
                    ),
                    self.line(
                        text="θ = 1 gives x, θ = 0 gives y, the values "
                        "between give the points of the segment.",
                        top=2.5,
                        font_size=15,
                    ),
                    self.video(
                        animation=Animation.CONVEX_SET,
                        position=Position(x=3.65, y=3.0),
                        height=3.2,
                    ),
                    TakeAway(
                        text="The robot's feasible velocities (left) are convex: linear "
                        "constraints always give a convex set."
                    ),
                ],
            ),
            ContentSlide(
                title="Convex Functions",
                section=Section.UNCONSTRAINED,
                items=[
                    self.line(
                        text="A function f is {a:convex} if the chord between two "
                        "points of its graph never lies below the graph:",
                        top=1.3,
                    ),
                    self.display(
                        latex=r"\underbrace{f(\theta x + (1 - \theta) y)}"
                        r"_{\text{graph}} \;\le\; \underbrace{\theta f(x) + "
                        r"(1 - \theta) f(y)}_{\text{chord}}",
                        top=1.85,
                        height=0.9,
                    ),
                    self.video(
                        animation=Animation.CONVEXITY,
                        position=Position(x=3.65, y=3.0),
                        height=3.2,
                    ),
                    TakeAway(
                        text="Convex functions have no bumps in which a descent could "
                        "get stuck."
                    ),
                ],
            ),
            ContentSlide(
                title="Testing Convexity",
                section=Section.UNCONSTRAINED,
                items=[
                    self.line(
                        text="{b:One variable:} f is convex if its slope never "
                        "decreases – the graph curves upward:",
                        top=1.3,
                    ),
                    self.display(
                        latex=r"f''(x) \ge 0 \ \text{for all } x \qquad "
                        r"\text{e.g. } f(x) = x^2: \ f''(x) = 2 \ge 0",
                        top=1.8,
                    ),
                    self.line(
                        text="{b:Several variables:} the matrix of second derivatives, "
                        "the {a:Hessian} {y:∇}²f, must curve upward in every "
                        "direction v:",
                        top=2.6,
                    ),
                    self.display(
                        latex=r"v^\top \nabla^2 f(x)\, v \ge 0 \ \text{for all } v "
                        r"\qquad \Longleftrightarrow \qquad \text{all eigenvalues of } "
                        r"\nabla^2 f(x) \ge 0",
                        top=3.15,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=3.95, width=12.4, height=2.25),
                        paragraphs=[
                            Paragraph(
                                text="Such a matrix is called {a:positive "
                                "semidefinite}, written {y:⪰} 0.",
                                space_after=10,
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "A quadratic ½ xᵀQx + cᵀx has the "
                                    "Hessian Q: it is convex exactly when all "
                                    "eigenvalues of Q are ≥ 0.",
                                    "Convex: linear functions, x², −log x. "
                                    "Not convex: sin x, the loss of a neural network.",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    TakeAway(text="Convex = curves upward in every direction."),
                ],
            ),
            BulletSlide(
                title="Why Convexity Matters",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.4, width=12.4, height=4.8),
                font_size=17,
                paragraphs=[
                    self.heading(text="Theorem:"),
                    Paragraph(
                        text="If f and the feasible region C are convex, then",
                        space_after=4,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "every {a:local} minimum is a {a:global} minimum,",
                            Paragraph(
                                text="without constraints, a zero gradient is "
                                "{i:enough} for a minimum.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.heading(text="Why:"),
                    Paragraph(
                        text="Suppose y were better than a local minimum x. The chord "
                        "from x to y lies above the graph, so points on the way to y "
                        "– even ones right next to x – would be better than "
                        "x. Then x was no local minimum.",
                        space_after=14,
                    ),
                    self.heading(text="Consequence:"),
                    *Paragraph.bullet_points(
                        texts=[
                            "Convex problems (LP, convex QP, least squares) are solved "
                            "reliably, to the global optimum.",
                            "Non-convex problems (neural networks) settle for a good "
                            "local minimum.",
                        ],
                        space_after=4,
                    ),
                ],
                take_away="Convex: any method that goes downhill finds the global "
                "optimum.",
            ),
        ]

    def quadratic_function_slides(self) -> list[Slide]:
        """
        :return: The slides minimizing a quadratic function and linear least squares.
        """
        rows = [
            (
                "function",
                r"f(x) = \tfrac{1}{2} q x^2 + c x",
                r"f(x) = \tfrac{1}{2} x^\top Q x + c^\top x",
            ),
            ("derivative", r"f'(x) = q x + c", r"\nabla f(x) = Q x + c"),
            ("set to zero", r"q x^* + c = 0", r"Q x^* + c = 0"),
            ("solve", r"x^* = -c / q", r"x^* = -Q^{-1} c"),
        ]
        row_top, row_height = 1.95, 0.62
        return [
            ContentSlide(
                title="Example: Minimizing a Quadratic Function",
                section=Section.UNCONSTRAINED,
                items=[
                    self.text_box(
                        area=Rectangle(left=2.6, top=1.35, width=4.6, height=0.45),
                        paragraphs=[self.heading(text="One variable", space_after=0)],
                    ),
                    self.text_box(
                        area=Rectangle(left=7.4, top=1.35, width=5.5, height=0.45),
                        paragraphs=[self.heading(text="Many variables", space_after=0)],
                    ),
                    *[
                        element
                        for index, (label, single, many) in enumerate(rows)
                        for element in [
                            self.text_box(
                                area=Rectangle(
                                    left=0.45,
                                    top=row_top + index * row_height + 0.1,
                                    width=2.0,
                                    height=0.4,
                                ),
                                paragraphs=[Paragraph(text=label, space_after=0)],
                                font_size=16,
                            ),
                            self.display(
                                latex=single,
                                top=row_top + index * row_height,
                                height=0.55,
                                left=2.6,
                                width=4.6,
                                alignment=Alignment.LEFT,
                            ),
                            self.display(
                                latex=many,
                                top=row_top + index * row_height,
                                height=0.55,
                                left=7.4,
                                width=5.5,
                                alignment=Alignment.LEFT,
                            ),
                        ]
                    ],
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.6, width=12.4, height=1.6),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Dividing by q needs q > 0; inverting Q needs Q "
                                "{a:positive definite} (all eigenvalues > 0).",
                                "Then f is a bowl curving upward in every direction, "
                                "and x* is its unique minimum.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="Same steps as in school, with a matrix instead of a "
                        "number – Giskard's cost is such a quadratic."
                    ),
                ],
            ),
            ContentSlide(
                title="Linear Least Squares",
                section=Section.UNCONSTRAINED,
                items=[
                    self.line(
                        text="Fit x to m measurements: row aᵢ of A holds the inputs "
                        "of measurement i, bᵢ its measured value.",
                        top=1.3,
                    ),
                    self.display(
                        latex=r"\min_x\ \|Ax - b\|^2 = \sum_{i=1}^{m} "
                        r"\underbrace{(a_i^\top x - b_i)^2}_{\text{squared error of "
                        r"measurement } i}",
                        top=1.85,
                        height=1.0,
                    ),
                    self.line(
                        text="The gradient 2Aᵀ(Ax − b) is zero at the "
                        "{a:normal equations}, which have a closed-form solution:",
                        top=3.05,
                    ),
                    self.display(
                        latex=r"A^\top A\, x^* = A^\top b \qquad \Longrightarrow "
                        r"\qquad x^* = (A^\top A)^{-1} A^\top b",
                        top=3.6,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.5, width=12.4, height=1.6),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Used in regression, calibration and data fitting.",
                                "For many parameters or many measurements: gradient "
                                "descent instead.",
                            ],
                            space_after=6,
                        ),
                    ),
                    TakeAway(
                        text="Least squares comes back as maximum likelihood at the end."
                    ),
                ],
            ),
        ]

    # %% gradient methods

    def gradient_method_slides(self) -> list[Slide]:
        """
        :return: The section on gradient descent, its problems and its variants.
        """
        return [
            self.contents(highlighted_section=Section.GRADIENT_METHODS),
            *self.gradient_descent_slides(),
            *self.gradient_descent_variant_slides(),
            *self.adam_slides(),
        ]

    def gradient_descent_slides(self) -> list[Slide]:
        """
        :return: The slides on gradient descent, its step size and its problems.
        """
        return [
            BulletSlide(
                title="Gradient Descent: Core Idea",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=6.4, top=1.6, width=6.5, height=2.3),
                font_size=18,
                paragraphs=[
                    Paragraph(
                        text="{b:Goal:} minimize f without constraints.",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The {a:negative} gradient points downhill.",
                            "So take a small step against the gradient, and repeat:",
                        ],
                        space_after=6,
                    ),
                ],
                items=[
                    self.display(
                        latex=r"x_{k+1} = x_k - \alpha\, \nabla f(x_k)",
                        top=3.95,
                        left=6.4,
                        width=6.5,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.4, top=4.75, width=6.5, height=1.4),
                        paragraphs=[
                            Paragraph(
                                text="x{y:ₖ} is the point after k steps, α the "
                                "{a:step size} or {a:learning rate}."
                            )
                        ],
                    ),
                    self.video(
                        animation=Animation.GRADIENT_DESCENT_SURFACE,
                        position=Position(x=0.6, y=1.3),
                        width=4.9,
                    ),
                ],
                take_away="Gradient descent only needs {y:∇}f – no closed form.",
            ),
            ContentSlide(
                title="Gradient Descent: Where Does the Update Come From?",
                section=Section.GRADIENT_METHODS,
                items=[
                    self.line(
                        text="Near x, f is almost linear (first-order Taylor "
                        "approximation):",
                        top=1.5,
                    ),
                    self.display(
                        latex=r"f(x + \Delta x) \approx f(x) + \nabla f(x)^\top "
                        r"\Delta x",
                        top=2.05,
                    ),
                    self.line(
                        text="For a step Δx of fixed length, the change "
                        "{y:∇}f(x)ᵀΔx is most negative when Δx points "
                        "opposite to the gradient:",
                        top=2.95,
                    ),
                    self.display(latex=r"\Delta x = -\alpha\, \nabla f(x)", top=3.6),
                    TakeAway(text="−{y:∇}f is the direction of steepest descent."),
                ],
            ),
            ContentSlide(
                title="Choosing a Step Size (Learning Rate)",
                section=Section.GRADIENT_METHODS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.3),
                        paragraphs=[
                            self.heading(text="The learning rate α controls:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{a:How far} we move in the descent direction.",
                                    "Stability and convergence speed.",
                                ],
                                space_after=4,
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=3.2, top=2.75, width=3.8, height=1.3),
                        paragraphs=[
                            self.heading(text="Small α:"),
                            *Paragraph.bullet_points(
                                texts=["Very stable", "Converges slowly"], space_after=4
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=7.5, top=2.75, width=4.6, height=1.3),
                        paragraphs=[
                            self.heading(text="Large α:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Faster progress",
                                    "Risk of overshooting or divergence",
                                ],
                                space_after=4,
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.25, width=12.4, height=1.95),
                        paragraphs=[
                            self.heading(text="In practice:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Constant α (simple)",
                                    "Decreasing schedule",
                                    "{a:Line search}: try steps along −{y:∇}f "
                                    "until the function decreases sufficiently",
                                ],
                                space_after=3,
                            ),
                        ],
                        font_size=16,
                    ),
                    TakeAway(text="The step size is the most important knob."),
                ],
            ),
            BulletSlide(
                title="Convergence Intuition",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=6.4, top=2.0, width=6.5, height=2.4),
                font_size=18,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "Far from the optimum the gradient is large: big steps.",
                            "Near the optimum it is small: small steps.",
                            Paragraph(
                                text="Stop when the gradient is almost zero:",
                                level=BulletLevel.FIRST,
                                space_after=0,
                            ),
                        ],
                        space_after=8,
                    ),
                ],
                items=[
                    self.display(
                        latex=r"\|\nabla f(x_k)\| < \varepsilon",
                        top=4.5,
                        left=6.4,
                        width=6.5,
                    ),
                    self.video(
                        animation=Animation.CONVERGENCE,
                        position=Position(x=1.0, y=1.75),
                        width=4.3,
                    ),
                ],
                take_away="With a fixed α, the steps shrink by themselves.",
            ),
            BulletSlide(
                title="Common Problems in Gradient Descent",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=6.0, top=1.9, width=6.9, height=4.3),
                font_size=18,
                paragraphs=[
                    paragraph
                    for heading, points in [
                        (
                            "1. Local minima and plateaus",
                            [
                                "Non-convex: stuck in the nearest valley",
                                "Almost flat: the gradient is tiny, progress stalls",
                            ],
                        ),
                        (
                            "2. Ill-conditioning",
                            [
                                "Contours stretched into a long valley",
                                "Steps zig-zag and converge slowly",
                            ],
                        ),
                        (
                            "3. Overshooting",
                            ["Large step size causes divergence or oscillation"],
                        ),
                    ]
                    for paragraph in [
                        self.heading(text=heading),
                        *Paragraph.bullet_points(texts=points, space_after=4),
                    ]
                ],
                items=[
                    self.video(
                        animation=Animation.GRADIENT_DESCENT_PROBLEMS,
                        position=Position(x=0.3, y=2.0),
                        width=5.2,
                    )
                ],
                take_away="The variants that follow address these problems.",
            ),
        ]

    def gradient_descent_variant_slides(self) -> list[Slide]:
        """
        :return: The slides on momentum and stochastic gradient descent.
        """
        return [
            ContentSlide(
                title="Momentum",
                section=Section.GRADIENT_METHODS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.5, width=12.4, height=2.3),
                        paragraphs=[
                            Paragraph(
                                text="{b:Problem:} gradient descent zig-zags in narrow "
                                "valleys.",
                                space_after=10,
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Keep a {a:velocity} v: a running average of the "
                                    "past steps.",
                                    "Directions that keep going downhill build up "
                                    "speed; directions that flip sign cancel out.",
                                ],
                                space_after=6,
                            ),
                        ],
                    ),
                    self.display(
                        latex=r"v_{k+1} = \beta\, v_k - \alpha\, \nabla f(x_k), "
                        r"\qquad x_{k+1} = x_k + v_{k+1}",
                        top=3.9,
                    ),
                    self.line(
                        text="β {y:∈} [0, 1) says how much of the old velocity is "
                        "kept; β = 0 is plain gradient descent.",
                        top=4.75,
                    ),
                    TakeAway(text="Momentum remembers where it was going."),
                ],
            ),
            ContentSlide(
                title="Stochastic Gradient Descent (SGD)",
                section=Section.GRADIENT_METHODS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=6.9, height=0.75),
                        paragraphs=[
                            Paragraph(
                                text="Learning objectives {a:average} a loss "
                                "ℓ{y:ⱼ} over N samples j:",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    self.display(
                        latex=r"f(\theta) = \frac{1}{N} \sum_{j=1}^{N} \ell_j(\theta)",
                        top=1.85,
                        height=0.85,
                        left=0.45,
                        width=6.9,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=2.8, width=6.9, height=0.75),
                        paragraphs=[
                            Paragraph(
                                text="One gradient of f costs N sample gradients. SGD "
                                "uses a random {a:minibatch} B of samples per step:",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    self.display(
                        latex=r"\theta \leftarrow \theta - \alpha\, \frac{1}{|B|} "
                        r"\sum_{j \in B} \nabla \ell_j(\theta)",
                        top=3.6,
                        height=0.85,
                        left=0.45,
                        width=6.9,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.55, width=6.9, height=1.65),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "On average the minibatch gradient equals the full "
                                "gradient.",
                                "Cheap but noisy steps; decrease α to settle.",
                                "One pass through all samples is an {a:epoch}.",
                            ],
                            space_after=4,
                        ),
                        font_size=16,
                    ),
                    self.video(
                        animation=Animation.STOCHASTIC_GRADIENT_DESCENT,
                        position=Position(x=7.6, y=1.6),
                        width=5.3,
                    ),
                    TakeAway(
                        text="SGD never needs all data at once (→ Data-Intensive "
                        "Systems, 26.11.)."
                    ),
                ],
            ),
        ]

    def adam_slides(self) -> list[Slide]:
        """
        :return: The idea of Adam, then its update line by line.
        """
        adam = self.adam
        update = [
            (r"g_k = \nabla f(x_k)", "the gradient at the current point"),
            (
                r"m_k = \beta_1 m_{k-1} + (1 - \beta_1)\, g_k",
                "average gradient: {a:where to go} (β₁ = "
                f"{self.number(value=adam.first_moment_decay)}: about the last "
                f"{round(1 / (1 - adam.first_moment_decay))} steps)",
            ),
            (
                r"s_k = \beta_2 s_{k-1} + (1 - \beta_2)\, g_k^2",
                "average squared gradient per coordinate: {a:how steep} it usually "
                f"is (β₂ = {self.number(value=adam.second_moment_decay)})",
            ),
            (
                r"\hat m_k = \frac{m_k}{1 - \beta_1^k}, \quad \hat s_k = "
                r"\frac{s_k}{1 - \beta_2^k}",
                "m and s start at 0, so early averages are too small; this corrects "
                "them",
            ),
            (
                r"x_{k+1} = x_k - \alpha\, \frac{\hat m_k}{\sqrt{\hat s_k} + "
                r"\varepsilon}",
                "step towards m̂, divided by the typical size √ŝ; "
                "ε avoids dividing by zero",
            ),
        ]
        row_top, row_height = 1.45, 0.92
        return [
            BulletSlide(
                title="Adam: the Idea",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=0.45, top=1.3, width=7.4, height=4.9),
                font_size=16,
                paragraphs=[
                    self.heading(text="Problem:"),
                    Paragraph(
                        text="One step size α for all coordinates. In a narrow "
                        "valley the gradient is large across and small along it: a "
                        "step that is safe across is far too small along.",
                        space_after=12,
                    ),
                    self.heading(text="Idea:"),
                    *Paragraph.bullet_points(
                        texts=[
                            "Average the recent gradients – like momentum – "
                            "for a smooth {a:direction}.",
                            "Also average the {i:squared} gradients: how large the "
                            "gradient of each coordinate usually is.",
                            "Divide each coordinate's step by that typical size: "
                            "{a:steep coordinates get small steps, flat ones large "
                            "steps}.",
                        ],
                        space_after=8,
                    ),
                    Paragraph(
                        text="Every coordinate then moves at a similar pace, about "
                        "α per step.",
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.OPTIMIZER_COMPARISON,
                        position=Position(x=8.0, y=1.9),
                        width=5.0,
                    )
                ],
                take_away="Adam is the default optimizer for neural networks.",
            ),
            ContentSlide(
                title="Adam: the Update, Line by Line",
                section=Section.GRADIENT_METHODS,
                items=[
                    *[
                        element
                        for index, (latex, meaning) in enumerate(update)
                        for element in [
                            self.display(
                                latex=latex,
                                top=row_top + index * row_height,
                                height=0.8,
                                left=0.45,
                                width=5.6,
                                font_size=18,
                                alignment=Alignment.LEFT,
                            ),
                            self.text_box(
                                area=Rectangle(
                                    left=6.3,
                                    top=row_top + index * row_height + 0.1,
                                    width=6.6,
                                    height=0.75,
                                ),
                                paragraphs=[Paragraph(text=meaning, space_after=0)],
                                font_size=15,
                            ),
                        ]
                    ],
                    TakeAway(
                        text=f"Defaults α = {self.number(value=adam.learning_rate)}"
                        f", β₁ = {self.number(value=adam.first_moment_decay)}"
                        f", β₂ = {self.number(value=adam.second_moment_decay)}"
                        ", ε = 10{y:⁻}⁸ often work without tuning."
                    ),
                ],
            ),
        ]

    # %% computational graphs

    def computational_graph_slides(self) -> list[Slide]:
        """
        :return: The section on computational graphs and automatic differentiation.
        """
        return [
            self.contents(highlighted_section=Section.COMPUTATIONAL_GRAPHS),
            self.gradient_source_slide(),
            ContentSlide(
                title="Computational Graphs",
                section=Section.COMPUTATIONAL_GRAPHS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=5.3, height=2.9),
                        paragraphs=[
                            Paragraph(
                                text="A program, drawn as a graph:", space_after=6
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{b:nodes:} the inputs and every elementary "
                                    "operation (+, ·, sin, exp, …)",
                                    "{b:arrows:} which result is used where",
                                    "Every program of elementary operations defines "
                                    "one; loops are unrolled.",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.2, width=5.3, height=0.4),
                        paragraphs=[self.heading(text="Example:", space_after=0)],
                        font_size=16,
                    ),
                    self.display(
                        latex=r"f(a, b) = (a + b) \cdot b",
                        top=4.6,
                        height=0.55,
                        left=0.45,
                        width=5.3,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=5.2, width=5.3, height=1.0),
                        paragraphs=[
                            Paragraph(
                                text="with c = a + b. The input b reaches f along "
                                "{a:two paths}.",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    self.video(
                        animation=Animation.COMPUTATIONAL_GRAPH,
                        position=Position(x=5.95, y=1.5),
                        width=7.0,
                    ),
                    TakeAway(
                        text="The graph is the program, written so that it can be "
                        "differentiated."
                    ),
                ],
            ),
            self.backward_pass_slide(),
            ContentSlide(
                title="Forward Mode and Reverse Mode",
                section=Section.COMPUTATIONAL_GRAPHS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.4, width=6.0, height=2.4),
                        paragraphs=[
                            self.heading(text="Forward mode", space_after=6),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Carries a derivative along with every value, "
                                    "from the inputs to the output",
                                    "One pass per input",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.9, top=1.4, width=6.0, height=2.4),
                        paragraphs=[
                            self.heading(
                                text="Reverse mode (backpropagation)", space_after=6
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Forward pass stores the values, backward pass "
                                    "sends the adjoints back",
                                    "One backward pass per output",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.0, width=12.4, height=2.2),
                        paragraphs=[
                            self.heading(text="Which one?", space_after=6),
                            *Paragraph.bullet_points(
                                texts=[
                                    "A loss: millions of inputs (parameters), one "
                                    "output → {a:reverse mode} gives the whole "
                                    "gradient in one backward pass.",
                                    "Few inputs, many outputs → forward mode.",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    TakeAway(
                        text="Backpropagation is reverse mode on the graph of a neural "
                        "network."
                    ),
                ],
            ),
            ContentSlide(
                title="Computational Graphs in Practice",
                section=Section.COMPUTATIONAL_GRAPHS,
                items=[
                    Table(
                        position=Position(x=0.45, y=1.4),
                        column_widths=[1.6, 4.9],
                        rows=[
                            ["Library", "How it builds the graph"],
                            ["PyTorch", "records the operations while the code runs"],
                            ["JAX", "traces Python functions; {m:grad}, {m:jit}"],
                            ["TensorFlow", "graphs of tensor operations"],
                            [
                                "CasADi",
                                "symbolic expressions; Giskard's kinematics and QP",
                            ],
                        ],
                        row_height=0.5,
                        font_size=14,
                    ),
                    CodeBlock.from_file(
                        area=Rectangle(left=7.2, top=1.4, width=5.7, height=2.75),
                        path=Snippet.BACKPROPAGATION.path,
                        font_size=12,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.4, width=12.4, height=1.8),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Giskard writes the robot's kinematics as an expression "
                                "graph and differentiates it into the {a:Jacobians} its "
                                "QP needs.",
                                "PyTorch prints the {a:same numbers} as our backward "
                                "pass by hand: 3 and 8.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="A robot's Jacobians and a network's gradients come from "
                        "the same machinery."
                    ),
                ],
            ),
        ]

    def gradient_source_slide(self) -> Slide:
        """
        :return: Three ways to get a derivative, compared on :math:`f(x) = x^2` at 3.
        """
        point, step = 3.0, 0.001
        exact = 2 * point
        difference = ((point + step) ** 2 - point**2) / step
        columns = [
            (
                "By hand",
                rf"f'(x) = 2x \ \Rightarrow\ f'({point:g}) = {exact:g}",
                [
                    "Exact",
                    "Derived again for every new model",
                    "Tedious for millions of parameters",
                ],
            ),
            (
                "Finite differences",
                rf"\frac{{f({point + step:g}) - f({point:g})}}{{{step:g}}} = "
                rf"{difference:.4f}",
                [
                    "Nudge the input a little, see how f changes",
                    "Only approximate",
                    "n parameters: nudge each one separately – n + 1 runs of f "
                    "per gradient",
                ],
            ),
            (
                "Automatic differentiation",
                rf"x \cdot x \ \to\ 2x \ \Rightarrow\ {exact:g}",
                [
                    "Knows the derivative of every elementary operation and chains "
                    "them",
                    "Exact",
                    "All n partial derivatives for the cost of a few runs of f",
                ],
            ),
        ]
        return ContentSlide(
            title="Where Do Gradients Come From?",
            section=Section.COMPUTATIONAL_GRAPHS,
            items=[
                self.line(
                    text=f"Example: the slope of f(x) = x² at x = {point:g}, which "
                    f"is exactly {exact:g}.",
                    top=1.3,
                ),
                *[
                    element
                    for index, (heading, latex, points) in enumerate(columns)
                    for element in [
                        self.text_box(
                            area=Rectangle(
                                left=0.45 + index * 4.2, top=1.95, width=3.9, height=0.4
                            ),
                            paragraphs=[self.heading(text=heading, space_after=0)],
                        ),
                        self.display(
                            latex=latex,
                            top=2.4,
                            height=0.85,
                            left=0.45 + index * 4.2,
                            width=3.9,
                            font_size=17,
                        ),
                        self.text_box(
                            area=Rectangle(
                                left=0.45 + index * 4.2, top=3.4, width=3.9, height=2.8
                            ),
                            paragraphs=Paragraph.bullet_points(
                                texts=points, space_after=6
                            ),
                            font_size=15,
                        ),
                    ]
                ],
                TakeAway(
                    text="Automatic differentiation: exact gradients at the cost of a "
                    "few function evaluations."
                ),
            ],
        )

    def backward_pass_slide(self) -> Slide:
        """
        :return: The forward and backward pass through :attr:`graph`, as a table.
        """
        nodes = self.graph.nodes
        first, second, total, output = (nodes[label] for label in "abcf")
        value = {label: self.number(value=node.value) for label, node in nodes.items()}
        adjoint = {
            label: self.number(value=node.adjoint) for label, node in nodes.items()
        }
        return ContentSlide(
            title="The Backward Pass: Chain Rule on the Graph",
            section=Section.COMPUTATIONAL_GRAPHS,
            items=[
                self.line(
                    text="The {a:adjoint} v̄ of a node is ∂f/∂v. Start "
                    "with f̄ = 1 and sum what the consumers u of v send back:",
                    top=1.3,
                ),
                self.display(
                    latex=r"\bar v = \sum_{u \text{ uses } v} \bar u \, "
                    r"\frac{\partial u}{\partial v}",
                    top=1.8,
                    height=0.85,
                ),
                Table(
                    position=Position(x=0.9, y=2.85),
                    column_widths=[2.4, 2.0, 3.4, 3.9],
                    rows=[
                        ["Node", "Forward value", "Local derivatives", "Adjoint"],
                        [
                            "f = c · b",
                            value["f"],
                            "∂f/∂c = b,  ∂f/∂b = c",
                            f"f̄ = {adjoint['f']}",
                        ],
                        [
                            "c = a + b",
                            value["c"],
                            "∂c/∂a = ∂c/∂b = 1",
                            f"c̄ = f̄ · b = {adjoint['c']}",
                        ],
                        [
                            "b",
                            value["b"],
                            "",
                            "b̄ = f̄ · c + c̄ · 1 = "
                            f"{self.number(value=output.adjoint * total.value)} + "
                            f"{adjoint['c']} = {adjoint['b']}",
                        ],
                        [
                            "a",
                            value["a"],
                            "",
                            f"ā = c̄ · 1 = {adjoint['a']}",
                        ],
                    ],
                    row_height=0.48,
                    font_size=15,
                ),
                self.line(
                    text="Check: f = ab + b², so ∂f/∂a = b = "
                    f"{value['b']} and ∂f/∂b = a + 2b = "
                    f"{self.number(value=first.value + 2 * second.value)}.",
                    top=5.45,
                    font_size=16,
                ),
                TakeAway(text="Where a value branches, its adjoints add up."),
            ],
        )

    # %% constrained optimization

    def constrained_slides(self) -> list[Slide]:
        """
        :return: The section on linear and quadratic programs, KKT and Giskard.
        """
        return [
            self.contents(highlighted_section=Section.CONSTRAINED),
            *self.linear_program_slides(),
            *self.linear_program_solver_slides(),
            *self.quadratic_program_slides(),
            *self.optimality_slides(),
        ]

    def linear_program_slides(self) -> list[Slide]:
        """
        :return: The definition of linear programs and the robot's fastest gripper LP.
        """
        robot = self.robot
        optimum = robot.linear_optimum
        inequalities = [
            self.latex_inequality(coefficients=row, bound=bound)
            for row, bound in zip(robot.constraint_matrix, robot.constraint_bounds)
            if bound > 0
        ]
        return [
            ContentSlide(
                title="Linear Programs (LP)",
                section=Section.CONSTRAINED,
                items=[
                    self.display(
                        latex=r"\min_x\ c^\top x \quad \text{s.t.} \quad G x \le g, "
                        r"\quad H x = h",
                        top=1.35,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=2.2, width=12.4, height=4.0),
                        paragraphs=[
                            *Paragraph.bullet_points(
                                texts=[
                                    "{b:Linear objective}: its contour lines are "
                                    "straight.",
                                    "{b:Linear constraints}: the feasible region is a "
                                    "convex {a:polyhedron} – flat faces, edges, "
                                    "corners.",
                                    "{b:Real-valued variables}: integer variables make "
                                    "it a different, harder class.",
                                ],
                                space_after=8,
                            ),
                            Paragraph(text="", space_after=6),
                            self.heading(text="Why LPs are “easy”:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "If an optimum exists, one lies at a {a:corner} "
                                    "(vertex) of the polyhedron.",
                                    "Solvers walk from corner to corner ({a:simplex}) "
                                    "or through the interior ({a:interior-point}).",
                                ],
                                space_after=6,
                            ),
                        ],
                    ),
                    TakeAway(
                        text="Linear objective, linear constraints: the optimum is at "
                        "a corner."
                    ),
                ],
            ),
            ContentSlide(
                title="Example: The Fastest Gripper",
                section=Section.CONSTRAINED,
                items=[
                    self.line(
                        text="Ignore the motion cost for a moment: how fast can the "
                        "gripper approach the cup?",
                        top=1.3,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.95, width=5.0, height=0.45),
                        paragraphs=[self.heading(text="Inequality form")],
                        font_size=18,
                    ),
                    self.display(
                        latex=r"\begin{aligned} \max_x\ & x_1 + x_2 \\ \text{s.t.}\ "
                        r"& "
                        + r" \\ & ".join([*inequalities, r"x_1, x_2 \ge 0"])
                        + r" \end{aligned}",
                        top=2.5,
                        height=2.6,
                        left=0.45,
                        width=4.6,
                    ),
                    self.text_box(
                        area=Rectangle(left=5.5, top=1.95, width=5.0, height=0.45),
                        paragraphs=[self.heading(text="Matrix form")],
                        font_size=18,
                    ),
                    self.display(
                        latex=r"\begin{aligned} \max_x\ & J x, \quad J = "
                        + self.latex_matrix(values=robot.gripper_jacobian[None, :])
                        + r" \\ \text{s.t.}\ & "
                        + self.robot_constraints_latex()
                        + r" \end{aligned}",
                        top=2.5,
                        height=2.6,
                        left=5.5,
                        width=7.4,
                    ),
                    TakeAway(
                        text="A linear program over the robot's feasible velocities."
                    ),
                ],
            ),
            BulletSlide(
                title="Example: LP Solution",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.4, width=4.2, height=4.8),
                font_size=17,
                paragraphs=[
                    self.heading(text="Optimal solution:"),
                    *Paragraph.bullet_points(
                        texts=[
                            f"x* = {self.point_text(optimum=optimum)}",
                            f"gripper speed {self.number(value=optimum.value)} cm/s",
                        ],
                        space_after=14,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The arm moves at its limit.",
                            "The {a:elbow} constraint is active.",
                            "The goal of "
                            f"{self.number(value=robot.desired_gripper_speed)} cm/s "
                            "is out of reach.",
                        ],
                        space_after=6,
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.LINEAR_PROGRAM_SOLUTION,
                        position=Position(x=4.8, y=1.3),
                        height=4.9,
                    )
                ],
                take_away="Moving the line of equal speed: the optimum is the last "
                "corner it touches.",
            ),
        ]

    def linear_program_solver_slides(self) -> list[Slide]:
        """
        :return: The slides on the simplex method and interior-point methods.
        """
        return [
            BulletSlide(
                title="Simplex Method",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=7.0, height=4.9),
                font_size=16,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "Every corner is where some constraints are {a:active} "
                            "(hold with equality).",
                            "Start at a corner – for the robot, standing still at "
                            "(0, 0).",
                        ],
                        space_after=8,
                    ),
                    self.heading(text="One iteration (a pivot):"),
                    *[
                        Paragraph(text=step, indent=0.3, space_after=4)
                        for step in [
                            "1. Look at the edges leaving the current corner.",
                            "2. If none improves the objective → optimal.",
                            "3. Otherwise follow an improving edge …",
                            "4. … until the next constraint becomes active: a new "
                            "corner.",
                        ]
                    ],
                    Paragraph(text="", space_after=4),
                    Paragraph(
                        text="Implementations do this with slack variables and a "
                        "{a:tableau}.",
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.SIMPLEX,
                        position=Position(x=7.75, y=1.25),
                        height=4.95,
                    )
                ],
                take_away="Simplex walks along the edges, improving with every pivot.",
            ),
            ContentSlide(
                title="Interior-Point Method (IPM)",
                section=Section.CONSTRAINED,
                items=[
                    self.line(
                        text="{b:Key idea:} move {i:inside} the feasible region toward "
                        "the optimum, instead of along the boundary.",
                        top=1.25,
                    ),
                    self.video(
                        animation=Animation.INTERIOR_POINT,
                        position=Position(x=0.45, y=1.85),
                        width=6.4,
                    ),
                    self.text_box(
                        area=Rectangle(left=7.1, top=1.95, width=5.8, height=0.8),
                        paragraphs=[
                            Paragraph(
                                text="Replace the constraints by a {a:barrier} that "
                                "grows to +∞ at the boundary:",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    self.display(
                        latex=r"\min_x\ -t\, J x - \sum_i \log(g_i - G_i x)",
                        top=2.8,
                        height=0.75,
                        left=7.1,
                        width=5.8,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=7.1, top=3.7, width=5.8, height=2.5),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "An {b:unconstrained} problem: solve it with Newton "
                                "steps.",
                                "Increase t: the barrier weakens and the minimizers "
                                "(the {a:central path}) approach the optimum.",
                            ],
                            space_after=8,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="Constraints become part of an unconstrained objective."
                    ),
                ],
            ),
            ContentSlide(
                title="Summary of LP Solvers",
                section=Section.CONSTRAINED,
                items=[
                    *[
                        self.text_box(
                            area=Rectangle(left=left, top=top, width=6.0, height=2.0),
                            paragraphs=[
                                self.heading(text=heading),
                                *Paragraph.bullet_points(texts=points, space_after=3),
                            ],
                            font_size=16,
                        )
                        for left, top, heading, points in [
                            (
                                0.45,
                                1.5,
                                "Simplex",
                                [
                                    "Walks along the edges of the polyhedron",
                                    "Fast on most problems, exponential worst case",
                                    "Warm start from a previous corner",
                                ],
                            ),
                            (
                                6.9,
                                1.5,
                                "Interior-point methods",
                                [
                                    "Polynomial time",
                                    "Scale well to very large problems",
                                    "Also solve QPs and other convex problems",
                                ],
                            ),
                            (
                                0.45,
                                3.7,
                                "Libraries",
                                [
                                    "{m:scipy.optimize.linprog}, CVXPY",
                                    "HiGHS (open source)",
                                    "Gurobi, MOSEK (commercial)",
                                ],
                            ),
                        ]
                    ],
                    TakeAway(text="No solver is best for all LPs: benchmark."),
                ],
            ),
        ]

    def quadratic_program_slides(self) -> list[Slide]:
        """
        :return: The definition of quadratic programs and the robot's QP.
        """
        robot = self.robot
        optimum = robot.quadratic_optimum
        unconstrained = robot.unconstrained_minimum
        base_weight, arm_weight = robot.joint_weights
        elbow = robot.constraint_matrix[2]
        eigenvalues = np.linalg.eigvalsh(robot.quadratic_cost_matrix)
        return [
            ContentSlide(
                title="Quadratic Programs (QP)",
                section=Section.CONSTRAINED,
                items=[
                    self.line(
                        text="A quadratic objective under linear constraints:", top=1.3
                    ),
                    self.display(
                        latex=r"\min_x\ \tfrac{1}{2} x^\top Q x + c^\top x \quad "
                        r"\text{s.t.} \quad G x \le g, \quad H x = h",
                        top=1.8,
                    ),
                    self.display(
                        latex=r"x^\top Q x = \begin{bmatrix} x_1 & \cdots & x_n "
                        r"\end{bmatrix} \begin{bmatrix} Q_{11} & \cdots & Q_{1n} \\ "
                        r"\vdots & \ddots & \vdots \\ Q_{n1} & \cdots & Q_{nn} "
                        r"\end{bmatrix} \begin{bmatrix} x_1 \\ \vdots \\ x_n "
                        r"\end{bmatrix} = \sum_{i=1}^{n} \sum_{j=1}^{n} Q_{ij}\, x_i "
                        r"x_j",
                        top=2.55,
                        height=1.2,
                        font_size=17,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=3.95, width=12.4, height=2.25),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Qᵢᵢ weighs the square xᵢ², "
                                "Qᵢ{y:ⱼ} the product xᵢx{y:ⱼ}; the ½ "
                                "cancels the 2 of the derivative.",
                                "Convex exactly when all eigenvalues of Q are ≥ 0.",
                                "The feasible region is a polyhedron as before, but the "
                                "contours are {a:ellipses}: the optimum can lie on an "
                                "edge or inside, not only at a corner.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(text="A QP is the next simplest problem after an LP."),
                ],
            ),
            ContentSlide(
                title="The Robot's QP",
                section=Section.CONSTRAINED,
                items=[
                    self.display(
                        latex=r"\min_x\ \underbrace{\tfrac{1}{2} (w_1 x_1^2 + w_2 "
                        r"x_2^2)}_{\text{motion}} + \underbrace{\tfrac{1}{2} w_s (x_1 + "
                        r"x_2 - v_d)^2}_{\text{goal}} \quad \text{s.t.} \quad G x \le g",
                        top=1.35,
                        height=0.95,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=2.5, width=12.4, height=3.7),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{b:Motion term:} prefer small velocities; the base "
                                "costs more than the arm (w₁ = "
                                f"{self.number(value=base_weight)}, w₂ = "
                                f"{self.number(value=arm_weight)}).",
                                "{b:Goal term:} a {a:soft constraint}. The gripper "
                                "should move at v_d = "
                                f"{self.number(value=robot.desired_gripper_speed)} "
                                "cm/s; every cm/s off costs, with weight w{y:ₛ} = "
                                f"{self.number(value=robot.goal_weight)}.",
                                "Giskard writes this with a {a:slack variable} s = "
                                "x₁ + x₂ − v_d and penalizes s².",
                                "{b:Hard constraints} Gx ≤ g: joint limits and "
                                "collision avoidance, as for the LP.",
                            ],
                            space_after=8,
                        ),
                    ),
                    TakeAway(
                        text="Hard constraints must hold; soft constraints are traded "
                        "off in the objective."
                    ),
                ],
            ),
            ContentSlide(
                title="The Robot's QP in Matrix Form",
                section=Section.CONSTRAINED,
                items=[
                    self.display(
                        latex=r"\begin{aligned} \min_x\ & \tfrac{1}{2} x^\top Q x + "
                        r"c^\top x, \quad Q = "
                        + self.latex_matrix(values=robot.quadratic_cost_matrix)
                        + r", \quad c = "
                        + self.latex_matrix(values=robot.linear_cost)
                        + r" \\ \text{s.t.}\ & "
                        + self.robot_constraints_latex()
                        + r" \end{aligned}",
                        top=1.35,
                        height=2.8,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.3, width=12.4, height=1.9),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Expanding the objective gives Q = diag(w) + "
                                "w{y:ₛ} JᵀJ and c = −w{y:ₛ} v_d Jᵀ.",
                                "The goal couples the joints: the off-diagonal entries "
                                "of Q.",
                                "{b:Convex?} The eigenvalues of Q are "
                                f"{self.number(value=eigenvalues[0])} and "
                                f"{self.number(value=eigenvalues[1])}, both ≥ 0: "
                                "yes.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="Giskard assembles exactly these matrices, only larger."
                    ),
                ],
            ),
            BulletSlide(
                title="Example: QP Solution",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.4, width=4.4, height=4.8),
                font_size=16,
                paragraphs=[
                    self.heading(text="Optimal solution:"),
                    *Paragraph.bullet_points(
                        texts=[
                            f"x* = {self.point_text(optimum=optimum)}",
                            "gripper speed "
                            f"{self.number(value=sum(optimum.point))} cm/s",
                        ],
                        space_after=12,
                    ),
                    self.heading(text="Without constraints:"),
                    *Paragraph.bullet_points(
                        texts=[
                            f"x = {self.point_text(optimum=unconstrained)}",
                            "elbow at "
                            + self.number(
                                value=float(elbow @ np.array(unconstrained.point))
                            )
                            + f" > {self.number(value=robot.constraint_bounds[2])} "
                            "cm/s: it would hit the shelf",
                        ],
                        space_after=12,
                    ),
                    Paragraph(
                        text="The optimum lies on the elbow's edge, {a:not at a "
                        "corner}."
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.QUADRATIC_PROGRAM_SOLUTION,
                        position=Position(x=5.1, y=1.3),
                        height=4.9,
                    )
                ],
                take_away="The cost contours grow until they touch the feasible "
                "region.",
            ),
        ]

    def optimality_slides(self) -> list[Slide]:
        """
        :return: The KKT conditions, their check at the robot's optimum, the active set
            method and Giskard's real QP.
        """
        robot = self.robot
        optimum = robot.quadratic_optimum
        unconstrained = robot.unconstrained_minimum
        point = np.array(optimum.point)
        gradient = robot.cost_gradient(point=point)
        multipliers = robot.lagrange_multipliers(point=point)
        elbow_multiplier = multipliers[2]
        elbow = robot.constraint_matrix[2]
        gradient_latex = self.latex_matrix(values=gradient)
        elbow_latex = self.latex_matrix(values=elbow)
        return [
            ContentSlide(
                title="Karush-Kuhn-Tucker (KKT) Conditions",
                section=Section.CONSTRAINED,
                items=[
                    self.line(
                        text="At an optimum x* of a constrained problem there are "
                        "numbers λᵢ, ν{y:ⱼ} (the {a:multipliers}) with:",
                        top=1.3,
                    ),
                    self.display(
                        latex=r"\begin{aligned} & \text{stationarity:} && \nabla "
                        r"f(x^*) + \textstyle\sum_i \lambda_i \nabla g_i(x^*) + "
                        r"\sum_j \nu_j \nabla h_j(x^*) = 0 \\ & \text{feasibility:} && "
                        r"g_i(x^*) \le 0, \quad h_j(x^*) = 0, \quad \lambda_i \ge 0 \\ "
                        r"& \text{complementary slackness:} && \lambda_i\, g_i(x^*) = 0 "
                        r"\end{aligned}",
                        top=1.85,
                        height=1.5,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=3.55, width=12.4, height=2.65),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{b:In words:} the pull of the objective is balanced "
                                "exactly by the push of the constraints it presses "
                                "against.",
                                "A constraint that is not touched (gᵢ < 0) pushes "
                                "with λᵢ = 0.",
                                "Constraints may only push, never pull: λᵢ ≥ 0.",
                                "Without constraints this is just {y:∇}f(x*) = 0. For "
                                "convex problems a point meeting these conditions is a "
                                "global optimum.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(text="KKT generalizes “gradient = 0” to constraints."),
                ],
            ),
            ContentSlide(
                title="KKT at the Robot's Optimum",
                section=Section.CONSTRAINED,
                items=[
                    self.line(
                        text=f"At x* = {self.point_text(optimum=optimum)} only the "
                        "elbow constraint is active. Its gradient and that of the cost:",
                        top=1.3,
                    ),
                    self.display(
                        latex=rf"\nabla f(x^*) = Q x^* + c = {gradient_latex}, \qquad "
                        rf"\nabla g_{{\text{{elbow}}}} = {elbow_latex}",
                        top=1.85,
                        height=0.95,
                    ),
                    self.line(text="Stationarity:", top=2.95),
                    self.display(
                        latex=rf"{gradient_latex} + \lambda {elbow_latex} = 0 \quad "
                        rf"\Longrightarrow \quad \lambda = "
                        rf"{self.latex_number(value=elbow_multiplier)} \ge 0",
                        top=3.35,
                        height=0.95,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.45, width=12.4, height=1.75),
                        paragraphs=[
                            Paragraph(
                                text="All other constraints are inactive and get "
                                "λ = 0. All conditions hold: x* is optimal.",
                                space_after=10,
                            ),
                            Paragraph(
                                text="{b:Meaning:} λ is a {a:shadow price} – "
                                "allowing the elbow 1 cm/s more lowers the optimal cost "
                                f"by about {self.number(value=elbow_multiplier)}.",
                                space_after=0,
                            ),
                        ],
                    ),
                    TakeAway(
                        text="The multipliers tell the robot what each constraint costs."
                    ),
                ],
            ),
            BulletSlide(
                title="Active Set Method",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="{b:Idea:} guess which constraints are active, solve the "
                        "QP with those as {a:equalities}, then correct the guess.",
                        space_after=8,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The solution violates another constraint → add it "
                            "to the guess.",
                            "An active constraint pulls (λᵢ < 0) → remove it.",
                            Paragraph(
                                text="Feasible and all λᵢ ≥ 0 → KKT holds: optimal.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.heading(text="On the robot:"),
                    *[
                        Paragraph(text=step, indent=0.3, space_after=5)
                        for step in [
                            "1. No constraint active: the minimum "
                            f"{self.point_text(optimum=unconstrained)} violates the "
                            "elbow constraint.",
                            "2. Elbow active: the minimum on the elbow's line is "
                            f"{self.point_text(optimum=optimum)}, feasible, with "
                            f"λ = {self.number(value=elbow_multiplier)} ≥ 0: "
                            "optimal.",
                        ]
                    ],
                    Paragraph(text="", space_after=4),
                    Paragraph(
                        text="In a control loop the active constraints barely change "
                        "from one cycle to the next: a {a:warm start} makes each solve "
                        "fast."
                    ),
                ],
                take_away="Solving a QP: guessing the active constraints, checked by "
                "KKT.",
            ),
            BulletSlide(
                title="What Giskard Really Solves",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="The toy robot has the structure of Giskard's QP, scaled "
                        "up:",
                        space_after=8,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Variables:} velocities of all joints – and their "
                            "accelerations and jerks over a short prediction horizon",
                            "{b:Soft constraints:} one slack per goal; their weights "
                            "decide which goal gives way first",
                            "{b:Hard constraints:} position, velocity, acceleration and "
                            "jerk limits of every joint; collision avoidance from "
                            "distances, linearized with Jacobians",
                            "{b:Objective:} weighted squares of all variables and "
                            "slacks: a convex QP",
                            "{b:Jacobians:} differentiated from the kinematics' "
                            "computational graph",
                            Paragraph(
                                text="Solved again in {a:every control cycle}, warm "
                                "started from the last one",
                                level=BulletLevel.FIRST,
                                space_after=12,
                            ),
                        ],
                        space_after=6,
                    ),
                    Paragraph(
                        text="S. Stelter, G. Bartels, M. Beetz (2022): An open-source "
                        "motion planning framework for mobile manipulators using "
                        "constraint-based task space control with linear MPC. IROS",
                        font_size=12,
                    ),
                ],
                take_away="Convex, so its optimum is unique – and fast enough to "
                "find many times per second.",
            ),
        ]

    # %% likelihood

    def likelihood_slides(self) -> list[Slide]:
        """
        :return: The outlook on maximum likelihood, the takeaways and the reading list.
        """
        estimate = self.grasps.maximum_likelihood_estimate
        return [
            self.contents(highlighted_section=Section.LIKELIHOOD),
            ContentSlide(
                title="Fitting a Model Is Maximizing a Likelihood",
                section=Section.LIKELIHOOD,
                items=[
                    self.line(
                        text="Model: y = θᵀx + noise, the noise Gaussian with "
                        "spread σ. Data: N samples (x{y:ⱼ}, y{y:ⱼ}).",
                        top=1.3,
                    ),
                    self.line(
                        text="The {a:likelihood}: how probable the data is for "
                        "parameters θ.",
                        top=1.85,
                    ),
                    self.display(
                        latex=r"L(\theta) = \prod_{j=1}^{N} p(y_j \mid x_j, \theta)",
                        top=2.3,
                        height=0.85,
                    ),
                    self.line(
                        text="Its negative logarithm, for Gaussian noise:", top=3.25
                    ),
                    self.display(
                        latex=r"-\log L(\theta) = \frac{1}{2\sigma^2} \sum_{j=1}^{N} "
                        r"(y_j - \theta^\top x_j)^2 + N \log(\sigma \sqrt{2\pi})",
                        top=3.7,
                        height=0.85,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.7, width=12.4, height=1.5),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Maximizing the likelihood = minimizing the squared "
                                "error: {a:least squares}.",
                                "The logarithm keeps the maximizer and turns the "
                                "product into a {a:sum over samples} – ready for "
                                "SGD.",
                            ],
                            space_after=6,
                        ),
                    ),
                    TakeAway(
                        text="Learning is optimizing the likelihood (→ "
                        "Uncertainty, 03.12.)."
                    ),
                ],
            ),
            ContentSlide(
                title="Maximum Likelihood under a Constraint",
                section=Section.LIKELIHOOD,
                items=[
                    self.line(
                        text=f"The robot logged {self.grasps.attempt_count} grasps in "
                        "its episodic memory (NEEMs, lecture 02). How likely is each "
                        "outcome?",
                        top=1.3,
                    ),
                    Table(
                        position=Position(x=0.6, y=2.2),
                        column_widths=[1.6, 1.3, 1.8],
                        rows=[
                            ["Outcome", "Count", "Estimate"],
                            *[
                                [
                                    outcome.value,
                                    f"n = {count}",
                                    f"p = {estimate[outcome]:.2f}",
                                ]
                                for outcome, count in self.grasps.counts.items()
                            ],
                        ],
                        row_height=0.48,
                        font_size=15,
                    ),
                    self.display(
                        latex=r"\max_p\ \sum_k n_k \log p_k \quad \text{s.t.} \quad "
                        r"\sum_k p_k = 1",
                        top=2.1,
                        height=0.85,
                        left=5.7,
                        width=7.2,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=5.7, top=3.05, width=7.2, height=0.8),
                        paragraphs=[
                            Paragraph(
                                text="Stationarity with a multiplier ν for the "
                                "equality constraint:",
                                space_after=0,
                            )
                        ],
                        font_size=16,
                    ),
                    self.display(
                        latex=r"\frac{n_k}{p_k} = \nu \quad \Longrightarrow \quad "
                        r"\nu = N, \quad p_k = \frac{n_k}{N}",
                        top=3.8,
                        height=0.85,
                        left=5.7,
                        width=7.2,
                        font_size=18,
                    ),
                    self.text_box(
                        area=Rectangle(left=5.7, top=4.8, width=7.2, height=1.4),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Concave objective, linear constraint: a convex "
                                "problem.",
                                "The estimate is the relative frequency – the "
                                "numerical solver agrees.",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="KKT turns a constrained likelihood into a one-line "
                        "estimate."
                    ),
                ],
            ),
            BulletSlide(
                title="Key Takeaways",
                section=Section.LIKELIHOOD,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    *[
                        Paragraph(text=f"{index}. {point}", indent=0.3, space_after=8)
                        for index, point in enumerate(
                            [
                                "An optimization problem: objective, decision "
                                "variables, constraints.",
                                "Convex problems: every local minimum is global.",
                                "Gradient descent follows −{y:∇}f; momentum, "
                                "SGD and Adam make it fast and scalable.",
                                "Computational graphs give exact gradients: the "
                                "backward pass is the chain rule.",
                                "LPs have their optimum at a corner; QPs on an edge, a "
                                "corner or inside.",
                                "KKT: active constraints balance the gradient; the "
                                "multipliers price the constraints.",
                                "Giskard moves the robot by solving a convex QP every "
                                "control cycle.",
                            ],
                            start=1,
                        )
                    ],
                    Paragraph(text="", space_after=6),
                    Paragraph(text="{s:Next week:} Data-Intensive Systems"),
                ],
            ),
            BulletSlide(
                title="Further Reading",
                section=Section.LIKELIHOOD,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=5.4),
                font_size=14,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "S. Boyd, L. Vandenberghe (2004): Convex Optimization. "
                        "Cambridge University Press. Free at "
                        "{m:stanford.edu/~boyd/cvxbook}",
                        "J. Nocedal, S. J. Wright (2006): Numerical Optimization, 2nd "
                        "ed. Springer",
                        "I. Goodfellow, Y. Bengio, A. Courville (2016): Deep Learning. "
                        "MIT Press. Ch. 4 (numerical computation), 6.5 "
                        "(back-propagation), 8 (optimization for training)",
                        "S. J. D. Prince (2023): Understanding Deep Learning. MIT "
                        "Press. Ch. 6 (fitting models), 7 (gradients)",
                        "A. G. Baydin, B. A. Pearlmutter, A. A. Radul, J. M. Siskind "
                        "(2018): Automatic Differentiation in Machine Learning: a "
                        "Survey. JMLR 18",
                        "D. P. Kingma, J. Ba (2015): Adam: A Method for Stochastic "
                        "Optimization. ICLR",
                        "S. Stelter, G. Bartels, M. Beetz (2022): An open-source motion "
                        "planning framework for mobile manipulators using "
                        "constraint-based task space control with linear MPC. IROS",
                        "Giskard: {m:github.com/SemRoCo/giskardpy}",
                    ],
                    space_after=8,
                ),
            ),
        ]


# %% command line


def main() -> None:
    """
    Write the lecture to PowerPoint and PDF next to this module.
    """
    deck = IntroductionToOptimization().deck()
    output = Path(__file__).with_suffix("")
    PowerPointRenderer(deck=deck, path=output.with_suffix(".pptx")).render()
    PDFRenderer(deck=deck, path=output.with_suffix(".pdf")).render()
    print(f"{len(deck.slides)} slides -> {output}.pptx / .pdf")


if __name__ == "__main__":
    main()
