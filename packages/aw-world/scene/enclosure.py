# 囲い遺構（T字柱の円形構造）。中央の2本の大柱、周壁に埋め込まれた柱、石積みの周壁とベンチ、岩盤の床。
#
# 形の拠り所（概数。README の「わかっていること／推測」の表と対応）:
#   - 囲い D: 直径はおよそ 20m。中央に 2 本の大柱（高さ 5.5m 前後）、周壁に 11〜12 本の柱
#   - 中央の大柱の幅広の側面に腕、正面（幅の狭い面）で両手が合わさり、その下に帯と腰布
#   - 周壁の柱には動物（キツネ・イノシシ・ヘビ・鳥など）の浮彫
# 推測で埋めたもの: 柱の断面寸法、浮彫の配置と形（様式化したシルエット）、石積みの石の大きさ、
#   周壁の高さ、囲い同士の位置関係（模式的な配置）。
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from util import box, cylinder, mesh_object, tube_along

# ---------------------------------------------------------------- T 字柱


def _jitter_box(bm, size, center, rnd=None, j=0.0, rot=None):
    """bm に直方体を足す。j > 0 なら頂点を揺らして割り石らしくする。"""
    geom = bmesh.ops.create_cube(bm, size=1.0)
    vs = geom["verts"]
    for v in vs:
        co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
        if rnd and j > 0:
            co += Vector((rnd.uniform(-j, j) * size[0], rnd.uniform(-j, j) * size[1], rnd.uniform(-j, j) * size[2]))
        if rot is not None:
            co = rot @ co
        v.co = co + Vector(center)
    return vs


def t_pillar(name, p, H, w=1.0, t=0.36, head_h=1.0, head_len=1.7, head_t=0.42, front_over=0.35, mat=None):
    """T 字柱。局所座標: 原点 = 柱の足元中心、幅広の側面は ±X、正面（幅の狭い面）は -Y。
    頭部は前（-Y）に大きく張り出す。"""
    bm = bmesh.new()
    shaft_h = H - head_h
    _jitter_box(bm, (t, w, shaft_h + 0.05), (0, 0, shaft_h / 2))
    back_over = head_len - w - front_over
    _jitter_box(bm, (head_t, head_len, head_h), (0, (back_over - front_over) / 2, shaft_h + head_h / 2))
    obj = mesh_object(name, bm, mat or p.pillar)
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.04
    bev.segments = 3
    # 手で叩き出した面のゆらぎ: 細かく割ってからノイズで数 cm 押し引きする
    sub = obj.modifiers.new("Subdiv", "SUBSURF")
    sub.subdivision_type = "SIMPLE"
    sub.levels = sub.render_levels = 4
    disp = obj.modifiers.new("Chisel", "DISPLACE")
    tex = bpy.data.textures.get("ChiselNoise") or bpy.data.textures.new("ChiselNoise", "CLOUDS")
    tex.noise_scale = 0.35
    tex.noise_depth = 3
    disp.texture = tex
    disp.texture_coords = "GLOBAL"
    disp.strength = 0.035
    disp.mid_level = 0.5
    return obj


