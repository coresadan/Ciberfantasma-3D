"""Generate all nine playable campaign maps from the original Canvas level data."""

import json
import os
import unreal


PIXEL_TO_CM = 2.0
FLOOR_Y = 630.0
PLAY_DEPTH_CM = 600.0
MAP_NAMES = (
    "Act01_Rooftops", "Act02_DataCenter", "Act03_ExecutiveCore",
    "Act04_MemoryGardens", "Act05_ConsensusFactory", "Act06_SingleArchive",
    "Act07_DeadIdeasAvenue", "Act08_SilenceOffice", "Act09_DirectorOffice",
)
ENEMY_KIND = {
    "bot": 0, "drone": 1, "boss": 2, "crawler": 3, "harvester": 4,
    "boss2": 5, "enforcer": 6, "auditor": 7, "director": 8,
}
ENEMY_HEIGHT = {
    "bot": 60, "drone": 62, "boss": 135, "crawler": 60, "harvester": 70,
    "boss2": 150, "enforcer": 102, "auditor": 104, "director": 190,
}
FLYING = {"drone", "harvester"}


def project_path(*parts):
    return os.path.join(unreal.Paths.project_dir(), *parts)


def load_data():
    with open(project_path("Design", "campaign_levels.json"), "r", encoding="utf-8") as handle:
        return json.load(handle)["levels"]


def load_native_class(name):
    actor_class = unreal.load_class(None, f"/Script/Ciberfantasma3D.{name}")
    if not actor_class:
        raise RuntimeError(f"Native class unavailable: {name}")
    return actor_class


def source_to_world(x, y, z_offset=0.0):
    return unreal.Vector(x * PIXEL_TO_CM, 0.0, (FLOOR_Y - y) * PIXEL_TO_CM + z_offset)


