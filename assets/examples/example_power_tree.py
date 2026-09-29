"""Full-detail power tree -- the calibration reference for a finished figure.

This is the level of detail a delivered power tree is expected to reach:
every input, every converter, every rail, every load, real reference
designators and values, and a current label on each branch. A draft showing
three converters and three loads is a sketch, not a deliverable -- expand it
against the schematic before handing it over.

How to read it as a template:

* left column .......... input sources
* second column ........ charger / charge path
* centre vertical ...... VBATTERY then VCC_SYS, one thick rail per domain
* third column ......... stage-2 converters hanging off the system rail
* right column ......... loads, grouped by the rail that feeds them
* bottom band .......... sub-board sub-tree fed through the connector
* bottom right ......... voltage-domain legend

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
    f = Fig(2200, 1500)
    f.text(40, 46, "Video Doorbell Vision 电源树（Power Tree）", 26, INK, True)
    f.text(40, 76, "BLE 板为电源主干（充电 / 总开关 / 电池 / 3.3V 与 5V 域）；"
                   "SOC 板经 BTB 取电并在板内生成 CPU 各路电源", 13, GRAY)

    # ---------------------------------------------------------- 输入源 --
    for i, t in enumerate(["Type-C 5V\n充电输入", "太阳能板\nSOLAR_3V3",
                           "内机 Pogo\n6.2V DC IN"]):
        f.rect(60, 200 + i * 90, 240, 70, t, "#FFFFFF", "#000000", 1, 12,
               INK, True, 6)
        f.line(300, 235 + i * 90, 340, 235 + i * 90, INK, 2.6, True)

    # -------------------------------------------------------- 充电管理 --
    f.converter(340, 190, 300, 240,
                "U1 IU5987T\n充电管理\n4.25V / 1.5A\nMPPT 4.6V\nη≈90%")
    f.branch(640, 310, 700, 310, VBAT)

    # --------------------------------------------------------- VBATTERY --
    # 母线两端都落在分支点上（上接电池支路、下接 Q1 支路），不留悬空端
    f.bus(700, 222, 700, 480, VBAT, 8)
    f.text(712, 216, "VBATTERY　3.0–4.25V", 13, AMBER_D, True)
    f.branch(700, 222, 1890, 222, VBAT, 4, "3.0–4.25V_2.0A", 11, AMBER_D, 0, -9)
    f.rect(1890, 186, 280, 72, "电池包 J2\n3.0–4.25V · 2A 充 / 3A 放",
           "#FFFFFF", "#000000", 1, 12, INK, True, 6)

    # ----------------------------------------------- Q1 总开关 → VCC_SYS --
    f.branch(700, 480, 760, 480, VBAT)
    f.converter(760, 440, 300, 80, "Q1 SSC8415GS6\n系统总开关 ≤2.5A")
    f.branch(1060, 480, 1120, 480, VBAT)
    f.bus(1120, 480, 1120, 1300, VBAT, 8)
    f.text(1132, 474, "VCC_SYS　3.0–4.25V ≤2.5A", 13, AMBER_D, True)

    # ------------------------------------------------------ 二级转换器 --
    for y, t in [(530, "U28 EA8103A\n3.3V / 2.0A\nη≈90%"),
                 (660, "U10 SY7092SUC\n5.0V / 2.0A\nη≈85%"),
                 (800, "U22 LP6221ASPF\n9.2V / 1.2A"),
                 (940, "U27 LP3110B6F\n5.0V / 0.5A"),
                 (1080, "U21 QX7135E20\n恒流 300mA"),
                 (1220, "BTB J3→J12\n→ SOC 板取电")]:
        f.branch(1120, y, 1200, y, VBAT)
        f.converter(1200, y - 40, 300, 80, t)

    # 3.3V 域：一条绿色母线带 5 个负载
    f.branch(1500, 530, 1560, 530, V33)
    f.bus(1560, 320, 1560, 620, V33, 7)
    f.text(1572, 316, "3.3V", 13, V33, True)
    for name, lab, y in [("BLE 主控 RTL8762C", "3.3V_0.50A", 320),
                         ("APT32S1028（按键 / LED）", "3.3V_0.10A", 380),
                         ("Si512 NFC 读卡", "3.3V_0.10A", 440),
                         ("CW2015 电量计", "3.3V_0.05A", 500),
                         ("AIW6262 Wi-Fi 3.3V", "3.3V_0.30A", 560)]:
        f.branch(1560, y, 1660, y, V33, 4, lab, 10, -9)
        f.rect(1660, y - 24, 350, 48, name, "#FFFFFF", "#000000", 1, 11, INK,
               True, 6)

    # 其余各域负载（1.8V 由 3.3V 域的 LDO 二次变换而来）
    for name, lab, y, col in [
            ("光敏 D9（U20 TMI6030-18）", "1.8V_0.05A", 620, V18),
            ("Wi-Fi 模组 PA（AIW6262）", "5V_1.20A", 660, V5),
            ("人脸识别模组", "9.2V_0.60A", 800, V92),
            ("门铃指示 / 数字按键背光", "5V_0.20A", 940, V5),
            ("红外补光灯 ×6", "0.30A", 1080, V5),
            ("SOC 板电源（4×DCDC + 3×LDO）", "3.0–4.25V_2.0A", 1220, VBAT)]:
        f.branch(1560 if y == 620 else 1500, y, 1660, y, col, 4, lab, 10, -9)
        f.rect(1660, y - 24, 350, 48, name, "#FFFFFF", "#000000", 1, 11, INK,
               True, 6)

    # --------------------------------- 子板子树（经连接器引入 VCC_SYS）--
    f.text(60, 1276, "SOC 板内部电源（经 BTB 引入 VCC_SYS）", 14, BLUE, True)
    f.bus(1120, 1300, 190, 1300, VBAT, 7)
    f.text(600, 1291, "VCC_SYS → SOC 板", 11, AMBER_D, True, "center", True)
    for t, x in [("U30 JW5250A\n→ CPU_3V3 1A", 70),
                 ("U4 JW5250A\n→ CPU_0V8 1A", 330),
                 ("U6 JW5250A\n→ CPU_1V8 1A", 590),
                 ("U5 JW5250A\n→ CPU_1V5 1A", 850)]:
        f.branch(x + 120, 1300, x + 120, 1360, VBAT)
        f.converter(x, 1360, 240, 66, t)
    f.text(60, 1452, "二级 LDO：U31 LR6231B33M → VDD_3V3（IRCUT / 音频）· "
                     "U14 TMI6030-28 → 2V8_SENSOR · U15 TMI6030-18 → "
                     "1V8_SENSOR（EN = SENSOR_EN）", 12, INK)
    f.text(60, 1478, "上电顺序 POR：0V8 → 3V3 → 1V8 → 1V5（四路 EN 并联 "
                     "WIFI-CPU_PWR_EN，需实测）　·　待确认：Sensor DVDD(1.5V) "
                     "来源 / VBATTERY 仅 1 针过 BTB 的载流能力", 12, "#B45309")

    # ------------------------------------------------------------- 图例 --
    f.legend_box(1450, 1276, 700, 194, "电压域图例",
                 [(V92, "9.2V"), (V5, "5V"), (VBAT, "3.0–4.25V"),
                  (V33, "3.3V"), (V18, "1.8V"), (V15, "1.5V"),
                  (V08, "0.8V")], sw=7, row_h=36)
    return f
