"""アトランティスの図面（DXF、A2、単位 mm、表題欄つき）を 4 枚書き出す。

    python atlantis/drawings/make_dxf.py --out out/atlantis/dxf [--png]

図はすべて「用紙上の mm」で描く（実寸 m × 1000 / 縮尺）。縮尺は表題欄に書く。
寸法の元は atlantis/plan.py。
"""
import argparse
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import ezdxf  # noqa: E402
from ezdxf.enums import TextEntityAlignment  # noqa: E402

import plan as P  # noqa: E402

A2 = (594.0, 420.0)
MARGIN = 10.0
TB_W, TB_H = 190.0, 62.0  # 表題欄
NOTE_H = 78.0  # 特記事項の欄
FONT_JP = "ipam.ttf"  # IPA 明朝。無い環境では CAD 側の代替フォントで表示される
DATE = "2026-10-19"

NOTE_COMMON = [
    "本図はプラトン『クリティアス』の記述をもとにした想像図であり、実測図ではない。",
    "1スタディオン=185m、1プレトロン=30.8m、1フィート=0.31mとして換算した。",
    "記述に無い寸法（高さ・柱割り・建物の大きさ・配置など）は仮の値である。",
]

LAYERS = {
    "枠": 7, "表題": 7, "外形": 7, "水面": 5, "城壁": 1, "建物": 3, "神殿": 6,
    "寸法": 4, "注記": 7, "中心線": 8, "植栽": 3, "装飾": 2,
}


