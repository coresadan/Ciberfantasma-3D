"""Replace only generated environment art with the authored modular V3 pass.

Gameplay actors and collision stay untouched.  The script is deliberately
idempotent: every actor it owns carries CF_Environment, CF_Background or
CF_ArtPass3, so a later art pass can be rebuilt safely.
"""

import random

import unreal

from build_campaign import FLOOR_Y, MAP_NAMES, PIXEL_TO_CM, create_material, load_data, spawn_mesh


ART_TAGS = {"CF_Environment", "CF_Background", "CF_ArtPass3"}
LIGHT_PREFIXES = ("KeyLight", "SkyLight", "GameplayFill_", "NeonRim_", "ArtV3_")


THEME_COLORS = {
    "city": {
        "surface": ((0.022, 0.042, 0.068), 0.72, 0.32, 0.0),
        "fascia": ((0.009, 0.021, 0.038), 0.58, 0.43, 0.0),
        "metal": ((0.075, 0.105, 0.135), 0.82, 0.26, 0.0),
        "dark": ((0.003, 0.008, 0.018), 0.18, 0.76, 0.0),
        "window": ((0.002, 0.16, 0.34), 0.04, 0.20, 5.0),
        "accent": ((0.32, 0.002, 0.25), 0.03, 0.22, 5.5),
        "utility": ((0.38, 0.19, 0.012), 0.55, 0.34, 1.6),
        "haze": ((0.003, 0.010, 0.026), 0.0, 1.0, 0.12),
        "key": unreal.Color(172, 210, 255, 255),
        "fill": unreal.Color(90, 176, 255, 255),
        "rim": unreal.Color(255, 34, 220, 255),
        "fog": unreal.LinearColor(0.006, 0.018, 0.040, 1.0),
    },
    "consensus": {
        "surface": ((0.052, 0.044, 0.105), 0.62, 0.31, 0.0),
        "fascia": ((0.018, 0.012, 0.052), 0.46, 0.42, 0.0),
        "metal": ((0.16, 0.13, 0.22), 0.76, 0.25, 0.0),
        "dark": ((0.009, 0.005, 0.025), 0.14, 0.78, 0.0),
        "window": ((0.018, 0.16, 0.24), 0.03, 0.18, 4.2),
        "accent": ((0.20, 0.035, 0.48), 0.03, 0.20, 5.0),
        "utility": ((0.48, 0.31, 0.035), 0.62, 0.28, 1.7),
        "haze": ((0.012, 0.007, 0.038), 0.0, 1.0, 0.11),
        "key": unreal.Color(205, 198, 255, 255),
        "fill": unreal.Color(115, 155, 255, 255),
        "rim": unreal.Color(172, 74, 255, 255),
        "fog": unreal.LinearColor(0.020, 0.010, 0.050, 1.0),
    },
    "dominion": {
        "surface": ((0.082, 0.030, 0.018), 0.72, 0.34, 0.0),
        "fascia": ((0.030, 0.008, 0.005), 0.55, 0.44, 0.0),
        "metal": ((0.18, 0.095, 0.045), 0.84, 0.27, 0.0),
        "dark": ((0.015, 0.002, 0.002), 0.18, 0.80, 0.0),
        "window": ((0.40, 0.065, 0.008), 0.04, 0.20, 4.8),
        "accent": ((0.48, 0.002, 0.002), 0.04, 0.18, 6.0),
        "utility": ((0.42, 0.25, 0.025), 0.68, 0.30, 1.8),
        "haze": ((0.026, 0.003, 0.002), 0.0, 1.0, 0.10),
        "key": unreal.Color(255, 194, 154, 255),
        "fill": unreal.Color(255, 112, 70, 255),
        "rim": unreal.Color(255, 25, 15, 255),
        "fog": unreal.LinearColor(0.050, 0.008, 0.004, 1.0),
    },
}


