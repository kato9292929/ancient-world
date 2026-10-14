# 小物。古代史研究者の机まわり。リポジトリの中身（aw-data の台帳、aw-objects の角柱）を物として置く。
import json
import math
import random

import bmesh
import bpy
from mathutils import Vector

from furniture import DESK_X, DESK_Y, TOP
from util import box, cylinder, grid, lathe, mesh_object, shade_smooth

FONT_PATH = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"


def font():
    try:
        return bpy.data.fonts.load(FONT_PATH, check_existing=True)
    except RuntimeError:
        return None  # 日本語フォントが無い環境では Blender 既定フォント（和文は豆腐になる）


def text(name, body, size, loc, rot, mat, align="LEFT", extrude=0.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.extrude = extrude
    cu.align_x = align
    f = font()
    if f:
        cu.font = f
    obj = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def weld_blundell_prism(p, loc, yaw):
    """aw-objects と同じ寸法で起こした Weld-Blundell Prism の模型（机上のレプリカ）。
    高さ 20cm・断面 9cm 角（奥行きは記録が無いので幅と同値）・軸穴は名目直径 1.4cm。
    刻文は再現せず、各面 2 欄の区切りを浅い溝で示すだけ（aw-objects/src/geometry.ts と同じ方針）。"""
    h, s, hole_r = 0.20, 0.09, 0.007
    bm = bmesh.new()
    # 外形: 正方形断面の角柱に、中心を貫通する穴（外周 4 辺 + 内周の多角形をブリッジ）
    seg = 24
    outer_b, outer_t, inner_b, inner_t = [], [], [], []
    # 外周を穴と同じ分割数にそろえるため、正方形の周上に seg 点を取る
    for i in range(seg):
        a = 2 * math.pi * i / seg + math.pi / 4
        c, sn = math.cos(a), math.sin(a)
        k = (s / 2) / max(abs(c), abs(sn))
        outer_b.append(bm.verts.new((c * k, sn * k, 0)))
        outer_t.append(bm.verts.new((c * k, sn * k, h)))
        inner_b.append(bm.verts.new((c * hole_r, sn * hole_r, 0)))
        inner_t.append(bm.verts.new((c * hole_r, sn * hole_r, h)))
    for i in range(seg):
        j = (i + 1) % seg
        bm.faces.new((outer_b[i], outer_b[j], outer_t[j], outer_t[i]))
        bm.faces.new((inner_b[j], inner_b[i], inner_t[i], inner_t[j]))
        bm.faces.new((outer_t[i], outer_t[j], inner_t[j], inner_t[i]))
        bm.faces.new((outer_b[j], outer_b[i], inner_b[i], inner_b[j]))
    obj = mesh_object("WeldBlundellPrism", bm, p.terracotta)
    bev = obj.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.004
    bev.segments = 3
    bev.limit_method = "ANGLE"
    obj.location = loc
    obj.rotation_euler = (0, 0, yaw)
    # 欄の区切り: 各面の中央に細い溝（暗い細板を僅かに沈めて置く）
    for f in range(4):
        a = f * math.pi / 2
        n = Vector((math.cos(a), math.sin(a), 0))
        g = box(f"PrismDivider{f}", (0.0015, 0.0015, h - 0.03), (0, 0, 0), p.walnut)
        g.location = n * (s / 2 - 0.0003) + Vector((0, 0, h / 2))
        g.rotation_euler = (0, 0, a)
        g.parent = obj
    # 展示台
    stand = cylinder("PrismStand", 0.075, 0.02, (loc[0], loc[1], loc[2] - 0.01), p.walnut, segments=48)
    return obj, stand


def clay_tablet(p, loc, yaw):
    """粘土板（楔形文字の書板のレプリカ）。ふくらんだ枕形。刻文は描かない。"""
    o = box("ClayTablet", (0.11, 0.075, 0.025), loc, p.tablet, rot=(0, 0, yaw))
    o.modifiers.new("Subsurf", "SUBSURF").levels = 2
    shade_smooth(o)
    return o


def pottery_shards(p, center, n=5, seed=3):
    """土器片の小皿。不規則な曲面のかけら。"""
    rnd = random.Random(seed)
    lathe("ShardTray", [(0.0, 0.0), (0.07, 0.0), (0.09, 0.012), (0.092, 0.014)], mat=p.walnut, loc=(center[0], center[1], TOP))
    for i in range(n):
        bm = grid(3, 3)
        for v in bm.verts:
            v.co.x = v.co.x * rnd.uniform(0.025, 0.04) + rnd.uniform(-0.003, 0.003)
            v.co.y = v.co.y * rnd.uniform(0.02, 0.035) + rnd.uniform(-0.003, 0.003)
            v.co.z = -(v.co.x**2 + v.co.y**2) * 6
        o = mesh_object(f"Shard{i}", bm, p.shard)
        o.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.005
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.0, 0.04)
        o.location = (center[0] + r * math.cos(a), center[1] + r * math.sin(a), TOP + 0.01 + i * 0.002)
        o.rotation_euler = (rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(0, math.pi))


