# 遺跡のまわりの生き物と気配: 草（野生の麦を含む）、木立、焚き火、上空を回るハゲワシ、遠景のかすみ。
# どれも当時の環境の「ありえた姿」として置いた演出で、場所や数に根拠はない（README の推測の欄）。
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

from terrain import height
from util import add_noise, lathe, linear_keys, link, mesh_object, tube_along


def haze(mat, color=(0.75, 0.52, 0.36), distance=900.0):
    """空気遠近。カメラからの距離に応じて、素材の出力をかすみの色（発光）へ寄せる。ボリュームより軽い。"""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    src = out.inputs["Surface"].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    math_div = nt.nodes.new("ShaderNodeMath")
    math_div.operation = "DIVIDE"
    math_div.inputs[1].default_value = -distance
    nt.links.new(cam.outputs["View Distance"], math_div.inputs[0])
    exp = nt.nodes.new("ShaderNodeMath")
    exp.operation = "EXPONENT"
    nt.links.new(math_div.outputs[0], exp.inputs[0])
    inv = nt.nodes.new("ShaderNodeMath")
    inv.operation = "SUBTRACT"
    inv.inputs[0].default_value = 1.0
    nt.links.new(exp.outputs[0], inv.inputs[1])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    em.inputs["Strength"].default_value = 1.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(inv.outputs[0], mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])


def _tuft(name, mat, rnd, blades=9, h=0.35, seed_heads=0, col=None):
    """草の株（1 メッシュ）。細い先細りの葉を外へ反らせて束ねる。seed_heads > 0 なら細い茎の先に穂
    （野生のヒトツブコムギ風）を付ける。パーティクルで 1 株ずつ選ばれるので、部品を分けない。"""
    bm = bmesh.new()

    def strip(points, width):
        prev = None
        for k, c in enumerate(points):
            t = k / (len(points) - 1)
            d = (points[min(k + 1, len(points) - 1)] - points[max(k - 1, 0)]).normalized()
            side = d.cross(Vector((0, 0, 1)))
            if side.length < 1e-6:
                side = Vector((1, 0, 0))
            side = side.normalized() * width * (1 - t * 0.85)
            pair = (bm.verts.new(c - side), bm.verts.new(c + side))
            if prev:
                bm.faces.new((prev[0], prev[1], pair[1], pair[0]))
            prev = pair

    for b in range(blades):
        a = 2 * math.pi * b / blades + rnd.uniform(-0.3, 0.3)
        lean = rnd.uniform(0.15, 0.5)
        hh = h * rnd.uniform(0.6, 1.1)
        pts = [Vector((lean * hh * t * t * math.cos(a), lean * hh * t * t * math.sin(a), hh * t))
               for t in [k / 4 for k in range(5)]]
        strip(pts, 0.008)
    for s in range(seed_heads):
        a = rnd.uniform(0, 2 * math.pi)
        hh = h * rnd.uniform(1.5, 2.0)
        lean = rnd.uniform(0.05, 0.25)
        top = Vector((lean * math.cos(a), lean * math.sin(a), hh))
        strip([Vector((top.x * (k / 4) ** 2, top.y * (k / 4) ** 2, hh * k / 4)) for k in range(5)], 0.003)
        geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1.0)
        for v in geom["verts"]:
            v.co = Vector((v.co.x * 0.008, v.co.y * 0.008, v.co.z * 0.045)) + top + Vector((0, 0, 0.04))
    obj = mesh_object(name, bm, mat, col)
    return obj


