"""
Positions, sizes and areas on a slide.

Every coordinate is in inch, measured from the top left corner of the slide.
"""

from __future__ import annotations

from dataclasses import dataclass

from krrood.ormatic.utils import classproperty

# %% lengths


@dataclass(kw_only=True, frozen=True)
class Length:
    """
    A length on the slide, convertible between inch and typographic points.
    """

    inches: float
    """
    The length in inch.
    """

    @classproperty
    def points_per_inch(cls) -> int:
        """
        The number of typographic points in one inch.
        """
        return 72

    @property
    def points(self) -> float:
        """
        The length in typographic points.
        """
        return self.inches * Length.points_per_inch


# %% positions and areas


@dataclass(kw_only=True, frozen=True)
class Position:
    """
    A point on the slide.
    """

    x: float
    """
    The distance from the left edge of the slide.
    """

    y: float
    """
    The distance from the top edge of the slide.
    """


@dataclass(kw_only=True, frozen=True)
class Size:
    """
    The extent of something on the slide.
    """

    width: float
    """
    The horizontal extent.
    """

    height: float
    """
    The vertical extent.
    """


@dataclass(kw_only=True, frozen=True)
class Rectangle:
    """
    An axis-aligned area on the slide.
    """

    left: float
    """
    The distance of the left edge from the left edge of the slide.
    """

    top: float
    """
    The distance of the top edge from the top edge of the slide.
    """

    width: float
    """
    The horizontal extent.
    """

    height: float
    """
    The vertical extent.
    """

    @property
    def bottom(self) -> float:
        """
        The distance of the bottom edge from the top edge of the slide.
        """
        return self.top + self.height

    @property
    def center(self) -> Position:
        """
        The point in the middle of the area.
        """
        return Position(x=self.left + self.width / 2, y=self.top + self.height / 2)

    def inset(self, *, horizontal: float, vertical: float) -> Rectangle:
        """
        :param horizontal: The margin taken off the left and the right edge each.
        :param vertical: The margin taken off the top and the bottom edge each.
        :return: The area that remains inside those margins.
        """
        return Rectangle(
            left=self.left + horizontal,
            top=self.top + vertical,
            width=self.width - 2 * horizontal,
            height=self.height - 2 * vertical,
        )

    def transposed(self) -> Rectangle:
        """
        :return: The area with width and height swapped, around the same center.
        """
        center = self.center
        return Rectangle(
            left=center.x - self.height / 2,
            top=center.y - self.width / 2,
            width=self.height,
            height=self.width,
        )
