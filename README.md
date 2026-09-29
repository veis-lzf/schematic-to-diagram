# schematic-to-diagram

把电路原理图（PDF）转成 **系统框图** 和 **电源树**，一次输出四种格式：
`SVG`（矢量源）、`PNG`（预览）、`VSDX`（Visio 2013+ 可编辑）、`VDX`（Visio 2003–2010）。

一份坐标数据同时驱动四种输出，因此图片和 Visio 文件不会不一致。

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
- 标注加白色底衬，不压线
- 共用总线（I2C / UART 等）必须编号 + 配色 + 说明框

## 目录

```
schematic-to-diagram/
├── SKILL.md                    工作流、硬性规则、验证清单
├── references/
│   ├── style-guide.md          完整绘图规范（中文）
│   └── style-guide.en.md       same standard in English
├── scripts/
│   ├── diagramlib.py           渲染库（Fig + SVG/VSDX/VDX 导出器）
│   ├── build.py                命令行入口
│   └── pdf_prep.py             PDF → 逐页 PNG + 文本
└── assets/examples/            可直接套用的电源树 / 框图模板
```

## 说明

`.vsdx` / `.vdx` 由脚本按 OOXML 包结构生成，已校验包内 XML 合法性；
生成环境若未安装 Visio，则无法在 Visio 中实际打开确认。
