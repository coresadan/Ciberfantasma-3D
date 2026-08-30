"""Build and save the Act I 2.5D blockout inside the Unreal Editor."""

import json
import os
import unreal


MAP_PATH = "/Game/Maps/Act1_Blockout"
PIXEL_TO_CM = 2.0
FLOOR_Y = 630.0
PLAY_DEPTH_CM = 600.0


def project_path(*parts):
    return os.path.join(unreal.Paths.project_dir(), *parts)


def load_level_data():
    with open(project_path("Design", "act1_level.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)


def create_material(name, color, metallic=0.0, roughness=0.55, emissive=0.0):
    package_path = "/Game/Blockout/Materials"
    asset_path = f"{package_path}/{name}"
    existing = unreal.load_asset(asset_path)
    if existing:
        return existing

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    material = tools.create_asset(name, package_path, unreal.Material, unreal.MaterialFactoryNew())
    color_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -80
    )
    color_node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    metallic_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 30
    )
    metallic_node.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic_node, "", unreal.MaterialProperty.MP_METALLIC
    )

    roughness_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 120
    )
    roughness_node.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness_node, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    if emissive > 0.0:
        multiply = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -120, -120
        )
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -360, -180
        )
        strength.set_editor_property("r", emissive)
        unreal.MaterialEditingLibrary.connect_material_expressions(color_node, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def spawn_mesh(actor_subsystem, mesh, material, label, location, scale, tag):
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location)
    actor.set_actor_label(label)
    actor.set_editor_property("tags", [unreal.Name(tag)])
    actor.set_actor_scale3d(scale)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    return actor


def load_native_class(class_name):
    actor_class = unreal.load_class(None, f"/Script/Ciberfantasma3D.{class_name}")
    if not actor_class:
        raise RuntimeError(f"Native class is unavailable: {class_name}")
    return actor_class


def source_to_world(x, y, z_offset=0.0):
    return unreal.Vector(x * PIXEL_TO_CM, 0.0, (FLOOR_Y - y) * PIXEL_TO_CM + z_offset)