class Sheet:
    def __init__(self, title, number, scale_label, notes):
        self.doc = ezdxf.new("R2018", setup=True)
        self.doc.header["$INSUNITS"] = 4  # mm
        self.doc.header["$MEASUREMENT"] = 1
        self.doc.styles.add("JP", font=FONT_JP)
        for name, color in LAYERS.items():
            self.doc.layers.add(name, color=color)
        self.doc.layers.get("中心線").dxf.linetype = "CENTER"
        self.msp = self.doc.modelspace()
        self.title, self.number, self.scale_label, self.notes = title, number, scale_label, notes
        self._frame()

    # ---- 基本図形
    def line(self, a, b, layer="外形", lw=None):
        e = self.msp.add_line(a, b, dxfattribs={"layer": layer})
        if lw:
            e.dxf.lineweight = lw
        return e

    def poly(self, pts, layer="外形", closed=True, width=0.0):
        return self.msp.add_lwpolyline(pts, close=closed, dxfattribs={"layer": layer, "const_width": width})

    def rect(self, cx, cy, w, h, layer="外形", rot=0.0, width=0.0):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        return self.poly(pts, layer, True, width)

    def circle(self, c, r, layer="外形", lw=None):
        e = self.msp.add_circle(c, r, dxfattribs={"layer": layer})
        if lw:
            e.dxf.lineweight = lw
        return e

    def text(self, s, pos, h=3.0, layer="注記", align=TextEntityAlignment.MIDDLE_CENTER, rot=0.0):
        t = self.msp.add_text(s, height=h, rotation=rot, dxfattribs={"layer": layer, "style": "JP"})
        t.set_placement(pos, align=align)
        return t

    def annulus_hatch(self, c, r_in, r_out, layer="水面", pattern="ANSI31", scale=1.5):
        h = self.msp.add_hatch(dxfattribs={"layer": layer})
        h.set_pattern_fill(pattern, scale=scale)
        h.paths.add_edge_path().add_arc(c, r_out, 0, 360)
        h.paths.add_edge_path().add_arc(c, r_in, 0, 360)
        return h

    def leader(self, a, b, label, h=2.5):
        self.line(a, b, "注記")
        align = TextEntityAlignment.MIDDLE_LEFT if b[0] >= a[0] else TextEntityAlignment.MIDDLE_RIGHT
        self.line(b, (b[0] + (12 if b[0] >= a[0] else -12), b[1]), "注記")
        self.text(label, (b[0] + (13 if b[0] >= a[0] else -13), b[1]), h, align=align)

    def dim(self, p1, p2, base, text, angle=0.0):
        d = self.msp.add_linear_dim(base=base, p1=p1, p2=p2, angle=angle, text=text, dimstyle="EZDXF",
                                    override={"dimtxt": 2.5, "dimasz": 2.0, "dimtxsty": "JP"}, dxfattribs={"layer": "寸法"})
        d.render()

    def north(self, pos, size=14.0):
        x, y = pos
        self.poly([(x, y + size), (x - size * 0.3, y - size * 0.4), (x, y - size * 0.15), (x + size * 0.3, y - size * 0.4)], "注記")
        self.text("N", (x, y + size + 4), 4.0)

    def scale_bar(self, pos, scale, meters, step):
        x, y = pos
        mm = lambda m: m * 1000 / scale  # noqa: E731
        n = int(meters / step)
        for i in range(n):
            self.rect(x + mm(step) * (i + 0.5), y, mm(step), 2.0, "注記")
            if i % 2 == 0:
                h = self.msp.add_hatch(color=7, dxfattribs={"layer": "注記"})
                h.paths.add_polyline_path([(x + mm(step) * i, y - 1), (x + mm(step) * (i + 1), y - 1), (x + mm(step) * (i + 1), y + 1), (x + mm(step) * i, y + 1)])
        for i in range(n + 1):
            self.text(f"{int(step * i)}", (x + mm(step) * i, y - 4), 2.2)
        self.text("m", (x + mm(meters) + 5, y - 4), 2.2)

    # ---- 枠と表題欄
    def _frame(self):
        W, H = A2
        self.poly([(0, 0), (W, 0), (W, H), (0, H)], "枠")
        self.poly([(MARGIN + 10, MARGIN), (W - MARGIN, MARGIN), (W - MARGIN, H - MARGIN), (MARGIN + 10, H - MARGIN)], "枠", width=0.5)
        x0, y0 = W - MARGIN - TB_W, MARGIN
        self.tb = (x0, y0)
        self.rect(x0 + TB_W / 2, y0 + TB_H / 2, TB_W, TB_H, "表題", width=0.35)
        rows = [16.0, 10.0, 10.0, 10.0, 16.0]
        y = y0 + TB_H
        for h in rows[:-1]:
            y -= h
            self.line((x0, y), (x0 + TB_W, y), "表題")
        self.line((x0 + 30, y0), (x0 + 30, y0 + TB_H), "表題")
        self.line((x0 + 110, y0 + 16), (x0 + 110, y0 + TB_H - 16), "表題")
        self.line((x0 + 140, y0 + 16), (x0 + 140, y0 + TB_H - 16), "表題")
        # 特記事項の欄
        self.rect(x0 + TB_W / 2, y0 + TB_H + NOTE_H / 2, TB_W, NOTE_H, "表題")
        self.note_origin = (x0 + 3, y0 + TB_H + NOTE_H - 6)

    def finish(self, path):
        x0, y0 = self.tb
        top = y0 + TB_H
        L = TextEntityAlignment.MIDDLE_LEFT
        self.text("図名", (x0 + 15, top - 8), 3.0, "表題")
        self.text(self.title, (x0 + 33, top - 8), 5.0, "表題", align=L)
        self.text("縮尺", (x0 + 15, top - 21), 3.0, "表題")
        self.text(self.scale_label, (x0 + 33, top - 21), 3.5, "表題", align=L)
        self.text("用紙", (x0 + 125, top - 21), 3.0, "表題")
        self.text("A2", (x0 + 145, top - 21), 3.5, "表題", align=L)
        self.text("単位", (x0 + 15, top - 31), 3.0, "表題")
        self.text("mm（注記の実寸は m）", (x0 + 33, top - 31), 3.0, "表題", align=L)
        self.text("図番", (x0 + 125, top - 31), 3.0, "表題")
        self.text(self.number, (x0 + 145, top - 31), 3.5, "表題", align=L)
        self.text("日付", (x0 + 15, top - 41), 3.0, "表題")
        self.text(DATE, (x0 + 33, top - 41), 3.0, "表題", align=L)
        self.text("作成", (x0 + 125, top - 41), 3.0, "表題")
        self.text("ancient world", (x0 + 145, top - 41), 3.0, "表題", align=L)
        self.text("件名", (x0 + 15, y0 + 8), 3.0, "表題")
        self.text("アトランティス（伝説の都）想像図", (x0 + 33, y0 + 8), 4.0, "表題", align=L)
        nx, ny = self.note_origin
        self.text("特記事項", (nx, ny), 3.2, "表題", align=L)
        for i, s in enumerate(NOTE_COMMON + self.notes):
            self.text(f"{i + 1}. {s}", (nx, ny - 6 - i * 5.0), 2.3, "表題", align=L)
        self.doc.saveas(path)
        return path


def mmf(scale):
    return lambda m: m * 1000.0 / scale


