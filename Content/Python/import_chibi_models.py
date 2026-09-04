"""Import the generated chibi FBX meshes and build their Unreal materials."""

from pathlib import Path
import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir())
FBX_ROOT = PROJECT_ROOT / "SourceAssets" / "FBX"
TEXTURE_ROOT = PROJECT_ROOT / "SourceAssets" / "Textures" / "Hero"
HERO_MATERIAL_VERSION = 12
LEGACY_MATERIAL_VERSION = 8
EFFECT_MATERIAL_VERSION = 9
MATERIAL_VERSION = HERO_MATERIAL_VERSION

HERO_MATERIAL_NAMES = (
    "M_CF_Hood",
    "M_CF_Undersuit",
    "M_CF_Armor",
    "M_CF_Bone",
    "M_CF_Green",
    "M_CF_Visor",
)

HERO_SURFACE_TEXTURES = {
    "M_CF_Hood": "Hood",
    "M_CF_Undersuit": "Undersuit",
    "M_CF_Armor": "Armor",
    "M_CF_Bone": "Bone",
}

IMPORTED_SURFACE_TEXTURES = {}

HERO_SPECULAR = {
    "M_CF_Hood": 0.24,
    "M_CF_Undersuit": 0.18,
    "M_CF_Armor": 0.50,
    "M_CF_Bone": 0.28,
    "M_CF_Green": 0.35,
    "M_CF_Visor": 0.70,
}

# Small view-dependent highlights separate the black silhouette without flattening
# it with constant emission. Green circuitry keeps its own stronger emissive pass.
HERO_RIM = {
    "M_CF_Hood": (0.012, 0.020, 0.032),
    "M_CF_Undersuit": (0.006, 0.011, 0.018),
    "M_CF_Armor": (0.045, 0.078, 0.125),
    "M_CF_Bone": (0.025, 0.035, 0.032),
    "M_CF_Visor": (0.004, 0.045, 0.038),
}

ASSETS = {
    "SM_Ciberfantasma_Chibi": "/Game/Art/Characters",
    "SM_LicenseWarden_Chibi": "/Game/Art/Enemies",
    "SM_PanopticonDrone_Chibi": "/Game/Art/Enemies",
    # New enemy types
    "SM_BotGround_Chibi": "/Game/Art/Enemies",
    "SM_Crawler_Chibi": "/Game/Art/Enemies",
    "SM_Harvester_Chibi": "/Game/Art/Enemies",
    "SM_Enforcer_Chibi": "/Game/Art/Enemies",
    "SM_Auditor_Chibi": "/Game/Art/Enemies",
    "SM_CEO9000_Chibi": "/Game/Art/Enemies",
    "SM_Director_Chibi": "/Game/Art/Enemies",
}

SKELETAL_ASSETS = {
    "SK_Ciberfantasma_Chibi_Pro": "/Game/Art/Characters",
}

ANIMATIONS = (
    "A_Ciberfantasma_Pro_Idle",
    "A_Ciberfantasma_Pro_RunStart",
    "A_Ciberfantasma_Pro_Run",
    "A_Ciberfantasma_Pro_RunStop",
    "A_Ciberfantasma_Pro_JumpStart",
    "A_Ciberfantasma_Pro_JumpRise",
    "A_Ciberfantasma_Pro_JumpFall",
    "A_Ciberfantasma_Pro_Land",
    "A_Ciberfantasma_Pro_Crouch",
    "A_Ciberfantasma_Pro_CrouchWalk",
    "A_Ciberfantasma_Pro_Fire",
    "A_Ciberfantasma_Pro_FireBack",
    "A_Ciberfantasma_Pro_Shield",
    "A_Ciberfantasma_Pro_Hit",
)

