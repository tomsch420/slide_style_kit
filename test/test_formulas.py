"""
Tests of typesetting formulas with LaTeX and drawing them.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from pathlib import Path

import pytest
from PIL import Image
from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

from slide_style_kit.deck import Deck
from slide_style_kit.elements import Formula
from slide_style_kit.exceptions import FormulaTypesettingFailure
from slide_style_kit.formulas import FormulaTypesetter
from slide_style_kit.geometry import Rectangle
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer
from slide_style_kit.style import Color

# %% typesetting


@pytest.mark.skipif(shutil.which("latex") is None, reason="needs a TeX installation")
class TestFormulaTypesetting:
    """
    Formulas compiled with LaTeX into SVG and PNG files.
    """

    def test_vector_and_raster_images_have_the_same_shape(
        self, *, typesetter: FormulaTypesetter
    ):
        """
        The SVG and the PNG show the same formula, so their aspect ratios agree.
        """
        typeset = typesetter.typeset(latex=r"\sum_j x_j^2", color=Color.BLACK)
        with Image.open(typeset.raster_image) as image:
            pixel_width, pixel_height = image.size
        natural = typeset.natural_size
        assert pixel_width / pixel_height == pytest.approx(
            natural.width / natural.height, rel=0.05
        )

    def test_typesetting_again_reuses_the_cached_images(
        self, *, typesetter: FormulaTypesetter
    ):
        """
        A formula typeset before is read from the cache instead of compiled again.
        """
        first = typesetter.typeset(latex="x^2", color=Color.BLUE)
        written = first.vector_image.stat().st_mtime_ns
        second = typesetter.typeset(latex="x^2", color=Color.BLUE)
        assert second == first
        assert second.vector_image.stat().st_mtime_ns == written

    def test_invalid_latex_raises(self, *, typesetter: FormulaTypesetter):
        """
        LaTeX that does not compile raises instead of producing a broken image.
        """
        with pytest.raises(FormulaTypesettingFailure):
            typesetter.typeset(latex=r"\frac{", color=Color.BLACK)

    def test_formula_grows_with_its_font_size(self, *, formula_deck: Deck):
        """
        Doubling the font size doubles the size of the formula.
        """
        (formula,) = formula_deck.slides[0].items
        larger = replace(formula, font_size=2 * formula.font_size)
        assert larger.displayed_area().width == pytest.approx(
            2 * formula.displayed_area().width
        )

    def test_formula_too_wide_for_its_area_is_scaled_down(self, *, formula_deck: Deck):
        """
        A formula wider than its area is shrunk to the area's width.
        """
        (formula,) = formula_deck.slides[0].items
        narrow = replace(formula, area=Rectangle(left=1, top=1, width=0.5, height=2))
        assert narrow.displayed_area().width == pytest.approx(narrow.area.width)

    # %% rendering

    def test_pdf_draws_formulas_as_vectors(self, *, formula_deck: Deck, tmp_path: Path):
        """
        The PDF draws the formula's outlines instead of embedding an image.
        """
        renderer = PDFRenderer(deck=formula_deck, path=tmp_path / "deck.pdf")
        renderer.render()
        assert renderer.path.read_bytes().count(b"/Subtype /Image") == 0

    def test_power_point_shows_formulas_as_pictures(
        self, *, formula_deck: Deck, tmp_path: Path
    ):
        """
        PowerPoint cannot take SVG, so the slide shows the formula's PNG.
        """
        path = tmp_path / "deck.pptx"
        PowerPointRenderer(deck=formula_deck, path=path).render()
        (shape,) = Presentation(path).slides[0].shapes
        (formula,) = formula_deck.slides[0].items
        assert shape.shape_type == MSO_SHAPE_TYPE.PICTURE
        assert shape.image.blob == formula.typeset_formula.raster_image.read_bytes()