def build():
    data = load_level_data()
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Once the blockout is the startup map Unreal keeps references to its
    # package, so deleting and recreating the asset is unreliable. Rebuild the
    # contents in place instead; this also keeps the generator repeatable.
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level_subsystem.load_level(MAP_PATH):
            raise RuntimeError(f"Could not load existing map: {MAP_PATH}")
        existing_actors = actor_subsystem.get_all_level_actors()
        if existing_actors and not actor_subsystem.destroy_actors(existing_actors):
            raise RuntimeError(f"Could not clear existing map: {MAP_PATH}")
    elif not level_subsystem.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create map: {MAP_PATH}")

    cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
    sphere = unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere")
    cylinder = unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder")
    drone_mesh = unreal.load_asset("/Game/Art/Enemies/SM_PanopticonDrone_Chibi")
    shard_class = load_native_class("CFShard")
    hazard_class = load_native_class("CFHazard")
    enemy_class = load_native_class("CFPatrolEnemy")
    portal_class = load_native_class("CFExitPortal")
    game_mode_class = load_native_class("CFGameMode")

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    world_settings = world.get_world_settings()
    world_settings.set_editor_property("default_game_mode", game_mode_class)

    platform_mat = create_material("M_BlockoutPlatform_V3", (0.018, 0.045, 0.07), 0.42, 0.4)
    trim_mat = create_material("M_BlockoutTrim_V3", (0.008, 0.22, 0.055), 0.15, 0.35, 0.22)
    hazard_mat = create_material("M_BlockoutHazard_V3", (0.58, 0.01, 0.05), 0.08, 0.34, 0.8)
    cyan_mat = create_material("M_BlockoutCyan_V3", (0.008, 0.2, 0.36), 0.18, 0.32, 0.35)
    enemy_mat = create_material("M_BlockoutEnemy_V3", (0.42, 0.012, 0.16), 0.1, 0.42, 0.35)
    skyline_mat = create_material("M_BlockoutSkyline_V3", (0.008, 0.016, 0.03), 0.08, 0.76)

    for index, (x, y, width, height) in enumerate(data["platforms"]):
        location = source_to_world(x + width * 0.5, y + height * 0.5)
        scale = unreal.Vector(width * PIXEL_TO_CM / 100.0, PLAY_DEPTH_CM / 100.0, height * PIXEL_TO_CM / 100.0)
        spawn_mesh(actor_subsystem, cube, platform_mat, f"Platform_{index:02d}", location, scale, "CF_Platform")

        trim_location = source_to_world(x + width * 0.5, y - 2.5)
        trim_scale = unreal.Vector(width * PIXEL_TO_CM / 100.0, (PLAY_DEPTH_CM + 8.0) / 100.0, 5.0 * PIXEL_TO_CM / 100.0)
        spawn_mesh(actor_subsystem, cube, trim_mat, f"PlatformTrim_{index:02d}", trim_location, trim_scale, "CF_Trim")

    for index, (x, y, width, height) in enumerate(data["hazards"]):
        location = source_to_world(x + width * 0.5, y + height * 0.5)
        hazard = actor_subsystem.spawn_actor_from_class(hazard_class, location)
        hazard.set_actor_label(f"Hazard_{index:02d}")
        hazard.set_actor_scale3d(
            unreal.Vector(width * PIXEL_TO_CM / 100.0, 2.0, height * PIXEL_TO_CM / 100.0)
        )

    for index, (x, y) in enumerate(data["shards"]):
        location = source_to_world(x + 17.0, y + 20.0)
        shard = actor_subsystem.spawn_actor_from_class(shard_class, location)
        shard.set_actor_label(f"Shard_{index:02d}")

    for index, (x, y) in enumerate(data["terminals"]):
        location = source_to_world(x + 24.0, y + 31.0)
        spawn_mesh(actor_subsystem, cube, cyan_mat, f"Terminal_{index:02d}", location, unreal.Vector(0.48, 0.7, 0.62), "CF_Terminal")

    for index, (x, y, enemy_type) in enumerate(data["enemies"]):
        if enemy_type == "bot":
            location = source_to_world(x + 34.0, y + 60.0, 70.0)
            enemy = actor_subsystem.spawn_actor_from_class(enemy_class, location)
            enemy.set_actor_label(f"Enemy_{enemy_type}_{index:02d}")
        else:
            location = source_to_world(x + 34.0, y + 31.0)
            visual = drone_mesh if drone_mesh else cylinder
            scale = unreal.Vector(1.0, 1.0, 1.0) if drone_mesh else unreal.Vector(0.5, 0.5, 1.15)
            material = None if drone_mesh else enemy_mat
            spawn_mesh(actor_subsystem, visual, material, f"Enemy_{enemy_type}_{index:02d}", location, scale, "CF_EnemyMarker")

    portal_x, portal_y = data["portal"]
    portal_location = source_to_world(portal_x + 36.0, portal_y + 68.0)
    portal = actor_subsystem.spawn_actor_from_class(portal_class, portal_location)
    portal.set_actor_label("ExitPortal")

    world_width = data["world_width"] * PIXEL_TO_CM
    for index in range(32):
        width = 180.0 + (index % 5) * 55.0
        height = 500.0 + (index * 173) % 1100
        x = (index + 0.25) * world_width / 32.0
        # The side camera sits on +Y, so the skyline must remain on -Y.
        # Positive Y put these towers in front of the lens and caused the black screen.
        y = -900.0 - (index % 4) * 260.0
        location = unreal.Vector(x, y, height * 0.5 - 140.0)
        scale = unreal.Vector(width / 100.0, 2.2 + (index % 3), height / 100.0)
        spawn_mesh(actor_subsystem, cube, skyline_mat, f"Skyline_{index:02d}", location, scale, "CF_Background")

    spawn_x, _ = data["spawn"]
    player_start = actor_subsystem.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(spawn_x * PIXEL_TO_CM, 0.0, 260.0)
    )
    player_start.set_actor_label("PlayerStart_Act1")
    player_start.set_actor_rotation(unreal.Rotator(0.0, 0.0, 0.0), False)

    directional = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 1500.0), unreal.Rotator(-35.0, -25.0, 0.0)
    )
    directional.set_actor_label("KeyLight")
    directional.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    directional.light_component.set_editor_property("intensity", 3.5)

    sky = actor_subsystem.spawn_actor_from_class(unreal.SkyLight, unreal.Vector())
    sky.set_actor_label("SkyLight")
    sky.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.65)

    # Camera-side fill lights keep black armour readable without flattening it.
    for index, x in enumerate(range(350, int(world_width), 1200)):
        fill_light = actor_subsystem.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(float(x), 260.0, 430.0)
        )
        fill_light.set_actor_label(f"GameplayFill_{index:02d}")
        fill_light.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        fill_light.light_component.set_editor_property("intensity", 280.0)
        fill_light.light_component.set_editor_property("attenuation_radius", 1750.0)
        fill_light.light_component.set_editor_property("light_color", unreal.Color(165, 205, 255, 255))
        fill_light.light_component.set_editor_property("cast_shadows", False)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"Built {MAP_PATH} from Design/act1_level.json")


if __name__ == "__main__":
    build()
