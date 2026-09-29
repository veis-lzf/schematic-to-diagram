"""Example power tree (condensed). Copy and adapt to the new schematic.

Run:  python scripts/build.py assets/examples/example_power_tree.py --out ./out
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
from diagramlib import *   # noqa: F401,F403

NAME = "example_power_tree"
TITLE = "电源树"


def build():
    f = Fig(1800, 1000)
    f.text(40, 46, "Power Tree（示例）", 26, INK, True)

    # --- 输入源 -----------------------------------------------------------
    for i, t in enumerate(["Type-C 5V\n充电输入", "太阳能板\nSOLAR_3V3",
                           "内机 Pogo\n6.2V DC IN"]):
        f.rect(60, 140 + i * 90, 240, 70, t, "#FFFFFF", "#000000", 1, 12,
               INK, True, 6)
        f.line(300, 175 + i * 90, 334, 175 + i * 90, INK, 2.6, True)

    # --- 充电器 -----------------------------------------------------------
    f.converter(340, 130, 300, 240, "U1 IU5987T\n充电管理\n4.25V / 1.5A\nη≈90%")
    f.branch(640, 250, 698, 250, VBAT)

    # --- VBATTERY 母线（两端都落在分支点上，不留悬空端）-------------------
    f.bus(700, 200, 700, 420, VBAT, 8)
    f.text(712, 194, "VBATTERY　3.0–4.25V", 13, AMBER_D, True)
    f.branch(700, 200, 1520, 200, VBAT, 4, "3.0–4.25V_2.0A", 11, -9)
    f.rect(1530, 166, 240, 68, "电池包 J2\n3.0–4.25V · 2A/3A", "#FFFFFF",
           "#000000", 1, 12, INK, True, 6)

    # --- Q1 总开关 → VCC_SYS ---------------------------------------------
    f.branch(700, 420, 756, 420, VBAT)
    f.converter(760, 380, 300, 80, "Q1 SSC8415GS6\n系统总开关 ≤2.5A")
    f.branch(1060, 420, 1118, 420, VBAT)
    f.bus(1120, 420, 1120, 760, VBAT, 8)
    f.text(1132, 414, "VCC_SYS　≤2.5A", 13, AMBER_D, True)

    # --- 一级转换 + 负载 ---------------------------------------------------
    rows = [(460, "U28 EA8103A\n3.3V / 2.0A\nη≈90%", V33, "VDD_3V3",
             "3.3V_0.5A", "BLE 主控 RTL8762C"),
            (570, "U10 SY7092SUC\n5.0V / 2.0A\nη≈85%", V5, "VDD5V_IN",
             "5V_1.2A", "Wi-Fi 模组 PA"),
            (680, "U22 LP6221ASPF\n9.2V / 1.2A", V92, "9V2", "9.2V_0.6A",
             "人脸识别模组")]
    for y, blk, rail, tag, cur, load in rows:
        f.branch(1120, y, 1198, y, VBAT)
        f.converter(1200, y - 40, 300, 80, blk)
        f.branch(1500, y, 1558, y, rail, 4, cur, 10, -9)
        f.rect(1562, y - 16, 100, 32, tag, rail, rail, 1, 13, "#FFFFFF",
               True, 7)
        f.branch(1662, y, 1680, y, rail, 4)
        f.rect(1680, y - 24, 110, 48, load, "#FFFFFF", "#000000", 1, 11, INK,
               True, 6)

    f.legend_box(1200, 790, 540, 170, "电压域图例",
                 [(V92, "9.2V"), (V5, "5V"), (VBAT, "3.0–4.25V"),
                  (V33, "3.3V")])
    return f
