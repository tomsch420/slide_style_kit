"""
Tests of the slide kinds and of how a deck decorates its slides.
"""

from __future__ import annotations

import pytest

from slide_style_kit.components import TodoNote
from slide_style_kit.deck import Deck
from slide_style_kit.elements import Paragraph, TextFrame
from slide_style_kit.geometry import Rectangle
from slide_style_kit.slides import (
    ContentSlide,
    PlainSlide,
    TableOfContentsEntry,
    TableOfContentsSlide,
)
from slide_style_kit.style import Color

# %% table of contents


@pytest.fixture
def entries() -> list[TableOfContentsEntry]:
    """
    Two entries in different sections, the second with two subentries.
    """
    return [
        TableOfContentsEntry(text="One", section="first"),
        TableOfContentsEntry(text="Two", section="second", subentries=["a", "b"]),
    ]


def test_table_of_contents_belongs_to_the_first_section_by_default(
    entries: list[TableOfContentsEntry],
):
    """
    Without a highlighted section, the slide belongs to the first entry's section.
    """
    assert TableOfContentsSlide(entries=entries).section == entries[0].section


def test_table_of_contents_fades_all_but_the_highlighted_section(
    entries: list[TableOfContentsEntry],
):
    """
    Entries outside the highlighted section are faded, subentries included.
    """
    slide = TableOfContentsSlide(entries=entries, highlighted_section="second")
    (frame,) = slide.content(page_size=Deck(title="", author="", slides=[]).page_size)
    assert [paragraph.color for paragraph in frame.paragraphs] == [
        Color.FADED_BLUE,
        Color.BLUE,
        Color.BLUE,
        Color.BLUE,
    ]
    assert slide.section == "second"


# %% notes


def test_todo_adds_a_note_and_leads_the_speaker_notes():
    """
    A to-do shows as a note on top of the slide and opens the speaker notes.
    """
    slide = ContentSlide(todo="fix", notes="say hello")
    page_size = Deck(title="", author="", slides=[]).page_size
    assert isinstance(slide.elements(page_size=page_size)[-1], TodoNote)
    assert slide.speaker_notes() == "TODO: fix\n\nsay hello"


# %% decoration


def test_only_decorated_slides_get_title_bar_and_footer():
    """
    A plain slide shows only its content; a content slide gets the decoration under it.
    """
    content = TextFrame(
        area=Rectangle(left=1, top=2, width=3, height=1),
        paragraphs=[Paragraph(text="content")],
    )
    decorated = ContentSlide(items=[content])
    plain = PlainSlide(items=[content])
    deck = Deck(title="", author="", slides=[decorated, plain], sections=["s"])
    assert deck.page_elements(slide=plain, page_number=2) == [content]
    decorated_elements = deck.page_elements(slide=decorated, page_number=1)
    assert decorated_elements[-1] is content
    assert len(decorated_elements) > 1


def test_footer_highlights_the_slides_section():
    """
    The footer shows the slide's section in blue and the others in grey.
    """
    deck = Deck(title="", author="", slides=[], sections=["a", "b"])
    navigation = deck.decoration.navigation(sections=deck.sections, active_section="b")
    assert [frame.paragraphs[0].color for frame in navigation] == [
        Color.GRAY,
        Color.BLUE,
    ]