def mug(p, loc):
    """マグカップ。陶器（コート付き）。液面はコーヒー。"""
    prof = [(0.0, 0.0), (0.036, 0.0), (0.04, 0.004), (0.041, 0.09), (0.038, 0.092), (0.036, 0.086), (0.035, 0.008), (0.0, 0.008)]
    body = lathe("Mug", prof, mat=p.ceramic, loc=loc)
    lathe("MugCoffee", [(0.0, 0.07), (0.0355, 0.07)], mat=p.coffee, loc=loc)
    from util import tube_along

    x, y, z = loc
    tube_along("MugHandle", [(x + 0.038, y, z + 0.075), (x + 0.065, y, z + 0.07), (x + 0.068, y, z + 0.035), (x + 0.038, y, z + 0.022)], 0.006, p.ceramic)
    return body


def magnifier(p, loc, yaw):
    """ルーペ。レンズはガラス（モデリングして素材を分ける対象）、枠は真鍮、柄は木。"""
    x, y, z = loc
    lens = lathe("MagnifierLens", [(0.0, 0.004), (0.038, 0.0), (0.0, -0.004)], mat=p.glass, loc=(0, 0, 0))
    rim = lathe("MagnifierRim", [(0.038, -0.005), (0.042, -0.005), (0.042, 0.005), (0.038, 0.005)], mat=p.brass, loc=(0, 0, 0))
    handle = cylinder("MagnifierHandle", 0.008, 0.1, (0.092, 0, 0), p.walnut, rot=(0, math.pi / 2, 0))
    root = bpy.data.objects.new("Magnifier", None)
    bpy.context.scene.collection.objects.link(root)
    for o in (lens, rim, handle):
        o.parent = root
    root.location = (x, y, z + 0.006)
    root.rotation_euler = (0, 0, yaw)


def notebook(p, loc, yaw):
    """開いたノート。左右のページを僅かに反らせる。"""
    x, y, z = loc
    root = bpy.data.objects.new("Notebook", None)
    bpy.context.scene.collection.objects.link(root)
    cover = box("NotebookCover", (0.3, 0.21, 0.003), (0, 0, 0.0015), p.leather)
    cover.parent = root
    for side in (-1, 1):
        bm = grid(8, 2)
        for v in bm.verts:
            u = v.co.x + 0.5  # 0..1 を綴じ目→小口
            v.co.x = side * u * 0.14
            v.co.y *= 0.2
            v.co.z = 0.004 + 0.012 * math.sin(u * math.pi * 0.9)
        o = mesh_object(f"NotebookPage{side}", bm, p.paper)
        o.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.004
        shade_smooth(o)
        o.parent = root
    pen = cylinder("Pen", 0.0045, 0.14, (0.05, -0.02, 0.025), p.black_plastic, rot=(0, math.pi / 2, 0.4))
    pen.parent = root
    root.location = (x, y, z)
    root.rotation_euler = (0, 0, yaw)


def sticky_note(p, name, color, hinge, size=0.065, curl=0.25, tilt=0.0):
    """付箋。上端（糊の帯）を蝶番にしてぶら下がる。下に行くほど手前に反る形をメッシュに焼き込む。
    なびきは motion.py が蝶番まわりの回転にノイズを入れて作る。"""
    bm = grid(4, 10)
    for v in bm.verts:
        t = 0.5 - v.co.y  # 0（上端）..1（下端）
        v.co = Vector((v.co.x * size, -curl * size * t * t, -t * size))
    o = mesh_object(name, bm, p.sticky[color])
    o.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.0004
    shade_smooth(o)
    o.location = hinge
    o.rotation_euler = (0, tilt, 0)
    return o


