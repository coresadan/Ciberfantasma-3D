"""Render key poses from the generated hero rig for quick visual comparison."""

from pathlib import Path
import math
import sys

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = PROJECT_ROOT / "SourceAssets" / "Previews" / "AnimationReview"


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    action_name = "A_Ciberfantasma_Pro_Run"
    frames = [1, 4, 7, 10, 13, 16, 19, 22]
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if args:
        action_name = args[0]
    if len(args) > 1:
        frames = [int(value) for value in args[1].split(",")]

    hero = bpy.data.objects.get("SM_Ciberfantasma_Chibi")
    armature = bpy.data.objects.get("SK_Ciberfantasma_Chibi_Armature")
    action = bpy.data.actions.get(action_name)
    if not hero or not armature or not action:
        raise RuntimeError(f"Missing review source: hero={hero} armature={armature} action={action_name}")

    for obj in bpy.context.scene.objects:
        obj.hide_render = obj not in (hero, armature)
    hero.hide_render = False
    hero.location = (0.0, 0.0, 0.0)
    # Match the three-quarter gameplay presentation: enough turn to read boot
    # direction and fore/aft limb separation without losing the skull mask.
    hero.rotation_euler = (0.0, 0.0, 0.0)
    hero.scale = (1.0, 1.0, 1.0)
    armature.hide_render = False
    armature.location = (0.0, 0.0, 0.0)
    armature.rotation_euler = (0.0, 0.0, math.radians(55.0))
    armature.scale = (1.0, 1.0, 1.0)
    armature.animation_data_create()
    armature.animation_data.action = action

    floor_material = bpy.data.materials.get("M_ReviewFloor") or bpy.data.materials.new("M_ReviewFloor")
    floor_material.diffuse_color = (0.025, 0.035, 0.05, 1.0)
    bpy.ops.mesh.primitive_plane_add(size=500, location=(0, 0, -1.0))
    floor = bpy.context.object
    floor.name = "REVIEW_Floor"
    floor.data.materials.append(floor_material)
    floor.hide_render = False

    for location, energy, size, color in (
        ((-130, -180, 240), 1500, 140, (0.82, 0.9, 1.0)),
        ((150, -80, 150), 950, 110, (0.25, 1.0, 0.4)),
        ((0, 100, 190), 1200, 120, (0.32, 0.48, 1.0)),
    ):
        bpy.ops.object.light_add(type="AREA", location=location)
        light = bpy.context.object
        light.data.energy = energy
        light.data.size = size
        light.data.color = color
        light.hide_render = False
        look_at(light, (0, 0, 82))

    bpy.ops.object.camera_add(location=(0, -440, 94))
    camera = bpy.context.object
    camera.data.lens = 68
    look_at(camera, (0, 0, 78))
    camera.hide_render = False
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 560
    scene.render.resolution_y = 640
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.006, 0.008, 0.014)
    scene.view_settings.look = "AgX - Medium High Contrast"
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

    for frame in frames:
        scene.frame_set(frame)
        scene.render.filepath = str(OUTPUT_ROOT / f"{action_name}_F{frame:03d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"Rendered {scene.render.filepath}")


main()
