"""Full-detail system block diagram -- the calibration reference.

This is the level of detail a delivered block diagram is expected to reach:
board regions, the connector band, every subsystem block with its interface
list, one orthogonal link per bus with the bus index on the line, a bus-group
legend and an engineering title block. A draft with six boxes and plain arrows
is a sketch, not a deliverable.

Layout contract (see references/style-guide.md):

* board regions stacked top to bottom, connector band between them
* controllers are tall blue blocks; peripherals are white boxes in two columns
* one horizontal line per bus, labelled with the bus index and shared/exclusive
  tag, coloured by bus type
* cross-board nets use the connector band as an intermediate - two short
  vertical stubs, never a long routed net
* bottom right: bus-group legend and title block

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
    f = Fig(2200, 1700)
    f.text(40, 46, "Video Doorbell Vision", 24, INK, True)
    f.text(40, 74, "系统框图 / SYSTEM BLOCK DIAGRAM　（全部连线横平竖直）",
           14, GRAY, True)

    SW = 2.4          # 信号线宽

    # ================= 上层：主控板 =================
    f.rect(30, 100, 2140, 556, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 128, "SOC 板 — DoorbellPro-MB（T23ZN）", 15, BLUE, True)

    soc_left = [("SC3336 摄像头", "MIPI 2-lane ＋ I2C-S1",
                 "MIPI 2-lane ＋ I2C-S1", 170, "#FFFFFF", "#000000", INK,
                 BUS["MIPI"]),
                ("ZB25Q256ASJG", "SPI-1（SFC0，独占）", "SPI-1（SFC0，独占）",
                 285, "#FFFFFF", "#000000", INK, BUS["SPI"]),
                ("时钟 Y1 / Y2", "24MHz + 32.768kHz", "24MHz / 32.768kHz", 400,
                 "#FFFFFF", "#000000", INK, BUS["GPIO"]),
                ("电源　4×JW5250A + 3×LDO", "CPU 0V8 / 1V8 / 1V5 / 3V3",
                 "CPU_0V8 / 1V8 / 1V5 / 3V3", 515, "#FBE5E5", "#C00000",
                 "#7F1D1D", BUS["PWR"])]
    soc_right = [("NS8002 功放 + MIC", "2.4W · HPOUT / MICP-N", "I2S / 模拟音频",
                  170, BUS["AUDIO"]),
                 ("SA1511 / KTH1601", "IRCUT + 防撬霍尔", "PWM / GPIO", 285,
                  BUS["GPIO"]),
                 ("USB2.0 / UART1", "Type-C 下载调试", "USB2.0 / UART-1", 400,
                  BUS["USB"]),
                 ("SW4 / SW5", "船型开关 + 配置键", "GPIO / 电源使能", 515,
                  BUS["GPIO"])]

    # 主控用竖长蓝块，左右外设各用一条水平直线直连（无斜线）
    f.rect(880, 160, 460, 440,
           "T23ZN\n主控 SoC\n\nMIPS32 528MHz\n内封 DDR2 / DDR3\n\n"
           "MIPI CSI · USB2.0\nSFC0 · MSC1(SDIO)\nI2C · PWM · GPIO",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)
    for name, sub, lab, y, fill, stroke, fc, col in soc_left:
        f.rect(60, y, 380, 96, name + "\n" + sub, fill, stroke, 1.2, 12, fc,
               True, 4)
        f.line(440, y + 48, 880, y + 48, col, SW, True, lab, 10, col, 0, -9)
    for name, sub, lab, y, col in soc_right:
        f.rect(1520, y, 620, 96, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               12, INK, True, 4)
        f.line(1340, y + 48, 1520, y + 48, col, SW, True, lab, 10, col, 0, -9)

    # ================= 中间：板对板连接器条带 =================
    f.rect(30, 662, 2140, 86, "", "#FFF8E6", "#D97706", 1.2, 10, INK, False, 4)
    f.text(48, 688, "BTB　J12（SOC 公座）↔ J3（BLE 母座）　18Pin 1×18 0.5mm",
           13, "#B45309", True)
    f.text(48, 712, "① GPIO / 控制：KEY_CONFIG · T23_IR_STA · T23_WHITE_STA · "
                    "AUDIO_VO1/2", 11, "#B45309")
    f.text(48, 734, "② SDIO 1-bit：MSC1 CLK / CMD / D0　·　电源：VCC_SYS ×2 · "
                    "VBATTERY ×1 · GND ×2（载流需核算）", 11, "#B45309")

    # ================= 下层：外设板 =================
    f.rect(30, 762, 2140, 908, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 790, "BLE 板 — Video_Doorbell_Vision_BLE（V03 / PVT1）", 15,
           "#15803D", True)

    ble_left = [("24G 雷达模组", "I2C-1 ＋ INT · LADAR_3V3",
                 "I2C-1 ＋ INT（共用）", 850, BUS["I2C"]),
                ("人脸识别模组", "UART-3 · 9.2V（U22 升压）", "UART-3", 960,
                 BUS["UART"]),
                ("WTV380 语音 + 喇叭", "I2C-3 · 8Ω / 0.5W", "I2C-3", 1070,
                 BUS["I2C"]),
                ("光敏 + 白光 / 红外补光", "ADC / GPIO · 300mA", "ADC / GPIO",
                 1180, BUS["GPIO"]),
                ("内机接口 J12 / J13", "内机充电 + 插入检测", "GPIO / 充电",
                 1290, BUS["GPIO"])]
    for name, sub, lab, y, col in ble_left:
        f.rect(60, y, 400, 94, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               12, INK, True, 4)
        f.line(460, y + 47, 800, y + 47, col, SW, True, lab, 10, col, 0, -9)
    # 供电块单独用淡红底区分（电源，不是信号）
    f.rect(60, 1400, 400, 94, "U1 IU5987T + Q1\n充电 4.25V / 1.5A → "
                              "VCC_SYS ≤2.5A", "#FBE5E5", "#C00000", 1.2, 12,
           "#7F1D1D", True, 4)
    f.line(460, 1447, 800, 1447, BUS["PWR"], SW, True, "VCC_SYS", 10,
           BUS["PWR"], 0, -9)

    f.rect(800, 860, 400, 634,
           "RTL8762C\nBLE 主控\n\nBLE 5.x\n40MHz 晶振\nANT1 IPEX\n\n"
           "I2C-1 / I2C-2 / I2C-3 主控\nUART-2 / UART-3\nGPIO / PWM",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)

    # 右侧 IC 与外设，全部一条水平线接入，连线停靠在框边上
    f.rect(1300, 1030, 800, 140,
           "AIW6262　Wi-Fi + BT 模组\nSDIO-1（MSC1）↔ T23ZN　·　"
           "UART-2 ＋ INT ↔ RTL8762C\n3.3V_WIFI（Q2）· 5V PA（Q7）",
           BLUE_F, BLUE, 2.4, 15, "#1F4E79", True, 6)
    f.rect(1300, 850, 500, 140,
           "APT32S1028F8P7\nIO 扩展\nI2C-2 从机 ＋ INT\n"
           "雷达电源 / 门铃 / 背光",
           BLUE_F, BLUE, 2.4, 14, "#1F4E79", True, 6)
    f.rect(1300, 1210, 800, 94, "Si512 NFC 读卡\n13.56MHz · I2C-1 ＋ INT",
           "#FFFFFF", "#000000", 1.2, 12, INK, True, 4)
    f.rect(1300, 1334, 800, 94,
           "CW2015 电量计 + NTC\nI2C-1 ＋ GAUGE_ALRT · NTC 10K-3950", "#FFFFFF",
           "#000000", 1.2, 12, INK, True, 4)
    f.line(1200, 920, 1300, 920, BUS["I2C"], SW, True, "I2C-2 ＋ INT", 10,
           BUS["I2C"], 0, -9)
    f.line(1200, 1100, 1300, 1100, BUS["UART"], SW, True, "UART-2 ＋ INT", 10,
           BUS["UART"], 0, -9)
    f.line(1200, 1256, 1300, 1256, BUS["I2C"], SW, True, "I2C-1（共用）", 10,
           BUS["I2C"], 0, -9)
    f.line(1200, 1380, 1300, 1380, BUS["I2C"], SW, True, "I2C-1 ＋ ALRT", 10,
           BUS["I2C"], 0, -9)

    # 跨板信号：以 BTB 条带为中转，四条短竖线，互不交叉
    f.line(1000, 600, 1000, 662, BUS["GPIO"], SW, True)
    f.line(1150, 600, 1150, 662, BUS["SDIO"], SW, True)
    f.text(986, 630, "① GPIO / 控制 经 BTB", 11, BUS["GPIO"], True, "right",
           True)
    f.text(1164, 630, "② SDIO-1 经 BTB", 11, BUS["SDIO"], True, "left", True)
    f.line(1500, 748, 1500, 850, BUS["GPIO"], SW, True)
    f.line(2000, 748, 2000, 1030, BUS["SDIO"], SW, True)
    f.text(1508, 800, "① → APT32S1028", 11, BUS["GPIO"], True, "left", True)
    f.text(1992, 800, "② → AIW6262", 11, BUS["SDIO"], True, "right", True)

    # ================= 总线分组说明 + 图框标题栏 =================
    f.legend_box_2col(
        60, 1500, 1620, 150, "总线分组（编号与线色对应）",
        [(BUS["GPIO"], "① GPIO / 控制（经 BTB）：KEY_CONFIG · IR / "
                       "WHITE_STA · AUDIO_VO · Tamper_HALL"),
         (BUS["SDIO"], "② SDIO-1（MSC1，独占 1-bit）：T23ZN ↔ AIW6262"),
         (BUS["I2C"], "I2C-1（共用，4.7K 上拉）：RTL8762C ↔ Si512 NFC · "
                      "CW2015 电量计 · 24G 雷达"),
         (BUS["I2C"], "I2C-2：RTL8762C ↔ APT32S1028　·　"
                      "I2C-3：RTL8762C ↔ WTV380 语音")],
        [(BUS["I2C"], "I2C-S1：T23ZN ↔ SC3336（SOC 板，4.7K 上拉）"),
         (BUS["MIPI"], "MIPI 2-lane（独占）：SC3336 → T23ZN"),
         (BUS["UART"], "UART-1 调试（T23ZN）· UART-2 BLE ↔ WiFi · "
                       "UART-3 BLE ↔ 人脸"),
         (BUS["SPI"], "SPI-1（SFC0，独占）：T23ZN ↔ ZB25Q256ASJG NOR Flash")])
    f.title_block(1700, 1530, 470, 110,
                  ["BLE 板 V03 / PVT1 · SOC 板 DVT2",
                   "Date：2026-09-29　Rev：V03　Sheet：1 of 1",
                   "卧安科技（深圳）有限公司"],
                  "Video Doorbell Vision — 系统框图")
    return f
