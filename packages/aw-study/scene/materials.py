# 素材。外部テクスチャを持たず、すべてプロシージャルで組む（キーなし・素材DLなしで再現できるように）。
# 例外は画面とポスターで、リポジトリ内のスクリーンショットを画像として貼る。
import bpy


def _new(name):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    return mat, nt, bsdf


def _tex_coord(nt, kind="Object"):
    tc = nt.nodes.new("ShaderNodeTexCoord")
    return tc.outputs[kind]


def _ramp(nt, src, stops):
    r = nt.nodes.new("ShaderNodeValToRGB")
    el = r.color_ramp.elements
    el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
    el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
    for pos, col in stops[1:-1]:
        e = el.new(pos)
        e.color = (*col, 1)
    nt.links.new(src, r.inputs["Fac"])
    return r.outputs["Color"]


def _bump(nt, bsdf, height, strength):
    b = nt.nodes.new("ShaderNodeBump")
    b.inputs["Strength"].default_value = strength
    b.inputs["Distance"].default_value = 0.002
    nt.links.new(height, b.inputs["Height"])
    nt.links.new(b.outputs["Normal"], bsdf.inputs["Normal"])


def plain(name, color, rough=0.5, metal=0.0, coat=0.0):
    mat, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    bsdf.inputs["Coat Weight"].default_value = coat
    return mat


