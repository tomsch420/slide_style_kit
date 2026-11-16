"""
The font files the PDF renderer embeds.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum, StrEnum
from pathlib import Path

from reportlab.lib.fonts import addMapping
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from slide_style_kit.exceptions import MissingFontFile
from slide_style_kit.style import Typeface

# %% font variants


@dataclass(frozen=True)
class FontVariantStyle:
    """
    The weight and slant of one file of a font family.
    """

    file_suffix: str
    """
    The suffix that follows the family name in the file name.
    """

    bold: bool
    """
    Whether the variant is bold.
    """

    italic: bool
    """
    Whether the variant is italic.
    """


class FontVariant(FontVariantStyle, Enum):
    """
    The four files of a Liberation font family.
    """

    REGULAR = "Regular", False, False
    """
    Upright, normal weight.
    """

    BOLD = "Bold", True, False
    """
    Upright, bold.
    """

    ITALIC = "Italic", False, True
    """
    Italic, normal weight.
    """

    BOLD_ITALIC = "BoldItalic", True, True
    """
    Italic, bold.
    """

    def font_name(self, *, typeface: Typeface) -> str:
        """
        :param typeface: A typeface with a family of four files.
        :return: The name this variant of *typeface* is registered under.
        """
        return f"{typeface.pdf}-{self.file_suffix}"


class FontEnvironmentVariable(StrEnum):
    """
    The environment variables that point to font files in non-standard locations.
    """

    LIBERATION_DIRECTORY = "SLIDEKIT_LIBERATION_DIR"
    """
    The directory holding ``LiberationSans-Regular.ttf`` and its siblings.
    """

    DEJAVU_SANS = "SLIDEKIT_DEJAVU"
    """
    The path of ``DejaVuSans.ttf``.
    """


# %% font files


@dataclass(kw_only=True)
class FontFiles:
    """
    The locations of the font files, and their registration with reportlab.
    """

    liberation_directory: Path = Path("/usr/share/fonts/truetype/liberation")
    """
    The directory holding the Liberation Sans and Liberation Mono files.
    """

    dejavu_sans: Path = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    """
    The DejaVu Sans file, which the symbol typeface and the bullets use.
    """

    @classmethod
    def from_environment(cls) -> FontFiles:
        """
        :return: The locations the environment variables give, the defaults otherwise.
        """
        defaults = cls()
        return cls(
            liberation_directory=Path(
                os.environ.get(
                    FontEnvironmentVariable.LIBERATION_DIRECTORY,
                    defaults.liberation_directory,
                )
            ),
            dejavu_sans=Path(
                os.environ.get(
                    FontEnvironmentVariable.DEJAVU_SANS, defaults.dejavu_sans
                )
            ),
        )

    def register(self) -> None:
        """
        Register every font file with reportlab, so paragraphs can name the fonts.

        :raises MissingFontFile: If a font file does not exist.
        """
        for typeface in (Typeface.SANS_SERIF, Typeface.MONOSPACE):
            for variant in FontVariant:
                name = variant.font_name(typeface=typeface)
                path = self.liberation_directory / f"{name}.ttf"
                self.register_file(
                    name=name,
                    path=path,
                    environment_variable=FontEnvironmentVariable.LIBERATION_DIRECTORY,
                )
                addMapping(typeface.pdf, variant.bold, variant.italic, name)
        self.register_file(
            name=Typeface.SYMBOL.pdf,
            path=self.dejavu_sans,
            environment_variable=FontEnvironmentVariable.DEJAVU_SANS,
        )

    def register_file(
        self,
        *,
        name: str,
        path: Path,
        environment_variable: FontEnvironmentVariable,
    ) -> None:
        """
        :param name: The name the font is registered under.
        :param path: The font file.
        :param environment_variable: The variable that points to the file's location.
        :raises MissingFontFile: If the file does not exist.
        """
        if not path.is_file():
            raise MissingFontFile(path=path, environment_variable=environment_variable)
        pdfmetrics.registerFont(TTFont(name, path))
