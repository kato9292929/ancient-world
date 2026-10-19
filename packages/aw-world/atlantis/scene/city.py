# 都の形。寸法は plan.py。要素ごとに 1 つのメッシュにまとめ（塔はまとめて 1 つ、など）、肉付けの単位にする。
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

import plan as P

LAND_TOP = 6.0  # 陸の環の天端（海面 0 から）
ISLAND_EDGE = 8.0
HILL_TOP = 28.0  # 神殿の基壇が載る丘の頂
BASIN = -14.0  # 環の水路と運河の底
SCROLL_Z = 3.0


class MB:
    """メッシュの組み立て。頂点はワールド座標で足し、最後に原点を base に置く。"""

    def __init__(self):
        self.bm = bmesh.new()
        self.mat_index = 0

    def _faces(self, faces):
        for f in faces:
            f.material_index = self.mat_index

    def box(self, c, size, rot=0.0, mat=0):
        self.mat_index = mat
        g = bmesh.ops.create_cube(self.bm, size=1.0)
        R = Matrix.Rotation(math.radians(rot), 3, "Z")
        for v in g["verts"]:
            v.co = R @ Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2])) + Vector(c)
        self._faces({f for v in g["verts"] for f in v.link_faces})

    def cyl(self, c, r, h, seg=16, r_top=None, mat=0):
        self.mat_index = mat
        g = bmesh.ops.create_cone(self.bm, cap_ends=True, segments=seg, radius1=r, radius2=r if r_top is None else r_top, depth=h)
        for v in g["verts"]:
            v.co += Vector((c[0], c[1], c[2] + h / 2))
        self._faces({f for v in g["verts"] for f in v.link_faces})

    def annulus(self, r0, r1, z0, z1, seg=192, mat=0, top_mat=None, top_fn=None):
        """円環の立体（内周・外周の壁と天端）。top_fn(r) で天端の高さを変えられる。"""
        bm = self.bm
        rings = []
        steps = [r0, r1] if top_fn is None else [r0 + (r1 - r0) * k / 12 for k in range(13)]
        bottom_in = [bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), z0)) for a in [2 * math.pi * i / seg for i in range(seg)]]
        for r in steps:
            z = z1 if top_fn is None else top_fn(r)
            rings.append([bm.verts.new((r * math.cos(a), r * math.sin(a), z)) for a in [2 * math.pi * i / seg for i in range(seg)]])
        bottom_out = [bm.verts.new((r1 * math.cos(a), r1 * math.sin(a), z0)) for a in [2 * math.pi * i / seg for i in range(seg)]]
        side = []
        tops = []
        for i in range(seg):
            j = (i + 1) % seg
            side.append(bm.faces.new((bottom_in[j], bottom_in[i], rings[0][i], rings[0][j])))
            for a, b in zip(rings, rings[1:]):
                tops.append(bm.faces.new((a[i], a[j], b[j], b[i])))
            side.append(bm.faces.new((rings[-1][j], rings[-1][i], bottom_out[i], bottom_out[j])))
        for f in side:
            f.material_index = mat
        for f in tops:
            f.material_index = mat if top_mat is None else top_mat

    def disc(self, r, z_fn, z0, seg=128, rings=24, mat=0, top_mat=None):
        """円盤状の島（中心が高い丘）。"""
        bm = self.bm
        center = bm.verts.new((0, 0, z_fn(0.0)))
        loops = []
        for k in range(1, rings + 1):
            rr = r * k / rings
            loops.append([bm.verts.new((rr * math.cos(a), rr * math.sin(a), z_fn(rr))) for a in [2 * math.pi * i / seg for i in range(seg)]])
        bottom = [bm.verts.new((r * math.cos(a), r * math.sin(a), z0)) for a in [2 * math.pi * i / seg for i in range(seg)]]
        tops = []
        for i in range(seg):
            j = (i + 1) % seg
            tops.append(bm.faces.new((center, loops[0][i], loops[0][j])))
            for a, b in zip(loops, loops[1:]):
                tops.append(bm.faces.new((a[i], b[i], b[j], a[j])))
            f = bm.faces.new((loops[-1][j], loops[-1][i], bottom[i], bottom[j]))
            f.material_index = mat
        for f in tops:
            f.material_index = mat if top_mat is None else top_mat

    def prism_gable(self, c, size, rot, mat=0):
        """切妻屋根（長手方向 = 局所 X）。"""
        self.mat_index = mat
        L, W, H = size
        R = Matrix.Rotation(math.radians(rot), 3, "Z")
        pts = [(-L / 2, -W / 2, 0), (L / 2, -W / 2, 0), (L / 2, W / 2, 0), (-L / 2, W / 2, 0), (-L / 2, 0, H), (L / 2, 0, H)]
        vs = [self.bm.verts.new(R @ Vector(p) + Vector(c)) for p in pts]
        faces = [(0, 1, 5, 4), (2, 3, 4, 5), (0, 4, 3), (1, 2, 5), (3, 2, 1, 0)]
        self._faces([self.bm.faces.new([vs[i] for i in f]) for f in faces])

    def finish(self, name, mats, base=(0, 0, 0), smooth=False, collection=None):
        me = bpy.data.meshes.new(name)
        for v in self.bm.verts:
            v.co -= Vector(base)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces[:])
        self.bm.to_mesh(me)
        self.bm.free()
        for m in mats:
            me.materials.append(m)
        if smooth:
            for p in me.polygons:
                p.use_smooth = True
        obj = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(obj)
        obj.location = base
        return obj