def create_material(name, color, metallic=0.0, roughness=0.55, emissive=0.0):
    package = "/Game/Campaign/Materials"
    asset_path = f"{package}/{name}"
    existing = unreal.load_asset(asset_path)
    if existing:
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, package, unreal.Material, unreal.MaterialFactoryNew()
    )
    color_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -80
    )
    color_node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(color_node, "", unreal.MaterialProperty.MP_BASE_COLOR)
    for value, y, prop in (
        (metallic, 30, unreal.MaterialProperty.MP_METALLIC),
        (roughness, 120, unreal.MaterialProperty.MP_ROUGHNESS),
    ):
        node = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant, -360, y)
        node.set_editor_property("r", value)
        unreal.MaterialEditingLibrary.connect_material_property(node, "", prop)
    if emissive:
        strength = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant, -360, -180)
        strength.set_editor_property("r", emissive)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionMultiply, -100, -120)
        unreal.MaterialEditingLibrary.connect_material_expressions(color_node, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def spawn_mesh(subsystem, mesh, material, label, location, scale, tag="", collision=True, cast_shadow=True):
    actor = subsystem.spawn_actor_from_class(unreal.StaticMeshActor, location)
    actor.set_actor_label(label)
    if tag:
        actor.set_editor_property("tags", [unreal.Name(tag)])
    actor.set_actor_scale3d(scale)
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    component.set_collision_enabled(
        unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION
    )
    component.set_editor_property("cast_shadow", cast_shadow)
    return actor


def build_world_art(actors, assets, palette, world_width, data, level_index):
    """Build three parallax layers and a modular rooftop kit without changing gameplay collision."""
    backdrop = unreal.Vector(world_width * 0.5, -2850.0, 760.0)
    spawn_mesh(actors, assets["cube"], palette["backdrop"], "NightBackdrop", backdrop,
               unreal.Vector((world_width + 1800.0) / 100.0, 3.0, 22.0),
               "CF_Environment", False, False)

    # Far silhouette layer establishes scale without competing with the playable lane.
    for index in range(28):
        width = 210.0 + (index % 5) * 58.0
        height = 430.0 + (index * 173 + level_index * 97) % 1050
        location = unreal.Vector((index + 0.25) * world_width / 28.0,
                                 -1750.0 - (index % 4) * 210.0, height * 0.5 - 150.0)
        spawn_mesh(actors, assets["cube"], palette["skyline"], f"FarSkyline_{index:02d}", location,
                   unreal.Vector(width / 100.0, 2.4 + index % 3, height / 100.0),
                   "CF_Background", False, False)

    # Mid-distance authored facades: edge trims, window bands, rooftop caps and antennas.
    for index in range(17):
        width = 330.0 + (index * 71 + level_index * 31) % 260
        height = 480.0 + (index * 137 + level_index * 83) % 720
        x = (index + 0.45) * world_width / 17.0
        depth = -690.0 - (index % 3) * 170.0
        base_z = -150.0
        spawn_mesh(actors, assets["cube"], palette["facade"], f"Facade_{index:02d}",
                   unreal.Vector(x, depth, base_z + height * 0.5),
                   unreal.Vector(width / 100.0, 2.25, height / 100.0),
                   "CF_Environment", False, True)
        for side in (-1.0, 1.0):
            spawn_mesh(actors, assets["cube"], palette["edge"], f"FacadeEdge_{index:02d}_{int(side)}",
                       unreal.Vector(x + side * (width * 0.5 - 10.0), depth + 230.0, base_z + height * 0.53),
                       unreal.Vector(0.08, 0.05, height * 0.92 / 100.0),
                       "CF_Environment", False, False)
        for row in range(3):
            window_z = base_z + height * (0.24 + row * 0.22)
            window_material = palette["window"] if (index + row) % 3 else palette["accent"]
            spawn_mesh(actors, assets["cube"], window_material, f"WindowBand_{index:02d}_{row}",
                       unreal.Vector(x, depth + 232.0, window_z),
                       unreal.Vector(width * 0.68 / 100.0, 0.045, 0.055),
                       "CF_Environment", False, False)
        spawn_mesh(actors, assets["cube"], palette["metal"], f"RoofCap_{index:02d}",
                   unreal.Vector(x, depth, base_z + height + 18.0),
                   unreal.Vector(width * 0.82 / 100.0, 2.5, 0.18),
                   "CF_Environment", False, True)
        if index % 2 == 0:
            spawn_mesh(actors, assets["cube"], palette["edge"], f"Antenna_{index:02d}",
                       unreal.Vector(x + width * 0.22, depth, base_z + height + 105.0),
                       unreal.Vector(0.045, 0.045, 1.8),
                       "CF_Environment", False, False)

    # Near rooftop dressing sits just behind the gameplay lane and preserves all original collisions.
    decorated = 0
    for index, (x, y, width, height) in enumerate(data["platforms"]):
        if width < 260 or index % 2:
            continue
        top_z = (FLOOR_Y - y) * PIXEL_TO_CM
        prop_x = (x + width * (0.68 if index % 4 else 0.32)) * PIXEL_TO_CM
        spawn_mesh(actors, assets["cube"], palette["metal"], f"HVAC_{index:02d}",
                   unreal.Vector(prop_x, -365.0, top_z + 34.0), unreal.Vector(0.72, 1.25, 0.54),
                   "CF_Environment", False, True)
        spawn_mesh(actors, assets["cube"], palette["edge"], f"HVACGlow_{index:02d}",
                   unreal.Vector(prop_x, -300.0, top_z + 43.0), unreal.Vector(0.42, 0.035, 0.045),
                   "CF_Environment", False, False)
        if width >= 430:
            rail_x = (x + width * 0.5) * PIXEL_TO_CM
            rail_width = min(width * PIXEL_TO_CM * 0.62, 620.0)
            spawn_mesh(actors, assets["cube"], palette["metal"], f"RailTop_{index:02d}",
                       unreal.Vector(rail_x, -326.0, top_z + 88.0),
                       unreal.Vector(rail_width / 100.0, 0.035, 0.045),
                       "CF_Environment", False, True)
            for post in (-0.46, 0.0, 0.46):
                spawn_mesh(actors, assets["cube"], palette["metal"],
                           f"RailPost_{index:02d}_{int((post + 0.5) * 100)}",
                           unreal.Vector(rail_x + rail_width * post, -326.0, top_z + 47.0),
                           unreal.Vector(0.04, 0.04, 0.78), "CF_Environment", False, True)
        decorated += 1
        if decorated >= 12:
            break


def build_map(level_index, data, classes, assets, materials):
    map_path = f"/Game/Maps/{MAP_NAMES[level_index]}"
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level_subsystem.load_level(map_path):
            raise RuntimeError(f"Could not load {map_path}")
        existing = actors.get_all_level_actors()
        if existing and not actors.destroy_actors(existing):
            raise RuntimeError(f"Could not clear {map_path}")
    elif not level_subsystem.new_level(map_path):
        raise RuntimeError(f"Could not create {map_path}")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    world.get_world_settings().set_editor_property("default_game_mode", classes["game_mode"])
    theme = data.get("theme", "city")
    palette = materials[theme]
    platform_mat = palette["platform"]
    trim_mat = palette["trim"]

    for index, (x, y, width, height) in enumerate(data["platforms"]):
        location = source_to_world(x + width * 0.5, y + height * 0.5)
        scale = unreal.Vector(width * PIXEL_TO_CM / 100.0, PLAY_DEPTH_CM / 100.0, height * PIXEL_TO_CM / 100.0)
        spawn_mesh(actors, assets["cube"], platform_mat, f"Platform_{index:02d}", location, scale, "CF_Platform")
        trim_location = source_to_world(x + width * 0.5, y - 2.5)
        trim_location.y = PLAY_DEPTH_CM * 0.5 + 7.0
        trim_scale = unreal.Vector(width * PIXEL_TO_CM / 100.0, 0.14, 0.1)
        spawn_mesh(actors, assets["cube"], trim_mat, f"PlatformTrim_{index:02d}", trim_location, trim_scale, "CF_Trim")

    for index, values in enumerate(data.get("moving", [])):
        x, y, width, height, mode, movement_range = values
        platform = actors.spawn_actor_from_class(classes["moving"], source_to_world(x + width * 0.5, y + height * 0.5))
        platform.set_actor_label(f"MovingPlatform_{index:02d}")
        platform.set_actor_scale3d(unreal.Vector(width * PIXEL_TO_CM / 100.0, PLAY_DEPTH_CM / 100.0, height * PIXEL_TO_CM / 100.0))
        platform.set_editor_property("horizontal", mode == "h")
        platform.set_editor_property("movement_range", movement_range * PIXEL_TO_CM)
        platform.set_editor_property("phase_offset", index * 1.7)

    for index, values in enumerate(data.get("phase", [])):
        x, y, width, height, phase = values
        platform = actors.spawn_actor_from_class(classes["moving"], source_to_world(x + width * 0.5, y + height * 0.5))
        platform.set_actor_label(f"PhasePlatform_{index:02d}")
        platform.set_actor_scale3d(unreal.Vector(width * PIXEL_TO_CM / 100.0, PLAY_DEPTH_CM / 100.0, height * PIXEL_TO_CM / 100.0))
        platform.set_editor_property("phase_platform", True)
        platform.set_editor_property("phase_offset", phase)

    for index, values in enumerate(data["hazards"]):
        x, y, width, height = values[:4]
        hazard = actors.spawn_actor_from_class(classes["hazard"], source_to_world(x + width * 0.5, y + height * 0.5))
        hazard.set_actor_label(f"Hazard_{index:02d}_{values[4] if len(values) > 4 else 'spikes'}")
        hazard.set_actor_scale3d(unreal.Vector(width * PIXEL_TO_CM / 100.0, 2.0, height * PIXEL_TO_CM / 100.0))

    for index, (x, y) in enumerate(data["shards"]):
        shard = actors.spawn_actor_from_class(classes["shard"], source_to_world(x + 17.0, y + 20.0))
        shard.set_actor_label(f"Shard_{index:02d}")

    for index, (x, y) in enumerate(data["terminals"]):
        terminal = actors.spawn_actor_from_class(classes["terminal"], source_to_world(x + 24.0, y + 31.0))
        terminal.set_actor_label(f"Terminal_{index:02d}")

    for index, (x, y, enemy_type) in enumerate(data["enemies"]):
        height = ENEMY_HEIGHT[enemy_type]
        if enemy_type in FLYING:
            location = source_to_world(x + 34.0, y + height * 0.5)
        else:
            foot_z = (FLOOR_Y - (y + height)) * PIXEL_TO_CM
            location = unreal.Vector((x + 34.0) * PIXEL_TO_CM, 0.0, foot_z + 70.0)
        enemy = actors.spawn_actor_from_class(classes["enemy"], location)
        enemy.set_actor_label(f"Enemy_{enemy_type}_{index:02d}")
        enemy.set_editor_property("enemy_kind", ENEMY_KIND[enemy_type])

    portal_x, portal_y = data["portal"]
    portal = actors.spawn_actor_from_class(classes["portal"], source_to_world(portal_x + 36.0, portal_y + 68.0))
    portal.set_actor_label("ExitPortal")
    portal.set_editor_property("level_index", level_index)
    portal.set_editor_property("level_name", data["name"])
    portal.set_editor_property("level_title", data["title"])

    world_width = data["width"] * PIXEL_TO_CM
    build_world_art(actors, assets, palette, world_width, data, level_index)

    spawn_x, spawn_y = data["spawn"]
    spawn_foot_z = (FLOOR_Y - (spawn_y + 96.0)) * PIXEL_TO_CM
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(spawn_x * PIXEL_TO_CM, 0.0, max(92.0, spawn_foot_z + 92.0)))
    start.set_actor_label(f"PlayerStart_{level_index + 1:02d}")

    directional = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 1500.0), unreal.Rotator(-35.0, -25.0, 0.0))
    directional.set_actor_label("KeyLight")
    directional.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    directional.light_component.set_editor_property("intensity", 0.78)
    directional.light_component.set_editor_property("light_color", unreal.Color(186, 215, 255, 255))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector())
    sky.set_actor_label("SkyLight")
    sky.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.2)
    accent_colors = {
        "city": unreal.Color(235, 35, 255, 255),
        "consensus": unreal.Color(142, 72, 255, 255),
        "dominion": unreal.Color(255, 55, 25, 255),
    }
    for index, x in enumerate(range(350, int(world_width), 1400)):
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(float(x), 260.0, 430.0))
        light.set_actor_label(f"GameplayFill_{index:02d}")
        light.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("intensity", 95.0)
        light.light_component.set_editor_property("attenuation_radius", 1850.0)
        light.light_component.set_editor_property("light_color", unreal.Color(165, 205, 255, 255))
        light.light_component.set_editor_property("cast_shadows", False)
    for index, x in enumerate(range(700, int(world_width), 1900)):
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(float(x), -260.0, 330.0))
        light.set_actor_label(f"NeonRim_{index:02d}")
        light.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("intensity", 80.0)
        light.light_component.set_editor_property("attenuation_radius", 1050.0)
        light.light_component.set_editor_property("light_color", accent_colors[theme])
        light.light_component.set_editor_property("cast_shadows", False)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"Built {map_path}: {len(data['platforms'])} platforms, {len(data['enemies'])} enemies")


