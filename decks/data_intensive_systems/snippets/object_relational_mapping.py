class Position(Base):
    x: Mapped[float]
    y: Mapped[float]
    z: Mapped[float]


class Quaternion(Base):
    x: Mapped[float]
    y: Mapped[float]
    z: Mapped[float]
    w: Mapped[float]


class Pose(PositionMixin, QuaternionMixin, Base):
    time: Mapped[datetime.datetime]
    frame: Mapped[str]