# ---------------------------------------------------------------- 地形
def island_height(r):
    t = max(0.0, 1 - r / (P.R_ISLAND * 0.85))
    z = ISLAND_EDGE + (HILL_TOP - ISLAND_EDGE) * (t * t * (3 - 2 * t))
    if r < 150:
        z = HILL_TOP
    return z


def land(M):
    """中央島（丘）と陸の環 2 つ。側面は石張りの護岸、天端は庭と土。"""
    mb = MB()
    mb.disc(P.R_ISLAND, island_height, BASIN, mat=0, top_mat=1)
    for kind, r0, r1, name in P.RINGS:
        if kind == "land":
            mb.annulus(r0, r1, BASIN, LAND_TOP, mat=0, top_mat=1)
    # 外側の水の環の外岸（平野との境の護岸）
    mb.annulus(P.R_OUTER, P.R_OUTER + 12, BASIN, 1.0, mat=0, top_mat=1)
    return mb.finish("LandRings", [M.stone, M.ground_city])


def plain_height(x, y):
    p = Vector((x * 0.0004, y * 0.0004, 0.0))
    z = 0.8 + 1.2 * noise.fractal(p, 0.5, 2.0, 4)
    r = math.hypot(x, y)
    if r < P.R_OUTER + 6:
        return BASIN
    if abs(x) < P.CANAL_W / 2 + 2 and P.COAST_Y_3D - 50 < y < 0:
        return BASIN
    if y < P.COAST_Y_3D:
        d = P.COAST_Y_3D - y
        return max(-30.0, 0.4 - d * 0.06)
    if y < P.COAST_Y_3D + 60:  # 浜
        return 0.4 + (y - P.COAST_Y_3D) / 60 * (z - 0.4)
    # 巻物の外では少しずつ起伏を大きくする
    far = max(0.0, (r - 4200) / 6000)
    z += 25 * far * (0.5 + 0.5 * noise.noise(p * 3))
    return max(0.4, z)


def _axis(limit, fine_half, fine_step, mid, mid_step, far_step):
    xs = set()
    x = 0.0
    while x <= limit:
        xs.add(x)
        xs.add(-x)
        x += fine_step if x < fine_half else (mid_step if x < mid else far_step)
    return sorted(xs)


def plain(M):
    """平野と海底。運河の付近だけ格子を細かくして、運河の縁を立てる。"""
    xs = _axis(14000, 80, 6, 4500, 40, 220)
    ys = _axis(14000, 0, 40, 5200, 40, 220)
    bm = bmesh.new()
    grid = [[bm.verts.new((x, y, plain_height(x, y))) for x in xs] for y in ys]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
    me = bpy.data.meshes.new("Plain")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.ground)
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new("Plain", me)
    bpy.context.scene.collection.objects.link(obj)
    # 運河の護岸
    mb = MB()
    length = abs(P.COAST_Y_3D) - P.R_OUTER + 20
    for sx in (-1, 1):
        mb.box((sx * (P.CANAL_W / 2 + 3), -P.R_OUTER - length / 2 + 10, (BASIN + 1.5) / 2), (6, length, 1.5 - BASIN))
    mb.finish("CanalBanks", [M.stone])
    return obj


