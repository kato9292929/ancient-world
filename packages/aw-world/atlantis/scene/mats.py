# 素材。すべてプロシージャル（巻物の絵だけ atlantis/drawings/parchment.py で作った画像）。
# 金属は白飛びさせないよう、粗さを 0.25 以上にして色が残るようにする。
# 石の三色（白・黒・赤）は、ブロックごとの控えめな色差と大きなノイズで混ぜ、チェック柄にしない。
import bpy

ANIM = {}  # 動かす値ノード（名前 → ソケット）。anim.py からキーを打つ


def _new(name):
    m = bpy.data.materials.new(name)
    nt = m.node_tree
    return m, nt, nt.nodes["Principled BSDF"]


def _n(nt, kind, **inputs):
    node = nt.nodes.new(kind)
    for k, v in inputs.items():
        node.inputs[k].default_value = v
    return node


def _coord(nt, kind="Object"):
    return nt.nodes.new("ShaderNodeTexCoord").outputs[kind]


def _noise(nt, scale, detail=4.0, vec=None):
    n = _n(nt, "ShaderNodeTexNoise", Scale=scale, Detail=detail)
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
    if isinstance(fac, (int, float)):
        m.inputs["Factor"].default_value = fac
    else:
        nt.links.new(fac, m.inputs["Factor"])
    for sock, v in (("A", a), ("B", b)):
        if isinstance(v, tuple):
            m.inputs[sock].default_value = (*v, 1)
        else:
            nt.links.new(v, m.inputs[sock])
    return m.outputs["Result"]


def _math(nt, op, a, b=None):
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = op
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            m.inputs[i].default_value = v
        else:
            nt.links.new(v, m.inputs[i])
    return m.outputs[0]


