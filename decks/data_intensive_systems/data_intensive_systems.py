"""
The lecture *Data-Intensive Systems* of Advanced Methods of AI, after Kleppmann's
book: why databases are a vital component of modern systems, and the design
decisions behind them. Run it to write its ``.pptx`` and ``.pdf`` next to it.
"""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from pathlib import Path

from krrood.patterns.path_enumeration import PathEnumeration

from slide_style_kit.assets import Asset
from slide_style_kit.components import Caption, CodeBlock, DiagramNode, Label, TakeAway
from slide_style_kit.deck import Deck
from slide_style_kit.elements import (
    Arrow,
    Box,
    Element,
    Paragraph,
    Picture,
    Table,
    TextFrame,
)
from slide_style_kit.geometry import Position, Rectangle
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer
from slide_style_kit.slides import (
    BulletSlide,
    Column,
    ComparisonSlide,
    ContentSlide,
    Person,
    SectionDividerSlide,
    Slide,
    TableOfContentsEntry,
    TableOfContentsSlide,
    TitleSlide,
)
from slide_style_kit.style import Alignment, BulletLevel, Color, VerticalAnchor

from examples import (
    Chart,
    KitchenGraph,
    PoseDatabase,
    PoseStore,
    PoseTable,
    Predicate,
    ResponseTimes,
    Snippet,
)

# %% sections and figures


class Section(StrEnum):
    """
    The sections of the lecture, as the footer navigation names them.
    """

    INTRODUCTION = "Introduction"
    """
    Where the data of an AI system lives and why databases matter.
    """

    REQUIREMENTS = "Requirements"
    """
    Reliability, scalability and maintainability, transactions and distribution.
    """

    DATA_MODELS = "Data Models"
    """
    The relational, document, graph and log data models and how to choose one.
    """

    DERIVED_DATA = "Derived Data"
    """
    Systems of record, batch and stream processing, and training as a batch job.
    """

    KRROOD = "krrood"
    """
    How krrood maps dataclasses to tables and queries them with EQL.
    """

    OUTLOOK = "Outlook"
    """
    The design decisions at a glance, the takeaways and further reading.
    """


class Figure(PathEnumeration):
    """
    The images shown on the slides, cropped from the deck of the winter term 2024/2025.
    """

    DIRECTORY = Path(__file__).parent / "figures"
    """
    The directory holding the other figures.
    """

    BOOK_COVER = DIRECTORY / "book_cover.png"
    """
    The cover illustration of Kleppmann's book with its three pillars.
    """

    PRODUCT_SIZE = DIRECTORY / "product_size.png"
    """
    The code size of a software product over its releases, from *Clean Architecture*.
    """

    ENGINEERING_STAFF = DIRECTORY / "engineering_staff.png"
    """
    The engineering staff of the same product over its releases.
    """

    MAP_OF_DATA_MODELS = DIRECTORY / "map_of_data_models.png"
    """
    The book's map of the data model districts.
    """

    DOCUMENT_SCHEMA = DIRECTORY / "document_schema.png"
    """
    The fields of a document of recorded transforms.
    """

    DOCUMENT_COLLECTION = DIRECTORY / "document_collection.png"
    """
    A collection of recorded transform documents.
    """

    DATABASE_RANKING = DIRECTORY / "database_ranking.png"
    """
    The DB-Engines popularity ranking of database management systems over time.
    """

    MAP_OF_DERIVED_DATA = DIRECTORY / "map_of_derived_data.png"
    """
    The book's map of the island of derived data.
    """

    MAP_REDUCE_JOB = DIRECTORY / "map_reduce_job.png"
    """
    A MapReduce job with three mappers and three reducers, from the book.
    """


# %% design decisions


@dataclass(kw_only=True, frozen=True)
class DesignDecision:
    """
    A decision in designing the storage of the kitchen robots' episodes, taken in
    one section of the lecture.
    """

    decision: str
    """
    What is decided.
    """

    question: str
    """
    The question the decision answers.
    """

    options: str
    """
    The options to decide between.
    """

    choice: str
    """
    The option chosen for the episodes, with its reason.
    """

    section: Section
    """
    The section of the lecture whose content the decision rests on.
    """


# %% lecture


