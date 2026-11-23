"""
Tests of the geometry, bullet indentation and element layout.
"""

from __future__ import annotations

import pytest

from slide_style_kit.assets import Asset
from slide_style_kit.components import CodeBlock, Matrix, TodoNote
from slide_style_kit.elements import Box, Picture, Table
from slide_style_kit.exceptions import UnsizedPicture
from slide_style_kit.geometry import Length, Position, Rectangle
from slide_style_kit.style import Alignment, BulletLevel, Color, Rotation, Typeface

# %% geometry


def test_inset_takes_the_margins_off_both_sides():
    """
    An inset shrinks the area by the margin on each side, not once.
    """
    area = Rectangle(left=1, top=2, width=10, height=4)
    assert area.inset(horizontal=1, vertical=0.5) == Rectangle(
        left=2, top=2.5, width=8, height=3
    )


def test_transposed_keeps_the_center():
    """
    Transposing swaps width and height around the same center.
    """
    area = Rectangle(left=1, top=2, width=4, height=2)
    transposed = area.transposed()
    assert transposed.center == area.center
    assert (transposed.width, transposed.height) == (area.height, area.width)


def test_rotated_box_is_drawn_from_its_transposed_area():
    """
    A box reading upward is drawn upright in its transposed area, then turned.
    """
    area = Rectangle(left=0, top=0, width=1, height=3)
    box = Box(area=area, rotation=Rotation.READING_UPWARD)
    assert box.unrotated_area == area.transposed()


# %% bullets


def test_each_bullet_level_is_indented_one_step_further():
    """
    The second level's bullet starts where the first level's text starts.
    """
    font_size = 20
    step = font_size / Length.points_per_inch * BulletLevel.indentation_step_in_ems
    offsets = BulletLevel.SECOND.offsets(font_size=font_size)
    assert offsets.bullet == pytest.approx(step)
    assert offsets.text == pytest.approx(2 * step)


# %% pictures


def test_a_picture_without_width_and_height_is_rejected():
    """
    A picture needs at least one side to be drawn at a defined size.
    """
    with pytest.raises(UnsizedPicture):
        Picture(path=Asset.ROBOT_SKETCH, position=Position(x=0, y=0))


def test_a_picture_given_one_side_keeps_its_aspect_ratio():
    """
    Sizing by width or by the resulting height gives the same picture.
    """
    by_width = Picture(path=Asset.AICOR_LOGO, position=Position(x=0, y=0), width=2)
    size = by_width.displayed_size()
    by_height = Picture(
        path=Asset.AICOR_LOGO, position=Position(x=0, y=0), height=size.height
    )
    assert by_height.displayed_size().width == pytest.approx(2)


# %% tables


def test_table_rules_follow_booktabs():
    """
    Thick rules above and below the table, a thin one under the header only.
    """
    table = Table(
        position=Position(x=0, y=0),
        column_widths=[1, 1],
        rows=[["a", "b"], ["c", "d"], ["e", "f"]],
    )
    widths = [table.rule_width(boundary=boundary) for boundary in range(4)]
    assert widths == [
        table.outer_rule_width,
        table.header_rule_width,
        0,
        table.outer_rule_width,
    ]


def test_only_the_header_row_is_bold():
    """
    The first row is set in bold and every row keeps its column's alignment.
    """
    table = Table(
        position=Position(x=0, y=0),
        column_widths=[1],
        rows=[["head"], ["body"]],
        column_alignments=[Alignment.RIGHT],
    )
    header = table.cell_paragraph(row_index=0, column_index=0)
    body = table.cell_paragraph(row_index=1, column_index=0)
    assert (header.bold, body.bold) == (True, False)
    assert body.alignment == Alignment.RIGHT


# %% components


def test_code_block_keeps_indentation_and_widens_the_gap_at_blank_lines():
    """
    A blank line becomes extra space and leading spaces become an indent.
    """
    code = CodeBlock(
        area=Rectangle(left=0, top=0, width=5, height=2),
        source_code="def f():\n\n    return 1\n",
    )
    first, second = code.code_paragraphs()
    character_width = (
        CodeBlock.character_width_in_ems * code.font_size / Length.points_per_inch
    )
    assert first.space_after == code.font_size * code.blank_line_height
    assert second.indent == pytest.approx(4 * character_width)


def test_todo_note_grows_by_one_line_per_line_of_text():
    """
    Text one character longer than a line makes the note one line taller.
    """
    short = TodoNote(text="x")
    long = TodoNote(text="x" * (short.characters_per_line + 1))
    assert long.area.height - short.area.height == pytest.approx(short.line_height)


def test_matrix_brackets_enclose_all_entries():
    """
    The brackets span every row and leave the gap on both sides of the columns.
    """
    matrix = Matrix(
        position=Position(x=1, y=2), entries=[["1", "2"], ["3", "4"], ["5", "6"]]
    )
    left_stroke, right_stroke = matrix.parts()[0], matrix.parts()[3]
    assert (left_stroke.start.y, left_stroke.end.y) == (2, 2 + 3 * matrix.row_height)
    assert right_stroke.start.x - left_stroke.start.x == pytest.approx(
        2 * matrix.column_width + 2 * matrix.bracket_gap
    )


def test_code_block_highlights_keywords_numbers_and_comments():
    """
    Each kind of token is set in its own colour, comments also in italics.
    """
    code = CodeBlock(
        area=Rectangle(left=0, top=0, width=5, height=2),
        source_code="import torch  # load\nx = 2.0\n",
    )
    first, second = code.code_paragraphs()
    keyword, _, comment = first.markup.runs()
    number = second.markup.runs()[-1]
    assert (keyword.text, keyword.color) == ("import", Color.CODE_KEYWORD)
    assert (comment.color, comment.italic) == (Color.CODE_COMMENT, True)
    assert (number.text, number.color) == ("2.0", Color.CODE_NUMBER)


def test_code_block_keeps_closing_braces_monospaced():
    """
    Braces of the code stay part of the code instead of ending its markup spans.
    """
    code = CodeBlock(
        area=Rectangle(left=0, top=0, width=5, height=2),
        source_code='x = {"a": 1}\n',
    )
    (line,) = code.code_paragraphs()
    runs = line.markup.runs()
    assert "".join(run.text for run in runs) == 'x = {"a": 1}'
    assert all(run.typeface == Typeface.MONOSPACE for run in runs)
