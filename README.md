# slide_style_kit

Describe a lecture deck in the Uni Bremen beamer look (16:9) once in Python, and render it
to both **.pptx** and **.pdf**. Built for the *Advanced Methods of AI* lecture slides,
following the krrood conventions (see `AGENTS.md`).

## Setup

```bash
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev,decks]"
pre-commit install
```

The `decks` extra brings what the decks under `decks/` compute with (numpy, scipy,
matplotlib, rdflib). The decks use krrood from the main branch of
[cram2](https://github.com/cram2/cognitive_robot_abstract_machine), newer than its
release on PyPI. Install it editable from a checkout, the krrood distributions
together with the packages they need at the same version:

```bash
git clone https://github.com/cram2/cognitive_robot_abstract_machine.git
cd cognitive_robot_abstract_machine
pip install $(printf -- '-e %s ' krrood/krrood-*/) -e krrood \
    -e random_events -e probabilistic_model -e domain_models/krrood_compute_resources
```

To update krrood, pull that checkout and run the same `pip install` again.

Fonts for the PDF: Liberation Sans/Mono and DejaVu Sans
(`apt install fonts-liberation fonts-dejavu-core`). For other locations, set
`SLIDEKIT_LIBERATION_DIR` (folder with `LiberationSans-Regular.ttf` etc.) and
`SLIDEKIT_DEJAVU` (path of `DejaVuSans.ttf`). The .pptx uses Arial / Courier New /
Cambria Math.

Formulas (`Formula`) are typeset with LaTeX the way manim does it: `latex` compiles
them to DVI, `dvisvgm` converts that to SVG, which the PDF draws as vectors (via
svglib), and `dvipng` to the PNG the .pptx shows. They need a TeX installation
(`apt install texlive texlive-latex-extra dvisvgm dvipng`). Rendered formulas are
cached in `~/.cache/slide_style_kit/formulas`, keyed by a hash of their source.

## Quick start

`python -m slide_style_kit.example` writes `example.pptx` and `example.pdf` into the
current directory. Copy `src/slide_style_kit/example.py` to start a new deck:

```python
from pathlib import Path

from slide_style_kit.deck import Deck
from slide_style_kit.elements import Paragraph
from slide_style_kit.pdf import PDFRenderer
from slide_style_kit.power_point import PowerPointRenderer
from slide_style_kit.slides import BulletSlide

deck = Deck(
    title="My lecture",
    author="Me",
    sections=["Introduction"],
    slides=[
        BulletSlide(
            title="Hello",
            section="Introduction",
            paragraphs=Paragraph.bullet_points(texts=["one", "{b:two}"]),
            take_away="that is all",
        )
    ],
)
PowerPointRenderer(deck=deck, path=Path("deck.pptx")).render()
PDFRenderer(deck=deck, path=Path("deck.pdf")).render()
```

## Modules

| Module | Content |
|---|---|
| `elements` | `Paragraph`, `TextFrame`, `Picture`, `Video`, `Formula`, `Box`, `Arrow`, `Table` |
| `formulas` | `FormulaTypesetter`: LaTeX to SVG and PNG, cached |
| `components` | `DiagramNode`, `Label`, `Caption`, `TakeAway`, `CodeBlock`, `TodoNote` |
| `slides` | `TitleSlide`, `TableOfContentsSlide`, `SectionDividerSlide`, `BulletSlide`, `ComparisonSlide`, `ContentSlide`, `PlainSlide` |
| `deck` | `Deck` and `PageDecoration` (title bar, footer navigation, logo) |
| `style` | `Color` palette, `Typeface`, `BulletLevel`, `Alignment`, `VerticalAnchor`, `Rotation` |
| `markup` | the inline markup below |
| `geometry` | `Position`, `Size`, `Rectangle`, `Length` |
| `power_point`, `pdf` | the renderers |
| `assets` | logos, robot sketch, example code |

## Text markup

Inside any string (not nestable):
`{b:bold}` `{i:italic}` `{a:alert red}` `{s:structure blue bold}` `{m:monospace}`
`{y:math symbol font}` `{t:todo marker}`

## Layout

* A page is 13.333 x 7.5 in; all coordinates are inches from the top left.
* Title bar at the top, footer (page number, section navigation, logo) below y = 6.97.
  Content goes between y ≈ 1.2 and 6.8.
* `Deck.sections` lists the footer sections; each slide's `section` highlights one.
* Bullets: `BulletLevel.FIRST` blue ▶, `SECOND` –, `THIRD` •.
* `TitleSlide` and `PlainSlide` have no title bar and footer.
* Any slide's `todo` shows as a sticky note on it and leads its speaker notes.

## Development

```bash
pytest
krrood check --all-lines $(git ls-files '*.py')
krrood agents-md   # regenerate AGENTS.md after a krrood update
```
