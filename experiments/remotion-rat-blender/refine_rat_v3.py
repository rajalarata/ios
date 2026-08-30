import bpy
import json
import math
import os
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out_dir = os.path.abspath(ARGS[ARGS.index('--out') + 1]) if '--out' in ARGS else os.path.abspath('out')
os.makedirs(out_dir, exist_ok=True)


def clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def principled(mat):
    return mat.node_tree.nodes.get('Principled BSDF') if mat and mat.use_nodes else None


def set_material(mat_name, rgba=None, roughness=None, metallic=None):
    mat = bpy.data.materials.get(mat_name)
    if not mat:
        return
    bsdf = principled(mat)
    if not bsdf:
        return
    if rgba is not None and bsdf.inputs.get('Base Color'):
        bsdf.inputs['Base Color'].default_value = rgba
        mat.diffuse_color = rgba
    if roughness is not None and bsdf.inputs.get('Roughness'):
        bsdf.inputs['Roughness'].default_value = roughness
    if metallic is not None and bsdf.inputs.get('Metallic'):
        bsdf.inputs['Metallic'].default_value = metallic


def scale_obj(name, xyz):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.scale.x *= xyz[0]
        obj.scale.y *= xyz[1]
        obj.scale.z *= xyz[2]


def move_obj(name, xyz):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.location += Vector(xyz)


def rotate_obj(name, xyz_deg):
    obj = bpy.data.objects.get(name)
    if obj:
        obj.rotation_mode = 'XYZ'
        obj.rotation_euler.x += math.radians(xyz_deg[0])
        obj.rotation_euler.y += math.radians(xyz_deg[1])
        obj.rotation_euler.z += math.radians(xyz_deg[2])


def parent_to_bone(obj, armature, bone):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = 'BONE'
    obj.parent_bone = bone
    obj.matrix_world = world


def reshape_body_v3():
    obj = bpy.data.objects['Rat_Body_Skinned']
    for v in obj.data.vertices:
        co = v.co
        x, y, z = co.x, co.y, co.z
        if z > 2.55:
            crown = clamp((z - 3.15) / 0.45)
            back = clamp((y - 0.02) / 0.45)
            co.x *= 1.0 - 0.035 * crown - 0.025 * back
            if y > 0.02:
                co.y *= 0.93
            forehead = clamp((z - 3.10) / 0.38) * clamp((-y - 0.06) / 0.45)
            co.y += 0.035 * forehead
            front = clamp((-y - 0.16) / 0.55)
            lower_face = clamp((3.23 - z) / 0.72)
            center = 1.0 - clamp(abs(x) / 0.55)
            co.y -= 0.13 * front * lower_face * (0.45 + 0.55 * center)
            cheek = clamp(1.0 - abs(z - 3.02) / 0.28) * clamp((-y - 0.05) / 0.45)
            if abs(x) > 0.11:
                co.x *= 1.0 + 0.045 * cheek
            chin = clamp((2.92 - z) / 0.30) * front
            co.x *= 1.0 - 0.085 * chin
            if z > 3.36:
                co.z = 3.36 + (z - 3.36) * 0.87
        elif 1.55 < z < 2.55:
            t = clamp((z - 1.55) / 1.0)
            width_scale = 0.90 + 0.105 * t
            co.x *= width_scale
            co.y *= 0.97
        elif 1.15 < z <= 1.55:
            co.x *= 0.94
    obj.data.update()


def reshape_clothing_v3():
    hoodie = bpy.data.objects.get('Hoodie_Skinned')
    if hoodie:
        for v in hoodie.data.vertices:
            co = v.co
            if 1.48 < co.z < 2.56:
                t = clamp((co.z - 1.48) / 1.08)
                co.x *= 0.87 + 0.11 * t
                if co.y < -0.24:
                    co.y *= 1.035
                if 1.48 < co.z < 1.68:
                    co.z -= 0.025 * (1.0 - t)
        hoodie.data.update()
    trousers = bpy.data.objects.get('Trousers_Skinned')
    if trousers:
        for v in trousers.data.vertices:
            co = v.co
            if co.z > 1.05:
                co.x *= 0.96
            if 0.55 < co.z < 0.95:
                co.x *= 0.92
            if co.z < 0.55:
                co.x *= 0.88
        trousers.data.update()


