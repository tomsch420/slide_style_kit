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
