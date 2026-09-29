"""Renderer for schematic-derived power trees and system block diagrams.

One shape list drives four outputs so the picture and the Visio file can never
disagree:  SVG (source), PNG (rasterised by a headless browser), VSDX
(Visio 2013+) and VDX (Visio 2003-2010 XML).

Coordinates are pixels; 100 px == 1 inch on the Visio page, so a 2200x1500
figure becomes a 22x15 in page.
"""
import os
import shutil
import subprocess
import zipfile

# ------------------------------------------------------------------ palette --
VBAT = "#FFC000"   # 3.0-4.25V
V5 = "#C00000"     # 5V
V33 = "#00B050"    # 3.3V
V18 = "#00B0F0"    # 1.8V
V15 = "#7030A0"    # 1.5V
V08 = "#2E75B6"    # 0.8V
V92 = "#E5007D"    # 9.2V
RED = "#C00000"
BLUE = "#2E75B6"
BLUE_F = "#DEEBF7"
INK = "#1F2933"
GRAY = "#64748B"
AMBER_D = "#7F6000"
WIFI = "#D6009A"   # 外设控制/状态由无线模组而非主控承担时使用

# bus-type colours (see references/style-guide.md)
BUS = {"MIPI": "#00A0A0", "SPI": "#7030A0", "I2C": "#ED7D31",
       "UART": "#00A651", "SDIO": "#0070C0", "USB": "#2E75B6",
       "GPIO": "#7F7F7F", "AUDIO": "#C55A11", "PWR": "#C00000",
       "WIFI": WIFI}


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _svg_text(x, y, s, fs, fc, bold, align, italic=False):
    lines = s.split("\n")
    anchor = {"left": "start", "center": "middle", "right": "end"}[align]
    lh = fs * 1.28
    y0 = y - (len(lines) - 1) * lh / 2.0 + fs * 0.34
    out = ['<text x="%g" y="%g" font-size="%g" fill="%s" text-anchor="%s" '
           'font-family="Segoe UI, Microsoft YaHei, sans-serif"%s%s>'
           % (x, y0, fs, fc, anchor, ' font-weight="700"' if bold else '',
              ' font-style="italic"' if italic else '')]
    for i, ln in enumerate(lines):
        out.append('<tspan x="%g" dy="%g">%s</tspan>'
                   % (x, 0 if i == 0 else lh, _esc(ln)))
    out.append('</text>')
    return "".join(out)