def main():
    levels = load_data()
    if len(levels) != 9:
        raise RuntimeError(f"Expected 9 levels, found {len(levels)}")
    classes = {
        "game_mode": load_native_class("CFGameMode"), "moving": load_native_class("CFMovingPlatform"),
        "hazard": load_native_class("CFHazard"), "shard": load_native_class("CFShard"),
        "terminal": load_native_class("CFTerminal"), "enemy": load_native_class("CFPatrolEnemy"),
        "portal": load_native_class("CFExitPortal"),
    }
    assets = {"cube": unreal.load_asset("/Engine/BasicShapes/Cube.Cube")}
    materials = {
        "city": {
            "platform": create_material("M_CityPlatform_Pro2", (0.008, 0.019, 0.032), 0.62, 0.38),
            "trim": create_material("M_CityTrim_Pro2", (0.002, 0.075, 0.14), 0.28, 0.28, 0.32),
            "skyline": create_material("M_CitySkyline_Pro2", (0.002, 0.006, 0.016), 0.12, 0.82),
            "facade": create_material("M_CityFacade_Pro2", (0.006, 0.013, 0.024), 0.48, 0.5),
            "window": create_material("M_CityWindow_Pro2", (0.003, 0.07, 0.15), 0.05, 0.24, 0.65),
            "accent": create_material("M_CityAccent_Pro2", (0.15, 0.002, 0.11), 0.08, 0.22, 0.82),
            "edge": create_material("M_CityEdge_Pro2", (0.003, 0.065, 0.11), 0.36, 0.3, 0.28),
            "metal": create_material("M_CityMetal_Pro2", (0.028, 0.04, 0.052), 0.78, 0.32),
            "backdrop": create_material("M_CityBackdrop_Pro2", (0.001, 0.0025, 0.008), 0.0, 1.0, 0.025),
        },
        "consensus": {
            "platform": create_material("M_ConsensusPlatform_Pro2", (0.018, 0.014, 0.052), 0.48, 0.38),
            "trim": create_material("M_ConsensusTrim_Pro2", (0.07, 0.012, 0.14), 0.2, 0.26, 0.38),
            "skyline": create_material("M_ConsensusSkyline_Pro2", (0.008, 0.005, 0.026), 0.08, 0.82),
            "facade": create_material("M_ConsensusFacade_Pro2", (0.017, 0.012, 0.045), 0.42, 0.44),
            "window": create_material("M_ConsensusWindow_Pro2", (0.035, 0.11, 0.16), 0.08, 0.2, 0.58),
            "accent": create_material("M_ConsensusAccent_Pro2", (0.13, 0.035, 0.22), 0.06, 0.22, 0.78),
            "edge": create_material("M_ConsensusEdge_Pro2", (0.09, 0.032, 0.17), 0.32, 0.28, 0.32),
            "metal": create_material("M_ConsensusMetal_Pro2", (0.09, 0.075, 0.14), 0.72, 0.28),
            "backdrop": create_material("M_ConsensusBackdrop_Pro2", (0.004, 0.002, 0.015), 0.0, 1.0, 0.025),
        },
        "dominion": {
            "platform": create_material("M_DominionPlatform_Pro2", (0.036, 0.011, 0.008), 0.64, 0.38),
            "trim": create_material("M_DominionTrim_Pro2", (0.15, 0.005, 0.002), 0.2, 0.26, 0.38),
            "skyline": create_material("M_DominionSkyline_Pro2", (0.017, 0.003, 0.002), 0.1, 0.84),
            "facade": create_material("M_DominionFacade_Pro2", (0.03, 0.009, 0.007), 0.52, 0.46),
            "window": create_material("M_DominionWindow_Pro2", (0.17, 0.045, 0.008), 0.08, 0.22, 0.62),
            "accent": create_material("M_DominionAccent_Pro2", (0.19, 0.004, 0.002), 0.12, 0.2, 0.86),
            "edge": create_material("M_DominionEdge_Pro2", (0.11, 0.018, 0.005), 0.42, 0.3, 0.3),
            "metal": create_material("M_DominionMetal_Pro2", (0.095, 0.052, 0.028), 0.82, 0.3),
            "backdrop": create_material("M_DominionBackdrop_Pro2", (0.008, 0.0015, 0.001), 0.0, 1.0, 0.022),
        },
    }
    for index, data in enumerate(levels):
        build_map(index, data, classes, assets, materials)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(f"/Game/Maps/{MAP_NAMES[0]}")
    unreal.log("Nine-act Ciberfantasma campaign generated successfully")


if __name__ == "__main__":
    main()