# ================================================================ 1. 配置図
def sheet_site(out):
    S = 20000
    m = mmf(S)
    sh = Sheet("配置図（都の全図）", "AT-01", "1:20000（小図 1:150000）", [
        "大運河は外側の水の環から海まで50スタディオン（約9.25km）。本図では途中を省略した。",
        "橋の方位（東西南北の4本）、塔の数、陸の環の建物の配置は仮。",
        "外壁（環から50スタディオン）と海岸は小図に示す。",
    ])
    c = (165.0, 235.0)
    # 水の環
    for kind, r0, r1, name in P.RINGS:
        if kind == "water":
            sh.annulus_hatch(c, m(r0), m(r1), scale=2.0)
    for kind, r0, r1, name in P.RINGS:
        sh.circle(c, m(r1), "外形", lw=35)
    sh.circle(c, m(P.R_ISLAND), "外形", lw=35)
    # 城壁と塔
    for r, mat, h, t, towers in P.WALLS:
        sh.circle(c, m(r) - 0.4, "城壁", lw=70)
        for k in range(towers):
            a = 360.0 * k / towers
            x, y = P.polar(m(r) - 0.4, a)
            sh.rect(c[0] + x, c[1] + y, max(0.9, m(P.TOWER_W)), max(0.9, m(P.TOWER_W)), "城壁", rot=a)
    # 競馬場
    for r in P.HIPPODROME:
        sh.circle(c, m(r), "建物")
    # 橋と運河
    for a in P.BRIDGE_AXES:
        r_in, r_out = P.R_ISLAND, P.R_OUTER
        mid = (r_in + r_out) / 2
        x, y = P.polar(m(mid), a)
        sh.rect(c[0] + x, c[1] + y, m(r_out - r_in), max(1.2, m(P.BRIDGE_W)), "建物", rot=a)
    cw = m(P.CANAL_W)
    y_top = c[1] - m(P.R_OUTER)
    y_cut = MARGIN + 12
    sh.line((c[0] - cw / 2, y_top), (c[0] - cw / 2, y_cut), "水面", lw=35)
    sh.line((c[0] + cw / 2, y_top), (c[0] + cw / 2, y_cut), "水面", lw=35)
    zig = [(c[0] - cw, y_cut), (c[0] - cw * 0.3, y_cut), (c[0], y_cut + 3), (c[0] + 0.2 * cw, y_cut - 3), (c[0] + cw * 0.3, y_cut), (c[0] + cw, y_cut)]
    sh.poly(zig, "注記", closed=False)
    # 南の橋の下の水路
    for kind, r0, r1, name in P.RINGS:
        if kind == "land":
            sh.rect(c[0], c[1] - m((r0 + r1) / 2), m(P.PASSAGE_W) + 0.6, m(r1 - r0), "水面")
    # 中央島
    tx, ty = P.TEMPLE_CENTER
    sh.rect(c[0] + m(tx), c[1] + m(ty), m(P.TEMPLE_W), m(P.TEMPLE_L), "神殿", width=0.3)
    sh.line((c[0] - m(P.R_OUTER) - 8, c[1]), (c[0] + m(P.R_OUTER) + 8, c[1]), "中心線")
    sh.line((c[0], c[1] - m(P.R_OUTER) - 8), (c[0], c[1] + m(P.R_OUTER) + 8), "中心線")
    # 注記
    lbl = [
        (P.R_ISLAND * 0.6, 120, "中央島（アクロポリス）径5スタディオン"),
        ((P.RINGS[0][1] + P.RINGS[0][2]) / 2, 150, "水の環（幅1スタディオン）"),
        ((P.RINGS[1][1] + P.RINGS[1][2]) / 2, 160, "陸の環（幅2スタディオン）"),
        ((P.RINGS[2][1] + P.RINGS[2][2]) / 2, 170, "水の環（幅2スタディオン）"),
        ((P.RINGS[3][1] + P.RINGS[3][2]) / 2, 30, "陸の環（幅3）・競馬場"),
        ((P.RINGS[4][1] + P.RINGS[4][2]) / 2, 40, "水の環（幅3スタディオン）"),
        (P.WALLS[0][0], 55, "城壁（青銅張り）"),
        (P.WALLS[1][0], 62, "城壁（錫張り）"),
        (P.WALLS[2][0], 70, "城壁（オリハルコン張り）"),
    ]
    lbl.insert(0, (12.0, 0, "ポセイドン神殿（中央島の丘）"))
    # 注記は右側に縦に並べ、各環の右側の点から引き出す
    for i, (r, _a, s) in enumerate(lbl):
        ly = 330.0 - i * 18.0
        dy = (ly - c[1]) / m(r)
        a = math.degrees(math.asin(max(-0.95, min(0.95, dy))))
        x, y = P.polar(m(r), a)
        sh.leader((c[0] + x, c[1] + y), (c[0] + m(P.R_OUTER) + 16, ly), s)
    sh.leader((c[0] + cw / 2, y_cut + 18), (c[0] + 40, y_cut + 18), "大運河 幅3プレトロン(92.5m) 深さ100フィート 長さ50スタディオン（以下省略）")
    sh.dim((c[0] - m(P.R_OUTER) - 6, c[1] - m(P.R_OUTER)), (c[0] - m(P.R_OUTER) - 6, c[1] + m(P.R_OUTER)), (c[0] - m(P.R_OUTER) - 12, 0),
           f"{P.R_OUTER * 2:.0f}m（27スタディオン）", angle=90)
    sh.north((40, 390))
    sh.scale_bar((30, 30), S, 2000, 500)
    sh.text("配置図 S=1:20000", (c[0], 412 - MARGIN - 4), 5.0)

    # 小図: 外壁と海岸（1:150000）
    S2 = 150000
    m2 = mmf(S2)
    k = (494.0, 318.0)
    sh.circle(k, m2(P.R_OUTER), "外形")
    sh.circle(k, m2(P.R_ISLAND), "外形")
    coast_y = k[1] - m2(P.R_OUTER + P.CANAL_LEN)
    # 外壁: 海から海へ（海岸線より上の円弧）
    # 外壁は環から 50 スタディオン。運河の長さも 50 スタディオンなので、外壁は運河の河口で海岸に接する
    sh.circle(k, m2(P.R_CITY_WALL), "城壁", lw=50)
    sh.line((k[0] - 88, coast_y), (k[0] + 88, coast_y), "水面", lw=50)
    sh.text("海", (k[0], coast_y - 7), 3.5)
    sh.line((k[0] - m2(P.CANAL_W) - 0.4, k[1] - m2(P.R_OUTER)), (k[0] - 0.4, coast_y), "水面")
    sh.line((k[0] + 0.4, k[1] - m2(P.R_OUTER)), (k[0] + 0.4, coast_y), "水面")
    for i in range(9):
        x = k[0] - 80 + i * 20
        sh.poly([(x - 6, k[1] + 80), (x, k[1] + 86), (x + 6, k[1] + 80)], "植栽", closed=False)
    sh.text("北の山並み", (k[0] + 70, k[1] + 72), 2.5)
    sh.text("外壁（環から50スタディオン）", (k[0], k[1] + 50), 2.5)
    sh.text("小図 外壁と海岸 S=1:150000", (k[0], k[1] - 105), 3.5)
    return sh.finish(os.path.join(out, "AT-01_配置図.dxf"))