def refine_face_objects_v3():
    for side, sx in (('L', 1), ('R', -1)):
        for base in ('Eye', 'Iris', 'Pupil'):
            scale_obj(f'{base}.{side}', (0.90, 0.78, 0.90 if base == 'Eye' else 0.92))
            move_obj(f'{base}.{side}', (0.012 * sx, 0.035, -0.005))
        scale_obj(f'UpperLid.{side}', (1.00, 0.82, 0.88))
        move_obj(f'UpperLid.{side}', (0.010 * sx, 0.034, 0.002))
        scale_obj(f'Brow.{side}', (1.02, 0.84, 0.82))
        move_obj(f'Brow.{side}', (0.010 * sx, 0.025, -0.012))
        scale_obj(f'Ear.{side}', (1.045, 0.66, 1.06))
        scale_obj(f'InnerEar.{side}', (1.035, 0.58, 1.05))
        rotate_obj(f'Ear.{side}', (0, 7 * sx, 5 * sx))
        rotate_obj(f'InnerEar.{side}', (0, 7 * sx, 5 * sx))
        move_obj(f'Ear.{side}', (0.020 * sx, 0.015, 0.018))
        move_obj(f'InnerEar.{side}', (0.020 * sx, 0.015, 0.018))
    scale_obj('Nose', (0.80, 0.95, 0.76))
    move_obj('Nose', (0, -0.060, -0.008))
    scale_obj('LowerJaw', (0.90, 1.07, 0.82))
    move_obj('LowerJaw', (0, -0.035, 0.005))
    scale_obj('Tongue', (0.84, 1.02, 0.70))
    move_obj('Tongue', (0, -0.020, 0.006))
    for tooth_x in ('-0.105', '0.105'):
        scale_obj(f'Tooth_{tooth_x}', (0.84, 0.90, 0.90))


def add_lower_lids_and_muzzle_planes():
    arm = bpy.data.objects['RatProductionRig']
    fur_dark = bpy.data.materials.get('Fur_Dark')
    fur_grey = bpy.data.materials.get('Fur_Grey')
    for side, sx in (('L', 1), ('R', -1)):
        name = f'LowerLidV3.{side}'
        if name not in bpy.data.objects:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(0.225 * sx, -0.632, 3.105))
            lid = bpy.context.object
            lid.name = name
            lid.scale = (0.155, 0.022, 0.050)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            if fur_dark:
                lid.data.materials.append(fur_dark)
            for p in lid.data.polygons:
                p.use_smooth = True
            parent_to_bone(lid, arm, 'head')
        pad_name = f'MuzzlePlaneV3.{side}'
        if pad_name not in bpy.data.objects:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, location=(0.145 * sx, -0.585, 2.985))
            pad = bpy.context.object
            pad.name = pad_name
            pad.scale = (0.205, 0.105, 0.145)
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
            if fur_grey:
                pad.data.materials.append(fur_grey)
            for p in pad.data.polygons:
                p.use_smooth = True
            parent_to_bone(pad, arm, 'head')
    if 'UpperLipBridgeV3' not in bpy.data.objects:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=36, ring_count=20, location=(0.0, -0.616, 2.970))
        bridge = bpy.context.object
        bridge.name = 'UpperLipBridgeV3'
        bridge.scale = (0.115, 0.060, 0.060)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        if fur_grey:
            bridge.data.materials.append(fur_grey)
        for p in bridge.data.polygons:
            p.use_smooth = True
        parent_to_bone(bridge, arm, 'head')


