# Power Tree / System Block Diagram - Drawing Standard

These rules were converged on over several review rounds. Violating any one of
them makes the figure unreadable, so run the checklist before delivering and
redo the figure if it fails.

Chinese version: [style-guide.md](style-guide.md)

## 1. Hard Rules (violating one means redoing the figure)

1. **No dangling ends.** Every link, rail and branch must terminate on another
   line, a device box, or a connector boundary. A rail may only stop where it
   actually branches or reaches a device.
   *Seen in review:* a bus drawn across the whole sheet with a loose end that
   connects to nothing reads as a broken connection.
2. **No crossings.** Nets must not pass through each other. Route long
   cross-board nets through a shared intermediate (a connector band), or
   reorder the blocks so the paths stop overlapping.
3. **Orthogonal only.** Horizontal and vertical segments only; no diagonals.
   A peripheral connects to its controller with a single horizontal line.
4. **Arrowheads must stay visible.** Use a fixed-size marker (in SVG,
   `markerUnits="userSpaceOnUse"`, 16 units) that does **not** scale with the
   line. With an 8 px rail, a scaling arrow becomes a black wedge that swallows
   the line. Leave at least ~50 px of run on a short branch.
5. **Labels never straddle a line.** Give any label longer than ~60 px a white
   backing (`text(..., bg=True)`).
6. **Shared buses get an index and a colour** - see section 5.
7. **Verify who actually drives each control line** - see section 5.1.

## 2. Geometry and Palette

- Canvas: power tree 2200x1500, system block diagram 2200x1650 (adjust to
  content, but keep 100 px = 1 inch). At that ratio the Visio page is exactly
  22x15 / 22x16.5 in and prints 1:1.
- Line weight tiers: trunk rail 8 px, branch 4 px, block-diagram signal 2.4 px,
  device outline 1.2-2.4 px (IC blocks are the heavy end).
- Colour the power tree by **voltage domain**:

| Domain | Colour | Typical use |
| --- | --- | --- |
| 9.2 V | `#E5007D` magenta | boost output feeding a face/peripheral module |
| 5 V | `#C00000` dark red | PA rail, 5 V LEDs |
| 3.0-4.25 V | `#FFC000` amber | battery and system trunk rail |
| 3.3 V | `#00B050` green | main 3V3 domain |
| 1.8 V | `#00B0F0` cyan | IO / sensor DOVDD |
| 1.5 V | `#7030A0` purple | DDR or sensor DVDD |
| 0.8 V | `#2E75B6` blue | core |

- Colour the block diagram by **bus type** (table in section 5); IC blocks are
  a uniform pale blue fill with a blue outline.

## 3. Power Tree Conventions

- Flow left to right: sources on the left (Type-C / solar / indoor unit /
  battery) -> charger and main switch in the middle -> DC-DC and LDO stages to
  the right -> load boxes at the end. Put the voltage-domain legend bottom
  right.
- Converter: **solid colour block with white text**, holding
  "refdes + topology + output voltage/current + efficiency", three lines max.
- Load: **white fill, black outline, rounded rectangle**, load name only - no
  parameters.
- Label each branch `voltage_current` (for example `3.3V_0.50A`) 8-9 px above
  the line.
- One same-coloured rail per voltage domain; different domains never share a
  line.
- A sub-board fed through a connector gets its own sub-tree, with the feed line
  and the branch arrowheads drawn heavier and longer.

## 4. System Block Diagram Conventions

- Layer by board: main board on top, connector band in the middle, peripheral
  board below (or two columns side by side). Peripherals sit in two columns.
- The controller (SoC / MCU) is a **tall blue block** in the centre; each
  peripheral is a **white fill / black outline** box on either side, connected
  to the controller edge by **one horizontal line** with the bus name on it
  (white backing).
- Number the signal groups inside the connector band ((1)(2)(3)). Cross-board
  signals **use the band as an intermediate**: draw a short vertical stub on
  each side rather than running a long net around the sheet.
- Offset the vertical stubs of different ICs in x (longer stubs on the outside)
  so they cannot cross.
- Put an engineering title block bottom right: drawing name, board/version,
  date, rev, sheet.

## 5. Shared Bus Indexing and Colour

When one physical bus (especially I2C or UART) carries several devices it
**must be indexed**. Give every segment of the same bus the same colour, and
document the index, pull-up value, master/slave and attached devices in a
corner "bus groups" legend.

