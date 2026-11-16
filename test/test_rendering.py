"""
Tests of writing a deck to PowerPoint and PDF.
"""

from __future__ import annotations

import re
from pathlib import Path
from urllib.request import url2pathname

import pytest
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from slide_style_kit.deck import Deck
from slide_style_kit.exceptions import MissingFontFile
from slide_style_kit.fonts import FontFiles
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer

# %% PowerPoint


def test_power_point_has_one_slide_per_slide_and_keeps_the_notes(
    deck: Deck, tmp_path: Path
):
    """
    The PowerPoint file has a slide per slide, the deck title and the notes.
    """
    deck.slides[1].notes = "remember this"
    path = tmp_path / "deck.pptx"
    PowerPointRenderer(deck=deck, path=path).render()
    presentation = Presentation(path)
    assert len(presentation.slides) == len(deck.slides)
    assert presentation.core_properties.title == deck.title
    notes = presentation.slides[1].notes_slide.notes_text_frame.text
    assert notes == deck.slides[1].speaker_notes()


def test_power_point_embeds_videos(video_deck: Deck, tmp_path: Path):
    """
    A video becomes a media shape holding the video file itself.
    """
    path = tmp_path / "deck.pptx"
    PowerPointRenderer(deck=video_deck, path=path).render()
    presentation = Presentation(path)
    (shape,) = presentation.slides[0].shapes
    assert shape.shape_type == MSO_SHAPE_TYPE.MEDIA
    videos = [
        part.blob
        for part in presentation.part.package.iter_parts()
        if part.content_type == "video/mp4"
    ]
    (video,) = video_deck.slides[0].items
    assert videos == [video.movie.read_bytes()]


# %% PDF


def test_pdf_has_one_page_per_slide(deck: Deck, tmp_path: Path):
    """
    The PDF file has a page per slide.
    """
    renderer = PDFRenderer(deck=deck, path=tmp_path / "deck.pdf")
    renderer.render()
    assert renderer.path.is_file()
    assert renderer.canvas.getPageNumber() - 1 == len(deck.slides)


def test_a_missing_font_file_is_reported(deck: Deck, tmp_path: Path):
    """
    A font directory without the font files fails before anything is drawn.
    """
    fonts = FontFiles(liberation_directory=tmp_path)
    with pytest.raises(MissingFontFile):
        PDFRenderer(deck=deck, path=tmp_path / "deck.pdf", font_files=fonts)


def test_pdf_shows_the_poster_of_a_video(video_deck: Deck, tmp_path: Path):
    """
    A PDF cannot play a video, so the page shows its poster image instead.
    """
    renderer = PDFRenderer(deck=video_deck, path=tmp_path / "deck.pdf")
    renderer.render()
    assert renderer.path.read_bytes().count(b"/Subtype /Image") == 1


def test_pdf_poster_links_to_the_video(video_deck: Deck, tmp_path: Path):
    """
    Clicking the poster opens the video, through a link relative to the PDF.
    """
    renderer = PDFRenderer(deck=video_deck, path=tmp_path / "slides" / "deck.pdf")
    renderer.path.parent.mkdir()
    renderer.render()
    (link,) = re.findall(rb"/URI \((.*?)\)", renderer.path.read_bytes())
    (video,) = video_deck.slides[0].items
    linked = renderer.path.parent / url2pathname(link.decode())
    assert linked.resolve() == video.movie.resolve()