class Fig:
    def __init__(self, w, h, scale=100.0):
        self.w, self.h, self.scale = w, h, scale
        self.items = []

    # ------------------------------------------------------------ primitives --
    def rect(self, x, y, w, h, text="", fill=None, stroke="#000000", sw=1.0,
             fs=12, fc="#000000", bold=False, round_r=0, align="center"):
        self.items.append(dict(t="rect", x=x, y=y, w=w, h=h, text=text,
                               fill=fill, stroke=stroke, sw=sw, fs=fs, fc=fc,
                               bold=bold, round=round_r, align=align))

    def line(self, x1, y1, x2, y2, color="#000000", sw=1.0, arrow=False,
             label="", lfs=10, lcolor=None, lox=0, loy=0, dash=False):
        self.items.append(dict(t="line", x1=x1, y1=y1, x2=x2, y2=y2,
                               color=color, sw=sw, arrow=arrow, label=label,
                               lfs=lfs, lcolor=lcolor or color, lox=lox,
                               loy=loy, dash=dash))

    def poly(self, pts, color="#000000", sw=1.0, arrow=True, dash=False):
        """Orthogonal polyline: arrowheads only on the final segment."""
        for i in range(len(pts) - 1):
            (x1, y1), (x2, y2) = pts[i], pts[i + 1]
            self.line(x1, y1, x2, y2, color, sw,
                      arrow and i == len(pts) - 2, dash=dash)

    def text(self, x, y, s, fs=12, fc="#000000", bold=False, align="left",
             bg=False):
        if bg:
            w = len(s) * fs * 0.63 + 12
            h = fs * 1.5
            rx = {"left": x - 6, "center": x - w / 2.0, "right": x - w}[align]
            self.rect(rx, y - fs * 1.0, w, h, "", "#FFFFFF", None, 0, fs, fc)
        self.items.append(dict(t="text", x=x, y=y, s=s, fs=fs, fc=fc,
                               bold=bold, align=align))

    # -------------------------------------------------- diagram helpers ------
    def block(self, x, y, w, h, name, sub="", fill="#FFFFFF",
              stroke="#000000", fs=12, fc=INK, note=""):
        """Peripheral / load box: name + optional sub-title."""
        body = name + (("\n" + sub) if sub else "") + (("\n" + note) if note else "")
        self.rect(x, y, w, h, body, fill, stroke, 1.2, fs, fc, True, 4)

    def converter(self, x, y, w, h, text):
        """Solid converter / power-path block (power tree)."""
        self.rect(x, y, w, h, text, RED, RED, 1.5, 13, "#FFFFFF", True, 10)

    def bus(self, x1, y1, x2, y2, color, sw=8):
        self.line(x1, y1, x2, y2, color, sw)

    def branch(self, x1, y1, x2, y2, color, sw=4, label="", lfs=10,
               lcolor=None, lox=0, loy=-9):
        """Rail branch: coloured arrow with an optional voltage/current label.

        Takes the same optional label arguments as ``line`` so callers do not
        have to remember a shorter signature.
        """
        self.line(x1, y1, x2, y2, color, sw, True, label, lfs,
                  lcolor or color, lox, loy)

    def link(self, x1, y1, x2, y2, bus, label, sw=2.4, lfs=10):
        """Bus link in a block diagram: coloured arrow + white-backed label."""
        col = BUS.get(bus, bus if str(bus).startswith("#") else INK)
        self.line(x1, y1, x2, y2, col, sw, True, label, lfs, col, 0, -9)

    def legend_box(self, x, y, w, h, title, entries, sw=3, row_h=28):
        """Colour-swatch legend: entries = [(colour, text), ...] left column."""
        self.rect(x, y, w, h, "", "#FFFFFF", "#BFBFBF", 1.2, 11, INK, False, 4)
        self.text(x + 16, y + 22, title, 13, INK, True)
        for i, (col, txt) in enumerate(entries):
            yy = y + 50 + i * row_h
            self.line(x + 16, yy, x + 58, yy, col, sw)
            self.text(x + 66, yy + 4, txt, 11, INK)

    def legend_box_2col(self, x, y, w, h, title, left, right, sw=3, row_h=28):
        self.rect(x, y, w, h, "", "#FFFFFF", "#BFBFBF", 1.2, 11, INK, False, 4)
        self.text(x + 16, y + 22, title, 13, INK, True)
        mid = x + w * 0.46
        for i, (col, txt) in enumerate(left):
            yy = y + 50 + i * row_h
            self.line(x + 16, yy, x + 58, yy, col, sw)
            self.text(x + 66, yy + 4, txt, 11, INK)
        for i, (col, txt) in enumerate(right):
            yy = y + 50 + i * row_h
            self.line(mid, yy, mid + 42, yy, col, sw)
            self.text(mid + 50, yy + 4, txt, 11, INK)

    def title_block(self, x, y, w, h, rows, title, subtitle=""):
        """Engineering title block for the bottom-right corner."""
        self.rect(x, y, w, h, "", "#FFFFFF", "#000000", 1.2, 10, INK,
                  False, 0)
        lines = [title] + ([subtitle] if subtitle else []) + list(rows)
        n = len(lines)
        step = h / float(n)
        for i in range(1, n):
            self.line(x, y + step * i, x + w, y + step * i, "#000000", 1)
        for i, t in enumerate(lines):
            self.text(x + 12, y + step * (i + 0.72), t, 12 if i == 0 else 11,
                      INK, i == 0)

    # ------------------------------------------------------------------ svg --
    def svg(self):
        used = []
        for it in self.items:
            if it["t"] == "line" and it["arrow"]:
                c = it["color"].upper()
                if c not in used:
                    used.append(c)
        o = ['<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d">' % (self.w, self.h, self.w, self.h),
             '<defs>']
        for i, col in enumerate(used):
            o.append('<marker id="m%d" viewBox="0 0 16 16" refX="15" refY="8" '
                     'markerUnits="userSpaceOnUse" markerWidth="16" '
                     'markerHeight="16" orient="auto-start-reverse">'
                     '<path d="M0,1.6 L15.2,8 L0,14.4 z" fill="%s"/></marker>'
                     % (i, col))
        o.append('</defs>')
        o.append('<rect width="%d" height="%d" fill="#FFFFFF"/>'
                 % (self.w, self.h))
        for it in self.items:
            if it["t"] == "rect":
                rx = ' rx="%d"' % it["round"] if it["round"] else ''
                o.append('<rect x="%g" y="%g" width="%g" height="%g"%s '
                         'fill="%s" stroke="%s" stroke-width="%g"/>'
                         % (it["x"], it["y"], it["w"], it["h"], rx,
                            it["fill"] or "none", it["stroke"] or "none",
                            it["sw"]))
                if it["text"]:
                    o.append(_svg_text(it["x"] + it["w"] / 2.0,
                                       it["y"] + it["h"] / 2.0, it["text"],
                                       it["fs"], it["fc"], it["bold"],
                                       "center"))
            elif it["t"] == "line":
                mk = (' marker-end="url(#m%d)"'
                      % used.index(it["color"].upper()) if it["arrow"] else '')
                dash = ' stroke-dasharray="7 5"' if it["dash"] else ''
                o.append('<line x1="%g" y1="%g" x2="%g" y2="%g" stroke="%s" '
                         'stroke-width="%g" stroke-linecap="round"%s%s/>'
                         % (it["x1"], it["y1"], it["x2"], it["y2"],
                            it["color"], it["sw"], dash, mk))
                if it["label"]:
                    mx = (it["x1"] + it["x2"]) / 2.0 + it["lox"]
                    my = (it["y1"] + it["y2"]) / 2.0 + it["loy"]
                    o.append('<text x="%g" y="%g" font-size="%g" fill="%s" '
                             'font-weight="700" text-anchor="middle" '
                             'font-family="Segoe UI, Microsoft YaHei, '
                             'sans-serif">%s</text>'
                             % (mx, my, it["lfs"], it["lcolor"],
                                _esc(it["label"])))
            else:
                o.append(_svg_text(it["x"], it["y"], it["s"], it["fs"],
                                   it["fc"], it["bold"], it["align"]))
        o.append('</svg>')
        return "\n".join(o)

    # ------------------------------------------------------- shape model -----
    def _model(self, it):
        s, H = self.scale, self.h
        m = dict(text=it.get("text") or it.get("label") or it.get("s") or "",
                 fs=it.get("fs") or it.get("lfs") or 12,
                 fc=it.get("fc") or it.get("lcolor") or "#000000",
                 bold=bool(it.get("bold", it["t"] == "line" and bool(it.get("label")))),
                 align=it.get("align", "center"),
                 fill=None, fillpat=0, line=None, linew=0.01, linepat=1,
                 arrow=0, rounding=0.0, geom="none")
        if it["t"] == "rect":
            m.update(kind="rect", geom="rect", w=it["w"] / s, h=it["h"] / s,
                     pinx=(it["x"] + it["w"] / 2.0) / s,
                     piny=(H - it["y"] - it["h"] / 2.0) / s,
                     flipx=0, flipy=0, fill=it["fill"] or "#FFFFFF",
                     fillpat=0 if it["fill"] is None else 1,
                     line=it["stroke"] or "#000000", linew=it["sw"] / s,
                     linepat=0 if it["stroke"] is None else 1,
                     rounding=it["round"] / s)
        elif it["t"] == "line":
            x1, y1 = it["x1"] / s, (H - it["y1"]) / s
            x2, y2 = it["x2"] / s, (H - it["y2"]) / s
            m.update(kind="line", geom="line", w=abs(x2 - x1), h=abs(y2 - y1),
                     pinx=(x1 + x2) / 2.0, piny=(y1 + y2) / 2.0,
                     flipx=1 if x2 < x1 else 0, flipy=1 if y2 < y1 else 0,
                     line=it["color"], linew=it["sw"] / s,
                     linepat=2 if it["dash"] else 1,
                     arrow=4 if it["arrow"] else 0, align="center")
        else:
            wid = max(0.8, len(it["s"]) * it["fs"] * 0.62 / s)
            left = it["x"] / s
            m.update(kind="text", geom="none", w=wid, h=0.3,
                     pinx=left if it["align"] == "center" else left + wid / 2.0,
                     piny=(H - it["y"]) / s, flipx=0, flipy=0, align="left")
        return m

    # ---------------------------------------------------------------- vsdx --
    def vsdx_page(self):
        shapes = []
        for i, it in enumerate(self.items, start=1):
            m = self._model(it)
            cells = ['<Cell N="PinX" V="%g"/>' % m["pinx"],
                     '<Cell N="PinY" V="%g"/>' % m["piny"],
                     '<Cell N="Width" V="%g"/>' % m["w"],
                     '<Cell N="Height" V="%g"/>' % m["h"],
                     '<Cell N="LocPinX" V="%g" F="Width*0.5"/>' % (m["w"] / 2.0),
                     '<Cell N="LocPinY" V="%g" F="Height*0.5"/>' % (m["h"] / 2.0),
                     '<Cell N="Angle" V="0"/>',
                     '<Cell N="FlipX" V="%d"/>' % m["flipx"],
                     '<Cell N="FlipY" V="%d"/>' % m["flipy"]]
            if m["geom"] == "rect":
                geo = ['<Section N="Geometry" IX="0">',
                       '<Cell N="NoFill" V="%d"/>' % (0 if m["fillpat"] else 1),
                       '<Cell N="NoLine" V="0"/>',
                       '<Cell N="NoSnap" V="0"/><Cell N="NoShow" V="0"/>']
                if m["rounding"]:
                    geo.append('<Cell N="Rounding" V="%g"/>' % m["rounding"])
                geo += ['<Row T="RelMoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>',
                        '<Row T="RelLineTo" IX="2"><Cell N="X" V="1"/><Cell N="Y" V="0"/></Row>',
                        '<Row T="RelLineTo" IX="3"><Cell N="X" V="1"/><Cell N="Y" V="1"/></Row>',
                        '<Row T="RelLineTo" IX="4"><Cell N="X" V="0"/><Cell N="Y" V="1"/></Row>',
                        '<Row T="RelLineTo" IX="5"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>',
                        '</Section>']
            elif m["geom"] == "line":
                geo = ['<Section N="Geometry" IX="0">',
                       '<Cell N="NoFill" V="1"/><Cell N="NoLine" V="0"/>',
                       '<Cell N="NoSnap" V="0"/><Cell N="NoShow" V="0"/>',
                       '<Row T="MoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>',
                       '<Row T="LineTo" IX="2"><Cell N="X" V="%g"/><Cell N="Y" V="%g"/></Row>'
                       % (m["w"], m["h"]), '</Section>']
            else:
                geo = ['<Section N="Geometry" IX="0">',
                       '<Cell N="NoFill" V="1"/><Cell N="NoLine" V="1"/>',
                       '<Cell N="NoSnap" V="0"/><Cell N="NoShow" V="0"/>',
                       '<Row T="MoveTo" IX="1"><Cell N="X" V="0"/><Cell N="Y" V="0"/></Row>',
                       '<Row T="LineTo" IX="2"><Cell N="X" V="%g"/><Cell N="Y" V="0"/></Row>'
                       % m["w"], '</Section>']
            fill = ('<Cell N="FillForegnd" V="%s"/><Cell N="FillPattern" V="%d"/>'
                    % (m["fill"], m["fillpat"])) if m["fillpat"] else \
                   '<Cell N="FillPattern" V="0"/>'
            lc = ''
            if m["line"]:
                lc = ('<Cell N="LineColor" V="%s"/><Cell N="LineWeight" V="%g"/>'
                      '<Cell N="LinePattern" V="%d"/><Cell N="EndArrow" V="%d"/>'
                      '<Cell N="EndArrowSize" V="%d"/>'
                      % (m["line"], m["linew"], m["linepat"], m["arrow"],
                         3 if m["linew"] * self.scale >= 3 else 2))
            halign = {"left": 0, "center": 1, "right": 2}[m["align"]]
            ch = ('<Section N="Character"><Row IX="0"><Cell N="Size" V="%g"/>'
                  '<Cell N="Style" V="%d"/><Cell N="Color" V="%s"/>'
                  '<Cell N="Font" V="1"/></Row></Section>'
                  '<Section N="Paragraph"><Row IX="0">'
                  '<Cell N="HorzAlign" V="%d"/></Row></Section>'
                  '<Section N="TextBlock"><Row IX="0">'
                  '<Cell N="LeftMargin" V="0.02"/><Cell N="RightMargin" V="0.02"/>'
                  '<Cell N="TopMargin" V="0.01"/><Cell N="BottomMargin" V="0.01"/>'
                  '<Cell N="VerticalAlign" V="1"/><Cell N="TextBkgnd" V="0"/>'
                  '</Row></Section>'
                  % (m["fs"] / self.scale, 1 if m["bold"] else 0, m["fc"],
                     halign))
            txt = '<Text>%s</Text>' % _esc(m["text"]) if m["text"] else ''
            shapes.append('<Shape ID="%d" NameU="Shape.%d" Type="Shape" '
                          'LineStyle="0" FillStyle="0" TextStyle="0">%s%s%s%s%s%s'
                          '</Shape>'
                          % (i, i, "".join(cells), fill, lc, "".join(geo),
                             ch, txt))
        return ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<PageContents xmlns="http://schemas.microsoft.com/office/visio/2012/main" '
                'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
                'xml:space="preserve"><Shapes>%s</Shapes></PageContents>'
                % "".join(shapes))

    # ----------------------------------------------------------------- vdx --
    def vdx_page(self):
        shapes = []
        for i, it in enumerate(self.items, start=1):
            m = self._model(it)
            xf = ("<PinX>%g</PinX><PinY>%g</PinY><Width>%g</Width>"
                  "<Height>%g</Height><LocPinX F=\"Width*0.5\">%g</LocPinX>"
                  "<LocPinY F=\"Height*0.5\">%g</LocPinY><Angle>0</Angle>"
                  "<FlipX>%d</FlipX><FlipY>%d</FlipY>"
                  % (m["pinx"], m["piny"], m["w"], m["h"], m["w"] / 2.0,
                     m["h"] / 2.0, m["flipx"], m["flipy"]))
            fill = ("<Fill><FillForegnd>%s</FillForegnd><FillPattern>%d</FillPattern>"
                    "</Fill>" % (m["fill"], m["fillpat"])) if m["fillpat"] else \
                   "<Fill><FillPattern>0</FillPattern></Fill>"
            line = ""
            if m["line"]:
                line = ("<Line><LineColor>%s</LineColor><LineWeight>%g</LineWeight>"
                        "<LinePattern>%d</LinePattern><EndArrow>%d</EndArrow>"
                        "<EndArrowSize>%d</EndArrowSize></Line>"
                        % (m["line"], m["linew"], m["linepat"], m["arrow"],
                           3 if m["linew"] * self.scale >= 3 else 2))
            if m["geom"] == "rect":
                geo = ['<Geom IX="0">']
                if not m["fillpat"]:
                    geo.append("<NoFill>1</NoFill>")
                if m["rounding"]:
                    geo.append("<Rounding>%g</Rounding>" % m["rounding"])
                geo += ['<MoveTo IX="1"><X>0</X><Y>0</Y></MoveTo>',
                        '<LineTo IX="2"><X>%g</X><Y>0</Y></LineTo>' % m["w"],
                        '<LineTo IX="3"><X>%g</X><Y>%g</Y></LineTo>'
                        % (m["w"], m["h"]),
                        '<LineTo IX="4"><X>0</X><Y>%g</Y></LineTo>' % m["h"],
                        '<LineTo IX="5"><X>0</X><Y>0</Y></LineTo>', '</Geom>']
            elif m["geom"] == "line":
                geo = ['<Geom IX="0"><NoFill>1</NoFill>',
                       '<MoveTo IX="1"><X>0</X><Y>0</Y></MoveTo>',
                       '<LineTo IX="2"><X>%g</X><Y>%g</Y></LineTo>'
                       % (m["w"], m["h"]), '</Geom>']
            else:
                geo = ['<Geom IX="0"><NoFill>1</NoFill><NoLine>1</NoLine>',
                       '<MoveTo IX="1"><X>0</X><Y>0</Y></MoveTo>',
                       '<LineTo IX="2"><X>%g</X><Y>0</Y></LineTo>' % m["w"],
                       '</Geom>']
            ch = ("<Char><Font>1</Font><Color>%s</Color><Size>%g</Size>"
                  "<Style>%d</Style></Char>"
                  % (m["fc"], m["fs"] / self.scale, 1 if m["bold"] else 0))
            txt = "<Text>%s</Text>" % _esc(m["text"]) if m["text"] else ""
            shapes.append('<Shape ID="%d" NameU="Sheet.%d" Type="Shape">'
                          '<XForm>%s</XForm>%s%s%s%s%s</Shape>'
                          % (i, i, xf, fill, line, "".join(geo), ch, txt))
        return ('<?xml version="1.0" encoding="utf-8"?>\n'
                '<VisioDocument xmlns="http://schemas.microsoft.com/visio/2003/core" '
                'xml:space="preserve"><DocumentProperties><Creator>Codex</Creator>'
                '</DocumentProperties><Pages><Page ID="0" NameU="Page-1" Name="Page-1">'
                '<PageSheet><PageProps><PageWidth>%g</PageWidth>'
                '<PageHeight>%g</PageHeight><ShdwOffsetX>0.1</ShdwOffsetX>'
                '<ShdwOffsetY>-0.1</ShdwOffsetY></PageProps></PageSheet>'
                '<Shapes>%s</Shapes></Page></Pages></VisioDocument>'
                % (self.w / self.scale, self.h / self.scale, "".join(shapes)))


