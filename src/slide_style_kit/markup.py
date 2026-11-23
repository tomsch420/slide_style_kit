"""
The inline markup of slide text.

A span ``{x:text}`` styles *text* by the letter ``x`` (see :class:`MarkupStyle`); spans
do not nest, and the styled text cannot contain a closing brace.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum

from krrood.patterns.classproperty import classproperty

from slide_style_kit.style import Color, Typeface

# %% styled text


@dataclass(kw_only=True, frozen=True)
class TextRun:
    """
    A stretch of text in one style.
    """

    text: str
    """
    The characters of the run.
    """

    color: str
    """
    The text colour as hexadecimal RGB, usually a :class:`~slide_style_kit.style.Color`.
    """

    bold: bool = False
    """
    Whether the run is set in bold.
    """

    italic: bool = False
    """
    Whether the run is set in italics.
    """

    typeface: Typeface = Typeface.SANS_SERIF
    """
    The typeface the run is set in.
    """


class MarkupStyle(StrEnum):
    """
    The styles of a markup span, by the letter that opens it.
    """

    ALERT = "a"
    """
    Alert red.
    """

    BOLD = "b"
    """
    Bold.
    """

    ITALIC = "i"
    """
    Italics.
    """

    MONOSPACE = "m"
    """
    Monospaced, for code.
    """

    STRUCTURE = "s"
    """
    Bold in the structure blue.
    """

    SYMBOL = "y"
    """
    The symbol typeface, for glyphs the sans-serif face lacks.
    """

    TODO = "t"
    """
    Bold in the to-do orange.
    """

    CODE_KEYWORD = "k"
    """
    Monospaced in the keyword colour.
    """

    CODE_STRING = "l"
    """
    Monospaced in the string colour.
    """

    CODE_COMMENT = "c"
    """
    Monospaced italics in the comment colour.
    """

    CODE_NUMBER = "n"
    """
    Monospaced in the number colour.
    """

    CODE_NAME = "f"
    """
    Monospaced in the colour of built-in and function names.
    """

    def apply(self, *, run: TextRun) -> TextRun:
        """
        :param run: The run as the surrounding text styles it.
        :return: The run in this style.
        """
        match self:
            case MarkupStyle.ALERT:
                return replace(run, color=Color.ALERT)
            case MarkupStyle.BOLD:
                return replace(run, bold=True)
            case MarkupStyle.ITALIC:
                return replace(run, italic=True)
            case MarkupStyle.MONOSPACE:
                return replace(run, typeface=Typeface.MONOSPACE)
            case MarkupStyle.STRUCTURE:
                return replace(run, color=Color.BLUE, bold=True)
            case MarkupStyle.SYMBOL:
                return replace(run, typeface=Typeface.SYMBOL)
            case MarkupStyle.TODO:
                return replace(run, color=Color.TODO, bold=True)
            case MarkupStyle.CODE_KEYWORD:
                return replace(
                    run, color=Color.CODE_KEYWORD, typeface=Typeface.MONOSPACE
                )
            case MarkupStyle.CODE_STRING:
                return replace(
                    run, color=Color.CODE_STRING, typeface=Typeface.MONOSPACE
                )
            case MarkupStyle.CODE_COMMENT:
                return replace(
                    run,
                    color=Color.CODE_COMMENT,
                    italic=True,
                    typeface=Typeface.MONOSPACE,
                )
            case MarkupStyle.CODE_NUMBER:
                return replace(
                    run, color=Color.CODE_NUMBER, typeface=Typeface.MONOSPACE
                )
            case MarkupStyle.CODE_NAME:
                return replace(run, color=Color.CODE_NAME, typeface=Typeface.MONOSPACE)


# %% parsing


@dataclass(kw_only=True, frozen=True)
class Markup:
    """
    A string of markup with the style of the text around its spans.
    """

    text: str
    """
    The markup.
    """

    color: str = Color.BLACK
    """
    The colour of the text outside colouring spans, as hexadecimal RGB.
    """

    bold: bool = False
    """
    Whether all of the text is set in bold.
    """

    @classproperty
    def span_pattern(cls) -> re.Pattern[str]:
        """
        The pattern of one span: its style letter and its text.
        """
        return re.compile(rf"\{{([{''.join(MarkupStyle)}]):(.*?)\}}")

    def runs(self) -> list[TextRun]:
        """
        :return: The text split into runs, in order.
        """
        surrounding_style = TextRun(text="", color=self.color, bold=self.bold)
        runs = []
        position = 0
        for span in Markup.span_pattern.finditer(self.text):
            if span.start() > position:
                plain_text = self.text[position : span.start()]
                runs.append(replace(surrounding_style, text=plain_text))
            styled = replace(surrounding_style, text=span.group(2))
            runs.append(MarkupStyle(span.group(1)).apply(run=styled))
            position = span.end()
        if position < len(self.text):
            runs.append(replace(surrounding_style, text=self.text[position:]))
        return runs
