import bpy


def bounds(points):
    return {
        'x': (min(p.x for p in points), max(p.x for p in points)),
        'y': (min(p.y for p in points), max(p.y for p in points)),
        'z': (min(p.z for p in points), max(p.z for p in points)),
    }


def inspect(name):
    obj = bpy.data.objects[name]
    local = [v.co.copy() for v in obj.data.vertices]
    world = [obj.matrix_world @ v.co for v in obj.data.vertices]
    print(f'OBJECT {name}')
    print('VERTEX_COUNT', len(local))
    print('MATRIX_WORLD')
    print(obj.matrix_world)
    print('LOCAL_BOUNDS', bounds(local))
    print('WORLD_BOUNDS', bounds(world))
    return local, world

body_local, body_world = inspect('Rat_Body_Skinned')
hoodie_local, hoodie_world = inspect('Hoodie_Skinned')
trousers_local, trousers_world = inspect('Trousers_Skinned')

print('BODY_LOCAL_HEAD_COUNT_Z_GT_2_55', sum(1 for p in body_local if p.z > 2.55))
print('BODY_WORLD_HEAD_COUNT_Z_GT_2_55', sum(1 for p in body_world if p.z > 2.55))
print('HOODIE_LOCAL_TAPER_COUNT', sum(1 for p in hoodie_local if 1.48 < p.z < 2.56))
print('HOODIE_WORLD_TAPER_COUNT', sum(1 for p in hoodie_world if 1.48 < p.z < 2.56))
print('TROUSERS_LOCAL_ABOVE_1_05', sum(1 for p in trousers_local if p.z > 1.05))
print('TROUSERS_WORLD_ABOVE_1_05', sum(1 for p in trousers_world if p.z > 1.05))

assert len(body_local) > 0
assert len(hoodie_local) > 0
assert len(trousers_local) > 0
assert len(body_world) == len(body_local)
