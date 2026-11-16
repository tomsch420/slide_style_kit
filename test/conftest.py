"""
Fixtures shared by the tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from krrood.patterns.path_enumeration import PathEnumeration

from slide_style_kit.deck import Deck
from slide_style_kit.elements import Video
from slide_style_kit.example import example_deck
from slide_style_kit.geometry import Position
from slide_style_kit.slides import PlainSlide

# %% resources


class Resource(PathEnumeration):
    """
    The files the tests read.
    """

    DIRECTORY = Path(__file__).parent / "resources"
    """
    The directory holding the other resources.
    """

    BLUE_SQUARE_VIDEO = DIRECTORY / "blue_square.mp4"
    """
    A one-second video of a blue square moving right.
    """

    BLUE_SQUARE_POSTER = DIRECTORY / "blue_square.png"
    """
    The last frame of :attr:`BLUE_SQUARE_VIDEO`.
    """


# %% decks


@pytest.fixture
def deck() -> Deck:
    """
    The example deck, which uses every kind of slide and element.
    """
    return example_deck()


@pytest.fixture
def video_deck() -> Deck:
    """
    A deck with one undecorated slide showing one video.
    """
    video = Video(
        path=Resource.BLUE_SQUARE_POSTER,
        movie=Resource.BLUE_SQUARE_VIDEO,
        position=Position(x=1, y=1.5),
        width=4,
    )
    return Deck(title="video", author="test", slides=[PlainSlide(items=[video])])