def grass(p, terrain_obj, hollows, count=90000, seed=5):
    rnd = random.Random(seed)
    # シーンに繋がないコレクション（インスタンスの元。それ自体はレンダリングされない）
    col = bpy.data.collections.new("GrassTufts")
    for i in range(3):
        _tuft(f"Tuft{i}", p.grass if i else p.grass_green, rnd, blades=rnd.randint(7, 12), h=rnd.uniform(0.25, 0.45), col=col)
    for i in range(2):
        _tuft(f"Cereal{i}", p.grass, rnd, blades=6, h=0.35, seed_heads=5, col=col)

    # 密度: 近いほど濃く、囲いの中と壁の上は 0
    vg = terrain_obj.vertex_groups.new(name="GrassDensity")
    for v in terrain_obj.data.vertices:
        x, y = v.co.x, v.co.y
        w = max(0.0, 1.0 - math.hypot(x, y) / 70.0) ** 0.7
        if any((Vector((x, y)) - hl.c).length < hl.r_rim + 0.4 for hl in hollows):
            w = 0.0
        vg.add([v.index], w, "REPLACE")

    mod = terrain_obj.modifiers.new("Grass", "PARTICLE_SYSTEM")
    ps = mod.particle_system
    ps.vertex_group_density = "GrassDensity"
    ps.seed = seed
    s = ps.settings
    s.type = "HAIR"
    s.count = count
    s.hair_length = 1.0
    s.use_advanced_hair = True
    s.render_type = "COLLECTION"
    s.instance_collection = col
    s.use_collection_pick_random = True
    s.use_rotations = True
    s.rotation_mode = "GLOB_Z"
    s.phase_factor_random = 2.0
    s.particle_size = 1.0
    s.size_random = 0.6
    s.use_emit_random = True
    s.distribution = "RAND"
    return ps


def tree(p, name, loc, rnd, scale=1.0):
    """ピスタチオ（テレビンノキ）やアーモンドを思わせる、低く横に広がる疎林の木。"""
    x, y, z = loc
    h = rnd.uniform(3.0, 5.0) * scale
    trunk = tube_along(
        name + "Trunk",
        [(x, y, z - 0.2), (x + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.3, 0.3), z + h * 0.4), (x + rnd.uniform(-0.5, 0.5), y + rnd.uniform(-0.5, 0.5), z + h * 0.7)],
        0.12 * scale,
        p.bark,
    )
    crown_mat = p.leaves if rnd.random() < 0.6 else p.leaves_dry
    for k in range(rnd.randint(7, 11)):
        r = rnd.uniform(0.6, 1.1) * scale
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x + rnd.uniform(-1.8, 1.8) * scale, y + rnd.uniform(-1.8, 1.8) * scale, z + h * 0.8 + rnd.uniform(-0.6, 0.9) * scale))
        c = bpy.context.object
        c.name = f"{name}Crown{k}"
        c.scale.z = 0.7
        c.data.materials.append(crown_mat)
        d = c.modifiers.new("Lumps", "DISPLACE")
        tex = bpy.data.textures.get("CrownNoise") or bpy.data.textures.new("CrownNoise", "VORONOI")
        tex.noise_scale = 0.5
        d.texture = tex
        d.strength = 0.7 * scale
        for poly in c.data.polygons:
            poly.use_smooth = True
    return trunk


def woodland(p, hollows, n=70, seed=9, avoid=()):
    rnd = random.Random(seed)
    placed = 0
    tries = 0
    while placed < n and tries < n * 20:
        tries += 1
        r = 22 + rnd.random() ** 1.6 * 600
        a = rnd.uniform(0, 2 * math.pi)
        x, y = r * math.cos(a), r * math.sin(a)
        if any((Vector((x, y)) - hl.c).length < hl.r_rim + 4 for hl in hollows):
            continue
        if any((Vector((x, y)) - Vector(c)).length < rad for c, rad in avoid):
            continue
        z = height(x, y, hollows)
        tree(p, f"Tree{placed}", (x, y, z), rnd, scale=1.0 if r < 150 else 1.6)
        placed += 1


