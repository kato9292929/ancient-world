# 部屋の箱・窓・光。座標系: x = 左右（左壁 -X に窓）、y = 奥行き（+Y が机のある奥の壁）、z = 高さ。単位 m。
import math
import random

import bpy
from mathutils import Vector

from util import box, grid, mesh_object, plane

W, D, H = 4.2, 3.6, 2.7  # 部屋の内寸
T = 0.12  # 壁厚
X0, X1, Y0, Y1 = -W / 2, W / 2, -D / 2, D / 2

# 左壁の窓（開口）。y 範囲と z 範囲。
WIN_Y = (0.15, 1.45)
WIN_Z = (0.95, 2.25)


def build(p):
    box("Floor", (W + 2 * T, D + 2 * T, T), (0, 0, -T / 2), p.floor)
    box("Ceiling", (W + 2 * T, D + 2 * T, T), (0, 0, H + T / 2), p.ceiling)
    box("WallBack", (W, T, H), (0, Y1 + T / 2, H / 2), p.wall)
    box("WallFront", (W, T, H), (0, Y0 - T / 2, H / 2), p.wall)
    box("WallRight", (T, D + 2 * T, H), (X1 + T / 2, 0, H / 2), p.wall)
    _window_wall(p)
    _skirting(p)
    _rug(p)
    _outside(p)
    _curtain(p)


def _window_wall(p):
    """左壁を開口の周り4枚に分けて組む（ブーリアンを使わない）。"""
    x = X0 - T / 2
    y_lo, y_hi = WIN_Y
    z_lo, z_hi = WIN_Z
    box("WallLeft_A", (T, y_lo - Y0 + T, H), (x, (Y0 - T + y_lo) / 2, H / 2), p.wall)
    box("WallLeft_B", (T, Y1 + T - y_hi, H), (x, (y_hi + Y1 + T) / 2, H / 2), p.wall)
    box("WallLeft_Sill", (T, y_hi - y_lo, z_lo), (x, (y_lo + y_hi) / 2, z_lo / 2), p.wall)
    box("WallLeft_Head", (T, y_hi - y_lo, H - z_hi), (x, (y_lo + y_hi) / 2, (z_hi + H) / 2), p.wall)

    # 木枠と方立て。ガラスは入れない（太陽光の集光ノイズを避けるため。手前から見えない角度に置いている）。
    f = 0.05
    cy = (y_lo + y_hi) / 2
    cz = (z_lo + z_hi) / 2
    for name, size, loc in [
        ("WinFrameL", (T + 0.02, f, z_hi - z_lo), (x, y_lo + f / 2, cz)),
        ("WinFrameR", (T + 0.02, f, z_hi - z_lo), (x, y_hi - f / 2, cz)),
        ("WinFrameT", (T + 0.02, y_hi - y_lo, f), (x, cy, z_hi - f / 2)),
        ("WinFrameB", (T + 0.06, y_hi - y_lo + 0.08, f), (x + 0.03, cy, z_lo - f / 2)),
        ("WinMullion", (0.04, 0.035, z_hi - z_lo), (x, cy, cz)),
        ("WinTransom", (0.04, y_hi - y_lo, 0.035), (x, cy, z_lo + (z_hi - z_lo) * 0.62)),
    ]:
        box(name, size, loc, p.steel_white, bevel=0.004)

    # 窓のポータル。空の光を窓から重点的にサンプリングしてノイズを減らす。
    bpy.ops.object.light_add(type="AREA", location=(X0 - T - 0.01, cy, cz))
    portal = bpy.context.object
    portal.name = "WindowPortal"
    portal.data.shape = "RECTANGLE"
    portal.data.size = y_hi - y_lo
    portal.data.size_y = z_hi - z_lo
    portal.data.cycles.is_portal = True
    portal.rotation_euler = (0, math.radians(90), 0)


