# 地形。原点 = 囲い遺構 D の床の中心。+Y を北とみなす。単位 m。
# 遺跡は石灰岩の丘陵の上にあり、南にハッラーン平原を見下ろす（位置関係は概略。等高線の再現ではない）。
# 囲い遺構は周囲の地面より掘り下がっている（D の床は岩盤を削って均したもの）。
import math

import bmesh
from mathutils import Vector, noise

from util import mesh_object

SURFACE = 2.4  # 囲いの外の地表の高さ（床からの高さ）。壁の天端とほぼ同じにする


class Hollow:
    """地表を掘り下げる円形の範囲。囲い遺構ひとつにつきひとつ。"""

    def __init__(self, center, r_floor, r_rim, floor_z=0.0):
        self.c = Vector((center[0], center[1]))
        self.r_floor = r_floor
        self.r_rim = r_rim
        self.floor_z = floor_z


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def height(x, y, hollows):
    p = Vector((x, y, 0))
    r = math.hypot(x, y)
    # 丘: 遺跡の周りはゆるい高まり、南へ行くほど平原へ下る
    h = SURFACE + 3.0 * (math.exp(-((r / 90) ** 2)) - 1)
    south = _smooth((-y - 60) / 900)
    h -= 45 * south
    far = _smooth((r - 400) / 1500)
    h += 60 * far * (1 - south) * (0.5 + 0.5 * noise.noise(p * 0.002))  # 北・東西の遠い山並み
    # 起伏
    h += 1.2 * noise.fractal(p * 0.02, 0.5, 2.0, 5) * _smooth(r / 30)
    h += 0.15 * noise.noise(p * 0.4)
    # 囲いの掘り込み
    for hl in hollows:
        d = (Vector((x, y)) - hl.c).length
        if d < hl.r_rim:
            t = _smooth((d - hl.r_floor) / (hl.r_rim - hl.r_floor))
            h = hl.floor_z + 0.05 * noise.noise(p * 2) + (h - hl.floor_z) * t
    return h


def _grid(name, p, n, coord, hollows, sink=None):
    bm = bmesh.new()
    rows = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            x, y = coord(i / n * 2 - 1, j / n * 2 - 1)
            z = height(x, y, hollows)
            if sink and sink(x, y):
                z -= 0.6  # 近景の格子の下に隠す
            row.append(bm.verts.new((x, y, z)))
        rows.append(row)
    for j in range(n):
        for i in range(n):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    obj = mesh_object(name, bm, p.ground)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def build(p, hollows, near=140.0, near_res=280, far=4000.0, far_res=220):
    """近景（0.5m 格子の正方形）と遠景（中心ほど細かい u^2 格子）の2枚。遠景は近景の範囲を沈めて隠す。"""
    h = near / 2
    near_obj = _grid("TerrainNear", p, near_res, lambda u, v: (u * h, v * h), hollows)
    far_obj = _grid(
        "TerrainFar",
        p,
        far_res,
        lambda u, v: (math.copysign(u * u, u) * far / 2, math.copysign(v * v, v) * far / 2),
        hollows,
        sink=lambda x, y: abs(x) < h - 1 and abs(y) < h - 1,
    )
    return near_obj, far_obj
