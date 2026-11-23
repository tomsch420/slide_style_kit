"""
The poses of the kitchen robot's gripper as plain dataclasses: the domain model that
the pose database stores by hand and ORMatic maps to tables.
"""

from __future__ import annotations

from dataclasses import dataclass

# %% poses


@dataclass(kw_only=True, frozen=True)
class Point:
    """
    A point in space, in metres.
    """

    x: float
    """
    The coordinate along the first axis.
    """

    y: float
    """
    The coordinate along the second axis.
    """

    z: float
    """
    The coordinate along the third axis.
    """


@dataclass(kw_only=True, frozen=True)
class Quaternion:
    """
    An orientation as a unit quaternion.
    """

    x: float = 0
    """
    The first imaginary component.
    """

    y: float = 0
    """
    The second imaginary component.
    """

    z: float = 0
    """
    The third imaginary component.
    """

    w: float = 1
    """
    The real component.
    """


@dataclass(kw_only=True, frozen=True)
class GripperPose:
    """
    Where the gripper was at one moment.
    """

    time: float
    """
    The time since the start of the episode, in seconds.
    """

    position: Point
    """
    The position of the gripper.
    """

    orientation: Quaternion = Quaternion()
    """
    The orientation of the gripper.
    """

    frame: str = "map"
    """
    The coordinate frame the pose is given in.
    """