@dataclass(kw_only=True)
class DataIntensiveSystems:
    """
    The slides of the lecture, section by section.
    """

    caption_height: float = 0.3
    """
    The height of a figure caption, in inch.
    """

    poses: PoseDatabase = field(default_factory=PoseDatabase)
    """
    The pose database the relational slides draw and query.
    """

    response_times: ResponseTimes = field(default_factory=ResponseTimes)
    """
    The simulated response times the scalability slide shows.
    """

    kitchen: KitchenGraph = field(default_factory=KitchenGraph)
    """
    The knowledge graph the graph example draws and queries.
    """

    @cached_property
    def pose_store(self) -> PoseStore:
        """
        The poses of :attr:`poses`, stored and queried with krrood.
        """
        return PoseStore(poses=self.poses.poses)

    def deck(self) -> Deck:
        """
        :return: The whole lecture.
        """
        return Deck(
            title="Advanced Methods of AI - Data-Intensive Systems",
            author="Tom Schierenbeck",
            sections=list(Section),
            slides=[
                *self.introduction_slides(),
                *self.requirement_slides(),
                *self.data_model_slides(),
                *self.derived_data_slides(),
                *self.krrood_slides(),
                *self.outlook_slides(),
            ],
        )

    # %% building blocks

    def heading(self, *, text: str, space_after: float = 8) -> Paragraph:
        """
        :return: A bold paragraph introducing the paragraphs below it.
        """
        return Paragraph(text=text, bold=True, space_after=space_after)

    def numbered(self, *, texts: list[str], space_after: float = 8) -> list[Paragraph]:
        """
        :return: One indented paragraph per text, numbered from one.
        """
        return [
            Paragraph(text=f"{number}. {text}", indent=0.3, space_after=space_after)
            for number, text in enumerate(texts, start=1)
        ]

    def text_box(
        self, *, area: Rectangle, paragraphs: list[Paragraph], font_size: float = 18
    ) -> TextFrame:
        """
        :return: The *paragraphs* set into *area*.
        """
        return TextFrame(area=area, paragraphs=paragraphs, font_size=font_size)

    def quote(self, *, text: str, source: str, top: float = 2.2) -> TextFrame:
        """
        :return: The italic *text* with its *source* right-aligned below it.
        """
        return TextFrame(
            area=Rectangle(left=1.4, top=top, width=10.5, height=2.8),
            paragraphs=[
                Paragraph(text=f"{{i:{text}}}", space_after=12, line_spacing=1.3),
                Paragraph(text=f"— {source}", alignment=Alignment.RIGHT),
            ],
            font_size=22,
            anchor=VerticalAnchor.MIDDLE,
        )

    def caption(
        self, *, text: str, top: float, left: float = 0.45, width: float = 12.4
    ) -> Caption:
        """
        :return: A caption whose top edge is at *top*, across the slide by default.
        """
        return Caption(
            area=Rectangle(left=left, top=top, width=width, height=self.caption_height),
            text=text,
            font_size=14,
        )

    def contents(self, *, highlighted_section: Section | None = None) -> Slide:
        """
        :return: The table of contents with *highlighted_section* not faded.
        """
        entries = [
            TableOfContentsEntry(
                text="Why Databases Matter",
                section=Section.INTRODUCTION,
                subentries=["The Data of a Robot Clearing the Table"],
            ),
            TableOfContentsEntry(
                text="Requirements",
                section=Section.REQUIREMENTS,
                subentries=["Reliability, Scalability, Maintainability"],
            ),
            TableOfContentsEntry(
                text="Data Models and Query Languages",
                section=Section.DATA_MODELS,
                subentries=["Relational, Document, Graph, Log – and How to Choose"],
            ),
            TableOfContentsEntry(
                text="Derived Data",
                section=Section.DERIVED_DATA,
                subentries=["Batch Processing, Training as a Batch Job, Streams"],
            ),
            TableOfContentsEntry(
                text="How We Do This with krrood",
                section=Section.KRROOD,
                subentries=["Dataclasses as Tables, EQL as SQL"],
            ),
            TableOfContentsEntry(
                text="Outlook",
                section=Section.OUTLOOK,
                subentries=["Design Decisions at a Glance"],
            ),
        ]
        return TableOfContentsSlide(
            entries=entries,
            highlighted_section=highlighted_section,
            space_between_entries=10,
            font_size=20,
            subentry_font_size=16,
        )

    def pillar(self, *, title: str, definition: str, examples: list[str]) -> Slide:
        """
        :return: A slide defining one pillar of the book, with kitchen robot
            *examples*, next to the book's cover.
        """
        return BulletSlide(
            title=title,
            section=Section.REQUIREMENTS,
            font_size=18,
            paragraphs=[
                *Paragraph.bullet_points(texts=[definition], space_after=16),
                Paragraph(text="{s:Kitchen robot:}", space_after=4),
                *Paragraph.bullet_points(
                    texts=examples, level=BulletLevel.SECOND, space_after=4
                ),
            ],
            text_area=Rectangle(left=0.45, top=1.3, width=7.9, height=5.0),
            items=[
                Picture(
                    path=Figure.BOOK_COVER,
                    position=Position(x=8.9, y=1.2),
                    height=5.6,
                )
            ],
        )

    def code_with_caption(
        self, *, snippet: Snippet, area: Rectangle, caption: str, font_size: float = 14
    ) -> list[Element]:
        """
        :return: The code of *snippet* in *area* with *caption* below it.
        """
        return [
            CodeBlock.from_file(area=area, path=snippet.path, font_size=font_size),
            self.caption(
                text=caption,
                top=area.top + area.height + 0.05,
                left=area.left,
                width=area.width,
            ),
        ]

    # %% design task

    def design_decisions(self) -> list[DesignDecision]:
        """
        :return: The decisions of the design task, in the order the lecture takes
            them.
        """
        return [
            DesignDecision(
                decision="Transactions",
                question="What may a crash leave behind?",
                options="all-or-nothing, or none",
                choice="yes – an episode is stored whole or not at all",
                section=Section.REQUIREMENTS,
            ),
            DesignDecision(
                decision="Distribution",
                question="How much data, how many users, where?",
                options="one machine, replication, partitioning",
                choice="replicate; partition only when one disk is full",
                section=Section.REQUIREMENTS,
            ),
            DesignDecision(
                decision="Indexes",
                question="Which queries must be fast?",
                options="which columns and paths to index",
                choice="time and object – watch the 99th percentile",
                section=Section.REQUIREMENTS,
            ),
            DesignDecision(
                decision="Data model",
                question="Which shape has the data?",
                options="relational, document, graph, log",
                choice="relational episodes, RDF ontology, sensor log",
                section=Section.DATA_MODELS,
            ),
            DesignDecision(
                decision="Schema",
                question="Who checks the data, and when?",
                options="on write (enforced), on read (interpreted)",
                choice="on write – many programs read the episodes",
                section=Section.DATA_MODELS,
            ),
            DesignDecision(
                decision="Query language",
                question="Who decides how to compute?",
                options="declarative (SQL, SPARQL, Datalog, EQL) or code",
                choice="SQL for episodes, SPARQL for the ontology",
                section=Section.DATA_MODELS,
            ),
            DesignDecision(
                decision="Data flow",
                question="What can be recomputed?",
                options="system of record, derived data",
                choice="episodes are the record; statistics and models derived",
                section=Section.DERIVED_DATA,
            ),
        ]

    def design_table(
        self, *, top: float, decided_through: Section | None, row_height: float
    ) -> Table:
        """
        :return: The design decisions with the choices of the sections up to
            *decided_through* filled in, the newest ones highlighted, the rest open.
        """
        sections = list(Section)
        decided = (
            []
            if decided_through is None
            else sections[: sections.index(decided_through) + 1]
        )
        choices = [
            "?"
            if decision.section not in decided
            else f"{{a:{decision.choice}}}"
            if decision.section == decided_through
            else decision.choice
            for decision in self.design_decisions()
        ]
        return Table(
            position=Position(x=0.6, y=top),
            column_widths=[2.3, 4.4, 5.4],
            rows=[
                ["Decision", "Question it answers", "Our choice"],
                *[
                    [decision.decision, decision.question, choice]
                    for decision, choice in zip(self.design_decisions(), choices)
                ],
            ],
            row_height=row_height,
            font_size=15,
        )

    def design_task_slide(self) -> Slide:
        """
        :return: The design task the lecture solves step by step, all decisions open.
        """
        return ContentSlide(
            title="Our Design Task",
            section=Section.INTRODUCTION,
            items=[
                self.text_box(
                    area=Rectangle(left=0.45, top=1.25, width=12.4, height=1.2),
                    paragraphs=[
                        Paragraph(
                            text="{s:Kitchen robot:} ten robots clear tables all day "
                            "and record every episode – poses, perceived objects, "
                            "grasp outcomes. openEASE shows the episodes, students "
                            "query them, a learner trains on them.",
                            space_after=4,
                        ),
                        Paragraph(text="{b:Design the storage of the episodes.}"),
                    ],
                    font_size=17,
                ),
                self.design_table(top=2.6, decided_through=None, row_height=0.45),
                TakeAway(text="{a:Which decision would you take first?}"),
            ],
        )

    def design_progress_slide(self, *, decided_through: Section) -> Slide:
        """
        :return: The design task with the decisions of the sections up to
            *decided_through* taken.
        """
        return ContentSlide(
            title="Our Design So Far",
            section=decided_through,
            items=[
                self.design_table(
                    top=1.35, decided_through=decided_through, row_height=0.55
                ),
                TakeAway(text="highlighted: decided in this section"),
            ],
        )

    # %% introduction

    def introduction_slides(self) -> list[Slide]:
        """
        :return: The title, the learning goals, the recap and why databases matter.
        """
        return [
            TitleSlide(
                course="Advanced Methods of AI (WiSe 2026/2027)",
                title="Data-Intensive Systems",
                people=[
                    Person(name="Prof. Michael Beetz"),
                    Person(name="Tom Schierenbeck", role="lecturer"),
                ],
                place="Bremen, Germany",
                date="26th of November 2026",
                image=Asset.ROBOT_SKETCH,
            ),
            *self.outage_slides(),
            BulletSlide(
                title="Learning Goals",
                section=Section.INTRODUCTION,
                text_area=Rectangle(left=0.45, top=1.4, width=12.4, height=5.3),
                font_size=18,
                paragraphs=[
                    Paragraph(text="After this lecture you can …", space_after=12),
                    *self.numbered(
                        texts=[
                            "explain why databases are a vital component of modern AI "
                            "systems, robots included,",
                            "state the reliability, scalability and maintainability any "
                            "system has to provide,",
                            "compare the relational, document, graph and log data "
                            "models and relate them to Datalog and RDF,",
                            "choose a data model for a given shape of data and queries, "
                            "and justify the choice,",
                            "tell recorded data from data derived from it,",
                            "explain batch and stream processing, and why SGD can train "
                            "on data that does not fit into memory.",
                        ]
                    ),
                ],
                take_away="the lecture follows the book {i:Designing Data-Intensive "
                "Applications} by M. Kleppmann [1]",
            ),
            ContentSlide(
                title="Where We Left Off",
                section=Section.INTRODUCTION,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.5, width=6.0, height=4.6),
                        paragraphs=[
                            self.heading(text="Last weeks"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "KR&R: what {a:follows} from a knowledge base – "
                                    "entailment, closed world, Datalog",
                                    "Optimization: what is {a:best} – and SGD never "
                                    "needs all data at once",
                                    "Both took the facts and the samples as given",
                                ],
                                space_after=8,
                            ),
                        ],
                    ),
                    self.text_box(
                        area=Rectangle(left=6.9, top=1.5, width=6.0, height=4.6),
                        paragraphs=[
                            self.heading(text="Today: Data-Intensive Systems"),
                            *Paragraph.bullet_points(
                                texts=[
                                    "Where is the data {a:stored}, and in which shape?",
                                    "Which design decisions does a database make for "
                                    "us – and which must we make?",
                                    "How does data flow from the robot's sensors to a "
                                    "fitted model?",
                                ],
                                space_after=8,
                            ),
                        ],
                    ),
                    TakeAway(
                        text="Data says what is stored. Knowledge also says what "
                        "follows from it. (KR&R I)"
                    ),
                ],
            ),
            self.contents(),
            ContentSlide(
                title="The Data of a Robot Clearing the Table",
                section=Section.INTRODUCTION,
                items=[
                    Table(
                        position=Position(x=0.6, y=1.4),
                        column_widths=[3.2, 4.4, 2.9, 1.6],
                        rows=[
                            ["Data", "Example", "Shape", "Lecture"],
                            [
                                "World model (Semantic Digital Twin)",
                                "cup_3 is on the table",
                                "objects and relations",
                                "02",
                            ],
                            ["Ontology", "{y:Cup ⊑ Container}", "triples", "03"],
                            [
                                "Rules",
                                "cups belong in the dishwasher",
                                "Horn clauses",
                                "05",
                            ],
                            [
                                "Recorded transforms",
                                "pose of the gripper over time",
                                "stream of messages",
                                "today",
                            ],
                            [
                                "Episodes (NEEMs)",
                                "“the plate slipped”",
                                "log of runs",
                                "02",
                            ],
                            [
                                "Training data",
                                "outcomes of logged grasps",
                                "samples",
                                "06",
                            ],
                        ],
                        row_height=0.55,
                        font_size=17,
                    ),
                    TakeAway(
                        text="every row has to be stored, queried and kept consistent "
                        "– each in its own shape"
                    ),
                ],
            ),
            BulletSlide(
                title="Why Databases Matter",
                section=Section.INTRODUCTION,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "{b:Persistence:} the data outlives the program that wrote it – "
                        "a restart or a crash does not lose it",
                        "{b:Shared access:} many programs and users read and write the "
                        "same data at the same time without overwriting each other",
                        "{b:Data larger than memory:} indexes find a few records among "
                        "billions on disk without reading all of them",
                        "{b:Guarantees:} transactions, constraints and replication, "
                        "built once, used by every application",
                        "{b:Everywhere:} the web, robots (openEASE), LLM agents "
                        "(retrieval and memory, lecture 02)",
                    ],
                    space_after=10,
                ),
                take_away="most systems are not compute-bound but data-bound: "
                "{i:data-intensive}",
            ),
            ContentSlide(
                title="Invisible Design Decisions",
                section=Section.INTRODUCTION,
                items=[
                    TextFrame(
                        area=Rectangle(left=0.45, top=1.3, width=12.4, height=0.9),
                        paragraphs=[
                            Paragraph(
                                text="We use databases so routinely that their design "
                                "decisions become invisible:"
                            )
                        ],
                    ),
                    self.quote(
                        text="The Internet was done so well that most people think of "
                        "it as a natural resource like the Pacific Ocean, rather than "
                        "something that was man-made. When was the last time a "
                        "technology with a scale like that was so error-free?",
                        source="Alan Kay, in interview with Dr Dobb’s Journal (2012)",
                    ),
                ],
            ),
            self.design_task_slide(),
        ]

    def outage_slides(self) -> list[Slide]:
        """
        :return: The GitLab.com database outage of 2017 as the opening story, its
            question first, then what was left to restore from.
        """
        return [
            BulletSlide(
                title="31 January 2017: GitLab.com Loses Its Database",
                section=Section.INTRODUCTION,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "GitLab.com hosts the code, issues and merge requests of its "
                        "users in one production database, plus a replica",
                        "Evening: high load, probably spam – the replica falls behind "
                        "until replication breaks",
                        "Near midnight UTC, an engineer rebuilds the replica and wipes "
                        "its data directory – in the terminal of the {a:primary}",
                        "Stopped after a second or two: about 300 GB of data are "
                        "already gone",
                    ],
                    space_after=12,
                ),
                take_away="{a:Four backup and replication mechanisms were in place – "
                "how many could restore the data?}",
            ),
            ContentSlide(
                title="What Was Left",
                section=Section.INTRODUCTION,
                notes="Answer: one, and only by luck.",
                items=[
                    Table(
                        position=Position(x=0.6, y=1.35),
                        column_widths=[3.4, 8.7],
                        rows=[
                            ["Mechanism", "What happened"],
                            [
                                "Daily pg_dump to S3",
                                "wrong PostgreSQL version: the bucket was empty, and "
                                "the failure emails were rejected",
                            ],
                            [
                                "Azure disk snapshots",
                                "not enabled for the database servers",
                            ],
                            [
                                "Replication",
                                "the replica wiped on purpose, the primary by mistake",
                            ],
                            [
                                "LVM snapshot",
                                "a manual copy for staging, taken 6 hours earlier – "
                                "{a:the only one that worked}",
                            ],
                        ],
                        row_height=0.55,
                        font_size=17,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.4, width=12.4, height=1.7),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "About 6 hours of data lost: about 5,000 projects, "
                                "5,000 comments and 700 new users; about 18 hours "
                                "down",
                                "Nobody had tested the backups – nobody owned them "
                                "[13]",
                            ],
                            space_after=6,
                        ),
                        font_size=17,
                    ),
                    TakeAway(
                        text="today: reliability, replication and durability – and "
                        "why an untested backup is no backup"
                    ),
                ],
            ),
        ]

    # %% requirements

    def requirement_slides(self) -> list[Slide]:
        """
        :return: The three pillars of data systems, transactions and distribution.
        """
        return [
            SectionDividerSlide(heading="Requirements", section=Section.REQUIREMENTS),
            *self.reliability_slides(),
            *self.scalability_slides(),
            *self.maintainability_slides(),
            self.design_progress_slide(decided_through=Section.REQUIREMENTS),
        ]

    def reliability_slides(self) -> list[Slide]:
        """
        :return: Reliability, what can go wrong while writing, and transactions.
        """
        return [
            self.pillar(
                title="Reliability",
                definition="{b:Reliability:} The system should continue to work "
                "correctly (performing the correct function at the desired level of "
                "performance) even in the face of adversity (hardware or software "
                "faults, and even human error)",
                examples=[
                    "{b:hardware:} the battery dies while an episode is being written",
                    "{b:software:} a perception bug stores cup poses in the wrong "
                    "coordinate frame",
                    "{b:human:} a student deletes last week's episodes by mistake – "
                    "as at GitLab",
                ],
            ),
            BulletSlide(
                title="Reliability",
                section=Section.REQUIREMENTS,
                paragraphs=[
                    Paragraph(
                        text="Everybody has an intuitive idea of what it means for "
                        "something to be reliable or unreliable. For software, typical "
                        "expectations include:"
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "The application performs the function that the user "
                            "expected",
                            "It can tolerate the user making mistakes or using the "
                            "software in unexpected ways",
                            "Its performance is good enough for the required use case, "
                            "under the expected load and data volume",
                            "The system prevents any unauthorized access and abuse",
                        ]
                    ),
                ],
            ),
            *self.lost_update_slides(),
            BulletSlide(
                title="What Can Go Wrong While Writing?",
                section=Section.REQUIREMENTS,
                paragraphs=[
                    Paragraph(
                        text="{s:Kitchen robot:} the robots of a lab store their "
                        "episodes in one shared database.",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "An episode is many rows – the battery dies after half of "
                            "them",
                            "Two robots count the grasps of cup_3: both read 7, both "
                            "write 8 – one grasp is lost",
                            "The database reports “stored”, then the disk fails",
                            "A bug stores a pose that belongs to no episode",
                        ],
                        space_after=10,
                    ),
                ],
                take_away="{a:How would you prevent each of these?}",
            ),
            BulletSlide(
                title="Transactions: All or Nothing",
                section=Section.REQUIREMENTS,
                paragraphs=[
                    Paragraph(
                        text="A transaction groups several reads and writes into one "
                        "unit that happens completely or not at all – with four "
                        "guarantees, ACID:",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Atomicity:} a failure midway rolls the half-written "
                            "episode back",
                            "{b:Consistency:} the constraints hold before and after – "
                            "no pose without its episode",
                            "{b:Isolation:} concurrent transactions act as if they ran "
                            "one after another – no lost grasp",
                            "{b:Durability:} the data is on disk, or on replicas, "
                            "before “stored” is reported",
                        ],
                        space_after=10,
                    ),
                ],
                take_away="without transactions, every application has to handle every "
                "failure itself",
            ),
        ]

    def lost_update_slides(self) -> list[Slide]:
        """
        :return: Two students acting out two robots counting grasps, then the
            interleaving that loses an update and how a database prevents it.
        """
        return [
            BulletSlide(
                title="Act It Out: Two Robots, One Counter",
                section=Section.REQUIREMENTS,
                notes="Call A read, B read, A write, B write.",
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "Two volunteers are robot A and robot B",
                        "The board shows how often cup_3 was grasped: {b:7}",
                        "Each robot grasps cup_3 once and records it: read the board, "
                        "remember the number, write the number + 1",
                        "Reading and writing are separate steps – I call who acts next",
                    ],
                    space_after=12,
                ),
                take_away="{a:Two grasps, so the board should show 9 – what does it "
                "show?}",
            ),
            ContentSlide(
                title="A Lost Update",
                section=Section.REQUIREMENTS,
                items=[
                    Table(
                        position=Position(x=0.6, y=1.4),
                        column_widths=[0.9, 1.9, 1.9, 1.3],
                        rows=[
                            ["step", "robot A", "robot B", "board"],
                            ["1", "read 7", "", "7"],
                            ["2", "", "read 7", "7"],
                            ["3", "write 8", "", "8"],
                            ["4", "", "write 8", "{a:8}"],
                        ],
                        row_height=0.55,
                        font_size=17,
                    ),
                    self.text_box(
                        area=Rectangle(left=7.0, top=1.3, width=5.85, height=2.4),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Both robots followed the instructions – their steps "
                                "interleaved",
                                "{b:Lost update:} B overwrote A's write without having "
                                "seen it",
                                "Fix: let the database read and write in one step",
                            ],
                            space_after=6,
                        ),
                        font_size=17,
                    ),
                    *self.code_with_caption(
                        snippet=Snippet.COUNT_GRASP,
                        area=Rectangle(left=7.0, top=3.85, width=5.85, height=1.1),
                        caption="one atomic statement instead of read, then write",
                    ),
                    TakeAway(
                        text="for longer read-then-write steps: a transaction makes B "
                        "wait or retry – isolation"
                    ),
                ],
            ),
        ]

    def scalability_slides(self) -> list[Slide]:
        """
        :return: Scalability, measuring it, and scaling a database up and out, each
            problem asked before its solution is shown.
        """
        problems = [
            "The episodes no longer fit on one disk",
            "All robots together write faster than one machine can store",
            "When that machine fails, no robot can store or read",
            "A lab on another continent waits for every round trip",
        ]
        return [
            self.pillar(
                title="Scalability",
                definition="{b:Scalability:} As the system grows (in data volume, "
                "traffic volume, or complexity), there should be reasonable ways of "
                "dealing with that growth",
                examples=[
                    "{b:more robots:} a fleet shares its episodes",
                    "{b:more data:} more cameras, higher rates, longer runs",
                    "{b:more readers:} the learner and openEASE users query all "
                    "episodes",
                    "{b:harder queries:} from “where is cup_3?” to “which grasps "
                    "failed on wet plates?”",
                ],
            ),
            *self.response_time_slides(),
            *self.tail_slides(),
            BulletSlide(
                title="One Database Is Not Enough",
                section=Section.REQUIREMENTS,
                paragraphs=[
                    Paragraph(
                        text="{s:Kitchen robot:} a fleet of robots in several labs "
                        "shares one episode database.",
                        space_after=12,
                    ),
                    *Paragraph.bullet_points(texts=problems, space_after=10),
                ],
                take_away="{a:How would you solve this?}",
            ),
            ComparisonSlide(
                title="Scaling Up and Out",
                section=Section.REQUIREMENTS,
                left=Column(heading="The problems", points=problems),
                right=Column(
                    heading="Approaches",
                    points=[
                        "{b:Vertical scaling:} a bigger machine – until there is no "
                        "bigger one, and it still fails alone",
                        "{b:Shared disk:} several machines on one storage – limited by "
                        "contention",
                        "{b:Shared nothing:} independent nodes, each with its own "
                        "data, coordinated over the network",
                    ],
                ),
            ),
            ComparisonSlide(
                title="Shared Nothing: Replication and Partitioning",
                section=Section.REQUIREMENTS,
                left=Column(
                    heading="Techniques",
                    points=[
                        "{b:Replication:} copies on several nodes – survives the "
                        "failed machine, serves the distant lab, spreads reads",
                        "{b:Partitioning:} each node holds a part – the data fits "
                        "again, writes are spread",
                        "Usually combined",
                    ],
                ),
                right=Column(
                    heading="Challenges and trade-offs",
                    points=[
                        "Replicas can disagree: which one is right?",
                        "When the network fails, choose between consistency and "
                        "availability",
                        "Queries across partitions are slower than on one machine",
                        "{a:Distributed systems are complex – distribute only when "
                        "one machine is not enough}",
                    ],
                ),
            ),
        ]

    def response_time_slides(self) -> list[Slide]:
        """
        :return: How to describe load and performance, first asking for a guess of
            the slowest response times, then showing the simulated ones.
        """
        times = self.response_times
        median = times.percentile(percent=50)
        slowest_percent = times.percentile(percent=99)
        explanation = self.text_box(
            area=Rectangle(left=0.45, top=1.3, width=5.8, height=4.8),
            paragraphs=Paragraph.bullet_points(
                texts=[
                    "First describe the load: requests per second, reads "
                    "vs. writes, amount of data",
                    "Then measure performance, e.g. the response time of each query",
                    "Response times vary: report percentiles, not only the mean",
                    "The slowest requests are the ones users notice",
                ],
                space_after=10,
            ),
        )
        title = "Scalability Needs Numbers"
        return [
            ContentSlide(
                title=title,
                section=Section.REQUIREMENTS,
                items=[
                    explanation,
                    TakeAway(
                        text=f"{{a:The median query takes {median:.0f} ms. Guess: how "
                        "long do the slowest 1 % take?}"
                    ),
                ],
            ),
            ContentSlide(
                title=title,
                section=Section.REQUIREMENTS,
                items=[
                    explanation,
                    Picture(
                        path=Chart.RESPONSE_TIMES,
                        position=Position(x=6.55, y=1.3),
                        width=6.3,
                    ),
                    self.caption(
                        text=f"Simulated response times of {times.query_count:,} queries "
                        "(log-normal)",
                        top=5.55,
                        left=6.55,
                        width=6.3,
                    ),
                    TakeAway(
                        text=f"median {median:.0f} ms – but one query in a hundred takes "
                        f"longer than {slowest_percent:.0f} ms"
                    ),
                ],
            ),
        ]

    def tail_slides(self, *, server_count: int = 100) -> list[Slide]:
        """
        :return: A request waiting for *server_count* servers as a question, then
            how often such a request meets a slow answer.
        """
        share = self.response_times.slow_request_share(server_count=server_count)
        exponent = str(server_count).translate(
            str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        )
        return [
            BulletSlide(
                title=f"Waiting for {server_count} Servers",
                section=Section.REQUIREMENTS,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "Each server is slow – slower than its 99th percentile – in "
                        "1 % of its answers",
                        f"One user request needs answers from {server_count} servers, "
                        "asked in parallel",
                        "The request is only as fast as its slowest answer",
                    ],
                    space_after=12,
                ),
                take_away="{a:What share of the user requests is slow?}",
            ),
            BulletSlide(
                title="The Tail at Scale",
                section=Section.REQUIREMENTS,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        f"No slow answer among {server_count}: 0.99{{y:{exponent}}} ≈ "
                        f"{1 - share:.0%}",
                        f"So {{b:{share:.0%}}} of the user requests are slow – the rare "
                        "case has become the normal one",
                        f"{{s:Kitchen robot:}} a plan that asks the world model "
                        f"{server_count} times waits for its slowest answer",
                        "Large systems therefore tune the 99th and 99.9th percentiles, "
                        "not the mean",
                    ],
                    space_after=12,
                ),
                take_away="J. Dean and L. A. Barroso, “The Tail at Scale” [14]",
            ),
        ]

    def maintainability_slides(self) -> list[Slide]:
        """
        :return: Maintainability, what it costs, and the signature of a mess.
        """
        return [
            self.pillar(
                title="Maintainability",
                definition="{b:Maintainability:} Over time, many different people will "
                "work on the system (engineering and operations, both maintaining "
                "current behavior and adapting the system to new use cases), and they "
                "should all be able to work on it productively",
                examples=[
                    "{b:operability:} someone backs up the episodes and notices the "
                    "full disk at night",
                    "{b:simplicity:} a new student understands the world model in "
                    "days, not months",
                    "{b:evolvability:} a new force sensor adds a field to every "
                    "episode",
                ],
            ),
            BulletSlide(
                title="Maintenance Is Most of the Cost",
                section=Section.REQUIREMENTS,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "Maintenance consumes 40–80 % of software costs, 60 % on "
                        "average – and 60 % of that is enhancement, not bug fixing [9]",
                        "{b:Operability:} Make it easy for operations teams to keep the "
                        "system running smoothly",
                        "{b:Simplicity:} Make it easy for new engineers to understand "
                        "the system, by removing as much complexity as possible from "
                        "the system (not the same as simplicity of the user interface)",
                        "{b:Evolvability:} Make it easy for engineers to change the "
                        "system in the future, adapting it for unanticipated use cases "
                        "as requirements change",
                    ],
                    space_after=10,
                ),
                take_away="coding agents inherit code too: on agent-written code, their task "
                "resolve rate drops by up to 13.1 % [10]",
            ),
            ContentSlide(
                title="The Signature of a Mess",
                section=Section.REQUIREMENTS,
                items=[
                    Picture(
                        path=Figure.PRODUCT_SIZE,
                        position=Position(x=0.6, y=1.5),
                        width=5.8,
                    ),
                    Picture(
                        path=Figure.ENGINEERING_STAFF,
                        position=Position(x=6.9, y=1.3),
                        width=5.8,
                    ),
                    self.caption(
                        text="Source and (audio) book recommendation: "
                        "{i:Clean Architecture} [2]",
                        top=5.6,
                    ),
                    TakeAway(
                        text="the code keeps growing, the productivity per engineer "
                        "keeps falling"
                    ),
                ],
            ),
        ]

    # %% data models

    def data_model_slides(self) -> list[Slide]:
        """
        :return: The relational, document, graph and log models, their trade-offs
            and how to choose between them.
        """
        return [
            self.contents(highlighted_section=Section.DATA_MODELS),
            ContentSlide(
                title="Data Models and Query Languages",
                section=Section.DATA_MODELS,
                items=[
                    self.quote(
                        text="I call it the law of the instrument, and it may be "
                        "formulated as follows: Give a small boy a hammer, and he will "
                        "find that everything he encounters needs pounding.",
                        source="Abraham Kaplan in 1964 [3]",
                    ),
                    TakeAway(
                        text="lecture 01: AI is a toolbox – the right tool for the "
                        "right job. The same holds for databases."
                    ),
                ],
            ),
            ContentSlide(
                title="A Map of Data Models",
                section=Section.DATA_MODELS,
                items=[
                    Picture(
                        path=Figure.MAP_OF_DATA_MODELS,
                        position=Position(x=3.3, y=1.1),
                        height=5.0,
                    ),
                    self.caption(text="Illustration from [1]", top=6.2),
                ],
            ),
            self.abstraction_slide(),
            *self.relational_slides(),
            *self.document_slides(),
            *self.graph_slides(),
            self.event_log_slide(),
            ContentSlide(
                title="Choosing a Data Model",
                section=Section.DATA_MODELS,
                items=[
                    Table(
                        position=Position(x=0.6, y=1.4),
                        column_widths=[4.6, 2.9, 4.6],
                        rows=[
                            [
                                "Shape of the data and queries",
                                "Data model",
                                "Kitchen robot",
                            ],
                            [
                                "Entities with many relations, constraints, joins",
                                "relational",
                                "world model, poses",
                            ],
                            [
                                "Self-contained trees, read as a whole",
                                "document",
                                "one recorded transform message",
                            ],
                            [
                                "Highly connected, paths of any length",
                                "graph, triples",
                                "ontology, knowledge graph",
                            ],
                            [
                                "Append-only events in time order",
                                "log, stream",
                                "sensor streams, rosbags",
                            ],
                        ],
                        row_height=0.7,
                        font_size=17,
                    ),
                    TakeAway(
                        text="the shape of the data and of its queries picks the model "
                        "– not habit"
                    ),
                ],
            ),
            ContentSlide(
                title="Popularity of Database Management Systems",
                section=Section.DATA_MODELS,
                items=[
                    Picture(
                        path=Figure.DATABASE_RANKING,
                        position=Position(x=1.6, y=1.2),
                        width=10.1,
                    ),
                    self.caption(
                        text="Ranking of popular database management systems [7]",
                        top=6.6,
                    ),
                ],
            ),
            self.design_progress_slide(decided_through=Section.DATA_MODELS),
        ]

    def abstraction_slide(self) -> Slide:
        """
        :return: The layers between the real world and the bytes on disk, each with
            its kitchen robot example.
        """
        layers = [
            ("Real world", "a cup on the kitchen table", Color.PALE_GREEN),
            (
                "Domain model",
                "cup_3: Cup, located on the table – the Semantic Digital Twin",
                Color.PALE_YELLOW,
            ),
            (
                "General-purpose data model",
                "a row of a table, a JSON document, or an edge of a graph",
                Color.PALE_BLUE,
            ),
            (
                "Storage",
                "bytes in files, pages and indexes of the storage engine",
                Color.PALE_PURPLE,
            ),
        ]
        node_width = 3.8
        node_height = 0.75
        spacing = 1.15
        top = 1.35
        items: list[Element] = []
        for index, (layer, example, fill) in enumerate(layers):
            layer_top = top + index * spacing
            items.append(
                DiagramNode(
                    area=Rectangle(
                        left=0.6, top=layer_top, width=node_width, height=node_height
                    ),
                    text=layer,
                    fill=fill,
                    bold=True,
                )
            )
            items.append(
                self.text_box(
                    area=Rectangle(
                        left=4.8, top=layer_top, width=8.0, height=node_height
                    ),
                    paragraphs=[Paragraph(text=f"{{s:Kitchen robot:}} {example}")],
                    font_size=17,
                )
            )
            if index > 0:
                items.append(
                    Arrow(
                        start=Position(
                            x=0.6 + node_width / 2,
                            y=layer_top - spacing + node_height,
                        ),
                        end=Position(x=0.6 + node_width / 2, y=layer_top),
                        color=Color.DARK_GRAY,
                    )
                )
        items.append(
            TakeAway(
                text="each layer hides the complexity of the one below – choosing a "
                "data model chooses the third layer"
            )
        )
        return ContentSlide(
            title="Layers of Abstraction", section=Section.DATA_MODELS, items=items
        )

    def relational_slides(self) -> list[Slide]:
        """
        :return: The relational model, its relation to Datalog, a pose database, its
            benefits and taxes, the object-relational mismatch and schema on write.
        """
        return [
            ContentSlide(
                title="The Everlasting Relational Empire",
                section=Section.DATA_MODELS,
                items=[
                    self.text_box(
                        area=Rectangle(left=0.45, top=1.3, width=7.0, height=4.9),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "{b:1970:} Edgar Codd proposes the relational model "
                                "[4]",
                                "{b:1974:} SQL, then called SEQUEL, at IBM; {b:1979:} "
                                "the first commercial SQL database",
                                "Data lives in {b:relations} (tables): unordered sets "
                                "of {b:tuples} (rows) with named {b:attributes} "
                                "(columns)",
                                "First doubted to be efficient – query optimizers "
                                "proved it can be",
                                "Still dominant after more than 40 years",
                            ],
                            space_after=10,
                        ),
                    ),
                    Table(
                        position=Position(x=8.1, y=1.6),
                        column_widths=[2.2, 2.2],
                        rows=[
                            ["object", "support"],
                            ["cup_3", "table"],
                            ["plate_1", "table"],
                        ],
                        row_height=0.45,
                        font_size=17,
                    ),
                    self.caption(
                        text="relation located_on: 2 tuples, 2 attributes",
                        top=3.05,
                        left=8.1,
                        width=4.4,
                    ),
                    Table(
                        position=Position(x=8.1, y=3.7),
                        column_widths=[2.2, 2.2],
                        rows=[
                            ["object", "kind"],
                            ["cup_3", "cup"],
                            ["plate_1", "plate"],
                        ],
                        row_height=0.45,
                        font_size=17,
                    ),
                    self.caption(
                        text="relation category", top=5.15, left=8.1, width=4.4
                    ),
                ],
            ),
            ContentSlide(
                title="You Already Know the Relational Model",
                section=Section.DATA_MODELS,
                items=[
                    *self.code_with_caption(
                        snippet=Snippet.PUT_AWAY_DATALOG,
                        area=Rectangle(left=0.45, top=1.3, width=6.0, height=3.2),
                        caption="Datalog (lecture 05): facts and one rule",
                        font_size=15,
                    ),
                    *self.code_with_caption(
                        snippet=Snippet.PUT_AWAY_SQL,
                        area=Rectangle(left=6.85, top=1.3, width=6.0, height=3.2),
                        caption="SQL: the same question as a join",
                        font_size=15,
                    ),
                    self.text_box(
                        area=Rectangle(left=0.45, top=4.95, width=12.4, height=1.3),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Facts are rows, a predicate is a table, a shared "
                                "variable is a join (lecture 05)",
                                "A missing row is false: the closed world (lecture 04)",
                            ],
                            space_after=4,
                        ),
                        font_size=17,
                    ),
                    TakeAway(text="both answer cup_3 → dishwasher, plate_1 → cupboard"),
                ],
            ),
            self.pose_database_slide(),
            ComparisonSlide(
                title="Benefits and Taxes of the Empire",
                section=Section.DATA_MODELS,
                left=Column(
                    heading="Benefits of the empire",
                    points=[
                        "Closeness to data structures in your application",
                        "Object-relational mappings like SQLAlchemy [6]",
                        "All kinds of relationships are supported",
                        "Joining is native to the engine",
                        "Almost no duplicated data",
                        "Query optimization, arbitrary indexing",
                        "Easy access, wide community support",
                    ],
                ),
                right=Column(
                    heading="Taxes of the empire",
                    points=[
                        "Object-relational mismatch {i:(next slide)}",
                        "Locality of data: one object is spread over several tables",
                        "Schema inflexibility {i:(schema on write, in two slides)}",
                    ],
                ),
            ),
            self.three_shapes_slide(),
            self.schema_slide(),
            ContentSlide(
                title="Object-Relational Mapping Example",
                section=Section.DATA_MODELS,
                items=[
                    CodeBlock.from_file(
                        area=Rectangle(left=0.45, top=1.3, width=7.4, height=4.6),
                        path=Snippet.OBJECT_RELATIONAL_MAPPING.path,
                        font_size=16,
                    ),
                    self.text_box(
                        area=Rectangle(left=8.3, top=1.3, width=4.6, height=4.6),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                "Each class becomes a table, each typed attribute a "
                                "column",
                                "The mapping writes the SQL and the joins; the "
                                "program keeps its objects",
                                "It narrows the mismatch, but cannot remove it",
                                "EQL (lecture 02) asks relational questions about the "
                                "same Python objects",
                            ]
                        ),
                    ),
                ],
            ),
        ]

    def pose_database_slide(self) -> Slide:
        """
        :return: The schema of the pose database drawn from the database itself,
            next to a join over it and the rows it answers.
        """
        table_areas = {
            PoseTable.POSE: Position(x=0.5, y=2.5),
            PoseTable.POSITION: Position(x=3.75, y=1.3),
            PoseTable.QUATERNION: Position(x=3.75, y=3.75),
        }
        table_width = 2.55
        header_height = 0.38
        row_height = 0.27
        items: list[Element] = []
        for table, corner in table_areas.items():
            columns = self.poses.columns(table=table)
            items.append(
                Box(
                    area=Rectangle(
                        left=corner.x,
                        top=corner.y,
                        width=table_width,
                        height=header_height,
                    ),
                    text=table.value,
                    fill=Color.PALE_BLUE,
                    bold=True,
                    font_size=14,
                )
            )
            body = Rectangle(
                left=corner.x,
                top=corner.y + header_height,
                width=table_width,
                height=len(columns) * row_height + 0.1,
            )
            items.append(Box(area=body))
            items.append(
                self.text_box(
                    area=body.inset(horizontal=0.08, vertical=0.04),
                    paragraphs=[
                        Paragraph(
                            text=f"{{m:{column.name}}} {column.declared_type}",
                            space_after=0,
                            line_spacing=1.0,
                        )
                        for column in columns
                    ],
                    font_size=12,
                )
            )
        pose_columns = [
            column.name for column in self.poses.columns(table=PoseTable.POSE)
        ]
        pose_corner = table_areas[PoseTable.POSE]
        for foreign_key in self.poses.foreign_keys():
            row = pose_columns.index(foreign_key.column)
            target = table_areas[foreign_key.referenced_table]
            items.append(
                Arrow(
                    start=Position(
                        x=pose_corner.x + table_width,
                        y=pose_corner.y + header_height + (row + 0.6) * row_height,
                    ),
                    end=Position(x=target.x, y=target.y + header_height / 2),
                    color=Color.DARK_GRAY,
                )
            )
        rows = self.poses.joined_rows()
        return ContentSlide(
            title="A Relational Database of Robot Poses",
            section=Section.DATA_MODELS,
            items=[
                *items,
                CodeBlock.from_file(
                    area=Rectangle(left=6.8, top=1.3, width=6.05, height=1.55),
                    path=Snippet.POSE_QUERY.path,
                    font_size=13,
                ),
                Table(
                    position=Position(x=6.8, y=3.05),
                    column_widths=[1.1, 1.15, 1.15, 1.15, 1.15],
                    rows=[
                        ["time", "frame", "x", "y", "z"],
                        *[
                            [
                                f"{value:g}" if isinstance(value, float) else value
                                for value in row
                            ]
                            for row in rows
                        ],
                    ],
                    row_height=0.38,
                    font_size=15,
                ),
                self.caption(
                    text="The gripper approaching cup_3: a pose schema inspired by "
                    "CRAM [5], and a join over it (computed with SQLite)",
                    top=5.75,
                ),
            ],
        )

    def three_shapes_slide(self) -> Slide:
        """
        :return: The last pose of the pose database as an object, a document and the
            rows that store it.
        """
        last_pose = len(self.poses.poses)
        stored = self.poses.stored_rows(pose_id=last_pose)
        rows = "\n".join(f"{table.value:<11}{row!r}" for table, row in stored.items())
        widths = [4.5, 4.2, 3.2]
        gap = 0.25
        lefts = [0.45, 0.45 + widths[0] + gap, 0.45 + widths[0] + widths[1] + 2 * gap]
        headings = ["Object (Python)", "Document (JSON)", "Rows (SQL)"]
        code_blocks = [
            CodeBlock.from_file(
                area=Rectangle(left=lefts[0], top=1.8, width=widths[0], height=2.3),
                path=Snippet.POSE_OBJECT.path,
                font_size=10,
            ),
            CodeBlock.from_file(
                area=Rectangle(left=lefts[1], top=1.8, width=widths[1], height=2.3),
                path=Snippet.POSE_DOCUMENT.path,
                font_size=10,
            ),
            CodeBlock(
                area=Rectangle(left=lefts[2], top=1.8, width=widths[2], height=2.3),
                source_code=rows,
                language="text",
                font_size=10,
            ),
        ]
        return ContentSlide(
            title="One Pose, Three Shapes",
            section=Section.DATA_MODELS,
            items=[
                *[
                    self.text_box(
                        area=Rectangle(left=left, top=1.3, width=width, height=0.45),
                        paragraphs=[self.heading(text=heading, space_after=0)],
                        font_size=17,
                    )
                    for left, width, heading in zip(lefts, widths, headings)
                ],
                *code_blocks,
                self.text_box(
                    area=Rectangle(left=0.45, top=4.35, width=12.4, height=1.9),
                    paragraphs=Paragraph.bullet_points(
                        texts=[
                            "Object and document: one nested tree – stored and loaded "
                            "in one piece, so documents have {b:less mismatch}",
                            "Rows: three flat tuples linked by ids – written with three "
                            "inserts, put back together with joins",
                            "Ids and joins do not exist in the program: that gap is "
                            "the {b:object-relational mismatch}",
                        ],
                        space_after=6,
                    ),
                    font_size=17,
                ),
            ],
        )

    def schema_slide(self) -> Slide:
        """
        :return: Schema on write against schema on read, with adding a force reading
            to stored poses as the example.
        """
        return ContentSlide(
            title="Schema on Write vs. Schema on Read",
            section=Section.DATA_MODELS,
            items=[
                self.text_box(
                    area=Rectangle(left=0.45, top=1.3, width=6.0, height=2.0),
                    paragraphs=[
                        self.heading(text="Schema on write (relational)"),
                        *Paragraph.bullet_points(
                            texts=[
                                "The database knows the structure and rejects data "
                                "that does not fit",
                                "Like static typing: errors show when writing",
                                "A change migrates every row:",
                            ],
                            space_after=6,
                        ),
                    ],
                    font_size=17,
                ),
                CodeBlock.from_file(
                    area=Rectangle(left=0.45, top=3.65, width=6.0, height=0.5),
                    path=Snippet.ADD_FORCE_COLUMN.path,
                    font_size=13,
                ),
                self.text_box(
                    area=Rectangle(left=6.85, top=1.3, width=6.0, height=2.3),
                    paragraphs=[
                        self.heading(text="Schema on read (document)"),
                        *Paragraph.bullet_points(
                            texts=[
                                "Any document is accepted; the structure lives in the "
                                "code that reads it",
                                "Like dynamic typing: errors show when reading",
                                "A change is just new documents – readers handle old "
                                "and new:",
                            ],
                            space_after=6,
                        ),
                    ],
                    font_size=17,
                ),
                CodeBlock.from_file(
                    area=Rectangle(left=6.85, top=3.65, width=6.0, height=0.75),
                    path=Snippet.READ_FORCE.path,
                    font_size=13,
                ),
                TakeAway(
                    text="kitchen robot gets a force sensor: migrate once, or handle "
                    "both shapes in every reader"
                ),
            ],
        )

    def document_slides(self) -> list[Slide]:
        """
        :return: The document model, a collection of recorded transforms and its
            benefits and drawbacks.
        """
        return [
            BulletSlide(
                title="The Document Data District",
                section=Section.DATA_MODELS,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "NoSQL (Not only SQL) solutions are getting more popular",
                        "Data is stored in self-contained JSON-like documents",
                        "Tree-like structures work well",
                        "No schema and no data types are enforced: schema on read",
                        "MongoDB is the most popular implementation",
                        "{s:Kitchen robot:} one document per recorded transform "
                        "message",
                    ]
                ),
                text_area=Rectangle(left=0.45, top=1.2, width=8.2, height=5.0),
                items=[
                    Picture(
                        path=Figure.DOCUMENT_SCHEMA,
                        position=Position(x=9.3, y=1.2),
                        height=5.5,
                    )
                ],
            ),
            ContentSlide(
                title="A Document Collection",
                section=Section.DATA_MODELS,
                items=[
                    Picture(
                        path=Figure.DOCUMENT_COLLECTION,
                        position=Position(x=0.45, y=2.0),
                        width=12.4,
                    ),
                    self.caption(
                        text="Recorded transforms of a robot, one document per message",
                        top=6.2,
                    ),
                ],
            ),
            ComparisonSlide(
                title="Benefits and Drawbacks of Documents",
                section=Section.DATA_MODELS,
                left=Column(
                    heading="Benefits",
                    points=[
                        "Flexibility of everything",
                        "Locality of data",
                        "Easy one-to-many relationships",
                        "Less mismatch: a document is shaped like the object in memory",
                        "Good for data without structure",
                    ],
                ),
                right=Column(
                    heading="Drawbacks",
                    points=[
                        "Bad many-to-many and many-to-one relationships",
                        "No data validation",
                        "Joining has to be done in application code",
                        "Weak indexing",
                        "Duplicated data",
                        "Messy path access",
                    ],
                ),
            ),
        ]

    def graph_slides(self) -> list[Slide]:
        """
        :return: The graph model, a kitchen graph queried with SPARQL, why graphs
            suit many-to-many data, and their peaks and valleys.
        """
        return [
            BulletSlide(
                title="Graph Data Peaks",
                section=Section.DATA_MODELS,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "Many-to-many relationships everywhere: in SQL every hop is "
                        "one more join, and joins pile up",
                        "Graph databases model data as a graph: entities are nodes, "
                        "relationships are edges",
                        "Lecture 03: RDF stores knowledge as triples – a triple store "
                        "{i:is} a graph database, queried with SPARQL",
                        "Property graphs: nodes and edges carry key-value properties "
                        "(e.g. Neo4j, queried with Cypher)",
                        "Queries follow paths of any length – like recursive Datalog "
                        "rules",
                    ]
                ),
            ),
            *self.kitchen_graph_slides(),
            BulletSlide(
                title="Why Graphs for Many-to-Many Data?",
                section=Section.DATA_MODELS,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "A table answers one hop with one join; {i:k} hops need "
                            "{i:k} joins over the whole relation",
                            "A graph database stores each node's edges with the node "
                            "and follows them directly",
                            Paragraph(
                                text="A benchmark from [11]: 1 million people, find "
                                "everyone within {i:k} friendship hops",
                                level=BulletLevel.FIRST,
                                space_after=4,
                            ),
                        ],
                        space_after=10,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "4 hops: MySQL 1,543.5 s, Neo4j 1.4 s",
                            "5 hops: the SQL query did not finish within an hour",
                        ],
                        level=BulletLevel.SECOND,
                        space_after=10,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "{a:Caution:} a book by Neo4j authors – independent "
                            "comparisons find that tuning and scenario decide, and "
                            "MySQL sometimes wins [12]",
                        ]
                    ),
                ],
                take_away="measure on your own data and queries before you switch",
            ),
            ComparisonSlide(
                title="Peaks and Valleys of Graphs",
                section=Section.DATA_MODELS,
                left=Column(
                    heading="Peaks",
                    points=[
                        "High performance for many-to-many connected data",
                        "Flexible schema, since new data can be added as new nodes",
                        "Close to objects with references",
                    ],
                ),
                right=Column(
                    heading="Valleys",
                    points=[
                        "Non-relationship queries (scans, aggregates) perform poorly",
                        "Several query languages (SPARQL, Cypher, Gremlin); the ISO "
                        "standard GQL only since 2024",
                        "No classes: types and constraints stay in the application",
                        "No data validation by default",
                    ],
                ),
            ),
        ]

    def kitchen_graph_slides(self) -> list[Slide]:
        """
        :return: The kitchen graph drawn from its triples next to the SPARQL query
            for the containers on the table, first asking for its answer, then
            showing the computed one.
        """
        node_width = 1.9
        node_height = 0.42
        corners = {
            "Container": Position(x=1.5, y=1.3),
            "DrinkingContainer": Position(x=0.45, y=2.2),
            "Bowl": Position(x=2.55, y=2.2),
            "Plate": Position(x=4.65, y=2.2),
            "Cup": Position(x=0.45, y=3.1),
            "cup_3": Position(x=0.45, y=4.15),
            "bowl_2": Position(x=2.55, y=4.15),
            "plate_1": Position(x=4.65, y=4.15),
            "table": Position(x=2.55, y=5.2),
        }
        classes = self.kitchen.classes()
        items: list[Element] = [
            DiagramNode(
                area=Rectangle(
                    left=corner.x, top=corner.y, width=node_width, height=node_height
                ),
                text=name,
                fill=Color.PALE_PURPLE if name in classes else Color.PALE_YELLOW,
                font_size=13,
            )
            for name, corner in corners.items()
        ]
        for edge in self.kitchen.edges():
            source = corners[edge.subject]
            target = corners[edge.target]
            upward = target.y < source.y
            start = Position(
                x=source.x + node_width / 2,
                y=source.y if upward else source.y + node_height,
            )
            end = Position(
                x=target.x + node_width / 2,
                y=target.y + node_height if upward else target.y,
            )
            items.append(Arrow(start=start, end=end, color=Color.DARK_GRAY))
            items.append(
                Label(
                    area=Rectangle(
                        left=(start.x + end.x) / 2 + 0.05,
                        top=(start.y + end.y) / 2 - 0.13,
                        width=1.0,
                        height=0.26,
                    ),
                    text="a" if edge.predicate == Predicate.TYPE else edge.predicate,
                    font_size=10,
                    alignment=Alignment.LEFT,
                )
            )
        answer = ", ".join(self.kitchen.containers_on_table())
        items.extend(
            [
                CodeBlock.from_file(
                    area=Rectangle(left=6.9, top=1.3, width=5.95, height=2.3),
                    path=Snippet.CONTAINERS_ON_TABLE.path,
                    font_size=13,
                ),
                self.caption(
                    text="SPARQL (lecture 03): every container on the table",
                    top=3.65,
                    left=6.9,
                    width=5.95,
                ),
            ]
        )
        title = "A Graph of the Kitchen"
        return [
            ContentSlide(
                title=title,
                section=Section.DATA_MODELS,
                items=[
                    *items,
                    TakeAway(
                        text="{a:Which objects does the query return – and the plate?}"
                    ),
                ],
            ),
            ContentSlide(
                title=title,
                section=Section.DATA_MODELS,
                items=[
                    *items,
                    self.text_box(
                        area=Rectangle(left=6.9, top=4.1, width=5.95, height=2.1),
                        paragraphs=Paragraph.bullet_points(
                            texts=[
                                f"Answer: {{b:{answer}}}",
                                "{m:subClassOf*} follows a path of any length – cup_3 "
                                "is a Container two hops up",
                                "plate_1 is on the table, but no Container",
                            ],
                            space_after=6,
                        ),
                        font_size=16,
                    ),
                    TakeAway(
                        text="purple: classes, yellow: individuals – the drawing and the "
                        "answer both come from the same triples"
                    ),
                ],
            ),
        ]

    def event_log_slide(self) -> Slide:
        """
        :return: The event log as a data model for streams, with a rosbag-like log.
        """
        return ContentSlide(
            title="Event Logs: A Data Model for Streams",
            section=Section.DATA_MODELS,
            items=[
                self.text_box(
                    area=Rectangle(left=0.45, top=1.3, width=6.1, height=4.9),
                    paragraphs=Paragraph.bullet_points(
                        texts=[
                            "An append-only sequence of events in time order – nothing "
                            "is updated in place",
                            "Each reader keeps its own position (offset) and can "
                            "replay from any point",
                            "The current state is derived: replay the log to rebuild "
                            "it",
                            "Event logs such as Apache Kafka; time-series databases "
                            "such as InfluxDB for sensor data",
                            "{s:Kitchen robot:} a rosbag records topics into a log – "
                            "replaying it re-runs the episode",
                        ],
                        space_after=8,
                    ),
                    font_size=17,
                ),
                Table(
                    position=Position(x=6.9, y=1.5),
                    column_widths=[0.85, 0.95, 1.75, 2.4],
                    rows=[
                        ["offset", "time", "topic", "message"],
                        ["0", "12.00", "/joint_states", "arm joints"],
                        ["1", "12.03", "/camera/image", "image 1842"],
                        ["2", "12.05", "/tf", "gripper in map"],
                        ["3", "12.10", "/perception", "cup_3 on table"],
                        ["4", "12.40", "/grasp", "grasp succeeded"],
                    ],
                    row_height=0.45,
                    font_size=14,
                ),
                self.caption(
                    text="An illustrative log: a reader at offset 3 has seen offsets "
                    "0 to 2",
                    top=4.35,
                    left=6.9,
                    width=5.95,
                ),
            ],
        )

    # %% derived data

    def derived_data_slides(self) -> list[Slide]:
        """
        :return: Systems of record, the robot's data flow, batch processing with
            training as a batch job, MapReduce and stream processing.
        """
        return [
            self.contents(highlighted_section=Section.DERIVED_DATA),
            self.derived_data_slide(),
            ContentSlide(
                title="A Map of Derived Data",
                section=Section.DERIVED_DATA,
                items=[
                    Picture(
                        path=Figure.MAP_OF_DERIVED_DATA,
                        position=Position(x=4.4, y=1.1),
                        height=5.0,
                    ),
                    self.caption(text="Illustration from [1]", top=6.2),
                ],
            ),
            self.robot_data_flow(),
            BulletSlide(
                title="Batch Processing",
                section=Section.DERIVED_DATA,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Core idea:} process large datasets in batches, "
                            "producing a final output",
                            "{b:Building blocks:} inspired by Unix tools ({m:awk}, "
                            "{m:grep}, {m:sort})",
                            Paragraph(
                                text="{b:Design principles:}",
                                level=BulletLevel.FIRST,
                                space_after=4,
                            ),
                        ]
                    ),
                    *Paragraph.bullet_points(
                        texts=["Immutable input data", "Small, well-defined tasks"],
                        level=BulletLevel.SECOND,
                        space_after=4,
                    ),
                    Paragraph(
                        text="{b:Key challenges:}",
                        level=BulletLevel.FIRST,
                        space_after=4,
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Partitioning data for efficient processing",
                            "Handling failures and ensuring data consistency",
                        ],
                        level=BulletLevel.SECOND,
                        space_after=4,
                    ),
                ],
            ),
            BulletSlide(
                title="Back to SGD: Training Is a Batch Job",
                section=Section.DERIVED_DATA,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "The training set is the immutable input; the fitted model is "
                        "derived data",
                        "A mini-batch is a small part of the data, read from storage "
                        "when it is needed",
                        "An epoch is one pass over the whole dataset; shuffling "
                        "re-partitions it",
                        "A crash costs one epoch, not the whole training run: "
                        "checkpoint the parameters",
                        "Retrain from the record when the data or the model changes",
                    ],
                    space_after=10,
                ),
                take_away="SGD never needs all data at once – so the data can live in "
                "a database, not in memory",
            ),
            BulletSlide(
                title="Joins, Fault Tolerance and Limits of Batch Processing",
                section=Section.DERIVED_DATA,
                paragraphs=[
                    *Paragraph.bullet_points(
                        texts=[
                            "{b:Join algorithms:} sort-merge joins, broadcast hash "
                            "joins, partitioned hash joins – the joins of a Datalog "
                            "rule, at scale",
                            "{b:Fault tolerance:} frequent checkpoints and task retries "
                            "(MapReduce), in-memory state and deterministic operators "
                            "(dataflow engines)",
                            Paragraph(
                                text="{b:Limitations:}",
                                level=BulletLevel.FIRST,
                                space_after=4,
                            ),
                        ]
                    ),
                    *Paragraph.bullet_points(
                        texts=[
                            "Batch processing is suitable for offline, historical data "
                            "analysis",
                            "Lacks real-time capabilities",
                            "Requires bounded input data",
                        ],
                        level=BulletLevel.SECOND,
                        space_after=4,
                    ),
                ],
            ),
            ComparisonSlide(
                title="MapReduce: Batch Jobs over a Distributed Filesystem",
                section=Section.DERIVED_DATA,
                left=Column(
                    heading="Mapper",
                    points=[
                        "Called once for every input record",
                        "Extracts arbitrarily many key-value pairs",
                        "Stateless: each record is handled independently",
                    ],
                ),
                right=Column(
                    heading="Reducer",
                    points=[
                        "Collects all the values belonging to the same key from the "
                        "mappers",
                        "Is called with an iterator over that collection of values",
                    ],
                ),
            ),
            ContentSlide(
                title="A MapReduce Job",
                section=Section.DERIVED_DATA,
                items=[
                    Picture(
                        path=Figure.MAP_REDUCE_JOB,
                        position=Position(x=2.6, y=1.15),
                        height=5.0,
                    ),
                    self.caption(
                        text="MapReduce job with three mappers and three reducers [1]",
                        top=6.3,
                    ),
                ],
            ),
            BulletSlide(
                title="Continuous Data Flows",
                section=Section.DERIVED_DATA,
                paragraphs=Paragraph.bullet_points(
                    texts=[
                        "{b:Core idea:} process unbounded streams of data in real time "
                        "or near real time",
                        "{b:Building blocks:} the event logs of the data models "
                        "section, message brokers and stream processing engines, for "
                        "example ROS topics",
                        "{b:Data sources:} user activity, sensor data, data feeds, "
                        "database change logs, robots",
                        "{b:Key concepts:} event time vs. processing time, windowing, "
                        "watermarks",
                        "{s:Kitchen robot:} a camera image is stamped when it is taken, "
                        "not when perception finishes with it",
                    ]
                ),
            ),
        ]

    def derived_data_slide(self) -> Slide:
        """
        :return: One system of record and three kinds of data derived from it, with
            the question which of them to trust.
        """
        record = Rectangle(left=0.8, top=2.6, width=3.4, height=1.1)
        derived = [
            "Search index over episodes",
            "Grasp success rate per object",
            "Trained grasp model",
        ]
        derived_left = 6.6
        derived_width = 3.6
        derived_height = 0.75
        derived_tops = [1.55, 2.775, 4.0]
        return ContentSlide(
            title="Systems of Record and Derived Data",
            section=Section.DERIVED_DATA,
            notes="Let the students vote by show of hands first. Answer: the NEEMs. "
            "The success rate is recomputed from them.",
            items=[
                DiagramNode(
                    area=record,
                    text="Episodes (NEEMs)",
                    fill=Color.PALE_YELLOW,
                    bold=True,
                    font_size=17,
                ),
                Label(
                    area=Rectangle(
                        left=record.left,
                        top=record.top + record.height + 0.05,
                        width=record.width,
                        height=0.35,
                    ),
                    text="system of record: the authoritative data, written once",
                    font_size=13,
                ),
                *[
                    DiagramNode(
                        area=Rectangle(
                            left=derived_left,
                            top=top,
                            width=derived_width,
                            height=derived_height,
                        ),
                        text=text,
                        fill=Color.PALE_GREEN,
                    )
                    for text, top in zip(derived, derived_tops)
                ],
                *[
                    Arrow(
                        start=Position(
                            x=record.left + record.width,
                            y=record.top + record.height / 2,
                        ),
                        end=Position(x=derived_left, y=top + derived_height / 2),
                        color=Color.DARK_GRAY,
                    )
                    for top in derived_tops
                ],
                Label(
                    area=Rectangle(
                        left=derived_left,
                        top=derived_tops[-1] + derived_height + 0.05,
                        width=derived_width,
                        height=0.35,
                    ),
                    text="derived: computed from the record, can be recomputed",
                    font_size=13,
                ),
                self.text_box(
                    area=Rectangle(left=10.5, top=1.55, width=2.4, height=3.2),
                    paragraphs=[
                        Paragraph(
                            text="Real systems combine several stores: databases, "
                            "caches, indexes, analytics",
                        )
                    ],
                    font_size=15,
                ),
                TakeAway(
                    text="{a:The grasp success rate and the NEEMs disagree – which one "
                    "do you trust?}"
                ),
            ],
        )

    def robot_data_flow(self) -> Slide:
        """
        :return: The diagram of how the kitchen robot's data flows from its sensors
            to the world model, the episodes and what is derived from them.
        """
        top_row = 1.9
        bottom_row = 4.0
        node_width = 2.4
        node_height = 0.9
        lefts = [0.6, 3.6, 6.6, 9.6]
        nodes = [
            (lefts[0], top_row, "Sensors", Color.PALE_BLUE),
            (lefts[1], top_row, "ROS topics", Color.PALE_BLUE),
            (lefts[2], top_row, "Episodes (NEEMs)", Color.PALE_YELLOW),
            (lefts[3], top_row, "Batch job", Color.PALE_PURPLE),
            (lefts[1], bottom_row, "World model (twin)", Color.PALE_GREEN),
            (
                lefts[3],
                bottom_row,
                "Grasp statistics, trained models",
                Color.PALE_GREEN,
            ),
        ]
        middle = top_row + node_height / 2
        horizontal_arrows = [
            Arrow(
                start=Position(x=left + node_width, y=middle),
                end=Position(x=next_left, y=middle),
                color=Color.DARK_GRAY,
            )
            for left, next_left in zip(lefts, lefts[1:])
        ]
        vertical_arrows = [
            Arrow(
                start=Position(x=left + node_width / 2, y=top_row + node_height),
                end=Position(x=left + node_width / 2, y=bottom_row),
                color=Color.DARK_GRAY,
            )
            for left in [lefts[1], lefts[3]]
        ]
        labels = [
            Label(
                area=Rectangle(left=left, top=top, width=node_width, height=0.35),
                text=text,
            )
            for left, top, text in [
                (lefts[1], top_row - 0.4, "stream"),
                (lefts[2], top_row - 0.4, "system of record"),
                (lefts[1], bottom_row + node_height + 0.05, "current state, EQL"),
                (lefts[3], bottom_row + node_height + 0.05, "derived, recomputable"),
            ]
        ]
        return ContentSlide(
            title="The Kitchen Robot's Data Flow",
            section=Section.DERIVED_DATA,
            items=[
                *[
                    DiagramNode(
                        area=Rectangle(
                            left=left, top=top, width=node_width, height=node_height
                        ),
                        text=text,
                        fill=fill,
                    )
                    for left, top, text, fill in nodes
                ],
                *horizontal_arrows,
                *vertical_arrows,
                *labels,
                TakeAway(
                    text="the grasp success rate is derived data – the NEEMs are "
                    "its record"
                ),
            ],
        )

    # %% krrood

    def krrood_slides(self) -> list[Slide]:
        """
        :return: How krrood generates tables from dataclasses, stores objects and
            answers EQL queries with SQL, and the design decisions it takes.
        """
        return [
            self.contents(highlighted_section=Section.KRROOD),
            self.mapped_tables_slide(),
            self.stored_query_slide(),
            ContentSlide(
                title="krrood and the Design Decisions",
                section=Section.KRROOD,
                items=[
                    Table(
                        position=Position(x=0.6, y=1.35),
                        column_widths=[2.6, 9.5],
                        rows=[
                            ["Decision", "With krrood"],
                            [
                                "Data model",
                                "relational tables, generated from the dataclasses "
                                "by ORMatic",
                            ],
                            [
                                "Schema",
                                "on write, derived from the dataclasses – one source "
                                "for program and database",
                            ],
                            [
                                "Query language",
                                "EQL, evaluated on objects in memory or translated "
                                "to SQL",
                            ],
                            [
                                "Transactions",
                                "the SQLAlchemy session: commit all or roll back",
                            ],
                            [
                                "Documents",
                                "JSON through {m:DataclassJSONSerializer}",
                            ],
                            [
                                "Ontologies",
                                "dataclasses generated from OWL ontologies by "
                                "ontomatic",
                            ],
                        ],
                        row_height=0.6,
                        font_size=16,
                    ),
                    TakeAway(
                        text="the Semantic Digital Twin and Giskard store their data "
                        "with ORMatic as well"
                    ),
                ],
            ),
        ]

    def mapped_tables_slide(self) -> Slide:
        """
        :return: The pose dataclasses next to how ORMatic is run on them and the
            tables it generates.
        """
        rows = [
            [
                table.name,
                ", ".join(
                    column.name
                    if column.referenced_table is None
                    else f"{column.name} → {column.referenced_table}"
                    for column in table.columns
                ),
            ]
            for table in self.pose_store.tables()
        ]
        return ContentSlide(
            title="The Dataclass Is the Schema",
            section=Section.KRROOD,
            items=[
                *self.code_with_caption(
                    snippet=Snippet.POSE_DATACLASSES,
                    area=Rectangle(left=0.45, top=1.3, width=4.5, height=3.3),
                    caption="the domain model: plain dataclasses",
                    font_size=12,
                ),
                *self.code_with_caption(
                    snippet=Snippet.GENERATE_INTERFACE,
                    area=Rectangle(left=5.2, top=1.3, width=7.65, height=1.75),
                    caption="ORMatic generates the SQLAlchemy tables from them",
                    font_size=13,
                ),
                Table(
                    position=Position(x=5.2, y=3.55),
                    column_widths=[2.0, 5.65],
                    rows=[["table", "columns"], *rows],
                    row_height=0.4,
                    font_size=12,
                ),
                TakeAway(
                    text="change the dataclass and regenerate – no hand-written "
                    "schema to drift apart"
                ),
            ],
        )

    def stored_query_slide(self, *, height: float = 0.85) -> Slide:
        """
        :return: Storing the poses and querying the ones lower than *height* with
            EQL, next to the SQL the query becomes and the answers it gives.
        """
        store = self.pose_store
        sql = "\n".join(
            textwrap.fill(line, width=58, subsequent_indent="    ")
            for line in store.sql_of_poses_below(height=height).splitlines()
        )
        stored = store.stored_poses_below(height=height)
        in_memory = store.poses_in_memory_below(height=height)
        times = ", ".join(f"t = {pose.time:g} s" for pose in stored)
        agreement = "the same" if stored == in_memory else "a different"
        return ContentSlide(
            title="Storing and Querying with EQL",
            section=Section.KRROOD,
            items=[
                *self.code_with_caption(
                    snippet=Snippet.STORE_AND_QUERY,
                    area=Rectangle(left=0.45, top=1.3, width=6.3, height=2.3),
                    caption="to_dao and from_dao bridge objects and rows",
                    font_size=12,
                ),
                CodeBlock(
                    area=Rectangle(left=7.0, top=1.3, width=5.85, height=2.3),
                    source_code=sql,
                    language="sql",
                    font_size=10,
                ),
                self.caption(
                    text="the SQL the EQL query becomes (computed)",
                    top=3.65,
                    left=7.0,
                    width=5.85,
                ),
                self.text_box(
                    area=Rectangle(left=0.45, top=4.2, width=12.4, height=1.9),
                    paragraphs=Paragraph.bullet_points(
                        texts=[
                            f"Answer from the database: the pose at {{b:{times}}}",
                            f"With {{m:domain=poses}} the same query runs on the "
                            f"objects in memory – with {agreement} answer",
                            "{m:commit()} ends a transaction: all poses are stored, "
                            "or none",
                        ],
                        space_after=6,
                    ),
                    font_size=17,
                ),
                TakeAway(
                    text="one query language for objects and databases – EQL "
                    "(lecture 02)"
                ),
            ],
        )

    # %% outlook

    def outlook_slides(self) -> list[Slide]:
        """
        :return: The design decisions at a glance, the takeaways, a closing quote and
            the references.
        """
        return [
            ContentSlide(
                title="Design Decisions at a Glance",
                section=Section.OUTLOOK,
                items=[
                    Table(
                        position=Position(x=0.6, y=1.35),
                        column_widths=[2.2, 4.6, 5.3],
                        rows=[
                            ["Decision", "Options", "Our choice for the episodes"],
                            *[
                                [decision.decision, decision.options, decision.choice]
                                for decision in self.design_decisions()
                            ],
                        ],
                        row_height=0.6,
                        font_size=15,
                    ),
                    TakeAway(
                        text="the task is solved – for these episodes; other data "
                        "would need other choices"
                    ),
                ],
            ),
            BulletSlide(
                title="Key Takeaways",
                section=Section.OUTLOOK,
                text_area=Rectangle(left=0.45, top=1.3, width=12.4, height=4.9),
                font_size=17,
                paragraphs=[
                    *self.numbered(
                        texts=[
                            "Databases are a vital component of modern AI systems: "
                            "persistence, shared access, large data and guarantees.",
                            "Every system has to be reliable, scalable and "
                            "maintainable; transactions and replication provide much "
                            "of it.",
                            "Relational tables are Datalog facts in the closed world; "
                            "triple stores are graph databases.",
                            "The shape of the data and of its queries picks the data "
                            "model – no single tool fits all data needs.",
                            "Keep recorded data apart from derived data: statistics "
                            "and trained models can be recomputed.",
                            "Training with SGD is a batch job over stored data; robots "
                            "produce streams.",
                            "Technology is a tool – don't be religious about it.",
                        ],
                        space_after=6,
                    ),
                    Paragraph(text="", space_after=6),
                    Paragraph(text="{s:Next week:} Uncertainty"),
                ],
            ),
            ContentSlide(
                title="System Design Is an Iterative Process",
                section=Section.OUTLOOK,
                items=[
                    self.quote(
                        text="A Complex System That Works Is Invariably Found To Have "
                        "Evolved From A Simple System That Worked. The parallel "
                        "proposition also appears to be true: A Complex System Designed "
                        "From Scratch Never Works And Cannot Be Made To Work. You Have "
                        "To Start Over, Beginning With A Working Simple System.",
                        source="John Gall, Systemantics (1975) [8]",
                        top=1.8,
                    )
                ],
            ),
            self.references(),
        ]

    def references(self) -> Slide:
        """
        :return: The works the slides cite, numbered as they cite them.
        """
        works = [
            "M. Kleppmann, {i:Designing Data-Intensive Applications}. O’Reilly, 2019.",
            "R. Martin, {i:Clean Architecture: A Craftsman’s Guide to Software "
            "Structure and Design}. Pearson Education, 2018.",
            "A. Kaplan, {i:The Conduct of Inquiry: Methodology for Behavioural "
            "Science}. Routledge, 2017.",
            "E. F. Codd, “A relational model of data for large shared data banks,” "
            "{i:Commun. ACM}, vol. 13, no. 6, pp. 377–387, 1970.",
            "M. Beetz, L. Mösenlechner, M. Tenorth, “CRAM – A Cognitive Robot Abstract "
            "Machine for Everyday Manipulation in Human Environments,” IROS, 2010.",
            "M. Bayer, “SQLAlchemy,” {i:The Architecture of Open Source Applications, "
            "Volume II}. aosabook.org, 2012.",
            "DB-Engines, “DB-Engines Ranking.” https://db-engines.com/en/ranking",
            "J. Gall, {i:Systemantics}. Wildwood House, 1977.",
            "R. L. Glass, {i:Facts and Fallacies of Software Engineering}. "
            "Addison-Wesley, 2002. Facts 41 and 42.",
            "S. Patel, B. L. Hou, A. Purohit, K. Xu, J. Pan, H. He, V. Chen, “Is Agent "
            "Code Less Maintainable Than Human Code?” arXiv:2606.21804, 2026.",
            "A. Vukotic, N. Watt, T. Abedrabbo, D. Fox, J. Partner, {i:Neo4j in "
            "Action}. Manning, 2014.",
            "Hohenstein, Jergler, “Database Performance Comparisons: …,” SciTePress, "
            "2019. https://www.scitepress.org/Papers/2019/79266/79266.pdf",
            "GitLab, “Postmortem of database outage of January 31,” 2017. "
            "https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-"
            "january-31/",
            "J. Dean, L. A. Barroso, “The Tail at Scale,” {i:Commun. ACM}, vol. 56, "
            "no. 2, pp. 74–80, 2013.",
        ]
        return BulletSlide(
            title="Further Reading",
            section=Section.OUTLOOK,
            paragraphs=[
                Paragraph(text=f"[{number}]  {work}", space_after=4)
                for number, work in enumerate(works, start=1)
            ],
            font_size=13,
        )


# %% command line


def main() -> None:
    """
    Render the charts, then write the lecture to PowerPoint and PDF next to this
    module.
    """
    lecture = DataIntensiveSystems()
    lecture.response_times.render_histogram(path=Chart.RESPONSE_TIMES)
    deck = lecture.deck()
    output = Path(__file__).with_suffix("")
    PowerPointRenderer(deck=deck, path=output.with_suffix(".pptx")).render()
    PDFRenderer(deck=deck, path=output.with_suffix(".pdf")).render()
    print(f"{len(deck.slides)} slides -> {output.name}.pptx / .pdf")


if __name__ == "__main__":
    main()