MATERIALS = {
    # Linear-space values calibrated against the fixed-exposure gameplay camera.
    # V12 uses authored packed RMA and tangent-normal maps for the four hero
    # surface families while preserving the near-black concept-art hierarchy.
    "M_CF_Hood": ((0.011, 0.017, 0.027), 0.0, 0.54, None),
    "M_CF_Undersuit": ((0.017, 0.024, 0.034), 0.0, 0.68, None),
    "M_CF_Armor": ((0.060, 0.073, 0.090), 0.78, 0.27, None),
    "M_CF_Bone": ((0.86, 0.89, 0.85), 0.02, 0.34, ((0.18, 0.20, 0.18), 0.16)),
    "M_CF_Green": ((0.002, 0.30, 0.008), 0.0, 0.25, ((0.0, 0.54, 0.009), 4.4)),
    "M_CF_Visor": ((0.0005, 0.001, 0.002), 0.0, 0.10, None),
    "M_Warden_Ivory": ((0.48, 0.44, 0.36), 0.7, 0.24, None),
    "M_Enemy_Dark": ((0.02, 0.028, 0.045), 0.8, 0.22, None),
    "M_Enemy_Red": ((0.5, 0.003, 0.015), 0.48, 0.16, ((1.0, 0.005, 0.02), 12.0)),
    "M_Drone_Silver": ((0.34, 0.39, 0.43), 0.88, 0.18, None),
    "M_Drone_Magenta": ((0.38, 0.003, 0.32), 0.45, 0.12, ((1.0, 0.01, 0.8), 14.0)),
    "M_Drone_Cyan": ((0.005, 0.25, 0.5), 0.4, 0.15, ((0.01, 0.65, 1.0), 10.0)),
    # Bot ground
    "M_Bot_Green": ((0.002, 0.32, 0.008), 0.12, 0.22, ((0.003, 0.72, 0.012), 8.0)),
    # Crawler
    "M_Crawler_Orange": ((0.5, 0.11, 0.001), 0.62, 0.2, ((1.0, 0.22, 0.003), 8.0)),
    "M_Crawler_Heavy": ((0.022, 0.028, 0.038), 0.85, 0.18, None),
    # Harvester
    "M_Harvester_Teal": ((0.002, 0.32, 0.3), 0.35, 0.15, ((0.004, 0.72, 0.65), 12.0)),
    "M_Harvester_Gold": ((0.38, 0.26, 0.014), 0.78, 0.2, None),
    # Enforcer
    "M_Enforcer_Blue": ((0.003, 0.045, 0.32), 0.25, 0.28, ((0.005, 0.07, 0.75), 7.0)),
    "M_Enforcer_Grey": ((0.14, 0.16, 0.18), 0.72, 0.24, None),
    # Auditor
    "M_Auditor_Yellow": ((0.45, 0.36, 0.001), 0.3, 0.2, ((0.9, 0.72, 0.003), 8.0)),
    "M_Auditor_White": ((0.65, 0.68, 0.72), 0.15, 0.35, None),
    # CEO-9000
    "M_CEO_Gold": ((0.55, 0.38, 0.014), 0.85, 0.16, ((1.0, 0.65, 0.025), 16.0)),
    "M_CEO_Dark": ((0.006, 0.006, 0.009), 0.92, 0.14, None),
    "M_CEO_Red": ((0.62, 0.002, 0.002), 0.35, 0.14, ((1.0, 0.005, 0.005), 18.0)),
    # Director
    "M_Director_White": ((0.72, 0.76, 0.8), 0.12, 0.28, None),
    "M_Director_Red": ((0.65, 0.002, 0.002), 0.2, 0.12, ((1.0, 0.004, 0.004), 20.0)),
    "M_Director_Black": ((0.003, 0.003, 0.005), 0.94, 0.12, None),
}


