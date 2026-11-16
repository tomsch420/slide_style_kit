# Optimization

The *Advanced Methods of AI* lecture on convexity, gradient methods, computational
graphs, LP, QP and KKT, with a two-joint version of Giskard's QP as the running example,
built with `slide_style_kit`. Every number and every animation is computed in Python, so the deck
is reproducible from this folder alone.

| File | Content |
|---|---|
| `examples.py` | The problems, solved numerically: the velocity control LP/QP and its KKT multipliers (scipy), tableau simplex, log-barrier interior-point method, gradient descent / momentum / SGD / Adam, critical points of the peaks function, a backpropagated computational graph, a constrained maximum likelihood estimate |
| `scenes.py` | One manim scene per animation, drawn from `examples.py` |
| `animation_catalogue.py` | The animations, their frame sizes and file names |
| `render_animations.py` | Renders the scenes to `animations/<name>.mp4` plus the last frame as `<name>.png` |
| `introduction_to_optimization.py` | The deck; writes `.pptx` (embedded videos, click to play) and `.pdf` (poster frames linking to the videos) |
| `snippets/` | Code shown on the slides; `python snippets/backpropagation.py` prints what the slide claims |

## Build

From the repository root, in its `.venv` (manim needs `libcairo2-dev` and
`libpango1.0-dev` to install):

```bash
cd decks/introduction_to_optimization
python render_animations.py            # all animations, ~15 min (the 3D ones dominate)
python render_animations.py simplex    # or only some
python introduction_to_optimization.py # the .pptx and .pdf
```
