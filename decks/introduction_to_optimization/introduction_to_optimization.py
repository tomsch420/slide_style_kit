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
from slide_style_kit.components import CodeBlock, Matrix, TakeAway
from slide_style_kit.deck import Deck, PageDecoration
from slide_style_kit.elements import Element, Paragraph, Table, TextFrame, Video
from slide_style_kit.geometry import Length, Position, Rectangle
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
from slide_style_kit.style import Alignment, BulletLevel, VerticalAnchor

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
    Adam with its default decays, whose values the Adam slide states.
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

    def formula(
        self, *, text: str, font_size: float | None = None, space_after: float = 10
    ) -> Paragraph:
        """
        :return: A displayed formula, centred on its own line.
        """
        return Paragraph(
            text=text,
            alignment=Alignment.CENTER,
            font_size=font_size or self.formula_font_size,
            space_after=space_after,
        )

    def number(self, *, value: float) -> str:
        """
        :return: *value* with as many decimals as it needs and a typographic minus.
        """
        return f"{value:.4g}".replace("-", "\u2212")

    def point_text(self, *, optimum: Optimum) -> str:
        """
        :return: The markup of the point of *optimum*, such as ``(2.5, 25)``.
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

    def aligned_formulas(
        self,
        *,
        labels: list[str],
        expressions: list[str],
        position: Position,
        label_width: float,
        expression_width: float,
        font_size: float = 18,
        line_height: float = 1.6,
    ) -> list[Element]:
        """
        :param labels: The markup left of each expression, such as ``max`` or ``s.t.``;
            an empty string leaves the line unlabelled.
        :param expressions: The markup of each line of the formula.
        :param line_height: The height reserved per line, in font sizes.
        :return: The labels in one column and the expressions aligned in the next.
        """
        height = len(expressions) * font_size * line_height / Length.points_per_inch
        return [
            TextFrame(
                area=Rectangle(
                    left=position.x, top=position.y, width=label_width, height=height
                ),
                paragraphs=[Paragraph(text=label) for label in labels],
                font_size=font_size,
            ),
            TextFrame(
                area=Rectangle(
                    left=position.x + label_width,
                    top=position.y,
                    width=expression_width,
                    height=height,
                ),
                paragraphs=[Paragraph(text=expression) for expression in expressions],
                font_size=font_size,
            ),
        ]

    def matrix_label(
        self, *, text: str, area: Rectangle, font_size: float = 18
    ) -> TextFrame:
        """
        :return: The markup *text* right-aligned and vertically centred in *area*,
            in front of a matrix.
        """
        return TextFrame(
            area=area,
            paragraphs=[Paragraph(text=text, alignment=Alignment.RIGHT, space_after=0)],
            font_size=font_size,
            anchor=VerticalAnchor.MIDDLE,
        )

    def inequality_text(self, *, coefficients: np.ndarray, bound: float) -> str:
        """
        :return: The markup of :math:`a^T x \\le b` for the two joint velocities, such
            as ``x₁ + 0.5 x₂ ≤ 15``.
        """
        terms = [
            variable
            if coefficient == 1
            else f"{self.number(value=coefficient)} {variable}"
            for coefficient, variable in zip(coefficients, ["x\u2081", "x\u2082"])
            if coefficient != 0
        ]
        return f"{{y:{' + '.join(terms)} \u2264 {self.number(value=bound)}}}"

    def matrix_entries(self, *, values: np.ndarray) -> list[list[str]]:
        """
        :return: The entries of the matrix or column vector *values* as text.
        """
        rows = values if values.ndim == 2 else values[:, None]
        return [[self.number(value=entry) for entry in row] for row in rows]

    def constraint_matrices(self, *, top: float, left: float = 6.9) -> list[Element]:
        """
        :return: The constraints :math:`Gx \\le g` of the robot as matrices, from *top*
            down.
        """
        return [
            self.matrix_label(
                text="{y:s.t.   Gx \u2264 g,   G =}",
                area=Rectangle(left=left, top=top, width=2.6, height=1.6),
            ),
            Matrix(
                position=Position(x=left + 2.7, y=top),
                entries=self.matrix_entries(values=self.robot.constraint_matrix),
            ),
            self.matrix_label(
                text="{y:,   g =}",
                area=Rectangle(left=left + 3.85, top=top, width=0.75, height=1.6),
            ),
            Matrix(
                position=Position(x=left + 4.7, y=top),
                entries=self.matrix_entries(values=self.robot.constraint_bounds),
                column_width=0.6,
            ),
        ]

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
                    Paragraph(text="After this lecture you can \u2026", space_after=12),
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
                                    "{a:numbers} in rule bodies \u2013 announced for "
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
                                    "Lecture 01: the performance measure "
                                    "{y:state \u00d7 action \u2192 \u211d} \u2013 "
                                    "optimization picks the action",
                                    "Lecture 02: how does Giskard turn \u201cgrasp the "
                                    "cup\u201d into joint velocities?",
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
                                    "How do we reason with incomplete knowledge \u2013 "
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
                        text="Today's tools \u2013 gradients, constraints, KKT \u2013 "
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
                            "{b:Goals} (\u201cgripper to the cup\u201d) become {i:soft} "
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
                        "Today we build and solve a version with {a:two joints} \u2013 "
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
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.5),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Two joints: {y:x\u2081} = velocity of the {a:base}, "
                                "{y:x\u2082} = velocity of the {a:arm}, both in cm/s",
                                "The gripper moves forward at {y:v = x\u2081 + x\u2082}, "
                                "the elbow at {y:x\u2081 + "
                                f"{self.number(value=elbow_share)} x\u2082}}",
                            ],
                            space_after=6,
                        ),
                    ),
                    Table(
                        position=Position(x=0.9, y=2.8),
                        column_widths=[2.6, 3.2, 5.9],
                        rows=[
                            ["Constraint", "Formula", "Meaning"],
                            [
                                "Base limit",
                                self.inequality_text(
                                    coefficients=robot.constraint_matrix[0],
                                    bound=base_limit,
                                ),
                                "the base is slow",
                            ],
                            [
                                "Arm limit",
                                self.inequality_text(
                                    coefficients=robot.constraint_matrix[1],
                                    bound=arm_limit,
                                ),
                                "the arm is faster",
                            ],
                            [
                                "Collision avoidance",
                                self.inequality_text(
                                    coefficients=robot.constraint_matrix[2],
                                    bound=elbow_limit,
                                ),
                                "the elbow approaches a shelf at most "
                                f"{self.number(value=elbow_limit)} cm/s",
                            ],
                            [
                                "Forward only",
                                "{y:x\u2081 \u2265 0,  x\u2082 \u2265 0}",
                                "no joint moves away from the cup",
                            ],
                            [
                                "Goal (soft)",
                                "{y:x\u2081 + x\u2082 \u2248 "
                                f"{self.number(value=robot.desired_gripper_speed)}}}",
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
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.25, width=12.4, height=1.2),
                        paragraphs=[
                            Paragraph(
                                text="Choose the {a:decision variables} {y:x} that "
                                "minimize an {a:objective} {y:f}:",
                                space_after=10,
                            ),
                            self.formula(
                                text="{y:min\u2093 f(x)}    subject to (s.t.)    "
                                "{y:x \u2208 C}"
                            ),
                        ],
                        font_size=18,
                    ),
                    self.video(
                        animation=Animation.FEASIBLE_REGION,
                        position=Position(x=0.6, y=2.5),
                        width=4.2,
                    ),
                    TextFrame(
                        area=Rectangle(left=0.6, top=5.7, width=5.4, height=0.55),
                        paragraphs=[
                            Paragraph(
                                text="{a:Feasible region C}: all points that satisfy "
                                "the constraints.",
                                space_after=0,
                            )
                        ],
                        font_size=14,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.3, top=2.6, width=6.6, height=3.6),
                        paragraphs=[
                            self.heading(text="Examples:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{b:Robot:} joint velocities that reach the goal "
                                    "within the limits",
                                    "{b:Learning:} parameters that minimize a loss or "
                                    "maximize a likelihood ({y:\u2192} Uncertainty)",
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
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.6, width=12.4, height=0.5),
                        paragraphs=[
                            Paragraph(
                                text="The general form of an optimization problem:"
                            )
                        ],
                        font_size=18,
                    ),
                    *self.aligned_formulas(
                        labels=["{y:min}", "{y:s.t.}", ""],
                        expressions=[
                            "{y:f(x),   x \u2208 \u211d\u207f}",
                            "{y:g\u1d62(x) \u2264 0,   i = 1, \u2026, m}",
                            "{y:h\u2c7c(x) = 0,   j = 1, \u2026, p}",
                        ],
                        position=Position(x=0.9, y=2.6),
                        label_width=0.9,
                        expression_width=4.0,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.3, top=2.4, width=6.6, height=2.6),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{y:f(x)} is the {a:objective function}",
                                "{y:x} are the {a:decision variables}",
                                "{y:g\u1d62(x) \u2264 0} are {y:m} inequality "
                                "constraints",
                                "{y:h\u2c7c(x) = 0} are {y:p} equality constraints",
                            ],
                            space_after=6,
                        ),
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=5.1, width=12.4, height=1.1),
                        paragraphs=[
                            Paragraph(
                                text="{b:Maximizing} is minimizing the negative: "
                                "{y:max f(x) = \u2212min (\u2212f(x))}. The robot's LP "
                                "maximizes, everything else today minimizes.",
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
                            ["{a:Unconstrained}", "{y:min\u2093 f(x)}"],
                            [
                                "{a:Constrained}",
                                "{y:min\u2093 f(x)   s.t.   g\u1d62(x) \u2264 0,  "
                                "h\u2c7c(x) = 0}",
                            ],
                            ["{a:Linear (LP)}", "objective linear, constraints linear"],
                            [
                                "{a:Quadratic (QP)}",
                                "objective quadratic, constraints linear",
                            ],
                            [
                                "{a:Convex}",
                                "feasible set and objective convex {y:\u2192} every "
                                "local minimum is global",
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
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=2.2),
                        paragraphs=[
                            self.heading(text="Smooth functions:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    Paragraph(
                                        text="{y:f(x)} has a well-defined derivative "
                                        "(gradient) everywhere, and it changes "
                                        "continuously.",
                                        level=BulletLevel.FIRST,
                                        space_after=14,
                                    ),
                                ],
                                space_after=4,
                            ),
                            self.heading(text="Gradient {y:\u2207f(x)}:"),
                            *Paragraph.bullet_points(
                                texts=["Collects all partial derivatives of {y:f}."]
                            ),
                        ],
                        font_size=17,
                    ),
                    self.matrix_label(
                        text="{y:\u2207f(x) =}",
                        area=Rectangle(left=4.4, top=3.4, width=1.6, height=1.2),
                    ),
                    Matrix(
                        position=Position(x=6.1, y=3.4),
                        entries=[
                            ["{y:\u2202f/\u2202x\u2081}"],
                            ["{y:\u22ee}"],
                            ["{y:\u2202f/\u2202x\u2099}"],
                        ],
                        column_width=1.0,
                        row_height=0.4,
                    ),
                    TextFrame(
                        area=Rectangle(left=0.45, top=4.85, width=12.4, height=1.3),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Describes how {y:f(x)} changes locally as we move in "
                                "different directions.",
                                "The gradient tells us how to {i:move} to reduce the "
                                "function value.",
                            ],
                            space_after=6,
                        ),
                        font_size=17,
                    ),
                    TakeAway(text="The gradient is the local map of the landscape."),
                ],
            ),
            ContentSlide(
                title="Geometric Meaning of the Gradient",
                section=Section.UNCONSTRAINED,
                items=[
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.25, width=12.4, height=1.3),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{y:\u2207f(x)} points in the direction of the "
                                "{a:steepest increase} of {y:f}.",
                                "Moving in the opposite direction makes {y:f(x)} "
                                "decrease fastest.",
                            ],
                            space_after=4,
                        ),
                        font_size=17,
                    ),
                    self.video(
                        animation=Animation.GRADIENT_BOWL,
                        position=Position(x=3.9, y=2.3),
                        width=5.6,
                    ),
                    TakeAway(
                        text="To minimize {y:f(x)}, move along {y:\u2212\u2207f(x)}."
                    ),
                ],
            ),
            BulletSlide(
                title="Critical Points and \u201cGradient = 0\u201d",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.25, width=7.6, height=5.0),
                font_size=17,
                paragraphs=[
                    self.heading(text="Unconstrained minimum:"),
                    *Paragraph.bullet_points(
                        texts=[
                            "For smooth functions in {y:\u211d\u207f}, a minimum must "
                            "satisfy:"
                        ],
                        space_after=4,
                    ),
                    self.formula(text="{y:\u2207f(x*) = 0}", font_size=18),
                    *Paragraph.bullet_points(
                        texts=[
                            Paragraph(
                                text="Otherwise {y:\u2212\u2207f(x*)} would be a "
                                "direction that decreases {y:f}.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.heading(text="Types of critical points:"),
                    *Paragraph.bullet_points(
                        texts=["minima,", "maxima,", "saddle points."], space_after=2
                    ),
                    Paragraph(
                        text="The {a:Hessian} {y:\u2207\u00b2f(x*)} tells them apart: "
                        "positive definite {y:\u2192} minimum, indefinite {y:\u2192} "
                        "saddle point."
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.CRITICAL_POINTS,
                        position=Position(x=8.2, y=2.0),
                        width=4.6,
                    )
                ],
                take_away="{y:\u2207f = 0} is necessary, not sufficient \u2013 unless "
                "{y:f} is convex.",
            ),
        ]

    def convexity_slides(self) -> list[Slide]:
        """
        :return: The slides defining and testing convexity, and why it matters.
        """
        eigenvalues = np.linalg.eigvalsh(self.robot.quadratic_cost_matrix)
        return [
            BulletSlide(
                title="Convex Sets and Convex Functions",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="{b:Convex set} {y:C}: the segment between any two points "
                        "stays inside,   {y:\u03b8x + (1 \u2212 \u03b8)y \u2208 C}  for "
                        "all {y:x, y \u2208 C,  \u03b8 \u2208 [0, 1]}",
                        space_after=8,
                    ),
                    Paragraph(
                        text="{b:Convex function} {y:f}: the chord lies above the graph,"
                        "   {y:f(\u03b8x + (1 \u2212 \u03b8)y) \u2264 \u03b8f(x) + "
                        "(1 \u2212 \u03b8)f(y)}",
                        space_after=8,
                    ),
                    Paragraph(
                        text="Every polyhedron {y:{x : Gx \u2264 g}} is convex \u2013 such "
                        "as the toy robot's feasible velocities.",
                        space_after=0,
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.CONVEXITY,
                        position=Position(x=3.65, y=3.25),
                        height=3.0,
                    )
                ],
                take_away="Linear constraints always give a convex feasible region.",
            ),
            ContentSlide(
                title="Testing Convexity",
                section=Section.UNCONSTRAINED,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.1),
                        paragraphs=[
                            Paragraph(
                                text="A twice differentiable {y:f} is convex if and only "
                                "if its Hessian is positive semidefinite everywhere:",
                                space_after=6,
                            ),
                            self.formula(
                                text="{y:\u2207\u00b2f(x) \u2ab0 0}      (one variable: "
                                "{y:f\u2033(x) \u2265 0})",
                                font_size=18,
                                space_after=0,
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=2.6, width=6.0, height=3.6),
                        paragraphs=[
                            self.heading(text="Convex"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "linear functions {y:c\u1d40x}",
                                    "{y:\u2016x\u2016\u00b2} and {y:\u00bd x\u1d40Qx + "
                                    "c\u1d40x} with {y:Q \u2ab0 0}",
                                    "{y:\u2212log x} \u2013 the negative "
                                    "log-likelihood comes back later",
                                    "sums with non-negative weights, and a convex "
                                    "function of a linear map",
                                ],
                                space_after=5,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.9, top=2.6, width=6.0, height=3.6),
                        paragraphs=[
                            self.heading(text="Not convex"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{y:sin x}, the peaks function",
                                    "the loss of a neural network",
                                    "the free space around an obstacle",
                                ],
                                space_after=5,
                            ),
                        ],
                        font_size=16,
                    ),
                    TakeAway(
                        text="The robot's cost matrix {y:Q} has eigenvalues "
                        f"{self.number(value=eigenvalues[0])} and "
                        f"{self.number(value=eigenvalues[1])}: its cost is convex."
                    ),
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
                        text="If {y:f} and the feasible region {y:C} are convex, then",
                        space_after=4,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "every {a:local} minimum is a {a:global} minimum,",
                            "the minimizers form a convex set,",
                            Paragraph(
                                text="without constraints, {y:\u2207f(x*) = 0} is "
                                "{i:sufficient} for a minimum.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.heading(text="Why:"),
                    Paragraph(
                        text="If {y:y} were better than a local minimum {y:x}, convexity "
                        "makes every point on the segment from {y:x} to {y:y} better "
                        "than {y:x} \u2013 also the points arbitrarily close to {y:x}.",
                        space_after=14,
                    ),
                    self.heading(text="Consequence:"),
                    *Paragraph.bullet_points(
                        texts=[
                            "Convex problems (LP, QP with {y:Q \u2ab0 0}, least squares) "
                            "are solved reliably, to the global optimum.",
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
        return [
            BulletSlide(
                title="Example: Minimizing a Quadratic Function",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=18,
                paragraphs=[
                    self.heading(text="Quadratic model:"),
                    self.formula(
                        text="{y:f(x) = \u00bd x\u1d40Qx + c\u1d40x,}", space_after=4
                    ),
                    Paragraph(
                        text="where {y:Q} is symmetric ({y:Q = Q\u1d40}) and positive "
                        "definite.",
                        space_after=14,
                    ),
                    self.heading(text="Gradient:"),
                    self.formula(
                        text="{y:\u2207f(x) = \u00bd (Q + Q\u1d40)x + c = Qx + c}",
                        space_after=14,
                    ),
                    self.heading(text="Critical point:"),
                    self.formula(
                        text="{y:Qx* + c = 0      \u27f9      x* = \u2212Q\u207b\u00b9c}",
                        space_after=14,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Convex, with a unique global minimum.",
                            "A local approximation of every smooth function near a "
                            "minimum.",
                        ],
                        space_after=4,
                    ),
                ],
                take_away="Giskard's cost is a quadratic like this one.",
            ),
            BulletSlide(
                title="Linear Least Squares",
                section=Section.UNCONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.6, width=12.4, height=4.6),
                font_size=18,
                paragraphs=[
                    self.heading(text="Problem:"),
                    self.formula(
                        text="{y:min\u2093 \u2016Ax \u2212 b\u2016\u00b2 = "
                        "x\u1d40(A\u1d40A)x \u2212 2b\u1d40Ax + b\u1d40b}"
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{y:A \u2208 \u211d\u1d50\u02e3\u207f,  b \u2208 "
                            "\u211d\u1d50}: one row per measurement.",
                            "A quadratic with {y:Q = 2A\u1d40A}, so it has a "
                            "{a:closed-form solution}:",
                        ],
                        space_after=4,
                    ),
                    self.formula(
                        text="{y:x* = (A\u1d40A)\u207b\u00b9A\u1d40b}", space_after=18
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Used in regression, calibration and data fitting.",
                            "For many parameters or many samples: gradient descent "
                            "instead.",
                        ],
                        space_after=4,
                    ),
                ],
                take_away="Least squares comes back as maximum likelihood at the end.",
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
        ]

    def gradient_descent_slides(self) -> list[Slide]:
        """
        :return: The slides on gradient descent, its step size and its problems.
        """
        return [
            BulletSlide(
                title="Gradient Descent: Core Idea",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=6.4, top=1.7, width=6.5, height=4.5),
                font_size=18,
                paragraphs=[
                    Paragraph(
                        text="{b:Goal:} Minimize an {i:unconstrained} function {y:f(x)}.",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The gradient {y:\u2207f(x)} points in the direction of "
                            "{a:steepest ascent}.",
                            Paragraph(
                                text="The {a:negative} gradient points toward "
                                "{i:steepest descent}.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=4,
                    ),
                    Paragraph(
                        text="Move a small step {i:against} the gradient:",
                        space_after=10,
                    ),
                    self.formula(
                        text="{y:x\u2096\u208a\u2081 = x\u2096 \u2212 \u03b1 "
                        "\u2207f(x\u2096)}",
                        space_after=14,
                    ),
                    Paragraph(
                        text="where {y:\u03b1} is the {a:step size} or {a:learning "
                        "rate}."
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.GRADIENT_DESCENT_SURFACE,
                        position=Position(x=0.6, y=1.3),
                        width=4.9,
                    )
                ],
                take_away="Gradient descent only needs {y:\u2207f} \u2013 no closed "
                "form.",
            ),
            BulletSlide(
                title="Gradient Descent: Where Does the Update Come From?",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=0.45, top=1.6, width=12.4, height=4.6),
                font_size=18,
                paragraphs=[
                    self.heading(text="Local linear approximation:"),
                    self.formula(
                        text="{y:f(x + \u0394x) \u2248 f(x) + \u2207f(x)\u1d40\u0394x}",
                        space_after=22,
                    ),
                    Paragraph(
                        text="We want a step {y:\u0394x} of fixed length that makes "
                        "{y:f(x + \u0394x)} as {a:small} as possible.",
                        space_after=22,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The inner product {y:\u2207f(x)\u1d40\u0394x} is smallest "
                            "when {y:\u0394x} points opposite to {y:\u2207f(x)}:"
                        ],
                        space_after=14,
                    ),
                    self.formula(text="{y:\u0394x = \u2212\u03b1\u2207f(x)}"),
                ],
                take_away="{y:\u2212\u2207f} is the direction of steepest descent.",
            ),
            ContentSlide(
                title="Choosing a Step Size (Learning Rate)",
                section=Section.GRADIENT_METHODS,
                items=[
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.3),
                        paragraphs=[
                            self.heading(text="The learning rate {y:\u03b1} controls:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "{a:How far} we move in the descent direction.",
                                    "Stability and convergence speed.",
                                ],
                                space_after=4,
                            ),
                        ],
                        font_size=17,
                    ),
                    TextFrame(
                        area=Rectangle(left=3.2, top=2.75, width=3.8, height=1.3),
                        paragraphs=[
                            self.heading(text="Small {y:\u03b1}:"),
                            *Paragraph.bullet_points(
                                texts=["Very stable", "Converges slowly"], space_after=4
                            ),
                        ],
                        font_size=17,
                    ),
                    TextFrame(
                        area=Rectangle(left=7.5, top=2.75, width=4.6, height=1.3),
                        paragraphs=[
                            self.heading(text="Large {y:\u03b1}:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Faster progress",
                                    "Risk of overshooting or divergence",
                                ],
                                space_after=4,
                            ),
                        ],
                        font_size=17,
                    ),
                    TextFrame(
                        area=Rectangle(left=0.45, top=4.25, width=12.4, height=1.95),
                        paragraphs=[
                            self.heading(text="In practice:"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Constant {y:\u03b1} (simple)",
                                    "Decreasing schedule",
                                    "{a:Line search}: try steps along {y:\u2212\u2207f} "
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
                text_area=Rectangle(left=6.4, top=2.0, width=6.5, height=4.2),
                font_size=18,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "Gradient is large far from the optimum {y:\u21d2} big "
                            "steps.",
                            "Gradient becomes small near the optimum {y:\u21d2} smaller "
                            "steps.",
                            Paragraph(
                                text="Steps point roughly toward the optimum.",
                                level=BulletLevel.FIRST,
                                space_after=18,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.heading(text="Stop when:"),
                    self.formula(text="{y:\u2016\u2207f(x\u2096)\u2016 < \u03b5}"),
                ],
                items=[
                    self.video(
                        animation=Animation.CONVERGENCE,
                        position=Position(x=1.0, y=1.75),
                        width=4.3,
                    )
                ],
                take_away="With a fixed {y:\u03b1}, the steps shrink by themselves.",
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
                                "Gradient almost zero: progress stalls",
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
        :return: The slides on momentum, stochastic gradient descent and Adam.
        """
        adam = self.adam
        return [
            BulletSlide(
                title="Momentum",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=0.45, top=1.6, width=12.4, height=4.6),
                font_size=18,
                paragraphs=[
                    Paragraph(
                        text="{b:Problem:} Gradient descent zig-zags in narrow valleys.",
                        space_after=10,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Accumulate a moving average of past steps (a velocity).",
                            "Directions that consistently decrease the objective build "
                            "up speed.",
                            Paragraph(
                                text="Directions that flip sign cancel out.",
                                level=BulletLevel.FIRST,
                                space_after=22,
                            ),
                        ],
                        space_after=4,
                    ),
                    self.formula(
                        text="{y:v\u2096\u208a\u2081 = \u03b2v\u2096 \u2212 "
                        "\u03b1\u2207f(x\u2096)}",
                        space_after=4,
                    ),
                    self.formula(
                        text="{y:x\u2096\u208a\u2081 = x\u2096 + v\u2096\u208a\u2081}",
                        space_after=14,
                    ),
                    Paragraph(text="with {y:\u03b2 \u2208 [0, 1)}."),
                ],
                take_away="Momentum remembers where it was going.",
            ),
            BulletSlide(
                title="Stochastic Gradient Descent (SGD)",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=0.45, top=1.3, width=6.9, height=4.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="Learning objectives are {a:averages over samples}:",
                        space_after=6,
                    ),
                    self.formula(
                        text="{y:f(\u03b8) = 1/N \u2211\u2c7c \u2113\u2c7c(\u03b8)}",
                        font_size=18,
                        space_after=6,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "One gradient of {y:f} costs {y:N} sample gradients.",
                            "SGD draws a random {a:minibatch} {y:B} per step:",
                        ],
                        space_after=4,
                    ),
                    self.formula(
                        text="{y:\u03b8 \u2190 \u03b8 \u2212 \u03b1 \u00b7 1/|B| "
                        "\u2211\u2c7c\u2208B \u2207\u2113\u2c7c(\u03b8)}",
                        font_size=18,
                        space_after=6,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The minibatch gradient is {a:unbiased}: its expectation "
                            "is {y:\u2207f(\u03b8)}.",
                            "Cheap but noisy steps; decrease {y:\u03b1} to settle.",
                            "One pass through all samples is an {a:epoch}.",
                        ],
                        space_after=4,
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.STOCHASTIC_GRADIENT_DESCENT,
                        position=Position(x=7.6, y=1.6),
                        width=5.3,
                    )
                ],
                take_away="SGD never needs all data at once ({y:\u2192} Data-Intensive "
                "Systems, 26.11.).",
            ),
            BulletSlide(
                title="Adam: Adaptive Step Sizes",
                section=Section.GRADIENT_METHODS,
                text_area=Rectangle(left=0.45, top=1.3, width=7.4, height=4.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="Momentum plus a {a:step size per coordinate}, with "
                        "{y:g\u2096 = \u2207f(x\u2096)}:",
                        space_after=8,
                    ),
                    self.formula(
                        text="{y:m\u2096 = \u03b2\u2081m\u2096\u208b\u2081 + "
                        "(1 \u2212 \u03b2\u2081)g\u2096}",
                        font_size=17,
                        space_after=2,
                    ),
                    self.formula(
                        text="{y:s\u2096 = \u03b2\u2082s\u2096\u208b\u2081 + "
                        "(1 \u2212 \u03b2\u2082)g\u2096\u00b2}",
                        font_size=17,
                        space_after=2,
                    ),
                    self.formula(
                        text="{y:x\u2096\u208a\u2081 = x\u2096 \u2212 \u03b1 "
                        "m\u0302\u2096 / (\u221as\u0302\u2096 + \u03b5)}",
                        font_size=17,
                        space_after=8,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{y:m\u0302, s\u0302}: {y:m, s} divided by "
                            "{y:1 \u2212 \u03b2\u1d4f}, correcting the start at zero",
                            "Defaults: {y:\u03b2\u2081 = "
                            f"{self.number(value=adam.first_moment_decay)}, "
                            f"\u03b2\u2082 = {self.number(value=adam.second_moment_decay)}"
                            ", \u03b5 = 10\u207b\u2078}",
                            "Steep coordinates get small steps, flat ones large steps",
                            "Robust to noisy gradients; the defaults often work",
                        ],
                        space_after=4,
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
        ]

    # %% computational graphs

    def computational_graph_slides(self) -> list[Slide]:
        """
        :return: The section on computational graphs and automatic differentiation.
        """
        return [
            self.contents(highlighted_section=Section.COMPUTATIONAL_GRAPHS),
            ContentSlide(
                title="Where Do Gradients Come From?",
                section=Section.COMPUTATIONAL_GRAPHS,
                items=[
                    *[
                        self.text_box(
                            area=Rectangle(
                                left=0.45 + index * 4.2, top=1.5, width=3.9, height=4.6
                            ),
                            paragraphs=[
                                self.heading(text=heading, space_after=8),
                                *Paragraph.bullet_points(texts=points, space_after=6),
                            ],
                            font_size=16,
                        )
                        for index, (heading, points) in enumerate(
                            [
                                (
                                    "By hand",
                                    [
                                        "Exact",
                                        "Tedious and error-prone",
                                        "Redone for every new model",
                                    ],
                                ),
                                (
                                    "Finite differences",
                                    [
                                        "{y:(f(x + h e\u1d62) \u2212 f(x)) / h}",
                                        "{y:n + 1} evaluations of {y:f} for a gradient "
                                        "in {y:\u211d\u207f}",
                                        "Approximate: {y:h} trades truncation against "
                                        "rounding error",
                                    ],
                                ),
                                (
                                    "Automatic differentiation",
                                    [
                                        "Exact up to floating point",
                                        "Applies the chain rule to the program itself",
                                        "Whole gradient for a few evaluations' cost",
                                    ],
                                ),
                            ]
                        )
                    ],
                    TakeAway(
                        text="Every deep learning framework and Giskard rely on "
                        "automatic differentiation."
                    ),
                ],
            ),
            BulletSlide(
                title="Computational Graphs",
                section=Section.COMPUTATIONAL_GRAPHS,
                text_area=Rectangle(left=0.45, top=1.3, width=5.3, height=4.9),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="A {a:computational graph} is a directed acyclic graph:",
                        space_after=6,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:nodes:} inputs and primitive operations "
                            "({y:+, \u00b7, sin, exp}, \u2026)",
                            "{b:edges:} the intermediate values passed on",
                            Paragraph(
                                text="Every program of primitive operations defines "
                                "one; loops are unrolled.",
                                level=BulletLevel.FIRST,
                                space_after=14,
                            ),
                        ],
                        space_after=6,
                    ),
                    self.heading(text="Example:"),
                    self.formula(
                        text="{y:f(a, b) = (a + b) \u00b7 b}",
                        font_size=18,
                        space_after=6,
                    ),
                    Paragraph(
                        text="with {y:c = a + b}. The input {y:b} reaches {y:f} along "
                        "{a:two paths}.",
                    ),
                ],
                items=[
                    self.video(
                        animation=Animation.COMPUTATIONAL_GRAPH,
                        position=Position(x=5.95, y=1.5),
                        width=7.0,
                    )
                ],
                take_away="The graph is the program, written so that it can be "
                "differentiated.",
            ),
            self.backward_pass_slide(),
            ContentSlide(
                title="Forward Mode and Reverse Mode",
                section=Section.COMPUTATIONAL_GRAPHS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.4, width=6.0, height=2.9),
                        paragraphs=[
                            self.heading(text="Forward mode", space_after=6),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Carries a derivative along with every value, "
                                    "from the inputs to the output",
                                    "One pass per input direction",
                                ],
                                space_after=6,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=6.9, top=1.4, width=6.0, height=2.9),
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
                        area=Rectangle(left=0.45, top=4.3, width=12.4, height=1.9),
                        paragraphs=[
                            self.heading(text="Which one?", space_after=6),
                            *Paragraph.bullet_points(
                                texts=[
                                    "A loss {y:\u211d\u207f \u2192 \u211d} with millions "
                                    "of parameters: {a:reverse mode} \u2013 the whole "
                                    "gradient from one backward pass",
                                    "A Jacobian {y:\u211d\u207f \u2192 \u211d\u1d50}: "
                                    "forward mode if {y:n < m}, reverse mode if "
                                    "{y:m < n}",
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
                                "Giskard writes the forward kinematics of the robot as "
                                "an expression graph and differentiates it into the "
                                "{a:Jacobians} its QP needs.",
                                "PyTorch computes the {a:same numbers} as our backward "
                                "pass by hand: {y:\u2202f/\u2202a = 3, \u2202f/\u2202b = "
                                "8}.",
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
                self.text_box(
                    area=Rectangle(left=0.45, top=1.3, width=12.4, height=1.2),
                    paragraphs=[
                        Paragraph(
                            text="The {a:adjoint} {y:v\u0304 = \u2202f/\u2202v} of a node "
                            "sums what its consumers {y:u} send back:",
                            space_after=6,
                        ),
                        self.formula(
                            text="{y:f\u0304 = 1,      v\u0304 = \u2211\u1d64 "
                            "u\u0304 \u00b7 \u2202u/\u2202v}",
                            font_size=18,
                            space_after=0,
                        ),
                    ],
                ),
                Table(
                    position=Position(x=0.9, y=2.75),
                    column_widths=[2.4, 2.0, 3.4, 3.9],
                    rows=[
                        ["Node", "Forward value", "Local derivatives", "Adjoint"],
                        [
                            "{y:f = c \u00b7 b}",
                            value["f"],
                            "{y:\u2202f/\u2202c = b,  \u2202f/\u2202b = c}",
                            f"{{y:f\u0304 = {adjoint['f']}}}",
                        ],
                        [
                            "{y:c = a + b}",
                            value["c"],
                            "{y:\u2202c/\u2202a = \u2202c/\u2202b = 1}",
                            f"{{y:c\u0304 = f\u0304 \u00b7 b = {adjoint['c']}}}",
                        ],
                        [
                            "{y:b}",
                            value["b"],
                            "",
                            "{y:b\u0304 = f\u0304 \u00b7 c + c\u0304 \u00b7 1 = "
                            f"{self.number(value=output.adjoint * total.value)} + "
                            f"{adjoint['c']} = {adjoint['b']}}}",
                        ],
                        [
                            "{y:a}",
                            value["a"],
                            "",
                            f"{{y:a\u0304 = c\u0304 \u00b7 1 = {adjoint['a']}}}",
                        ],
                    ],
                    row_height=0.5,
                    font_size=15,
                ),
                self.text_box(
                    area=Rectangle(left=0.45, top=5.4, width=12.4, height=0.8),
                    paragraphs=[
                        Paragraph(
                            text="Check: {y:f = ab + b\u00b2}, so {y:\u2202f/\u2202a = b "
                            f"= {value['b']}}} and {{y:\u2202f/\u2202b = a + 2b = "
                            f"{self.number(value=first.value + 2 * second.value)}}}.",
                            space_after=0,
                        )
                    ],
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
        return [
            BulletSlide(
                title="Linear Programs (LP)",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    self.formula(
                        text="{y:min c\u1d40x    s.t.    Gx \u2264 g,   Hx = h,   "
                        "x \u2208 \u211d\u207f}",
                        space_after=16,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Linear objective}: contour lines are straight.",
                            "{b:Linear constraints}: the feasible region is a convex "
                            "{a:polyhedron} \u2013 flat faces, edges, vertices.",
                            "{b:Continuous variables}: integer variables make it a "
                            "different, harder class (MILP).",
                        ],
                        space_after=8,
                    ),
                    Paragraph(text="", space_after=6),
                    self.heading(text="Why LPs are \u201ceasy\u201d:"),
                    *Paragraph.bullet_points(
                        texts=[
                            "If an optimum exists, one lies at a {a:vertex} of the "
                            "polyhedron.",
                            "Solvers walk from vertex to vertex ({a:simplex}) or "
                            "through the interior ({a:interior-point}).",
                        ],
                        space_after=6,
                    ),
                ],
                take_away="Linear objective, linear constraints: the optimum is at a "
                "corner.",
            ),
            ContentSlide(
                title="Example: The Fastest Gripper",
                section=Section.CONSTRAINED,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=0.5),
                        paragraphs=[
                            Paragraph(
                                text="Ignore the motion cost for a moment: how fast "
                                "can the gripper approach the cup?"
                            )
                        ],
                        font_size=18,
                    ),
                    TextFrame(
                        area=Rectangle(left=0.45, top=2.0, width=5.0, height=0.45),
                        paragraphs=[self.heading(text="Inequality form")],
                        font_size=18,
                    ),
                    *self.aligned_formulas(
                        labels=["{y:max}", "{y:s.t.}"],
                        expressions=[
                            "{y:v = x\u2081 + x\u2082}",
                            *[
                                self.inequality_text(coefficients=row, bound=bound)
                                for row, bound in zip(
                                    robot.constraint_matrix, robot.constraint_bounds
                                )
                                if bound > 0
                            ],
                            "{y:x\u2081, x\u2082 \u2265 0}",
                        ],
                        position=Position(x=1.6, y=2.6),
                        label_width=0.9,
                        expression_width=3.6,
                    ),
                    TextFrame(
                        area=Rectangle(left=6.9, top=2.0, width=5.0, height=0.45),
                        paragraphs=[self.heading(text="Matrix form")],
                        font_size=18,
                    ),
                    self.matrix_label(
                        text="{y:max   J x,   J =}",
                        area=Rectangle(left=6.9, top=2.6, width=2.6, height=0.4),
                    ),
                    Matrix(
                        position=Position(x=9.6, y=2.6),
                        entries=self.matrix_entries(
                            values=robot.gripper_jacobian[None, :]
                        ),
                        column_width=0.45,
                    ),
                    *self.constraint_matrices(top=3.35),
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
                            f"{{y:x* = {self.point_text(optimum=optimum)}}}",
                            f"{{y:v* = {self.number(value=optimum.value)}}} cm/s",
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
                            "Slack variables turn inequalities into equalities: "
                            "{y:Gx + s = g,  s \u2265 0}.",
                            "A {a:basis} picks which variables may be non-zero; its "
                            "solution is a {a:vertex}.",
                        ],
                        space_after=8,
                    ),
                    self.heading(text="One iteration (a pivot):"),
                    *[
                        Paragraph(text=step, indent=0.3, space_after=4)
                        for step in [
                            "1. Does increasing a non-basic variable improve the "
                            "objective (its {a:reduced cost})?",
                            "2. If none does {y:\u2192} the vertex is optimal.",
                            "3. Otherwise it enters the basis: move along that edge.",
                            "4. The first variable that reaches zero leaves the basis.",
                        ]
                    ],
                    Paragraph(text="", space_after=4),
                    Paragraph(
                        text="On the robot, starting from standing still {y:x = (0, 0)}.",
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
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.25, width=12.4, height=0.5),
                        paragraphs=[
                            Paragraph(
                                text="{b:Key idea:} move {i:inside} the feasible region "
                                "toward the optimum, instead of along the boundary."
                            )
                        ],
                        font_size=17,
                    ),
                    self.video(
                        animation=Animation.INTERIOR_POINT,
                        position=Position(x=0.45, y=1.85),
                        width=6.4,
                    ),
                    self.text_box(
                        area=Rectangle(left=7.1, top=1.95, width=5.8, height=4.25),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Replace the constraints by a {a:barrier} that grows to "
                                "{y:+\u221e} at the boundary:",
                                Paragraph(
                                    text="{y:min \u2212t J x \u2212 \u2211\u1d62 "
                                    "log(g\u1d62 \u2212 G\u1d62x)}",
                                    alignment=Alignment.CENTER,
                                    space_after=8,
                                ),
                                "An {b:unconstrained} problem: solve it with Newton "
                                "steps.",
                                "Increase {y:t}: the barrier weakens and the minimizers "
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
                        TextFrame(
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
                                    "Warm start from a previous basis",
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
        quadratic_form_top = 2.25
        robot = self.robot
        optimum = robot.quadratic_optimum
        unconstrained = robot.unconstrained_minimum
        base_weight, arm_weight = robot.joint_weights
        elbow = robot.constraint_matrix[2]
        return [
            ContentSlide(
                title="Quadratic Programs (QP)",
                section=Section.CONSTRAINED,
                items=[
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.2, width=12.4, height=0.95),
                        paragraphs=[
                            Paragraph(
                                text="A quadratic objective under linear constraints:",
                                space_after=6,
                            ),
                            self.formula(
                                text="{y:min \u00bd x\u1d40Qx + c\u1d40x    s.t.    "
                                "Gx \u2264 g,  Hx = h,    x \u2208 \u211d\u207f}",
                                font_size=17,
                                space_after=0,
                            ),
                        ],
                        font_size=16,
                    ),
                    self.matrix_label(
                        text="{y:x\u1d40Qx =}",
                        area=Rectangle(
                            left=2.0, top=quadratic_form_top, width=1.55, height=0.96
                        ),
                        font_size=17,
                    ),
                    Matrix(
                        position=Position(x=3.65, y=quadratic_form_top + 0.32),
                        entries=[["{y:x\u2081}", "{y:\u22ef}", "{y:x\u2099}"]],
                        column_width=0.5,
                    ),
                    Matrix(
                        position=Position(x=5.45, y=quadratic_form_top),
                        entries=[
                            ["{y:Q\u2081\u2081}", "{y:\u22ef}", "{y:Q\u2081\u2099}"],
                            ["{y:\u22ee}", "{y:\u22f1}", "{y:\u22ee}"],
                            ["{y:Q\u2099\u2081}", "{y:\u22ef}", "{y:Q\u2099\u2099}"],
                        ],
                        column_width=0.6,
                    ),
                    Matrix(
                        position=Position(x=7.55, y=quadratic_form_top),
                        entries=[["{y:x\u2081}"], ["{y:\u22ee}"], ["{y:x\u2099}"]],
                        column_width=0.5,
                    ),
                    TextFrame(
                        area=Rectangle(
                            left=8.3, top=quadratic_form_top, width=4.5, height=0.96
                        ),
                        paragraphs=[
                            Paragraph(
                                text="{y:= \u2211\u1d62\u208c\u2081\u207f "
                                "\u2211\u2c7c\u208c\u2081\u207f Q\u1d62\u2c7c x\u1d62 "
                                "x\u2c7c}",
                                space_after=0,
                            )
                        ],
                        font_size=17,
                        anchor=VerticalAnchor.MIDDLE,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=3.55, width=12.4, height=2.65),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Diagonal entries {y:Q\u1d62\u1d62} weigh the squares "
                                "{y:x\u1d62\u00b2}, off-diagonal entries the cross terms "
                                "{y:x\u1d62x\u2c7c}; the {y:\u00bd} cancels the 2 of "
                                "the derivative.",
                                "Convex if and only if {y:Q \u2ab0 0}.",
                                "The feasible region is still a polyhedron, but the "
                                "contours are {a:ellipses}:",
                                Paragraph(
                                    text="the optimum can lie on an edge or inside, not "
                                    "only at a vertex.",
                                    level=BulletLevel.SECOND,
                                ),
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(text="A QP is the next simplest problem after an LP."),
                ],
            ),
            BulletSlide(
                title="The Robot's QP",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    self.formula(
                        text="{y:min  \u00bd (w\u2081x\u2081\u00b2 + w\u2082x\u2082\u00b2)"
                        "  +  \u00bd w\u209b (x\u2081 + x\u2082 \u2212 v_d)\u00b2    "
                        "s.t.    Gx \u2264 g}",
                        space_after=14,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Motion term:} small velocities; the base costs more "
                            f"than the arm ({{y:w\u2081 = {self.number(value=base_weight)}"
                            f", w\u2082 = {self.number(value=arm_weight)}}}).",
                            "{b:Goal term:} a {a:soft constraint} \u2013 the gripper "
                            "speed should be {y:v_d = "
                            f"{self.number(value=robot.desired_gripper_speed)}}} cm/s, "
                            "each deviation costs with weight {y:w\u209b = "
                            f"{self.number(value=robot.goal_weight)}}}.",
                            "Same as a {a:slack variable} {y:s}: minimize "
                            "{y:\u2026 + \u00bd w\u209b s\u00b2} s.t. "
                            "{y:x\u2081 + x\u2082 \u2212 s = v_d}.",
                            "{b:Hard constraints} {y:Gx \u2264 g}: joint limits and "
                            "collision avoidance, as for the LP.",
                        ],
                        space_after=8,
                    ),
                ],
                take_away="Hard constraints must hold; soft constraints are traded off "
                "in the objective.",
            ),
            ContentSlide(
                title="The Robot's QP in Matrix Form",
                section=Section.CONSTRAINED,
                items=[
                    self.matrix_label(
                        text="{y:min  \u00bd x\u1d40Qx + c\u1d40x,   Q =}",
                        area=Rectangle(left=0.45, top=1.6, width=3.6, height=0.64),
                    ),
                    Matrix(
                        position=Position(x=4.15, y=1.6),
                        entries=self.matrix_entries(values=robot.quadratic_cost_matrix),
                        column_width=0.6,
                    ),
                    self.matrix_label(
                        text="{y:,   c =}",
                        area=Rectangle(left=5.5, top=1.6, width=0.75, height=0.64),
                    ),
                    Matrix(
                        position=Position(x=6.35, y=1.6),
                        entries=self.matrix_entries(values=robot.linear_cost),
                        column_width=0.75,
                    ),
                    *self.constraint_matrices(top=2.6, left=0.45),
                    self.text_box(
                        area=Rectangle(left=7.0, top=2.6, width=5.9, height=3.6),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{y:Q = diag(w) + w\u209b J\u1d40J}",
                                "{y:c = \u2212w\u209b v_d J\u1d40}",
                                "The constant {y:\u00bd w\u209b v_d\u00b2} does not "
                                "move the minimizer.",
                                "Goal weight couples the joints: off-diagonal "
                                "{y:w\u209b}.",
                            ],
                            space_after=8,
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
                            f"{{y:x* = {self.point_text(optimum=optimum)}}}",
                            "gripper speed {y:"
                            f"{self.number(value=sum(optimum.point))}}} cm/s",
                        ],
                        space_after=12,
                    ),
                    self.heading(text="Without constraints:"),
                    *Paragraph.bullet_points(
                        texts=[
                            f"{{y:x = {self.point_text(optimum=unconstrained)}}}",
                            "elbow at {y:"
                            + self.number(
                                value=float(elbow @ np.array(unconstrained.point))
                            )
                            + f" > {self.number(value=robot.constraint_bounds[2])}}} "
                            "cm/s: it would hit the shelf",
                        ],
                        space_after=12,
                    ),
                    Paragraph(
                        text="The optimum lies on the elbow's edge, {a:not at a "
                        "vertex}."
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
        gradient_text = ", ".join(self.number(value=entry) for entry in gradient)
        elbow_text = ", ".join(self.number(value=entry) for entry in elbow)
        return [
            BulletSlide(
                title="Karush-Kuhn-Tucker (KKT) Conditions",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.25, width=12.4, height=4.95),
                font_size=16,
                paragraphs=[
                    Paragraph(
                        text="At an optimum {y:x*} of {y:min f(x)  s.t.  g\u1d62(x) \u2264 "
                        "0,  h\u2c7c(x) = 0} there are multipliers {y:\u03bb\u1d62, "
                        "\u03bd\u2c7c} with:",
                        space_after=10,
                    ),
                    *[
                        Paragraph(text=condition, indent=0.3, space_after=6)
                        for condition in [
                            "{b:Stationarity:}   {y:\u2207f(x*) + \u2211\u1d62 "
                            "\u03bb\u1d62\u2207g\u1d62(x*) + \u2211\u2c7c "
                            "\u03bd\u2c7c\u2207h\u2c7c(x*) = 0}",
                            "{b:Primal feasibility:}   {y:g\u1d62(x*) \u2264 0,  "
                            "h\u2c7c(x*) = 0}",
                            "{b:Dual feasibility:}   {y:\u03bb\u1d62 \u2265 0}",
                            "{b:Complementary slackness:}   {y:\u03bb\u1d62 "
                            "g\u1d62(x*) = 0} \u2013 inactive constraints get "
                            "{y:\u03bb\u1d62 = 0}",
                        ]
                    ],
                    Paragraph(text="", space_after=4),
                    *Paragraph.bullet_points(
                        texts=[
                            "Active constraints push back exactly as hard as the "
                            "objective pulls.",
                            "Without constraints: {y:\u2207f(x*) = 0}.",
                            "For {a:convex} problems the conditions are also "
                            "sufficient: a KKT point is a global optimum.",
                        ],
                        space_after=6,
                    ),
                ],
                take_away="KKT generalizes {y:\u2207f = 0} to constraints.",
            ),
            BulletSlide(
                title="KKT at the Robot's Optimum",
                section=Section.CONSTRAINED,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    Paragraph(
                        text=f"At {{y:x* = {self.point_text(optimum=optimum)}}} the "
                        "elbow constraint is active, all others are not.",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Cost gradient: {y:\u2207f(x*) = Qx* + c = "
                            f"({gradient_text})}}",
                            f"Elbow gradient: {{y:\u2207g(x*) = ({elbow_text})}}",
                            "Stationarity: {y:"
                            f"({gradient_text}) + \u03bb ({elbow_text}) = 0  "
                            f"\u21d2  \u03bb = {self.number(value=elbow_multiplier)} "
                            "\u2265 0  \u2713}",
                            Paragraph(
                                text="All inactive constraints: {y:\u03bb\u1d62 = 0  "
                                "\u2713}",
                                level=BulletLevel.FIRST,
                                space_after=18,
                            ),
                        ],
                        space_after=8,
                    ),
                    self.heading(text="Meaning of the multiplier:"),
                    Paragraph(
                        text="{y:\u03bb} is a {a:shadow price}: allowing the elbow 1 "
                        "cm/s more lowers the optimal cost by about "
                        f"{self.number(value=elbow_multiplier)}."
                    ),
                ],
                take_away="The multipliers tell the robot what each constraint costs.",
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
                            "A solution violates an inactive constraint {y:\u2192} add "
                            "it to the active set.",
                            "An active constraint has {y:\u03bb\u1d62 < 0} {y:\u2192} "
                            "remove it.",
                            Paragraph(
                                text="Feasible and all {y:\u03bb\u1d62 \u2265 0} "
                                "{y:\u2192} KKT holds: optimal.",
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
                            "1. {y:A = \u2205}: unconstrained minimum {y:"
                            f"{self.point_text(optimum=unconstrained)}}} violates "
                            "the elbow constraint.",
                            "2. {y:A = }{elbow}: minimum on the elbow's line "
                            f"{{y:{self.point_text(optimum=optimum)}}}, feasible, "
                            f"{{y:\u03bb = {self.number(value=elbow_multiplier)} "
                            "\u2265 0}: optimal.",
                        ]
                    ],
                    Paragraph(text="", space_after=4),
                    Paragraph(
                        text="In a control loop the active set barely changes from one "
                        "cycle to the next: a {a:warm start} makes each solve fast."
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
                            "{b:Variables:} velocities of all joints \u2013 and their "
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
                take_away="Convex, so its optimum is unique \u2013 and fast enough to "
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
            BulletSlide(
                title="Fitting a Model Is Maximizing a Likelihood",
                section=Section.LIKELIHOOD,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    Paragraph(
                        text="Model: {y:y = \u03b8\u1d40x + \u03b5} with Gaussian noise "
                        "{y:\u03b5 ~ N(0, \u03c3\u00b2)}, samples {y:(x\u2c7c, "
                        "y\u2c7c)}.",
                        space_after=10,
                    ),
                    self.heading(text="Likelihood of the parameters:"),
                    self.formula(
                        text="{y:L(\u03b8) = \u220f\u2c7c p(y\u2c7c | x\u2c7c, \u03b8)}",
                        font_size=18,
                        space_after=8,
                    ),
                    self.heading(text="Negative log-likelihood:"),
                    self.formula(
                        text="{y:\u2212log L(\u03b8) = 1/(2\u03c3\u00b2) \u2211\u2c7c "
                        "(y\u2c7c \u2212 \u03b8\u1d40x\u2c7c)\u00b2 + "
                        "N log(\u03c3\u221a(2\u03c0))}",
                        font_size=18,
                        space_after=10,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Maximizing the likelihood {y:=} minimizing the squared "
                            "error: {a:least squares}.",
                            "The logarithm keeps the maximizer and turns the product "
                            "into a {a:sum over samples} \u2013 ready for SGD.",
                        ],
                        space_after=6,
                    ),
                ],
                take_away="Learning is optimizing the likelihood ({y:\u2192} "
                "Uncertainty, 03.12.).",
            ),
            ContentSlide(
                title="Maximum Likelihood under a Constraint",
                section=Section.LIKELIHOOD,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=0.8),
                        paragraphs=[
                            Paragraph(
                                text="The robot logged "
                                f"{self.grasps.attempt_count} grasps in its episodic "
                                "memory (NEEMs, lecture 02). How likely is each "
                                "outcome?"
                            )
                        ],
                    ),
                    Table(
                        position=Position(x=0.6, y=2.2),
                        column_widths=[1.6, 1.3, 1.8],
                        rows=[
                            ["Outcome", "Count", "Estimate"],
                            *[
                                [
                                    outcome.value,
                                    f"{{y:n = {count}}}",
                                    f"{{y:p = {estimate[outcome]:.2f}}}",
                                ]
                                for outcome, count in self.grasps.counts.items()
                            ],
                        ],
                        row_height=0.48,
                        font_size=15,
                    ),
                    self.text_box(
                        area=Rectangle(left=5.7, top=2.1, width=7.2, height=4.1),
                        paragraphs=[
                            self.formula(
                                text="{y:max\u209a \u2211\u2096 n\u2096 log p\u2096    "
                                "s.t.    \u2211\u2096 p\u2096 = 1}",
                                font_size=18,
                                space_after=10,
                            ),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Concave objective, linear constraint: a convex "
                                    "problem.",
                                    "Stationarity with multiplier {y:\u03bd}: "
                                    "{y:n\u2096 / p\u2096 = \u03bd}",
                                    "With {y:\u2211\u2096 p\u2096 = 1}: {y:\u03bd = N}, "
                                    "so {y:p\u2096 = n\u2096 / N}",
                                    "The relative frequencies \u2013 what the solver "
                                    "returns, too.",
                                ],
                                space_after=8,
                            ),
                        ],
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
                                "Gradient descent follows {y:\u2212\u2207f}; momentum, "
                                "SGD and Adam make it fast and scalable.",
                                "Computational graphs give exact gradients: the "
                                "backward pass is the chain rule.",
                                "LPs have their optimum at a vertex; QPs on an edge, a "
                                "vertex or inside.",
                                "KKT: active constraints balance the gradient; the "
                                "multipliers price the constraints.",
                                "Giskard moves the robot by solving a convex QP every "
                                "control cycle.",
                            ],
                            start=1,
                        )
                    ],
                    Paragraph(text="", space_after=6),
                    Paragraph(
                        text="{s:Next week:} Data-Intensive Systems",
                    ),
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