| Bus type | Colour | Notes |
| --- | --- | --- |
| I2C | `#ED7D31` orange | Number groups when several devices share it (I2C-1, I2C-2, ...) |
| SPI | `#7030A0` purple | Usually exclusive per chip select; annotate `SPI-x (exclusive)` |
| UART | `#00A651` green | Point to point; annotate `UART-x` |
| SDIO | `#0070C0` blue | State the width, e.g. `SDIO-1 (MSC1, 1-bit)` |
| MIPI | `#00A0A0` cyan | State the lane count |
| USB | `#2E75B6` blue | |
| GPIO / control | `#7F7F7F` grey | Discrete control and status, numbered (1)(2) |
| Audio | `#C55A11` brown | I2S / analogue |
| Power | `#C00000` red | Supply and enables |

- The line label carries the index plus a shared/exclusive tag, for example
  `I2C-1 + INT (shared)` or `SPI-1 (SFC0, exclusive)`.
- Mirror the index inside the device box subtitle (for example
  `I2C-2 slave + INT`) so a device can be traced back to its bus.

### 5.1 Control-signal ownership (the easiest thing to get wrong)

**A control or status net belongs to the device that actually drives or reads
it, not to whichever device "ought" to own it.** Trace the net to a specific
page and reference designator before drawing the link; never infer it from
what a signal name sounds like.

Mistakes already made on this family of drawings:

| Net | Naive guess | Actual owner |
| --- | --- | --- |
| `WIFI_IRCUT_FBC` (IR-CUT driver) | SoC (as a PWM pin) | **Wi-Fi module** (routed over the connector to U19 SA1511 on the other board) |
| `WIFI_WHITE_LED` / `WIFI_IR_LED` (fill light) | SoC GPIO | **Wi-Fi module** |
| `WiFi_LDR_ADC` / `LIDAR_ADC_PWR_EN` (light sensor) | SoC ADC / GPIO | **Wi-Fi module** |
| `APT_LOG_TX_Tamper_HALL` (tamper hall) | SoC GPIO | **APT32S1028** (I/O expander MCU) |
| `KEY_CONFIG` / `WHOLE_SYSTEM_POWERON` (rocker switch, config key) | SoC, or the same board | **Q1 / APT32S1028 on the opposite board**, over the connector |

Anti-pattern: wiring a device straight to the SoC because the signal "looks
like a GPIO", or because the device happens to sit on the SoC's board.
**Which board a part is on and which device controls it are two different
questions** - the first row above is a part on the SoC board controlled by the
Wi-Fi module.

How to verify:

1. Search the text layer for the net name and note **every** page it appears on.
2. Open the page where it meets a device pin and read the pin name plus the
   port arrow direction (`>>` out, `<<` in).
3. If the net also appears on a connector page it is cross-board: draw a
   matching stub on both sides of the connector band with the same index.
4. Only draw the link once you have reached the driving end. If it is still
   unclear, mark it "to be confirmed" rather than defaulting to the SoC.

## 6. Extracting the Data from a Schematic

1. Rasterise the pages first and read the **wiring** from the images; search the
   text layer for **net names, refdes and values**.
2. For the power tree, read: the charger FB/VSEN divider (float and MPPT
   voltage), the sense resistor (charge current), DC-DC feedback dividers
   (output voltage), and LDO part numbers (output and current limit).
3. For bus grouping, read the net-name prefixes (`BLE_I2C_*`, `APT_IIC_*`,
   `Sensor_*` ...) and cross-check the pull-up refdes to confirm which groups are
  electrically the same bus.
4. For diagram layering, read the connector pin tables (BTB / pogo / header) to
   establish which signals cross between boards.
5. Only use current and efficiency figures that are actually annotated on the
   drawing. Otherwise mark them "to be confirmed" - never invent them.

## 7. Pre-flight Checklist

- [ ] Every line ends on a device, another line, or a connector - no loose ends
- [ ] No diagonals; everything is orthogonal
- [ ] No crossings, including long cross-board nets
- [ ] Arrowheads are visible, unhidden by lines or boxes, and uniform
- [ ] Every label has a backing, does not straddle a line, and is not clipped
- [ ] Shared buses are indexed, the index matches the line colour, and a legend
      explains the grouping
- [ ] Voltage-domain colours match the legend
- [ ] SVG / PNG / VSDX / VDX are all regenerated and in sync