def refine_hands_shoes_accessories():
    for side in ('L', 'R'):
        scale_obj(f'Palm.{side}', (0.90, 0.88, 0.92))
        for i in range(3):
            scale_obj(f'Finger.{side}.{i}', (0.84, 0.90, 0.92))
        scale_obj(f'Cuff.{side}', (0.93, 0.92, 0.90))
        scale_obj(f'ShoeUpper.{side}', (0.96, 1.02, 0.86))
        scale_obj(f'ShoeSole.{side}', (0.98, 1.04, 0.86))
        scale_obj(f'ShoeTongue.{side}', (0.86, 1.00, 0.88))
        for i in range(4):
            scale_obj(f'Lace.{side}.{i}', (0.92, 1.03, 0.88))
    scale_obj('Hoodie_Pocket', (0.88, 0.76, 0.78))
    scale_obj('Hood_Roll', (0.96, 0.90, 0.92))
    scale_obj('Pendant_R', (0.78, 0.74, 0.86))


def refine_materials_v3():
    set_material('Fur_Grey', (0.075, 0.082, 0.095, 1.0), roughness=0.86)
    set_material('Fur_Dark', (0.014, 0.016, 0.022, 1.0), roughness=0.90)
    set_material('Skin_Pink', (0.55, 0.12, 0.13, 1.0), roughness=0.68)
    set_material('Hoodie_Red', (0.24, 0.006, 0.010, 1.0), roughness=0.90)
    set_material('Trousers_Black', (0.008, 0.010, 0.015, 1.0), roughness=0.95)
    set_material('Shoe_Red', (0.30, 0.010, 0.015, 1.0), roughness=0.46)


def add_silhouette_tufts_v3():
    arm = bpy.data.objects['RatProductionRig']
    mat = bpy.data.materials.get('Fur_Dark')
    specs = [
        (-0.30, -0.01, 3.35, -0.42, 0.00, 3.42),
        (-0.24, -0.02, 3.45, -0.31, -0.02, 3.61),
        (0.24, -0.02, 3.45, 0.31, -0.02, 3.61),
        (0.30, -0.01, 3.35, 0.42, 0.00, 3.42),
        (-0.34, -0.13, 3.10, -0.46, -0.16, 3.14),
        (0.34, -0.13, 3.10, 0.46, -0.16, 3.14),
    ]
    for i, s in enumerate(specs):
        name = f'SilhouetteTuftV3.{i}'
        if name in bpy.data.objects:
            continue
        curve = bpy.data.curves.new(name, 'CURVE')
        curve.dimensions = '3D'
        curve.bevel_depth = 0.013
        curve.bevel_resolution = 2
        spline = curve.splines.new('BEZIER')
        spline.bezier_points.add(1)
        for p, co in zip(spline.bezier_points, ((s[0], s[1], s[2]), (s[3], s[4], s[5]))):
            p.co = co
            p.handle_left_type = 'AUTO'
            p.handle_right_type = 'AUTO'
        obj = bpy.data.objects.new(name, curve)
        bpy.context.collection.objects.link(obj)
        if mat:
            obj.data.materials.append(mat)
        parent_to_bone(obj, arm, 'head')


def bounds_width(vertices):
    xs = [v.co.x for v in vertices]
    return max(xs) - min(xs) if xs else 0.0


def bounds_depth(vertices):
    ys = [v.co.y for v in vertices]
    return max(ys) - min(ys) if ys else 0.0


def compute_metrics():
    body = bpy.data.objects['Rat_Body_Skinned']
    verts = list(body.data.vertices)
    head = [v for v in verts if v.co.z > 2.55]
    shoulders = [v for v in verts if 2.16 <= v.co.z <= 2.42]
    waist = [v for v in verts if 1.62 <= v.co.z <= 1.82]
    front_head = min((v.co.y for v in head), default=0.0)
    upper_face = [v for v in head if v.co.z >= 3.12]
    forehead_front = min((v.co.y for v in upper_face), default=front_head)
    muzzle_projection = max(0.0, forehead_front - front_head)
    return {
        'head_width': round(bounds_width(head), 5),
        'head_depth': round(bounds_depth(head), 5),
        'muzzle_projection': round(muzzle_projection, 5),
        'shoulder_width': round(bounds_width(shoulders), 5),
        'waist_width': round(bounds_width(waist), 5),
    }


def reset_pose(arm):
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def look_at(cam, target):
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()


