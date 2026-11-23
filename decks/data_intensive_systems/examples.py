"""
The examples the slides show, computed: a pose database in SQLite, the same poses
stored with ORMatic and queried with EQL, simulated response times and a small
kitchen knowledge graph queried with SPARQL.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property
from pathlib import Path

import numpy as np
from krrood.entity_query_language.factories import an, entity, variable
from krrood.entity_query_language.query.query import Entity
from krrood.ormatic.data_access_objects.helper import to_dao
from krrood.ormatic.eql_interface import eql_to_sql
from krrood.patterns.path_enumeration import PathEnumeration
from matplotlib.figure import Figure
from rdflib import Graph
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from slide_style_kit.style import Color

from orm.pose_interface import Base
from poses import GripperPose, Point

# %% files


class Snippet(StrEnum):
    """
    The code snippets shown on the slides or run by the examples, by file name.
    """

    OBJECT_RELATIONAL_MAPPING = "object_relational_mapping.py"
    """
    The SQLAlchemy classes of a pose.
    """

    PUT_AWAY_DATALOG = "put_away.prolog"
    """
    The objects on the table and where they belong, as a Datalog rule over facts.
    """

    PUT_AWAY_SQL = "put_away.sql"
    """
    The same question as :attr:`PUT_AWAY_DATALOG`, as an SQL join.
    """

    POSE_SCHEMA = "pose_schema.sql"
    """
    The tables of the pose database.
    """

    POSE_QUERY = "pose_query.sql"
    """
    The join that reads the gripper's positions back from the pose database.
    """

    POSE_OBJECT = "pose_object.py"
    """
    The last pose of :class:`PoseDatabase` as a Python object.
    """

    POSE_DOCUMENT = "pose.json"
    """
    The last pose of :class:`PoseDatabase` as a JSON document.
    """

    ADD_FORCE_COLUMN = "add_force_column.sql"
    """
    The migration that adds a force reading to every stored pose.
    """

    READ_FORCE = "read_force.py"
    """
    Reading a force reading that only newer documents have.
    """

    KITCHEN_GRAPH = "kitchen.ttl"
    """
    The kitchen knowledge graph of :class:`KitchenGraph`, in Turtle.
    """

    CONTAINERS_ON_TABLE = "containers_on_table.rq"
    """
    The SPARQL query for every container on the table, whatever its subclass depth.
    """

    POSE_DATACLASSES = "pose_dataclasses.py"
    """
    The pose dataclasses of :mod:`poses`, without their docstrings.
    """

    GENERATE_INTERFACE = "generate_interface.py"
    """
    The heart of :mod:`generate_pose_interface`: ORMatic mapping the pose dataclasses.
    """

    STORE_AND_QUERY = "store_and_query.py"
    """
    Storing poses through the generated interface and querying them with EQL.
    """

    COUNT_GRASP = "count_grasp.sql"
    """
    Counting one grasp of cup_3 in a single statement, so no update is lost.
    """

    @property
    def path(self) -> Path:
        """
        The file holding the snippet.
        """
        return Path(__file__).parent / "snippets" / self.value


class Chart(PathEnumeration):
    """
    The charts the examples render, written next to this module.
    """

    DIRECTORY = Path(__file__).parent / "charts"
    """
    The directory holding the other charts.
    """

    RESPONSE_TIMES = DIRECTORY / "response_times.png"
    """
    The histogram of :class:`ResponseTimes` with its percentiles marked.
    """


# %% pose database


class PoseTable(StrEnum):
    """
    The tables of the pose database.
    """

    POSE = "pose"
    """
    A timestamped pose in a coordinate frame, referencing its position and orientation.
    """

    POSITION = "position"
    """
    A point in space.
    """

    QUATERNION = "quaternion"
    """
    An orientation as a unit quaternion.
    """


@dataclass(kw_only=True, frozen=True)
class TableColumn:
    """
    One column of a database table.
    """

    name: str
    """
    The name of the column.
    """

    declared_type: str
    """
    The SQL type the schema declares for the column.
    """


@dataclass(kw_only=True, frozen=True)
class ForeignKey:
    """
    A column whose values are the ids of rows of another table.
    """

    table: PoseTable
    """
    The table holding the column.
    """

    column: str
    """
    The name of the referencing column.
    """

    referenced_table: PoseTable
    """
    The table whose ids the column holds.
    """


@dataclass(kw_only=True)
class PoseDatabase:
    """
    The gripper approaching cup_3, stored in an in-memory SQLite database with the
    schema of :attr:`Snippet.POSE_SCHEMA`.
    """

    poses: list[GripperPose] = field(
        default_factory=lambda: [
            GripperPose(time=0.0, position=Point(x=0.4, y=0.0, z=0.9)),
            GripperPose(time=0.5, position=Point(x=0.5, y=0.15, z=0.88)),
            GripperPose(time=1.0, position=Point(x=0.6, y=0.3, z=0.85)),
            GripperPose(time=1.5, position=Point(x=0.7, y=0.45, z=0.8)),
        ]
    )
    """
    The poses stored, in the order they are inserted.
    """

    @cached_property
    def connection(self) -> sqlite3.Connection:
        """
        The database with the schema created and every pose inserted.
        """
        connection = sqlite3.connect(":memory:")
        connection.executescript(Snippet.POSE_SCHEMA.path.read_text())
        for pose in self.poses:
            position_id = connection.execute(
                "INSERT INTO position (x, y, z) VALUES (?, ?, ?)",
                (pose.position.x, pose.position.y, pose.position.z),
            ).lastrowid
            orientation = pose.orientation
            orientation_id = connection.execute(
                "INSERT INTO quaternion (x, y, z, w) VALUES (?, ?, ?, ?)",
                (orientation.x, orientation.y, orientation.z, orientation.w),
            ).lastrowid
            connection.execute(
                "INSERT INTO pose (time, frame, position_id, orientation_id) "
                "VALUES (?, ?, ?, ?)",
                (pose.time, pose.frame, position_id, orientation_id),
            )
        return connection

    def columns(self, *, table: PoseTable) -> list[TableColumn]:
        """
        :return: The columns of *table*, in the order the schema declares them.
        """
        return [
            TableColumn(name=name, declared_type=declared_type)
            for _, name, declared_type, *_ in self.connection.execute(
                f"PRAGMA table_info({table.value})"
            )
        ]

    def foreign_keys(self) -> list[ForeignKey]:
        """
        :return: Every foreign key of every table.
        """
        return [
            ForeignKey(
                table=table, column=column, referenced_table=PoseTable(referenced)
            )
            for table in PoseTable
            for _, _, referenced, column, *_ in self.connection.execute(
                f"PRAGMA foreign_key_list({table.value})"
            )
        ]

    def joined_rows(self) -> list[tuple[float, str, float, float, float]]:
        """
        :return: The rows :attr:`Snippet.POSE_QUERY` answers: time, frame and position.
        """
        return self.connection.execute(Snippet.POSE_QUERY.path.read_text()).fetchall()

    def stored_rows(self, *, pose_id: int) -> dict[PoseTable, tuple]:
        """
        :return: The rows that together store the pose with id *pose_id*, by table.
        """
        pose = self.connection.execute(
            "SELECT * FROM pose WHERE id = ?", (pose_id,)
        ).fetchone()
        position_id, orientation_id = pose[-2:]
        return {
            PoseTable.POSE: pose,
            PoseTable.POSITION: self.connection.execute(
                "SELECT * FROM position WHERE id = ?", (position_id,)
            ).fetchone(),
            PoseTable.QUATERNION: self.connection.execute(
                "SELECT * FROM quaternion WHERE id = ?", (orientation_id,)
            ).fetchone(),
        }


# %% poses stored with ORMatic


@dataclass(kw_only=True, frozen=True)
class MappedColumn:
    """
    A column of a table ORMatic generated.
    """

    name: str
    """
    The name of the column.
    """

    referenced_table: str | None = None
    """
    The table whose ids the column holds, if it is a foreign key.
    """


@dataclass(kw_only=True, frozen=True)
class MappedTable:
    """
    A table ORMatic generated for a dataclass.
    """

    name: str
    """
    The name of the table.
    """

    columns: list[MappedColumn]
    """
    The columns of the table, in the order they are declared.
    """


@dataclass(kw_only=True)
class PoseStore:
    """
    Poses stored in an in-memory SQLite database through the ORMatic interface of
    :mod:`poses`, and queried with EQL.
    """

    poses: list[GripperPose]
    """
    The poses stored.
    """

    @cached_property
    def engine(self) -> Engine:
        """
        The database with the generated tables created and every pose stored.
        """
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            session.add_all([to_dao(pose) for pose in self.poses])
            session.commit()
        return engine

    def tables(self) -> list[MappedTable]:
        """
        :return: The tables of the generated interface.
        """
        return [
            MappedTable(
                name=table.name,
                columns=[
                    MappedColumn(
                        name=column.name,
                        referenced_table=next(
                            (key.column.table.name for key in column.foreign_keys),
                            None,
                        ),
                    )
                    for column in table.columns
                ],
            )
            for table in Base.metadata.sorted_tables
        ]

    def poses_below(
        self, *, height: float, domain: list[GripperPose]
    ) -> Entity[GripperPose]:
        """
        :return: The query for the poses in *domain* whose gripper is lower than
            *height*; an empty *domain* leaves the poses to the database.
        """
        pose = variable(type_=GripperPose, domain=domain)
        return an(entity(pose).where(pose.position.z < height))

    def stored_poses_below(self, *, height: float) -> list[GripperPose]:
        """
        :return: The answer of :meth:`poses_below` translated to SQL and run on the
            database.
        """
        with Session(self.engine) as session:
            rows = eql_to_sql(
                self.poses_below(height=height, domain=[]), session
            ).evaluate()
            return [row.from_dao() for row in rows]

    def poses_in_memory_below(self, *, height: float) -> list[GripperPose]:
        """
        :return: The answer of :meth:`poses_below` evaluated on the poses in memory.
        """
        return list(self.poses_below(height=height, domain=self.poses).evaluate())

    def sql_of_poses_below(self, *, height: float) -> str:
        """
        :return: The SQL that :meth:`poses_below` translates to, with *height*
            written into it.
        """
        with Session(self.engine) as session:
            statement = eql_to_sql(
                self.poses_below(height=height, domain=[]), session
            ).sql_query
            return str(statement.compile(compile_kwargs={"literal_binds": True}))


# %% response times


@dataclass(kw_only=True)
class ResponseTimes:
    """
    Simulated response times of database queries, drawn from a log-normal distribution.
    """

    query_count: int = 10_000
    """
    The number of simulated queries.
    """

    median_milliseconds: float = 20
    """
    The median of the distribution, in milliseconds.
    """

    spread: float = 0.6
    """
    The standard deviation of the logarithm of the response times.
    """

    seed: int = 0
    """
    The seed of the random number generator, so every build draws the same times.
    """

    @cached_property
    def milliseconds(self) -> np.ndarray:
        """
        The response time of each query, in milliseconds.
        """
        generator = np.random.default_rng(self.seed)
        return generator.lognormal(
            mean=np.log(self.median_milliseconds),
            sigma=self.spread,
            size=self.query_count,
        )

    def percentile(self, *, percent: float) -> float:
        """
        :return: The response time that *percent* percent of the queries stay below.
        """
        return float(np.percentile(self.milliseconds, percent))

    def mean(self) -> float:
        """
        :return: The mean response time, in milliseconds.
        """
        return float(self.milliseconds.mean())

    def slow_request_share(self, *, server_count: int, percent: float = 99) -> float:
        """
        :return: The share of requests that wait for at least one answer slower than
            the *percent* percentile, when each request waits for *server_count*
            independent answers.
        """
        return 1 - (percent / 100) ** server_count

    def render_histogram(self, *, path: Path) -> None:
        """
        Write the histogram of the response times with the mean, the median and the
        95th and 99th percentiles marked to *path*.
        """
        figure = Figure(figsize=(6, 4), dpi=200)
        axes = figure.add_subplot()
        axes.hist(
            self.milliseconds,
            bins=120,
            range=(0, self.percentile(percent=99.9)),
            color=f"#{Color.LIGHT_BLUE.value}",
        )
        markers = [
            ("mean", self.mean(), Color.DARK_GRAY, 0.8),
            ("median", self.percentile(percent=50), Color.BLUE, 1),
            ("95th", self.percentile(percent=95), Color.ALERT, 1),
            ("99th", self.percentile(percent=99), Color.ALERT, 1),
        ]
        for label, value, color, label_height in markers:
            axes.axvline(value, color=f"#{color.value}", linewidth=1.5)
            axes.annotate(
                f"{label}\n{value:.0f} ms",
                xy=(value, label_height),
                xycoords=("data", "axes fraction"),
                xytext=(3, -3),
                textcoords="offset points",
                va="top",
                fontsize=10,
                color=f"#{color.value}",
            )
        axes.set_xlabel("response time (ms)")
        axes.set_ylabel("number of queries")
        axes.spines[["top", "right"]].set_visible(False)
        figure.tight_layout()
        path.parent.mkdir(exist_ok=True)
        figure.savefig(path)


# %% kitchen graph


class Predicate(StrEnum):
    """
    The predicates of the kitchen graph, by local name.
    """

    SUBCLASS_OF = "subClassOf"
    """
    Every member of the subject class is a member of the target class.
    """

    TYPE = "type"
    """
    The subject is a member of the target class.
    """

    LOCATED_ON = "locatedOn"
    """
    The subject stands on the target.
    """


@dataclass(kw_only=True, frozen=True)
class GraphEdge:
    """
    One triple of a graph, with every resource by its local name.
    """

    subject: str
    """
    The node the edge starts at.
    """

    predicate: Predicate
    """
    The label of the edge.
    """

    target: str
    """
    The node the edge ends at.
    """


@dataclass(kw_only=True)
class KitchenGraph:
    """
    The kitchen knowledge graph of :attr:`Snippet.KITCHEN_GRAPH`, queried with SPARQL.
    """

    @cached_property
    def graph(self) -> Graph:
        """
        The triples of the kitchen.
        """
        return Graph().parse(Snippet.KITCHEN_GRAPH.path, format="turtle")

    def containers_on_table(self) -> list[str]:
        """
        :return: The local names of the objects :attr:`Snippet.CONTAINERS_ON_TABLE`
            finds, sorted.
        """
        answers = self.graph.query(Snippet.CONTAINERS_ON_TABLE.path.read_text())
        return sorted(self.local_name(resource=row[0]) for row in answers)

    def edges(self) -> list[GraphEdge]:
        """
        :return: Every triple of the graph as an edge, sorted.
        """
        return sorted(
            (
                GraphEdge(
                    subject=self.local_name(resource=subject),
                    predicate=Predicate(self.local_name(resource=predicate)),
                    target=self.local_name(resource=target),
                )
                for subject, predicate, target in self.graph
            ),
            key=lambda edge: (edge.subject, edge.predicate, edge.target),
        )

    def local_name(self, *, resource: object) -> str:
        """
        :return: The part of *resource*'s IRI after its namespace.
        """
        return str(resource).split("#")[-1]

    def classes(self) -> set[str]:
        """
        :return: The local names of the nodes that are classes rather than individuals.
        """
        edges = self.edges()
        return {
            edge.target
            for edge in edges
            if edge.predicate in (Predicate.TYPE, Predicate.SUBCLASS_OF)
        } | {edge.subject for edge in edges if edge.predicate == Predicate.SUBCLASS_OF}