def make_materials():
    result = {}
    for theme, settings in THEME_COLORS.items():
        title = theme.capitalize()
        result[theme] = {
            role: create_material(
                f"M_{title}_{role.capitalize()}_ArtV3", *settings[role]
            )
            for role in ("surface", "fascia", "metal", "dark", "window", "accent", "utility", "haze")
        }
    return result


def actor_tags(actor):
    return {str(tag) for tag in actor.get_editor_property("tags")}


def remove_owned_art(actors):
    doomed = []
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if actor_tags(actor) & ART_TAGS or label.startswith(LIGHT_PREFIXES):
            doomed.append(actor)
    if doomed and not actors.destroy_actors(doomed):
        raise RuntimeError("Could not remove the previous generated art pass")


def spawn(actors, mesh, material, label, location, scale, tag="CF_ArtPass3", rotation=None,
          shadow=True):
    actor = spawn_mesh(
        actors, mesh, material, label, location, scale, tag, collision=False, cast_shadow=shadow
    )
    if rotation:
        actor.set_actor_rotation(rotation, False)
    return actor


def build_far_layer(actors, meshes, palette, world_width, rng, level_index):
    # Layered haze bands stop the skyline falling into an undifferentiated black void.
    for band in range(3):
        spawn(
            actors, meshes["cube"], palette["haze"], f"ArtV3_HazeBand_{band}",
            unreal.Vector(world_width * 0.5, -3300.0 - band * 180.0, 280.0 + band * 520.0),
            unreal.Vector((world_width + 2200.0) / 100.0, 2.5, 6.0), "CF_Background", None, False,
        )

    for index in range(30):
        width = rng.uniform(180.0, 410.0)
        height = rng.uniform(360.0, 1320.0)
        x = (index + 0.2) * world_width / 29.5
        depth = -2050.0 - (index % 5) * 155.0
        spawn(actors, meshes["cube"], palette["dark"], f"ArtV3_FarTower_{index:02d}",
              unreal.Vector(x, depth, height * 0.5 - 180.0),
              unreal.Vector(width / 100.0, rng.uniform(1.8, 3.8), height / 100.0),
              "CF_Background", None, False)
        # Sparse vertical light channels create scale without visual noise.
        if index % 2 == level_index % 2:
            spawn(actors, meshes["cube"], palette["window"], f"ArtV3_FarStrip_{index:02d}",
                  unreal.Vector(x + width * 0.28, depth + 200.0, height * 0.48 - 120.0),
                  unreal.Vector(0.025, 0.025, height * 0.34 / 100.0),
                  "CF_Background", None, False)

    # Distant traffic gives the skyline a lived-in horizontal rhythm.
    for index in range(10):
        x = world_width * (0.06 + index * 0.095)
        z = 260.0 + (index * 137 + level_index * 61) % 760
        mat = palette["accent"] if index % 3 == 0 else palette["window"]
        spawn(actors, meshes["cube"], mat, f"ArtV3_Traffic_{index:02d}",
              unreal.Vector(x, -1500.0, z), unreal.Vector(0.75, 0.018, 0.012),
              "CF_Background", None, False)


