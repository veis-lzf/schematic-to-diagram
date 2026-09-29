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
    f = Fig(2200, 1880)
    f.text(40, 46, "Video Doorbell Vision", 24, INK, True)
    f.text(40, 74, "系统框图 / SYSTEM BLOCK DIAGRAM　（全部连线横平竖直）",
           14, GRAY, True)

    SW = 2.4          # 信号线宽

    # ================= 上层：主控板 =================
    f.rect(30, 100, 2140, 590, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 128, "SOC 板 — DoorbellPro-MB（T23ZN）", 15, BLUE, True)

    # 左列：由 T23ZN 直接控制/访问的器件
    soc_left = [("SC3336 摄像头", "MIPI 2-lane ＋ I2C-S1",
                 "MIPI 2-lane ＋ I2C-S1", 150, BUS["MIPI"]),
                ("ZB25Q256ASJG", "SPI-1（SFC0，独占）", "SPI-1（SFC0，独占）",
                 250, BUS["SPI"]),
                ("时钟 Y1 / Y2", "24MHz + 32.768kHz", "24MHz / 32.768kHz", 350,
                 BUS["GPIO"])]

    # 主控用竖长蓝块，左右外设各用一条水平直线直连（无斜线）
    f.rect(880, 150, 460, 400,
           "T23ZN\n主控 SoC\n\nMIPS32 528MHz\n内封 DDR2 / DDR3\n\n"
           "MIPI CSI · USB2.0\nSFC0 · MSC1(SDIO)\nI2C · PWM · GPIO",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)
    for name, sub, lab, y, col in soc_left:
        f.rect(60, y, 380, 86, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               12, INK, True, 4)
        f.line(440, y + 43, 880, y + 43, col, SW, True, lab, 10, col, 0, -9)

    # 右列：只有真正由 T23ZN 驱动的音频与 USB
    for name, sub, lab, y, col in [
            ("NS8002 功放 + MIC", "2.4W · HPOUT / MICP-N", "I2S / 模拟音频",
             150, BUS["AUDIO"]),
            ("USB2.0 / UART1", "Type-C 下载调试", "USB2.0 / UART-1", 250,
             BUS["USB"])]:
        f.rect(1560, y, 580, 86, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               12, INK, True, 4)
        f.line(1340, y + 43, 1560, y + 43, col, SW, True, lab, 10, col, 0, -9)

    # 底排：元件虽在 SOC 板上，但控制/状态实际来自 BLE 板，
    # 因此连线一律向下进连接器条带，不连到 T23ZN
    soc_bottom = [("电源　4×JW5250A + 3×LDO", "CPU 0V8 / 1V8 / 1V5 / 3V3",
                   60, 220, BUS["PWR"], "④"),
                  ("U19 SA1511", "IR-CUT 驱动（WiFi 控制）",
                   420, 580, WIFI, "③"),
                  ("U18 KTH1601SH", "防撬霍尔 → APT32S1028",
                   780, 940, BUS["GPIO"], "①"),
                  ("SW4 / SW5", "船型开关 + 配置键 → BLE 板",
                   1140, 1280, BUS["GPIO"], "①")]
    for name, sub, x, dx, col, tag in soc_bottom:
        w = 320 if x != 1140 else 280
        f.rect(x, 570, w, 90, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               11.5, INK, True, 4)
        f.line(dx, 660, dx, 710, col, SW, True)
        f.text(dx + 10, 692, "%s 经 BTB" % tag, 10, col, True, "left", True)

    # T23ZN 自身的跨板信号：从右边缘引出后向下进条带
    f.line(1340, 470, 1470, 470, BUS["GPIO"], SW)
    f.line(1470, 470, 1470, 710, BUS["GPIO"], SW, True)
    f.text(1480, 462, "① GPIO / 音频 / 状态", 10, BUS["GPIO"], True, "left",
           True)
    f.line(1340, 520, 1505, 520, BUS["SDIO"], SW)
    f.line(1505, 520, 1505, 710, BUS["SDIO"], SW, True)
    f.text(1516, 512, "② SDIO-1", 10, BUS["SDIO"], True, "left", True)

    # ================= 中间：板对板连接器条带 =================
    f.rect(30, 710, 2140, 120, "", "#FFF8E6", "#D97706", 1.2, 10, INK,
           False, 4)
    f.text(48, 740, "BTB　J12（SOC 公座）↔ J3（BLE 母座）　18Pin 1×18 0.5mm",
           13, "#B45309", True)
    f.text(48, 764, "① GPIO / 控制：KEY_CONFIG · T23_IR_STA · T23_WHITE_STA · "
                    "AUDIO_VO1/2 · Tamper_HALL", 11, "#B45309")
    f.text(48, 786, "② SDIO-1：MSC1 CLK / CMD / D0　·　"
                    "③ WiFi 外设控制：WIFI_IRCUT_FBC", 11, "#B45309")
    f.text(48, 808, "④ 电源使能：WIFI-CPU_PWR_EN（BLE 板 → SOC 板四路 DCDC EN）"
                    "　·　电源：VCC_SYS ×2 · VBATTERY ×1 · GND ×2", 11,
           "#B45309")

    # ================= 下层：外设板 =================
    f.rect(30, 850, 2140, 830, "", "#FFFFFF", "#BFBFBF", 1.2, 10, INK,
           False, 4)
    f.text(48, 878, "BLE 板 — Video_Doorbell_Vision_BLE（V03 / PVT1）", 15,
           "#15803D", True)

    # 左列：由 RTL8762C 直接管理的器件
    for name, sub, lab, y, col in [
            ("24G 雷达模组", "I2C-1 ＋ INT · LADAR_3V3",
             "I2C-1 ＋ INT（共用）", 1010, BUS["I2C"]),
            ("人脸识别模组", "UART-3 · 9.2V（U22 升压）", "UART-3", 1120,
             BUS["UART"]),
            ("WTV380 语音 + 喇叭", "I2C-3 · 8Ω / 0.5W", "I2C-3", 1230,
             BUS["I2C"]),
            ("内机接口 J12 / J13", "内机充电 + 插入检测", "GPIO / 充电", 1340,
             BUS["GPIO"])]:
        f.rect(60, y, 400, 94, name + "\n" + sub, "#FFFFFF", "#000000", 1.2,
               12, INK, True, 4)
        f.line(460, y + 47, 800, y + 47, col, SW, True, lab, 10, col, 0, -9)

    # 供电块：总开关使能来自 SOC 板 SW4，经 BTB，不在本板由 MCU 驱动
    f.rect(60, 900, 400, 94, "U1 IU5987T + Q1\n充电 4.25V / 1.5A → "
                             "VCC_SYS ≤2.5A（使能 ← SW4 经 BTB）",
           "#FBE5E5", "#C00000", 1.2, 12, "#7F1D1D", True, 4)
    f.line(440, 900, 440, 850, BUS["GPIO"], SW, True)
    f.text(452, 876, "① WHOLE_SYSTEM_POWERON", 10, BUS["GPIO"], True, "left",
           True)

    f.rect(800, 890, 400, 620,
           "RTL8762C\nBLE 主控\n\nBLE 5.x\n40MHz 晶振\nANT1 IPEX\n\n"
           "I2C-1 / I2C-2 / I2C-3 主控\nUART-2 / UART-3\nGPIO / PWM",
           BLUE_F, BLUE, 2.4, 16, "#1F4E79", True, 6)

    # 右侧：Wi-Fi 模组及其外设。光敏与补光实际由 AIW6262 驱动/采样，
    # 不由 RTL8762C 承担，所以它们的连线只接到 AIW6262。
    f.rect(1300, 890, 800, 140,
           "AIW6262　Wi-Fi + BT 模组\nSDIO-1（MSC1）↔ T23ZN　·　"
           "UART-2 ＋ INT ↔ RTL8762C\n3.3V_WIFI（Q2）· 5V PA（Q7）",
           BLUE_F, BLUE, 2.4, 15, "#1F4E79", True, 6)
    f.rect(1300, 1100, 800, 110,
           "光敏 + 白光 / 红外补光\n"
           "WiFi_LDR_ADC ← 光敏（D9）· WIFI_WHITE_LED / WIFI_IR_LED → 补光\n"
           "LIDAR_ADC_PWR_EN → 光敏 LDO · T23_IR/WHITE_STA 仅作状态回读",
           "#FFFFFF", WIFI, 1.6, 11.5, INK, True, 4)
    f.rect(1300, 1260, 800, 140,
           "APT32S1028F8P7\nIO 扩展\nI2C-2 从机 ＋ INT\n"
           "雷达电源 / 门铃 / 按键背光 / 内机插入",
           BLUE_F, BLUE, 2.4, 14, "#1F4E79", True, 6)
    f.rect(1300, 1430, 800, 94, "Si512 NFC 读卡\n13.56MHz · I2C-1 ＋ INT",
           "#FFFFFF", "#000000", 1.2, 12, INK, True, 4)
    f.rect(1300, 1554, 800, 94,
           "CW2015 电量计 + NTC\nI2C-1 ＋ GAUGE_ALRT · NTC 10K-3950", "#FFFFFF",
           "#000000", 1.2, 12, INK, True, 4)

    # RTL8762C ↔ 右侧器件（全部水平直线，停靠在框边）
    f.line(1200, 960, 1300, 960, BUS["UART"], SW, True, "UART-2 ＋ INT", 10,
           BUS["UART"], 0, -9)
    f.line(1200, 1330, 1300, 1330, BUS["I2C"], SW, True, "I2C-2 ＋ INT", 10,
           BUS["I2C"], 0, -9)
    f.line(1200, 1477, 1300, 1477, BUS["I2C"], SW, True, "I2C-1（共用）", 10,
           BUS["I2C"], 0, -9)
    f.line(1200, 1601, 1300, 1601, BUS["I2C"], SW, True, "I2C-1 ＋ ALRT", 10,
           BUS["I2C"], 0, -9)

    # Wi-Fi 模组 ↔ 光敏/补光：③ 组，短竖线直连
    f.line(1350, 1030, 1350, 1100, WIFI, SW, True)
    f.text(1362, 1050, "③ WiFi 外设控制", 10, WIFI, True, "left", True)

    # ================= 跨板信号：以 BTB 条带为中转 =================
    f.line(1620, 890, 1620, 850, BUS["SDIO"], SW, True)
    f.text(1632, 876, "② SDIO-1", 10, BUS["SDIO"], True, "left", True)
    f.line(2020, 890, 2020, 850, WIFI, SW, True)
    f.text(2032, 876, "③ WIFI_IRCUT_FBC →", 10, WIFI, True, "left", True)
    f.line(2100, 1330, 2140, 1330, BUS["GPIO"], SW)
    f.line(2140, 1330, 2140, 850, BUS["GPIO"], SW, True)
    f.text(2124, 1232, "① KEY_CONFIG / Tamper_HALL /", 10, BUS["GPIO"], True,
           "right", True)
    f.text(2124, 1250, "WIFI-CPU_PWR_EN →", 10, BUS["GPIO"], True, "right",
           True)

    # ================= 总线分组说明 + 图框标题栏 =================
    f.legend_box_2col(
        60, 1700, 1620, 150, "总线分组（编号与线色对应）",
        [(BUS["GPIO"], "① GPIO / 控制（经 BTB）：KEY_CONFIG · Tamper_HALL · "
                       "T23_IR/WHITE_STA · AUDIO_VO · WHOLE_SYSTEM_POWERON"),
         (BUS["SDIO"], "② SDIO-1（MSC1，独占 1-bit）：T23ZN ↔ AIW6262"),
         (WIFI, "③ WiFi 外设控制：AIW6262 → WIFI_IRCUT_FBC（U19 SA1511，"
                "SOC 板）/ WIFI_WHITE_LED / WIFI_IR_LED / WiFi_LDR_ADC"),
         (BUS["PWR"], "④ WIFI-CPU_PWR_EN：BLE 板 → SOC 板四路 DCDC EN")],
        [(BUS["I2C"], "I2C-1（共用，4.7K 上拉）：RTL8762C ↔ Si512 NFC · "
                      "CW2015 电量计 · 24G 雷达"),
         (BUS["I2C"], "I2C-2：RTL8762C ↔ APT32S1028　·　"
                      "I2C-3：RTL8762C ↔ WTV380 语音"),
         (BUS["I2C"], "I2C-S1：T23ZN ↔ SC3336（SOC 板，4.7K 上拉）"),
         (BUS["MIPI"], "MIPI 2-lane（独占）：SC3336 → T23ZN　·　"
                       "SPI-1（SFC0，独占）：T23ZN ↔ NOR Flash")])
    f.title_block(1700, 1700, 470, 150,
                  ["BLE 板 V03 / PVT1 · SOC 板 DVT2",
                   "Date：2026-09-29　Rev：V03　Sheet：1 of 1",
                   "卧安科技（深圳）有限公司"],
                  "Video Doorbell Vision — 系统框图")
    return f
