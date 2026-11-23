"""
The colours, typefaces, bullets and alignments of the Uni Bremen lecture look.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, IntEnum, StrEnum

from krrood.patterns.classproperty import classproperty

from slide_style_kit.geometry import Length

# %% colours


class Color(StrEnum):
    """
    The palette, as hexadecimal RGB values without a leading ``#``.
    """

    BLACK = "000000"
    """
    Body text, outlines and table rules.
    """

    WHITE = "FFFFFF"
    """
    The page background and the default fill of boxes.
    """

    BLUE = "144F78"
    """
    The structure colour: titles, level-one bullets, the title bar and the footer rule.
    """

    LIGHT_BLUE = "ABDBF4"
    """
    The logo band of the title slide.
    """

    FADED_BLUE = "B4C6D6"
    """
    The entries of the inactive sections in a table of contents.
    """

    ALERT = "8C021F"
    """
    Alerted text.
    """

    TODO = "C2410C"
    """
    The text and outline of a to-do note.
    """

    TODO_FILL = "FFF1B8"
    """
    The fill of a to-do note.
    """

    GRAY = "6B6B6B"
    """
    The inactive sections in the footer navigation.
    """

    DARK_GRAY = "555555"
    """
    Diagram arrows and captions.
    """

    LABEL_GRAY = "444444"
    """
    Diagram labels.
    """

    SLATE = "44546A"
    """
    The heading of a section divider slide.
    """

    CODE_BACKGROUND = "F3F3F3"
    """
    The fill of a code block.
    """

    CODE_BORDER = "C8C8C8"
    """
    The outline of a code block.
    """

    CODE_KEYWORD = "0033B3"
    """
    Keywords and keyword constants in code.
    """

    CODE_STRING = "067D17"
    """
    String literals in code.
    """

    CODE_COMMENT = "8C8C8C"
    """
    Comments in code.
    """

    CODE_NUMBER = "1750EB"
    """
    Number literals in code.
    """

    CODE_NAME = "00627A"
    """
    Built-in and function names in code.
    """

    PALE_GREEN = "DDF0D8"
    """
    A fill for boxes and diagram nodes.
    """

    PALE_PINK = "F6DCE0"
    """
    A fill for boxes and diagram nodes.
    """

    PALE_BLUE = "DCE7F3"
    """
    A fill for boxes and diagram nodes.
    """

    PALE_YELLOW = "FFF4CC"
    """
    A fill for boxes and diagram nodes.
    """

    PALE_PURPLE = "EADCF0"
    """
    A fill for boxes and diagram nodes.
    """


# %% typefaces


@dataclass(frozen=True)
class FontNames:
    """
    The names one typeface has in each output format.
    """

    power_point: str
    """
    The font a PowerPoint file names.
    """

    pdf: str
    """
    The font family a PDF embeds, metric compatible with :attr:`power_point`.
    """


class Typeface(FontNames, Enum):
    """
    The typefaces text is set in.
    """

    SANS_SERIF = "Arial", "LiberationSans"
    """
    Body text.
    """

    MONOSPACE = "Courier New", "LiberationMono"
    """
    Code.
    """

    SYMBOL = "Cambria Math", "DejaVuSans"
    """
    Mathematical symbols and arrows that the sans-serif face lacks.
    """


# %% alignment


class Alignment(StrEnum):
    """
    The horizontal alignment of a paragraph or a table column.
    """

    LEFT = "left"
    """
    Flush with the left edge.
    """

    CENTER = "center"
    """
    Centred between the edges.
    """

    RIGHT = "right"
    """
    Flush with the right edge.
    """


class VerticalAnchor(StrEnum):
    """
    Where the text of a frame sits when it is shorter than the frame.
    """

    TOP = "top"
    """
    At the top edge.
    """

    MIDDLE = "middle"
    """
    Centred between the top and the bottom edge.
    """

    BOTTOM = "bottom"
    """
    At the bottom edge.
    """


class Rotation(IntEnum):
    """
    The rotation of a box, in degrees clockwise.
    """

    NONE = 0
    """
    Upright.
    """

    READING_UPWARD = 270
    """
    Text that reads from bottom to top.
    """


# %% bullets


@dataclass(kw_only=True, frozen=True)
class BulletOffsets:
    """
    The horizontal offsets of a bulleted paragraph from the left edge of its frame.
    """

    bullet: float
    """
    The offset of the bullet character, in inch.
    """

    text: float
    """
    The offset of the text, in inch.
    """


@dataclass(frozen=True)
class BulletStyle:
    """
    How the bullet of one nesting depth looks.
    """

    depth: int
    """
    The nesting depth, starting at zero for the outermost level.
    """

    character: str
    """
    The bullet character.
    """

    color: Color
    """
    The colour of the bullet character.
    """

    relative_size: float
    """
    The size of the bullet character as a fraction of the font size of the text.
    """


class BulletLevel(BulletStyle, Enum):
    """
    The nesting levels of bulleted paragraphs.
    """

    FIRST = 0, "▶", Color.BLUE, 0.6
    """
    The outermost level, with a blue triangle.
    """

    SECOND = 1, "–", Color.BLACK, 1.0
    """
    The second level, with an en dash.
    """

    THIRD = 2, "•", Color.BLACK, 1.0
    """
    The third level, with a round bullet.
    """

    @classproperty
    def indentation_step_in_ems(cls) -> float:
        """
        How far each level is indented further than the one above it, in font sizes.
        """
        return 1.25

    def offsets(self, *, font_size: float) -> BulletOffsets:
        """
        :param font_size: The font size of the paragraph, in points.
        :return: Where the bullet and the text of a paragraph at this level start.
        """
        step = font_size / Length.points_per_inch * BulletLevel.indentation_step_in_ems
        return BulletOffsets(bullet=self.depth * step, text=(self.depth + 1) * step)
