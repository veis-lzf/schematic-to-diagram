"""Prepare a schematic PDF: one PNG per page + a per-page text dump.

Usage
-----
python pdf_prep.py <schematic.pdf> --out <dir> [--dpi 200] [--text-only]

Rasterising uses poppler ``pdftoppm`` (bundled with the Codex runtime);
text extraction tries ``pypdf`` then ``pdfplumber``.  The text dump is what you
search for net names, part numbers and values; the PNGs are what you actually
read when tracing the schematic.
"""
import argparse
import os
import shutil
import subprocess
import sys


def find_poppler(name):
    hit = shutil.which(name)
    if hit:
        return hit
    roots = [r"C:\Users\woan\.cache\codex-runtimes\codex-primary-runtime\dependencies\native\poppler"]
    for r in roots:
        for dirpath, _dirs, files in os.walk(r):
            if name + ".exe" in files or name in files:
                return os.path.join(dirpath, name + (".exe" if os.name == "nt" else ""))
    return None


def rasterise(pdf, outdir, dpi=200, prefix="page"):
    exe = find_poppler("pdftoppm")
    if not exe:
        print("! pdftoppm not found - skipping rasterisation")
        return []
    os.makedirs(outdir, exist_ok=True)
    cmd = [exe, "-r", str(dpi), "-png", pdf, os.path.join(outdir, prefix)]
    subprocess.run(cmd, check=True)
    made = sorted(os.path.join(outdir, f) for f in os.listdir(outdir)
                  if f.startswith(prefix) and f.lower().endswith(".png"))
    return made


def extract_text(pdf, out_path):
    text = None
    try:
        from pypdf import PdfReader
        reader = PdfReader(pdf)
        parts = []
        for i, page in enumerate(reader.pages, start=1):
            parts.append("===== PAGE %d =====" % i)
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)
    except Exception:
        try:
            import pdfplumber
            parts = []
            with pdfplumber.open(pdf) as doc:
                for i, page in enumerate(doc.pages, start=1):
                    parts.append("===== PAGE %d =====" % i)
                    parts.append(page.extract_text() or "")
            text = "\n".join(parts)
        except Exception as exc:
            print("! text extraction failed (%s) - read the PNGs instead" % exc)
            return None
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return out_path


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--out", default=".")
    ap.add_argument("--dpi", type=int, default=200)
    ap.add_argument("--text-only", action="store_true")
    a = ap.parse_args(argv)

    os.makedirs(a.out, exist_ok=True)
    base = os.path.splitext(os.path.basename(a.pdf))[0]
    pngs = [] if a.text_only else rasterise(a.pdf, os.path.join(a.out, base), a.dpi)
    txt = extract_text(a.pdf, os.path.join(a.out, base + "_text.txt"))
    print("pages rasterised:", len(pngs))
    for p in pngs:
        print("  ", p)
    if txt:
        print("text ->", txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
