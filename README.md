# schematic-to-diagram

把电路原理图（PDF）转成 **系统框图** 和 **电源树**，一次输出四种格式：
`SVG`（矢量源）、`PNG`（预览）、`VSDX`（Visio 2013+ 可编辑）、`VDX`（Visio 2003–2010）。

一份坐标数据同时驱动四种输出，因此图片和 Visio 文件不会不一致。
可选把图发布到 **飞书 / Lark 云文档**，并转为可直接编辑的原生画板。

## 安装

把整个目录放到 Codex 的 skills 目录下即可：

```bash
# 项目级
<repo>/.agents/skills/schematic-to-diagram/
# 或用户级
~/.codex/skills/schematic-to-diagram/
```

## 用法

```bash
# 1. 原理图 PDF → 逐页 PNG + 文本层
python scripts/pdf_prep.py schematic.pdf --out work --dpi 200

# 2. 按参考示例写一份图定义（暴露 build() -> Fig）
cp assets/examples/example_power_tree.py my_power_tree.py

# 3. 出图
python scripts/build.py my_power_tree.py --out out --name my_power_tree

# 4.（可选）发布到飞书云文档为原生可编辑画板
#    见 references/lark-integration.md
```

依赖：Poppler（`pdftoppm`，用于光栅化）、`pypdf` 或 `pdfplumber`（文本层）、
本机 Edge 或 Chrome（PNG 栅格化）。

## 绘图规范

完整规范：[中文](references/style-guide.md) ／ [English](references/style-guide.en.md)。
核心硬性规则：

- 连线不允许断开（母线两端必须落在分支点或器件上）
- 不允许交叉；跨板长线走连接器条带中转
- 全横平竖直，禁止斜线
- 箭头固定尺寸，不随线宽放大（否则会变成盖住连接线的黑三角）
- 箭头方向按真实信号流；双向总线标注“双向”，不得画成误导性的单向箭头
- 标签不得遮断线路：在线标注直接显示，偏移标注才可使用白底且不能遮线
- 控制 / 状态信号必须追到真实驱动端，不能默认归主控
- 共用总线（I2C / UART 等）必须编号 + 配色 + 说明框
- 图例框与标题栏固定同一尺寸，不随空白横向拉长

## 目录

```
schematic-to-diagram/
├── SKILL.md                    工作流、硬性规则、验证清单
├── references/
│   ├── style-guide.md          完整绘图规范（中文）
│   ├── style-guide.en.md       same standard in English
│   ├── lark-integration.md     飞书云文档 / 原生画板对接流程
│   └── lark-integration.en.md  same workflow in English
├── scripts/
│   ├── diagramlib.py           渲染库（Fig + SVG/VSDX/VDX 导出器）
│   ├── build.py                命令行入口
│   ├── pdf_prep.py             PDF → 逐页 PNG + 文本
│   └── lark_board_check.py     飞书画板几何验收（断线 / 非正交 / 嵌入节点）
├── tests/
│   └── test_lark_board_check.py 画板几何验收回归测试
└── assets/examples/            可直接套用的电源树 / 框图模板
```

## 说明

`.vsdx` / `.vdx` 由脚本按 OOXML 包结构生成，已校验包内 XML 合法性；
生成环境若未安装 Visio，则无法在 Visio 中实际打开确认。

## 飞书 / Lark 云文档交付

需要让图在飞书内直接编辑时，不要插入 PNG，改用飞书原生画板：

1. `build.py` 输出 SVG；
2. 在文档插入 `<whiteboard type="blank">`，取 `block_token`；
3. 用 `@larksuite/whiteboard-cli` 把 SVG 转成 OpenAPI JSON；
4. `lark-cli whiteboard +update --overwrite --dry-run` 检查后正式写入；
5. 回读 `--output_as raw`，运行 `python scripts/lark_board_check.py board.json`；
6. 回读 `--output_as image` 目视确认无断线、无折行、无遮挡；
7. 通过后删除旧 PNG 块。

完整命令、硬化规则和验收清单见 [references/lark-integration.md](references/lark-integration.md)。

## 测试

```bash
python -m unittest discover -s tests -v
```