def mountains(M):
    """北の山並み。原点を麓に置き、Z の伸びで「せり上がる」。"""
    bm = bmesh.new()
    nx, ny = 220, 70
    x0, x1, y0, y1 = -16000.0, 16000.0, 5200.0, 15000.0
    rows = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            x = x0 + (x1 - x0) * i / nx
            y = y0 + (y1 - y0) * j / ny
            p = Vector((x * 0.00025, y * 0.00025, 0))
            ridge = 1 - abs(noise.noise(p * 1.3))
            t = min(1.0, (y - y0) / 3500)
            h = (300 + 1300 * ridge * ridge) * (t * t * (3 - 2 * t)) + 180 * noise.fractal(p * 6, 0.5, 2.0, 4)
            row.append(bm.verts.new((x, y, max(0.0, h))))
        rows.append(row)
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))
    me = bpy.data.meshes.new("Mountains")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.forest)
    for p in me.polygons:
        p.use_smooth = True
    obj = bpy.data.objects.new("Mountains", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------- 城壁・塔・橋
def walls(M):
    out = []
    mats = {"bronze": M.bronze, "tin": M.tin, "orichalcum": M.orichalcum}
    for r, mat, h, t, towers in P.WALLS:
        base = ISLAND_EDGE if mat == "orichalcum" else LAND_TOP
        mb = MB()
        mb.annulus(r - t, r, base - 1, base + h, seg=256)
        # 狭間（胸壁の凹凸）
        n = int(2 * math.pi * r / 8)
        for k in range(n):
            if k % 2:
                continue
            a = 360 * k / n
            x, y = P.polar(r - t / 2, a)
            mb.box((x, y, base + h + 0.9), (t, 3.2, 1.8), rot=a)
        for k in range(towers):
            a = 360 * k / towers
            x, y = P.polar(r - t / 2, a)
            mb.box((x, y, base + P.TOWER_H / 2 - 1), (P.TOWER_W, P.TOWER_W, P.TOWER_H), rot=a)
            mb.box((x, y, base + P.TOWER_H), (P.TOWER_W + 2, P.TOWER_W + 2, 1.2), rot=a)
        out.append(mb.finish(f"Wall_{mat}", [mats[mat]], base=(0, 0, base - 1)))
    return out


def tower_tops():
    """篝火を置く塔の天端（4 基に 1 基）。"""
    pts = []
    for r, mat, h, t, towers in P.WALLS:
        base = ISLAND_EDGE if mat == "orichalcum" else LAND_TOP
        for k in range(0, towers, 4):
            x, y = P.polar(r - t / 2, 360 * k / towers)
            pts.append((x, y, base + P.TOWER_H + 1.5))
    return pts


def bridges(M):
    mb = MB()
    for a in P.BRIDGE_AXES:
        for kind, r0, r1, name in P.RINGS:
            if kind != "water":
                continue
            mid = (r0 + r1) / 2
            x, y = P.polar(mid, a)
            mb.box((x, y, LAND_TOP + 1.5), (r1 - r0 + 30, P.BRIDGE_W, 3.0), rot=a)
            # 橋脚とアーチの代わりの壁柱
            n = int((r1 - r0) / 46)
            for k in range(1, n):
                rr = r0 + (r1 - r0) * k / n
                px, py = P.polar(rr, a)
                mb.box((px, py, (BASIN + LAND_TOP) / 2), (7, P.BRIDGE_W - 4, LAND_TOP - BASIN), rot=a)
            # 両側の門塔
            for rr in (r0 - 8, r1 + 8):
                for side in (-1, 1):
                    px, py = P.polar(rr, a)
                    ox, oy = P.polar(P.BRIDGE_W / 2 + 6, a + 90 * side)
                    mb.box((px + ox, py + oy, LAND_TOP + 9), (12, 12, 18), rot=a)
    return mb.finish("Bridges", [M.stone], base=(0, 0, BASIN))


# ---------------------------------------------------------------- 陸の環の建物
def buildings(M):
    out = []
    # 兵舎（瓦の切妻）
    mb = MB()
    for r, a in P.BARRACKS_RING1 + P.BARRACKS_RING2:
        x, y = P.polar(r, a)
        L, W, H = P.BARRACKS_SIZE
        mb.box((x, y, LAND_TOP + H / 2), (L, W, H), rot=a + 90, mat=0)
        mb.prism_gable((x, y, LAND_TOP + H), (L + 2, W + 2, 5.0), a + 90, mat=1)
    out.append(mb.finish("Barracks", [M.stone_fine, M.roof_tiles], base=(0, 0, LAND_TOP)))
    # 王宮（中庭を囲む四棟）
    mb = MB()
    for x, y, _ in P.PALACES:
        L, W, H = P.PALACE_SIZE
        z = island_height(math.hypot(x, y))
        for dx, dy, l, w in ((0, W / 2 - 8, L, 16), (0, -W / 2 + 8, L, 16), (L / 2 - 8, 0, 16, W), (-L / 2 + 8, 0, 16, W)):
            mb.box((x + dx, y + dy, z + H / 2 - 4), (l, w, H + 8), mat=0)
            mb.prism_gable((x + dx, y + dy, z + H + 4), (l + 2, w + 2, 6.0) if l > w else (w + 2, l + 2, 6.0), 0 if l > w else 90, mat=1)
        mb.box((x, y, z + 0.2), (L - 32, W - 32, 0.5), mat=2)
    out.append(mb.finish("Palaces", [M.marble, M.roof_tiles, M.stone_plain], base=(0, 0, ISLAND_EDGE)))
    # 円形神殿（円柱の環＋円錐屋根）
    mb = MB()
    for r, a in P.ROUND_TEMPLES:
        x, y = P.polar(r, a)
        R = P.ROUND_TEMPLE_R
        mb.cyl((x, y, LAND_TOP), R + 3, 2.0, seg=32, mat=0)
        mb.cyl((x, y, LAND_TOP + 2), R * 0.6, 12.0, seg=32, mat=0)
        for k in range(16):
            cx, cy = P.polar(R, 360 * k / 16)
            mb.cyl((x + cx, y + cy, LAND_TOP + 2), 0.9, 12.0, seg=10, mat=0)
        mb.cyl((x, y, LAND_TOP + 14), R + 1.5, 2.0, seg=32, mat=0)
        mb.cyl((x, y, LAND_TOP + 16), R + 2, 8.0, seg=32, r_top=1.0, mat=1)
    out.append(mb.finish("RoundTemples", [M.marble, M.orichalcum], base=(0, 0, LAND_TOP)))
    # 柱廊（背壁＋列柱＋片流れの屋根）
    mb = MB()
    for r, a in P.STOAS:
        x, y = P.polar(r, a)
        L, W, H = P.STOA_SIZE
        R = Matrix.Rotation(math.radians(a + 90), 3, "Z")
        back = R @ Vector((0, W / 2 - 1.5, 0))
        mb.box((x + back.x, y + back.y, LAND_TOP + H / 2), (L, 3, H), rot=a + 90)
        n = 22
        for k in range(n):
            v = R @ Vector((-L / 2 + 3 + (L - 6) * k / (n - 1), -W / 2 + 2, 0))
            mb.cyl((x + v.x, y + v.y, LAND_TOP), 0.8, H, seg=10)
        mb.box((x, y, LAND_TOP + H + 0.8), (L + 2, W + 2, 1.6), rot=a + 90, mat=1)
    out.append(mb.finish("Stoas", [M.marble, M.roof_tiles], base=(0, 0, LAND_TOP)))
    # 競馬場（砂の走路と中央の分離帯）
    mb = MB()
    r0, r1 = P.HIPPODROME
    mb.annulus(r0, r1, LAND_TOP - 0.5, LAND_TOP + 0.15, seg=256, mat=0)
    mb.annulus((r0 + r1) / 2 - 4, (r0 + r1) / 2 + 4, LAND_TOP, LAND_TOP + 2.0, seg=256, mat=1)
    mb.annulus(r0 - 4, r0, LAND_TOP, LAND_TOP + 6, seg=256, mat=1)
    mb.annulus(r1, r1 + 4, LAND_TOP, LAND_TOP + 6, seg=256, mat=1)
    out.append(mb.finish("Hippodrome", [M.sand, M.stone_fine], base=(0, 0, LAND_TOP - 0.5)))
    # 泉（温泉と冷泉の池と柱廊）
    mb = MB()
    for x, y, _ in P.SPRINGS:
        z = island_height(math.hypot(x, y))
        mb.cyl((x, y, z - 1), 22, 1.6, seg=32, mat=0)
        for k in range(12):
            cx, cy = P.polar(26, 30 * k)
            mb.cyl((x + cx, y + cy, z), 0.7, 7, seg=8, mat=0)
        mb.cyl((x, y, z + 0.4), 18, 0.3, seg=32, mat=1)
    out.append(mb.finish("Springs", [M.marble, M.ring_water], base=(0, 0, ISLAND_EDGE)))
    return out


# ---------------------------------------------------------------- 神殿
TEMPLE_Z = HILL_TOP


def temple(M):
    """ポセイドン神殿。肉付けの順に、基壇・柱（1 本ずつ）・梁と屋根・金の飾りを別オブジェクトにする。"""
    cx, cy = P.TEMPLE_CENTER
    L, W = P.TEMPLE_L, P.TEMPLE_W
    z = TEMPLE_Z
    parts = {}
    mb = MB()
    for k in range(3):
        mb.box((cx, cy, z + P.TEMPLE_PODIUM_H * (k + 0.5) / 3), (W - k * 5, L - k * 5, P.TEMPLE_PODIUM_H / 3), mat=0)
    # 南の階段
    for k in range(10):
        mb.box((cx, cy - L / 2 - 6 + k * 0.9, z + 0.3 + k * 0.6), (30, 2.0, 0.6), mat=0)
    cl, cw_ = L - 40, W - 36
    mb.box((cx, cy, z + P.TEMPLE_PODIUM_H + P.TEMPLE_COL_H / 2), (cw_, cl, P.TEMPLE_COL_H), mat=1)
    parts["podium"] = mb.finish("TemplePodium", [M.stone, M.marble], base=(cx, cy, z))

    cols = []
    from_dxf = _temple_columns()
    # 南正面の中央から左右へ、次に側面を南から北へ、最後に北正面（建て込みの順）
    from_dxf.sort(key=lambda p: (p[1] > -L / 2 + 10, p[1], abs(p[0])))
    zc = z + P.TEMPLE_PODIUM_H
    for i, (x, y) in enumerate(from_dxf):
        mb = MB()
        mb.cyl((cx + x, cy + y, zc), P.TEMPLE_COL_R * 1.15, 1.2, seg=20, mat=0)
        mb.cyl((cx + x, cy + y, zc + 1.2), P.TEMPLE_COL_R, P.TEMPLE_COL_H - 3.2, seg=20, r_top=P.TEMPLE_COL_R * 0.85, mat=0)
        mb.cyl((cx + x, cy + y, zc + P.TEMPLE_COL_H - 2.0), P.TEMPLE_COL_R * 0.85, 0.8, seg=20, r_top=P.TEMPLE_COL_R * 1.3, mat=1)
        mb.box((cx + x, cy + y, zc + P.TEMPLE_COL_H - 0.6), (P.TEMPLE_COL_R * 2.8, P.TEMPLE_COL_R * 2.8, 1.2), mat=1)
        o = mb.finish(f"TempleCol{i:03d}", [M.silver, M.gold], base=(cx + x, cy + y, zc))
        for p in o.data.polygons:
            p.use_smooth = True
        cols.append(o)
    parts["columns"] = cols

    top = zc + P.TEMPLE_COL_H
    mb = MB()
    mb.box((cx, cy, top + P.TEMPLE_ENTAB_H / 2), (W - 6, L - 6, P.TEMPLE_ENTAB_H), mat=0)
    mb.box((cx, cy, top + P.TEMPLE_ENTAB_H * 0.55), (W - 5, L - 5, 1.4), mat=1)  # 金の帯（フリーズ）
    mb.prism_gable((cx, cy, top + P.TEMPLE_ENTAB_H), (L - 4, W - 2, P.TEMPLE_ROOF_H), 90, mat=2)
    parts["roof"] = mb.finish("TempleRoof", [M.silver, M.gold, M.orichalcum], base=(cx, cy, top))

    mb = MB()
    ridge = top + P.TEMPLE_ENTAB_H + P.TEMPLE_ROOF_H
    for sy in (-1, 1):
        mb.cyl((cx, cy + sy * (L / 2 - 2), ridge), 2.2, 5.0, seg=12, r_top=0.4)  # 棟の頂の飾り
        for sx in (-1, 1):
            mb.cyl((cx + sx * (W / 2 - 2), cy + sy * (L / 2 - 2), top + P.TEMPLE_ENTAB_H), 1.6, 4.0, seg=10, r_top=0.3)
    for k in range(1, 12):
        mb.cyl((cx, cy - L / 2 + 2 + (L - 4) * k / 12, ridge - 0.5), 0.8, 2.5, seg=8, r_top=0.2)
    # 黄金の囲い（神殿の北のクレイトとポセイドンの聖所）
    gx, gy, gr, gl = P.GOLD_ENCLOSURE
    gy = cy + L / 2 + gl / 2 + 4
    for k in range(40):
        a = 2 * math.pi * k / 40
        mb.cyl((gx + gr * math.cos(a), gy + gr * 0.8 * math.sin(a), z), 0.4, 3.0, seg=6)
    mb.cyl((gx, gy, z), gr + 0.6, 0.4, seg=48)
    parts["gold"] = mb.finish("TempleGold", [M.gold], base=(cx, cy, top))
    mb = MB()
    mb.cyl((gx, gy, z), gr * 0.45, 9.0, seg=24, mat=0)
    mb.cyl((gx, gy, z + 9), gr * 0.5, 5.0, seg=24, r_top=1.0, mat=1)
    parts["shrine"] = mb.finish("ClitoShrine", [M.marble, M.gold], base=(gx, gy, z))

    # 三叉の矛の記念柱（演出）
    tx, ty = P.TRIDENT_COLUMN
    tz = island_height(math.hypot(tx, ty))
    mb = MB()
    mb.box((tx, ty, tz + 1.5), (6, 6, 3), mat=0)
    mb.cyl((tx, ty, tz + 3), 1.1, P.TRIDENT_COL_H, seg=20, r_top=0.9, mat=0)
    top_t = tz + 3 + P.TRIDENT_COL_H
    mb.cyl((tx, ty, top_t), 0.35, 7.0, seg=10, mat=1)
    mb.box((tx, ty, top_t + 5.0), (5.0, 0.6, 0.6), mat=1)
    for sx in (-1, 0, 1):
        mb.cyl((tx + sx * 2.2, ty, top_t + 5.0), 0.28, 4.5 if sx == 0 else 3.6, seg=8, r_top=0.02, mat=1)
    parts["trident"] = mb.finish("TridentColumn", [M.marble, M.gold], base=(tx, ty, tz))
    return parts


def _temple_columns():
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


# ---------------------------------------------------------------- 港・灯台・船台
def harbor(M):
    out = {}
    cy = P.COAST_Y_3D
    mb = MB()
    # 外港の防波堤（運河の河口を両側から抱く）
    for sx in (-1, 1):
        pts = [(sx * (P.CANAL_W / 2 + 20 + 160 * math.sin(t * math.pi / 2)), cy - 340 * t) for t in [k / 14 for k in range(15)]]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            a = math.degrees(math.atan2(y1 - y0, x1 - x0))
            mb.box(((x0 + x1) / 2, (y0 + y1) / 2, -5), (math.hypot(x1 - x0, y1 - y0) + 6, 22, 14), rot=a)
    out["moles"] = mb.finish("Moles", [M.stone], base=(0, 0, -12))
    lx, ly = P.LIGHTHOUSE
    mb = MB()
    mb.box((lx, ly, -6), (40, 40, 16), mat=0)
    mb.box((lx, ly, 2 + 9), (24, 24, 18), mat=0)
    mb.cyl((lx, ly, 20), 9, 26, seg=24, r_top=7, mat=0)
    mb.cyl((lx, ly, 46), 6.5, 8, seg=16, mat=0)
    mb.cyl((lx, ly, 54), 7.5, 1.5, seg=16, r_top=4, mat=1)
    out["lighthouse"] = mb.finish("Lighthouse", [M.marble, M.bronze], base=(lx, ly, -14))
    mb = MB()
    mb.cyl((lx, ly, 47), 3.2, 6.5, seg=12)
    out["beacon"] = mb.finish("Beacon", [M.beacon], base=(lx, ly, 47))
    # 船台（屋根のある斜路）。運河の東岸
    sx, sy = P.SHIPYARD
    mb = MB()
    for k in range(4):
        x = sx + 18 + k * 26
        mb.box((x, sy, 2.0), (16, 60, 1.0), mat=0)
        mb.prism_gable((x, sy, 14.0), (64, 22, 7), 90, mat=1)
        for px_ in (-10, 10):
            for py_ in (-28, 0, 28):
                mb.box((x + px_, sy + py_, 7.5), (1.2, 1.2, 13), mat=0)
    out["shipyard"] = mb.finish("Shipyard", [M.wood, M.roof_tiles], base=(sx, sy, 0))
    return out


# ---------------------------------------------------------------- 三段櫂船
def trireme(M, name="Trireme"):
    """三段櫂船（長さ約 37m）。船体・三段の櫂・帆柱と帆。原点は喫水線の中央、船首は +Y。"""
    mb = MB()
    L, W = 37.0, 5.0
    hull = []
    for k in range(13):
        t = k / 12
        y = -L / 2 + L * t
        w = W / 2 * math.sin(math.pi * min(1, t * 1.15)) ** 0.6
        hull.append((y, max(0.4, w)))
    bm = mb.bm
    rows = []
    for y, w in hull:
        rows.append([bm.verts.new(c) for c in ((-w, y, 2.6), (-w * 0.8, y, 0.0), (0, y, -1.2), (w * 0.8, y, 0.0), (w, y, 2.6))])
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    bm.faces.new(list(reversed(rows[0])))
    bm.faces.new(rows[-1])
    mb.box((0, 0, 2.7), (W * 0.95, L * 0.8, 0.3), mat=0)
    mb.box((0, L / 2 + 2.0, -0.3), (0.5, 4.0, 0.6), mat=1)  # 衝角（青銅）
    mb.cyl((0, -L / 2 + 1, 2.6), 0.5, 4.0, seg=8, r_top=0.2, mat=0)  # 船尾の反り
    for tier, (z, reach) in enumerate(((0.6, 4.2), (1.3, 4.8), (2.0, 5.4))):
        for k in range(27 if tier == 2 else 29):
            y = -L * 0.36 + L * 0.72 * k / 28
            for sx in (-1, 1):
                p0 = Vector((sx * W / 2 * 0.95, y, z))
                p1 = Vector((sx * (W / 2 + reach), y - 0.6, -0.4))
                d = p1 - p0
                c = (p0 + p1) / 2
                g = bmesh.ops.create_cone(bm, cap_ends=False, segments=4, radius1=0.07, radius2=0.07, depth=d.length)
                rot = d.to_track_quat("Z", "Y").to_matrix()
                for v in g["verts"]:
                    v.co = rot @ v.co + c
                for f in {f for v in g["verts"] for f in v.link_faces}:
                    f.material_index = 0
    mb.cyl((0, 2.0, 2.7), 0.25, 14.0, seg=8, mat=0)
    mb.box((0, 2.0, 15.5), (12.0, 0.25, 0.25), mat=0)
    mb.box((0, 2.3, 11.0), (11.0, 0.12, 8.0), mat=2)
    return mb.finish(name, [M.wood, M.bronze, M.sail])


# ---------------------------------------------------------------- 庭木・森・オリーブ畑・家並み（ジオメトリノードの複製）
def _points(name, pts, attrs):
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(pts))
    me.vertices.foreach_set("co", [c for p in pts for c in p])
    for key, (kind, vals) in attrs.items():
        a = me.attributes.new(key, kind, "POINT")
        a.data.foreach_set("value", vals)
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def instancer(obj, collection, grow_default=1.0, softness=0.08):
    """点ごとに collection の中の 1 つを複製する。属性: variant（何番目）、rot（Z 回転）、scl（大きさ）、
    birth（0..1。入力 Grow がこれを越えると育つ）。"""
    ng = bpy.data.node_groups.new(obj.name + "GN", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    sock = ng.interface.new_socket("Grow", in_out="INPUT", socket_type="NodeSocketFloat")
    sock.default_value = grow_default
    sock.min_value = -10.0
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    N = ng.nodes
    L = ng.links
    gi = N.new("NodeGroupInput")
    go = N.new("NodeGroupOutput")
    coll = N.new("GeometryNodeCollectionInfo")
    coll.inputs["Collection"].default_value = collection
    coll.inputs["Separate Children"].default_value = True
    coll.inputs["Reset Children"].default_value = True
    inst = N.new("GeometryNodeInstanceOnPoints")
    inst.inputs["Pick Instance"].default_value = True

    def attr(name, kind="FLOAT"):
        n = N.new("GeometryNodeInputNamedAttribute")
        n.data_type = kind
        n.inputs["Name"].default_value = name
        return n.outputs["Attribute"]

    L.new(gi.outputs["Geometry"], inst.inputs["Points"])
    L.new(coll.outputs["Instances"], inst.inputs["Instance"])
    L.new(attr("variant", "INT"), inst.inputs["Instance Index"])
    comb = N.new("ShaderNodeCombineXYZ")
    L.new(attr("rot"), comb.inputs["Z"])
    e2r = N.new("FunctionNodeEulerToRotation")
    L.new(comb.outputs[0], e2r.inputs[0])
    L.new(e2r.outputs[0], inst.inputs["Rotation"])
    sub = N.new("ShaderNodeMath")
    sub.operation = "SUBTRACT"
    L.new(gi.outputs["Grow"], sub.inputs[0])
    L.new(attr("birth"), sub.inputs[1])
    div = N.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    div.use_clamp = True
    L.new(sub.outputs[0], div.inputs[0])
    div.inputs[1].default_value = softness
    mul = N.new("ShaderNodeMath")
    mul.operation = "MULTIPLY"
    L.new(div.outputs[0], mul.inputs[0])
    L.new(attr("scl"), mul.inputs[1])
    L.new(mul.outputs[0], inst.inputs["Scale"])
    L.new(inst.outputs["Instances"], go.inputs["Geometry"])
    mod = obj.modifiers.new("Instancer", "NODES")
    mod.node_group = ng
    ident = ng.interface.items_tree["Grow"].identifier
    return mod, ident


def _hidden_collection(name, objs):
    col = bpy.data.collections.new(name)
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        col.objects.link(o)
    return col


def tree_kinds(M):
    """オリーブ（丸い樹冠）と糸杉（細い円錐）。"""
    kinds = []
    mb = MB()
    mb.cyl((0, 0, 0), 0.35, 2.5, seg=6, mat=0)
    bm = mb.bm
    for k in range(4):
        g = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=2.2)
        off = Vector((math.cos(k * 1.7) * 1.2, math.sin(k * 1.7) * 1.2, 3.6 + 0.4 * k % 2))
        for v in g["verts"]:
            v.co = Vector((v.co.x, v.co.y, v.co.z * 0.75)) + off
        for f in {f for v in g["verts"] for f in v.link_faces}:
            f.material_index = 1
    kinds.append(mb.finish("TreeOlive", [M.bark, M.olive], smooth=True))
    mb = MB()
    mb.cyl((0, 0, 0), 0.3, 1.5, seg=6, mat=0)
    mb.cyl((0, 0, 1.0), 1.4, 12.0, seg=10, r_top=0.15, mat=1)
    kinds.append(mb.finish("TreeCypress", [M.bark, M.cypress], smooth=True))
    mb = MB()
    mb.cyl((0, 0, 0), 2.0, 14.0, seg=7, r_top=0.2, mat=0)
    kinds.append(mb.finish("TreePine", [M.cypress], smooth=True))
    return kinds


