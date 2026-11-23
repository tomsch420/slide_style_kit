"""
The kinds of slides a lecture deck is made of.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path

from krrood.patterns.classproperty import classproperty

from slide_style_kit.assets import Asset
from slide_style_kit.components import TakeAway, TodoNote
from slide_style_kit.elements import Box, Element, Paragraph, Picture, TextFrame
from slide_style_kit.geometry import Position, Rectangle, Size
from slide_style_kit.style import Alignment, Color, VerticalAnchor

# %% slide interface


@dataclass(kw_only=True)
class Slide(ABC):
    """
    One page of a deck.
    """

    title: str = ""
    """
    The markup of the title.
    """

    section: str | None = None
    """
    The section of the deck the slide belongs to, highlighted in the footer navigation.
    """

    notes: str = ""
    """
    The speaker notes.
    """

    todo: str = ""
    """
    What is still to be done on the slide, shown as a note on it and in the speaker
    notes.
    """

    @classproperty
    def has_page_decoration(cls) -> bool:
        """
        Whether the slide gets the title bar and the footer.
        """
        return True

    @abstractmethod
    def content(self, *, page_size: Size) -> list[Element]:
        """
        :param page_size: The size of the page the slide is drawn on.
        :return: The elements of the slide besides the title bar, footer and to-do note.
        """

    def elements(self, *, page_size: Size) -> list[Element]:
        """
        :param page_size: The size of the page the slide is drawn on.
        :return: The content followed by the to-do note, if there is one.
        """
        if not self.todo:
            return self.content(page_size=page_size)
        return [*self.content(page_size=page_size), TodoNote(text=self.todo)]

    def speaker_notes(self) -> str:
        """
        :return: The to-do text followed by the notes, separated by a blank line.
        """
        todo = f"TODO: {self.todo}" if self.todo else ""
        return "\n\n".join(text for text in (todo, self.notes) if text)


# %% free-form slides


@dataclass(kw_only=True)
class ContentSlide(Slide):
    """
    A slide with a title bar, a footer and arbitrary elements.
    """

    items: list[Element] = field(default_factory=list)
    """
    The elements, in drawing order.
    """

    def content(self, *, page_size: Size) -> list[Element]:
        return self.items


@dataclass(kw_only=True)
class PlainSlide(ContentSlide):
    """
    A slide of arbitrary elements without title bar and footer.
    """

    @classproperty
    def has_page_decoration(cls) -> bool:
        """
        Unlike :meth:`Slide.has_page_decoration`, without title bar and footer.
        """
        return False


# %% title slide


@dataclass(kw_only=True)
class Person:
    """
    Someone named on the title slide.
    """

    name: str
    """
    The full name, with any title.
    """

    role: str | None = None
    """
    The role in the lecture, such as ``lecturer``, shown below the name.
    """


@dataclass(kw_only=True)
class TitleSlideLayout:
    """
    Where the parts of a title slide go.
    """

    band_height: float = 1.15
    """
    The height of the light blue band holding the logos, in inch.
    """

    university_logo_position: Position = Position(x=4.03, y=0.27)
    """
    The top left corner of the University of Bremen logo.
    """

    university_logo_height: float = 0.62
    """
    The height of the University of Bremen logo, in inch.
    """

    institute_logo_position: Position = Position(x=6.56, y=0.235)
    """
    The top left corner of the AICOR logo.
    """

    institute_logo_height: float = 0.68
    """
    The height of the AICOR logo, in inch.
    """

    course_top: float = 1.45
    """
    The top of the course line, in inch.
    """

    course_height: float = 0.6
    """
    The height of the course line, in inch.
    """

    course_font_size: float = 24
    """
    The font size of the course line, in points.
    """

    title_bar_top: float = 2.3
    """
    The top of the blue bar holding the title, in inch.
    """

    title_bar_height: float = 0.82
    """
    The height of the blue bar holding the title, in inch.
    """

    title_font_size: float = 26
    """
    The font size of the title, in points.
    """

    people_area: Rectangle = Rectangle(left=3.5, top=3.4, width=6.3, height=2.8)
    """
    The area holding the people, the place and the date.
    """

    name_font_size: float = 16
    """
    The font size of the names, the place and the date, in points.
    """

    role_font_size: float = 14
    """
    The font size of the roles, in points.
    """

    image_position: Position = Position(x=0.9, y=3.55)
    """
    The top left corner of the image.
    """


@dataclass(kw_only=True)
class TitleSlide(Slide):
    """
    The opening slide: logo band, course line, title bar, people, place and date.
    """

    course: str
    """
    The markup of the course name, shown above the title.
    """

    people: list[Person]
    """
    The people giving the lecture, in the order they are listed.
    """

    place: str
    """
    The place of the lecture.
    """

    date: str
    """
    The date of the lecture.
    """

    image: Path | None = None
    """
    A picture drawn bottom left, such as :attr:`Asset.ROBOT_SKETCH`.
    """

    image_height: float = 3.1
    """
    The height of the picture, in inch.
    """

    layout: TitleSlideLayout = field(default_factory=TitleSlideLayout)
    """
    Where the parts of the slide go.
    """

    @classproperty
    def has_page_decoration(cls) -> bool:
        """
        Unlike :meth:`Slide.has_page_decoration`, without title bar and footer.
        """
        return False

    def people_paragraphs(self) -> list[Paragraph]:
        """
        :return: The names and roles of the people, then the place and the date.
        """
        paragraphs = []
        for index, person in enumerate(self.people):
            space_below_person = 22 if index == len(self.people) - 1 else 14
            paragraphs.append(
                self.centered_paragraph(
                    text=f"{{b:{person.name}}}",
                    space_after=4 if person.role else space_below_person,
                    font_size=self.layout.name_font_size,
                )
            )
            if person.role:
                paragraphs.append(
                    self.centered_paragraph(
                        text=person.role,
                        space_after=space_below_person,
                        font_size=self.layout.role_font_size,
                    )
                )
        paragraphs.append(
            self.centered_paragraph(
                text=self.place, space_after=6, font_size=self.layout.name_font_size
            )
        )
        paragraphs.append(
            self.centered_paragraph(
                text=self.date, space_after=0, font_size=self.layout.name_font_size
            )
        )
        return paragraphs

    def centered_paragraph(
        self, *, text: str, space_after: float, font_size: float
    ) -> Paragraph:
        """
        :return: A centred paragraph in the structure blue.
        """
        return Paragraph(
            text=text,
            space_after=space_after,
            color=Color.BLUE,
            font_size=font_size,
            alignment=Alignment.CENTER,
        )

    def content(self, *, page_size: Size) -> list[Element]:
        layout = self.layout
        course = self.centered_paragraph(
            text=f"{{b:{self.course}}}",
            space_after=0,
            font_size=layout.course_font_size,
        )
        elements = [
            Box(
                area=Rectangle(
                    left=0, top=0, width=page_size.width, height=layout.band_height
                ),
                fill=Color.LIGHT_BLUE,
                outline=None,
            ),
            Picture(
                path=Asset.UNIVERSITY_OF_BREMEN_LOGO,
                position=layout.university_logo_position,
                height=layout.university_logo_height,
            ),
            Picture(
                path=Asset.AICOR_LOGO,
                position=layout.institute_logo_position,
                height=layout.institute_logo_height,
            ),
            TextFrame(
                area=Rectangle(
                    left=0,
                    top=layout.course_top,
                    width=page_size.width,
                    height=layout.course_height,
                ),
                paragraphs=[course],
                font_size=layout.course_font_size,
                anchor=VerticalAnchor.MIDDLE,
            ),
            Box(
                area=Rectangle(
                    left=0,
                    top=layout.title_bar_top,
                    width=page_size.width,
                    height=layout.title_bar_height,
                ),
                text=self.title,
                fill=Color.BLUE,
                outline=None,
                rounded=True,
                font_size=layout.title_font_size,
                text_color=Color.WHITE,
            ),
            TextFrame(
                area=layout.people_area,
                paragraphs=self.people_paragraphs(),
                font_size=layout.name_font_size,
            ),
        ]
        if self.image is not None:
            elements.append(
                Picture(
                    path=self.image,
                    position=layout.image_position,
                    height=self.image_height,
                )
            )
        return elements


# %% table of contents


@dataclass(kw_only=True)
class TableOfContentsEntry:
    """
    One entry of a table of contents.
    """

    text: str
    """
    The markup shown for the entry.
    """

    section: str
    """
    The section of the footer navigation the entry belongs to.
    """

    subentries: list[str] = field(default_factory=list)
    """
    The markup of the entries listed below this one, indented.
    """


@dataclass(kw_only=True)
class TableOfContentsSlide(Slide):
    """
    A table of contents in which every section but the highlighted one is faded.

    Without a :attr:`section`, the slide belongs to the highlighted section, or to the
    first entry's when none is highlighted.
    """

    entries: list[TableOfContentsEntry]
    """
    The entries, top to bottom.
    """

    highlighted_section: str | None = None
    """
    The section whose entries are not faded, or ``None`` to fade none.
    """

    title: str = "Table of Contents"
    """
    The markup of the title.
    """

    area: Rectangle = Rectangle(left=0.9, top=1.3, width=10, height=5.4)
    """
    The area the entries are set into.
    """

    font_size: float = 22
    """
    The font size of the entries, in points.
    """

    subentry_font_size: float = 18
    """
    The font size of the subentries, in points.
    """

    subentry_indent: float = 0.42
    """
    How far the subentries are indented, in inch.
    """

    space_between_entries: float = 16
    """
    The space below an entry and its subentries, in points.
    """

    space_between_subentries: float = 4
    """
    The space below an entry followed by subentries, and between subentries, in points.
    """

    def __post_init__(self) -> None:
        """
        Assign the slide to its section in the footer navigation if none is given.
        """
        if self.section is None:
            self.section = self.highlighted_section or self.entries[0].section

    def entry_paragraphs(self, *, entry: TableOfContentsEntry) -> list[Paragraph]:
        """
        :return: The paragraph of *entry* followed by those of its subentries.
        """
        is_highlighted = self.highlighted_section in (None, entry.section)
        color = Color.BLUE if is_highlighted else Color.FADED_BLUE
        heading = Paragraph(
            text=entry.text,
            space_after=self.space_between_subentries
            if entry.subentries
            else self.space_between_entries,
            color=color,
        )
        subentries = [
            Paragraph(
                text=text,
                space_after=self.space_between_entries
                if index == len(entry.subentries) - 1
                else self.space_between_subentries,
                color=color,
                font_size=self.subentry_font_size,
                indent=self.subentry_indent,
            )
            for index, text in enumerate(entry.subentries)
        ]
        return [heading, *subentries]

    def content(self, *, page_size: Size) -> list[Element]:
        paragraphs = [
            paragraph
            for entry in self.entries
            for paragraph in self.entry_paragraphs(entry=entry)
        ]
        return [
            TextFrame(area=self.area, paragraphs=paragraphs, font_size=self.font_size)
        ]


# %% section divider


@dataclass(kw_only=True)
class SectionDividerSlide(Slide):
    """
    A divider between sections: one underlined heading in the middle of the slide.
    """

    heading: str
    """
    The markup of the heading.
    """

    heading_top: float = 3.2
    """
    The top of the heading, in inch.
    """

    heading_height: float = 0.8
    """
    The height of the heading, in inch.
    """

    font_size: float = 26
    """
    The font size of the heading, in points.
    """

    def content(self, *, page_size: Size) -> list[Element]:
        heading = Paragraph(
            text=self.heading,
            space_after=0,
            color=Color.SLATE,
            bold=True,
            alignment=Alignment.CENTER,
        )
        return [
            TextFrame(
                area=Rectangle(
                    left=0,
                    top=self.heading_top,
                    width=page_size.width,
                    height=self.heading_height,
                ),
                paragraphs=[heading],
                font_size=self.font_size,
                anchor=VerticalAnchor.MIDDLE,
                underline=True,
            )
        ]


# %% bullet slides


@dataclass(kw_only=True)
class BulletSlide(Slide):
    """
    The standard slide: paragraphs, further elements and an optional take-away line.
    """

    paragraphs: list[Paragraph] = field(default_factory=list)
    """
    The paragraphs of the text, usually made with :meth:`Paragraph.bullet_points`.
    """

    items: list[Element] = field(default_factory=list)
    """
    Further elements, such as a diagram next to the text.
    """

    take_away: str | None = None
    """
    The markup of the closing line, or ``None`` for no closing line.
    """

    text_area: Rectangle = Rectangle(left=0.45, top=1.2, width=12.4, height=5.0)
    """
    The area the paragraphs are set into.
    """

    font_size: float = 20
    """
    The font size of the paragraphs, in points.
    """

    def content(self, *, page_size: Size) -> list[Element]:
        elements = [
            TextFrame(
                area=self.text_area,
                paragraphs=self.paragraphs,
                font_size=self.font_size,
            ),
            *self.items,
        ]
        if self.take_away is not None:
            elements.append(TakeAway(text=self.take_away))
        return elements


@dataclass(kw_only=True)
class Column:
    """
    One column of a comparison: a heading over bullet points.
    """

    heading: str
    """
    The markup of the heading, set in bold.
    """

    points: list[str | Paragraph]
    """
    The bullet points, as markup or as paragraphs.
    """


@dataclass(kw_only=True)
class ComparisonSlide(Slide):
    """
    Two columns of bullet points side by side, each under a bold heading.
    """

    left: Column
    """
    The left column.
    """

    right: Column
    """
    The right column.
    """

    font_size: float = 18
    """
    The font size of the bullet points, in points.
    """

    heading_font_size: float = 20
    """
    The font size of the headings, in points.
    """

    left_heading_area: Rectangle = Rectangle(
        left=0.45, top=1.75, width=5.9, height=0.45
    )
    """
    The area of the left heading.
    """

    left_points_area: Rectangle = Rectangle(left=0.6, top=2.3, width=5.75, height=4.3)
    """
    The area of the left bullet points.
    """

    right_heading_area: Rectangle = Rectangle(
        left=6.75, top=1.75, width=6.1, height=0.45
    )
    """
    The area of the right heading.
    """

    right_points_area: Rectangle = Rectangle(left=6.9, top=2.3, width=6.0, height=4.3)
    """
    The area of the right bullet points.
    """

    def column_elements(
        self, *, column: Column, heading_area: Rectangle, points_area: Rectangle
    ) -> list[Element]:
        """
        :return: The heading and the bullet points of *column* in the given areas.
        """
        heading = Paragraph(text=column.heading, space_after=0, bold=True)
        return [
            TextFrame(
                area=heading_area,
                paragraphs=[heading],
                font_size=self.heading_font_size,
            ),
            TextFrame(
                area=points_area,
                paragraphs=Paragraph.bullet_points(texts=column.points),
                font_size=self.font_size,
            ),
        ]

    def content(self, *, page_size: Size) -> list[Element]:
        return [
            *self.column_elements(
                column=self.left,
                heading_area=self.left_heading_area,
                points_area=self.left_points_area,
            ),
            *self.column_elements(
                column=self.right,
                heading_area=self.right_heading_area,
                points_area=self.right_points_area,
            ),
        ]