def import_hero_surface_textures():
    """Import deterministic Blender-authored PBR maps before building V12 materials."""
    destination = "/Game/Art/Textures/Hero"
    unreal.EditorAssetLibrary.make_directory(destination)
    for surface in sorted(set(HERO_SURFACE_TEXTURES.values())):
        for suffix in ("RMA", "Normal"):
            asset_name = f"T_CF_{surface}_{suffix}"
            filename = TEXTURE_ROOT / f"{asset_name}.png"
            if not filename.exists():
                raise RuntimeError(f"Missing generated hero texture: {filename}")
            task = unreal.AssetImportTask()
            task.set_editor_property("filename", str(filename))
            task.set_editor_property("destination_path", destination)
            task.set_editor_property("destination_name", asset_name)
            task.set_editor_property("automated", True)
            task.set_editor_property("replace_existing", True)
            task.set_editor_property("replace_existing_settings", True)
            task.set_editor_property("save", True)
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            texture = unreal.load_asset(f"{destination}/{asset_name}")
            if not texture:
                raise RuntimeError(f"Unreal did not import {asset_name}")
            texture.set_editor_property("srgb", False)
            if suffix == "Normal":
                texture.set_editor_property(
                    "compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP
                )
            else:
                texture.set_editor_property(
                    "compression_settings", unreal.TextureCompressionSettings.TC_MASKS
                )
            unreal.EditorAssetLibrary.save_loaded_asset(texture)
            IMPORTED_SURFACE_TEXTURES[(surface, suffix)] = texture
            unreal.log(f"Imported hero surface texture {asset_name}")



def scalar(material, value, x, y, prop):
    node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, x, y
    )
    node.set_editor_property("r", value)
    unreal.MaterialEditingLibrary.connect_material_property(node, "", prop)