def gardens(M, kinds, seed=2):
    """中央島と陸の環の庭木。birth は中心から外へ。"""
    rnd = random.Random(seed)
    pts, var, rot, scl, birth = [], [], [], [], []
    for _ in range(9000):
        r = math.sqrt(rnd.random()) * P.RINGS[3][2]
        a = rnd.uniform(0, 360)
        x, y = P.polar(r, a)
        kind = next((k for k, r0, r1, _ in P.RINGS if r0 <= r < r1), "island" if r < P.R_ISLAND else None)
        if kind == "water" or kind is None:
            continue
        if kind == "island":
            if abs(x - P.TEMPLE_CENTER[0]) < P.TEMPLE_W / 2 + 25 and abs(y - P.TEMPLE_CENTER[1]) < P.TEMPLE_L / 2 + 70:
                continue
            if r > P.R_ISLAND - 15:
                continue
            z = island_height(r)
        else:
            if P.HIPPODROME[0] - 6 < r < P.HIPPODROME[1] + 6:
                continue
            ring = next(rg for rg in P.RINGS if rg[1] <= r < rg[2])
            if r < ring[1] + 10 or r > ring[2] - 16:
                continue
            z = LAND_TOP
        pts.append((x, y, z))
        var.append(0 if rnd.random() < 0.6 else 1)
        rot.append(rnd.uniform(0, 6.28))
        scl.append(rnd.uniform(0.8, 1.3))
        birth.append(min(1.0, r / P.RINGS[3][2]))
    obj = _points("Gardens", pts, {"variant": ("INT", var), "rot": ("FLOAT", rot), "scl": ("FLOAT", scl), "birth": ("FLOAT", birth)})
    col = _hidden_collection("TreeKinds", kinds)
    mod, ident = instancer(obj, col)
    return obj, ident


