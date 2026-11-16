"""
The interface every output format implements.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from slide_style_kit.deck import Deck
    from slide_style_kit.elements import (
        Arrow,
        Box,
        Formula,
        Picture,
        Table,
        TextFrame,
        Video,
    )
    from slide_style_kit.slides import Slide

# %% renderer interface


@dataclass(kw_only=True)
class Renderer(ABC):
    """
    Writes a deck to a file of one format.
    """

    deck: Deck
    """
    The deck to write.
    """

    path: Path
    """
    The file to write.
    """

    def render(self) -> None:
        """
        Draw every slide of the deck and write the file.
        """
        for page_number, slide in enumerate(self.deck.slides, start=1):
            self.start_slide(slide=slide)
            for element in self.deck.page_elements(
                slide=slide, page_number=page_number
            ):
                element.draw(renderer=self)
            self.finish_slide(slide=slide)
        self.save()

    @abstractmethod
    def start_slide(self, *, slide: Slide) -> None:
        """
        Begin a new, empty page that the following drawing goes to.
        """

    @abstractmethod
    def finish_slide(self, *, slide: Slide) -> None:
        """
        Complete the current page after every element of *slide* is drawn.
        """

    @abstractmethod
    def save(self) -> None:
        """
        Write the drawn pages to :attr:`path`.
        """

    @abstractmethod
    def draw_text_frame(self, *, text_frame: TextFrame) -> None:
        """
        Draw *text_frame* on the current page.
        """

    @abstractmethod
    def draw_picture(self, *, picture: Picture) -> None:
        """
        Draw *picture* on the current page.
        """

    @abstractmethod
    def draw_video(self, *, video: Video) -> None:
        """
        Draw *video* on the current page, as a video where the format can play one.
        """

    @abstractmethod
    def draw_formula(self, *, formula: Formula) -> None:
        """
        Draw *formula* in its :meth:`Formula.displayed_area`.
        """

    @abstractmethod
    def draw_box(self, *, box: Box) -> None:
        """
        Draw *box* on the current page.
        """

    @abstractmethod
    def draw_arrow(self, *, arrow: Arrow) -> None:
        """
        Draw *arrow* on the current page.
        """

    @abstractmethod
    def draw_table(self, *, table: Table) -> None:
        """
        Draw *table* on the current page.
        """
