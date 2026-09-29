"""CLI: turn a figure definition into SVG / PNG / VSDX / VDX.

Usage
-----
python build.py <figure.py> --out <dir> [--name NAME] [--title TITLE]
                [--no-png] [--scale 1.4]

The figure file must expose ``build()`` returning a ``diagramlib.Fig`` and may
optionally expose ``NAME`` and ``TITLE`` module constants.  Example figures live
in ``assets/examples/`` of this skill.
"""
import argparse
import importlib.util
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from diagramlib import export  # noqa: E402


def load_figure(path):
    spec = importlib.util.spec_from_file_location("figure_def", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "build"):
        raise SystemExit("%s does not define build()" % path)
    return mod


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("figure", help="python file defining build()")
    ap.add_argument("--out", default=".", help="output directory")
    ap.add_argument("--name", default=None, help="output basename")
    ap.add_argument("--title", default=None, help="Visio page name")
    ap.add_argument("--scale", type=float, default=1.4, help="PNG pixel scale")
    ap.add_argument("--no-png", action="store_true", help="skip rasterising")
    a = ap.parse_args(argv)

    mod = load_figure(a.figure)
    fig = mod.build()
    name = a.name or getattr(mod, "NAME",
                             os.path.splitext(os.path.basename(a.figure))[0])
    title = a.title or getattr(mod, "TITLE", name)
    made = export(fig, a.out, name, title, png=not a.no_png, scale=a.scale)
    print("shapes: %d" % len(fig.items))
    for p in made:
        print("  ->", p)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