def build_facades(actors, meshes, palette, world_width, rng, level_index):
    for index in range(15):
        width = rng.uniform(350.0, 590.0)
        height = rng.uniform(520.0, 1180.0)
        x = (index + 0.42) * world_width / 15.0
        depth = -760.0 - (index % 3) * 145.0
        base_z = -190.0
        body_mat = palette["fascia"] if index % 4 else palette["surface"]
        spawn(actors, meshes["cube"], body_mat, f"ArtV3_Facade_{index:02d}",
              unreal.Vector(x, depth, base_z + height * 0.5),
              unreal.Vector(width / 100.0, 2.6, height / 100.0))

        # Recessed central bay and strong corner columns create true depth cues.
        spawn(actors, meshes["cube"], palette["dark"], f"ArtV3_FacadeBay_{index:02d}",
              unreal.Vector(x, depth + 268.0, base_z + height * 0.52),
              unreal.Vector(width * 0.66 / 100.0, 0.16, height * 0.82 / 100.0), shadow=False)
        for side in (-1.0, 1.0):
            spawn(actors, meshes["cube"], palette["metal"],
                  f"ArtV3_FacadeColumn_{index:02d}_{int(side)}",
                  unreal.Vector(x + side * width * 0.43, depth + 276.0, base_z + height * 0.50),
                  unreal.Vector(0.10, 0.10, height * 0.93 / 100.0))

        columns = 2 + index % 3
        rows = 4 + index % 4
        for row in range(rows):
            for column in range(columns):
                lit = (row * 5 + column * 3 + index + level_index) % 7 not in (0, 1)
                if not lit:
                    continue
                wx = x + (column - (columns - 1) * 0.5) * width * 0.18
                wz = base_z + height * (0.18 + row * 0.66 / max(rows - 1, 1))
                mat = palette["accent"] if (row + column + index) % 11 == 0 else palette["window"]
                spawn(actors, meshes["cube"], mat,
                      f"ArtV3_Window_{index:02d}_{row}_{column}",
                      unreal.Vector(wx, depth + 288.0, wz),
                      unreal.Vector(width * 0.055 / 100.0, 0.022, 0.075), shadow=False)

        # Stepped crowns, roof machinery and antennas prevent copy-paste silhouettes.
        crown_width = width * (0.62 if index % 2 else 0.82)
        spawn(actors, meshes["cube"], palette["metal"], f"ArtV3_Crown_{index:02d}",
              unreal.Vector(x, depth, base_z + height + 24.0),
              unreal.Vector(crown_width / 100.0, 2.85, 0.22))
        if index % 3 == 0:
            spawn(actors, meshes["cube"], palette["accent"], f"ArtV3_Billboard_{index:02d}",
                  unreal.Vector(x, depth + 300.0, base_z + height * 0.72),
                  unreal.Vector(width * 0.24 / 100.0, 0.025, 0.34), shadow=False)
            spawn(actors, meshes["cube"], palette["metal"], f"ArtV3_BillboardFrame_{index:02d}",
                  unreal.Vector(x, depth + 296.0, base_z + height * 0.72),
                  unreal.Vector(width * 0.29 / 100.0, 0.035, 0.40))
        if index % 2 == 0:
            antenna_height = 105.0 + (index % 4) * 35.0
            spawn(actors, meshes["cylinder"], palette["metal"], f"ArtV3_Antenna_{index:02d}",
                  unreal.Vector(x + width * 0.20, depth, base_z + height + antenna_height * 0.5),
                  unreal.Vector(0.045, 0.045, antenna_height / 100.0))
            spawn(actors, meshes["sphere"], palette["accent"], f"ArtV3_Beacon_{index:02d}",
                  unreal.Vector(x + width * 0.20, depth, base_z + height + antenna_height),
                  unreal.Vector(0.055, 0.055, 0.055), shadow=False)


