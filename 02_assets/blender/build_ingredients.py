# 具材のローポリ代替モデルを作って build-burger-ingredients.blend に保存し、GLB も書き出す。
# 最初の1回だけ使う（.blend を作り直すと、手で編集した内容は消える）。編集後の書き出しは export_glb.py。
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b -P 02_assets/blender/build_ingredients.py

import bpy
import bmesh
import math
import os
import random
from mathutils import Matrix, Vector

here = os.path.dirname(os.path.abspath(__file__))
R = 5.0  # 半径cm（1 Blender単位 = 1cm）

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
ingredients = bpy.data.collections.new("Ingredients")
scene.collection.children.link(ingredients)


def srgb(r, g, b):
    return tuple((c / 255) ** 2.2 for c in (r, g, b)) + (1.0,)


def material(name, rgb, rough=0.7):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = srgb(*rgb)
    bsdf.inputs["Roughness"].default_value = rough
    m.diffuse_color = srgb(*rgb)
    return m


def lathe(bm, profile, seg, radial=lambda th, i: 1.0):
    """profile: [(r, z), ...] 下から上。半径0の点は中心1点にまとめる"""
    rows = []
    for i, (r, z) in enumerate(profile):
        if r == 0:
            rows.append([bm.verts.new((0, 0, z))] * seg)
        else:
            rows.append([bm.verts.new((math.cos(t) * r * radial(t, i), math.sin(t) * r * radial(t, i), z))
                         for t in (j / seg * math.tau for j in range(seg))])
    for a, b in zip(rows, rows[1:]):
        for j in range(seg):
            vs = [a[j], a[(j + 1) % seg], b[(j + 1) % seg], b[j]]
            uniq = list(dict.fromkeys(vs))
            if len(uniq) >= 3:
                bm.faces.new(uniq)


def new_ingredient(name, index, stack_height):
    col = bpy.data.collections.new(name)
    ingredients.children.link(col)
    col["stack_height"] = stack_height
    root = bpy.data.objects.new(f"{name}_root", None)
    root.location = (index * 14, 0, 0)  # .blend の中では横に並べる（書き出し時は原点に戻す）
    col.objects.link(root)
    return col, root


def add_mesh(col, root, name, bm, mat, smooth=True):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        me.shade_smooth()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    ob.parent = root
    return ob


def wobble(seed, amp, n=3):
    rnd = random.Random(seed)
    terms = [(k + 2, (rnd.random() - 0.5) * amp / (k + 1), rnd.random() * math.tau) for k in range(n)]
    return lambda th: 1 + sum(a * math.sin(k * th + p) for k, a, p in terms)


# ---- バンズ（下） ----
col, root = new_ingredient("bun-bottom", 0, 2.0)
bm = bmesh.new()
lathe(bm, [(0, 0), (R * 0.92, 0), (R, 0.6), (R, 1.5), (R * 0.9, 2.0), (0, 2.0)], 20)
add_mesh(col, root, "bun-bottom", bm, material("bun-crust", (200, 130, 60)))
bm = bmesh.new()  # 切り口（白いクラム）を少し浮かせて重ねる
lathe(bm, [(R * 0.88, 2.001), (0, 2.001)], 20)
add_mesh(col, root, "bun-bottom-crumb", bm, material("bun-crumb", (238, 214, 160), 0.9))

# ---- バンズ（上） ----
col, root = new_ingredient("bun-top", 1, 4.2)
bm = bmesh.new()
dome = [(R * math.cos(a), 0.4 + 3.8 * math.sin(a)) for a in (k / 6 * math.pi / 2 for k in range(7))]
dome[-1] = (0, 4.2)
lathe(bm, [(R * 0.95, 0.0), (R, 0.4)] + dome[1:], 20, lambda th, i: wobble(12, 0.05)(th))
add_mesh(col, root, "bun-top", bm, material("bun-top-crust", (190, 105, 40)))
bm = bmesh.new()
lathe(bm, [(0, -0.001), (R * 0.93, -0.001)], 20)
add_mesh(col, root, "bun-top-crumb", bm, bpy.data.materials["bun-crumb"])
bm = bmesh.new()
rnd = random.Random(13)
for _ in range(36):  # ごま
    th, a = rnd.random() * math.tau, math.acos(1 - rnd.random() * 0.8)
    n = Vector((math.sin(a) * math.cos(th), math.sin(a) * math.sin(th), math.cos(a)))
    p = Vector((n.x * R, n.y * R, 0.4 + 3.8 * n.z))
    rot = n.to_track_quat("Z", "Y").to_matrix().to_4x4() @ Matrix.Rotation(rnd.random() * math.pi, 4, "Z")
    m = Matrix.Translation(p) @ rot @ Matrix.Diagonal((0.28, 0.14, 0.07, 1))
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=1, matrix=m)
add_mesh(col, root, "sesame", bm, material("sesame", (250, 240, 205), 0.5))

