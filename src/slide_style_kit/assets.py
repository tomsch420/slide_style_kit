"""
The image and code files shipped with the package.
"""

from __future__ import annotations

from pathlib import Path

from krrood.patterns.path_enumeration import PathEnumeration

# %% shipped files


class Asset(PathEnumeration):
    """
    The files in the package's ``assets`` directory.
    """

    DIRECTORY = Path(__file__).parent / "assets"
    """
    The directory holding the other assets.
    """

    UNIVERSITY_OF_BREMEN_LOGO = DIRECTORY / "unibremen_logo.png"
    """
    The logo of the University of Bremen, on the title slide and in the footer.
    """

    AICOR_LOGO = DIRECTORY / "aicor_logo.png"
    """
    The logo of the AICOR institute, on the title slide.
    """

    ROBOT_SKETCH = DIRECTORY / "robot_sketch.png"
    """
    A sketch of a robot, for the bottom left of a title slide.
    """

    EXAMPLE_CODE = DIRECTORY / "example_code.py"
    """
    The code the example deck shows in a code block.
    """