def olive_groves(M, kinds, seed=4):
    """平野のオリーブ畑。区画（1 スタディオン）の中に格子で並ぶ。市街が広がるのと同時に現れる。"""
    rnd = random.Random(seed)
    pts, var, rot, scl, birth = [], [], [], [], []
    step = 14.0
    for bx in range(-30, 31):
        for by in range(-30, 31):
            if rnd.random() < 0.45:
                continue
            x0, y0 = bx * P.STADION, by * P.STADION
            r = math.hypot(x0, y0)
            if r < P.R_CITY_3D + 150 or r > 6500 or y0 < P.COAST_Y_3D + 200 or abs(x0) < 260:
                continue
            for i in range(1, int(P.STADION / step)):
                for j in range(1, int(P.STADION / step)):
                    x, y = x0 + i * step, y0 + j * step
                    pts.append((x, y, plain_height(x, y)))
                    var.append(0)
                    rot.append(rnd.uniform(0, 6.28))
                    scl.append(rnd.uniform(0.7, 1.0))
                    birth.append(min(1.0, (r - P.R_CITY_3D) / 4000))
    obj = _points("OliveGroves", pts, {"variant": ("INT", var), "rot": ("FLOAT", rot), "scl": ("FLOAT", scl), "birth": ("FLOAT", birth)})
    col = bpy.data.collections["TreeKinds"]
    mod, ident = instancer(obj, col)
    return obj, ident