def build_platform_art(actors, meshes, palette, data, existing):
    for index, (x, y, width, height) in enumerate(data["platforms"]):
        platform = existing.get(f"Platform_{index:02d}")
        if platform:
            platform.static_mesh_component.set_material(0, palette["surface"])
        trim = existing.get(f"PlatformTrim_{index:02d}")
        if trim:
            trim.static_mesh_component.set_material(0, palette["window"])

        world_x = (x + width * 0.5) * PIXEL_TO_CM
        world_width = width * PIXEL_TO_CM
        top_z = (FLOOR_Y - y) * PIXEL_TO_CM
        world_height = height * PIXEL_TO_CM
        fascia_height = min(max(world_height * 0.55, 22.0), 78.0)
        fascia_z = top_z - fascia_height * 0.5 - 4.0
        spawn(actors, meshes["cube"], palette["fascia"], f"ArtV3_Fascia_{index:02d}",
              unreal.Vector(world_x, 308.0, fascia_z),
              unreal.Vector(world_width * 0.96 / 100.0, 0.075, fascia_height / 100.0))
        spawn(actors, meshes["cube"], palette["metal"], f"ArtV3_FasciaLip_{index:02d}",
              unreal.Vector(world_x, 316.0, top_z - 4.0),
              unreal.Vector(world_width / 100.0, 0.065, 0.055))

        brace_count = max(2, min(7, int(world_width / 260.0)))
        for brace in range(brace_count):
            bx = world_x + world_width * ((brace + 0.5) / brace_count - 0.5) * 0.90
            spawn(actors, meshes["cube"], palette["metal"],
                  f"ArtV3_FasciaBrace_{index:02d}_{brace}",
                  unreal.Vector(bx, 318.0, fascia_z),
                  unreal.Vector(0.035, 0.045, fascia_height * 0.78 / 100.0))

        if index % 2 == 0 and world_width > 330.0:
            spawn(actors, meshes["cube"], palette["utility"],
                  f"ArtV3_WarningPanel_{index:02d}",
                  unreal.Vector(world_x + world_width * 0.28, 323.0, fascia_z),
                  unreal.Vector(0.20, 0.018, 0.035), shadow=False)

    # Composed rooftop props sit behind the gameplay plane and never collide.
    prop_count = 0
    for index, (x, y, width, _height) in enumerate(data["platforms"]):
        if width < 430 or index % 2:
            continue
        top_z = (FLOOR_Y - y) * PIXEL_TO_CM
        prop_x = (x + width * (0.28 if index % 4 else 0.72)) * PIXEL_TO_CM
        spawn(actors, meshes["cube"], palette["dark"], f"ArtV3_HVACBase_{index:02d}",
              unreal.Vector(prop_x, -235.0, top_z + 10.0), unreal.Vector(0.90, 1.28, 0.20))
        spawn(actors, meshes["cube"], palette["metal"], f"ArtV3_HVACBody_{index:02d}",
              unreal.Vector(prop_x, -235.0, top_z + 45.0), unreal.Vector(0.78, 1.10, 0.52))
        for vent in (-1, 0, 1):
            spawn(actors, meshes["cube"], palette["fascia"],
                  f"ArtV3_HVACVent_{index:02d}_{vent}",
                  unreal.Vector(prop_x + vent * 22.0, -176.0, top_z + 46.0),
                  unreal.Vector(0.15, 0.025, 0.035), shadow=False)
        spawn(actors, meshes["cylinder"], palette["dark"], f"ArtV3_HVACFan_{index:02d}",
              unreal.Vector(prop_x, -174.0, top_z + 45.0), unreal.Vector(0.26, 0.08, 0.26),
              rotation=unreal.Rotator(90.0, 0.0, 0.0))
        spawn(actors, meshes["sphere"], palette["window"], f"ArtV3_HVACCore_{index:02d}",
              unreal.Vector(prop_x, -165.0, top_z + 45.0), unreal.Vector(0.055, 0.025, 0.055),
              shadow=False)

        rail_x = (x + width * 0.56) * PIXEL_TO_CM
        rail_width = min(width * PIXEL_TO_CM * 0.48, 560.0)
        spawn(actors, meshes["cube"], palette["metal"], f"ArtV3_RailTop_{index:02d}",
              unreal.Vector(rail_x, -305.0, top_z + 92.0),
              unreal.Vector(rail_width / 100.0, 0.030, 0.035))
        for post in (-0.48, 0.0, 0.48):
            spawn(actors, meshes["cube"], palette["metal"],
                  f"ArtV3_RailPost_{index:02d}_{int((post + 0.5) * 100)}",
                  unreal.Vector(rail_x + rail_width * post, -305.0, top_z + 48.0),
                  unreal.Vector(0.030, 0.030, 0.84))
        prop_count += 1
        if prop_count >= 7:
            break


