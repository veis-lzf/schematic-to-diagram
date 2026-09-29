"""Example system block diagram (condensed). Copy and adapt.

Run:  python scripts/build.py assets/examples/example_block_diagram.py --out ./out
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "..", "..", "scripts"))
from diagramlib import *   # noqa: F401,F403

NAME = "example_block_diagram"
TITLE = "系统框图"


def build():
    f = Fig(1800, 1200)
    f.text(40, 46, "System Block Diagram（示例）", 24, INK, True)
    SW = 2.4

    # --- 上层：主控板 ------------------------------------------------------
    f.rect(30, 90, 1740, 420, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 118, "Main board", 15, BLUE, True)
    f.rect(700, 140, 420, 340,
           "SoC\n主控\n\nMIPI CSI · USB2.0\nSFC0 · MSC1(SDIO)\nI2C · PWM · GPIO",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)
    left = [("SC3336 摄像头", "MIPI 2-lane ＋ I2C-S1", "MIPI 2-lane", 160,
             BUS["MIPI"]),
            ("NOR Flash", "SPI-1（SFC0，独占）", "SPI-1（SFC0，独占）", 280,
             BUS["SPI"])]
    right = [("电源", "CPU 0V8 / 1V8 / 1V5 / 3V3", "CPU 0V8 / 1V8 / 1V5 / 3V3",
              160, BUS["PWR"]),
             ("USB / 调试", "Type-C 下载", "USB2.0 / UART-1", 280, BUS["USB"])]
    for name, sub, lab, y, col in left:
        f.block(60, y, 360, 96, name, sub)
        f.line(422, y + 48, 698, y + 48, col, SW, True, lab, 10, col, 0, -9)
    for name, sub, lab, y, col in right:
        f.block(1380, y, 360, 96, name, sub)
        f.line(1122, y + 48, 1378, y + 48, col, SW, True, lab, 10, col, 0, -9)

    # --- BTB 条带（跨板信号以它为中转，避免长线交叉）----------------------
    f.rect(30, 530, 1740, 80, "", "#FFF8E6", "#D97706", 1.2, 10, INK, False, 4)
    f.text(48, 558, "BTB  J1（公座）↔ J2（母座）　18Pin 0.5mm", 13, "#B45309",
           True)
    f.text(48, 584, "① GPIO / 控制　② SDIO-1：MSC1 CLK / CMD / D0", 11,
           "#B45309")

    # --- 下层：外设板 ------------------------------------------------------
    f.rect(30, 630, 1740, 440, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 658, "Peripheral board", 15, "#15803D", True)
    f.rect(560, 700, 400, 230,
           "MCU\n外设主控\n\nBLE 5.x\nI2C-1 / I2C-2 主控\nUART-2 / GPIO",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)
    peri = [("24G 雷达模组", "I2C-1 ＋ INT（共用）", 690, BUS["I2C"]),
            ("人脸识别模组", "UART-2", 780, BUS["UART"]),
            ("NFC 读卡", "I2C-1（共用）", 870, BUS["I2C"])]
    for name, lab, y, col in peri:
        f.block(60, y, 380, 70, name, lab)
        f.line(442, y + 35, 558, y + 35, col, SW, True, lab, 10, col, 0, -9)
    f.block(1160, 760, 520, 130, "Wi-Fi 模组", "SDIO-1（MSC1）↔ SoC")
    f.line(962, 825, 1158, 825, BUS["UART"], SW, True, "UART-2 ＋ INT", 10,
           BUS["UART"], 0, -9)
    f.line(1000, 626, 1000, 698, BUS["GPIO"], SW, True)
    f.line(1030, 626, 1030, 698, BUS["SDIO"], SW, True)
    f.line(1400, 626, 1400, 758, BUS["SDIO"], SW, True)
    f.text(995, 668, "① GPIO", 11, BUS["GPIO"], True, "right", True)
    f.text(1035, 668, "② SDIO-1", 11, BUS["SDIO"], True, "left", True)

    f.legend_box_2col(
        60, 943, 1400, 120, "总线分组（编号与线色对应）",
        [(BUS["GPIO"], "① GPIO / 控制（经 BTB）"),
         (BUS["SDIO"], "② SDIO-1（MSC1，独占）：SoC ↔ Wi-Fi"),
         (BUS["I2C"], "I2C-1（共用，4.7K 上拉）：NFC ＋ 电量计 ＋ 雷达")],
        [(BUS["I2C"], "I2C-2：MCU ↔ APT32S1028"),
         (BUS["UART"], "UART-2：MCU ↔ Wi-Fi"),
         (BUS["SPI"], "SPI-1（SFC0，独占）：SoC ↔ NOR Flash")])
    f.title_block(1480, 943, 290, 120,
                  ["Rev：V01　Sheet：1 of 1", "Date：2026-01-01"],
                  "系统框图", "Example Project")
    return f
