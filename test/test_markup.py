"""
Tests of parsing the inline markup into styled runs.
"""

from __future__ import annotations

from slide_style_kit.markup import Markup, TextRun
from slide_style_kit.style import Color, Typeface

# %% spans


def test_plain_text_is_one_run_in_the_surrounding_style():
    """
    Text without spans keeps the surrounding colour in a single run.
    """
    markup = Markup(text="plain", color=Color.BLUE)
    assert markup.runs() == [TextRun(text="plain", color=Color.BLUE)]


def test_spans_split_the_text_into_styled_runs():
    """
    Each span becomes its own run between the plain runs around it.
    """
    markup = Markup(text="a {b:bold} and {m:code}!")
    assert markup.runs() == [
        TextRun(text="a ", color=Color.BLACK),
        TextRun(text="bold", color=Color.BLACK, bold=True),
        TextRun(text=" and ", color=Color.BLACK),
        TextRun(text="code", color=Color.BLACK, typeface=Typeface.MONOSPACE),
        TextRun(text="!", color=Color.BLACK),
    ]


def test_colouring_spans_override_the_surrounding_colour():
    """
    Alert, structure and to-do spans replace the surrounding colour.
    """
    markup = Markup(text="{a:alert}{s:structure}{t:todo}", color=Color.GRAY)
    assert [(run.color, run.bold) for run in markup.runs()] == [
        (Color.ALERT, False),
        (Color.BLUE, True),
        (Color.TODO, True),
    ]


def test_bold_markup_makes_every_run_bold():
    """
    Bold markup applies to plain runs and to spans alike.
    """
    markup = Markup(text="x {i:y}", bold=True)
    assert all(run.bold for run in markup.runs())


def test_unknown_style_letters_stay_literal_text():
    """
    Braces with a letter that is no style are kept as they are.
    """
    markup = Markup(text="{q:not a span}")
    assert markup.runs() == [TextRun(text="{q:not a span}", color=Color.BLACK)]


def test_doubled_closing_brace_is_a_literal_brace_inside_a_span():
    """
    Inside a span, ``}}`` stands for one closing brace and does not end the span.
    """
    markup = Markup(text="{m:x}}}!")
    assert markup.runs() == [
        TextRun(text="x}", color=Color.BLACK, typeface=Typeface.MONOSPACE),
        TextRun(text="!", color=Color.BLACK),
    ]
