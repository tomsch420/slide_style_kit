@dataclass
class Point:
    x: float
    y: float
    z: float


@dataclass
class GripperPose:
    time: float
    position: Point
    orientation: Quaternion = Quaternion()
    frame: str = "map"
