from pathlib import Path

# Reuse the validated v3 refinement implementation, but load only its definitions.
# The original script's top-level execution is intentionally not run because its
# region selection and metric collection used mesh-local coordinates.
base_script = Path(__file__).with_name('refine_rat_v3.py')
source = base_script.read_text(encoding='utf-8')
marker = '\nreshape_body_v3()\nreshape_clothing_v3()\n'
if marker not in source:
    raise RuntimeError('Could not locate refine_rat_v3.py execution marker')
definitions = source.split(marker, 1)[0]
exec(compile(definitions, str(base_script), 'exec'), globals(), globals())


def reshape_body_v3():
    obj = bpy.data.objects['Rat_Body_Skinned']
    to_world = obj.matrix_world.copy()
    to_local = to_world.inverted()
    touched = {'head': 0, 'torso': 0, 'lower_torso': 0}

    for v in obj.data.vertices:
        co = to_world @ v.co
        x, y, z = co.x, co.y, co.z

        if z > 2.55:
            touched['head'] += 1
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
            touched['torso'] += 1
            t = clamp((z - 1.55) / 1.0)
            co.x *= 0.90 + 0.105 * t
            co.y *= 0.97
        elif 1.15 < z <= 1.55:
            touched['lower_torso'] += 1
            co.x *= 0.94

        v.co = to_local @ co

    obj.data.update()
    print('BODY_WORLD_SCULPT_COUNTS', touched)
    if touched['head'] == 0 or touched['torso'] == 0:
        raise RuntimeError(f'World-space body sculpt selected no vertices: {touched}')


def reshape_clothing_v3():
    hoodie = bpy.data.objects.get('Hoodie_Skinned')
    if hoodie:
        to_world = hoodie.matrix_world.copy()
        to_local = to_world.inverted()
        touched = 0
        for v in hoodie.data.vertices:
            co = to_world @ v.co
            if 1.48 < co.z < 2.56:
                touched += 1
                t = clamp((co.z - 1.48) / 1.08)
                co.x *= 0.87 + 0.11 * t
                if co.y < -0.24:
                    co.y *= 1.035
                if 1.48 < co.z < 1.68:
                    co.z -= 0.025 * (1.0 - t)
            v.co = to_local @ co
        hoodie.data.update()
        print('HOODIE_WORLD_SCULPT_COUNT', touched)
        if touched == 0:
            raise RuntimeError('World-space hoodie sculpt selected no vertices')

    trousers = bpy.data.objects.get('Trousers_Skinned')
    if trousers:
        to_world = trousers.matrix_world.copy()
        to_local = to_world.inverted()
        counts = {'upper': 0, 'mid': 0, 'lower': 0}
        for v in trousers.data.vertices:
            co = to_world @ v.co
            if co.z > 1.05:
                counts['upper'] += 1
                co.x *= 0.96
            if 0.55 < co.z < 0.95:
                counts['mid'] += 1
                co.x *= 0.92
            if co.z < 0.55:
                counts['lower'] += 1
                co.x *= 0.88
            v.co = to_local @ co
        trousers.data.update()
        print('TROUSERS_WORLD_SCULPT_COUNTS', counts)
        if counts['upper'] == 0 or counts['mid'] == 0 or counts['lower'] == 0:
            raise RuntimeError(f'World-space trouser sculpt missed a region: {counts}')


def bounds_width(points):
    xs = [p.x for p in points]
    return max(xs) - min(xs) if xs else 0.0


def bounds_depth(points):
    ys = [p.y for p in points]
    return max(ys) - min(ys) if ys else 0.0


def compute_metrics():
    body = bpy.data.objects['Rat_Body_Skinned']
    verts = [body.matrix_world @ v.co for v in body.data.vertices]
    head = [p for p in verts if p.z > 2.55]
    shoulders = [p for p in verts if 2.16 <= p.z <= 2.42]
    waist = [p for p in verts if 1.62 <= p.z <= 1.82]
    front_head = min((p.y for p in head), default=0.0)
    upper_face = [p for p in head if p.z >= 3.12]
    forehead_front = min((p.y for p in upper_face), default=front_head)
    muzzle_projection = max(0.0, forehead_front - front_head)
    metrics = {
        'head_width': round(bounds_width(head), 5),
        'head_depth': round(bounds_depth(head), 5),
        'muzzle_projection': round(muzzle_projection, 5),
        'shoulder_width': round(bounds_width(shoulders), 5),
        'waist_width': round(bounds_width(waist), 5),
        'head_vertex_count': len(head),
        'shoulder_vertex_count': len(shoulders),
        'waist_vertex_count': len(waist),
    }
    print('WORLD_SCULPT_METRICS', json.dumps(metrics, indent=2))
    if not head or not shoulders or not waist:
        raise RuntimeError(f'World-space metric regions are empty: {metrics}')
    return metrics


# Run the same visual refinement pipeline with corrected spatial semantics.
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
print('RAT SCULPT V3 WORLD-SPACE COMPLETE')
print(json.dumps(metrics, indent=2))
