---
name: schematic-to-diagram
description: Convert circuit schematics or structured hardware descriptions into clean system block diagrams and power trees, exporting SVG, PNG, VSDX, and VDX. Use when the user asks to turn a schematic PDF into a block diagram or power tree, simplify signal or power flow, produce a Visio-compatible diagram, publish diagrams to a Feishu/Lark cloud document, or create native editable Feishu whiteboards. Do not use for detailed PCB layout, netlist editing, or datasheet parameter lookup.
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

For Feishu/Lark cloud-document delivery, read
[references/lark-integration.md](references/lark-integration.md) (English:
[references/lark-integration.en.md](references/lark-integration.en.md)). It
covers native whiteboard publishing, the known conversion traps, and the
0-gap geometry acceptance check.

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
   `bus()` / `branch()` for rails, `link()` for a coloured bus arrow with an
   on-line label, and `legend_box()` / `legend_box_2col()` /
   `title_block()` for the furniture.

4. Build the diagram:

   ```bash
   python scripts/build.py <figure.py> --out <out-dir> --name <name> --title <title>
   ```

   The build runs `diagramlib.validate()` and prints a style check. **A figure
   is not done until it reports `style check: clean`** - the check catches
   dangling endpoints, endpoints inside a box, nets crossing each other, and
   nets passing through a box. Use `--strict` to make warnings fail the build.

5. Inspect the generated PNG at full size. Check for clipped text, overlapping
   labels, signal direction, control ownership, label-induced line gaps,
   disconnected endpoints, and crossings that obscure the intended flow. Fix
   the figure definition and rebuild.

6. Optional Feishu/Lark delivery: when the user wants an editable cloud
   document, publish the SVG as a native whiteboard. Follow
   [references/lark-integration.md](references/lark-integration.md). Read the
   board back and run `python scripts/lark_board_check.py board.json`; it must
   report `clean`, with 0 dangling endpoints and 0 embedded svg/image nodes.

## Required Level of Detail

The bundled examples are **finished figures, not sketches** - copy one and keep
its density. A thin, three-box draft is the most common way a run goes wrong,
so calibrate against the examples before considering the figure done:

| Figure | Expected content |
| --- | --- |
| Power tree | every input source; the charger with its charge path and switch; one rail per voltage domain; **every** converter stage; **every** named load in its own box with voltage domain and current budget; a left-to-right layered tree when the hierarchy is the message; the sub-board sub-tree; the voltage-domain legend |
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
- **Labels never break a line.** Put the label directly on the line with the
  line's built-in label, or offset it beside the line. A white backing is only
  allowed when it does not mask or interrupt the net; a visible gap looks like
  an open circuit.
- **Arrow direction follows the signal, not the layout.** Trace every one-way
  control or status net to its driver and receiver before drawing it. For a
  bidirectional bus (I2C, UART if bidirectional, SDIO data, and similar), do
  not use a misleading one-way arrow: omit the arrowhead or use a clearly
  two-way indicator and label it `bidirectional` / `双向`.
- **Shared buses get an index and a colour.** When one physical I2C/UART bus
  carries several devices, number it (`I2C-1`, `I2C-2`, ...), colour every
  segment of that bus the same, label the line with the index plus a
  shared/exclusive tag, and add a bus-group legend box.
- **Furniture boxes have a fixed footprint.** Within one sheet, the legend box
  and title block must use the same width and height; never stretch them to fill
  the remaining width. Default A4 landscape footprint at 2339x1654 is
  `650x160`; default A3 landscape footprint at 3308x2338 is `900x220`.
- **Layered power-tree layout.** When the source-to-rail hierarchy is the
  message, lay the power tree out left to right: one hierarchy level per
  column, siblings ordered top to bottom, and the next level in the next
  column to the right. Converters, rails and loads each occupy their own
  column.
- **One box per named load.** Give every peripheral/load its own box carrying
  name, function, voltage domain and current budget. Do not hide several named
  loads in one text list; Feishu users cannot select, move or recolour them
  individually.
- **Zero-gap connectors.** Arrow tips and trunk ends must land exactly on the
  target box border or on another line. A trunk must span the first through
  the last branch row; a branch below the trunk end reads as a broken
  connection. A 1 px gap is a defect.
- **Native arrowheads for editable targets.** When the output becomes a
  Feishu/Lark whiteboard, use native connector arrows (`triangle_arrow`), not
  embedded SVG triangles. Embedded arrowheads are not individually editable
  and commonly leave 3-9 px gaps after conversion.
- **Verify control-signal ownership before drawing a link.** A control or
  status net belongs to the device that actually drives or reads it - not to
  the main SoC by default, and not to the board the part happens to sit on.
  Trace the net to a page and refdes first. LED / IR-CUT / light-sensor
  controls are routinely owned by a wireless module or main-board I/O
  expander, and mechanical or tamper inputs are often read by an I/O expander
  even when the sensor sits on another board. In this project, IR-CUT control
  comes from the main-board IO expander to the SOC-board AP1511B, Hall output
  returns from the SOC board to the main-board IO expander, and SOC power is
  enabled from the main board. Section 5.1 of the style guide lists the traps
  already hit on this project.

## Verifying a Figure

`build.py` writes SVG, VSDX and VDX even when rasterising fails, so a successful
exit code does not prove the picture is correct. After every build:

1. Render and inspect the PNG at full size (or the SVG when no browser exists).
2. Walk the pre-flight checklist in the style guide.
3. For a Feishu/Lark whiteboard, read the board back and run the geometry
   check:

   ```bash
   lark-cli whiteboard +query --whiteboard-token <token> \
     --output_as raw --format json > board.json
   python scripts/lark_board_check.py board.json
   ```

   It must report `clean` with 0 dangling endpoints, 0 non-orthogonal
   segments and 0 embedded svg/image nodes.

   After changing `scripts/lark_board_check.py`, run
   `python -m unittest discover -s tests -v`.

4. Check the Visio package when the user will edit it:

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
- Feishu/Lark delivery: a native whiteboard is the editable form. Do not
  leave a PNG behind when the user asked for an editable board; verify the
  board with `scripts/lark_board_check.py` and `+query --output_as image`.

## Diagram Library

Read `scripts/diagramlib.py` when you need the available primitives or exact
signatures. Common building blocks include `text`, `rect`, `block`, `line`,
`branch`, `bus`, `converter`, `legend_box`, `legend_box_2col`, and
`title_block`. When validating a Feishu/Lark whiteboard read-back, use
`scripts/lark_board_check.py`.

Use the existing color constants for voltage domains and bus groups. Add a
legend when color or numbering carries meaning.
