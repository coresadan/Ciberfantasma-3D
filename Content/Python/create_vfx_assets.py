"""Create VFX materials and runtime-ready Niagara systems for the campaign.

Run inside Unreal Editor-Cmd:
  UnrealEditor-Cmd.exe Project.uproject -run=pythonscript -script=Content/Python/create_vfx_assets.py -unattended
"""

import os

import unreal


VFX_PACKAGE = "/Game/Art/VFX"
VFX_VERSION = "4"

# Start from Epic's authored Niagara templates instead of NiagaraSystemFactoryNew.
# A factory-created system contains no emitter and therefore renders nothing.
SYSTEM_TEMPLATES = {
    "NS_PulseImpact_Runtime": "/Niagara/DefaultAssets/Templates/Systems/RadialBurst",
    "NS_EnemyDeath_Runtime": "/Niagara/DefaultAssets/Templates/Systems/RadialBurst",
    "NS_MuzzleFlash_Runtime": "/Niagara/DefaultAssets/Templates/Systems/DirectionalBurst",
    "NS_ShieldAbsorb_Runtime": "/Niagara/DefaultAssets/Templates/Systems/RadialBurst",
    "NS_BossExplosion_Runtime": "/Niagara/DefaultAssets/Templates/Systems/SimpleExplosion",
}
LEGACY_SYSTEMS = (
    "NS_PulseImpact",
    "NS_EnemyDeath",
    "NS_MuzzleFlash",
    "NS_ShieldAbsorb",
    "NS_BossExplosion",
)


def ensure_package(path):
    unreal.EditorAssetLibrary.make_directory(path)


def create_material_for_vfx(name, color, emissive_strength):
    """Unlit additive material for particle sprites."""
    package = VFX_PACKAGE + "/Materials"
    asset_path = package + "/" + name
    existing = unreal.load_asset(asset_path)
    if existing:
        return existing
    unreal.EditorAssetLibrary.make_directory(package)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, package, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not material:
        return None
    # UE 5.8: use string-based property names for enums
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    material.set_editor_property("two_sided", True)
    color_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -460, -80
    )
    color_node.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    strength_node = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -460, 60
    )
    strength_node.set_editor_property("r", emissive_strength)
    multiply = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, -220, -40
    )
    unreal.MaterialEditingLibrary.connect_material_expressions(color_node, "", multiply, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength_node, "", multiply, "B")
    unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    unreal.log("Created VFX material: " + asset_path)
    return material


def create_niagara_system(name, template_path):
    """Duplicate an authored engine template into a cookable game asset."""
    asset_path = VFX_PACKAGE + "/" + name
    existing = unreal.load_asset(asset_path)
    relative_path = asset_path.removeprefix("/Game/") + ".uasset"
    filename = os.path.join(unreal.Paths.project_content_dir(), relative_path)
    disk_size = os.path.getsize(filename) if os.path.isfile(filename) else 0
    version = unreal.EditorAssetLibrary.get_metadata_tag(existing, "CFVFXVersion") if existing else ""
    if existing and disk_size >= 100_000 and version == VFX_VERSION:
        unreal.log("VFX asset already exists: " + asset_path)
        return existing

    template = unreal.load_asset(template_path)
    if not template:
        raise RuntimeError("Missing Niagara template: " + template_path)
    if existing:
        if not unreal.EditorAssetLibrary.delete_asset(asset_path):
            raise RuntimeError("Could not delete obsolete Niagara asset: " + asset_path)
        existing = None
        unreal.SystemLibrary.collect_garbage()

    system = unreal.EditorAssetLibrary.duplicate_asset(template_path, asset_path)
    if system:
        try:
            system.set_editor_property("is_template_asset", False)
        except Exception:
            pass
        unreal.EditorAssetLibrary.set_metadata_tag(system, "CFVFXVersion", VFX_VERSION)
        unreal.EditorAssetLibrary.save_loaded_asset(system)
        unreal.log("Created runtime Niagara system: " + asset_path + " from " + template_path)
    else:
        raise RuntimeError("Could not duplicate Niagara system: " + name)
    return system


def main():
    ensure_package(VFX_PACKAGE)
    create_material_for_vfx("M_VFX_PulseImpact", (0.02, 1.0, 0.18), 18.0)
    create_material_for_vfx("M_VFX_EnemyImpact", (1.0, 0.05, 0.02), 16.0)
    create_material_for_vfx("M_VFX_EnemyDeath", (1.0, 0.35, 0.01), 22.0)
    create_material_for_vfx("M_VFX_MuzzleFlash", (0.05, 1.0, 0.22), 28.0)
    create_material_for_vfx("M_VFX_ShieldAbsorb", (0.0, 0.9, 0.2), 24.0)
    for system_name, template_path in SYSTEM_TEMPLATES.items():
        create_niagara_system(system_name, template_path)
    for legacy_name in LEGACY_SYSTEMS:
        legacy_path = VFX_PACKAGE + "/" + legacy_name
        if unreal.EditorAssetLibrary.does_asset_exist(legacy_path):
            if not unreal.EditorAssetLibrary.delete_asset(legacy_path):
                raise RuntimeError("Could not remove legacy Niagara asset: " + legacy_path)
            unreal.log("Removed legacy Niagara asset: " + legacy_path)
    unreal.SystemLibrary.collect_garbage()
    unreal.log("VFX assets created in " + VFX_PACKAGE)


if __name__ == "__main__":
    main()