# --------------------------------------------------------------- exporters --
def write_vsdx(fig, path, title):
    ct = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
          '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="xml" ContentType="application/xml"/>'
          '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>'
          '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
          '<Override PartName="/visio/document.xml" ContentType="application/vnd.ms-visio.drawing.main+xml"/>'
          '<Override PartName="/visio/pages/pages.xml" ContentType="application/vnd.ms-visio.pages+xml"/>'
          '<Override PartName="/visio/pages/page1.xml" ContentType="application/vnd.ms-visio.page+xml"/>'
          '</Types>')
    rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/document" Target="visio/document.xml"/>'
            '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
            '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>'
            '</Relationships>')
    core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
            'xmlns:dc="http://purl.org/dc/elements/1.1/" '
            'xmlns:dcterms="http://purl.org/dc/terms/" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<dc:title>%s</dc:title><dc:creator>Codex</dc:creator>'
            '<cp:lastModifiedBy>Codex</cp:lastModifiedBy>'
            '<dcterms:created xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z'
            '</dcterms:created>'
            '<dcterms:modified xsi:type="dcterms:W3CDTF">2026-01-01T00:00:00Z'
            '</dcterms:modified></cp:coreProperties>' % _esc(title))
    app = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
           '<Application>Microsoft Visio</Application>'
           '<AppVersion>16.0000</AppVersion></Properties>')
    pal = ["#000000", "#FFFFFF", "#FF0000", "#00FF00", "#0000FF", "#FFFF00",
           "#FF00FF", "#00FFFF", "#800000", "#008000", "#000080", "#808000",
           "#800080", "#008080", "#C0C0C0", "#808080", "#9999FF", "#993366",
           "#FFFFCC", "#CCFFFF", "#660066", "#FF8080", "#0066CC", "#CCCCFF"]
    colors = "".join('<ColorEntry IX="%d" RGB="%s"/>' % (i, c)
                     for i, c in enumerate(pal))
    doc = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
           '<VisioDocument xmlns="http://schemas.microsoft.com/office/visio/2012/main" '
           'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
           'xml:space="preserve"><DocumentSettings TopPage="0" DefaultTextStyle="0" '
           'DefaultLineStyle="0" DefaultFillStyle="0" DefaultGuideStyle="0">'
           '<GlueSettings>9</GlueSettings><SnapSettings>65847</SnapSettings>'
           '<SnapExtensions>34</SnapExtensions><SnapAngles/>'
           '<DynamicGridEnabled>1</DynamicGridEnabled><ProtectStyles>0</ProtectStyles>'
           '<ProtectShapes>0</ProtectShapes><ProtectMasters>0</ProtectMasters>'
           '<ProtectBkgnds>0</ProtectBkgnds></DocumentSettings>'
           '<Colors>%s</Colors><FaceNames>'
           '<FaceName ID="0" NameU="Calibri" UnicodeRanges="-" CharSets="-" '
           'Panos="2 15 5 2 2 2 4 3 2 4" Flags="325"/>'
           '<FaceName ID="1" NameU="Microsoft YaHei" UnicodeRanges="-" '
           'CharSets="-" Panos="2 11 5 3 2 2 4 2 2 4" Flags="325"/>'
           '</FaceNames><StyleSheets><StyleSheet ID="0" NameU="No Style" '
           'Name="No Style"><Cell N="LineWeight" V="0.01"/>'
           '<Cell N="LineColor" V="#000000"/><Cell N="LinePattern" V="1"/>'
           '<Cell N="FillForegnd" V="#FFFFFF"/><Cell N="FillPattern" V="1"/>'
           '<Cell N="Font" V="0"/><Cell N="Embellishment" V="0"/>'
           '<Cell N="HorzAlign" V="1"/><Cell N="VerticalAlign" V="1"/>'
           '</StyleSheet></StyleSheets></VisioDocument>' % colors)
    doc_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/pages" Target="pages/pages.xml"/>'
                '</Relationships>')
    pages = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Pages xmlns="http://schemas.microsoft.com/office/visio/2012/main" '
             'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
             'xml:space="preserve"><Page ID="0" NameU="%s" Name="%s" '
             'IsCustomName="1" IsCustomNameU="1" ViewScale="1" ViewCenterX="%g" '
             'ViewCenterY="%g"><PageSheet LineStyle="0" FillStyle="0" '
             'TextStyle="0"><Cell N="PageWidth" V="%g"/>'
             '<Cell N="PageHeight" V="%g"/><Cell N="PageScale" V="1"/>'
             '<Cell N="DrawingScale" V="1"/><Cell N="DrawingSizeType" V="3"/>'
             '<Cell N="DrawingScaleType" V="0"/><Cell N="InhibitSnap" V="0"/>'
             '<Cell N="ShdwType" V="0"/><Cell N="ShdwObliqueAngle" V="0"/>'
             '<Cell N="ShdwScaleFactor" V="1"/><Cell N="ShdwOffsetX" V="0.1"/>'
             '<Cell N="ShdwOffsetY" V="-0.1"/></PageSheet><Rel r:id="rId1"/>'
             '</Page></Pages>'
             % (_esc(title), _esc(title), fig.w / fig.scale / 2.0,
                fig.h / fig.scale / 2.0, fig.w / fig.scale, fig.h / fig.scale))
    pages_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                  '<Relationship Id="rId1" Type="http://schemas.microsoft.com/visio/2010/relationships/page" Target="page1.xml"/>'
                  '</Relationships>')
    if os.path.exists(path):
        os.remove(path)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", ct)
        z.writestr("_rels/.rels", rels)
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
        z.writestr("visio/document.xml", doc)
        z.writestr("visio/_rels/document.xml.rels", doc_rels)
        z.writestr("visio/pages/pages.xml", pages)
        z.writestr("visio/pages/_rels/pages.xml.rels", pages_rels)
        z.writestr("visio/pages/page1.xml", fig.vsdx_page())


