# 夕映えの空（物理的な空＋夕雲）、太陽、海、篝火と灯台の光。
import math

import bmesh
import bpy
from mathutils import Vector

import anim
import plan as P

SUN_EL, SUN_AZ = 3.5, 252.0  # 西南西の低い太陽（方位は北から時計回り）


def sun_dir():
    el, az = math.radians(SUN_EL), math.radians(SUN_AZ)
    return Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))


def sky(scene):
    """空 = 物理的な空（多重散乱）＋ 方向ベクトルから作る夕雲。雲は太陽に近いほど赤金に照らす。"""
    w = bpy.data.worlds.new("SunsetSky")
    scene.world = w
    nt = w.node_tree
    bg = nt.nodes["Background"]
    out = nt.nodes["World Output"]
    s = sun_dir()
    sk = nt.nodes.new("ShaderNodeTexSky")
    sk.sky_type = "MULTIPLE_SCATTERING"
    sk.sun_elevation = math.radians(SUN_EL)
    sk.sun_rotation = math.atan2(s.y, s.x)
    sk.sun_disc = True
    sk.sun_size = math.radians(1.2)
    sk.air_density = 1.6
    sk.aerosol_density = 3.0
    # 雲: 視線方向 d を高さで割って「雲の層」の平面座標にし、ノイズで塊を作る
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])

    def m(op, a, b=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs[0]

    zc = m("MAXIMUM", sep.outputs["Z"], 0.08)
    comb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(m("DIVIDE", sep.outputs["X"], zc), comb.inputs["X"])
    nt.links.new(m("MULTIPLY", m("DIVIDE", sep.outputs["Y"], zc), 1.8), comb.inputs["Y"])
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.35
    nz.inputs["Detail"].default_value = 8.0
    nz.inputs["Roughness"].default_value = 0.62
    nt.links.new(comb.outputs[0], nz.inputs["Vector"])
    cover = nt.nodes.new("ShaderNodeMapRange")
    cover.inputs["From Min"].default_value = 0.47
    cover.inputs["From Max"].default_value = 0.72
    nt.links.new(nz.outputs["Fac"], cover.inputs["Value"])
    # 地平線のすぐ上は雲を消す（座標が引き伸ばされて縞になるため）、天頂へも薄く
    low = nt.nodes.new("ShaderNodeMapRange")
    low.inputs["From Min"].default_value = 0.05
    low.inputs["From Max"].default_value = 0.16
    nt.links.new(sep.outputs["Z"], low.inputs["Value"])
    high = nt.nodes.new("ShaderNodeMapRange")
    high.inputs["From Min"].default_value = 0.6
    high.inputs["From Max"].default_value = 0.25
    nt.links.new(sep.outputs["Z"], high.inputs["Value"])
    dens = m("MULTIPLY", cover.outputs["Result"], m("MULTIPLY", low.outputs["Result"], high.outputs["Result"]))
    # 太陽に近い雲ほど明るい（d・s）
    dot = nt.nodes.new("ShaderNodeVectorMath")
    dot.operation = "DOT_PRODUCT"
    nt.links.new(tc.outputs["Generated"], dot.inputs[0])
    dot.inputs[1].default_value = tuple(s)
    near = m("POWER", m("MAXIMUM", m("ADD", m("MULTIPLY", dot.outputs["Value"], 0.5), 0.5), 0.0), 3.0)
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    el = ramp.color_ramp.elements
    el[0].position, el[0].color = 0.0, (0.16, 0.08, 0.1, 1)
    el[1].position, el[1].color = 1.0, (2.4, 1.0, 0.35, 1)
    el.new(0.35).color = (0.7, 0.28, 0.18, 1)
    nt.links.new(near, ramp.inputs["Fac"])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    nt.links.new(dens, mix.inputs["Factor"])
    nt.links.new(sk.outputs["Color"], mix.inputs["A"])
    nt.links.new(ramp.outputs["Color"], mix.inputs["B"])
    nt.links.new(mix.outputs["Result"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.4
    nt.links.new(bg.outputs[0], out.inputs["Surface"])

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 3000))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy = 3.2
    sun.data.angle = math.radians(1.0)
    sun.data.color = (1.0, 0.56, 0.28)
    sun.rotation_euler = (-s).to_track_quat("-Z", "Y").to_euler()
    return sun


def sea(M):
    """海と環の水。底（-14）から海面 0 まで満ちる。環の水は少し上に重ねて光らせる。"""
    bpy.ops.mesh.primitive_plane_add(size=36000, location=(0, 0, -14.5))
    s = bpy.context.object
    s.name = "Sea"
    s.data.materials.append(M.sea)
    f0, f1 = P.CUES["sea_fill"]
    anim.loc(s, [(1, (0, 0, -14.5)), (f0, (0, 0, -14.5)), (f1, (0, 0, 0.0))])
    rings = []
    for kind, r0, r1, name in P.RINGS:
        if kind != "water":
            continue
        bm = bmesh.new()
        outer = [bm.verts.new((r1 * math.cos(a), r1 * math.sin(a), 0)) for a in [2 * math.pi * i / 192 for i in range(192)]]
        inner = [bm.verts.new((r0 * math.cos(a), r0 * math.sin(a), 0)) for a in [2 * math.pi * i / 192 for i in range(192)]]
        for i in range(192):
            j = (i + 1) % 192
            bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
        me = bpy.data.meshes.new(f"RingWater_{int(r0)}")
        bm.to_mesh(me)
        bm.free()
        me.materials.append(M.ring_water)
        o = bpy.data.objects.new(me.name, me)
        bpy.context.scene.collection.objects.link(o)
        anim.loc(o, [(1, (0, 0, -14.4)), (f0, (0, 0, -14.4)), (f1, (0, 0, 0.05))])
        rings.append(o)
    g0, g1 = P.CUES["rings_glow"]
    anim.value("ring_glow", [(1, 0.0), (g0, 0.0), (g0 + 12, 1.0), (g1, 0.35), (P.MAIN_END, 0.3)])
    return s, rings


def fires(M, tops):
    """篝火: 塔の上の炎（発光体）と点光源。lights の区間で順にともる。"""
    bm = bmesh.new()
    for x, y, z in tops:
        g = bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=1.6, radius2=0.1, depth=4.0)
        for v in g["verts"]:
            v.co += Vector((x, y, z + 2.0))
    me = bpy.data.meshes.new("Fires")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.fire)
    o = bpy.data.objects.new("Fires", me)
    bpy.context.scene.collection.objects.link(o)
    o.visible_shadow = False
    f0, f1 = P.CUES["lights"]
    anim.value("fires", [(1, 0.0), (f0, 0.0), (f1, 1.0), (P.MAIN_END, 1.0)])
    lights = []
    for i, (x, y, z) in enumerate(tops[:: max(1, len(tops) // 24)]):
        bpy.ops.object.light_add(type="POINT", location=(x, y, z + 4))
        L = bpy.context.object
        L.name = f"FireLight{i}"
        L.data.color = (1.0, 0.5, 0.18)
        L.data.shadow_soft_size = 2.0
        start = f0 + int((f1 - f0) * i / 24)
        anim.light_energy(L, [(1, 0.0), (start, 0.0), (start + 8, 3.0e5), (P.MAIN_END, 3.0e5)])
        lights.append(L)
    lx, ly = P.LIGHTHOUSE
    bpy.ops.object.light_add(type="POINT", location=(lx, ly, 52))
    B = bpy.context.object
    B.name = "BeaconLight"
    B.data.color = (1.0, 0.7, 0.4)
    B.data.shadow_soft_size = 3.0
    anim.light_energy(B, [(1, 0.0), (f0 + 10, 0.0), (f0 + 22, 2.0e6), (P.MAIN_END, 2.0e6)])
    anim.value("beacon", [(1, 0.0), (f0 + 10, 0.0), (f0 + 22, 1.0)])
    anim.value("lights", [(1, 0.0), (f0, 0.0), (f1 + 20, 1.0)])
    return o
