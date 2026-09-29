---
name: schematic-to-diagram
description: Convert circuit schematics or structured hardware descriptions into clean system block diagrams and power trees, exporting SVG, PNG, VSDX, and VDX. Use when the user asks to turn a schematic PDF into a block diagram or power tree, simplify signal or power flow, or produce an editable Visio-compatible diagram. Do not use for detailed PCB layout, netlist editing, or datasheet parameter lookup.
---

# Schematic to Diagram

Turn a schematic or a structured hardware description into a readable diagram.
Trace only relationships that are supported by the source; do not invent
connections or voltage domains.

Output follows a fixed house style. Read
[references/style-guide.md](references/style-guide.md) before laying out a
figure; it holds the hard rules, the voltage/bus colour tables, and the
pre-flight checklist.

The same standard is available in English at
[references/style-guide.en.md](references/style-guide.en.md). Use whichever
matches the language of the request; the rules are identical.

## Workflow

1. If the input is a PDF, run:

   ```bash
   python scripts/pdf_prep.py <schematic.pdf> --out <work-dir> --dpi 200
   ```

   Read the page PNGs for wiring and annotations. Use `<work-dir>/<name>_text.txt`
   to search net names, reference designators, values, and page locations.

2. Decide the diagram type:

   - Use a power tree for source-to-rail-to-load flows, converters, switches,
     voltage domains, and current budgets.
   - Use a system block diagram for board boundaries, buses, interfaces, and
     subsystem relationships.

3. Create a Python figure module that imports `diagramlib` and exposes
   `build() -> Fig`. Copy the closest example before inventing a layout:

   - [example_power_tree.py](assets/examples/example_power_tree.py)
   - [example_block_diagram.py](assets/examples/example_block_diagram.py)

   Use the helper methods rather than raw primitives where one fits:
   `converter()` for power-path blocks, `block()` for peripherals,
   `bus()` / `branch()` for rails, `link()` for a coloured bus arrow with a
   white-backed label, and `legend_box()` / `legend_box_2col()` /
   `title_block()` for the furniture.

4. Build the diagram:

   ```bash
   python scripts/build.py <figure.py> --out <out-dir> --name <name> --title <title>
   ```

5. Inspect the generated PNG at full size. Check for clipped text, overlapping
   labels, ambiguous arrow direction, disconnected endpoints, and crossings
   that obscure the intended flow. Fix the figure definition and rebuild.

## Required Level of Detail

The bundled examples are **finished figures, not sketches** - copy one and keep
its density. A thin, three-box draft is the most common way a run goes wrong,
so calibrate against the examples before considering the figure done:

| Figure | Expected content |
| --- | --- |
| Power tree | every input source; the charger with its charge path and switch; one rail per voltage domain; **every** converter stage; **every** load with its per-branch current label; the sub-board sub-tree; the voltage-domain legend |
| Block diagram | board regions and the connector band; **every** controller and subsystem block with its interface list; one labelled link per bus; the shared-bus legend; the title block |

Concretely, a delivered figure of this family carries roughly 30 device boxes,
35+ links and 10+ labelled branches on a 2200 px canvas. If the result has a
handful of generic boxes such as "SoC", "MCU" or "Wi-Fi module" where the
schematic gives real part numbers, it is under-specified: go back to the
page PNGs and the text dump and fill in the actual refdes, values, rail names
and bus indices.

## Hard Rules for Every Figure

These came out of real review feedback; breaking one means redoing the figure.

- **No dangling ends.** Every rail, branch and link must terminate on another
  line, a device box, or a connector boundary. A trunk that extends past its
  last branch reads as a broken connection.
- **No crossings.** Re-route long cross-board nets through a connector band, or
  reorder the blocks, instead of letting two nets cross.
- **Orthogonal only.** Horizontal and vertical segments; no diagonals.
- **Arrowheads stay visible.** Keep the fixed-size marker (16 units,
  `userSpaceOnUse`); never let the arrow scale with a thick rail, or it becomes
  a black wedge that swallows the line. Leave roughly 50 px on short branches.
- **Labels sit on a white backing** (`bg=True`) so they never straddle a line.
- **Shared buses get an index and a colour.** When one physical I2C/UART bus
  carries several devices, number it (`I2C-1`, `I2C-2`, ...), colour every
  segment of that bus the same, label the line with the index plus a
  shared/exclusive tag, and add a bus-group legend box.
- **Verify control-signal ownership before drawing a link.** A control or
  status net belongs to the device that actually drives or reads it - not to
  the main SoC by default, and not to the board the part happens to sit on.
  Trace the net to a page and refdes first. LED / IR-CUT / light-sensor
  controls are routinely owned by a wireless module, and mechanical or tamper
  inputs are often read by an I/O expander. Section 5.1 of the style guide
  lists the traps already hit on this project.

## Verifying a Figure

`build.py` writes SVG, VSDX and VDX even when rasterising fails, so a successful
exit code does not prove the picture is correct. After every build:

1. Render and inspect the PNG at full size (or the SVG when no browser exists).
2. Walk the pre-flight checklist in the style guide.
3. Check the Visio package when the user will edit it:

   ```python
   import zipfile, xml.dom.minidom
   z = zipfile.ZipFile("out/figure.vsdx")
   for part in z.namelist():
       xml.dom.minidom.parseString(z.read(part))   # raises on malformed XML
   ```

   State plainly that the file could not be opened in Visio itself when Visio
   is not installed on this machine; do not claim it was visually confirmed.

## Outputs and Requirements

- `export()` always writes editable SVG, VSDX, and VDX files.
- PNG export uses a local Edge or Chrome installation. If PNG cannot be
  generated, inspect the SVG and report that limitation instead of treating the
  build as a complete visual verification.
- `pdf_prep.py` needs Poppler for page rasterisation and either `pypdf` or
  `pdfplumber` for text extraction. Use the page images when the PDF has no
  usable text layer.
- VSDX and VDX are XML representations intended for Visio-compatible editing;
  they are not a substitute for visual inspection of the rendered diagram.

## Diagram Library

Read `scripts/diagramlib.py` when you need the available primitives or exact
signatures. Common building blocks include `text`, `rect`, `block`, `line`,
`branch`, `bus`, `converter`, `legend_box`, `legend_box_2col`, and
`title_block`.

Use the existing color constants for voltage domains and bus groups. Add a
legend when color or numbering carries meaning.