def _bump(nt, bsdf, h, strength, dist=0.05):
    b = _n(nt, "ShaderNodeBump", Strength=strength, Distance=dist)
    nt.links.new(h, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def _value(nt, name, v=0.0):
    node = nt.nodes.new("ShaderNodeValue")
    node.name = name
    node.outputs[0].default_value = v
    ANIM.setdefault(name, []).append((nt, node))
    return node.outputs[0]


def fadeable(mat, extra=None):
    """オブジェクトの色の α で透明にできるようにする（巻物を消す、線を消す）。extra を掛け合わせられる。"""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    src = out.inputs["Surface"].links[0].from_socket
    info = nt.nodes.new("ShaderNodeObjectInfo")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    fac = info.outputs["Alpha"] if extra is None else _math(nt, "MULTIPLY", info.outputs["Alpha"], extra)
    nt.links.new(fac, mix.inputs["Fac"])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(src, mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


def metal(name, color, rough=0.3, aniso=0.0):
    m, nt, b = _new(name)
    b.inputs["Metallic"].default_value = 1.0
    b.inputs["Roughness"].default_value = rough
    b.inputs["Anisotropic"].default_value = aniso
    # わずかな曇りむら（真新しい鏡面にしない）
    col = _mix(nt, color, tuple(c * 0.8 for c in color), _noise(nt, 0.6, 6), "MIX")
    nt.links.new(col, b.inputs["Base Color"])
    rr = _math(nt, "ADD", _math(nt, "MULTIPLY", _noise(nt, 3.0), 0.15), rough - 0.07)
    nt.links.new(rr, b.inputs["Roughness"])
    return m


def stone3(name, scale=1.0, blocks=True):
    """白を基調に、黒と赤の石を控えめに混ぜた石積み。"""
    m, nt, b = _new(name)
    co = _coord(nt)
    white, black, red = (0.72, 0.69, 0.63), (0.5, 0.47, 0.44), (0.68, 0.53, 0.45)
    if blocks:
        br = _n(nt, "ShaderNodeTexBrick", Scale=0.35 / scale, **{"Mortar Size": 0.012, "Bias": 0.0, "Row Height": 0.45, "Brick Width": 1.1})
        br.inputs["Color1"].default_value = (0.0, 0.0, 0.0, 1)
        br.inputs["Color2"].default_value = (1.0, 1.0, 1.0, 1)
        br.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1)
        nt.links.new(co, br.inputs["Vector"])
        pick = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(br.outputs["Color"], pick.inputs[0])
        sel = pick.outputs[0]
        mortar = br.outputs["Fac"]
    else:
        sel = _noise(nt, 0.05 / scale, 2)
        mortar = None
    big = _noise(nt, 0.004 / scale, 3)
    redness = _ramp(nt, _math(nt, "ADD", _math(nt, "MULTIPLY", sel, 0.6), _math(nt, "MULTIPLY", big, 0.4)), [(0.55, (0, 0, 0)), (0.85, (1, 1, 1))])
    darkness = _ramp(nt, _math(nt, "SUBTRACT", 1.0, sel), [(0.75, (0, 0, 0)), (0.95, (1, 1, 1))])
    col = _mix(nt, white, red, redness)
    col = _mix(nt, col, black, darkness, "MIX")
    grime = _noise(nt, 0.5 / scale, 8)
    col = _mix(nt, col, _ramp(nt, grime, [(0.3, (0.8, 0.8, 0.8)), (0.7, (1, 1, 1))]), 1.0, "MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.75
    h = _noise(nt, 4.0 / scale, 8)
    if mortar is not None:
        h = _math(nt, "SUBTRACT", h, _math(nt, "MULTIPLY", mortar, 0.6))
    _bump(nt, b, h, 0.35, 0.08 * scale)
    return m


def marble(name):
    m, nt, b = _new(name)
    co = _coord(nt)
    wave = _n(nt, "ShaderNodeTexWave", Scale=0.08, Distortion=12.0, Detail=6.0)
    nt.links.new(co, wave.inputs["Vector"])
    col = _ramp(nt, wave.outputs["Fac"], [(0.0, (0.9, 0.88, 0.84)), (0.85, (0.86, 0.84, 0.8)), (0.95, (0.55, 0.52, 0.5)), (1.0, (0.85, 0.83, 0.79))])
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.35
    b.inputs["Coat Weight"].default_value = 0.15
    b.inputs["Subsurface Weight"].default_value = 0.05
    return m


def tiles(name, color=(0.5, 0.22, 0.12), scale=1.0):
    """瓦。行ごとの段差（波模様）と一枚ずつの色むら。"""
    m, nt, b = _new(name)
    br = _n(nt, "ShaderNodeTexBrick", Scale=2.0 / scale, **{"Mortar Size": 0.03, "Row Height": 0.35, "Brick Width": 0.6})
    br.inputs["Color1"].default_value = (*color, 1)
    br.inputs["Color2"].default_value = (*(c * 0.75 for c in color), 1)
    br.inputs["Mortar"].default_value = (0.1, 0.06, 0.04, 1)
    nt.links.new(_coord(nt), br.inputs["Vector"])
    nt.links.new(br.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.6
    _bump(nt, b, br.outputs["Fac"], 0.5, 0.1 * scale)
    return m


def house(name, wall=(0.78, 0.72, 0.62)):
    """家の壁。漆喰＋窓。窓は「灯り」の値で夕暮れに灯る（家ごとに点く・点かないが分かれる）。"""
    m, nt, b = _new(name)
    info = nt.nodes.new("ShaderNodeObjectInfo")
    tint = _ramp(nt, info.outputs["Random"], [(0.0, wall), (0.5, tuple(c * 0.92 for c in wall)), (1.0, (wall[0] * 0.95, wall[1] * 0.85, wall[2] * 0.78))])
    nt.links.new(tint, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    gen = _coord(nt, "Object")
    br = _n(nt, "ShaderNodeTexBrick", Scale=0.25, **{"Mortar Size": 0.7, "Row Height": 0.5, "Brick Width": 0.5, "Mortar Smooth": 0.0})
    br.inputs["Color1"].default_value = (1, 1, 1, 1)
    br.inputs["Color2"].default_value = (1, 1, 1, 1)
    br.inputs["Mortar"].default_value = (0, 0, 0, 1)
    nt.links.new(gen, br.inputs["Vector"])
    window = _math(nt, "SUBTRACT", 1.0, br.outputs["Fac"])
    on = _math(nt, "GREATER_THAN", info.outputs["Random"], 0.35)
    lights = _value(nt, "lights", 0.0)
    strength = _math(nt, "MULTIPLY", _math(nt, "MULTIPLY", window, on), _math(nt, "MULTIPLY", lights, 18.0))
    b.inputs["Emission Color"].default_value = (1.0, 0.55, 0.22, 1)
    nt.links.new(strength, b.inputs["Emission Strength"])
    return m


def water(name, deep=(0.01, 0.035, 0.05), glow_name=None):
    """水面。重ねた波のバンプ（うねり＋さざ波）、空の映り込み。glow_name を付けると環が光る値を持つ。"""
    m, nt, b = _new(name)
    co = _coord(nt)
    b.inputs["Base Color"].default_value = (*deep, 1)
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["IOR"].default_value = 1.33
    b.inputs["Specular IOR Level"].default_value = 0.6
    w1 = _n(nt, "ShaderNodeTexWave", Scale=0.004, Distortion=4.0, Detail=3.0)
    w1.wave_type = "BANDS"
    w1.bands_direction = "Y"
    nt.links.new(co, w1.inputs["Vector"])
    w2 = _noise(nt, 0.05, 8)
    w3 = _noise(nt, 0.6, 4)
    h = _math(nt, "ADD", _math(nt, "MULTIPLY", w1.outputs["Fac"], 0.6), _math(nt, "ADD", _math(nt, "MULTIPLY", w2, 0.3), _math(nt, "MULTIPLY", w3, 0.12)))
    _bump(nt, b, h, 0.25, 0.6)
    if glow_name:
        g = _value(nt, glow_name, 0.0)
        b.inputs["Emission Color"].default_value = (0.25, 0.6, 0.62, 1)
        ripple = _ramp(nt, w3, [(0.3, (0.4, 0.4, 0.4)), (0.7, (1, 1, 1))])
        sep = nt.nodes.new("ShaderNodeSeparateColor")
        nt.links.new(ripple, sep.inputs[0])
        nt.links.new(_math(nt, "MULTIPLY", g, sep.outputs[0]), b.inputs["Emission Strength"])
    return m


def ground(name):
    """平野: 乾いた土と草地、オリーブ畑の区画、灌漑水路の格子（1 スタディオンごと）。"""
    m, nt, b = _new(name)
    co = _coord(nt)
    soil = _ramp(nt, _noise(nt, 0.002, 4), [(0.3, (0.3, 0.23, 0.13)), (0.7, (0.36, 0.29, 0.16))])
    green = _ramp(nt, _noise(nt, 0.01, 4), [(0.3, (0.18, 0.19, 0.08)), (0.7, (0.24, 0.24, 0.1))])
    fields = _ramp(nt, _noise(nt, 0.0012, 2), [(0.35, (0, 0, 0)), (0.65, (0.8, 0.8, 0.8))])
    col = _mix(nt, soil, green, fields)
    # 区画の格子（185m ごと）と水路
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(co, sep.inputs[0])

    def line(axis):
        f = _math(nt, "FRACT", _math(nt, "DIVIDE", sep.outputs[axis], 185.0))
        d = _math(nt, "ABSOLUTE", _math(nt, "SUBTRACT", f, 0.5))
        return _math(nt, "GREATER_THAN", d, 0.488)

    canal = _math(nt, "MAXIMUM", line("X"), line("Y"))
    near = _math(nt, "LESS_THAN", _math(nt, "ABSOLUTE", sep.outputs["Y"]), 6000.0)
    canal = _math(nt, "MULTIPLY", canal, near)
    col = _mix(nt, col, (0.05, 0.1, 0.12), canal)
    nt.links.new(col, b.inputs["Base Color"])
    rough = _math(nt, "SUBTRACT", 0.95, _math(nt, "MULTIPLY", canal, 0.85))
    nt.links.new(rough, b.inputs["Roughness"])
    _bump(nt, b, _noise(nt, 0.05, 6), 0.3, 1.0)
    return m


def forest(name):
    """山の森。濃い緑の塊と、尾根の岩肌。"""
    m, nt, b = _new(name)
    co = _coord(nt)
    clumps = _n(nt, "ShaderNodeTexVoronoi", Scale=0.02)
    nt.links.new(co, clumps.inputs["Vector"])
    col = _ramp(nt, clumps.outputs["Distance"], [(0.0, (0.05, 0.09, 0.03)), (0.6, (0.08, 0.13, 0.05)), (1.0, (0.03, 0.05, 0.02))])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    rock = _ramp(nt, sep.outputs["Z"], [(0.55, (1, 1, 1)), (0.7, (0, 0, 0))])
    col = _mix(nt, col, (0.32, 0.3, 0.27), rock)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    _bump(nt, b, clumps.outputs["Distance"], 0.8, 4.0)
    return m


def leaves(name, color):
    m, nt, b = _new(name)
    col = _ramp(nt, _noise(nt, 0.6, 4), [(0.3, tuple(c * 0.55 for c in color)), (0.7, color)])
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Subsurface Weight"].default_value = 0.1
    _bump(nt, b, _noise(nt, 3.0, 4), 0.6, 0.3)
    return m


def emission(name, color, strength, anim_name=None):
    m, nt, b = _new(name)
    b.inputs["Base Color"].default_value = (0, 0, 0, 1)
    b.inputs["Emission Color"].default_value = (*color, 1)
    if anim_name:
        nt.links.new(_math(nt, "MULTIPLY", _value(nt, anim_name, 0.0), strength), b.inputs["Emission Strength"])
    else:
        b.inputs["Emission Strength"].default_value = strength
    return m


def wire(name, color=(1.0, 0.66, 0.28), strength=5.0):
    """光のインクの線。オブジェクトの色の α で現れたり消えたりする。"""
    m = emission(name, color, strength)
    return fadeable(m)


def parchment(name, img_path, mask_path):
    """羊皮紙。インクの線は "ink_glow" の値で光る。巻物全体はオブジェクトの α で消える。"""
    m, nt, b = _new(name)
    uv = _coord(nt, "UV")
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = bpy.data.images.load(img_path, check_existing=True)
    t.interpolation = "Cubic"
    nt.links.new(uv, t.inputs["Vector"])
    mk = nt.nodes.new("ShaderNodeTexImage")
    mk.image = bpy.data.images.load(mask_path, check_existing=True)
    mk.image.colorspace_settings.name = "Non-Color"
    nt.links.new(uv, mk.inputs["Vector"])
    nt.links.new(t.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    b.inputs["Sheen Weight"].default_value = 0.3
    glow = _value(nt, "ink_glow", 0.0)
    b.inputs["Emission Color"].default_value = (1.0, 0.7, 0.3, 1)
    nt.links.new(_math(nt, "MULTIPLY", mk.outputs["Color"], _math(nt, "MULTIPLY", glow, 6.0)), b.inputs["Emission Strength"])
    _bump(nt, b, _noise(nt, 0.02, 6), 0.15, 2.0)
    # 上（北）から広がる: UV の v が 1 - unroll より上だけ見せる
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(uv, sep.inputs[0])
    unroll = _value(nt, "unroll", 1.0)
    reveal = _math(nt, "GREATER_THAN", sep.outputs["Y"], _math(nt, "SUBTRACT", 1.0, unroll))
    return fadeable(m, reveal)


def haze(mat, color=(0.86, 0.6, 0.4), distance=38000.0):
    """空気遠近。カメラからの距離で、素材の出力を霞の色（発光）へ寄せる。ボリュームより軽い。"""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    src = out.inputs["Surface"].links[0].from_socket
    cam = nt.nodes.new("ShaderNodeCameraData")
    f = _math(nt, "SUBTRACT", 1.0, _math(nt, "EXPONENT", _math(nt, "DIVIDE", cam.outputs["View Distance"], -distance)))
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*color, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(f, mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(em.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return mat


class Mats:
    def __init__(self, tex_dir):
        import os

        self.stone = stone3("Stone3")
        self.stone_fine = stone3("Stone3Fine", scale=0.25)
        self.stone_plain = stone3("Stone3Plain", blocks=False)
        self.marble = marble("Marble")
        self.silver = metal("Silver", (0.86, 0.87, 0.9), rough=0.28)
        self.gold = metal("Gold", (0.95, 0.68, 0.3), rough=0.3)
        self.bronze = metal("Bronze", (0.62, 0.38, 0.18), rough=0.38)
        self.tin = metal("Tin", (0.72, 0.73, 0.72), rough=0.42)
        self.orichalcum = metal("Orichalcum", (0.88, 0.42, 0.22), rough=0.32)
        self.roof_tiles = tiles("RoofTiles")
        self.house_wall = house("HouseWall")
        self.house_wall2 = house("HouseWall2", (0.7, 0.6, 0.5))
        self.ground = ground("Ground")
        self.ground_city = leaves("GardenGround", (0.2, 0.2, 0.09))
        self.paper = leaves("PaperBack", (0.75, 0.66, 0.48))
        self.sand = stone3("Sand", blocks=False)
        self.forest = forest("Forest")
        self.olive = leaves("Olive", (0.16, 0.26, 0.09))
        self.cypress = leaves("Cypress", (0.06, 0.12, 0.05))
        self.bark = metal("Bark", (0.1, 0.08, 0.06), rough=0.9)
        self.bark.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.0
        self.sea = water("Sea")
        self.ring_water = water("RingWater", glow_name="ring_glow")
        self.wire = wire("Wire")
        self.wire_temple = wire("WireTemple", strength=4.0)
        self.parchment = parchment("Parchment", os.path.join(tex_dir, "parchment.png"), os.path.join(tex_dir, "ink_mask.png"))
        self.fire = emission("Fire", (1.0, 0.45, 0.12), 40.0, anim_name="fires")
        self.beacon = emission("Beacon", (1.0, 0.75, 0.4), 80.0, anim_name="beacon")
        self.wax = metal("Wax", (0.45, 0.04, 0.03), rough=0.35)
        self.wax.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.0
        self.wood = metal("Wood", (0.22, 0.13, 0.07), rough=0.7)
        self.wood.node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.0
        self.sail = leaves("Sail", (0.75, 0.68, 0.55))
        self.title = fadeable(emission("TitleInk", (1.0, 0.86, 0.6), 4.0))
        self.black = emission("Black", (0, 0, 0), 0.0)
        for mat in (self.ground, self.forest, self.olive, self.cypress, self.house_wall, self.house_wall2, self.roof_tiles,
                    self.stone, self.stone_fine, self.stone_plain, self.ground_city, self.sand, self.bronze, self.tin):
            haze(mat)
        haze(self.sea, distance=40000.0)
        haze(self.ring_water, distance=40000.0)
