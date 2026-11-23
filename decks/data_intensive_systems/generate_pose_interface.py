"""
Generate the ORMatic interface of the pose dataclasses of :mod:`poses`. Run it again
whenever those dataclasses change, and commit the generated module.
"""

from __future__ import annotations

from pathlib import Path

from krrood.class_diagrams.class_diagram import ClassDiagram
from krrood.ormatic.ormatic import ORMatic
from krrood.patterns.path_enumeration import PathEnumeration

from poses import GripperPose, Point, Quaternion

# %% files


class GeneratedModule(PathEnumeration):
    """
    The modules this script generates.
    """

    DIRECTORY = Path(__file__).parent / "orm"
    """
    The directory holding the generated modules.
    """

    POSE_INTERFACE = DIRECTORY / "pose_interface.py"
    """
    The SQLAlchemy data access objects of the pose dataclasses.
    """


# %% command line


def main() -> None:
    """
    Write the SQLAlchemy data access objects of the pose dataclasses.
    """
    ormatic = ORMatic(
        class_dependency_graph=ClassDiagram(classes=[GripperPose, Point, Quaternion])
    )
    ormatic.make_all_tables()
    with GeneratedModule.POSE_INTERFACE.open("w") as file:
        ormatic.to_sqlalchemy_file(file=file)


if __name__ == "__main__":
    main()