def _outside(p):
    """窓の外。地面と遠景の木立（形は大づかみ。窓越しに水平線が見えるのを防ぐ）。"""
    box("Ground", (60, 60, 0.1), (X0 - 30, 0, -0.6), p.grass)
    rnd = random.Random(11)
    for i in range(14):
        y = -9 + i * 1.6 + rnd.uniform(-0.5, 0.5)
        x = X0 - rnd.uniform(9, 14)
        r = rnd.uniform(1.4, 2.4)
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=r, location=(x, y, r * 0.8 + rnd.uniform(0, 1.5)))
        tree = bpy.context.object
        tree.name = f"Tree{i}"
        tree.scale.z = rnd.uniform(1.0, 1.5)
        tree.data.materials.append(p.foliage)
        d = tree.modifiers.new("Lumps", "DISPLACE")
        tex = bpy.data.textures.new(f"TreeNoise{i}", "CLOUDS")
        tex.noise_scale = 0.6
        d.texture = tex
        d.strength = 0.6
        tree.visible_shadow = False


def _curtain(p):
    """窓の奥側に寄せたレースのカーテン。プリーツは正弦波で、レールは天井際。"""
    x_wall = X0 + 0.06
    y_lo, y_hi = WIN_Y[1] - 0.55, WIN_Y[1] + 0.12
    z_lo, z_hi = WIN_Z[0] - 0.05, WIN_Z[1] + 0.2
    bm = grid(40, 6)
    for v in bm.verts:
        u, t = v.co.x + 0.5, v.co.y + 0.5
        v.co = Vector((0.03 * math.sin(u * 2 * math.pi * 9) * (0.7 + 0.3 * t), y_lo + (y_hi - y_lo) * u, z_lo + (z_hi - z_lo) * t))
    cur = mesh_object("Curtain", bm, p.curtain)
    cur.location.x = x_wall
    for poly in cur.data.polygons:
        poly.use_smooth = True
    box("CurtainRail", (0.02, WIN_Y[1] - WIN_Y[0] + 0.4, 0.02), (x_wall, (WIN_Y[0] + WIN_Y[1]) / 2, z_hi + 0.02), p.steel_white)


def _skirting(p):
    h, t = 0.08, 0.015
    box("SkirtBack", (W, t, h), (0, Y1 - t / 2, h / 2), p.steel_white)
    box("SkirtRight", (t, D, h), (X1 - t / 2, 0, h / 2), p.steel_white)


def _rug(p):
    box("Rug", (2.0, 1.4, 0.008), (-0.2, 0.55, 0.004), p.rug)


def lights_and_world(scene):
    """午後の西日が左の窓から差し込む想定。太陽 + 空。"""
    world = bpy.data.worlds.new("Sky")
    scene.world = world
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = math.radians(24)
    sky.sun_rotation = math.radians(200)
    sky.sun_disc = False
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.35

    bpy.ops.object.light_add(type="SUN", location=(X0 - 2, 0.8, 3))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy = 6.0
    sun.data.angle = math.radians(1.5)
    sun.data.color = (1.0, 0.86, 0.68)
    d = Vector((0.8, 0.25, -0.45)).normalized()  # 光の進む向き
    sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

    # 室内の環境光の底上げ。天井付近の大きな面光源（見えないように camera 不可視）。
    bpy.ops.object.light_add(type="AREA", location=(0.4, -0.2, H - 0.05))
    fill = bpy.context.object
    fill.name = "CeilingFill"
    fill.data.shape = "RECTANGLE"
    fill.data.size, fill.data.size_y = 2.5, 2.0
    fill.data.energy = 60
    fill.data.color = (1.0, 0.92, 0.82)
    fill.visible_camera = False


def poster(name, path, w, h, loc, frame_mat):
    """額装ポスター。画像の縦横比は呼び出し側で合わせる。"""
    from materials import image

    m = image(f"{name}Img", path, rough=0.35)
    fw = 0.025
    box(f"{name}Frame", (w + 2 * fw, 0.025, h + 2 * fw), (loc[0], loc[1] + 0.0125, loc[2]), frame_mat, bevel=0.003)
    plane(f"{name}Print", w, h, (loc[0], loc[1] - 0.001, loc[2]), mat=m)
