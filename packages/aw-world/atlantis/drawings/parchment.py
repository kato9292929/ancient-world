"""巻物に描く「セピアのインクの配置図」を画像にする（Pillow）。

画像の画素は 3D の地面の座標にそのまま対応する（巻物は都の上に広げるので、線が建物の位置から立ち上がる）。
出力: parchment.png（羊皮紙＋インク）と ink_mask.png（インクの線だけ。光らせる演出に使う）。
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402
from scipy.ndimage import gaussian_filter  # noqa: E402

import plan as P  # noqa: E402

# 巻物が覆う範囲（m）。南端は海岸の少し先、北端に題字の帯
X0, X1 = -3400.0, 3400.0
Y0, Y1 = -4700.0, 3900.0
PX_W = 4096
MPP = (X1 - X0) / PX_W
PX_H = int(round((Y1 - Y0) / MPP))

SEPIA = (78, 46, 22)
FONT_SERIF = "/usr/share/fonts/truetype/freefont/FreeSerifBold.ttf"
FONT_JP = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"


def px(x, y):
    return ((x - X0) / MPP, (Y1 - y) / MPP)


def pr(r):
    return r / MPP


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def parchment_base(seed=3):
    rng = np.random.default_rng(seed)
    h, w = PX_H, PX_W
    base = np.zeros((h, w), np.float32)
    for sigma, amp in ((180, 0.5), (60, 0.3), (14, 0.15), (2, 0.08)):
        n = gaussian_filter(rng.standard_normal((h // 4, w // 4)).astype(np.float32), sigma / 4)
        n = (n - n.mean()) / (n.std() + 1e-6)
        base += amp * np.array(Image.fromarray(n).resize((w, h), Image.BILINEAR))
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    edge = np.minimum.reduce([xx, w - xx, yy, h - yy]) / 220.0
    vignette = np.clip(edge, 0, 1) ** 0.6
    shade = 0.84 + 0.05 * base
    shade *= 0.72 + 0.28 * vignette
    col = np.stack([226 * shade, 203 * shade, 156 * shade], -1)
    # しみ
    for _ in range(14):
        cx, cy, r = rng.uniform(0, w), rng.uniform(0, h), rng.uniform(80, 380)
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
        ring = np.exp(-((d - 1) ** 2) / 0.004) * 0.05 + np.exp(-(d**2) * 3) * 0.04
        col *= (1 - ring)[..., None]
    return np.clip(col, 0, 255).astype(np.uint8)


class Ink:
    def __init__(self):
        self.mask = Image.new("L", (PX_W, PX_H), 0)
        self.d = ImageDraw.Draw(self.mask)

    def circle(self, c, r, w=4):
        x, y = px(*c)
        rr = pr(r)
        self.d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=255, width=w)

    def poly(self, pts, w=3, close=True, fill=False):
        q = [px(*p) for p in pts]
        if fill:
            self.d.polygon(q, fill=255)
        elif close:
            self.d.line(q + [q[0]], fill=255, width=w, joint="curve")
        else:
            self.d.line(q, fill=255, width=w, joint="curve")

    def rect(self, cx, cy, w_, h_, rot=0.0, w=3, fill=False):
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        pts = [(cx + x * c - y * s, cy + x * s + y * c) for x, y in ((-w_ / 2, -h_ / 2), (w_ / 2, -h_ / 2), (w_ / 2, h_ / 2), (-w_ / 2, h_ / 2))]
        self.poly(pts, w, True, fill)

    def text(self, s, pos, size, font=FONT_JP, anchor="mm"):
        self.d.text(px(*pos), s, fill=255, font=_font(font, size), anchor=anchor)

    def hatch_annulus(self, r0, r1, spacing=30.0, w=2):
        layer = Image.new("L", self.mask.size, 0)
        dl = ImageDraw.Draw(layer)
        for k in range(-int(PX_W * 2), int(PX_W * 2), int(spacing)):
            dl.line((k, 0, k + PX_H, PX_H), fill=255, width=w)
        ring = Image.new("L", self.mask.size, 0)
        dr = ImageDraw.Draw(ring)
        x, y = px(0, 0)
        dr.ellipse((x - pr(r1), y - pr(r1), x + pr(r1), y + pr(r1)), fill=255)
        dr.ellipse((x - pr(r0), y - pr(r0), x + pr(r0), y + pr(r0)), fill=0)
        self.mask.paste(255, (0, 0), Image.fromarray(np.minimum(np.array(layer), np.array(ring))))


def meander_border(ink, inset=90, unit=34):
    """ギリシャ雷文の縁。外周を一周する。"""
    d = ink.d
    w, h = PX_W, PX_H
    for side in range(4):
        length = (w if side % 2 == 0 else h) - 2 * inset
        n = int(length // (unit * 2))
        for i in range(n):
            u0 = inset + i * unit * 2
            pattern = [(0, 0), (0, 1.5), (1.5, 1.5), (1.5, 0.5), (0.75, 0.5), (0.75, 1.0)]
            pts = []
            for a, b in pattern:
                uu, vv = u0 + a * unit, inset - 60 + b * unit * 0.7
                if side == 0:
                    pts.append((uu, vv))
                elif side == 1:
                    pts.append((w - vv, uu))
                elif side == 2:
                    pts.append((w - uu, h - vv))
                else:
                    pts.append((vv, h - uu))
            d.line(pts, fill=255, width=5)
    for k in (inset - 70, inset + 30):
        d.rectangle((k, k, w - k, h - k), outline=255, width=6)


def compass(ink, c, r):
    x, y = px(*c)
    R = pr(r)
    d = ink.d
    for rr in (R, R * 0.92, R * 0.35):
        d.ellipse((x - rr, y - rr, x + rr, y + rr), outline=255, width=5)
    for k in range(16):
        a = math.radians(k * 22.5)
        L = R * (1.0 if k % 4 == 0 else 0.6 if k % 2 == 0 else 0.4)
        tip = (x + L * math.sin(a), y - L * math.cos(a))
        side1 = (x + R * 0.12 * math.sin(a + math.pi / 2), y - R * 0.12 * math.cos(a + math.pi / 2))
        side2 = (x + R * 0.12 * math.sin(a - math.pi / 2), y - R * 0.12 * math.cos(a - math.pi / 2))
        if k % 4 == 0:
            d.polygon([tip, side1, (x, y)], fill=255)
            d.line([tip, side2, (x, y)], fill=255, width=4)
        else:
            d.line([tip, side1, (x, y), side2, tip], fill=255, width=3)
    f = _font(FONT_SERIF, int(R * 0.28))
    for k, s in enumerate("NESW"):
        a = math.radians(k * 90)
        d.text((x + R * 1.18 * math.sin(a), y - R * 1.18 * math.cos(a)), s, fill=255, font=f, anchor="mm")


def cartouche(ink, center, w, h):
    """題字の飾り枠: 二重の枠、両端の渦巻き、上下の小さな三叉の矛。"""
    x, y = px(*center)
    W, H = pr(w), pr(h)
    d = ink.d
    for k, wd in ((0, 8), (24, 4)):
        d.rounded_rectangle((x - W / 2 + k, y - H / 2 + k, x + W / 2 - k, y + H / 2 - k), radius=H * 0.25, outline=255, width=wd)
    for sx in (-1, 1):
        cx = x + sx * (W / 2 + H * 0.28)
        pts = []
        for t in np.linspace(0, 4 * math.pi, 120):
            r = H * 0.32 * (1 - t / (4.6 * math.pi))
            pts.append((cx + sx * r * math.cos(t), y + r * math.sin(t)))
        d.line(pts, fill=255, width=6)
    f = _font(FONT_SERIF, int(H * 0.5))
    d.text((x, y - H * 0.06), "A T L A N T I S", fill=255, font=f, anchor="mm")
    f2 = _font(FONT_JP, int(H * 0.13))
    d.text((x, y + H * 0.33), "ポセイドンの都 ― 『クリティアス』による想像図", fill=255, font=f2, anchor="mm")


def draw_plan(ink):
    c = (0.0, 0.0)
    for kind, r0, r1, name in P.RINGS:
        if kind == "water":
            ink.hatch_annulus(r0, r1, spacing=26, w=2)
    for kind, r0, r1, name in P.RINGS:
        ink.circle(c, r1, 5)
    ink.circle(c, P.R_ISLAND, 5)
    for r, mat, h, t, towers in P.WALLS:
        ink.circle(c, r - 8, 9)
        for k in range(towers):
            a = 360 * k / towers
            x, y = P.polar(r - 8, a)
            ink.rect(x, y, P.TOWER_W * 1.6, P.TOWER_W * 1.6, rot=a, fill=True)
    for r in P.HIPPODROME:
        n = 180
        for k in range(0, n, 2):
            a0, a1 = 360 * k / n, 360 * (k + 1) / n
            ink.poly([P.polar(r, a0), P.polar(r, a1)], 3, close=False)
    for a in P.BRIDGE_AXES:
        mid = (P.R_ISLAND + P.R_OUTER) / 2
        x, y = P.polar(mid, a)
        ink.rect(x, y, P.R_OUTER - P.R_ISLAND, P.BRIDGE_W, rot=a, w=4)
    cw = P.CANAL_W
    ink.poly([(-cw / 2, -P.R_OUTER), (-cw / 2, P.COAST_Y_3D)], 5, close=False)
    ink.poly([(cw / 2, -P.R_OUTER), (cw / 2, P.COAST_Y_3D)], 5, close=False)
    # 海岸と波
    ink.poly([(X0 + 200, P.COAST_Y_3D), (-cw / 2 - 60, P.COAST_Y_3D)], 5, close=False)
    ink.poly([(cw / 2 + 60, P.COAST_Y_3D), (X1 - 200, P.COAST_Y_3D)], 5, close=False)
    for row in range(3):
        for k in range(16):
            x = X0 + 400 + k * 380 + (row % 2) * 190
            y = P.COAST_Y_3D - 160 - row * 160
            pts = [(x + 60 * t, y + 25 * math.sin(t * math.pi)) for t in np.linspace(0, 2, 12)]
            ink.poly(pts, 3, close=False)
    tx, ty = P.TEMPLE_CENTER
    ink.rect(tx, ty, P.TEMPLE_W, P.TEMPLE_L, w=6)
    ink.rect(tx, ty, P.TEMPLE_W - 30, P.TEMPLE_L - 40, w=3)
    for x, y, _ in P.PALACES:
        ink.rect(x, y, *P.PALACE_SIZE[:2], w=4)
    for r, a in P.ROUND_TEMPLES:
        ink.circle(P.polar(r, a), P.ROUND_TEMPLE_R, 4)
    for r, a in P.STOAS:
        x, y = P.polar(r, a)
        ink.rect(x, y, *P.STOA_SIZE[:2], rot=a + 90, w=3)
    for r, a in P.BARRACKS_RING1 + P.BARRACKS_RING2:
        x, y = P.polar(r, a)
        ink.rect(x, y, *P.BARRACKS_SIZE[:2], rot=a + 90, w=3)
    # 灯台
    lx, ly = P.LIGHTHOUSE
    ink.circle((lx, ly), 30, 5)
    for k in range(8):
        a = k * 45
        (ax, ay), (bx, by) = P.polar(40, a), P.polar(80, a)
        ink.poly([(lx + ax, ly + ay), (lx + bx, ly + by)], 3, close=False)
    # 北の山並み
    for k in range(18):
        x = X0 + 500 + k * 330
        y = 2950 + 60 * math.sin(k * 1.7)
        ink.poly([(x - 150, y - 80), (x, y + 140), (x + 150, y - 80)], 4, close=False)
        ink.poly([(x - 30, y + 80), (x + 40, y - 20)], 2, close=False)
    # 注記
    ink.text("ポセイドン神殿", (0, -330), 46)
    ink.text("大運河", (cw / 2 + 140, -P.R_OUTER - 600), 52)
    ink.text("外海", (-1800, P.COAST_Y_3D - 420), 60)
    ink.text("競馬場", P.polar(P.HIPPODROME[1] + 60, 140), 44)


def main(out):
    os.makedirs(out, exist_ok=True)
    ink = Ink()
    draw_plan(ink)
    meander_border(ink)
    compass(ink, (2500.0, -3700.0), 520.0)
    cartouche(ink, (0.0, 3420.0), 3600.0, 560.0)
    mask = ink.mask.filter(ImageFilter.GaussianBlur(0.8))
    base = parchment_base()
    m = np.array(mask, np.float32)[..., None] / 255.0
    # インクのにじみ: マスクを少しぼかして薄く重ねる
    bleed = np.array(mask.filter(ImageFilter.GaussianBlur(4)), np.float32)[..., None] / 255.0 * 0.25
    ink_col = np.array(SEPIA, np.float32)
    img = base.astype(np.float32) * (1 - np.clip(m * 0.92 + bleed, 0, 1)) + ink_col * np.clip(m * 0.92 + bleed, 0, 1)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(os.path.join(out, "parchment.png"))
    mask.save(os.path.join(out, "ink_mask.png"))
    print("wrote", out, PX_W, PX_H)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(HERE)), "out", "atlantis", "tex"))
