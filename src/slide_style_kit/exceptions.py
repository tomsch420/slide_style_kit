"""
The errors raised while describing or rendering a deck.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from typing_extensions import TYPE_CHECKING

from krrood.exceptions import DataclassException

if TYPE_CHECKING:
    from slide_style_kit.fonts import FontEnvironmentVariable
    from slide_style_kit.formulas import LatexTool

# %% fonts


@dataclass(kw_only=True)
class MissingFontFile(DataclassException):
    """
    Raised when a font file the PDF embeds does not exist.
    """

    path: Path
    """
    The font file that was looked for.
    """

    environment_variable: FontEnvironmentVariable
    """
    The environment variable that points to the font file or its directory.
    """

    def error_message(self) -> str:
        return f"The font file {self.path} does not exist."

    def suggest_correction(self) -> str:
        return (
            "Install the fonts with `apt install fonts-liberation fonts-dejavu-core`, "
            f"or set {self.environment_variable} to their location."
        )


# %% pictures


@dataclass(kw_only=True)
class UnsizedPicture(DataclassException):
    """
    Raised when a picture is given neither a width nor a height.
    """

    path: Path
    """
    The image file of the picture.
    """

    def error_message(self) -> str:
        return f"The picture of {self.path} has neither a width nor a height."

    def suggest_correction(self) -> str:
        return (
            "Give the width, the height or both; a missing one keeps the aspect ratio."
        )


# %% formulas


@dataclass(kw_only=True)
class MissingLatexTool(DataclassException):
    """
    Raised when a program needed to typeset formulas is not installed.
    """

    tool: LatexTool
    """
    The program that was looked for.
    """

    def error_message(self) -> str:
        return f"The program {self.tool} is not installed."

    def suggest_correction(self) -> str:
        return (
            "Install a TeX distribution with dvisvgm and dvipng, such as `apt install "
            "texlive texlive-latex-extra dvisvgm dvipng`."
        )


@dataclass(kw_only=True)
class FormulaTypesettingFailure(DataclassException):
    """
    Raised when a program of the TeX installation fails on a formula.
    """

    tool: LatexTool
    """
    The program that failed.
    """

    log: str
    """
    The output of the program.
    """

    def error_message(self) -> str:
        errors = [line for line in self.log.splitlines() if line.startswith("!")]
        return f"{self.tool} failed: {' '.join(errors) or self.log[-500:]}"

    def suggest_correction(self) -> str:
        return (
            "Check the formula's LaTeX; it is set in math mode, without dollar signs."
        )
