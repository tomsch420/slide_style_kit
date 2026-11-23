"""
Typesetting formulas with LaTeX, the way manim does: compile to DVI, convert to SVG for
vector output and to PNG for formats that only take raster images.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ElementTree
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

from krrood.patterns.classproperty import classproperty

from slide_style_kit.assets import Asset
from slide_style_kit.exceptions import FormulaTypesettingFailure, MissingLatexTool
from slide_style_kit.geometry import Length, Size
from slide_style_kit.style import Color

# %% tools


class LatexTool(StrEnum):
    """
    The programs of a TeX installation the typesetting runs.
    """

    LATEX = "latex"
    """
    Compiles the formula's document to DVI.
    """

    DVISVGM = "dvisvgm"
    """
    Converts the DVI to SVG, with the glyphs as outlines.
    """

    DVIPNG = "dvipng"
    """
    Converts the DVI to a PNG with a transparent background.
    """

    def run(self, *, arguments: list[str], directory: Path) -> str:
        """
        :param arguments: The command line arguments after the program name.
        :param directory: The working directory of the program.
        :return: The program's combined output.
        :raises MissingLatexTool: If the program is not installed.
        :raises FormulaTypesettingFailure: If the program exits with an error.
        """
        if shutil.which(self.value) is None:
            raise MissingLatexTool(tool=self)
        completed = subprocess.run(
            [self.value, *arguments],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )
        if completed.returncode != 0:
            raise FormulaTypesettingFailure(tool=self, log=completed.stdout)
        return completed.stdout


class TemplatePlaceholder(StrEnum):
    """
    The markers in the formula template that the typesetting replaces.
    """

    COLOR = "%COLOR%"
    """
    Replaced by the hexadecimal colour of the formula.
    """

    FORMULA = "%FORMULA%"
    """
    Replaced by the LaTeX math of the formula.
    """


# %% typesetting


@dataclass(kw_only=True, frozen=True)
class TypesetFormula:
    """
    A formula rendered to image files, at the size LaTeX sets it at 10 points.
    """

    vector_image: Path
    """
    The formula as SVG, its glyphs as outlines.
    """

    raster_image: Path
    """
    The formula as PNG with a transparent background.
    """

    natural_size: Size
    """
    The size of the formula at a 10 point font, in inch.
    """

    @classproperty
    def natural_font_size(cls) -> float:
        """
        The font size, in points, at which :attr:`natural_size` applies.
        """
        return 10.0


@dataclass(kw_only=True)
class FormulaTypesetter:
    """
    Typesets formulas with LaTeX and caches the results by a hash of their source.
    """

    cache_directory: Path = field(
        default_factory=lambda: Path.home() / ".cache" / "slide_style_kit" / "formulas"
    )
    """
    The directory the rendered formulas are kept in.
    """

    template: Path = field(default_factory=lambda: Path(Asset.FORMULA_TEMPLATE))
    """
    The LaTeX document a formula is set in, with :class:`TemplatePlaceholder` markers.
    """

    raster_resolution: int = 600
    """
    The resolution of the PNG files, in dots per inch.
    """

    def typeset(self, *, latex: str, color: Color) -> TypesetFormula:
        """
        :param latex: The formula as LaTeX math, without dollar signs.
        :param color: The colour of the formula.
        :return: The rendered formula, typeset now or read from the cache.
        """
        document = (
            self.template.read_text()
            .replace(TemplatePlaceholder.COLOR, color.value)
            .replace(TemplatePlaceholder.FORMULA, latex)
        )
        key = hashlib.sha256(
            f"{document}\n{self.raster_resolution}".encode()
        ).hexdigest()[:16]
        vector_image = self.cache_directory / f"{key}.svg"
        raster_image = self.cache_directory / f"{key}.png"
        if not (vector_image.exists() and raster_image.exists()):
            self.compile(
                document=document, vector_image=vector_image, raster_image=raster_image
            )
        return TypesetFormula(
            vector_image=vector_image,
            raster_image=raster_image,
            natural_size=self.svg_size(path=vector_image),
        )

    def compile(self, *, document: str, vector_image: Path, raster_image: Path) -> None:
        """
        Compile *document* and write its formula to *vector_image* and *raster_image*.
        """
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as directory:
            working_directory = Path(directory)
            (working_directory / "formula.tex").write_text(document)
            LatexTool.LATEX.run(
                arguments=["-interaction=nonstopmode", "-halt-on-error", "formula.tex"],
                directory=working_directory,
            )
            LatexTool.DVISVGM.run(
                arguments=[
                    "--no-fonts",
                    "--exact-bbox",
                    "-o",
                    str(vector_image),
                    "formula.dvi",
                ],
                directory=working_directory,
            )
            LatexTool.DVIPNG.run(
                arguments=[
                    "-D",
                    str(self.raster_resolution),
                    "-bg",
                    "Transparent",
                    "-T",
                    "tight",
                    "-o",
                    str(raster_image),
                    "formula.dvi",
                ],
                directory=working_directory,
            )

    def svg_size(self, *, path: Path) -> Size:
        """
        :return: The width and height an SVG written by dvisvgm declares, in inch.
        """
        root = ElementTree.parse(path).getroot()
        width, height = (
            float(root.attrib[dimension].removesuffix("pt"))
            for dimension in ("width", "height")
        )
        points_per_inch = Length.points_per_inch
        return Size(width=width / points_per_inch, height=height / points_per_inch)
