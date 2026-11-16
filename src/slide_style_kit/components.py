"""
The recurring building blocks of the lecture slides: diagram nodes, labels, captions,
take-away lines, code blocks, matrices and to-do notes.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from pathlib import Path

from krrood.ormatic.utils import classproperty
from pygments.lexers import get_lexer_by_name, get_lexer_for_filename
from pygments.token import Comment, Keyword, Name, Number, Operator, String, _TokenType

from slide_style_kit.elements import (
    Arrow,
    Box,
    CompositeElement,
    Element,
    Paragraph,
    TextFrame,
)
from slide_style_kit.geometry import Length, Position, Rectangle, Size
from slide_style_kit.markup import MarkupStyle
from slide_style_kit.style import Alignment, Color, VerticalAnchor

# %% diagrams


@dataclass(kw_only=True)
class DiagramNode(Box):
    """
    A node of a diagram: a rounded box with centred text.
    """

    rounded: bool = True
    """
    Whether the corners are rounded.
    """

    font_size: float = 15
    """
    The font size of the text, in points.
    """


@dataclass(kw_only=True)
class Label(CompositeElement):
    """
    A single line of small grey text, such as the name of a diagram arrow.
    """

    area: Rectangle
    """
    The area the text is set into.
    """

    text: str
    """
    The markup of the label.
    """

    font_size: float = 12
    """
    The font size, in points.
    """

    color: str = Color.LABEL_GRAY
    """
    The text colour, as hexadecimal RGB.
    """

    alignment: Alignment = Alignment.CENTER
    """
    The horizontal alignment.
    """

    anchor: VerticalAnchor = VerticalAnchor.MIDDLE
    """
    Where the text sits in the area.
    """

    def parts(self) -> list[Element]:
        paragraph = Paragraph(
            text=self.text, space_after=0, color=self.color, alignment=self.alignment
        )
        return [
            TextFrame(
                area=self.area,
                paragraphs=[paragraph],
                font_size=self.font_size,
                anchor=self.anchor,
            )
        ]


@dataclass(kw_only=True)
class Caption(Label):
    """
    A caption under a figure, such as the source of an image.
    """

    font_size: float = 10
    """
    The font size, in points.
    """

    color: str = Color.DARK_GRAY
    """
    The text colour, as hexadecimal RGB.
    """

    anchor: VerticalAnchor = VerticalAnchor.TOP
    """
    Where the text sits in the area.
    """


# %% text blocks


@dataclass(kw_only=True)
class TakeAway(CompositeElement):
    """
    The closing line of a slide, led by a squiggly arrow.
    """

    text: str
    """
    The markup of the line.
    """

    area: Rectangle = Rectangle(left=0.45, top=6.3, width=12.4, height=0.5)
    """
    The area the line is set into.
    """

    font_size: float = 18
    """
    The font size, in points.
    """

    def parts(self) -> list[Element]:
        paragraph = Paragraph(text=f"{{y:\u21dd}} {self.text}", space_after=0)
        return [
            TextFrame(area=self.area, paragraphs=[paragraph], font_size=self.font_size)
        ]


@dataclass(kw_only=True)
class CodeBlock(CompositeElement):
    """
    Source code in a grey box, highlighted, keeping the indentation of its lines.

    .. warning:: The code is set as markup, so it cannot contain a closing brace.
    """

    area: Rectangle
    """
    The area of the grey box.
    """

    source_code: str
    """
    The code; leading and trailing blank lines are dropped.
    """

    language: str = "python"
    """
    The Pygments name of the code's language, such as ``python`` or ``prolog``.
    """

    font_size: float = 12
    """
    The font size, in points.
    """

    blank_line_height: float = 0.9
    """
    The space a blank line adds below the line before it, in font sizes.
    """

    horizontal_padding: float = 0.15
    """
    The distance in inch between the code and the left and right edge of the box.
    """

    vertical_padding: float = 0.1
    """
    The distance in inch between the code and the top and bottom edge of the box.
    """

    @classproperty
    def character_width_in_ems(cls) -> float:
        """
        The advance width of one monospaced character, in font sizes.
        """
        return 0.6

    @classmethod
    def from_file(
        cls, *, area: Rectangle, path: Path, font_size: float = 12
    ) -> CodeBlock:
        """
        :param area: The area of the grey box.
        :param path: The file holding the code.
        :param font_size: The font size, in points.
        :return: A code block showing the file's content.
        """
        return cls(
            area=area,
            source_code=path.read_text(),
            language=get_lexer_for_filename(path.name).aliases[0],
            font_size=font_size,
        )

    def token_style(self, *, token_type: _TokenType) -> MarkupStyle:
        """
        :return: The markup style a token of *token_type* is highlighted with.
        """
        if token_type in Keyword or token_type in Operator.Word:
            return MarkupStyle.CODE_KEYWORD
        if token_type in String:
            return MarkupStyle.CODE_STRING
        if token_type in Comment:
            return MarkupStyle.CODE_COMMENT
        if token_type in Number:
            return MarkupStyle.CODE_NUMBER
        if token_type in Name.Builtin or token_type in Name.Function:
            return MarkupStyle.CODE_NAME
        return MarkupStyle.MONOSPACE

    def highlighted_lines(self) -> list[list[tuple[MarkupStyle, str]]]:
        """
        :return: Every line of the code as its highlighted pieces, in order.
        """
        lexer = get_lexer_by_name(self.language)
        lines: list[list[tuple[MarkupStyle, str]]] = [[]]
        for token_type, text in lexer.get_tokens(self.source_code.strip("\n")):
            style = self.token_style(token_type=token_type)
            for index, piece in enumerate(text.split("\n")):
                if index > 0:
                    lines.append([])
                if not piece:
                    continue
                if lines[-1] and lines[-1][-1][0] == style:
                    piece = lines[-1].pop()[1] + piece
                lines[-1].append((style, piece))
        if not lines[-1]:
            lines.pop()
        return lines

    def code_paragraphs(self) -> list[Paragraph]:
        """
        :return: One highlighted monospaced paragraph per non-blank line, indented
            like the line.
        """
        character_width_per_point = (
            CodeBlock.character_width_in_ems / Length.points_per_inch
        )
        paragraphs = []
        for pieces in self.highlighted_lines():
            line = "".join(piece for _, piece in pieces)
            body = line.lstrip(" ")
            if not body:
                paragraphs[-1] = replace(
                    paragraphs[-1],
                    space_after=self.font_size * self.blank_line_height,
                )
                continue
            indentation = (
                (len(line) - len(body)) * character_width_per_point * self.font_size
            )
            leading = len(line) - len(body)
            spans = []
            for style, piece in pieces:
                kept = piece[leading:]
                leading = max(leading - len(piece), 0)
                if kept:
                    spans.append(f"{{{style.value}:{kept}}}")
            paragraphs.append(
                Paragraph(text="".join(spans), space_after=1, indent=indentation)
            )
        return paragraphs

    def parts(self) -> list[Element]:
        background = Box(
            area=self.area,
            fill=Color.CODE_BACKGROUND,
            outline=Color.CODE_BORDER,
            outline_width=0.75,
            rounded=True,
            corner_radius=0.04,
        )
        code_area = self.area.inset(
            horizontal=self.horizontal_padding, vertical=self.vertical_padding
        )
        code = TextFrame(
            area=code_area, paragraphs=self.code_paragraphs(), font_size=self.font_size
        )
        return [background, code]


# %% matrices


@dataclass(kw_only=True)
class Matrix(CompositeElement):
    """
    A matrix or vector of markup entries between square brackets.
    """

    position: Position
    """
    The top left corner of the left bracket.
    """

    entries: list[list[str]]
    """
    The markup of each entry, row by row; every row has the same length.
    """

    column_width: float = 0.5
    """
    The width of every column, in inch.
    """

    row_height: float = 0.32
    """
    The height of every row, in inch.
    """

    font_size: float = 16
    """
    The font size of the entries, in points.
    """

    bracket_gap: float = 0.06
    """
    The distance between a bracket and the entries, in inch.
    """

    bracket_serif: float = 0.07
    """
    The length of the short horizontal strokes at the ends of a bracket, in inch.
    """

    line_width: float = 1
    """
    The width of the bracket lines, in points.
    """

    color: str = Color.BLACK
    """
    The colour of the brackets and of the entries outside colouring spans.
    """

    @property
    def size(self) -> Size:
        """
        The extent of the matrix from the left to the right bracket.
        """
        column_count = len(self.entries[0])
        return Size(
            width=column_count * self.column_width + 2 * self.bracket_gap,
            height=len(self.entries) * self.row_height,
        )

    def bracket_lines(self, *, x: float, serif_direction: int) -> list[Arrow]:
        """
        :param x: The horizontal position of the bracket's vertical stroke.
        :param serif_direction: 1 for a left bracket, whose serifs point right; -1 for
            a right bracket.
        :return: The vertical stroke and the two serifs of one bracket.
        """
        top, bottom = self.position.y, self.position.y + self.size.height
        serif_end = x + serif_direction * self.bracket_serif
        return [
            Arrow(
                start=Position(x=start_x, y=start_y),
                end=Position(x=end_x, y=end_y),
                color=self.color,
                line_width=self.line_width,
                has_head=False,
            )
            for start_x, start_y, end_x, end_y in (
                (x, top, x, bottom),
                (x, top, serif_end, top),
                (x, bottom, serif_end, bottom),
            )
        ]

    def parts(self) -> list[Element]:
        entries_left = self.position.x + self.bracket_gap
        cells = [
            TextFrame(
                area=Rectangle(
                    left=entries_left + column_index * self.column_width,
                    top=self.position.y + row_index * self.row_height,
                    width=self.column_width,
                    height=self.row_height,
                ),
                paragraphs=[
                    Paragraph(
                        text=entry,
                        space_after=0,
                        color=self.color,
                        alignment=Alignment.CENTER,
                    )
                ],
                font_size=self.font_size,
                anchor=VerticalAnchor.MIDDLE,
            )
            for row_index, row in enumerate(self.entries)
            for column_index, entry in enumerate(row)
        ]
        right = self.position.x + self.size.width
        return [
            *self.bracket_lines(x=self.position.x, serif_direction=1),
            *self.bracket_lines(x=right, serif_direction=-1),
            *cells,
        ]


# %% notes


@dataclass(kw_only=True)
class TodoNote(CompositeElement):
    """
    A sticky note in the top right corner listing what is still to be done on a slide.
    """

    text: str
    """
    The markup of the note.
    """

    position: Position = Position(x=8.35, y=0.12)
    """
    The top left corner of the note.
    """

    width: float = 4.8
    """
    The width of the note, in inch.
    """

    characters_per_line: int = 52
    """
    The number of characters assumed to fit on one line, to size the note.
    """

    line_height: float = 0.2
    """
    The height of one line of text, in inch.
    """

    padding: float = 0.11
    """
    The space in inch the note adds above and below its lines of text.
    """

    horizontal_text_margin: float = 0.1
    """
    The distance in inch between the text frame and the left and right edge.
    """

    vertical_text_margin: float = 0.05
    """
    The distance in inch between the text frame and the top and bottom edge.
    """

    font_size: float = 12
    """
    The font size, in points.
    """

    @property
    def area(self) -> Rectangle:
        """
        The area of the note, tall enough for its text.
        """
        lines = max(1, math.ceil(len(self.text) / self.characters_per_line))
        return Rectangle(
            left=self.position.x,
            top=self.position.y,
            width=self.width,
            height=self.line_height * lines + 2 * self.padding,
        )

    def parts(self) -> list[Element]:
        area = self.area
        note = Box(
            area=area,
            fill=Color.TODO_FILL,
            outline=Color.TODO,
            outline_width=0.75,
        )
        text_area = area.inset(
            horizontal=self.horizontal_text_margin,
            vertical=self.vertical_text_margin,
        )
        paragraph = Paragraph(text=f"{{t:TODO:}} {self.text}", space_after=0)
        text = TextFrame(
            area=text_area, paragraphs=[paragraph], font_size=self.font_size
        )
        return [note, text]
