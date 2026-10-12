# 飞书 / Lark 云文档与原生画板对接

适用场景：把 `schematic-to-diagram` 生成的系统框图或电源树放进飞书云文档，
并且要求图在飞书内可以直接编辑。

## 一、先选交付形态

| 目标 | 交付方式 |
| --- | --- |
| 只阅读、归档、打印 | 插入 PNG，使用 `docs +media-insert` |
| 需要在飞书内继续编辑 | 使用飞书原生画板 `<whiteboard type="blank">` |
| 既有图要改为可编辑 | 插入空白画板写入，确认后再删除旧图片块 |

一张图一个画板。框图和电源树分开，不要把多张图塞进同一个画板。

## 二、标准流程

1. 本地出图：

   ```bash
   python scripts/build.py <figure.py> --out <out-dir> --name <name> --title <title>
   ```

   `build.py` 生成的 SVG 是画板转换源；PNG 只用于肉眼检查。

2. 在飞书文档中插入空白画板：

   ```bash
   lark-cli docs +update --api-version v2 --doc <doc-id> \
     --command block_insert_after --block-id <anchor-block-id> \
     --content '<whiteboard type="blank"></whiteboard>' --format json
   ```

   从返回的 `data.document.new_blocks[]` 里取 `block_type == "whiteboard"` 的
   `block_token`，作为后续写入目标。

3. SVG 转飞书画板原生节点：

   ```bash
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg --check
   npx -y @larksuite/whiteboard-cli@^0.2.11 -i diagram.svg -f svg \
     --to openapi --format json > diagram.json
   ```

4. 写入前先 dry-run：

   ```bash
   cat diagram.json | lark-cli whiteboard +update \
     --whiteboard-token <board-token> \
     --source - --input_format raw \
     --idempotent-token <10+字符唯一串> \
     --overwrite --dry-run --as user
   ```

   空白画板正常显示 0 个删除节点；覆盖已有画板时，输出里若出现
   `XX whiteboard nodes will be deleted`，必须先确认这些节点确实属于本次任务。

5. 正式写入：

   ```bash
   cat diagram.json | lark-cli whiteboard +update \
     --whiteboard-token <board-token> \
     --source - --input_format raw \
     --idempotent-token <10+字符唯一串> \
     --overwrite --as user
   ```

6. 回读验证：

   ```bash
   lark-cli whiteboard +query --whiteboard-token <board-token> \
     --output_as raw --format json > board.json
   python scripts/lark_board_check.py board.json

   lark-cli whiteboard +query --whiteboard-token <board-token> \
     --output_as image --output board.jpg --overwrite
   ```

   `lark_board_check.py` 必须报 `clean`；`board.jpg` 必须目视无断线、无折行、无遮挡。

7. 旧图片块只在第 6 步通过后删除：

   ```bash
   lark-cli docs +update --api-version v2 --doc <doc-id> \
     --command block_delete --block-id <old-image-block-id>
   ```

## 三、飞书画板硬化规则

这些规则来自真实评审返工，写入画板前按此检查：

1. **原生箭头优先**：箭头使用 `connector.end.arrow_style = "triangle_arrow"`，
   不要用嵌入式 SVG 三角形。嵌入节点不可单独编辑，且从 SVG 转换后常常
   残留 3–9 px 缺口。
2. **端点 0 px 缺口**：每条 connector 的起点和终点都必须落在形状边界或
   另一条连接线上。箭头尖端必须顶住目标框边，不允许差几个像素。
3. **干线全跨距**：一条干线必须从第一条支路覆盖到最后一条支路。
   如果生成库只画到中间某一行，必须拆成“馈线 + 全跨距干线”，否则下方
   支路会悬空。
4. **每负载独立框**：每个具名外设/负载独立成框，框内写电压域和电流预算；
   不要用一个框里的文字列表代替，否则飞书里不能单独拖动、复制或改色。
5. **分层树从左到右**：同一层级的节点放在同一列、自上而下排列；下一层
   进入右列。转换器、电源域、负载各占自己的列。
6. **不要整幅白底**：飞书画板按创建顺序倒序绘制节点；如果画整幅白底矩形，
   必须显式设置 `z_index`，否则白底会盖住全部内容。更安全的做法是不画
   整幅白底。
7. **文本宽度留余量**：飞书字体度量比 SVG 解析器宽约 10%–25%。
   文本节点宽度建议按 `×1.25 + 12px` 放宽，并回读 PNG/JPG 确认不折行。
8. **折点坐标约定**：`turning_points` 是相对节点 bbox 原点，不是相对
   start 点。重算折线时按 `(node.x + tp.x, node.y + tp.y)` 还原。
9. **不要混入非原生节点**：最终画板中 `svg` / `image` / `picture` /
   `bitmap` 节点数必须为 0；`lark_board_check.py` 会检查这一项。

## 四、验收清单

- [ ] 空白画板已写入真实内容，不是空板
- [ ] `board.json` 中嵌入 svg/image/picture/bitmap 节点为 0
- [ ] `python scripts/lark_board_check.py board.json` 报 `clean`
- [ ] `+query --output_as image` 目视无断线、无折行、无遮挡
- [ ] 每层节点在同一列，同层自上而下，下一层在右列
- [ ] 每个具名负载独立成框，框内有电压域和电流预算
- [ ] 旧 PNG 已删除，文档中只保留需要的画板
