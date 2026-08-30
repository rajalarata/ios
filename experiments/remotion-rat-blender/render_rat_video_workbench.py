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
scene.render.engine = 'BLENDER_WORKBENCH'
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'WORLD'
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = 'WORLD'
scene.display.shading.background_color = (0.018, 0.022, 0.032)
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.resolution_percentage = 100
scene.render.fps = 24
scene.frame_start = 1
scene.frame_end = 120
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.constant_rate_factor = 'HIGH'
scene.render.ffmpeg.ffmpeg_preset = 'GOOD'
scene.render.filepath = os.path.join(out_dir, 'rat-production-workbench.mp4')

for datablock in (arm, cam, cam.data):
    if getattr(datablock, 'animation_data', None):
        datablock.animation_data_clear()

for pb in arm.pose.bones:
    pb.rotation_mode = 'XYZ'
    pb.rotation_euler = (0,0,0)
    pb.location = (0,0,0)


def kr(name, frame, deg):
    pb = arm.pose.bones.get(name)
    if not pb: return
    pb.rotation_mode='XYZ'
    pb.rotation_euler=tuple(math.radians(v) for v in deg)
    pb.keyframe_insert('rotation_euler', frame=frame)


def look_at(target):
    cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()


def kc(frame, loc, target, lens=60):
    cam.location=loc
    cam.data.lens=lens
    look_at(target)
    cam.keyframe_insert('location',frame=frame)
    cam.keyframe_insert('rotation_euler',frame=frame)
    cam.data.keyframe_insert('lens',frame=frame)

# Pose keys: readable, restrained, asymmetric.
for f in (1,120):
    for name in ('head','upper_arm.L','upper_arm.R','forearm.L','forearm.R','tail.02','tail.03','jaw'):
        kr(name,f,(0,0,0))
kr('head',30,(4,-2,-8)); kr('tail.02',30,(0,0,10)); kr('tail.03',30,(0,0,14))
kr('head',60,(-3,3,7)); kr('upper_arm.L',60,(0,-12,-28)); kr('forearm.L',60,(0,-18,-30)); kr('upper_arm.R',60,(0,8,16)); kr('forearm.R',60,(0,15,22)); kr('jaw',60,(7,0,0)); kr('tail.02',60,(0,0,16)); kr('tail.03',60,(0,0,20))
kr('head',90,(2,-2,-5)); kr('upper_arm.L',90,(0,-4,-8)); kr('forearm.L',90,(0,-5,-10)); kr('upper_arm.R',90,(0,8,18)); kr('forearm.R',90,(0,14,24)); kr('jaw',90,(3,0,0)); kr('tail.02',90,(0,0,-10)); kr('tail.03',90,(0,0,-14))

# Smooth 5-second camera orbit with a closer facial pass in the middle.
kc(1,(0,-7.3,2.65),(0,0,1.92),58)
kc(30,(4.8,-5.1,2.75),(0,0,1.95),62)
kc(60,(4.7,-3.8,3.15),(0,-0.08,2.55),70)
kc(90,(-4.5,-5.0,2.75),(0,0,1.95),62)
kc(120,(0,-7.3,2.65),(0,0,1.92),58)

for owner in (arm,cam):
    if owner.animation_data and owner.animation_data.action:
        for fc in owner.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation='BEZIER'
                kp.handle_left_type='AUTO_CLAMPED'
                kp.handle_right_type='AUTO_CLAMPED'

bpy.ops.render.render(animation=True)
print('Rendered',scene.render.filepath)