def hearth(p, loc, frames, seed=4):
    """炉。石の輪と薪、炎（発光体）と揺らぐ点光源。"""
    rnd = random.Random(seed)
    x, y, z = loc
    bm = bmesh.new()
    for k in range(11):
        a = 2 * math.pi * k / 11
        geom = bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.13)
        for v in geom["verts"]:
            v.co = Vector((v.co.x * rnd.uniform(0.9, 1.3), v.co.y, v.co.z * 0.7)) + Vector((0.55 * math.cos(a), 0.55 * math.sin(a), 0.05))
    stones = mesh_object("HearthStones", bm, p.rubble)
    stones.location = loc
    for k in range(5):
        a = 2 * math.pi * k / 5 + rnd.uniform(-0.2, 0.2)
        tube_along(f"Log{k}", [(x + 0.4 * math.cos(a), y + 0.4 * math.sin(a), z + 0.05), (x + 0.05 * math.cos(a), y + 0.05 * math.sin(a), z + 0.28)], 0.04, p.char)
    flames = []
    for k in range(4):
        fl = lathe(f"Flame{k}", [(0.0, 0.0), (0.12, 0.08), (0.08, 0.3), (0.0, 0.55)], segments=12, mat=p.fire)
        fl.location = (x + rnd.uniform(-0.08, 0.08), y + rnd.uniform(-0.08, 0.08), z + 0.08)
        fl.scale = (rnd.uniform(0.6, 1.0),) * 2 + (rnd.uniform(0.6, 1.1),)
        fl.visible_shadow = False
        fl.keyframe_insert("scale", frame=frames[0])
        add_noise(fl, "scale", strength=0.35, scale=2.5, phase=k * 7.0)
        flames.append(fl)
    bpy.ops.object.light_add(type="POINT", location=(x, y, z + 0.4))
    light = bpy.context.object
    light.name = "HearthLight"
    light.data.energy = 600
    light.data.color = (1.0, 0.55, 0.22)
    light.data.shadow_soft_size = 0.25
    light.data.keyframe_insert("energy", frame=frames[0])
    add_noise(light.data, "energy", strength=250, scale=2.0)
    return light


def vultures(p, center, frames, n=3, seed=6):
    """上空を旋回するハゲワシ。羽ばたかず滑空し、旋回に合わせて機体を傾ける。"""
    rnd = random.Random(seed)
    for i in range(n):
        pivot = bpy.data.objects.new(f"VulturePivot{i}", None)
        link(pivot)
        pivot.location = (center[0] + rnd.uniform(-15, 15), center[1] + rnd.uniform(-5, 20), rnd.uniform(28, 45))
        bm = bmesh.new()
        span = rnd.uniform(2.4, 2.8)
        # 胴と、先が指のように割れた幅広の翼（平面の多角形）
        wing = [(0, 0.35), (0.3, 0.35), (span / 2 * 0.8, 0.25), (span / 2, 0.12), (span / 2 * 0.95, -0.05), (span / 2 * 0.7, -0.15), (0.3, -0.25), (0, -0.25)]
        vs = [bm.verts.new((x, y, 0.08 * abs(x))) for x, y in wing] + [bm.verts.new((-x, y, 0.08 * abs(x))) for x, y in reversed(wing)]
        bm.faces.new(vs)
        geom = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.12, radius2=0.03, depth=1.0)
        bmesh.ops.rotate(bm, verts=geom["verts"], cent=(0, 0, 0), matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
        bird = mesh_object(f"Vulture{i}", bm, p.bark)
        bird.modifiers.new("Solidify", "SOLIDIFY").thickness = 0.03
        r = rnd.uniform(8, 16)
        bird.parent = pivot
        bird.location = (r, 0, 0)
        bird.rotation_euler = (0, math.radians(-22), 0)  # 内側へバンク
        speed = rnd.uniform(0.9, 1.4) * (1 if i % 2 == 0 else -1)
        start = rnd.uniform(0, 2 * math.pi)
        for f in frames:
            pivot.rotation_euler.z = start + speed * (f - frames[0]) / 24 * (2 * math.pi / 20)
            pivot.keyframe_insert("rotation_euler", index=2, frame=f)
        if speed < 0:
            bird.rotation_euler.z = math.pi
            bird.rotation_euler.y = math.radians(22)
        linear_keys(pivot)
