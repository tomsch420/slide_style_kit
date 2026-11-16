"""
A deck of slides and the title bar and footer its slides share.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from slide_style_kit.assets import Asset
from slide_style_kit.elements import Arrow, Element, Paragraph, Picture, TextFrame
from slide_style_kit.geometry import Position, Rectangle, Size
from slide_style_kit.slides import Slide
from slide_style_kit.style import Color, VerticalAnchor

# %% page decoration


@dataclass(kw_only=True)
class PageDecoration:
    """
    The title bar and the footer of a slide: a rule, the page number, the section
    navigation and the logo.
    """

    title_area: Rectangle = Rectangle(left=0.45, top=0.22, width=12.4, height=0.65)
    """
    The area of the slide title.
    """

    title_font_size: float = 28
    """
    The font size of the slide title, in points.
    """

    footer_rule_top: float = 6.97
    """
    The distance of the footer rule from the top of the slide, in inch.
    """

    footer_rule_width: float = 1.5
    """
    The width of the footer rule, in points.
    """

    footer_font_size: float = 11
    """
    The font size of the page number and the section navigation, in points.
    """

    page_number_area: Rectangle = Rectangle(left=0.3, top=7.08, width=0.5, height=0.3)
    """
    The area of the page number.
    """

    first_section_area: Rectangle = Rectangle(
        left=0.85, top=7.08, width=1.7, height=0.3
    )
    """
    The area of the first section of the navigation.
    """

    section_spacing: float = 1.72
    """
    The distance between the left edges of two neighbouring sections, in inch.
    """

    logo: Path = Asset.UNIVERSITY_OF_BREMEN_LOGO
    """
    The logo at the right end of the footer.
    """

    logo_position: Position = Position(x=11.45, y=7.03)
    """
    The top left corner of the logo.
    """

    logo_width: float = 1.1
    """
    The width of the logo, in inch.
    """

    def elements(
        self,
        *,
        slide: Slide,
        page_number: int,
        sections: list[str],
        page_size: Size,
    ) -> list[Element]:
        """
        :param slide: The slide being decorated.
        :param page_number: The number of the slide in the deck, starting at 1.
        :param sections: The sections of the footer navigation.
        :param page_size: The size of the page.
        :return: The title, the footer rule, page number, navigation and logo.
        """
        title = Paragraph(text=slide.title, space_after=0, color=Color.BLUE)
        page_number_paragraph = Paragraph(text=f"{{s:{page_number}}}", space_after=0)
        return [
            TextFrame(
                area=self.title_area,
                paragraphs=[title],
                font_size=self.title_font_size,
                anchor=VerticalAnchor.MIDDLE,
            ),
            Arrow(
                start=Position(x=0, y=self.footer_rule_top),
                end=Position(x=page_size.width, y=self.footer_rule_top),
                color=Color.BLUE,
                line_width=self.footer_rule_width,
                has_head=False,
            ),
            TextFrame(
                area=self.page_number_area,
                paragraphs=[page_number_paragraph],
                font_size=self.footer_font_size,
            ),
            *self.navigation(sections=sections, active_section=slide.section),
            Picture(path=self.logo, position=self.logo_position, width=self.logo_width),
        ]

    def navigation(
        self, *, sections: list[str], active_section: str | None
    ) -> list[TextFrame]:
        """
        :return: The section names side by side, the active one in the structure blue.
        """
        area = self.first_section_area
        return [
            TextFrame(
                area=Rectangle(
                    left=area.left + index * self.section_spacing,
                    top=area.top,
                    width=area.width,
                    height=area.height,
                ),
                paragraphs=[
                    Paragraph(
                        text=section,
                        space_after=0,
                        color=Color.BLUE if section == active_section else Color.GRAY,
                    )
                ],
                font_size=self.footer_font_size,
            )
            for index, section in enumerate(sections)
        ]


# %% deck


@dataclass(kw_only=True)
class Deck:
    """
    A presentation: its slides, the sections they are grouped into and its metadata.
    """

    title: str
    """
    The title stored in the file's metadata.
    """

    author: str
    """
    The author stored in the file's metadata.
    """

    slides: list[Slide]
    """
    The slides, in order.
    """

    sections: list[str] = field(default_factory=list)
    """
    The sections listed in the footer navigation; about six fit.
    """

    page_size: Size = Size(width=13.333, height=7.5)
    """
    The size of every page, in inch; the default is 16:9.
    """

    decoration: PageDecoration = field(default_factory=PageDecoration)
    """
    The title bar and footer of the slides that have them.
    """

    def page_elements(self, *, slide: Slide, page_number: int) -> list[Element]:
        """
        :param slide: A slide of this deck.
        :param page_number: The number of *slide* in the deck, starting at 1.
        :return: Everything drawn on the page of *slide*, in drawing order.
        """
        content = slide.elements(page_size=self.page_size)
        if not slide.has_page_decoration:
            return content
        decoration = self.decoration.elements(
            slide=slide,
            page_number=page_number,
            sections=self.sections,
            page_size=self.page_size,
        )
        return [*decoration, *content]