# ================================================================ 2. 中央島と内環
def sheet_acropolis(out):
    S = 6000
    m = mmf(S)
    sh = Sheet("中央島（アクロポリス）及び内環 平面図", "AT-02", "1:6000", [
        "王宮・泉・円形神殿・柱廊・兵舎の位置と大きさは仮。",
        "三叉の矛の記念柱は演出として加えたもので、記述に無い。",
    ])
    c = (200.0, 212.0)
    r_lim = P.RINGS[1][2]
    sh.annulus_hatch(c, m(P.RINGS[0][1]), m(P.RINGS[0][2]), scale=1.0)
    for r in (P.R_ISLAND, P.RINGS[0][2], P.RINGS[1][2]):
        sh.circle(c, m(r), "外形", lw=35)
    sh.annulus_hatch(c, m(P.RINGS[1][2]), m(P.RINGS[1][2]) + 6, scale=0.8)
    for r, mat, h, t, towers in P.WALLS[1:]:
        sh.circle(c, m(r) - m(t / 2), "城壁", lw=70)
        sh.circle(c, m(r) - m(t * 1.5), "城壁")
        for k in range(towers):
            a = 360 * k / towers
            x, y = P.polar(m(r) - m(t), a)
            sh.rect(c[0] + x, c[1] + y, m(P.TOWER_W), m(P.TOWER_W), "城壁", rot=a)
    for a in P.BRIDGE_AXES:
        mid = (P.R_ISLAND + P.RINGS[0][2]) / 2
        x, y = P.polar(m(mid), a)
        sh.rect(c[0] + x, c[1] + y, m(P.RINGS[0][2] - P.R_ISLAND) + 6, m(P.BRIDGE_W), "建物", rot=a)
    sh.rect(c[0], c[1] - m((P.RINGS[1][1] + P.RINGS[1][2]) / 2), m(P.PASSAGE_W), m(P.RINGS[1][2] - P.RINGS[1][1]), "水面")
    # 神殿と黄金の囲い
    tx, ty = P.TEMPLE_CENTER
    sh.rect(c[0] + m(tx), c[1] + m(ty), m(P.TEMPLE_W), m(P.TEMPLE_L), "神殿", width=0.35)
    sh.rect(c[0] + m(tx), c[1] + m(ty), m(P.TEMPLE_W) - 3, m(P.TEMPLE_L) - 3, "神殿")
    gx, gy, gw, gl = P.GOLD_ENCLOSURE
    sh.rect(c[0] + m(gx), c[1] + m(gy) + m(P.TEMPLE_L) / 2 + m(gl) / 2 + 2, m(gw) * 2, m(gl), "装飾")
    for x, y, name in P.PALACES:
        sh.rect(c[0] + m(x), c[1] + m(y), m(P.PALACE_SIZE[0]), m(P.PALACE_SIZE[1]), "建物", width=0.25)
        sh.text(name, (c[0] + m(x), c[1] + m(y) - m(P.PALACE_SIZE[1]) / 2 - 4), 2.8)
    for x, y, name in P.SPRINGS:
        sh.circle((c[0] + m(x), c[1] + m(y)), m(18), "水面")
        sh.text(name, (c[0] + m(x), c[1] + m(y) - 6), 2.8)
    sh.circle((c[0] + m(P.TRIDENT_COLUMN[0]), c[1] + m(P.TRIDENT_COLUMN[1])), 0.8, "装飾")
    for r, a in P.ROUND_TEMPLES:
        x, y = P.polar(m(r), a)
        sh.circle((c[0] + x, c[1] + y), m(P.ROUND_TEMPLE_R), "建物")
    for r, a in P.STOAS:
        x, y = P.polar(m(r), a)
        sh.rect(c[0] + x, c[1] + y, m(P.STOA_SIZE[0]), m(P.STOA_SIZE[1]), "建物", rot=a + 90)
    for r, a in P.BARRACKS_RING1:
        x, y = P.polar(m(r), a)
        sh.rect(c[0] + x, c[1] + y, m(P.BARRACKS_SIZE[0]), m(P.BARRACKS_SIZE[1]), "建物", rot=a + 90)
    sh.line((c[0] - m(r_lim) - 8, c[1]), (c[0] + m(r_lim) + 8, c[1]), "中心線")
    sh.line((c[0], c[1] - m(r_lim) - 8), (c[0], c[1] + m(r_lim) + 8), "中心線")
    labels = [
        ((c[0] + m(tx) + m(P.TEMPLE_W) / 2, c[1] + m(ty)), (c[0] + 95, c[1] + 120), "ポセイドン神殿（長さ1スタディオン×幅3プレトロン）"),
        ((c[0] + m(gx), c[1] + m(gy) + m(P.TEMPLE_L) / 2 + 4), (c[0] + 95, c[1] + 135), "黄金の囲い（クレイトとポセイドンの聖所）"),
        ((c[0] + m(P.R_ISLAND), c[1] + 10), (c[0] + m(r_lim) + 14, c[1] + 40), "オリハルコン張りの城壁"),
        ((c[0] + m(P.RINGS[1][2]), c[1] - 20), (c[0] + m(r_lim) + 14, c[1] - 20), "錫張りの城壁"),
        ((c[0], c[1] - m(P.RINGS[0][1]) - 2), (c[0] + m(r_lim) + 14, c[1] - 120), "橋（幅1プレトロン）と櫂船の水路"),
        ((c[0] + m(P.TRIDENT_COLUMN[0]), c[1] + m(P.TRIDENT_COLUMN[1])), (c[0] + m(r_lim) + 14, c[1] - 75), "三叉の矛の記念柱（演出）"),
    ]
    for a, b, s in labels:
        sh.leader(a, b, s)
    sh.dim((c[0] - m(P.R_ISLAND), c[1] - m(P.R_ISLAND) - 6), (c[0] + m(P.R_ISLAND), c[1] - m(P.R_ISLAND) - 6),
           (0, c[1] - m(r_lim) - 6), f"中央島 径{P.R_ISLAND * 2:.0f}m（5スタディオン）")
    sh.dim((c[0] + m(P.R_ISLAND), c[1] + 4), (c[0] + m(P.RINGS[0][2]), c[1] + 4), (0, c[1] + 6), f"{P.STADION:.0f}")
    sh.dim((c[0] + m(P.RINGS[1][1]), c[1] + 4), (c[0] + m(P.RINGS[1][2]), c[1] + 4), (0, c[1] + 6), f"{2 * P.STADION:.0f}")
    sh.north((40, 390))
    sh.scale_bar((30, 30), S, 600, 100)
    sh.text("中央島（アクロポリス）及び内環 平面図 S=1:6000", (c[0], 412 - MARGIN - 4), 5.0)
    return sh.finish(os.path.join(out, "AT-02_中央島及び内環平面図.dxf"))


