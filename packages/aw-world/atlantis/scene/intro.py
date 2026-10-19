# 冒頭: 都の上に広がる羊皮紙の巻物、巻き芯、三叉の矛の封蝋、貨幣（オリハルコン貨・銀貨・青銅貨）。
# 巻物の画像は都の座標に合わせて描いてあるので、線がそのまま建物の位置から立ち上がる。
import math

import bmesh
import bpy
from mathutils import Vector

import anim
import plan as P
from city import MB, SCROLL_Z

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "drawings"))
import parchment as PT  # noqa: E402


def scroll(M):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new((x, y, SCROLL_Z)) for x, y in ((PT.X0, PT.Y0), (PT.X1, PT.Y0), (PT.X1, PT.Y1), (PT.X0, PT.Y1))]
    f = bm.faces.new(vs)
    for loop, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        loop[uv].uv = (u, v)
    me = bpy.data.meshes.new("Scroll")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.parchment)
    obj = bpy.data.objects.new("Scroll", me)
    bpy.context.scene.collection.objects.link(obj)
    obj.color = (1, 1, 1, 1)

    # 巻き芯: 上端に固定の軸、下へ転がる巻き（紙の束）
    width = PT.X1 - PT.X0
    rod_r, roll_r = 45.0, 110.0
    top = MB()
    top.cyl((0, 0, 0), rod_r, width + 260, seg=24, mat=0)
    rod_top = top.finish("ScrollRodTop", [M.wood])
    rod_top.rotation_euler = (0, math.pi / 2, 0)
    rod_top.location = (PT.X0 - 130, PT.Y1 + rod_r, SCROLL_Z + rod_r)
    roll = MB()
    roll.cyl((0, 0, 0), roll_r, width, seg=32, mat=0)
    roll.cyl((0, 0, -130), rod_r, width + 260, seg=24, mat=1)
    roller = roll.finish("ScrollRoll", [M.paper, M.wood])
    roller.rotation_mode = "YXZ"  # 先に Y で横に寝かせ、そのあと X（巻物の軸）で転がす
    roller.rotation_euler = (0, math.pi / 2, 0)
    f0, f1 = P.CUES["scroll_unroll"]
    start_u = 0.38  # 冒頭 1 秒を切って、広がり始めた所から入る
    y_at = lambda u: PT.Y1 - u * (PT.Y1 - PT.Y0)  # noqa: E731
    anim.loc(roller, [(f0, (PT.X0, y_at(start_u), SCROLL_Z + roll_r)), (f1, (PT.X0, y_at(1.0) - roll_r * 0.6, SCROLL_Z + roll_r * 0.75))])
    for f, a in ((f0, 0.0), (f1, -(1 - start_u) * (PT.Y1 - PT.Y0) / roll_r)):
        roller.rotation_euler = (a, math.pi / 2, 0)
        roller.keyframe_insert("rotation_euler", index=0, frame=f)
    anim.value("unroll", [(f0, start_u), (f1, 1.0)])
    a0, a1 = P.CUES["scroll_away"]
    anim.alpha(obj, [(a0, 1.0), (a1, 0.0)])
    for o in (rod_top, roller):
        anim.shrink(o, a0, a0 + 8)
    return obj


def coin(M, name, mat, radius, motif):
    """貨幣（巻物の大きさに合わせて拡大した模型）。縁の盛り上がりと、図柄の浮き彫り。"""
    mb = MB()
    t = radius * 0.12
    mb.cyl((0, 0, 0), radius, t, seg=64)
    mb.cyl((0, 0, t), radius, t * 0.25, seg=64, r_top=radius * 0.94)
    h = t * 0.35
    if motif == "rings":  # 同心円の都
        bm = mb.bm
        for rr in (0.16, 0.3, 0.45, 0.62):
            g = bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=radius * rr, radius2=radius * rr, depth=h)
            for v in g["verts"]:
                v.co += Vector((0, 0, t + h / 2))
            g2 = bmesh.ops.create_cone(bm, cap_ends=True, segments=48, radius1=radius * (rr - 0.04), radius2=radius * (rr - 0.04), depth=h * 1.05)
            for v in g2["verts"]:
                v.co += Vector((0, 0, t + h / 2 + 0.01))
        mb.box((0, -radius * 0.55, t + h / 2), (radius * 0.08, radius * 0.3, h))
    elif motif == "trident":
        mb.box((0, -radius * 0.1, t + h / 2), (radius * 0.07, radius * 1.0, h))
        mb.box((0, radius * 0.25, t + h / 2), (radius * 0.6, radius * 0.07, h))
        for sx in (-1, 1):
            mb.box((sx * radius * 0.3, radius * 0.38, t + h / 2), (radius * 0.07, radius * 0.3, h))
        mb.box((0, radius * 0.45, t + h / 2), (radius * 0.07, radius * 0.4, h))
    else:  # 三段櫂船
        mb.box((0, -radius * 0.1, t + h / 2), (radius * 1.1, radius * 0.18, h))
        mb.box((radius * 0.6, -radius * 0.05, t + h / 2), (radius * 0.15, radius * 0.1, h))
        for k in range(9):
            mb.box((-radius * 0.45 + k * radius * 0.11, -radius * 0.3, t + h / 2), (radius * 0.03, radius * 0.25, h), rot=15)
        mb.box((0, radius * 0.2, t + h / 2), (radius * 0.05, radius * 0.5, h))
        mb.box((0, radius * 0.28, t + h / 2), (radius * 0.5, radius * 0.3, h))
    o = mb.finish(name, [mat])
    for p in o.data.polygons:
        p.use_smooth = True
    bev = o.modifiers.new("Bevel", "BEVEL")
    bev.width = t * 0.15
    bev.segments = 2
    bev.limit_method = "ANGLE"
    return o