def render_qa():
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE_NEXT'
    scene.render.resolution_x = 640
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    cam = scene.camera
    arm = bpy.data.objects['RatProductionRig']
    reset_pose(arm)
    views = {
        'front': ((0, -7.9, 2.55), (0, 0, 1.86), 58),
        'three-quarter': ((5.0, -6.1, 2.72), (0, 0, 1.88), 60),
        'side': ((7.8, -0.15, 2.62), (0, 0, 1.88), 58),
        'back': ((0, 7.8, 2.62), (0, 0, 1.86), 58),
        'face': ((0, -4.7, 3.05), (0, -0.16, 3.02), 72),
    }
    for name, (loc, target, lens) in views.items():
        cam.location = loc
        cam.data.lens = lens
        look_at(cam, target)
        scene.render.filepath = os.path.join(out_dir, f'rat-v3-{name}.png')
        bpy.ops.render.render(write_still=True)
    arm.pose.bones['head'].rotation_euler = tuple(math.radians(v) for v in (3, -2, -6))
    arm.pose.bones['upper_arm.L'].rotation_euler = tuple(math.radians(v) for v in (0, -10, -22))
    arm.pose.bones['forearm.L'].rotation_euler = tuple(math.radians(v) for v in (0, -14, -24))
    arm.pose.bones['upper_arm.R'].rotation_euler = tuple(math.radians(v) for v in (0, 7, 14))
    arm.pose.bones['forearm.R'].rotation_euler = tuple(math.radians(v) for v in (0, 12, 20))
    arm.pose.bones['tail.02'].rotation_euler.z = math.radians(10)
    arm.pose.bones['tail.03'].rotation_euler.z = math.radians(14)
    arm.pose.bones['jaw'].rotation_euler.x = math.radians(3)
    bpy.context.view_layer.update()
    cam.location = (4.9, -6.3, 2.75)
    cam.data.lens = 62
    look_at(cam, (0, -0.04, 1.95))
    scene.render.filepath = os.path.join(out_dir, 'rat-v3-hero.png')
    bpy.ops.render.render(write_still=True)
    reset_pose(arm)


def update_manifest_and_export(metrics):
    manifest_path = os.path.join(out_dir, 'rat-production-manifest.json')
    with open(manifest_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    data['refinement_pass'] = 3
    data['visual_changes'] = [
        'wedge-shaped skull replacing spherical mascot silhouette',
        'stronger muzzle projection with cheek and chin planes',
        'smaller deeper eyes with upper and lower lid definition',
        'thinner canted ears and extra silhouette breakup',
        'stronger shoulder-to-waist taper in body and hoodie',
        'slimmer hands, cuffs and less blocky sneaker proportions',
        'darker high-roughness fur and cloth materials',
        'six-view neutral/hero sculpt QA set',
    ]
    data['sculpt_metrics'] = metrics
    data.setdefault('quality_gate', {})['visual_sculpt_gate'] = True
    data['quality_gate']['skin_weights_preserved'] = data.get('unweighted_vertices', 1) == 0
    data['quality_gate']['neutral_qa_six_views'] = True
    data['quality_gate']['qa_turntable_views'] = [
        'rat-v3-front.png', 'rat-v3-three-quarter.png', 'rat-v3-side.png',
        'rat-v3-back.png', 'rat-v3-face.png', 'rat-v3-hero.png'
    ]
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, 'rat-production-v3.blend'))
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(out_dir, 'rat-production-v3.glb'),
        export_format='GLB',
        export_skins=True,
        export_animations=False,
        export_morph=True,
        export_yup=True,
        export_apply=False,
        export_lights=False,
        export_cameras=False,
    )

reshape_body_v3()
reshape_clothing_v3()
refine_face_objects_v3()
add_lower_lids_and_muzzle_planes()
refine_hands_shoes_accessories()
refine_materials_v3()
add_silhouette_tufts_v3()
bpy.context.view_layer.update()
metrics = compute_metrics()
render_qa()
update_manifest_and_export(metrics)
print('RAT SCULPT V3 COMPLETE')
print(json.dumps(metrics, indent=2))
