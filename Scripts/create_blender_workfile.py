"""Create a clean, Unreal-oriented Blender source scene for character production."""

from pathlib import Path
import math
import bpy


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_ROOT = PROJECT_ROOT / "ReferenceArt"
OUTPUT = PROJECT_ROOT / "SourceAssets" / "Blender" / "CF_Character_Workfile.blend"


def clean_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name != "Collection":
            bpy.data.collections.remove(collection)


def create_collection(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def add_reference_image(path, name, location, size, collection):
    image = bpy.data.images.load(str(path), check_existing=True)
    bpy.ops.object.empty_add(
        type="IMAGE",
        location=location,
        rotation=(math.radians(90.0), 0.0, 0.0),
    )
    ref = bpy.context.object
    ref.name = name
    ref.data = image
    ref.empty_display_size = size
    ref.color[3] = 0.7
    ref.show_in_front = True
    ref.hide_render = True
    move_to_collection(ref, collection)
    return ref


def build():
    clean_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.01
    scene.unit_settings.length_unit = "CENTIMETERS"
    scene.render.fps = 60
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"

    default_collection = bpy.data.collections.get("Collection")
    if default_collection:
        bpy.data.collections.remove(default_collection)

    references = create_collection("00_REFERENCES")
    character = create_collection("10_CHARACTER")
    equipment = create_collection("20_EQUIPMENT")
    rig = create_collection("30_RIG")
    export = create_collection("90_EXPORT")

    turnaround = REFERENCE_ROOT / "ciberfantasma-chibi-turnaround-v1.png"
    idle = REFERENCE_ROOT / "ciberfantasma-chibi-idle-final.png"
    if turnaround.exists():
        add_reference_image(turnaround, "REF_Ciberfantasma_Chibi_Turnaround", (0.0, 180.0, 90.0), 260.0, references)
    if idle.exists():
        add_reference_image(idle, "REF_Ciberfantasma_Chibi_Idle", (350.0, 185.0, 90.0), 230.0, references)

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=28.0, depth=150.0, location=(0.0, 0.0, 75.0))
    guide = bpy.context.object
    guide.name = "SCALE_GUIDE_CHIBI_150CM_NOT_FOR_EXPORT"
    guide.display_type = "WIRE"
    guide.color = (0.05, 0.95, 0.35, 1.0)
    guide.hide_render = True
    move_to_collection(guide, references)

    bpy.ops.mesh.primitive_cube_add(location=(0.0, 0.0, -5.0), scale=(500.0, 300.0, 5.0))
    ground = bpy.context.object
    ground.name = "SCALE_GROUND_NOT_FOR_EXPORT"
    ground.display_type = "WIRE"
    ground.hide_render = True
    move_to_collection(ground, references)

    scene["cf_pipeline"] = "Unreal Engine 5 skeletal mesh"
    scene["cf_character_height_cm"] = 150.0
    scene["cf_character_heads_tall"] = 2.6
    scene["cf_forward_axis"] = "+X"
    scene["cf_depth_axis"] = "+Y"
    scene["cf_up_axis"] = "+Z"
    scene["cf_note"] = "Scale guides are references only. Build final topology in 10_CHARACTER."

    text = bpy.data.texts.new("PIPELINE_NOTES")
    text.write(
        "EL CIBERFANTASMA 3D\n"
        "Final character target: friendly 2.6-head-tall chibi hard-surface suit, production topology, PBR textures.\n"
        "The oversized hood and skull mask define the silhouette; do not revert to adult athletic proportions.\n"
        "Do not export 00_REFERENCES. Keep weapons separate in 20_EQUIPMENT.\n"
        "The final skeleton will be retargeted against the Unreal mannequin before animation work.\n"
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), compress=True)
    print(f"Created Blender workfile: {OUTPUT}")


if __name__ == "__main__":
    build()