def seal(M, radius):
    """三叉の矛の封蝋。不定形にふくらんだ蝋と、押された矛の図柄。"""
    bm = bmesh.new()
    g = bmesh.ops.create_circle(bm, cap_ends=True, segments=48, radius=radius)
    for v in g["verts"]:
        a = math.atan2(v.co.y, v.co.x)
        k = 1 + 0.12 * math.sin(a * 5) + 0.06 * math.sin(a * 11)
        v.co.x *= k
        v.co.y *= k
    ext = bmesh.ops.extrude_face_region(bm, geom=bm.faces[:])
    bmesh.ops.translate(bm, verts=[e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)], vec=(0, 0, radius * 0.18))
    me = bpy.data.meshes.new("Seal")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.wax)
    o = bpy.data.objects.new("Seal", me)
    bpy.context.scene.collection.objects.link(o)
    o.modifiers.new("Sub", "SUBSURF").levels = 2
    for p in me.polygons:
        p.use_smooth = True
    stamp = coin(M, "SealStamp", M.wax, radius * 0.62, "trident")
    stamp.parent = o
    stamp.location = (0, 0, radius * 0.12)
    # リボン
    rb = MB()
    rb.box((radius * 0.2, -radius * 1.4, -radius * 0.02), (radius * 0.35, radius * 1.6, radius * 0.03), rot=12)
    rb.box((-radius * 0.25, -radius * 1.35, -radius * 0.02), (radius * 0.35, radius * 1.5, radius * 0.03), rot=-10)
    ribbon = rb.finish("SealRibbon", [M.wax])
    ribbon.parent = o
    return o


def props(M):
    """巻物の左下に封蝋と貨幣 3 枚。巻物と一緒に退く。"""
    items = []
    s = seal(M, 380.0)
    s.location = (-2350.0, -2900.0, SCROLL_Z)
    items.append(s)
    for (name, mat, dia, obv, rev), (x, y, motif, rot) in zip(P.COINS, ((-1600, -3350, "rings", 0.3), (-1050, -2950, "ship", -0.4), (-850, -3500, "trident", 0.9))):
        r = dia * 9.0  # 封蝋との釣り合いで拡大した模型
        mat_obj = {"orichalcum": M.orichalcum, "silver": M.silver, "bronze": M.bronze}[mat]
        c = coin(M, f"Coin_{mat}", mat_obj, r, motif)
        c.location = (x, y, SCROLL_Z)
        c.rotation_euler = (0, 0, rot)
        items.append(c)
    # 巻物が転がってきて、その場所が広がってから現れる
    u0, u1 = P.CUES["scroll_unroll"]
    start_u = 0.38
    for o in items:
        u = (PT.Y1 - o.location.y) / (PT.Y1 - PT.Y0)
        show = int(u0 + (u1 - u0) * max(0.0, (u - start_u)) / (1 - start_u)) + 2
        for part in [o] + list(o.children_recursive):  # 親を隠しても子（刻印・リボン）は残るので、子にも打つ
            part.hide_render = True
            part.keyframe_insert("hide_render", frame=1)
            part.keyframe_insert("hide_render", frame=max(1, show - 1))
            part.hide_render = False
            part.keyframe_insert("hide_render", frame=show)
    f0, f1 = P.CUES["coins_away"]
    for o in items:
        anim.shrink(o, f0, f1)
    return items
