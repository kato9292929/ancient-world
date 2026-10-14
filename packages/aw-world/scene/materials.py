# 素材。外部テクスチャを使わず、すべてプロシージャルで組む。
import bpy


def _new(name):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    return mat, nt, nt.nodes["Principled BSDF"]


def _coord(nt, kind="Object"):
    return nt.nodes.new("ShaderNodeTexCoord").outputs[kind]


def _noise(nt, scale, detail=6.0, rough=0.6, vec=None):
    n = nt.nodes.new("ShaderNodeTexNoise")
    n.inputs["Scale"].default_value = scale
    n.inputs["Detail"].default_value = detail
    n.inputs["Roughness"].default_value = rough
    nt.links.new(vec or _coord(nt), n.inputs["Vector"])
    return n.outputs["Fac"]


def _ramp(nt, src, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
    el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        el.new(pos).color = (*col, 1)
    nt.links.new(src, r.inputs["Fac"])
    return r.outputs["Color"]


def _mix(nt, a, b, fac, blend="MIX"):
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    m.blend_type = blend
    if isinstance(fac, float):
        m.inputs["Factor"].default_value = fac
    else:
        nt.links.new(fac, m.inputs["Factor"])
    nt.links.new(a, m.inputs["A"])
    nt.links.new(b, m.inputs["B"])
    return m.outputs["Result"]


def _bump(nt, bsdf, height, strength, distance=0.02):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = distance
    nt.links.new(height, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def limestone(name, base=(0.72, 0.64, 0.5), pitted=1.0):
    """石灰岩。大きな色むら（風化）＋細かい孔の凹凸。ノミ跡の荒さは pitted で調整。"""
    mat, nt, bsdf = _new(name)
    big = _noise(nt, 1.2, 4)
    fine = _noise(nt, 18.0, 10, 0.7)
    dark = tuple(c * 0.62 for c in base)
    warm = (base[0] * 1.05, base[1] * 0.95, base[2] * 0.82)
    col = _ramp(nt, big, [(0.3, dark), (0.5, base), (0.75, warm)])
    speck = _ramp(nt, fine, [(0.35, (0.55, 0.55, 0.55)), (0.6, (1, 1, 1))])
    nt.links.new(_mix(nt, col, speck, 0.6, "MULTIPLY"), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.92
    height = _noise(nt, 6.0, 12, 0.75)
    _bump(nt, bsdf, height, 0.45 * pitted, 0.03)
    return mat


def soil(name):
    """赤みのある乾いた土。テラ・ロッサ寄り。"""
    mat, nt, bsdf = _new(name)
    f = _noise(nt, 2.5, 8)
    col = _ramp(nt, f, [(0.3, (0.3, 0.17, 0.1)), (0.7, (0.48, 0.32, 0.2))])
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    _bump(nt, bsdf, _noise(nt, 30, 8), 0.4)
    return mat


def ground(name):
    """丘の地表。土と枯れ草色を大きなノイズで斑に混ぜる。草のインスタンスと色を合わせる。"""
    mat, nt, bsdf = _new(name)
    patch = _noise(nt, 0.08, 6, 0.55)
    dirt = _ramp(nt, _noise(nt, 3.0, 6), [(0.3, (0.28, 0.17, 0.1)), (0.7, (0.42, 0.29, 0.18))])
    grass = _ramp(nt, _noise(nt, 1.0, 4), [(0.3, (0.4, 0.32, 0.14)), (0.7, (0.55, 0.45, 0.22))])
    fac = _ramp(nt, patch, [(0.42, (0, 0, 0)), (0.58, (1, 1, 1))])
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = "RGBA"
    nt.links.new(fac, m.inputs["Factor"])
    nt.links.new(dirt, m.inputs["A"])
    nt.links.new(grass, m.inputs["B"])
    nt.links.new(m.outputs["Result"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    _bump(nt, bsdf, _noise(nt, 12, 8), 0.3)
    return mat


def plain(name, color, rough=0.8, sheen=0.0, translucent=0.0):
    mat, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Sheen Weight"].default_value = sheen
    if translucent > 0:
        bsdf.inputs["Subsurface Weight"].default_value = translucent
        bsdf.inputs["Subsurface Radius"].default_value = (0.2, 0.2, 0.05)
        bsdf.inputs["Subsurface Scale"].default_value = 0.01
    return mat


def foliage(name, color):
    """木の葉の塊。ノイズで明暗を入れ、裏から透ける光を少し足す。"""
    mat, nt, bsdf = _new(name)
    f = _noise(nt, 4.0, 6)
    dark = tuple(c * 0.5 for c in color)
    nt.links.new(_ramp(nt, f, [(0.35, dark), (0.65, color)]), bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    _bump(nt, bsdf, _noise(nt, 25, 4), 0.8)
    return mat


def fire(name):
    mat, nt, bsdf = _new(name)
    f = _noise(nt, 6.0, 4)
    col = _ramp(nt, f, [(0.3, (1.0, 0.25, 0.03)), (0.7, (1.0, 0.65, 0.2))])
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    nt.links.new(col, bsdf.inputs["Emission Color"])
    bsdf.inputs["Emission Strength"].default_value = 12.0
    return mat


class Palette:
    def __init__(self):
        self.pillar = limestone("PillarLimestone", (0.58, 0.5, 0.38), pitted=0.8)
        self.relief = limestone("ReliefLimestone", (0.62, 0.54, 0.41), pitted=0.6)
        self.rubble = limestone("RubbleStone", (0.5, 0.44, 0.34), pitted=1.4)
        self.bedrock = limestone("Bedrock", (0.5, 0.43, 0.33), pitted=0.5)
        self.soil = soil("Soil")
        self.ground = ground("Ground")
        self.grass = plain("DryGrass", (0.55, 0.45, 0.2), rough=0.7, translucent=0.2)
        self.grass_green = plain("GreenGrass", (0.25, 0.3, 0.1), rough=0.7, translucent=0.2)
        self.bark = plain("Bark", (0.12, 0.09, 0.07), rough=0.95)
        self.leaves = foliage("Leaves", (0.16, 0.22, 0.07))
        self.leaves_dry = foliage("LeavesOlive", (0.24, 0.26, 0.12))
        self.fire = fire("Fire")
        self.char = plain("Charcoal", (0.02, 0.018, 0.015), rough=0.9)
        self.hide = plain("Hide", (0.35, 0.22, 0.13), rough=0.85, sheen=0.4)
