import bpy
import math
import os
import sys
from mathutils import Vector

ARGS = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
out_dir = os.path.abspath(ARGS[ARGS.index('--out') + 1]) if '--out' in ARGS else os.path.abspath('out')
os.makedirs(out_dir, exist_ok=True)

scene = bpy.context.scene
arm = bpy.data.objects['RatProductionRig']
cam = scene.camera

# Fast but proper Blender render for review.
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 168
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.filepath = os.path.join(out_dir, 'rat-production-cinematic.mp4')

# Transparent disabled: show the lit studio environment from the .blend.
scene.render.film_transparent = False

# Helper setup.
def reset_pose():
    for pb in arm.pose.bones:
        pb.rotation_mode = 'XYZ'
        pb.rotation_euler = (0, 0, 0)
        pb.location = (0, 0, 0)
        pb.scale = (1, 1, 1)


def key_rot(bone_name, frame, xyz):
    pb = arm.pose.bones.get(bone_name)
    if not pb:
        return
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = tuple(math.radians(v) for v in xyz)
    pb.keyframe_insert('rotation_euler', frame=frame)


def key_loc(bone_name, frame, xyz):
    pb = arm.pose.bones.get(bone_name)
    if not pb:
        return
    pb.location = xyz
    pb.keyframe_insert('location', frame=frame)


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def key_camera(frame, location, target, lens):
    cam.location = location
    cam.data.lens = lens
    look_at(cam, target)
    cam.keyframe_insert('location', frame=frame)
    cam.keyframe_insert('rotation_euler', frame=frame)
    cam.data.keyframe_insert('lens', frame=frame)


def ease_all():
    # Blender Bezier interpolation + AUTO_CLAMPED handles gives smooth anticipation/overshoot.
    if arm.animation_data and arm.animation_data.action:
        for fc in arm.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
                kp.handle_left_type = 'AUTO_CLAMPED'
                kp.handle_right_type = 'AUTO_CLAMPED'


# Clear old animation data.
for datablock in (arm, cam, cam.data):
    if getattr(datablock, 'animation_data', None):
        datablock.animation_data_clear()
reset_pose()

# Character performance: restrained QA motion, enough to inspect deformation and personality.
# Neutral entrance.
for f in (1, 168):
    key_rot('head', f, (0, 0, 0))
    key_rot('jaw', f, (0, 0, 0))
    key_rot('upper_arm.L', f, (0, 0, 0))
    key_rot('upper_arm.R', f, (0, 0, 0))
    key_rot('forearm.L', f, (0, 0, 0))
    key_rot('forearm.R', f, (0, 0, 0))
    key_rot('ear.L', f, (0, 0, 0))
    key_rot('ear.R', f, (0, 0, 0))

# Curious look + light asymmetry.
key_rot('head', 34, (4, -2, -8))
key_rot('ear.L', 34, (0, 0, 6))
key_rot('ear.R', 34, (0, 0, -3))
key_rot('tail.02', 34, (0, 0, 8))
key_rot('tail.03', 34, (0, 0, 12))

# Hero gesture with planted body, avoiding robotic whole-body oscillation.
key_rot('head', 72, (-2, 4, 7))
key_rot('upper_arm.L', 72, (0, -12, -28))
key_rot('forearm.L', 72, (0, -18, -30))
key_rot('hand.L', 72, (0, 4, -8))
key_rot('upper_arm.R', 72, (0, 8, 16))
key_rot('forearm.R', 72, (0, 15, 22))
key_rot('jaw', 72, (7, 0, 0))
key_rot('ear.L', 72, (0, 0, 8))
key_rot('ear.R', 72, (0, 0, -7))
key_rot('tail.02', 72, (0, 0, 14))
key_rot('tail.03', 72, (0, 0, 18))
key_rot('tail.04', 72, (0, 0, 12))

# Relax, then opposite-side reaction.
key_rot('head', 112, (3, -3, -6))
key_rot('upper_arm.L', 112, (0, -4, -8))
key_rot('forearm.L', 112, (0, -5, -10))
key_rot('upper_arm.R', 112, (0, 10, 20))
key_rot('forearm.R', 112, (0, 16, 26))
key_rot('jaw', 112, (3, 0, 0))
key_rot('tail.02', 112, (0, 0, -10))
key_rot('tail.03', 112, (0, 0, -14))
key_rot('tail.04', 112, (0, 0, -8))

# Blink via eyelid objects parented to head: key their scale vertically.
for side in ('L', 'R'):
    lid = bpy.data.objects.get(f'UpperLid.{side}')
    if lid:
        base = lid.scale.copy()
        for frame, zscale in ((1,1.0),(45,1.0),(48,1.55),(51,1.0),(119,1.0),(122,1.55),(125,1.0),(168,1.0)):
            lid.scale = (base.x, base.y, base.z * zscale)
            lid.keyframe_insert('scale', frame=frame)

# Cinematic camera: establish, orbit, face close-up, then settle to hero three-quarter.
key_camera(1,   (0.0, -7.6, 2.65), (0.0, -0.02, 1.92), 58)
key_camera(42,  (3.8, -6.3, 2.75), (0.0, -0.03, 1.95), 62)
key_camera(82,  (5.9, -3.5, 2.95), (0.0, -0.02, 2.05), 65)
key_camera(116, (1.3, -4.6, 3.25), (0.0, -0.16, 2.95), 72)
key_camera(138, (-3.9, -5.8, 2.78), (0.0, -0.03, 1.98), 62)
key_camera(168, (3.9, -5.7, 2.75), (0.0, -0.03, 1.95), 62)

ease_all()

# Ensure light objects render consistently and add a moving rim accent if available.
for name in ('Key', 'Fill', 'Rim'):
    obj = bpy.data.objects.get(name)
    if obj and obj.type == 'LIGHT':
        obj.data.energy *= 1.05

# Save an animation-ready blend alongside the video.
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, 'rat-production-animated.blend'))

# Render H.264 MP4.
bpy.ops.render.render(animation=True)
print('Rendered', scene.render.filepath)