def forest_on(mountains_obj, kinds, seed=6, count=70000):
    rnd = random.Random(seed)
    me = mountains_obj.data
    verts = me.vertices
    pts, var, rot, scl, birth = [], [], [], [], []
    n = len(verts)
    for _ in range(count):
        v = verts[rnd.randrange(n)].co
        if v.z < 40:
            continue
        jx, jy = rnd.uniform(-70, 70), rnd.uniform(-70, 70)
        pts.append((v.x + jx, v.y + jy, v.z - 2))
        var.append(2 if rnd.random() < 0.7 else 1)
        rot.append(rnd.uniform(0, 6.28))
        scl.append(rnd.uniform(1.4, 2.6))
        birth.append(0.0)
    obj = _points("Forest", pts, {"variant": ("INT", var), "rot": ("FLOAT", rot), "scl": ("FLOAT", scl), "birth": ("FLOAT", birth)})
    obj.parent = mountains_obj
    mod, ident = instancer(obj, bpy.data.collections["TreeKinds"])
    return obj


def house_kinds(M):
    kinds = []
    rnd = random.Random(8)
    for k in range(5):
        mb = MB()
        L, W, H = rnd.uniform(9, 16), rnd.uniform(7, 11), rnd.uniform(5, 9)
        mb.box((0, 0, H / 2), (L, W, H), mat=0)
        if k % 2 == 0:
            mb.prism_gable((0, 0, H), (L + 1, W + 1, 2.6), 0, mat=1)
        else:
            mb.box((0, 0, H + 0.3), (L + 0.6, W + 0.6, 0.6), mat=1)
            mb.box((L * 0.25, 0, H + 1.6), (L * 0.4, W * 0.6, 2.6), mat=0)
        kinds.append(mb.finish(f"House{k}", [M.house_wall if k % 3 else M.house_wall2, M.roof_tiles]))
    return kinds


