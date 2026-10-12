# Feishu / Lark Cloud Doc and Native Whiteboard Delivery

Use this route when a generated system block diagram or power tree must be
placed in a Feishu/Lark cloud document and remain editable inside Feishu.

## 1. Choose the delivery form

| Goal | Delivery |
| --- | --- |
| Read, archive or print only | Insert a PNG with `docs +media-insert` |
| Edit inside Feishu | Use a native whiteboard: `<whiteboard type="blank">` |
| Convert an existing picture | Insert a blank whiteboard, write it, then delete the old image block |

One figure per whiteboard. Keep the block diagram and power tree in separate
whiteboards instead of combining them.

## 2. Standard workflow

1. Build the figure locally:

   ```bash
   python scripts/build.py <figure.py> --out <out-dir> --name <name> --title <title>
   ```

   The SVG produced by `build.py` is the whiteboard conversion source; the PNG
   is only for visual inspection.

2. Insert a blank whiteboard in the Feishu document:

   ```bash
   lark-cli docs +update --api-version v2 --doc <doc-id> \
     --command block_insert_after --block-id <anchor-block-id> \
     --content '<whiteboard type="blank"></whiteboard>' --format json
   ```

   Read the returned `data.document.new_blocks[]`; the entry with
   `block_type == "whiteboard"` carries the `block_token` to write into.

3. Convert the SVG to native whiteboard nodes:

   ```bash
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg --check
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg \
     --to openapi --format json > diagram.json
   ```

4. Dry-run before writing:

   ```bash
   cat diagram.json | lark-cli whiteboard +update \
     --whiteboard-token <board-token> \
     --source - --input_format raw \
     --idempotent-token <unique-10-char-min-string> \
     --overwrite --dry-run --as user
   ```

   A blank board reports 0 deleted nodes. When overwriting an existing board,
   if dry-run reports `XX whiteboard nodes will be deleted`, first confirm those
   nodes belong to this task.

5. Write for real:

   ```bash
   cat diagram.json | lark-cli whiteboard +update \
     --whiteboard-token <board-token> \
     --source - --input_format raw \
     --idempotent-token <unique-10-char-min-string> \
     --overwrite --as user
   ```

6. Read back and verify:

   ```bash
   lark-cli whiteboard +query --whiteboard-token <board-token> \
     --output_as raw --format json > board.json
   python scripts/lark_board_check.py board.json

   lark-cli whiteboard +query --whiteboard-token <board-token> \
     --output_as image --output board.jpg --overwrite
   ```

   `lark_board_check.py` must report `clean`. Inspect `board.jpg` for dangling
   lines, wrapped text and occluded labels.

7. Delete the old picture block only after step 6 passes:

   ```bash
   lark-cli docs +update --api-version v2 --doc <doc-id> \
     --command block_delete --block-id <old-image-block-id>
   ```

## 3. Whiteboard hardening rules

These rules come from real review rework. Check them before writing a board.

1. **Prefer native arrows.** Use
   `connector.end.arrow_style = "triangle_arrow"` instead of embedded SVG
   triangles. Embedded nodes cannot be edited individually and often leave a
   3-9 px gap after SVG conversion.
2. **Zero-gap endpoints.** Every connector start and end must land on a shape
   edge or on another connector segment. An arrow tip must touch the target box
   border exactly; a few missing pixels read as a broken wire.
3. **Full-span trunk.** A trunk must cover the first through the last branch
   row. If the drawing library only emits a partial trunk, split it into a
   feeder plus a full-span trunk, otherwise lower branches float.
4. **One box per load.** Give every named peripheral/load its own box with its
   voltage domain and current budget. Do not replace it with a text list inside
   one large box; Feishu users need to drag, copy and recolour each item.
5. **Layered tree left to right.** Keep one hierarchy level per column, ordered
   top to bottom; advance the next level to the right. Converters, rails and
   loads each occupy their own column.
6. **Do not paint a full-canvas background.** Feishu paints nodes in reverse
   creation order. If a full-canvas background rectangle is used, set an
   explicit `z_index`; otherwise it covers all content. Omitting the background
   is safer.
7. **Leave text width margin.** Feishu font metrics are roughly 10%-25% wider
   than the SVG measurer. Widen text nodes by about `x1.25 + 12px` and re-read
   the rendered image to confirm no wrapping.
8. **Turning-point coordinate convention.** `turning_points` are relative to
   the connector bbox origin, not to the start point. Restore them as
   `(node.x + tp.x, node.y + tp.y)`.
9. **No non-native nodes.** The final board must contain 0 `svg` / `image` /
   `picture` / `bitmap` nodes. `lark_board_check.py` enforces this.

## 4. Acceptance checklist

- [ ] The blank board was actually filled, not left empty
- [ ] `board.json` contains 0 embedded svg/image/picture/bitmap nodes
- [ ] `python scripts/lark_board_check.py board.json` reports `clean`
- [ ] `+query --output_as image` shows no dangling line, wrapped text or
      occluded label
- [ ] Each hierarchy level shares one column, ordered top to bottom, with the
      next level to the right
- [ ] Every named load has its own box with voltage domain and current budget
- [ ] The old PNG was deleted and only the required whiteboard remains
