import bpy
import json
import math
import os
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = os.path.abspath(ARGS[ARGS.index("--out") + 1]) if "--out" in ARGS else os.path.abspath("out")


def principled(mat):
    return mat.node_tree.nodes.get("Principled BSDF") if mat and mat.use_nodes else None


def set_base(mat_name, rgba, rough=None):
    mat = bpy.data.materials.get(mat_name)
    bsdf = principled(mat)
    if not bsdf:
        return
    if bsdf.inputs.get("Base Color"):
        bsdf.inputs["Base Color"].default_value = rgba
    if rough is not None and bsdf.inputs.get("Roughness"):
        bsdf.inputs["Roughness"].default_value = rough


def reshape_body():
    obj = bpy.data.objects["Rat_Body_Skinned"]
    # Sculpt-like proportional correction in the neutral bind mesh.
    # Head becomes less spherical, muzzle projects forward, torso becomes leaner.
    for v in obj.data.vertices:
        co = v.co
        if co.z > 2.55:
            pivot = Vector((0.0, -0.03, 2.96))
            d = co - pivot
            d.x *= 0.93
            d.y *= 1.09
            d.z *= 0.97
            if co.y < -0.30:
                d.y *= 1.14
                d.x *= 0.92
            co[:] = pivot + d
        elif 1.60 < co.z < 2.52:
            co.x *= 0.91
            co.y *= 0.95
        elif co.z < 1.58:
            co.x *= 0.94
    obj.data.update()


def reshape_clothing():
    hoodie = bpy.data.objects.get("Hoodie_Skinned")
    if hoodie:
        for v in hoodie.data.vertices:
            co = v.co
            if 1.55 < co.z < 2.52:
                # Taper from shoulders to hem instead of a round tube.
                t = max(0.0, min(1.0, (co.z - 1.55) / 0.97))
                co.x *= 0.93 + 0.05 * t
                if co.y < -0.30:
                    co.y *= 1.035
        hoodie.data.update()
    trousers = bpy.data.objects.get("Trousers_Skinned")
    if trousers:
        for v in trousers.data.vertices:
            co = v.co
            if co.z > 1.2:
                co.x *= 0.95
            if co.z < 0.72:
                co.x *= 0.91
        trousers.data.update()


def scale_world(obj_name, factors):
    obj = bpy.data.objects.get(obj_name)
    if obj:
        obj.scale.x *= factors[0]
        obj.scale.y *= factors[1]
        obj.scale.z *= factors[2]


def move_world(obj_name, delta):
    obj = bpy.data.objects.get(obj_name)
    if obj:
        obj.location += Vector(delta)


def facial_refinement():
    # Darker rat fur + warmer translucent skin reads less like plastic.
    set_base("Fur_Grey", (0.105, 0.115, 0.135, 1.0), 0.76)
    set_base("Fur_Dark", (0.018, 0.020, 0.026, 1.0), 0.82)
    set_base("Skin_Pink", (0.67, 0.19, 0.18, 1.0), 0.58)
    set_base("Hoodie_Red", (0.28, 0.010, 0.016, 1.0), 0.86)
    set_base("Trousers_Black", (0.010, 0.012, 0.018, 1.0), 0.91)
    set_base("Shoe_Red", (0.34, 0.014, 0.020, 1.0), 0.38)

    # Ears larger/thinner; eyes slightly smaller and deeper; muzzle/nose narrower.
    for side in ("L", "R"):
        scale_world(f"Ear.{side}", (1.07, 0.72, 1.09))
        scale_world(f"InnerEar.{side}", (1.06, 0.65, 1.08))
        scale_world(f"Eye.{side}", (0.88, 0.82, 0.94))
        scale_world(f"Iris.{side}", (0.92, 0.82, 0.94))
        scale_world(f"Pupil.{side}", (0.94, 0.82, 0.96))
        move_world(f"Eye.{side}", (0, 0.035, 0.015))
        move_world(f"Iris.{side}", (0, 0.035, 0.015))
        move_world(f"Pupil.{side}", (0, 0.035, 0.015))
    scale_world("Nose", (0.82, 1.02, 0.82))
    move_world("Nose", (0, -0.035, 0.015))
    scale_world("LowerJaw", (0.92, 1.05, 0.86))
    scale_world("Tongue", (0.88, 1.0, 0.75))

    # Less blocky wardrobe/accessories.
    scale_world("Hoodie_Pocket", (0.92, 0.72, 0.80))
    scale_world("Pendant_R", (0.82, 0.76, 0.92))
    for side in ("L", "R"):
        scale_world(f"ShoeUpper.{side}", (0.96, 0.94, 0.89))
        scale_world(f"ShoeSole.{side}", (0.98, 0.94, 0.88))
        scale_world(f"ShoeTongue.{side}", (0.88, 0.90, 0.90))


def add_eyelids():
    fur = bpy.data.materials.get("Fur_Dark")
    arm = bpy.data.objects.get("RatProductionRig")
    for side, sx in (("L", 0.22), ("R", -0.22)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(sx, -0.626, 3.185))
        lid = bpy.context.object
        lid.name = f"UpperLid.{side}"
        lid.scale = (0.175, 0.028, 0.080)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        lid.data.materials.append(fur)
        world = lid.matrix_world.copy()
        lid.parent = arm
        lid.parent_type = "BONE"
        lid.parent_bone = "head"
        lid.matrix_world = world
        for p in lid.data.polygons:
            p.use_smooth = True


