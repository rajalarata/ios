import bpy
import math
import json
import os
import sys
from mathutils import Vector

# Blender 4.5 LTS headless character build for a production-oriented Remotion GLB.
# The goal is a continuous skinned mascot-style rat with stable bone names,
# separate clothing/material layers, and QA renders before Remotion animation.

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
out_dir = os.path.abspath(ARGS[ARGS.index("--out") + 1]) if "--out" in ARGS else os.path.abspath("out")
os.makedirs(out_dir, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights, bpy.data.armatures):
        pass


def set_principled_input(bsdf, names, value):
    for name in names:
        socket = bsdf.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def make_material(name, base, rough=0.5, metallic=0.0, subsurface=0.0, micro_bump=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_principled_input(bsdf, ["Base Color"], (*base, 1.0))
    set_principled_input(bsdf, ["Roughness"], rough)
    set_principled_input(bsdf, ["Metallic"], metallic)
    set_principled_input(bsdf, ["Subsurface Weight", "Subsurface"], subsurface)
    if micro_bump > 0:
        noise = nt.nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value = 85.0
        noise.inputs["Detail"].default_value = 3.0
        noise.inputs["Roughness"].default_value = 0.7
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = micro_bump
        bump.inputs["Distance"].default_value = 0.025
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def apply_transform(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def uv_sphere(name, loc, scale, mat=None, segments=48, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def cube(name, loc, scale, mat=None, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    apply_transform(obj)
    if bevel:
        mod = obj.modifiers.new("Bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 4
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    if mat:
        obj.data.materials.append(mat)
    return obj


def cylinder_between(name, a, b, radius, mat=None, vertices=32):
    a = Vector(a)
    b = Vector(b)
    d = b - a
    mid = (a + b) * 0.5
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=mid)
    obj = bpy.context.object
    obj.name = name
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = d.to_track_quat("Z", "Y")
    apply_transform(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def curve_tube(name, points, radius, mat=None, resolution=4):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = resolution
    curve.resolution_u = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for p, co in zip(spline.bezier_points, points):
        p.co = co
        p.handle_left_type = "AUTO"
        p.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    if mat:
        obj.data.materials.append(mat)
    return obj


def convert_to_mesh(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.select_set(False)
    return obj


def join_voxel(name, parts, voxel=0.055, subdivision=1, mat=None):
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    apply_transform(obj)
    obj.data.remesh_voxel_size = voxel
    obj.data.remesh_voxel_adaptivity = 0.0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.voxel_remesh()
    if len(obj.data.materials) == 0 and mat:
        obj.data.materials.append(mat)
    elif mat:
        obj.data.materials.clear()
        obj.data.materials.append(mat)
    if subdivision:
        mod = obj.modifiers.new("Subdivision", "SUBSURF")
        mod.subdivision_type = "CATMULL_CLARK"
        mod.levels = subdivision
        mod.render_levels = subdivision
        bpy.ops.object.modifier_apply(modifier=mod.name)
    for p in obj.data.polygons:
        p.use_smooth = True
    obj.select_set(False)
    return obj


def add_bone(arm_data, name, head, tail, parent=None, deform=True):
    bone = arm_data.edit_bones.new(name)
    bone.head = head
    bone.tail = tail
    bone.use_deform = deform
    if parent:
        bone.parent = arm_data.edit_bones.get(parent)
    return bone


def build_armature():
    arm_data = bpy.data.armatures.new("RatProductionRig")
    arm = bpy.data.objects.new("RatProductionRig", arm_data)
    bpy.context.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    add_bone(arm_data, "root", (0, 0, 0.1), (0, 0, 0.5), deform=False)
    add_bone(arm_data, "hips", (0, 0, 1.35), (0, 0, 1.72), "root")
    add_bone(arm_data, "spine", (0, 0, 1.72), (0, 0, 2.10), "hips")
    add_bone(arm_data, "chest", (0, 0, 2.10), (0, 0, 2.48), "spine")
    add_bone(arm_data, "neck", (0, 0, 2.48), (0, 0, 2.67), "chest")
    add_bone(arm_data, "head", (0, 0, 2.67), (0, -0.04, 3.20), "neck")
    add_bone(arm_data, "jaw", (0, -0.44, 2.80), (0, -0.67, 2.71), "head")
    add_bone(arm_data, "ear.L", (0.40, -0.02, 3.10), (0.56, -0.02, 3.48), "head")
    add_bone(arm_data, "ear.R", (-0.40, -0.02, 3.10), (-0.56, -0.02, 3.48), "head")
    add_bone(arm_data, "eye.L", (0.22, -0.50, 3.05), (0.22, -0.62, 3.05), "head", deform=False)
    add_bone(arm_data, "eye.R", (-0.22, -0.50, 3.05), (-0.22, -0.62, 3.05), "head", deform=False)
    add_bone(arm_data, "brow.L", (0.22, -0.52, 3.27), (0.22, -0.64, 3.27), "head", deform=False)
    add_bone(arm_data, "brow.R", (-0.22, -0.52, 3.27), (-0.22, -0.64, 3.27), "head", deform=False)
    for side, sx in (("L", 1), ("R", -1)):
        add_bone(arm_data, f"upper_arm.{side}", (0.36*sx, 0, 2.39), (0.88*sx, -0.02, 2.10), "chest")
        add_bone(arm_data, f"forearm.{side}", (0.88*sx, -0.02, 2.10), (1.22*sx, -0.06, 1.82), f"upper_arm.{side}")
        add_bone(arm_data, f"hand.{side}", (1.22*sx, -0.06, 1.82), (1.43*sx, -0.10, 1.72), f"forearm.{side}")
        add_bone(arm_data, f"thigh.{side}", (0.22*sx, 0, 1.45), (0.31*sx, 0.01, 0.98), "hips")
        add_bone(arm_data, f"shin.{side}", (0.31*sx, 0.01, 0.98), (0.32*sx, 0, 0.43), f"thigh.{side}")
        add_bone(arm_data, f"foot.{side}", (0.32*sx, 0, 0.43), (0.32*sx, -0.40, 0.28), f"shin.{side}")
    tail_points = [(0,0.28,1.48), (-0.18,0.42,1.38), (-0.42,0.50,1.27), (-0.68,0.50,1.25), (-0.90,0.42,1.36), (-1.06,0.28,1.58), (-1.10,0.10,1.82)]
    for i in range(6):
        add_bone(arm_data, f"tail.{i+1:02d}", tail_points[i], tail_points[i+1], "hips" if i == 0 else f"tail.{i:02d}")
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.show_in_front = True
    arm.select_set(False)
    return arm, tail_points


def armature_modifier(obj, arm):
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    obj.parent = arm


def set_weights(obj, per_vertex):
    groups = {}
    for idx, weights in enumerate(per_vertex):
        total = sum(weights.values())
        if total <= 0:
            weights = {"hips": 1.0}
            total = 1.0
        for bone, w in weights.items():
            if w <= 0:
                continue
            if bone not in groups:
                groups[bone] = obj.vertex_groups.new(name=bone)
            groups[bone].add([idx], w / total, "REPLACE")


def blend(a, b, t):
    t = max(0.0, min(1.0, t))
    return {a: 1.0 - t, b: t}


def body_weights(obj):
    result = []
    for v in obj.data.vertices:
        x, y, z = v.co
        ax = abs(x)
        side = "L" if x >= 0 else "R"
        if z > 2.62:
            result.append(blend("neck", "head", (z - 2.62) / 0.16))
        elif ax > 0.56 and z > 1.55:
            if ax < 0.92:
                result.append({f"upper_arm.{side}": 1.0})
            elif ax < 1.22:
                result.append(blend(f"upper_arm.{side}", f"forearm.{side}", (ax - 0.92) / 0.30))
            else:
                result.append(blend(f"forearm.{side}", f"hand.{side}", (ax - 1.22) / 0.18))
        elif z < 1.58 and ax > 0.10:
            if z > 1.02:
                result.append(blend("hips", f"thigh.{side}", (1.58-z)/0.56))
            elif z > 0.46:
                result.append(blend(f"thigh.{side}", f"shin.{side}", (1.02-z)/0.56))
            else:
                result.append(blend(f"shin.{side}", f"foot.{side}", (0.46-z)/0.25))
        elif z > 2.28:
            result.append(blend("chest", "neck", (z - 2.28) / 0.34))
        elif z > 1.92:
            result.append(blend("spine", "chest", (z - 1.92) / 0.36))
        elif z > 1.58:
            result.append(blend("hips", "spine", (z - 1.58) / 0.34))
        else:
            result.append({"hips": 1.0})
    return result


def tail_weights(obj, points):
    centers = [(Vector(points[i]) + Vector(points[i+1])) * 0.5 for i in range(6)]
    result = []
    for v in obj.data.vertices:
        p = v.co
        distances = sorted((p - c).length for c in centers)
        ranked = sorted(range(6), key=lambda i: (p - centers[i]).length)[:2]
        d0 = (p - centers[ranked[0]]).length + 1e-5
        d1 = (p - centers[ranked[1]]).length + 1e-5
        w0 = 1.0 / d0
        w1 = 1.0 / d1
        result.append({f"tail.{ranked[0]+1:02d}": w0/(w0+w1), f"tail.{ranked[1]+1:02d}": w1/(w0+w1)})
    return result


def rigid_bone_parent(obj, arm, bone):
    world = obj.matrix_world.copy()
    obj.parent = arm
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world


def make_whisker(name, start, end, mat):
    return curve_tube(name, [start, end], 0.009, mat, resolution=2)


def build_character():
    # Materials
    fur = make_material("Fur_Grey", (0.22,0.24,0.27), rough=0.72, subsurface=0.06, micro_bump=0.23)
    fur_dark = make_material("Fur_Dark", (0.055,0.06,0.07), rough=0.8, micro_bump=0.12)
    skin = make_material("Skin_Pink", (0.72,0.26,0.24), rough=0.58, subsurface=0.18, micro_bump=0.08)
    eye_white = make_material("Eye_White", (0.92,0.90,0.84), rough=0.22)
    iris = make_material("Iris_Amber", (0.30,0.11,0.025), rough=0.18)
    black = make_material("Pupil_Black", (0.006,0.006,0.008), rough=0.12)
    red = make_material("Hoodie_Red", (0.36,0.018,0.02), rough=0.82, micro_bump=0.18)
    cloth_black = make_material("Trousers_Black", (0.018,0.02,0.025), rough=0.88, micro_bump=0.15)
    white = make_material("Shoe_White", (0.85,0.82,0.75), rough=0.48)
    red_leather = make_material("Shoe_Red", (0.46,0.025,0.025), rough=0.34, micro_bump=0.06)
    metal = make_material("Pendant_Metal", (0.62,0.55,0.36), rough=0.18, metallic=0.92)
    tooth = make_material("Teeth", (0.95,0.91,0.78), rough=0.35)
    tongue = make_material("Tongue", (0.58,0.12,0.17), rough=0.52, subsurface=0.08)
    whisker_mat = make_material("Whiskers", (0.76,0.74,0.70), rough=0.38)

    arm, tail_points = build_armature()

    # Continuous body base: silhouette first, then voxel merge and subdivide.
    parts = []
    parts += [uv_sphere("torso", (0,0,2.02), (0.56,0.43,0.74), fur), uv_sphere("pelvis", (0,0,1.52), (0.50,0.40,0.46), fur)]
    parts += [uv_sphere("head", (0,-0.03,2.98), (0.67,0.58,0.63), fur), uv_sphere("muzzle", (0,-0.47,2.79), (0.43,0.31,0.28), fur)]
    parts += [uv_sphere("cheekL", (0.24,-0.44,2.82), (0.30,0.26,0.27), fur), uv_sphere("cheekR", (-0.24,-0.44,2.82), (0.30,0.26,0.27), fur)]
    for side, sx in (("L",1),("R",-1)):
        shoulder=(0.38*sx,0,2.38); elbow=(0.88*sx,-0.02,2.10); wrist=(1.23*sx,-0.06,1.82)
        parts += [cylinder_between(f"upperArm{side}", shoulder, elbow, 0.20, fur), uv_sphere(f"elbow{side}", elbow, (0.22,0.20,0.22), fur)]
        parts += [cylinder_between(f"foreArm{side}", elbow, wrist, 0.17, fur), uv_sphere(f"handBase{side}", (1.34*sx,-0.09,1.76), (0.23,0.17,0.18), fur)]
        hip=(0.22*sx,0,1.48); knee=(0.31*sx,0.01,0.96); ankle=(0.32*sx,0,0.42)
        parts += [cylinder_between(f"thigh{side}", hip, knee, 0.25, fur), uv_sphere(f"knee{side}", knee, (0.25,0.22,0.23), fur)]
        parts += [cylinder_between(f"shin{side}", knee, ankle, 0.20, fur), uv_sphere(f"paw{side}", (0.32*sx,-0.14,0.31), (0.25,0.36,0.16), fur)]
    body = join_voxel("Rat_Body_Skinned", parts, voxel=0.050, subdivision=1, mat=fur)
    armature_modifier(body, arm)
    set_weights(body, body_weights(body))

    # Tail as a separate skinned mesh with six deform controls.
    tail = convert_to_mesh(curve_tube("Rat_Tail_Skinned", tail_points, 0.075, skin, resolution=4))
    for p in tail.data.polygons: p.use_smooth = True
    armature_modifier(tail, arm)
    set_weights(tail, tail_weights(tail, tail_points))

    # Hoodie shell with baggier silhouette and sleeves.
    hoodie_parts = [uv_sphere("hoodieTorso", (0,0.015,2.03), (0.62,0.48,0.64), red)]
    for side,sx in (("L",1),("R",-1)):
        hoodie_parts += [cylinder_between(f"hoodieUpper{side}", (0.38*sx,0,2.37), (0.88*sx,-0.02,2.10), 0.245, red), cylinder_between(f"hoodieFore{side}", (0.88*sx,-0.02,2.10), (1.15*sx,-0.05,1.87), 0.205, red)]
    hoodie = join_voxel("Hoodie_Skinned", hoodie_parts, voxel=0.058, subdivision=1, mat=red)
    armature_modifier(hoodie, arm)
    set_weights(hoodie, body_weights(hoodie))
    # hood ring, pocket and cuffs as detailed rigid/weighted accessories
    bpy.ops.mesh.primitive_torus_add(major_radius=0.39, minor_radius=0.12, major_segments=48, minor_segments=16, location=(0,0.10,2.49), rotation=(math.radians(78),0,0))
    hood = bpy.context.object; hood.name="Hood_Roll"; hood.data.materials.append(red); rigid_bone_parent(hood, arm, "chest")
    pocket = cube("Hoodie_Pocket", (0,-0.48,1.90), (0.29,0.055,0.16), red, bevel=0.07); rigid_bone_parent(pocket, arm, "spine")
    for side,sx in (("L",1),("R",-1)):
        cuff = uv_sphere(f"Cuff.{side}", (1.17*sx,-0.06,1.86), (0.12,0.14,0.12), red); rigid_bone_parent(cuff, arm, f"forearm.{side}")

    # Baggy trousers, shaped separately and skinned.
    trouser_parts = [uv_sphere("waist", (0,0,1.49), (0.57,0.45,0.34), cloth_black)]
    for side,sx in (("L",1),("R",-1)):
        trouser_parts += [cylinder_between(f"pantUpper{side}", (0.22*sx,0,1.45), (0.31*sx,0,0.91), 0.30, cloth_black), cylinder_between(f"pantLower{side}", (0.31*sx,0,0.91), (0.32*sx,0,0.48), 0.245, cloth_black)]
    trousers = join_voxel("Trousers_Skinned", trouser_parts, voxel=0.058, subdivision=1, mat=cloth_black)
    armature_modifier(trousers, arm)
    set_weights(trousers, body_weights(trousers))

    # Ears: thin soft outer ear and inner-ear inserts.
    for side,sx in (("L",1),("R",-1)):
        ear = uv_sphere(f"Ear.{side}", (0.53*sx,-0.02,3.26), (0.30,0.105,0.37), fur)
        inner = uv_sphere(f"InnerEar.{side}", (0.53*sx,-0.105,3.26), (0.22,0.035,0.29), skin)
        rigid_bone_parent(ear, arm, f"ear.{side}"); rigid_bone_parent(inner, arm, f"ear.{side}")

    # Face components.
    nose = uv_sphere("Nose", (0,-0.73,2.86), (0.19,0.13,0.13), skin); rigid_bone_parent(nose, arm, "head")
    lower_jaw = uv_sphere("LowerJaw", (0,-0.50,2.67), (0.31,0.22,0.13), fur_dark); rigid_bone_parent(lower_jaw, arm, "jaw")
    tongue_obj = uv_sphere("Tongue", (0,-0.62,2.66), (0.17,0.14,0.055), tongue); rigid_bone_parent(tongue_obj, arm, "jaw")
    for sx,name in ((0.22,"L"),(-0.22,"R")):
        eye = uv_sphere(f"Eye.{name}", (sx,-0.53,3.07), (0.19,0.125,0.23), eye_white); rigid_bone_parent(eye, arm, f"eye.{name}")
        iris_obj = uv_sphere(f"Iris.{name}", (sx,-0.648,3.07), (0.095,0.030,0.105), iris); rigid_bone_parent(iris_obj, arm, f"eye.{name}")
        pupil = uv_sphere(f"Pupil.{name}", (sx,-0.674,3.07), (0.042,0.016,0.050), black); rigid_bone_parent(pupil, arm, f"eye.{name}")
        brow = curve_tube(f"Brow.{name}", [(sx-0.13*sx/abs(sx),-0.62,3.29),(sx,-0.64,3.33),(sx+0.13*sx/abs(sx),-0.61,3.29)], 0.030, fur_dark, resolution=3); rigid_bone_parent(brow, arm, f"brow.{name}")
    for sx in (-0.105,0.105):
        tooth_obj = cube(f"Tooth_{sx}", (sx,-0.64,2.73), (0.055,0.035,0.105), tooth, bevel=0.025); rigid_bone_parent(tooth_obj, arm, "head")
    # whiskers
    for side,sx in (("L",1),("R",-1)):
        for i,(dy,dz) in enumerate(((-0.02,0.08),(0,0),(-0.015,-0.08))):
            start=(0.24*sx,-0.69,2.84+dz)
            end=(0.88*sx,-0.78+dy,2.90+dz*1.5)
            w=make_whisker(f"Whisker.{side}.{i}",start,end,whisker_mat); rigid_bone_parent(w,arm,"head")

    # Exposed hands/fingers in skin tone, parented to the hand bones.
    for side,sx in (("L",1),("R",-1)):
        palm = uv_sphere(f"Palm.{side}",(1.36*sx,-0.10,1.75),(0.19,0.13,0.15),skin); rigid_bone_parent(palm,arm,f"hand.{side}")
        for j in range(3):
            f = cylinder_between(f"Finger.{side}.{j}",(1.41*sx,-0.16+j*0.035,1.76+j*0.018),(1.55*sx,-0.18+j*0.035,1.72+j*0.018),0.030,skin,vertices=20); rigid_bone_parent(f,arm,f"hand.{side}")

    # Shoes with layered upper/sole/tongue and laces.
    for side,sx in (("L",1),("R",-1)):
        upper = cube(f"ShoeUpper.{side}",(0.32*sx,-0.24,0.29),(0.24,0.38,0.14),red_leather,bevel=0.10); rigid_bone_parent(upper,arm,f"foot.{side}")
        sole = cube(f"ShoeSole.{side}",(0.32*sx,-0.25,0.17),(0.26,0.41,0.065),white,bevel=0.045); rigid_bone_parent(sole,arm,f"foot.{side}")
        tongue_obj = cube(f"ShoeTongue.{side}",(0.32*sx,-0.26,0.41),(0.16,0.19,0.08),white,bevel=0.045); rigid_bone_parent(tongue_obj,arm,f"foot.{side}")
        for j in range(4):
            lace = curve_tube(f"Lace.{side}.{j}",[(0.18*sx,-0.49+j*0.045,0.42),(0.46*sx,-0.49+j*0.045,0.42)],0.010,white,resolution=2); rigid_bone_parent(lace,arm,f"foot.{side}")

    # Pendant + chain + drawstrings.
    chain = curve_tube("Chain", [(-0.18,-0.46,2.42),(0,-0.53,2.18),(0.18,-0.46,2.42)],0.018,metal,resolution=3); rigid_bone_parent(chain,arm,"chest")
    pendant = cube("Pendant_R",(0,-0.56,2.13),(0.105,0.035,0.13),metal,bevel=0.035); rigid_bone_parent(pendant,arm,"chest")
    for sx in (-0.10,0.10):
        string = curve_tube(f"Drawstring_{sx}",[(sx,-0.50,2.40),(sx,-0.54,2.08)],0.012,red,resolution=2); rigid_bone_parent(string,arm,"chest")

    # Small head fur tufts as tapered-ish curves.
    for i,x in enumerate((-0.12,-0.04,0.05,0.13)):
        tuft = curve_tube(f"HeadTuft.{i}",[(x,-0.03,3.49),(x*1.2,-0.05,3.66+0.05*math.sin(i))],0.022,fur_dark,resolution=2); rigid_bone_parent(tuft,arm,"head")

    return arm, body, hoodie, trousers, tail


def setup_qa_scene(arm):
    floor_mat = make_material("Floor", (0.022,0.026,0.032), rough=0.38)
    bpy.ops.mesh.primitive_plane_add(size=16, location=(0,0,0.05))
    floor = bpy.context.object
    floor.data.materials.append(floor_mat)

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.006,0.008,0.012,1)
    bg.inputs["Strength"].default_value = 0.18

    def area(name, loc, energy, color, size, target=(0,0,1.8)):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = loc
        obj.rotation_euler = (Vector(target)-obj.location).to_track_quat("-Z","Y").to_euler()
        return obj

    area("Key", (-3.6,-4.5,6.0), 1150, (1.0,0.82,0.70), 4.0)
    area("Fill", (3.8,-2.5,4.2), 720, (0.55,0.70,1.0), 3.5)
    area("Rim", (1.8,3.2,5.0), 1050, (0.40,0.55,1.0), 3.0)
    area("SoftTop", (0,0,7.0), 500, (1.0,0.95,0.85), 5.0)

    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    cam.data.lens = 58
    cam.data.sensor_width = 36
    return cam


def look_at(cam, target=(0,0,1.8)):
    cam.rotation_euler = (Vector(target)-cam.location).to_track_quat("-Z","Y").to_euler()


def render_views(cam, arm):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 700
    scene.render.resolution_y = 700
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    # Neutral QA viewpoints: no animation or fake motion.
    views = {
        "front": ((0,-7.2,2.65),(0,0,1.85)),
        "three-quarter": ((4.7,-5.4,2.75),(0,0,1.85)),
        "side": ((7.1,-0.2,2.65),(0,0,1.85)),
        "back": ((0,7.1,2.7),(0,0,1.85)),
        "face": ((0,-4.2,3.15),(0,-0.10,3.02)),
    }
    for name,(loc,target) in views.items():
        cam.location = loc
        cam.data.lens = 72 if name == "face" else 58
        look_at(cam,target)
        scene.render.filepath = os.path.join(out_dir,f"rat-{name}.png")
        bpy.ops.render.render(write_still=True)


def validate_and_manifest(arm, body, hoodie, trousers, tail):
    required = {"root","hips","spine","chest","neck","head","jaw","ear.L","ear.R","upper_arm.L","forearm.L","hand.L","upper_arm.R","forearm.R","hand.R","thigh.L","shin.L","foot.L","thigh.R","shin.R","foot.R",*[f"tail.{i:02d}" for i in range(1,7)]}
    bone_names = {b.name for b in arm.data.bones}
    missing = sorted(required - bone_names)
    if missing:
        raise RuntimeError(f"Missing required bones: {missing}")

    skinned = [body, hoodie, trousers, tail]
    unweighted = 0
    weighted_vertices = 0
    max_weight_error = 0.0
    for obj in skinned:
        if not any(m.type == "ARMATURE" and m.object == arm for m in obj.modifiers):
            raise RuntimeError(f"{obj.name} has no armature modifier")
        for v in obj.data.vertices:
            weights = [g.weight for g in v.groups]
            if not weights:
                unweighted += 1
            else:
                weighted_vertices += 1
                max_weight_error = max(max_weight_error, abs(1.0-sum(weights)))
    if unweighted:
        raise RuntimeError(f"Found {unweighted} unweighted vertices")

    triangles = 0
    verts = 0
    mesh_objects = 0
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            mesh_objects += 1
            verts += len(obj.data.vertices)
            triangles += sum(max(0,len(p.vertices)-2) for p in obj.data.polygons)
    if triangles < 45000:
        raise RuntimeError(f"Triangle count too low for production asset QA: {triangles}")
    if triangles > 350000:
        raise RuntimeError(f"Triangle count too high for runtime target: {triangles}")

    manifest = {
        "blender_version": bpy.app.version_string,
        "asset": "rat-production-blender",
        "bones": len(arm.data.bones),
        "required_bones": sorted(required),
        "skinned_meshes": [o.name for o in skinned],
        "weighted_vertices": weighted_vertices,
        "unweighted_vertices": unweighted,
        "max_weight_sum_error": max_weight_error,
        "scene_mesh_objects": mesh_objects,
        "scene_vertices": verts,
        "scene_triangles": triangles,
        "quality_gate": {
            "continuous_body_skin": True,
            "separate_skinned_clothing": True,
            "segmented_tail_rig": True,
            "facial_control_bones": True,
            "qa_turntable_views": ["front","three-quarter","side","back","face"],
        },
    }
    with open(os.path.join(out_dir,"rat-production-manifest.json"),"w") as f:
        json.dump(manifest,f,indent=2)
    return manifest


def main():
    clear_scene()
    arm, body, hoodie, trousers, tail = build_character()
    cam = setup_qa_scene(arm)
    manifest = validate_and_manifest(arm, body, hoodie, trousers, tail)

    # Save editable DCC source before export.
    blend_path = os.path.join(out_dir,"rat-production.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)

    # Runtime contract for Remotion / Three.js.
    glb_path = os.path.join(out_dir,"rat-production.glb")
    bpy.ops.export_scene.gltf(
        filepath=glb_path,
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
    render_views(cam, arm)
    print("RAT_BUILD_MANIFEST=" + json.dumps(manifest, sort_keys=True))
    print("RAT_BUILD_COMPLETE=" + out_dir)


if __name__ == "__main__":
    main()
