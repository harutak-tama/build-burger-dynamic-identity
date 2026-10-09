# build-burger-ingredients.blend の具材を、1つずつ GLB に書き出す。
# .blend を手で編集したあとは、これを実行するだけで、アプリに反映される。
#
#   /Applications/Blender.app/Contents/MacOS/Blender -b 02_assets/blender/build-burger-ingredients.blend -P 02_assets/blender/export_glb.py
#
# 約束（アプリ 03_work/web/main.js と共有）
# - 具材は「Ingredients」、マネキンなどは「Props」コレクションの下の子コレクション1つ＝GLB 1つ。コレクション名がファイル名になる
# - 各コレクションには、空のオブジェクト「<名前>_root」が1つあり、ほかのオブジェクトはその子
#   （.blend の中では、見やすいように root を横に並べてある。書き出すときだけ原点に戻す）
# - 単位: 1 Blender単位 = 1cm。原点は底面の中心、上が +Z（glTFでは +Y になる）
# - コレクションのカスタムプロパティ「stack_height」が、積むときの厚み。models.json に書き出す
#   （高さを変えるモデリングをしたら、ここも合わせて変える）

import bpy
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
out_dir = os.path.normpath(os.path.join(here, "..", "models"))
os.makedirs(out_dir, exist_ok=True)


def export_all():
    # 具材（Ingredients）と、マネキンなどの小道具（Props）
    cols = [c for g in ("Ingredients", "Props") if g in bpy.data.collections for c in bpy.data.collections[g].children]
    manifest = {}
    for col in cols:
        name = col.name
        root = bpy.data.objects[f"{name}_root"]
        saved = root.location.copy()
        root.location = (0, 0, 0)
        bpy.context.view_layer.update()

        bpy.ops.object.select_all(action="DESELECT")
        for ob in col.all_objects:
            ob.hide_set(False)
            ob.select_set(True)
        path = os.path.join(out_dir, f"{name}.glb")
        bpy.ops.export_scene.gltf(
            filepath=path,
            export_format="GLB",
            use_selection=True,
            export_apply=True,
            export_yup=True,
            export_normals=True,
            export_vertex_color="ACTIVE",
            export_materials="EXPORT",
        )
        root.location = saved
        manifest[name] = {"file": f"{name}.glb", "stackHeight": round(float(col.get("stack_height", 0)), 4)}
        print(f"exported {path}")

    with open(os.path.join(out_dir, "models.json"), "w") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")
    bpy.context.view_layer.update()


export_all()