# ================================================================ 3. ポセイドン神殿
def temple_columns():
    """柱の中心（神殿中心からの局所座標 m）。正面（短辺）と側面（長辺）の周柱。"""
    L, W = P.TEMPLE_L - 8, P.TEMPLE_W - 8
    cols = []
    nf, ns = P.TEMPLE_COLS_FRONT, P.TEMPLE_COLS_SIDE
    for i in range(nf):
        x = -W / 2 + W * i / (nf - 1)
        cols += [(x, -L / 2), (x, L / 2)]
    for j in range(1, ns - 1):
        y = -L / 2 + L * j / (ns - 1)
        cols += [(-W / 2, y), (W / 2, y)]
    return cols


def sheet_temple(out):
    S = 600
    m = mmf(S)
    sh = Sheet("ポセイドン神殿 平面図・南立面図・東立面図", "AT-03", "1:600", [
        "長さ・幅は記述どおり。高さ・柱の数と径・屋根勾配は仮。",
        "列柱は銀張り、屋根はオリハルコン、棟と隅の飾りは金（記述より）。",
        "平面図は北を右に置いた（方位記号を参照）。",
    ])
    L, W = P.TEMPLE_L, P.TEMPLE_W
    # 平面図: 用紙 x = 北(+Y)、用紙 y = 西(-X)
    o = (30.0 + m(L) / 2, 300.0)

    def pp(x, y):
        return (o[0] + m(y), o[1] - m(x))

    for k, inset in enumerate((0.0, 3.0, 6.0)):  # 基壇の段
        sh.rect(o[0], o[1], m(L - 2 * inset), m(W - 2 * inset), "神殿", width=0.35 if k == 0 else 0.0)
    for x, y in temple_columns():
        sh.circle(pp(x, y), m(P.TEMPLE_COL_R), "神殿")
    cella_l, cella_w = L - 40, W - 36
    sh.rect(o[0], o[1], m(cella_l), m(cella_w), "神殿", width=0.5)
    sh.rect(o[0] - m(cella_l) / 2 + 1.5, o[1], 1.0, m(14), "注記")  # 南の入口
    sh.rect(o[0] + m(cella_l * 0.25), o[1], m(18), m(12), "装飾")
    sh.leader((o[0] + m(cella_l * 0.25), o[1]), (o[0] + 60, o[1] + m(W) / 2 + 14), "ポセイドン像の台座（6頭の翼ある馬の戦車）")
    sh.leader(pp(-W / 2 + 4, -L / 2 + 30), (o[0] - m(L) / 2 + 60, o[1] + m(W) / 2 + 14), "銀張りの列柱（周柱 10×19）")
    sh.dim((o[0] - m(L) / 2, o[1] - m(W) / 2 - 8), (o[0] + m(L) / 2, o[1] - m(W) / 2 - 8), (0, o[1] - m(W) / 2 - 22),
           f"{L:.1f}m（1スタディオン）")
    sh.dim((o[0] + m(L) / 2 + 8, o[1] - m(W) / 2), (o[0] + m(L) / 2 + 8, o[1] + m(W) / 2), (o[0] + m(L) / 2 + 18, 0),
           f"{W:.1f}m（3プレトロン）", angle=90)
    sh.text("平面図", (o[0], o[1] + m(W) / 2 + 26), 4.5)
    nx, ny = o[0] + m(L) / 2 + 30, o[1] + m(W) / 2 + 6
    sh.poly([(nx + 12, ny), (nx - 4, ny + 4), (nx, ny), (nx - 4, ny - 4)], "注記")
    sh.text("N", (nx + 17, ny), 4.0)

    def elevation(origin, length, n_cols, front):
        x0, y0 = origin
        ph, ch, eh, rh = P.TEMPLE_PODIUM_H, P.TEMPLE_COL_H, P.TEMPLE_ENTAB_H, P.TEMPLE_ROOF_H
        for k in range(3):
            sh.rect(x0, y0 + m(ph) * (k + 0.5) / 3, m(length) - k * 2 * m(2.5), m(ph) / 3, "神殿")
        span = length - 8
        for i in range(n_cols):
            x = x0 - m(span) / 2 + m(span) * i / (n_cols - 1)
            r = m(P.TEMPLE_COL_R)
            sh.poly([(x - r, y0 + m(ph)), (x + r, y0 + m(ph)), (x + r * 0.82, y0 + m(ph + ch)), (x - r * 0.82, y0 + m(ph + ch))], "神殿")
            sh.rect(x, y0 + m(ph + ch) - 0.4, r * 2.6, 0.8, "神殿")
        top = y0 + m(ph + ch)
        sh.rect(x0, top + m(eh) / 2, m(length - 4), m(eh), "神殿", width=0.25)
        if front:
            sh.poly([(x0 - m(length - 4) / 2, top + m(eh)), (x0 + m(length - 4) / 2, top + m(eh)), (x0, top + m(eh + rh))], "神殿", width=0.3)
            for x, y in ((x0, top + m(eh + rh)), (x0 - m(length - 4) / 2, top + m(eh)), (x0 + m(length - 4) / 2, top + m(eh))):
                sh.poly([(x - 2, y), (x, y + 5), (x + 2, y)], "装飾")
        else:
            sh.poly([(x0 - m(length - 4) / 2, top + m(eh)), (x0 + m(length - 4) / 2, top + m(eh)),
                     (x0 + m(length - 4) / 2, top + m(eh + rh)), (x0 - m(length - 4) / 2, top + m(eh + rh))], "神殿", width=0.3)
            for i in range(9):
                x = x0 - m(length - 4) / 2 + m(length - 4) * i / 8
                sh.poly([(x - 1.5, top + m(eh + rh)), (x, top + m(eh + rh) + 4), (x + 1.5, top + m(eh + rh))], "装飾")
        sh.line((x0 - m(length) / 2 - 10, y0), (x0 + m(length) / 2 + 10, y0), "外形", lw=50)
        total = ph + ch + eh + rh
        sh.dim((x0 + m(length) / 2 + 6, y0), (x0 + m(length) / 2 + 6, y0 + m(total)), (x0 + m(length) / 2 + 14, 0), f"{total:.0f}m（仮）", angle=90)
        return top + m(eh + rh)

    e_origin = (o[0], 98.0)
    elevation(e_origin, L, P.TEMPLE_COLS_SIDE, front=False)
    sh.text("東立面図（北を右）", (e_origin[0], 86.0), 4.5)
    sh.leader((e_origin[0] + 20, e_origin[1] + m(P.TEMPLE_PODIUM_H + P.TEMPLE_COL_H + P.TEMPLE_ENTAB_H + P.TEMPLE_ROOF_H / 2)),
              (e_origin[0] + m(L) / 2 + 24, 190), "オリハルコンの屋根・金の棟飾り")
    s_origin = (480.0, 260.0)
    elevation(s_origin, W, P.TEMPLE_COLS_FRONT, front=True)
    sh.text("南立面図", (s_origin[0], 248.0), 4.5)
    sh.text("ポセイドン神殿 S=1:600", (297.0, 412 - MARGIN - 4), 5.0)
    sh.scale_bar((30, 30), S, 60, 10)
    return sh.finish(os.path.join(out, "AT-03_ポセイドン神殿.dxf"))