def replace_lighting(actors, theme_settings, world_width):
    directional = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0.0, 0.0, 1500.0), unreal.Rotator(-42.0, -28.0, 0.0)
    )
    directional.set_actor_label("ArtV3_KeyLight")
    directional.set_editor_property("tags", [unreal.Name("CF_ArtPass3")])
    directional.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    directional.light_component.set_editor_property("intensity", 1.02)
    directional.light_component.set_editor_property("light_color", theme_settings["key"])

    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector())
    sky.set_actor_label("ArtV3_SkyLight")
    sky.set_editor_property("tags", [unreal.Name("CF_ArtPass3")])
    sky.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.28)

    for index, x in enumerate(range(280, int(world_width), 1050)):
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(float(x), 220.0, 260.0))
        light.set_actor_label(f"ArtV3_GameplayFill_{index:02d}")
        light.set_editor_property("tags", [unreal.Name("CF_ArtPass3")])
        light.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("intensity", 185.0)
        light.light_component.set_editor_property("attenuation_radius", 1450.0)
        light.light_component.set_editor_property("light_color", theme_settings["fill"])
        light.light_component.set_editor_property("cast_shadows", False)

    for index, x in enumerate(range(720, int(world_width), 1650)):
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(float(x), -310.0, 390.0))
        light.set_actor_label(f"ArtV3_NeonRim_{index:02d}")
        light.set_editor_property("tags", [unreal.Name("CF_ArtPass3")])
        light.root_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("intensity", 135.0)
        light.light_component.set_editor_property("attenuation_radius", 1180.0)
        light.light_component.set_editor_property("light_color", theme_settings["rim"])
        light.light_component.set_editor_property("cast_shadows", False)

    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0.0, 0.0, -180.0))
    fog.set_actor_label("ArtV3_HeightFog")
    fog.set_editor_property("tags", [unreal.Name("CF_ArtPass3")])
    component = fog.component
    component.set_editor_property("fog_density", 0.006)
    component.set_editor_property("fog_height_falloff", 0.32)
    component.set_editor_property("fog_inscattering_luminance", theme_settings["fog"])
    component.set_editor_property("start_distance", 650.0)


def upgrade_map(level_index, data, meshes, materials):
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    map_path = f"/Game/Maps/{MAP_NAMES[level_index]}"
    if not level_subsystem.load_level(map_path):
        raise RuntimeError(f"Could not load {map_path}")

    existing = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    remove_owned_art(actors)
    theme = data.get("theme", "city")
    palette = materials[theme]
    settings = THEME_COLORS[theme]
    world_width = data["width"] * PIXEL_TO_CM
    rng = random.Random(0xCF30 + level_index * 7919)

    # Re-read gameplay actors after deleting only the old art layer.
    existing = {actor.get_actor_label(): actor for actor in actors.get_all_level_actors()}
    build_far_layer(actors, meshes, palette, world_width, rng, level_index)
    build_facades(actors, meshes, palette, world_width, rng, level_index)
    build_platform_art(actors, meshes, palette, data, existing)
    replace_lighting(actors, settings, world_width)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)

    owned = sum(1 for actor in actors.get_all_level_actors() if actor_tags(actor) & ART_TAGS)
    unreal.log(f"ART_V3 built {map_path}: {owned} owned art actors, gameplay preserved")


def main():
    meshes = {
        "cube": unreal.load_asset("/Engine/BasicShapes/Cube.Cube"),
        "cylinder": unreal.load_asset("/Engine/BasicShapes/Cylinder.Cylinder"),
        "sphere": unreal.load_asset("/Engine/BasicShapes/Sphere.Sphere"),
    }
    if not all(meshes.values()):
        raise RuntimeError("Engine basic shape kit is incomplete")
    materials = make_materials()
    for level_index, data in enumerate(load_data()):
        upgrade_map(level_index, data, meshes, materials)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(f"/Game/Maps/{MAP_NAMES[0]}")
    unreal.log("ART_V3 PASS: nine maps upgraded without rebuilding gameplay")


main()