def _relief_poly(name, outline, face_x, origin, scale, depth, mat, parent, flip=False):
    """2D の輪郭（0..1 の (前後, 上下)）を柱の側面に浮彫として貼る。face_x は側面の x、depth は彫りの高さ。"""
    bm = bmesh.new()
    sx = 1 if face_x > 0 else -1
    vs = []
    for a, b in outline:
        a = (1 - a) if flip else a
        vs.append(bm.verts.new((face_x - sx * 0.005, origin[0] + a * scale, origin[1] + b * scale)))
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    moved = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=moved, vec=(sx * depth, 0, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    o = mesh_object(name, bm, mat)
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.008
    bev.segments = 2
    o.parent = parent
    return o


# 様式化した動物の輪郭（前後 0..1、上下 0..1。頭は +前後 側）。写しではなく、モチーフの雰囲気だけ。
FOX = [(0.0, 0.32), (0.12, 0.42), (0.5, 0.46), (0.68, 0.42), (0.8, 0.52), (0.86, 0.66), (0.9, 0.54), (1.0, 0.44),
       (0.9, 0.38), (0.8, 0.32), (0.79, 0.08), (0.73, 0.08), (0.7, 0.28), (0.36, 0.29), (0.27, 0.06), (0.21, 0.06),
       (0.21, 0.28), (0.06, 0.26)]
BOAR = [(0.0, 0.36), (0.1, 0.52), (0.4, 0.62), (0.7, 0.58), (0.86, 0.47), (1.0, 0.36), (0.97, 0.3), (0.86, 0.28),
        (0.8, 0.04), (0.74, 0.04), (0.72, 0.25), (0.3, 0.25), (0.26, 0.04), (0.2, 0.04), (0.18, 0.27), (0.04, 0.3)]
BIRD = [(0.5, 0.0), (0.44, 0.3), (0.1, 0.52), (0.0, 0.74), (0.2, 0.68), (0.42, 0.6), (0.45, 0.84), (0.5, 0.95),
        (0.55, 0.84), (0.58, 0.6), (0.8, 0.68), (1.0, 0.74), (0.9, 0.52), (0.56, 0.3)]
MOTIFS = {"fox": FOX, "boar": BOAR, "bird": BIRD}


def anthropomorphic(obj, p, H, w, t, head_h, necklace=False):
    """中央の大柱の人体表現: 両側面の腕、正面で合わさる手、帯、腰布。"""
    shaft_top = H - head_h
    for sx in (-1, 1):
        x = sx * (t / 2 + 0.012)
        arm = tube_along(
            f"{obj.name}Arm{sx}",
            [(x, w * 0.3, shaft_top - 0.2), (x, w * 0.36, H * 0.56), (x, w * 0.1, H * 0.44), (x, -w / 2 + 0.06, H * 0.41)],
            0.045,
            p.relief,
        )
        arm.parent = obj
        # 指: 正面の縁から中央へ向かう細い棒を 5 本
        for k in range(5):
            z = H * 0.405 + (k - 2) * 0.03
            finger = box(f"{obj.name}Finger{sx}{k}", (0.16, 0.022, 0.018), (sx * 0.1, -w / 2 - 0.006, z), p.relief, bevel=0.006)
            finger.parent = obj
    belt_z = H * 0.33
    belt = box(f"{obj.name}Belt", (t + 0.03, w + 0.03, 0.11), (0, 0, belt_z), p.relief, bevel=0.01)
    belt.parent = obj
    buckle = box(f"{obj.name}Buckle", (0.16, 0.03, 0.12), (0, -w / 2 - 0.02, belt_z), p.relief, bevel=0.01)
    buckle.parent = obj
    # 腰布（毛皮）: 帯から垂れる先細りの板
    bm = bmesh.new()
    top, bot = 0.2, 0.08
    y = -w / 2 - 0.012
    vs = [bm.verts.new(c) for c in ((-top, y, belt_z - 0.05), (top, y, belt_z - 0.05), (bot, y, belt_z - 0.75), (-bot, y, belt_z - 0.75))]
    f = bm.faces.new(vs)
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=(0, -0.025, 0))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    pelt = mesh_object(f"{obj.name}Pelt", bm, p.relief)
    pelt.modifiers.new("Bevel", "BEVEL").width = 0.008
    pelt.parent = obj
    if necklace:
        # 首飾り風の三日月と円盤（正面、頭部のすぐ下）
        z = shaft_top - 0.35
        arc = [(0.12 * math.cos(a), -w / 2 - 0.012, z + 0.12 * math.sin(a)) for a in [math.pi * (1.1 + 0.8 * i / 6) for i in range(7)]]
        crescent = tube_along(f"{obj.name}Crescent", arc, 0.02, p.relief)
        crescent.parent = obj
        d = cylinder(f"{obj.name}DiscStone", 0.05, 0.03, (0, -w / 2 - 0.012, z + 0.02), p.relief, rot=(math.pi / 2, 0, 0))
        d.parent = obj