def book(p, name, w, h, d, loc, rot_y=0.0, mat=None, title=None, rnd=None):
    """本 1 冊。表紙（布装）と小口（紙）を分ける。title があれば背に縦書きで金箔押し風の文字を置く。
    loc は背の下端中央。背は -Y（手前）を向く。"""
    mat = mat or rnd.choice(p.book_colors)
    root = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(root)
    cov = box(name + "Cover", (w, d, h), (0, d / 2, h / 2), mat, bevel=0.0015)
    cov.parent = root
    block = box(name + "Pages", (w - 0.003, d - 0.004, h - 0.006), (0, d / 2 + 0.003, h / 2), p.paper)
    block.parent = root
    if title:
        size = min(w * 0.55, 0.016)
        t = text(name + "Title", "\n".join(title), size, (0, -0.0008, h - 0.03), (math.pi / 2, 0, 0), p.gilt, align="CENTER")
        t.data.space_line = 0.95
        t.parent = root
    root.location = loc
    root.rotation_euler = (0, rot_y, 0)
    return root


def fill_shelves(p, shelves, titles, seed=7):
    """606 の棚に本を並べる。ところどころ寝かせた本と、遺物の小物を置いて隙間を作る。"""
    rnd = random.Random(seed)
    titles = list(titles)
    count = 0
    for si, sh in enumerate(shelves):
        x = sh["x"] - sh["w"] / 2
        x_end = sh["x"] + sh["w"] / 2
        limit = x_end - (0.18 if si % 3 == 1 else 0.02)  # 3段に1段は右に空きを作る
        while x < limit:
            w = rnd.uniform(0.018, 0.045)
            h = rnd.uniform(0.19, 0.3)
            d = rnd.uniform(0.15, 0.22)
            if x + w > limit:
                break
            title = titles.pop(0) if titles and rnd.random() < 0.35 and w > 0.028 else None
            book(p, f"Book{count}", w, h, d, (x + w / 2, sh["y_back"] - d, sh["z"]), mat=None, title=title, rnd=rnd)
            x += w + rnd.uniform(0.0, 0.003)
            count += 1
        # 最後の1冊を立てかける
        if si % 2 == 0 and x < x_end - 0.08:
            w, h, d = 0.03, 0.26, 0.19
            ang = math.radians(16)
            book(p, f"Book{count}", w, h, d, (x + h * math.sin(ang) / 2 + 0.01, sh["y_back"] - d, sh["z"]), rot_y=ang, rnd=rnd)
            count += 1
        elif si % 3 == 1:
            # 空きに平積みと土器片
            for k in range(3):
                book(p, f"Book{count}", 0.022, 0.16 - k * 0.01, 0.12, (x_end - 0.1, sh["y_back"] - 0.16, sh["z"] + 0.011 + k * 0.022), rnd=rnd)
                bpy.data.objects[f"Book{count}"].rotation_euler = (0, math.pi / 2, rnd.uniform(-0.1, 0.1))
                count += 1
    return count


def desk_props(p, data_dir):
    sites = json.load(open(f"{data_dir}/sites.json", encoding="utf-8"))
    clusters = json.load(open(f"{data_dir}/clusters.json", encoding="utf-8"))
    # 机上の配置（机の中心からの相対）。左奥にライト、左手前に平積み、右に遺物。
    X, Y = DESK_X, DESK_Y
    prism, _ = weld_blundell_prism(p, (X + 0.45, Y + 0.14, TOP + 0.02), yaw=math.radians(28))
    clay_tablet(p, (X + 0.66, Y + 0.25, TOP + 0.0125), math.radians(-15))
    notebook(p, (X - 0.34, Y - 0.22, TOP), math.radians(8))
    magnifier(p, (X + 0.12, Y - 0.27, TOP), math.radians(-35))
    mug(p, (X + 0.64, Y - 0.12, TOP))
    pottery_shards(p, (X + 0.4, Y - 0.24))
    # 平積み（クラスタ名の背）
    for k, c in enumerate(clusters[:3]):
        o = book(p, f"DeskBook{k}", 0.028, 0.24 - k * 0.015, 0.17, (X - 0.73, Y - 0.27, TOP + 0.014 + k * 0.028), mat=p.book_colors[k + 1], title=c["name_ja"])
        o.rotation_euler = (0, math.pi / 2, math.radians(4 - 5 * k))
    return {"prism": prism, "sites": sites, "clusters": clusters}