# ================================================================ 4. 貨幣
def trident(sh, c, size, layer="装飾"):
    x, y = c
    sh.line((x, y - size), (x, y + size * 0.55), layer)
    sh.poly([(x - size * 0.4, y + size * 0.2), (x - size * 0.4, y + size * 0.55), (x - size * 0.48, y + size * 0.45)], layer, closed=False)
    sh.poly([(x + size * 0.4, y + size * 0.2), (x + size * 0.4, y + size * 0.55), (x + size * 0.48, y + size * 0.45)], layer, closed=False)
    sh.poly([(x - size * 0.4, y + size * 0.2), (x + size * 0.4, y + size * 0.2)], layer, closed=False)
    sh.poly([(x - 0.08 * size, y + size * 0.55), (x, y + size * 0.75), (x + 0.08 * size, y + size * 0.55)], layer, closed=False)


def sheet_coins(out):
    S = 0.5  # 2:1
    sh = Sheet("貨幣 表・裏", "AT-04", "2:1", [
        "『クリティアス』に貨幣の記述は無い。図柄・寸法・重さはすべて創作。",
        "鋳造貨幣の出現は前7世紀頃であり、伝説の年代とは合わない（想像図として描く）。",
    ])
    rows = [370.0 - 60, 370.0 - 170, 370.0 - 260]
    for (name, mat, dia, obv, rev), y in zip(P.COINS, rows):
        r = dia / S / 2
        xo, xr = 120.0, 260.0
        for x in (xo, xr):
            sh.circle((x, y), r, "外形", lw=50)
            sh.circle((x, y), r * 0.86, "外形")
            for k in range(60):
                a = 2 * math.pi * k / 60
                sh.line((x + r * 0.9 * math.cos(a), y + r * 0.9 * math.sin(a)), (x + r * 0.97 * math.cos(a), y + r * 0.97 * math.sin(a)), "装飾")
        # 表
        if mat == "orichalcum":
            trident(sh, (xo, y), r * 0.6)
            for i, ch in enumerate("ΑΤΛΑΝΤΙΣ"):
                a = math.radians(200 - i * 20)
                sh.text(ch, (xo + r * 0.74 * math.cos(a), y + r * 0.74 * math.sin(a)), 4.0, "装飾", rot=math.degrees(a) - 90)
            for k, rr in enumerate([0.14, 0.24, 0.36, 0.48, 0.62]):
                sh.circle((xr, y), r * rr, "装飾")
            sh.rect(xr, y - r * 0.55, r * 0.08, r * 0.3, "装飾")
        elif mat == "silver":
            head = [(-0.25, 0.5), (0.1, 0.55), (0.3, 0.35), (0.38, 0.1), (0.48, -0.02), (0.35, -0.08), (0.32, -0.3), (0.15, -0.35), (0.05, -0.55), (-0.3, -0.55), (-0.4, 0.0)]
            sh.poly([(xo + r * a, y + r * b) for a, b in head], "装飾")
            for k in range(6):
                sh.poly([(xo + r * (-0.35 + k * 0.08), y + r * 0.45), (xo + r * (-0.3 + k * 0.08), y + r * 0.62)], "装飾", closed=False)
            hull = [(-0.6, 0.0), (0.55, 0.0), (0.72, 0.15), (0.6, -0.12), (-0.5, -0.12)]
            sh.poly([(xr + r * a, y + r * b) for a, b in hull], "装飾")
            for k in range(9):
                xx = xr + r * (-0.45 + k * 0.11)
                sh.line((xx, y - r * 0.12), (xx - r * 0.08, y - r * 0.38), "装飾")
            sh.line((xr, y), (xr, y + r * 0.55), "装飾")
            sh.poly([(xr - r * 0.25, y + r * 0.5), (xr + r * 0.25, y + r * 0.5), (xr + r * 0.22, y + r * 0.15), (xr - r * 0.22, y + r * 0.15)], "装飾")
        else:
            bull = [(-0.55, 0.1), (-0.4, 0.25), (0.3, 0.22), (0.45, 0.35), (0.42, 0.18), (0.6, 0.12), (0.55, 0.0), (0.38, -0.02), (0.35, -0.4), (0.25, -0.4), (0.22, -0.1), (-0.3, -0.12), (-0.35, -0.4), (-0.45, -0.4), (-0.45, -0.05)]
            sh.poly([(xo + r * a, y + r * b) for a, b in bull], "装飾")
            trident(sh, (xr, y), r * 0.6)
        sh.text("表", (xo, y - r - 6), 3.5)
        sh.text("裏", (xr, y - r - 6), 3.5)
        L = TextEntityAlignment.MIDDLE_LEFT
        sh.text(f"{name}（{ {'orichalcum': 'オリハルコン', 'silver': '銀', 'bronze': '青銅'}[mat] }）", (340.0, y + 12), 4.0, align=L)
        sh.text(f"径 {dia:.0f}mm（図上 {dia / S:.0f}mm）", (340.0, y + 4), 3.0, align=L)
        sh.text(f"表: {obv}", (340.0, y - 4), 3.0, align=L)
        sh.text(f"裏: {rev}", (340.0, y - 12), 3.0, align=L)
        sh.dim((xo - r, y + r + 4), (xo + r, y + r + 4), (0, y + r + 8), f"φ{dia:.0f}")
    sh.text("貨幣 表・裏 S=2:1", (297.0, 412 - MARGIN - 4), 5.0)
    return sh.finish(os.path.join(out, "AT-04_貨幣.dxf"))


def to_png(path, png):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext
    from ezdxf.addons.drawing.config import BackgroundPolicy, ColorPolicy, Configuration
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend
    from matplotlib import font_manager

    for f in ("/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf", "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"):
        if os.path.exists(f):
            font_manager.fontManager.addfont(f)
    doc = ezdxf.readfile(path)
    fig = plt.figure(figsize=(A2[0] / 25.4, A2[1] / 25.4))
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = Configuration(background_policy=BackgroundPolicy.WHITE, color_policy=ColorPolicy.BLACK)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace())
    ax.set_xlim(0, A2[0])
    ax.set_ylim(0, A2[1])
    fig.savefig(png, dpi=110)
    plt.close(fig)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(os.path.dirname(os.path.dirname(HERE)), "out", "atlantis", "dxf"))
    ap.add_argument("--png", action="store_true", help="確認用の PNG も書く")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    for f in (sheet_site, sheet_acropolis, sheet_temple, sheet_coins):
        p = f(a.out)
        print("wrote", p)
        if a.png:
            to_png(p, p.replace(".dxf", ".png"))


if __name__ == "__main__":
    main(sys.argv[1:])