# ---------------------------------------------------------------- 周壁


def rubble_ring(name, p, center, r_in, r_out, height, gaps, rnd, bench=None):
    """割り石積みの周壁。内側の面に石を積み、芯は円筒で埋める。gaps = 柱の位置（角度, 半幅[m]）で、
    そこには石を積まない。bench = (奥行き, 高さ) なら内側にベンチを回す。"""
    cx, cy = center
    bm = bmesh.new()
    z = 0.0
    while z < height - 0.05:
        ch = rnd.uniform(0.17, 0.28)
        ch = min(ch, height - z)
        r_face = r_in - (bench[0] if bench and z < bench[1] - 0.01 else 0.0)
        a = rnd.uniform(0, 0.5) / r_face
        while a < 2 * math.pi - 0.02:
            length = rnd.uniform(0.32, 0.65)
            da = length / r_face
            mid = a + da / 2
            blocked = any(abs(((mid - g + math.pi) % (2 * math.pi)) - math.pi) * r_face < half + length / 2 for g, half in gaps)
            if not blocked:
                depth = rnd.uniform(0.28, 0.45)
                rr = r_face + depth / 2 + rnd.uniform(-0.03, 0.03)
                rot = Matrix.Rotation(mid + math.pi / 2, 3, "Z") @ Matrix.Rotation(rnd.uniform(-0.05, 0.05), 3, "X")
                _jitter_box(bm, (length * 0.97, depth, ch * 0.94), (cx + rr * math.cos(mid), cy + rr * math.sin(mid), z + ch / 2), rnd, 0.12, rot)
            a += da + rnd.uniform(0.005, 0.02) / r_face
        z += ch
    # 天端の石（平たい石を不揃いに）
    for k in range(int(2 * math.pi * (r_in + r_out) / 2 / 0.3 * 4)):
        ang = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(r_in + 0.2, r_out - 0.1)
        rot = Matrix.Rotation(rnd.uniform(0, math.pi), 3, "Z")
        _jitter_box(bm, (rnd.uniform(0.2, 0.42), rnd.uniform(0.18, 0.32), rnd.uniform(0.1, 0.18)), (cx + rr * math.cos(ang), cy + rr * math.sin(ang), height - 0.08), rnd, 0.15, rot)
    stones = mesh_object(name + "Stones", bm, p.rubble)
    stones.modifiers.new("Bevel", "BEVEL").width = 0.025

    # 芯（土と小石の詰め）: 内面より少し奥から外周まで
    core_in = r_in + 0.2
    bm = bmesh.new()
    seg = 96
    rings = []
    for r, zz in ((core_in, 0.0), (core_in, height - 0.12), (r_out, height - 0.12), (r_out + 1.0, height - 0.9)):
        rings.append([bm.verts.new((cx + r * math.cos(2 * math.pi * i / seg), cy + r * math.sin(2 * math.pi * i / seg), zz)) for i in range(seg)])
    for ra, rb in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    mesh_object(name + "Core", bm, p.ground)

    if bench:
        depth, bh = bench
        box_r = r_in - depth / 2
        bm = bmesh.new()
        n = int(2 * math.pi * box_r / 0.7)
        for i in range(n):
            mid = 2 * math.pi * (i + 0.5) / n
            if any(abs(((mid - g + math.pi) % (2 * math.pi)) - math.pi) * box_r < half + 0.35 for g, half in gaps):
                continue
            rot = Matrix.Rotation(mid + math.pi / 2, 3, "Z")
            _jitter_box(bm, (0.68, depth + 0.06, 0.12), (cx + box_r * math.cos(mid), cy + box_r * math.sin(mid), bh - 0.05), rnd, 0.06, rot)
        slabs = mesh_object(name + "BenchSlabs", bm, p.bedrock)
        slabs.modifiers.new("Bevel", "BEVEL").width = 0.02