def find_browser():
    cands = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"), shutil.which("google-chrome"),
        shutil.which("chromium"), shutil.which("chromium-browser"),
    ]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def rasterise(svg_path, png_path, w, h, scale=1.4):
    """SVG -> PNG with a headless browser. Returns True when it worked."""
    exe = find_browser()
    if not exe:
        print("  ! no Edge/Chrome found - PNG skipped (SVG is still written)")
        return False
    url = "file:///" + os.path.abspath(svg_path).replace("\\", "/")
    cmd = [exe, "--headless=new", "--disable-gpu", "--no-first-run",
           "--hide-scrollbars", "--force-device-scale-factor=%g" % scale,
           "--window-size=%d,%d" % (w, h),
           "--screenshot=" + os.path.abspath(png_path), url]
    try:
        subprocess.run(cmd, check=False, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as exc:                      # pragma: no cover
        print("  ! rasterise failed:", exc)
        return False
    return os.path.exists(png_path)


def export(fig, outdir, name, title, png=True, scale=1.4):
    """Write <name>.svg / .vsdx / .vdx (+ .png). Returns the file paths."""
    os.makedirs(outdir, exist_ok=True)
    svg = os.path.join(outdir, name + ".svg")
    with open(svg, "w", encoding="utf-8") as fh:
        fh.write(fig.svg())
    write_vsdx(fig, os.path.join(outdir, name + ".vsdx"), title)
    with open(os.path.join(outdir, name + ".vdx"), "w", encoding="utf-8") as fh:
        fh.write(fig.vdx_page())
    made = [svg, os.path.join(outdir, name + ".vsdx"),
            os.path.join(outdir, name + ".vdx")]
    if png and rasterise(svg, os.path.join(outdir, name + ".png"),
                         fig.w, fig.h, scale):
        made.append(os.path.join(outdir, name + ".png"))
    return made