def create_material(name, settings):
    package = "/Game/Art/Materials"
    # UE 5.8 commandlets can assert while deleting rooted material expressions.
    # Version generated materials instead of mutating their expression graph in-place.
    version = HERO_MATERIAL_VERSION if name in HERO_MATERIAL_NAMES else LEGACY_MATERIAL_VERSION
    asset_name = f"{name}_V{version}"
    asset_path = f"{package}/{asset_name}"
    existing = (
        unreal.load_asset(asset_path)
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path)
        else None
    )
    if existing:
        unreal.MaterialEditingLibrary.set_base_material_usage(
            existing, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True
        )
        unreal.MaterialEditingLibrary.recompile_material(existing)
        unreal.EditorAssetLibrary.save_loaded_asset(existing)
        return existing
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package, unreal.Material, unreal.MaterialFactoryNew()
    )
    color, metallic, roughness, emission = settings
    color_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -420, -80
    )
    color_node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color_node, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    surface = HERO_SURFACE_TEXTURES.get(name)
    if surface:
        packed_texture = IMPORTED_SURFACE_TEXTURES.get((surface, "RMA"))
        normal_texture = IMPORTED_SURFACE_TEXTURES.get((surface, "Normal"))
        if not packed_texture or not normal_texture:
            raise RuntimeError(f"Surface textures were not imported for {name}")
        packed_sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -420, 40
        )
        packed_sample.set_editor_property("texture", packed_texture)
        packed_sample.set_editor_property(
            "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            packed_sample, "R", unreal.MaterialProperty.MP_METALLIC
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            packed_sample, "G", unreal.MaterialProperty.MP_ROUGHNESS
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            packed_sample, "B", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
        )
        normal_sample = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -130, 90
        )
        normal_sample.set_editor_property("texture", normal_texture)
        normal_sample.set_editor_property(
            "sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            normal_sample, "", unreal.MaterialProperty.MP_NORMAL
        )
    else:
        scalar(material, metallic, -420, 40, unreal.MaterialProperty.MP_METALLIC)
        scalar(material, roughness, -420, 130, unreal.MaterialProperty.MP_ROUGHNESS)
    scalar(material, HERO_SPECULAR.get(name, 0.5), -420, 220, unreal.MaterialProperty.MP_SPECULAR)

    emission_output = None
    if emission:
        emission_color, strength_value = emission
        emission_node = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -420, -220
        )
        emission_node.set_editor_property("constant", unreal.LinearColor(*emission_color, 1.0))
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -420, -310
        )
        strength.set_editor_property("r", strength_value)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -160, -240
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(emission_node, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        emission_output = multiply

    rim_color = HERO_RIM.get(name)
    if rim_color:
        fresnel = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionFresnel, -410, -430
        )
        rim = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -410, -520
        )
        rim.set_editor_property("constant", unreal.LinearColor(*rim_color, 1.0))
        rim_multiply = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -180, -450
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", rim_multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(rim, "", rim_multiply, "B")
        if emission_output:
            combined = unreal.MaterialEditingLibrary.create_material_expression(
                material, unreal.MaterialExpressionAdd, 20, -300
            )
            unreal.MaterialEditingLibrary.connect_material_expressions(emission_output, "", combined, "A")
            unreal.MaterialEditingLibrary.connect_material_expressions(rim_multiply, "", combined, "B")
            emission_output = combined
        else:
            emission_output = rim_multiply

    if emission_output:
        unreal.MaterialEditingLibrary.connect_material_property(
            emission_output, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

    unreal.MaterialEditingLibrary.set_base_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH, True
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def create_effect_materials():
    """Create lightweight runtime materials for the pulse and shield presentation."""
    package = "/Game/Art/Materials"

    pulse_name = f"M_CF_Pulse_V{EFFECT_MATERIAL_VERSION}"
    pulse_path = f"{package}/{pulse_name}"
    pulse = unreal.load_asset(pulse_path) if unreal.EditorAssetLibrary.does_asset_exist(pulse_path) else None
    if not pulse:
        pulse = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            pulse_name, package, unreal.Material, unreal.MaterialFactoryNew()
        )
        pulse.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        color = unreal.MaterialEditingLibrary.create_material_expression(
            pulse, unreal.MaterialExpressionConstant3Vector, -240, 0
        )
        color.set_editor_property("constant", unreal.LinearColor(0.01, 1.0, 0.08, 1.0))
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            pulse, unreal.MaterialExpressionConstant, -240, 100
        )
        strength.set_editor_property("r", 22.0)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(
            pulse, unreal.MaterialExpressionMultiply, 0, 20
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(color, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        unreal.MaterialEditingLibrary.recompile_material(pulse)
        unreal.EditorAssetLibrary.save_loaded_asset(pulse)

    shield_name = f"M_CF_Shield_V{EFFECT_MATERIAL_VERSION}"
    shield_path = f"{package}/{shield_name}"
    shield = unreal.load_asset(shield_path) if unreal.EditorAssetLibrary.does_asset_exist(shield_path) else None
    if not shield:
        shield = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            shield_name, package, unreal.Material, unreal.MaterialFactoryNew()
        )
        shield.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        shield.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
        shield.set_editor_property("two_sided", True)
        fresnel = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionFresnel, -420, -20
        )
        floor = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionConstant, -420, 80
        )
        floor.set_editor_property("r", 0.08)
        facing = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionAdd, -250, 0
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", facing, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(floor, "", facing, "B")
        color = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionConstant3Vector, -420, -150
        )
        # Cyan-green glass separates the shield body from the greener hero
        # circuits and frame, matching the Canvas shield sheet more closely.
        color.set_editor_property("constant", unreal.LinearColor(0.0, 2.8, 0.62, 1.0))
        glow = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionMultiply, -160, -80
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(facing, "", glow, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(color, "", glow, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        opacity_strength = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionConstant, -220, 100
        )
        opacity_strength.set_editor_property("r", 0.19)
        opacity = unreal.MaterialEditingLibrary.create_material_expression(
            shield, unreal.MaterialExpressionMultiply, 20, 80
        )
        unreal.MaterialEditingLibrary.connect_material_expressions(facing, "", opacity, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(opacity_strength, "", opacity, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity, "", unreal.MaterialProperty.MP_OPACITY
        )
        unreal.MaterialEditingLibrary.recompile_material(shield)
        unreal.EditorAssetLibrary.save_loaded_asset(shield)
    return pulse, shield


def import_mesh(name, destination):
    filename = FBX_ROOT / f"{name}.fbx"
    if not filename.exists():
        raise RuntimeError(f"Missing generated FBX: {filename}")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(f"{destination}/{name}")
    if not mesh:
        raise RuntimeError(f"Unreal did not create {destination}/{name}")
    return mesh


def import_skeletal_mesh(name, destination):
    filename = FBX_ROOT / f"{name}.fbx"
    if not filename.exists():
        raise RuntimeError(f"Missing generated skeletal FBX: {filename}")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.skeletal_mesh_import_data.set_editor_property("import_meshes_in_bone_hierarchy", False)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.load_asset(f"{destination}/{name}")
    if not mesh:
        raise RuntimeError(f"Unreal did not create skeletal mesh {destination}/{name}")
    return mesh


def import_animation(name, destination, skeleton):
    filename = FBX_ROOT / f"{name}.fbx"
    if not filename.exists():
        raise RuntimeError(f"Missing generated animation FBX: {filename}")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", False)
    options.set_editor_property("import_animations", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
    options.set_editor_property("skeleton", skeleton)
    options.anim_sequence_import_data.set_editor_property("import_bone_tracks", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    animation = unreal.load_asset(f"{destination}/{name}")
    if not animation:
        raise RuntimeError(f"Unreal did not create animation {destination}/{name}")
    return animation


def assign_materials(mesh, materials):
    is_skeletal = isinstance(mesh, unreal.SkeletalMesh)
    slots_property = "materials" if is_skeletal else "static_materials"
    slots = mesh.get_editor_property(slots_property)
    assigned = []
    rebuilt_skeletal_slots = []
    for index, slot in enumerate(slots):
        slot_name = str(slot.get_editor_property("material_slot_name"))
        material = materials.get(slot_name)
        if material:
            if is_skeletal:
                slot.set_editor_property("material_interface", material)
                rebuilt_skeletal_slots.append(slot)
            else:
                mesh.set_material(index, material)
            assigned.append(slot_name)
        else:
            unreal.log_warning(f"No material mapping for {mesh.get_name()} slot {slot_name}")
            if is_skeletal:
                rebuilt_skeletal_slots.append(slot)
    if is_skeletal:
        mesh.set_editor_property("materials", rebuilt_skeletal_slots)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log(f"{mesh.get_name()}: assigned {len(assigned)} materials")


def main():
    import_hero_surface_textures()
    materials = {name: create_material(name, settings) for name, settings in MATERIALS.items()}
    create_effect_materials()
    for name, destination in ASSETS.items():
        mesh = import_mesh(name, destination)
        assign_materials(mesh, materials)
    imported_skeletal_mesh = None
    for name, destination in SKELETAL_ASSETS.items():
        mesh = import_skeletal_mesh(name, destination)
        assign_materials(mesh, materials)
        imported_skeletal_mesh = mesh
    if imported_skeletal_mesh:
        skeleton = imported_skeletal_mesh.get_editor_property("skeleton")
        imported_animations = {}
        for animation_name in ANIMATIONS:
            imported_animations[animation_name] = import_animation(
                animation_name, "/Game/Art/Characters/Animations", skeleton
            )
        # Both fire actions are authored as upper-body deltas and layer over locomotion.
        idle = imported_animations["A_Ciberfantasma_Pro_Idle"]
        for fire_name in ("A_Ciberfantasma_Pro_Fire", "A_Ciberfantasma_Pro_FireBack"):
            fire = imported_animations[fire_name]
            fire.set_editor_property(
                "additive_anim_type", unreal.AdditiveAnimationType.AAT_LOCAL_SPACE_BASE
            )
            fire.set_editor_property(
                "ref_pose_type", unreal.AdditiveBasePoseType.ABPT_ANIM_SCALED
            )
            fire.set_editor_property("ref_pose_seq", idle)
            unreal.EditorAssetLibrary.save_loaded_asset(fire)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("Ciberfantasma chibi models imported successfully")


if __name__ == "__main__":
    main()