def wood(name, light, dark, rough=0.45, scale=1.0, planks=False):
    """木目。Wave テクスチャを Noise で歪ませて年輪を出す。planks=True で床板の継ぎ目も入れる。"""
    mat, nt, bsdf = _new(name)
    co = _tex_coord(nt)
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = (scale * 0.6, scale * 8.0, scale * 0.6)
    nt.links.new(co, mapping.inputs["Vector"])
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.wave_type = "RINGS"
    wave.inputs["Scale"].default_value = 3.0
    wave.inputs["Distortion"].default_value = 6.0
    wave.inputs["Detail"].default_value = 3.0
    nt.links.new(mapping.outputs["Vector"], wave.inputs["Vector"])
    col = _ramp(nt, wave.outputs["Fac"], [(0.0, dark), (0.55, light), (1.0, dark)])
    if planks:
        brick = nt.nodes.new("ShaderNodeTexBrick")
        brick.inputs["Scale"].default_value = 1.0
        brick.inputs["Brick Width"].default_value = 1.2
        brick.inputs["Row Height"].default_value = 0.14
        brick.inputs["Mortar Size"].default_value = 0.0015
        brick.inputs["Color1"].default_value = (1, 1, 1, 1)
        brick.inputs["Color2"].default_value = (0.82, 0.8, 0.78, 1)
        brick.inputs["Mortar"].default_value = (0.1, 0.08, 0.06, 1)
        nt.links.new(_tex_coord(nt), brick.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        nt.links.new(col, mix.inputs["A"])
        nt.links.new(brick.outputs["Color"], mix.inputs["B"])
        col = mix.outputs["Result"]
        _bump(nt, bsdf, brick.outputs["Fac"], 0.15)
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def plaster(name, color):
    """漆喰の壁。ごく弱い凹凸だけ入れて、光が当たったときに面がのっぺりしないようにする。"""
    mat, nt, bsdf = _new(name)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 40.0
    noise.inputs["Detail"].default_value = 8.0
    nt.links.new(_tex_coord(nt), noise.inputs["Vector"])
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.9
    _bump(nt, bsdf, noise.outputs["Fac"], 0.05)
    return mat


def clay(name, color, rough=0.85):
    """素焼き・粘土板。角柱の模型と粘土板に使う。"""
    mat, nt, bsdf = _new(name)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 120.0
    noise.inputs["Detail"].default_value = 10.0
    nt.links.new(_tex_coord(nt), noise.inputs["Vector"])
    dark = tuple(c * 0.7 for c in color)
    col = _ramp(nt, noise.outputs["Fac"], [(0.35, dark), (0.65, color)])
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = rough
    _bump(nt, bsdf, noise.outputs["Fac"], 0.35)
    return mat


def fabric(name, color):
    """ラグ。織りの細かいノイズ＋Sheen で布らしさを出す。"""
    mat, nt, bsdf = _new(name)
    wave = nt.nodes.new("ShaderNodeTexWave")
    wave.inputs["Scale"].default_value = 300.0
    nt.links.new(_tex_coord(nt), wave.inputs["Vector"])
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 3.0
    nt.links.new(_tex_coord(nt), noise.inputs["Vector"])
    dark = tuple(c * 0.75 for c in color)
    col = _ramp(nt, noise.outputs["Fac"], [(0.3, dark), (0.7, color)])
    nt.links.new(col, bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Sheen Weight"].default_value = 0.6
    _bump(nt, bsdf, wave.outputs["Fac"], 0.3)
    return mat


def glass(name, tint=(0.95, 0.97, 0.96)):
    mat, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (*tint, 1)
    bsdf.inputs["Roughness"].default_value = 0.0
    bsdf.inputs["Transmission Weight"].default_value = 1.0
    bsdf.inputs["IOR"].default_value = 1.5
    return mat


def sheer(name, color):
    """レースのカーテン。半透明（透過＋拡散透過）で、窓の光を柔らかく散らす。"""
    mat, nt, bsdf = _new(name)
    out = nt.nodes["Material Output"]
    trans = nt.nodes.new("ShaderNodeBsdfTranslucent")
    trans.inputs["Color"].default_value = (*color, 1)
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs["Fac"].default_value = 0.45
    nt.links.new(trans.outputs[0], mix.inputs[1])
    nt.links.new(clear.outputs[0], mix.inputs[2])
    mix2 = nt.nodes.new("ShaderNodeMixShader")
    mix2.inputs["Fac"].default_value = 0.35
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    nt.links.new(mix.outputs[0], mix2.inputs[1])
    nt.links.new(bsdf.outputs[0], mix2.inputs[2])
    nt.links.new(mix2.outputs[0], out.inputs["Surface"])
    return mat


def emission(name, color, strength):
    mat, nt, bsdf = _new(name)
    bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
    bsdf.inputs["Emission Color"].default_value = (*color, 1)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def stacked_image(name, paths):
    """同じ幅の画像を上から順に縦に連結した画像を作る（画面のスクロール素材）。"""
    import numpy as np

    parts = []
    for path in paths:
        img = bpy.data.images.load(path, check_existing=True)
        w, h = img.size
        parts.append(np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4))
    # Blender の画素は下の行から並ぶので、上に来る画像を後ろに積む
    arr = np.concatenate(parts[::-1], axis=0)
    h, w = arr.shape[:2]
    out = bpy.data.images.new(name, w, h)
    out.pixels.foreach_set(arr.ravel())
    out.pack()
    return out


def image(name, path, emit=0.0, rough=0.6, scale=(1, 1), offset=(0, 0)):
    """画像を貼る素材。emit > 0 で画面（自己発光）、0 でポスター（紙）。
    Mapping ノードを "Scroll" という名前で残す。画面のスクロールはこの Location をキーで動かす。"""
    mat, nt, bsdf = _new(name)
    img = path if isinstance(path, bpy.types.Image) else bpy.data.images.load(path, check_existing=True)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.extension = "CLIP"
    uv = _tex_coord(nt, "UV")
    mapping = nt.nodes.new("ShaderNodeMapping")
    mapping.name = "Scroll"
    mapping.inputs["Scale"].default_value = (scale[0], scale[1], 1)
    mapping.inputs["Location"].default_value = (offset[0], offset[1], 0)
    nt.links.new(uv, mapping.inputs["Vector"])
    nt.links.new(mapping.outputs["Vector"], tex.inputs["Vector"])
    if emit > 0:
        bsdf.inputs["Base Color"].default_value = (0, 0, 0, 1)
        bsdf.inputs["Roughness"].default_value = 0.15
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emit
    else:
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = rough
    return mat


class Palette:
    """シーン全体で共有する素材一式。色はここだけで決める。"""

    def __init__(self):
        self.wall = plaster("Wall", (0.78, 0.74, 0.67))
        self.ceiling = plaster("Ceiling", (0.85, 0.83, 0.79))
        self.floor = wood("FloorOak", (0.42, 0.27, 0.15), (0.24, 0.14, 0.07), rough=0.5, scale=0.8, planks=True)
        self.oak = wood("Oak", (0.55, 0.37, 0.2), (0.32, 0.2, 0.1), rough=0.38)
        self.walnut = wood("Walnut", (0.26, 0.15, 0.08), (0.12, 0.06, 0.03), rough=0.4)
        self.bentwood = wood("Bentwood", (0.16, 0.09, 0.05), (0.07, 0.04, 0.02), rough=0.35, scale=3.0)
        self.aluminium = plain("Aluminium", (0.82, 0.83, 0.85), rough=0.28, metal=1.0)
        self.brass = plain("Brass", (0.78, 0.58, 0.3), rough=0.25, metal=1.0)
        self.steel_white = plain("PowderWhite", (0.86, 0.86, 0.84), rough=0.55)
        self.black_plastic = plain("BlackPlastic", (0.02, 0.02, 0.022), rough=0.35)
        self.dark_metal = plain("DarkMetal", (0.06, 0.06, 0.065), rough=0.4, metal=1.0)
        self.paper = plain("Paper", (0.86, 0.83, 0.75), rough=0.9)
        self.leather = plain("Leather", (0.25, 0.08, 0.05), rough=0.55, coat=0.2)
        self.ceramic = plain("Ceramic", (0.88, 0.86, 0.8), rough=0.15, coat=0.6)
        self.coffee = plain("Coffee", (0.05, 0.02, 0.01), rough=0.05)
        self.terracotta = clay("ClayPrism", (0.55, 0.38, 0.24))
        self.tablet = clay("ClayTablet", (0.46, 0.36, 0.27))
        self.shard = clay("Shard", (0.6, 0.3, 0.16))
        self.cork = clay("Cork", (0.58, 0.42, 0.26), rough=0.95)
        self.rug = fabric("Rug", (0.42, 0.12, 0.08))
        self.glass = glass("Glass")
        self.curtain = sheer("Sheer", (0.95, 0.93, 0.88))
        self.grass = plaster("Grass", (0.16, 0.22, 0.09))
        self.foliage = plaster("Foliage", (0.07, 0.13, 0.05))
        self.screen_text = emission("ScreenText", (1.0, 0.72, 0.35), 3.0)
        self.screen_bg = emission("ScreenBg", (0.01, 0.012, 0.016), 1.0)
        self.sticky = {
            "yellow": plain("StickyYellow", (0.95, 0.82, 0.25), rough=0.85),
            "pink": plain("StickyPink", (0.95, 0.45, 0.55), rough=0.85),
            "green": plain("StickyGreen", (0.55, 0.85, 0.5), rough=0.85),
        }
        self.book_colors = [
            plain(f"Cloth{i}", c, rough=0.75)
            for i, c in enumerate(
                [
                    (0.35, 0.08, 0.06),
                    (0.08, 0.14, 0.22),
                    (0.12, 0.2, 0.12),
                    (0.55, 0.45, 0.3),
                    (0.7, 0.66, 0.58),
                    (0.18, 0.16, 0.14),
                    (0.45, 0.25, 0.1),
                    (0.25, 0.3, 0.35),
                ]
            )
        ]
        self.gilt = plain("GiltLetters", (0.9, 0.7, 0.35), rough=0.3, metal=1.0)