# ---------------------------------------------------------------- 囲いひとつ


def enclosure(p, name, center, r_in, r_out, wall_h, n_wall, central_h, seed, motifs=(), detailed=True, rot0=0.0):
    rnd = random.Random(seed)
    cx, cy = center
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    before = set(bpy.data.objects)

    # 岩盤の床
    cylinder(name + "Floor", r_in + 0.4, 0.4, (cx, cy, -0.2), p.bedrock, segments=96)

    # 周壁の柱: 正面（-Y）を中心へ向け、幅広の面は周方向に向く
    gaps = []
    wall_pillars = []
    for i in range(n_wall):
        ang = rot0 + 2 * math.pi * i / n_wall + rnd.uniform(-0.04, 0.04)
        Hp = rnd.uniform(3.2, 3.9)
        w = rnd.uniform(0.75, 0.95)
        r = r_in + w * 0.35
        pl = t_pillar(f"{name}P{i}", p, Hp, w=w, t=0.32, head_h=0.75, head_len=w + 0.5, head_t=0.36, front_over=0.3)
        pl.location = (cx + r * math.cos(ang), cy + r * math.sin(ang), rnd.uniform(-0.05, 0.05))
        # 局所 -Y を中心へ向ける。z 回転 θ で -Y は (sinθ, -cosθ) に移るので、θ = ang - pi/2 で (-cos, -sin) = 中心向き
        pl.rotation_euler = (rnd.uniform(-0.015, 0.015), rnd.uniform(-0.015, 0.015), ang - math.pi / 2)
        gaps.append((ang, 0.2))
        wall_pillars.append((pl, Hp, w))
    if detailed:
        for k, motif in enumerate(motifs):
            pl, Hp, w = wall_pillars[(k * 3 + 1) % n_wall]
            side = 0.16 + 0.01  # 側面の x（t/2 + 少し）
            sc = w * 0.85
            if motif == "snake":
                for s in range(3):
                    pts = [(0.06 * math.sin(z * 9 + s), -w / 2 - 0.012, Hp - 0.9 - z * 1.6 + s * 0.02) for z in [i / 10 for i in range(11)]]
                    pts = [(x + (s - 1) * 0.09, y, z) for x, y, z in pts]
                    sn = tube_along(f"{pl.name}Snake{s}", pts, 0.022, p.relief)
                    sn.parent = pl
            else:
                _relief_poly(f"{pl.name}{motif}", MOTIFS[motif], side * (1 if k % 2 == 0 else -1), (-w / 2 + 0.05, Hp - 0.75 - sc * 0.9 - 0.2), sc, 0.03, p.relief, pl)
        rubble_ring(name + "Wall", p, center, r_in + 0.35, r_out, wall_h, gaps, rnd, bench=(0.5, 0.48))
    else:
        rubble_ring(name + "Wall", p, center, r_in + 0.35, r_out, wall_h, gaps, rnd)

    # 中央の2本
    centrals = []
    if central_h:
        for k, sx in enumerate((-1, 1)):
            w, t, hh = 1.15, 0.38, 1.15
            c = t_pillar(f"{name}Central{k}", p, central_h, w=w, t=t, head_h=hh, head_len=1.95, head_t=0.45, front_over=0.45)
            c.location = (cx + sx * 1.7, cy + 0.6, 0.25)
            c.rotation_euler = (0, 0, rnd.uniform(-0.03, 0.03))
            if detailed:
                anthropomorphic(c, p, central_h, w, t, hh, necklace=(k == 0))
            # 台座（岩盤を削り残した受け）
            box(f"{name}Plinth{k}", (0.75, 1.6, 0.3), (c.location.x, c.location.y, 0.12), p.bedrock, bevel=0.04)
            centrals.append(c)

    for o in set(bpy.data.objects) - before:
        for cl in list(o.users_collection):
            cl.objects.unlink(o)
        col.objects.link(o)
    return {"centrals": centrals, "wall_pillars": [w[0] for w in wall_pillars]}
