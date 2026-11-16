"""
The elements a slide is made of: text frames, pictures, videos, formulas, boxes, arrows
and tables.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import cached_property
from pathlib import Path

from PIL import Image
from typing_extensions import TYPE_CHECKING

from slide_style_kit.exceptions import UnsizedPicture
from slide_style_kit.formulas import FormulaTypesetter, TypesetFormula
from slide_style_kit.geometry import Position, Rectangle, Size
from slide_style_kit.markup import Markup
from slide_style_kit.style import (
    Alignment,
    BulletLevel,
    Color,
    Rotation,
    VerticalAnchor,
)

if TYPE_CHECKING:
    from slide_style_kit.renderer import Renderer

# %% element interface


@dataclass(kw_only=True)
class Element(ABC):
    """
    Something drawn on a slide.
    """

    @abstractmethod
    def draw(self, *, renderer: Renderer) -> None:
        """
        Draw this element on the slide *renderer* is currently drawing.
        """


@dataclass(kw_only=True)
class CompositeElement(Element, ABC):
    """
    An element made of other elements.
    """

    @abstractmethod
    def parts(self) -> list[Element]:
        """
        :return: The elements this one is made of, in drawing order.
        """

    def draw(self, *, renderer: Renderer) -> None:
        for part in self.parts():
            part.draw(renderer=renderer)


# %% text


@dataclass(kw_only=True)
class Paragraph:
    """
    A paragraph of markup text, with or without a bullet.
    """

    text: str
    """
    The markup of the paragraph (see :mod:`slide_style_kit.markup`).
    """

    level: BulletLevel | None = None
    """
    The bullet level, or ``None`` for a paragraph without a bullet.
    """

    space_after: float = 6
    """
    The space below the paragraph, in points.
    """

    color: str = Color.BLACK
    """
    The text colour outside colouring spans, as hexadecimal RGB.
    """

    bold: bool = False
    """
    Whether all of the text is set in bold.
    """

    font_size: float | None = None
    """
    The font size in points, or ``None`` for the font size of the enclosing element.
    """

    alignment: Alignment = Alignment.LEFT
    """
    The horizontal alignment.
    """

    indent: float = 0
    """
    The left indent in inch of a paragraph without a bullet.
    """

    line_spacing: float = 1.2
    """
    The distance between the baselines of two lines, in font sizes.
    """

    @property
    def markup(self) -> Markup:
        """
        The text with the style it is set in.
        """
        return Markup(text=self.text, color=self.color, bold=self.bold)

    @classmethod
    def bullet_points(
        cls,
        *,
        texts: list[str | Paragraph],
        level: BulletLevel = BulletLevel.FIRST,
        space_after: float = 8,
    ) -> list[Paragraph]:
        """
        :param texts: The markup of each bullet point; paragraphs are kept as they are.
        :param level: The bullet level of the points given as markup.
        :param space_after: The space below each point given as markup, in points.
        :return: One paragraph per entry of *texts*.
        """
        return [
            cls(text=text, level=level, space_after=space_after)
            if isinstance(text, str)
            else text
            for text in texts
        ]


@dataclass(kw_only=True)
class TextFrame(Element):
    """
    Paragraphs set into an area, wrapped at its width.
    """

    area: Rectangle
    """
    The area the text is set into; text taller than it overflows at the bottom.
    """

    paragraphs: list[Paragraph]
    """
    The paragraphs, top to bottom.
    """

    font_size: float = 20
    """
    The font size in points of paragraphs that do not set their own.
    """

    anchor: VerticalAnchor = VerticalAnchor.TOP
    """
    Where text shorter than the area sits.
    """

    underline: bool = False
    """
    Whether all of the text is underlined.
    """

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_text_frame(text_frame=self)


# %% pictures


@dataclass(kw_only=True)
class Picture(Element):
    """
    An image file drawn at its aspect ratio unless both width and height are given.
    """

    path: Path
    """
    The image file.
    """

    position: Position
    """
    The top left corner of the picture.
    """

    width: float | None = None
    """
    The width in inch, or ``None`` to derive it from the height.
    """

    height: float | None = None
    """
    The height in inch, or ``None`` to derive it from the width.
    """

    def __post_init__(self) -> None:
        """
        :raises UnsizedPicture: If neither :attr:`width` nor :attr:`height` is given.
        """
        if self.width is None and self.height is None:
            raise UnsizedPicture(path=self.path)

    def displayed_size(self) -> Size:
        """
        :return: The size the picture is drawn at.
        """
        if self.width is not None and self.height is not None:
            return Size(width=self.width, height=self.height)
        with Image.open(self.path) as image:
            pixel_width, pixel_height = image.size
        if self.width is not None:
            return Size(
                width=self.width, height=self.width * pixel_height / pixel_width
            )
        return Size(width=self.height * pixel_width / pixel_height, height=self.height)

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_picture(picture=self)


@dataclass(kw_only=True)
class Video(Picture):
    """
    A video, shown at the size of its poster image :attr:`path`.

    Formats that cannot play video, such as PDF, show the poster image instead.
    """

    movie: Path
    """
    The MP4 file of the video.
    """

    def draw(self, *, renderer: Renderer) -> None:
        """
        Unlike :meth:`Picture.draw`, draw the video where the format can play it.
        """
        renderer.draw_video(video=self)


# %% shapes


@dataclass(kw_only=True)
class Formula(Element):
    """
    A formula typeset with LaTeX, scaled to its font size and placed in an area.
    """

    latex: str
    """
    The formula as LaTeX math, without dollar signs.
    """

    area: Rectangle
    """
    The area the formula is aligned in; a formula too large for it is scaled down.
    """

    font_size: float = 20
    """
    The font size the formula is set at, in points.
    """

    color: Color = Color.BLACK
    """
    The colour of the formula.
    """

    alignment: Alignment = Alignment.CENTER
    """
    The horizontal alignment in :attr:`area`; vertically, the formula is centred.
    """

    typesetter: FormulaTypesetter = field(default_factory=FormulaTypesetter)
    """
    The typesetter that renders the formula.
    """

    @cached_property
    def typeset_formula(self) -> TypesetFormula:
        """
        The formula rendered to image files.
        """
        return self.typesetter.typeset(latex=self.latex, color=self.color)

    def displayed_area(self) -> Rectangle:
        """
        :return: The area the formula is drawn in.
        """
        natural_size = self.typeset_formula.natural_size
        scale = min(
            self.font_size / TypesetFormula.natural_font_size,
            self.area.width / natural_size.width,
            self.area.height / natural_size.height,
        )
        width, height = natural_size.width * scale, natural_size.height * scale
        match self.alignment:
            case Alignment.LEFT:
                left = self.area.left
            case Alignment.CENTER:
                left = self.area.left + (self.area.width - width) / 2
            case Alignment.RIGHT:
                left = self.area.left + self.area.width - width
        return Rectangle(
            left=left,
            top=self.area.top + (self.area.height - height) / 2,
            width=width,
            height=height,
        )

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_formula(formula=self)


@dataclass(kw_only=True)
class Box(Element):
    """
    A rectangle, square-cornered or rounded, with optional centred text.
    """

    area: Rectangle
    """
    The area of the box as it appears on the slide, after any rotation.
    """

    text: str = ""
    """
    The markup of the text; each line break starts a new centred line.
    """

    fill: str | None = Color.WHITE
    """
    The fill colour as hexadecimal RGB, or ``None`` for a transparent box.
    """

    outline: str | None = Color.BLACK
    """
    The outline colour as hexadecimal RGB, or ``None`` for no outline.
    """

    outline_width: float = 1
    """
    The width of the outline, in points.
    """

    rounded: bool = False
    """
    Whether the corners are rounded.
    """

    corner_radius: float = 0.18
    """
    The radius of rounded corners, as a fraction of the shorter side.
    """

    font_size: float = 16
    """
    The font size of the text, in points.
    """

    text_color: str = Color.BLACK
    """
    The colour of the text outside colouring spans, as hexadecimal RGB.
    """

    bold: bool = False
    """
    Whether all of the text is set in bold.
    """

    line_spacing: float = 1.15
    """
    The distance between the baselines of two lines of text, in font sizes.
    """

    text_margin: float = 0.03
    """
    The distance in inch between the text and the edges of the box.
    """

    rotation: Rotation = Rotation.NONE
    """
    The rotation of the box and its text.
    """

    @property
    def unrotated_area(self) -> Rectangle:
        """
        The area of the box before rotation, around the same center as :attr:`area`.
        """
        if self.rotation == Rotation.NONE:
            return self.area
        return self.area.transposed()

    def paragraphs(self) -> list[Paragraph]:
        """
        :return: One centred paragraph per line of :attr:`text`.
        """
        return [
            Paragraph(
                text=line,
                space_after=0,
                color=self.text_color,
                bold=self.bold,
                font_size=self.font_size,
                alignment=Alignment.CENTER,
                line_spacing=self.line_spacing,
            )
            for line in self.text.split("\n")
        ]

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_box(box=self)


@dataclass(kw_only=True)
class Arrow(Element):
    """
    A straight line, with an arrowhead at its end unless turned off.
    """

    start: Position
    """
    Where the line starts.
    """

    end: Position
    """
    Where the line ends, at the tip of the arrowhead.
    """

    color: str = Color.BLACK
    """
    The line colour as hexadecimal RGB.
    """

    line_width: float = 1.5
    """
    The line width, in points.
    """

    dashed: bool = False
    """
    Whether the line is dotted instead of solid.
    """

    has_head: bool = True
    """
    Whether an arrowhead is drawn at :attr:`end`.
    """

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_arrow(arrow=self)


# %% tables


@dataclass(kw_only=True)
class Table(Element):
    """
    A table in booktabs style: thick rules above and below, a thin rule under the
    header.
    """

    position: Position
    """
    The top left corner of the table.
    """

    column_widths: list[float]
    """
    The width of each column, in inch.
    """

    rows: list[list[str]]
    """
    The markup of each cell, row by row; the first row is the header and set in bold.
    """

    row_height: float = 0.3
    """
    The height of every row, in inch.
    """

    font_size: float = 14
    """
    The font size of the cells, in points.
    """

    column_alignments: list[Alignment] | None = None
    """
    The alignment of each column, or ``None`` to align every column left.
    """

    cell_padding: float = 0.08
    """
    The distance in inch between the text of a cell and its left and right edges.
    """

    outer_rule_width: float = 1.5
    """
    The width of the rules above and below the table, in points.
    """

    header_rule_width: float = 0.75
    """
    The width of the rule under the header, in points.
    """

    def cell_area(self, *, row_index: int, column_index: int) -> Rectangle:
        """
        :return: The area of the cell in row *row_index* and column *column_index*.
        """
        return Rectangle(
            left=self.position.x + sum(self.column_widths[:column_index]),
            top=self.position.y + row_index * self.row_height,
            width=self.column_widths[column_index],
            height=self.row_height,
        )

    def cell_paragraph(self, *, row_index: int, column_index: int) -> Paragraph:
        """
        :return: The paragraph in row *row_index* and column *column_index*.
        """
        alignments = self.column_alignments or [Alignment.LEFT] * len(
            self.column_widths
        )
        return Paragraph(
            text=self.rows[row_index][column_index],
            space_after=0,
            bold=row_index == 0,
            font_size=self.font_size,
            alignment=alignments[column_index],
        )

    def rule_width(self, *, boundary: int) -> float:
        """
        :param boundary: The index of a row boundary: 0 above the first row, 1 below it.
        :return: The width in points of the rule along the boundary, 0 for none.
        """
        if boundary in (0, len(self.rows)):
            return self.outer_rule_width
        if boundary == 1:
            return self.header_rule_width
        return 0

    def draw(self, *, renderer: Renderer) -> None:
        renderer.draw_table(table=self)