def add_fur_breakup():
    # A small number of directional tufts breaks the perfect spherical silhouette
    # without shipping hundreds of thousands of hair strands in the web GLB.
    arm = bpy.data.objects.get("RatProductionRig")
    mat = bpy.data.materials.get("Fur_Dark")
    specs = [
        (-0.20, -0.02, 3.47, -0.27, -0.03, 3.63),
        (-0.10, -0.03, 3.51, -0.13, -0.04, 3.70),
        (0.00, -0.03, 3.52, 0.02, -0.04, 3.72),
        (0.11, -0.03, 3.50, 0.16, -0.04, 3.67),
        (0.21, -0.02, 3.46, 0.29, -0.03, 3.61),
    ]
    for i, s in enumerate(specs):
        curve = bpy.data.curves.new(f"FurTuftRefined.{i}", "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = 0.018
        curve.bevel_resolution = 2
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(1)
        for p, co in zip(spline.bezier_points, ((s[0],s[1],s[2]),(s[3],s[4],s[5]))):
            p.co = co
            p.handle_left_type = "AUTO"
            p.handle_right_type = "AUTO"
        obj = bpy.data.objects.new(f"FurTuftRefined.{i}", curve)
        bpy.context.collection.objects.link(obj)
        obj.data.materials.append(mat)
        world = obj.matrix_world.copy()
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = "head"
        obj.matrix_world = world


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (0,0,0)
        pb.location = (0,0,0)
        pb.scale = (1,1,1)


def set_hero_pose(arm):
    reset_pose(arm)
    # Deliberately subtle; this is a character QA pose, not dance animation.
    arm.pose.bones["head"].rotation_euler.z = math.radians(-5)
    arm.pose.bones["head"].rotation_euler.x = math.radians(3)
    arm.pose.bones["upper_arm.L"].rotation_euler.y = math.radians(-18)
    arm.pose.bones["upper_arm.R"].rotation_euler.y = math.radians(15)
    arm.pose.bones["forearm.L"].rotation_euler.y = math.radians(-12)
    arm.pose.bones["forearm.R"].rotation_euler.y = math.radians(10)
    arm.pose.bones["tail.02"].rotation_euler.z = math.radians(10)
    arm.pose.bones["tail.03"].rotation_euler.z = math.radians(12)
    bpy.context.view_layer.update()


def look_at(cam, target):
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()


def render_refined_views():
    scene = bpy.context.scene
    cam = scene.camera
    arm = bpy.data.objects["RatProductionRig"]
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"

    # Re-render neutral views after sculpt correction.
    reset_pose(arm)
    views = {
        "front": ((0,-7.2,2.65),(0,0,1.85),58),
        "three-quarter": ((4.7,-5.4,2.75),(0,0,1.85),58),
        "side": ((7.1,-0.2,2.65),(0,0,1.85),58),
        "back": ((0,7.1,2.7),(0,0,1.85),58),
        "face": ((0,-4.2,3.15),(0,-0.10,3.02),72),
    }
    for name,(loc,target,lens) in views.items():
        cam.location = loc
        cam.data.lens = lens
        look_at(cam,target)
        scene.render.filepath = os.path.join(out_dir,f"rat-{name}.png")
        bpy.ops.render.render(write_still=True)

    set_hero_pose(arm)
    cam.location = (4.3,-5.5,2.75)
    cam.data.lens = 62
    look_at(cam,(0,-0.05,1.95))
    scene.render.filepath = os.path.join(out_dir,"rat-hero.png")
    bpy.ops.render.render(write_still=True)
    reset_pose(arm)


def update_manifest_and_export():
    arm = bpy.data.objects["RatProductionRig"]
    path = os.path.join(out_dir,"rat-production-manifest.json")
    data = json.load(open(path))
    data["refinement_pass"] = 2
    data["visual_changes"] = [
        "leaner torso and corrected head silhouette",
        "projected narrower muzzle and nose",
        "larger thinner ears",
        "smaller inset eyes and upper eyelids",
        "darker fur and richer cloth/leather materials",
        "less blocky hoodie pocket, pendant and sneakers",
        "additional head fur silhouette breakup",
        "neutral and hero QA renders",
    ]
    data["quality_gate"]["hero_qa_render"] = "rat-hero.png"
    json.dump(data, open(path,"w"), indent=2)

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"rat-production.blend"))
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(out_dir,"rat-production.glb"),
        export_format="GLB",
        export_skins=True,
        export_animations=False,
        export_morph=True,
        export_yup=True,
        export_apply=False,
        export_lights=False,
        export_cameras=False,
        export_influence_nb=4,
    )


def main():
    reshape_body()
    reshape_clothing()
    facial_refinement()
    add_eyelids()
    add_fur_breakup()
    update_manifest_and_export()
    render_refined_views()
    # Re-save after pose reset so the editable source opens in neutral bind pose.
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir,"rat-production.blend"))
    print("RAT_REFINEMENT_COMPLETE=" + out_dir)


if __name__ == "__main__":
    main()