def houses(M, kinds, seed=10):
    """環の外の市街。中心から外へ birth が増え、Grow で外へ広がる。運河沿いと浜は空ける。"""
    rnd = random.Random(seed)
    pts, var, rot, scl, birth = [], [], [], [], []
    block = 34.0
    r_max = P.R_CITY_3D
    n = int(r_max / block)
    for i in range(-n, n + 1):
        for j in range(-n, n + 1):
            x, y = i * block + rnd.uniform(-6, 6), j * block + rnd.uniform(-6, 6)
            r = math.hypot(x, y)
            if r < P.R_OUTER + 50 or r > r_max:
                continue
            if abs(x) < P.CANAL_W / 2 + 30 and y < 0:
                continue
            if y < P.COAST_Y_3D + 90:
                continue
            if abs(x - P.SHIPYARD[0] - 50) < 90 and abs(y - P.SHIPYARD[1]) < 60:
                continue
            # 放射状の大通り（8 本）を空ける
            ang = math.degrees(math.atan2(y, x)) % 45
            if min(ang, 45 - ang) * math.pi / 180 * r < 14:
                continue
            if rnd.random() < 0.12:
                continue
            pts.append((x, y, plain_height(x, y)))
            var.append(rnd.randrange(len(kinds)))
            rot.append(math.atan2(y, x) + rnd.choice((0, math.pi / 2)) + rnd.uniform(-0.08, 0.08))
            scl.append(rnd.uniform(0.85, 1.15))
            birth.append((r - P.R_OUTER) / (r_max - P.R_OUTER) * 0.9 + rnd.uniform(0, 0.08))
    obj = _points("Houses", pts, {"variant": ("INT", var), "rot": ("FLOAT", rot), "scl": ("FLOAT", scl), "birth": ("FLOAT", birth)})
    col = _hidden_collection("HouseKinds", kinds)
    mod, ident = instancer(obj, col, grow_default=0.0, softness=0.05)
    return obj, ident, len(pts)


def moored_ships(M, seed=12):
    """運河の両岸と外港に停泊する船（複製）。"""
    rnd = random.Random(seed)
    base = trireme(M, "TriremeMoored")
    pts, var, rot, scl, birth = [], [], [], [], []
    y = -P.R_OUTER - 300
    while y > P.COAST_Y_3D + 100:
        for sx in (-1, 1):
            if rnd.random() < 0.7:
                pts.append((sx * (P.CANAL_W / 2 - 9), y, 0.0))
                var.append(0)
                rot.append(rnd.uniform(-0.03, 0.03))
                scl.append(1.0)
                birth.append(0.0)
        y -= 46
    obj = _points("MooredShips", pts, {"variant": ("INT", var), "rot": ("FLOAT", rot), "scl": ("FLOAT", scl), "birth": ("FLOAT", birth)})
    col = _hidden_collection("ShipKinds", [base])
    mod, ident = instancer(obj, col)
    return obj
