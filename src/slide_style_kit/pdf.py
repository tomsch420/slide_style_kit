"""
Rendering a deck to a PDF file.
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass, field
from functools import cached_property
from urllib.request import pathname2url
from xml.sax.saxutils import escape

from reportlab.graphics import renderPDF
from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import Paragraph as ReportLabParagraph
from svglib.svglib import svg2rlg
from typing_extensions import TYPE_CHECKING

from krrood.ormatic.utils import classproperty

from slide_style_kit.elements import TextFrame
from slide_style_kit.fonts import FontFiles, FontVariant
from slide_style_kit.geometry import Length
from slide_style_kit.renderer import Renderer
from slide_style_kit.style import (
    Alignment,
    Color,
    Rotation,
    Typeface,
    VerticalAnchor,
)

if TYPE_CHECKING:
    from slide_style_kit.elements import (
        Arrow,
        Box,
        Formula,
        Paragraph,
        Picture,
        Table,
        Video,
    )
    from slide_style_kit.markup import Markup
    from slide_style_kit.slides import Slide

# %% drawing parameters


@dataclass(kw_only=True)
class ArrowDrawing:
    """
    The proportions of arrowheads and dotted lines, in points.
    """

    head_minimum_length: float = 7
    """
    The length of the arrowhead of a thin line.
    """

    head_length_per_line_width: float = 3.0
    """
    The length of the arrowhead of a thick line, per point of line width.
    """

    head_width_ratio: float = 0.45
    """
    Half the width of the arrowhead's base, as a fraction of its length.
    """

    shaft_end_ratio: float = 0.8
    """
    How far back from the tip the line ends, as a fraction of the head's length.
    """

    dash_length: float = 1.2
    """
    The length of each dot of a dotted line.
    """

    gap_length: float = 2.2
    """
    The gap between the dots of a dotted line.
    """

    def head_length(self, *, line_width: float) -> float:
        """
        :return: The length of the arrowhead on a line of *line_width* points.
        """
        return max(
            self.head_minimum_length, line_width * self.head_length_per_line_width
        )


@dataclass(kw_only=True)
class PlayButtonDrawing:
    """
    The play button drawn on the poster of a video, marking it as a link to the video.
    """

    diameter: float = 0.4
    """
    The diameter of the button, in inch.
    """

    margin: float = 0.12
    """
    The distance between the button and the bottom right corner of the poster, in inch.
    """

    opacity: float = 0.85
    """
    The opacity of the button's disc.
    """


@dataclass(kw_only=True)
class LaidOutParagraph:
    """
    A paragraph wrapped to a width, ready to be drawn.
    """

    flowable: ReportLabParagraph
    """
    The reportlab paragraph.
    """

    height: float
    """
    The height of the wrapped paragraph, in points.
    """

    space_after: float
    """
    The space below the paragraph, in points.
    """


# %% renderer


@dataclass(kw_only=True)
class PDFRenderer(Renderer):
    """
    Writes a deck to a PDF file with embedded fonts.
    """

    font_files: FontFiles = field(default_factory=FontFiles.from_environment)
    """
    The font files to embed.
    """

    arrow_drawing: ArrowDrawing = field(default_factory=ArrowDrawing)
    """
    The proportions of arrowheads and dotted lines.
    """

    play_button: PlayButtonDrawing = field(default_factory=PlayButtonDrawing)
    """
    The play button on the posters of videos.
    """

    def __post_init__(self) -> None:
        """
        Register the font files, so the paragraphs drawn later can name the fonts.
        """
        self.font_files.register()

    @classproperty
    def unlimited_height(cls) -> float:
        """
        A height in points that no paragraph reaches, to wrap paragraphs to a width
        only.
        """
        return 10000

    @cached_property
    def canvas(self) -> Canvas:
        """
        The canvas being drawn, sized and titled after the deck.
        """
        page_size = self.deck.page_size
        canvas = Canvas(
            str(self.path),
            pagesize=(
                Length(inches=page_size.width).points,
                Length(inches=page_size.height).points,
            ),
        )
        canvas.setTitle(self.deck.title)
        canvas.setAuthor(self.deck.author)
        return canvas

    def distance_from_bottom(self, *, top: float) -> float:
        """
        :param top: A distance from the top of the page, in inch.
        :return: The same height measured from the bottom of the page, in points.
        """
        return Length(inches=self.deck.page_size.height - top).points

    def start_slide(self, *, slide: Slide) -> None:
        page_size = self.deck.page_size
        self.canvas.setFillColor(HexColor(f"#{Color.WHITE}"))
        self.canvas.rect(
            0,
            0,
            Length(inches=page_size.width).points,
            Length(inches=page_size.height).points,
            stroke=0,
            fill=1,
        )

    def finish_slide(self, *, slide: Slide) -> None:
        self.canvas.showPage()

    def save(self) -> None:
        self.canvas.save()

    # %% text

    def reportlab_markup(self, *, markup: Markup, underline: bool) -> str:
        """
        :return: *markup* in reportlab's paragraph markup.
        """
        text = ""
        for run in markup.runs():
            styled = escape(run.text)
            match run.typeface:
                case Typeface.MONOSPACE:
                    face = FontVariant.REGULAR.font_name(typeface=Typeface.MONOSPACE)
                    styled = f'<font face="{face}">{styled}</font>'
                case Typeface.SYMBOL:
                    styled = f'<font face="{Typeface.SYMBOL.pdf}">{styled}</font>'
            if run.bold:
                styled = f"<b>{styled}</b>"
            if run.italic:
                styled = f"<i>{styled}</i>"
            if underline:
                styled = f"<u>{styled}</u>"
            text += f'<font color="#{run.color}">{styled}</font>'
        return text

    def reportlab_alignment(self, *, alignment: Alignment) -> int:
        """
        :return: The reportlab alignment matching *alignment*.
        """
        match alignment:
            case Alignment.LEFT:
                return TA_LEFT
            case Alignment.CENTER:
                return TA_CENTER
            case Alignment.RIGHT:
                return TA_RIGHT

    def lay_out_paragraph(
        self,
        *,
        paragraph: Paragraph,
        font_size: float,
        width: float,
        underline: bool = False,
    ) -> LaidOutParagraph:
        """
        :param paragraph: The paragraph to lay out.
        :param font_size: The font size of the enclosing element, in points.
        :param width: The width to wrap the paragraph to, in inch.
        :param underline: Whether all of the text is underlined.
        :return: The paragraph wrapped to *width*.
        """
        size = paragraph.font_size or font_size
        style = ParagraphStyle(
            "paragraph",
            fontName=FontVariant.REGULAR.font_name(typeface=Typeface.SANS_SERIF),
            fontSize=size,
            leading=size * paragraph.line_spacing,
            alignment=self.reportlab_alignment(alignment=paragraph.alignment),
            leftIndent=Length(inches=paragraph.indent).points,
        )
        text = self.reportlab_markup(markup=paragraph.markup, underline=underline)
        bullet_character = None
        if paragraph.level is not None:
            offsets = paragraph.level.offsets(font_size=size)
            style.leftIndent = Length(inches=offsets.text).points
            style.bulletIndent = Length(inches=offsets.bullet).points
            style.bulletFontName = Typeface.SYMBOL.pdf
            style.bulletFontSize = size * paragraph.level.relative_size
            style.bulletColor = HexColor(f"#{paragraph.level.color}")
            bullet_character = paragraph.level.character
        flowable = ReportLabParagraph(text, style, bulletText=bullet_character)
        _, height = flowable.wrap(
            Length(inches=width).points, PDFRenderer.unlimited_height
        )
        return LaidOutParagraph(
            flowable=flowable, height=height, space_after=paragraph.space_after
        )

    def draw_text_frame(self, *, text_frame: TextFrame) -> None:
        area = text_frame.area
        laid_out = [
            self.lay_out_paragraph(
                paragraph=paragraph,
                font_size=text_frame.font_size,
                width=area.width,
                underline=text_frame.underline,
            )
            for paragraph in text_frame.paragraphs
        ]
        text_height = sum(item.height for item in laid_out) + sum(
            item.space_after for item in laid_out[:-1]
        )
        free_height = Length(inches=area.height).points - text_height
        top = self.distance_from_bottom(top=area.top)
        match text_frame.anchor:
            case VerticalAnchor.MIDDLE:
                top -= free_height / 2
            case VerticalAnchor.BOTTOM:
                top -= free_height
        left = Length(inches=area.left).points
        for item in laid_out:
            item.flowable.drawOn(self.canvas, left, top - item.height)
            top -= item.height + item.space_after

    # %% pictures and shapes

    def draw_picture(self, *, picture: Picture) -> None:
        size = picture.displayed_size()
        self.canvas.drawImage(
            str(picture.path),
            Length(inches=picture.position.x).points,
            self.distance_from_bottom(top=picture.position.y + size.height),
            Length(inches=size.width).points,
            Length(inches=size.height).points,
            mask="auto",
        )

    def draw_formula(self, *, formula: Formula) -> None:
        area = formula.displayed_area()
        drawing = svg2rlg(str(formula.typeset_formula.vector_image))
        scale = Length(inches=area.width).points / drawing.width
        drawing.scale(scale, scale)
        renderPDF.draw(
            drawing,
            self.canvas,
            Length(inches=area.left).points,
            self.distance_from_bottom(top=area.bottom),
        )

    def draw_video(self, *, video: Video) -> None:
        """
        Draw the poster of *video* with a play button, linked to the video file by a
        path relative to the PDF, so the two can be moved together.
        """
        self.draw_picture(picture=video)
        size = video.displayed_size()
        left = Length(inches=video.position.x).points
        bottom = self.distance_from_bottom(top=video.position.y + size.height)
        right = left + Length(inches=size.width).points
        top = bottom + Length(inches=size.height).points
        self.draw_play_button(right=right, bottom=bottom)
        link = os.path.relpath(video.movie.resolve(), self.path.resolve().parent)
        self.canvas.linkURL(pathname2url(link), (left, bottom, right, top), thickness=0)

    def draw_play_button(self, *, right: float, bottom: float) -> None:
        """
        Draw the play button in the corner left of *right* and above *bottom*, in
        points.
        """
        button = self.play_button
        radius = Length(inches=button.diameter).points / 2
        center_x = right - Length(inches=button.margin).points - radius
        center_y = bottom + Length(inches=button.margin).points + radius
        self.canvas.saveState()
        self.canvas.setFillColor(HexColor(f"#{Color.WHITE}"), alpha=button.opacity)
        self.canvas.setStrokeColor(HexColor(f"#{Color.BLUE}"))
        self.canvas.setLineWidth(1)
        self.canvas.circle(center_x, center_y, radius, stroke=1, fill=1)
        self.canvas.setFillColor(HexColor(f"#{Color.BLUE}"))
        triangle = self.canvas.beginPath()
        triangle.moveTo(center_x - 0.35 * radius, center_y - 0.5 * radius)
        triangle.lineTo(center_x - 0.35 * radius, center_y + 0.5 * radius)
        triangle.lineTo(center_x + 0.55 * radius, center_y)
        triangle.close()
        self.canvas.drawPath(triangle, stroke=0, fill=1)
        self.canvas.restoreState()

    def draw_box(self, *, box: Box) -> None:
        unrotated = box.unrotated_area
        width = Length(inches=unrotated.width).points
        height = Length(inches=unrotated.height).points
        if box.rotation == Rotation.NONE:
            self.draw_upright_box(
                box=box,
                left=Length(inches=unrotated.left).points,
                bottom=self.distance_from_bottom(top=unrotated.bottom),
                width=width,
                height=height,
            )
            return
        center = box.area.center
        self.canvas.saveState()
        self.canvas.translate(
            Length(inches=center.x).points, self.distance_from_bottom(top=center.y)
        )
        self.canvas.rotate(360 - box.rotation)
        self.draw_upright_box(
            box=box, left=-width / 2, bottom=-height / 2, width=width, height=height
        )
        self.canvas.restoreState()

    def draw_upright_box(
        self, *, box: Box, left: float, bottom: float, width: float, height: float
    ) -> None:
        """
        Draw *box* unrotated, with its lower left corner at (*left*, *bottom*) and the
        given *width* and *height*, all in points of the current coordinate system.
        """
        self.canvas.setLineWidth(box.outline_width)
        if box.outline:
            self.canvas.setStrokeColor(HexColor(f"#{box.outline}"))
        if box.fill:
            self.canvas.setFillColor(HexColor(f"#{box.fill}"))
        stroke, fill = int(bool(box.outline)), int(bool(box.fill))
        if box.rounded:
            radius = min(width, height) * box.corner_radius
            self.canvas.roundRect(
                left, bottom, width, height, radius, stroke=stroke, fill=fill
            )
        else:
            self.canvas.rect(left, bottom, width, height, stroke=stroke, fill=fill)
        if not box.text:
            return
        margin = Length(inches=box.text_margin).points
        text_width = width / Length.points_per_inch - 2 * box.text_margin
        line_height = box.font_size * box.line_spacing
        laid_out = [
            self.lay_out_paragraph(
                paragraph=paragraph, font_size=box.font_size, width=text_width
            )
            for paragraph in box.paragraphs()
        ]
        heights = [item.height or line_height for item in laid_out]
        top = bottom + height - (height - sum(heights)) / 2
        for item, item_height in zip(laid_out, heights):
            item.flowable.drawOn(self.canvas, left + margin, top - item_height)
            top -= item_height

    def draw_arrow(self, *, arrow: Arrow) -> None:
        color = HexColor(f"#{arrow.color}")
        self.canvas.setStrokeColor(color)
        self.canvas.setFillColor(color)
        self.canvas.setLineWidth(arrow.line_width)
        start_x = Length(inches=arrow.start.x).points
        start_y = self.distance_from_bottom(top=arrow.start.y)
        end_x = Length(inches=arrow.end.x).points
        end_y = self.distance_from_bottom(top=arrow.end.y)
        angle = math.atan2(end_y - start_y, end_x - start_x)
        drawing = self.arrow_drawing
        head_length = drawing.head_length(line_width=arrow.line_width)
        shaft_x, shaft_y = end_x, end_y
        if arrow.has_head:
            shaft_x -= head_length * drawing.shaft_end_ratio * math.cos(angle)
            shaft_y -= head_length * drawing.shaft_end_ratio * math.sin(angle)
        if arrow.dashed:
            self.canvas.setDash(drawing.dash_length, drawing.gap_length)
        self.canvas.line(start_x, start_y, shaft_x, shaft_y)
        self.canvas.setDash()
        if not arrow.has_head:
            return
        base_x = end_x - head_length * math.cos(angle)
        base_y = end_y - head_length * math.sin(angle)
        half_width = head_length * drawing.head_width_ratio
        offset_x, offset_y = -math.sin(angle) * half_width, math.cos(angle) * half_width
        head = self.canvas.beginPath()
        head.moveTo(end_x, end_y)
        head.lineTo(base_x + offset_x, base_y + offset_y)
        head.lineTo(base_x - offset_x, base_y - offset_y)
        head.close()
        self.canvas.drawPath(head, stroke=0, fill=1)

    # %% tables

    def draw_table(self, *, table: Table) -> None:
        for row_index in range(len(table.rows)):
            for column_index in range(len(table.column_widths)):
                cell_area = table.cell_area(
                    row_index=row_index, column_index=column_index
                )
                paragraph = table.cell_paragraph(
                    row_index=row_index, column_index=column_index
                )
                self.draw_text_frame(
                    text_frame=TextFrame(
                        area=cell_area.inset(horizontal=table.cell_padding, vertical=0),
                        paragraphs=[paragraph],
                        font_size=table.font_size,
                        anchor=VerticalAnchor.MIDDLE,
                    )
                )
        self.canvas.setStrokeColor(HexColor(f"#{Color.BLACK}"))
        left = Length(inches=table.position.x).points
        right = Length(inches=table.position.x + sum(table.column_widths)).points
        for boundary in range(len(table.rows) + 1):
            width = table.rule_width(boundary=boundary)
            if not width:
                continue
            height = self.distance_from_bottom(
                top=table.position.y + boundary * table.row_height
            )
            self.canvas.setLineWidth(width)
            self.canvas.line(left, height, right, height)
