# メッシュ生成・配置・アニメーションの小さな道具。aw-study の util.py と同じもの（パッケージ間で import しないため複製）。
import math

import bmesh
import bpy
from mathutils import Vector


def link(obj, collection=None):
    (collection or bpy.context.scene.collection).objects.link(obj)
    return obj


def mesh_object(name, bm, mat=None, collection=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    if mat is not None:
        obj.data.materials.append(mat)
    return link(obj, collection)


def box(name, size, loc, mat=None, bevel=0.0, rot=(0, 0, 0), collection=None):
    """中心 loc、寸法 size(x, y, z) の直方体。bevel > 0 なら角を面取りする（光を拾うため）。"""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co = Vector((v.co.x * size[0], v.co.y * size[1], v.co.z * size[2]))
    obj = mesh_object(name, bm, mat, collection)
    obj.location = loc
    obj.rotation_euler = rot
    if bevel > 0:
        m = obj.modifiers.new("Bevel", "BEVEL")
        m.width = bevel
        m.segments = 2
        m.limit_method = "ANGLE"
    return obj


def lathe(name, profile, segments=48, mat=None, loc=(0, 0, 0), smooth=True, collection=None):
    """(半径, 高さ) の列を Z 軸まわりに回した回転体。照明のシェードやマグカップ用。"""
    bm = bmesh.new()
    rings = []
    for r, z in profile:
        ring = []
        for i in range(segments):
            a = 2 * math.pi * i / segments
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segments):
            j = (i + 1) % segments
            bm.faces.new((a[i], a[j], b[j], b[i]))
    obj = mesh_object(name, bm, mat, collection)
    obj.location = loc
    if smooth:
        shade_smooth(obj)
    return obj


def cylinder(name, radius, depth, loc, mat=None, segments=32, rot=(0, 0, 0), collection=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=segments, radius1=radius, radius2=radius, depth=depth)
    obj = mesh_object(name, bm, mat, collection)
    obj.location = loc
    obj.rotation_euler = rot
    shade_smooth(obj)
    return obj


def tube_along(name, points, radius, mat=None, closed=False, collection=None):
    """点列を通る丸パイプ（曲げ木の椅子、照明のアーム用）。"""
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.use_fill_caps = True
    sp = cu.splines.new("NURBS")
    sp.points.add(len(points) - 1)
    for p, co in zip(sp.points, points):
        p.co = (*co, 1.0)
    sp.use_endpoint_u = not closed
    sp.use_cyclic_u = closed
    sp.order_u = min(4, len(points))
    sp.resolution_u = 16
    obj = bpy.data.objects.new(name, cu)
    if mat is not None:
        cu.materials.append(mat)
    return link(obj, collection)


def plane(name, w, h, loc, rot=(0, 0, 0), mat=None, cuts=0, collection=None):
    """XZ 面に立つ板（壁に貼るポスター向き）。UV は 0..1 で全面。"""
    bm = grid(cuts + 1, cuts + 1)
    for v in bm.verts:
        v.co = Vector((v.co.x * w, 0.0, v.co.y * h))
    obj = mesh_object(name, bm, mat, collection)
    obj.location = loc
    obj.rotation_euler = rot
    return obj


def grid(x_segments, y_segments):
    """-0.5..0.5 の格子（UV 付き）。calc_uvs は UV レイヤーが先にないと何も書かないので先に作る。"""
    bm = bmesh.new()
    bm.loops.layers.uv.new("UVMap")
    bmesh.ops.create_grid(bm, x_segments=x_segments, y_segments=y_segments, size=0.5, calc_uvs=True)
    return bm


def shade_smooth(obj):
    for p in obj.data.polygons:
        p.use_smooth = True


def look_at(obj, target):
    d = Vector(target) - obj.location
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def fcurves(id_data):
    """Blender 5 の slotted action からも旧 API からも F カーブを取り出す。"""
    ad = id_data.animation_data
    act = ad.action
    if hasattr(act, "fcurves"):
        return act.fcurves
    from bpy_extras import anim_utils

    return anim_utils.action_get_channelbag_for_slot(act, ad.action_slot).fcurves


def add_noise(id_data, data_path, strength, scale, phase=0.0, index=None):
    """キー済みチャンネルにノイズ修飾子を足す（手ブレ・付箋のなびき）。"""
    for fc in fcurves(id_data):
        if fc.data_path == data_path and (index is None or fc.array_index == index):
            m = fc.modifiers.new("NOISE")
            m.strength = strength
            m.scale = scale
            m.phase = phase + fc.array_index * 13.7


def linear_keys(id_data):
    for fc in fcurves(id_data):
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
