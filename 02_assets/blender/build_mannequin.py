# 規模感を伝えるための、身長160cmのローポリのマネキンを .blend に追加して、GLB も書き出す。
# .blend は作り直さない（「Props」コレクションの mannequin だけを作り直す）ので、具材の手直しは消えない。
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b 02_assets/blender/build-burger-ingredients.blend -P 02_assets/blender/build_mannequin.py
#
# 単位: 1 Blender単位 = 1cm。足元が原点、正面は -Y（glTFでは +Z）

import bpy
import bmesh
import os
from mathutils import Matrix

here = os.path.dirname(os.path.abspath(__file__))
NAME = "mannequin"

props = bpy.data.collections.get("Props")
if props is None:
    props = bpy.data.collections.new("Props")
    bpy.context.scene.collection.children.link(props)
old = bpy.data.collections.get(NAME)
if old:
    for ob in list(old.objects):
        bpy.data.objects.remove(ob)
    bpy.data.collections.remove(old)

col = bpy.data.collections.new(NAME)
props.children.link(col)
col["stack_height"] = 160.0  # 身長
root = bpy.data.objects.new(f"{NAME}_root", None)
root.location = (-30, 0, 0)  # .blend の中では具材の左に立たせる
col.objects.link(root)

bm = bmesh.new()


def T(x, y, z):
    return Matrix.Translation((x, y, z))


def S(x, y, z):
    return Matrix.Diagonal((x, y, z, 1))


def limb(x, z0, z1, r0, r1, y=0.0, seg=8):
    """z0→z1 の、先細りの円柱（r0 が下、r1 が上）"""
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1,
                          depth=z1 - z0, matrix=T(x, y, (z0 + z1) / 2))


def ball(x, y, z, sx, sy, sz, u=10, v=6):
    bmesh.ops.create_uvsphere(bm, u_segments=u, v_segments=v, radius=1, matrix=T(x, y, z) @ S(sx, sy, sz))


for side in (-1, 1):
    bmesh.ops.create_cube(bm, size=1, matrix=T(side * 9, -5, 3) @ S(9, 24, 6))  # 足
    limb(side * 9, 5, 46, 4.5, 6.5)  # すね
    ball(side * 9, 0, 47, 6.5, 6.5, 6.5, 8, 5)  # ひざ
    limb(side * 9, 47, 84, 6.5, 9)  # もも
    ball(side * 20.5, 0, 127, 6.5, 6.5, 6.5, 8, 5)  # 肩
    limb(side * 22, 100, 127, 4, 5.2)  # 上腕
    limb(side * 23, 75, 100, 3.3, 4)  # 前腕
    ball(side * 23, 0, 70, 3.8, 2.5, 6, 8, 5)  # 手
ball(0, 0, 88, 17, 11, 10)  # 腰
bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=14, radius2=19, depth=44,
                      matrix=T(0, 0, 112) @ S(1, 0.55, 1))  # 胴
limb(0, 132, 142, 5, 4.5)  # 首
ball(0, 0, 147.8, 9.5, 10.5, 12.2)  # 頭（てっぺんが160cm）

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new(NAME)
bm.to_mesh(me)
bm.free()
mat = bpy.data.materials.get("mannequin") or bpy.data.materials.new("mannequin")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = (0.75, 0.75, 0.73, 1)
bsdf.inputs["Roughness"].default_value = 0.6
me.materials.append(mat)
ob = bpy.data.objects.new(NAME, me)
col.objects.link(ob)
ob.parent = root

bpy.ops.wm.save_mainfile()
exec(open(os.path.join(here, "export_glb.py")).read())