# ---- パティ ----
col, root = new_ingredient("patty", 2, 1.3)
bm = bmesh.new()
lathe(bm, [(0, 0), (R * 0.98, 0), (R * 1.05, 0.4), (R * 1.05, 0.9), (R * 0.98, 1.3), (R * 0.5, 1.33), (0, 1.3)],
      18, lambda th, i: wobble(21, 0.1, 5)(th))
add_mesh(col, root, "patty", bm, material("patty", (88, 46, 26), 0.85))

# ---- スライスチーズ（縁がとろけて垂れる） ----
col, root = new_ingredient("cheese", 3, 0.2)
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=8, y_segments=8, size=4.6)
for v in bm.verts:
    over = max(0.0, math.hypot(v.co.x, v.co.y) - R * 0.95)
    v.co.z = -(over ** 1.5) * 0.55
ob = add_mesh(col, root, "cheese", bm, material("cheese", (250, 185, 35), 0.35))
mod = ob.modifiers.new("thickness", "SOLIDIFY")
mod.thickness, mod.offset = 0.2, 1

# ---- 刻み玉ねぎ（10g分） ----
col, root = new_ingredient("onion", 4, 0.45)
bm = bmesh.new()
rnd = random.Random(31)
for _ in range(60):
    r, th, s = R * 0.85 * math.sqrt(rnd.random()), rnd.random() * math.tau, 0.35 + rnd.random() * 0.25
    m = (Matrix.Translation((math.cos(th) * r, math.sin(th) * r, s * 0.3 + rnd.random() * 0.15))
         @ Matrix.Rotation(rnd.random() * math.pi, 4, "Z") @ Matrix.Diagonal((s, s, s * 0.6, 1)))
    bmesh.ops.create_cube(bm, size=1, matrix=m)
onion_mat = material("onion", (245, 228, 185), 0.3)  # 白っぽく半透明
onion_mat.node_tree.nodes["Principled BSDF"].inputs["Alpha"].default_value = 0.6
add_mesh(col, root, "onion", bm, onion_mat, smooth=False)

# ---- ソース3種（波打つ薄い円盤） ----
for k, (name, rgb, fleck) in enumerate([
    ("sauce-ketchup", (185, 20, 15), None),
    ("sauce-relish", (125, 140, 35), (55, 105, 20)),
    ("sauce-burger", (235, 145, 95), (200, 75, 40)),
]):
    col, root = new_ingredient(name, 5 + k, 0.12)
    bm = bmesh.new()
    w = wobble(41 + k, 0.35, 5)
    lathe(bm, [(0, 0), (R * 0.85, 0), (R * 0.85, 0.08), (R * 0.5, 0.13), (0, 0.13)], 24,
          lambda th, i: w(th) if i in (1, 2) else 1)
    add_mesh(col, root, name, bm, material(name, rgb, 0.25))
    if fleck:
        bm = bmesh.new()
        rnd = random.Random(50 + k)
        for _ in range(30):
            r, th = R * 0.7 * math.sqrt(rnd.random()), rnd.random() * math.tau
            m = Matrix.Translation((math.cos(th) * r, math.sin(th) * r, 0.13)) @ Matrix.Rotation(rnd.random() * 3, 4, "Z") @ Matrix.Diagonal((0.3, 0.2, 0.1, 1))
            bmesh.ops.create_cube(bm, size=1, matrix=m)
        add_mesh(col, root, f"{name}-fleck", bm, material(f"{name}-fleck", fleck, 0.4), smooth=False)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(here, "build-burger-ingredients.blend"))
exec(open(os.path.join(here, "export_glb.py")).read())
