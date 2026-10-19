# キーフレームの小道具。進行表（plan.CUES）の区間に合わせて、伸びる・現れる・消える・値を動かす。
import bpy

import mats
from util import fcurves


def _ease(obj_or_data):
    ad = obj_or_data.animation_data
    if not ad or not ad.action:
        return
    for fc in fcurves(obj_or_data):
        for k in fc.keyframe_points:
            k.interpolation = "BEZIER"
            k.easing = "AUTO"


def grow(obj, f0, f1, axis="z", hold_small=True):
    """f0 から f1 で、軸方向に 0 → 1 に伸びる（原点が足元なら地面から立ち上がる）。"""
    s1 = tuple(obj.scale)
    s0 = list(s1)
    idx = "xyz".index(axis) if axis in "xyz" else None
    if idx is None:
        s0 = [0.001, 0.001, 0.001]
    else:
        s0[idx] = 0.001
    if hold_small:
        obj.scale = s0
        obj.keyframe_insert("scale", frame=1)
        # 縮んで待っている間は描かない（平たい板が巻物の上に見えないように）
        obj.hide_render = True
        obj.keyframe_insert("hide_render", frame=1)
        obj.keyframe_insert("hide_render", frame=max(1, f0 - 1))
        obj.hide_render = False
        obj.keyframe_insert("hide_render", frame=f0)
    obj.scale = s0
    obj.keyframe_insert("scale", frame=f0)
    obj.scale = s1
    obj.keyframe_insert("scale", frame=f1)
    _ease(obj)


def shrink(obj, f0, f1):
    s = tuple(obj.scale)
    obj.keyframe_insert("scale", frame=f0)
    obj.scale = (0.001, 0.001, 0.001)
    obj.keyframe_insert("scale", frame=f1)
    obj.scale = s


def alpha(obj, keys):
    """オブジェクトの色の α（fadeable な素材で透明度になる）。keys = [(frame, a), ...]"""
    for f, a in keys:
        c = list(obj.color)
        c[3] = a
        obj.color = c
        obj.keyframe_insert("color", index=3, frame=f)
    _ease(obj)


def value(name, keys, linear=False):
    """素材の値ノード（mats.ANIM に登録したもの）を動かす。"""
    for nt, node in mats.ANIM.get(name, []):
        sock = node.outputs[0]
        for f, v in keys:
            sock.default_value = v
            sock.keyframe_insert("default_value", frame=f)
        if linear:
            for fc in fcurves(nt):
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"


def loc(obj, keys, linear=False):
    for f, p in keys:
        obj.location = p
        obj.keyframe_insert("location", frame=f)
    if linear:
        for fc in fcurves(obj):
            if fc.data_path == "location":
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"


def light_energy(light_obj, keys):
    for f, e in keys:
        light_obj.data.energy = e
        light_obj.data.keyframe_insert("energy", frame=f)


def modifier_input(obj, mod_name, ident, keys):
    mod = obj.modifiers[mod_name]
    props = getattr(mod, "properties", None)
    for f, v in keys:
        if props is not None:  # Blender 5: modifier.properties.inputs.<識別子>.value
            sock = getattr(props.inputs, ident)
            sock.value = v
            sock.keyframe_insert("value", frame=f)
        else:  # Blender 4: modifier["識別子"]
            mod[ident] = v
            obj.keyframe_insert(f'modifiers["{mod_name}"]["{ident}"]', frame=f)


def wire_twin(obj, mat, thickness, rise, fade):
    """実体と同じメッシュを光の線にした分身。rise で立ち上がり、fade で消える（実体に吸収される）。"""
    w = bpy.data.objects.new(obj.name + "_Wire", obj.data)
    bpy.context.scene.collection.objects.link(w)
    w.location, w.rotation_euler = obj.location.copy(), obj.rotation_euler.copy()
    w.scale = obj.scale.copy()
    wf = w.modifiers.new("Wire", "WIREFRAME")
    wf.thickness = thickness
    wf.use_replace = True
    wf.use_even_offset = False
    for slot in w.material_slots:  # メッシュは共有し、素材だけオブジェクト側で光の線に差し替える
        slot.link = "OBJECT"
        slot.material = mat
    w.visible_shadow = False
    w.visible_diffuse = False
    w.visible_glossy = False
    grow(w, *rise)
    alpha(w, [(1, 0.0), (rise[0], 0.0), (rise[0] + 4, 1.0), (fade[0], 1.0), (fade[1], 0.0)])
    # 消えた後も透明な線が残ると、重なった所で透過の上限を超えて黒くなる。描画から外す
    w.hide_render = False
    w.keyframe_insert("hide_render", frame=fade[1])
    w.hide_render = True
    w.keyframe_insert("hide_render", frame=fade[1] + 1)
    return w
