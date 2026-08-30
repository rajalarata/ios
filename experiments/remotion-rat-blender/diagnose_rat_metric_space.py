import bpy

body = bpy.data.objects['Rat_Body_Skinned']
local = [v.co.copy() for v in body.data.vertices]
world = [body.matrix_world @ v.co for v in body.data.vertices]


def bounds(points):
    return {
        'x': (min(p.x for p in points), max(p.x for p in points)),
        'y': (min(p.y for p in points), max(p.y for p in points)),
        'z': (min(p.z for p in points), max(p.z for p in points)),
    }

print('BODY_MATRIX_WORLD')
print(body.matrix_world)
print('LOCAL_BOUNDS', bounds(local))
print('WORLD_BOUNDS', bounds(world))
print('LOCAL_HEAD_COUNT_Z_GT_2_55', sum(1 for p in local if p.z > 2.55))
print('WORLD_HEAD_COUNT_Z_GT_2_55', sum(1 for p in world if p.z > 2.55))

assert len(local) > 0
assert len(world) == len(local)
