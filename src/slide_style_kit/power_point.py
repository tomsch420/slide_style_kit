"""
Rendering a deck to a PowerPoint (``.pptx``) file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from functools import cached_property

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt
from typing_extensions import TYPE_CHECKING

from krrood.ormatic.utils import classproperty

from slide_style_kit.renderer import Renderer
from slide_style_kit.style import Alignment, Color, Typeface, VerticalAnchor

if TYPE_CHECKING:
    from pptx.presentation import Presentation as PresentationDocument
    from pptx.slide import Slide as PresentationSlide
    from pptx.table import _Cell
    from pptx.text.text import TextFrame as PresentationTextFrame
    from pptx.text.text import _Paragraph

    from slide_style_kit.elements import (
        Arrow,
        Box,
        Paragraph,
        Picture,
        Table,
        TextFrame,
        Video,
    )
    from slide_style_kit.markup import TextRun
    from slide_style_kit.slides import Slide

# %% table cell borders


class CellBorder(StrEnum):
    """
    The borders of a table cell, by their OOXML tag.
    """

    LEFT = "a:lnL"
    """
    The left border.
    """

    RIGHT = "a:lnR"
    """
    The right border.
    """

    TOP = "a:lnT"
    """
    The top border.
    """

    BOTTOM = "a:lnB"
    """
    The bottom border.
    """


# %% renderer


@dataclass(kw_only=True)
class PowerPointRenderer(Renderer):
    """
    Writes a deck to a PowerPoint file, with the speaker notes in the notes pages.
    """

    current_slide: PresentationSlide | None = field(default=None, init=False)
    """
    The slide being drawn.
    """

    @classproperty
    def blank_layout_index(cls) -> int:
        """
        The index of the blank layout in python-pptx's default template.
        """
        return 6

    @classproperty
    def video_media_type(cls) -> str:
        """
        The media type of the embedded videos.
        """
        return "video/mp4"

    @cached_property
    def presentation(self) -> PresentationDocument:
        """
        The presentation being drawn, sized and titled after the deck.
        """
        presentation = Presentation()
        presentation.slide_width = Inches(self.deck.page_size.width)
        presentation.slide_height = Inches(self.deck.page_size.height)
        presentation.core_properties.title = self.deck.title
        presentation.core_properties.author = self.deck.author
        return presentation

    def start_slide(self, *, slide: Slide) -> None:
        layout = self.presentation.slide_layouts[PowerPointRenderer.blank_layout_index]
        self.current_slide = self.presentation.slides.add_slide(layout)

    def finish_slide(self, *, slide: Slide) -> None:
        notes = slide.speaker_notes()
        if notes:
            self.current_slide.notes_slide.notes_text_frame.text = notes

    def save(self) -> None:
        self.presentation.save(self.path)

    # %% text

    def draw_text_frame(self, *, text_frame: TextFrame) -> None:
        area = text_frame.area
        shape = self.current_slide.shapes.add_textbox(
            Inches(area.left), Inches(area.top), Inches(area.width), Inches(area.height)
        )
        frame = shape.text_frame
        self.prepare_frame(frame=frame, margin=0)
        frame.vertical_anchor = self.vertical_anchor(anchor=text_frame.anchor)
        for index, paragraph in enumerate(text_frame.paragraphs):
            target = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            self.write_paragraph(
                target=target,
                paragraph=paragraph,
                font_size=paragraph.font_size or text_frame.font_size,
                underline=text_frame.underline,
            )

    def prepare_frame(self, *, frame: PresentationTextFrame, margin: float) -> None:
        """
        Make *frame* wrap its text and give it *margin* inch on every side.
        """
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = Inches(margin)
        frame.margin_top = frame.margin_bottom = Inches(margin)

    def write_paragraph(
        self,
        *,
        target: _Paragraph,
        paragraph: Paragraph,
        font_size: float,
        underline: bool,
    ) -> None:
        """
        Fill the PowerPoint paragraph *target* with *paragraph* set at *font_size*.
        """
        target.alignment = self.horizontal_alignment(alignment=paragraph.alignment)
        target.line_spacing = Pt(font_size * paragraph.line_spacing)
        target.space_after = Pt(paragraph.space_after)
        self.write_bullet(target=target, paragraph=paragraph, font_size=font_size)
        for run in paragraph.markup.runs():
            self.write_run(
                target=target, run=run, font_size=font_size, underline=underline
            )

    def write_bullet(
        self, *, target: _Paragraph, paragraph: Paragraph, font_size: float
    ) -> None:
        """
        Give *target* the bullet and indentation of *paragraph*.
        """
        properties = target._p.get_or_add_pPr()
        if paragraph.level is None:
            etree.SubElement(properties, qn("a:buNone"))
            if paragraph.indent:
                properties.set("marL", str(Emu(Inches(paragraph.indent))))
            return
        offsets = paragraph.level.offsets(font_size=font_size)
        properties.set("marL", str(Emu(Inches(offsets.text))))
        properties.set("indent", str(-Emu(Inches(offsets.text - offsets.bullet))))
        color = etree.SubElement(properties, qn("a:buClr"))
        etree.SubElement(color, qn("a:srgbClr")).set("val", paragraph.level.color)
        relative_size = str(int(paragraph.level.relative_size * 100000))
        etree.SubElement(properties, qn("a:buSzPct")).set("val", relative_size)
        typeface = Typeface.SANS_SERIF.power_point
        etree.SubElement(properties, qn("a:buFont")).set("typeface", typeface)
        etree.SubElement(properties, qn("a:buChar")).set(
            "char", paragraph.level.character
        )

    def write_run(
        self,
        *,
        target: _Paragraph,
        run: TextRun,
        font_size: float,
        underline: bool = False,
    ) -> None:
        """
        Append *run* to *target*, set at *font_size*.
        """
        written = target.add_run()
        written.text = run.text
        font = written.font
        font.size = Pt(font_size)
        font.name = run.typeface.power_point
        font.bold = run.bold
        font.italic = run.italic
        font.color.rgb = RGBColor.from_string(run.color)
        if underline:
            font.underline = True

    def horizontal_alignment(self, *, alignment: Alignment) -> PP_ALIGN:
        """
        :return: The PowerPoint alignment matching *alignment*.
        """
        match alignment:
            case Alignment.LEFT:
                return PP_ALIGN.LEFT
            case Alignment.CENTER:
                return PP_ALIGN.CENTER
            case Alignment.RIGHT:
                return PP_ALIGN.RIGHT

    def vertical_anchor(self, *, anchor: VerticalAnchor) -> MSO_ANCHOR:
        """
        :return: The PowerPoint anchor matching *anchor*.
        """
        match anchor:
            case VerticalAnchor.TOP:
                return MSO_ANCHOR.TOP
            case VerticalAnchor.MIDDLE:
                return MSO_ANCHOR.MIDDLE
            case VerticalAnchor.BOTTOM:
                return MSO_ANCHOR.BOTTOM

    # %% pictures and shapes

    def draw_picture(self, *, picture: Picture) -> None:
        size = picture.displayed_size()
        self.current_slide.shapes.add_picture(
            str(picture.path),
            Inches(picture.position.x),
            Inches(picture.position.y),
            Inches(size.width),
            Inches(size.height),
        )

    def draw_video(self, *, video: Video) -> None:
        size = video.displayed_size()
        self.current_slide.shapes.add_movie(
            str(video.movie),
            Inches(video.position.x),
            Inches(video.position.y),
            Inches(size.width),
            Inches(size.height),
            poster_frame_image=str(video.path),
            mime_type=PowerPointRenderer.video_media_type,
        )

    def draw_box(self, *, box: Box) -> None:
        area = box.unrotated_area
        shape = self.current_slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE if box.rounded else MSO_SHAPE.RECTANGLE,
            Inches(area.left),
            Inches(area.top),
            Inches(area.width),
            Inches(area.height),
        )
        shape.rotation = box.rotation
        if box.rounded:
            shape.adjustments[0] = box.corner_radius
        shape.shadow.inherit = False
        if box.fill:
            shape.fill.solid()
            shape.fill.fore_color.rgb = RGBColor.from_string(box.fill)
        else:
            shape.fill.background()
        if box.outline:
            shape.line.color.rgb = RGBColor.from_string(box.outline)
            shape.line.width = Pt(box.outline_width)
        else:
            shape.line.fill.background()
        frame = shape.text_frame
        self.prepare_frame(frame=frame, margin=box.text_margin)
        frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        for index, paragraph in enumerate(box.paragraphs()):
            target = frame.paragraphs[0] if index == 0 else frame.add_paragraph()
            target.alignment = self.horizontal_alignment(alignment=paragraph.alignment)
            target.line_spacing = Pt(box.font_size * paragraph.line_spacing)
            for run in paragraph.markup.runs():
                self.write_run(target=target, run=run, font_size=box.font_size)

    def draw_arrow(self, *, arrow: Arrow) -> None:
        connector = self.current_slide.shapes.add_connector(
            MSO_CONNECTOR.STRAIGHT,
            Inches(arrow.start.x),
            Inches(arrow.start.y),
            Inches(arrow.end.x),
            Inches(arrow.end.y),
        )
        connector.line.color.rgb = RGBColor.from_string(arrow.color)
        connector.line.width = Pt(arrow.line_width)
        if arrow.dashed:
            connector.line.dash_style = MSO_LINE_DASH_STYLE.SQUARE_DOT
        if arrow.has_head:
            head = etree.SubElement(connector.line._get_or_add_ln(), qn("a:tailEnd"))
            head.set("type", "triangle")
            head.set("w", "med")
            head.set("len", "med")

    # %% tables

    def draw_table(self, *, table: Table) -> None:
        row_count, column_count = len(table.rows), len(table.column_widths)
        frame = self.current_slide.shapes.add_table(
            row_count,
            column_count,
            Inches(table.position.x),
            Inches(table.position.y),
            Inches(sum(table.column_widths)),
            Inches(table.row_height * row_count),
        )
        shape_table = frame.table
        shape_table._tbl.tblPr.set("firstRow", "0")
        shape_table._tbl.tblPr.set("bandRow", "0")
        for column_index, width in enumerate(table.column_widths):
            shape_table.columns[column_index].width = Inches(width)
        for row_index in range(row_count):
            shape_table.rows[row_index].height = Inches(table.row_height)
            for column_index in range(column_count):
                self.write_cell(
                    cell=shape_table.cell(row_index, column_index),
                    table=table,
                    row_index=row_index,
                    column_index=column_index,
                )

    def write_cell(
        self, *, cell: _Cell, table: Table, row_index: int, column_index: int
    ) -> None:
        """
        Fill *cell* with the content and rules of the cell of *table* it stands for.
        """
        cell.fill.background()
        cell.margin_left = cell.margin_right = Inches(table.cell_padding)
        cell.margin_top = cell.margin_bottom = Inches(0)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        paragraph = table.cell_paragraph(row_index=row_index, column_index=column_index)
        target = cell.text_frame.paragraphs[0]
        target.alignment = self.horizontal_alignment(alignment=paragraph.alignment)
        for run in paragraph.markup.runs():
            self.write_run(target=target, run=run, font_size=table.font_size)
        self.write_cell_border(cell=cell, border=CellBorder.LEFT, width=0)
        self.write_cell_border(cell=cell, border=CellBorder.RIGHT, width=0)
        self.write_cell_border(
            cell=cell,
            border=CellBorder.TOP,
            width=table.rule_width(boundary=row_index),
        )
        self.write_cell_border(
            cell=cell,
            border=CellBorder.BOTTOM,
            width=table.rule_width(boundary=row_index + 1),
        )

    def write_cell_border(
        self, *, cell: _Cell, border: CellBorder, width: float
    ) -> None:
        """
        Draw *border* of *cell* in black at *width* points, or remove it for a width of 0.
        """
        properties = cell._tc.get_or_add_tcPr()
        for old in properties.findall(qn(border)):
            properties.remove(old)
        line = etree.SubElement(properties, qn(border))
        if not width:
            line.set("w", "0")
            etree.SubElement(line, qn("a:noFill"))
            return
        line.set("w", str(int(Pt(width))))
        fill = etree.SubElement(line, qn("a:solidFill"))
        etree.SubElement(fill, qn("a:srgbClr")).set("val", Color.BLACK)
