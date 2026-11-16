"""
An example deck using every building block; copy it to start a new deck.

Run ``python -m slide_style_kit.example`` to write ``example.pptx`` and ``example.pdf``
into the current directory.
"""

from __future__ import annotations

from pathlib import Path

from slide_style_kit.assets import Asset
from slide_style_kit.components import Caption, CodeBlock, DiagramNode, Label
from slide_style_kit.deck import Deck
from slide_style_kit.elements import Arrow, Box, Paragraph, Table
from slide_style_kit.geometry import Position, Rectangle
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer
from slide_style_kit.slides import (
    BulletSlide,
    Column,
    ComparisonSlide,
    Person,
    SectionDividerSlide,
    TableOfContentsEntry,
    TableOfContentsSlide,
    TitleSlide,
)
from slide_style_kit.style import BulletLevel, Color

# %% example deck


def example_deck() -> Deck:
    """
    :return: A deck with a slide for each kind of slide and element.
    """
    contents = [
        TableOfContentsEntry(text="What This Is About", section="Introduction"),
        TableOfContentsEntry(
            text="Methods", section="Methods", subentries=["Diagrams", "Code"]
        ),
        TableOfContentsEntry(text="Summary", section="Summary"),
    ]
    slides = [
        TitleSlide(
            course="Advanced Methods of AI (WiSe 2026/2027)",
            title="Lecture Title",
            people=[
                Person(name="Prof. Michael Beetz", role="lecturer"),
                Person(name="Your Name"),
            ],
            place="Bremen, Germany",
            date="1st of January 2027",
            image=Asset.ROBOT_SKETCH,
        ),
        TableOfContentsSlide(entries=contents),
        BulletSlide(
            title="A Standard Bullet Slide",
            section="Introduction",
            paragraphs=[
                *Paragraph.bullet_points(
                    texts=[
                        "Plain text, {b:bold}, {i:italic}, {a:alert red} and "
                        "{s:structure blue}",
                        "Inline code: {m:hasTopping some Cheese}, symbols: "
                        "{y:\u2200x \u2203y \u2192 \u2293}",
                        Paragraph(
                            text="Sub-bullets:", level=BulletLevel.FIRST, space_after=4
                        ),
                    ]
                ),
                *Paragraph.bullet_points(
                    texts=["second level", "another one"],
                    level=BulletLevel.SECOND,
                    space_after=4,
                ),
                Paragraph(text="Third level", level=BulletLevel.THIRD, space_after=8),
            ],
            take_away="every slide can end with a take-away line",
        ),
        ComparisonSlide(
            title="Two Columns",
            section="Introduction",
            left=Column(heading="Left heading", points=["one", "two"]),
            right=Column(heading="Right heading", points=["three", "four"]),
        ),
        TableOfContentsSlide(entries=contents, highlighted_section="Methods"),
        SectionDividerSlide(heading="Diagrams", section="Methods"),
        BulletSlide(
            title="Diagram Elements",
            section="Methods",
            paragraphs=Paragraph.bullet_points(texts=["Nodes, arrows and labels"]),
            items=[
                DiagramNode(
                    area=Rectangle(left=1.0, top=2.5, width=2.4, height=0.8),
                    text="Perception",
                    fill=Color.PALE_BLUE,
                ),
                DiagramNode(
                    area=Rectangle(left=5.0, top=2.5, width=2.4, height=0.8),
                    text="Reasoning",
                    fill=Color.PALE_YELLOW,
                    bold=True,
                ),
                DiagramNode(
                    area=Rectangle(left=9.0, top=2.5, width=2.4, height=0.8),
                    text="Action",
                    fill=Color.PALE_GREEN,
                ),
                Arrow(
                    start=Position(x=3.4, y=2.9),
                    end=Position(x=5.0, y=2.9),
                    color=Color.DARK_GRAY,
                ),
                Arrow(
                    start=Position(x=7.4, y=2.9),
                    end=Position(x=9.0, y=2.9),
                    color=Color.DARK_GRAY,
                    dashed=True,
                ),
                Label(
                    area=Rectangle(left=3.4, top=2.45, width=1.6, height=0.3),
                    text="percepts",
                ),
                Box(
                    area=Rectangle(left=1.0, top=4.0, width=10.4, height=0.7),
                    text="a plain box with {a:markup}",
                ),
                Box(
                    area=Rectangle(left=1.0, top=5.0, width=10.4, height=0.7),
                    text="a filled rounded box",
                    fill=Color.BLUE,
                    outline=None,
                    rounded=True,
                    text_color=Color.WHITE,
                ),
                Caption(
                    area=Rectangle(left=1.0, top=5.8, width=10.4, height=0.3),
                    text="Source: a small grey caption",
                ),
            ],
        ),
        BulletSlide(
            title="Code and Tables",
            section="Methods",
            items=[
                CodeBlock.from_file(
                    area=Rectangle(left=0.45, top=1.3, width=6.0, height=2.2),
                    path=Asset.EXAMPLE_CODE,
                ),
                Table(
                    position=Position(x=6.9, y=1.3),
                    column_widths=[2.0, 3.8],
                    rows=[
                        ["Header", "Another header"],
                        ["row 1", "{m:mono} cell"],
                        ["row 2", "{a:alert} cell"],
                    ],
                    row_height=0.4,
                    font_size=15,
                ),
            ],
            take_away="tables get booktabs-style rules: thick top/bottom, thin under "
            "the header",
        ),
        BulletSlide(
            title="Summary",
            section="Summary",
            paragraphs=Paragraph.bullet_points(texts=["Done."]),
        ),
    ]
    return Deck(
        title="Example deck",
        author="Your Name",
        slides=slides,
        sections=["Introduction", "Methods", "Summary"],
    )


# %% command line


def main() -> None:
    """
    Write the example deck to ``example.pptx`` and ``example.pdf``.
    """
    deck = example_deck()
    PowerPointRenderer(deck=deck, path=Path("example.pptx")).render()
    PDFRenderer(deck=deck, path=Path("example.pdf")).render()
    print(f"{len(deck.slides)} slides -> example.pptx / example.pdf")


if __name__ == "__main__":
    main()
