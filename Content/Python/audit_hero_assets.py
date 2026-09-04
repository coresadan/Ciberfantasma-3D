"""Report the imported hero skeleton, material slots and gameplay animations."""

import unreal

from import_chibi_models import (
    EFFECT_MATERIAL_VERSION,
    HERO_MATERIAL_NAMES,
    HERO_SURFACE_TEXTURES,
    MATERIAL_VERSION,
)


HERO_PATH = "/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro"
ANIMATION_ROOT = "/Game/Art/Characters/Animations"
CONTROL_RIG_PATH = "/Game/Art/Characters/Rigs/CR_Ciberfantasma_FootIK"
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


def main():
    hero = unreal.load_asset(HERO_PATH)
    if not hero:
        raise RuntimeError(f"Missing hero asset: {HERO_PATH}")

    materials = hero.get_editor_property("materials")
    unreal.log(f"HERO_AUDIT material_slots={len(materials)}")
    material_paths = set()
    for index, slot in enumerate(materials):
        interface = slot.get_editor_property("material_interface")
        slot_name = slot.get_editor_property("material_slot_name")
        try:
            imported_name = slot.get_editor_property("imported_material_slot_name")
        except Exception:
            imported_name = "<unavailable>"
        material_path = interface.get_path_name() if interface else "<none>"
        material_paths.add(material_path)
        unreal.log(
            f"HERO_AUDIT slot={index} name={slot_name} imported={imported_name} material={material_path}"
        )
        if interface:
            base_node = unreal.MaterialEditingLibrary.get_material_property_input_node(
                interface, unreal.MaterialProperty.MP_BASE_COLOR
            )
            if base_node and hasattr(base_node, "get_editor_property"):
                try:
                    base_color = base_node.get_editor_property("constant")
                    unreal.log(f"HERO_AUDIT slot={index} base_color={base_color}")
                except Exception:
                    pass

    expected_materials = {
        f"/Game/Art/Materials/{name}_V{MATERIAL_VERSION}.{name}_V{MATERIAL_VERSION}"
        for name in HERO_MATERIAL_NAMES
    }
    if material_paths != expected_materials:
        missing = sorted(expected_materials - material_paths)
        unexpected = sorted(material_paths - expected_materials)
        raise RuntimeError(
            f"Hero material revision mismatch: missing={missing}, unexpected={unexpected}"
        )
    unreal.log(f"HERO_AUDIT material_revision=V{MATERIAL_VERSION}")
    for interface_path in expected_materials:
        interface = unreal.load_asset(interface_path.split(".")[0])
        for material_property in (
            unreal.MaterialProperty.MP_BASE_COLOR,
            unreal.MaterialProperty.MP_METALLIC,
            unreal.MaterialProperty.MP_ROUGHNESS,
            unreal.MaterialProperty.MP_SPECULAR,
        ):
            if not unreal.MaterialEditingLibrary.get_material_property_input_node(
                interface, material_property
            ):
                raise RuntimeError(
                    f"Hero material {interface_path} has no input for {material_property}"
                )
        material_name = interface.get_name().rsplit(f"_V{MATERIAL_VERSION}", 1)[0]
        if material_name in HERO_SURFACE_TEXTURES:
            for material_property in (
                unreal.MaterialProperty.MP_NORMAL,
                unreal.MaterialProperty.MP_AMBIENT_OCCLUSION,
            ):
                if not unreal.MaterialEditingLibrary.get_material_property_input_node(
                    interface, material_property
                ):
                    raise RuntimeError(
                        f"Mapped hero material {interface_path} has no input for {material_property}"
                    )

    for surface in sorted(set(HERO_SURFACE_TEXTURES.values())):
        for suffix in ("RMA", "Normal"):
            texture_path = f"/Game/Art/Textures/Hero/T_CF_{surface}_{suffix}"
            texture = unreal.load_asset(texture_path)
            if not texture:
                raise RuntimeError(f"Missing hero surface texture: {texture_path}")
            unreal.log(f"HERO_AUDIT surface_texture={texture.get_path_name()}")

    expected_effects = {
        "pulse": f"/Game/Art/Materials/M_CF_Pulse_V{EFFECT_MATERIAL_VERSION}",
        "shield": f"/Game/Art/Materials/M_CF_Shield_V{EFFECT_MATERIAL_VERSION}",
    }
    for effect_name, effect_path in expected_effects.items():
        interface = unreal.load_asset(effect_path)
        if not interface:
            raise RuntimeError(f"Missing {effect_name} presentation material: {effect_path}")
        emissive = unreal.MaterialEditingLibrary.get_material_property_input_node(
            interface, unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
        if not emissive:
            raise RuntimeError(f"{effect_name} presentation material has no emissive input")
        if effect_name == "shield":
            opacity = unreal.MaterialEditingLibrary.get_material_property_input_node(
                interface, unreal.MaterialProperty.MP_OPACITY
            )
            if not opacity:
                raise RuntimeError("Shield presentation material has no opacity input")
        unreal.log(f"HERO_AUDIT {effect_name}_material={interface.get_path_name()}")
    unreal.log(f"HERO_AUDIT effect_revision=V{EFFECT_MATERIAL_VERSION}")

    skeleton = hero.get_editor_property("skeleton")
    if not skeleton:
        raise RuntimeError("Hero has no skeleton")
    unreal.log(f"HERO_AUDIT skeleton={skeleton.get_path_name()}")

    missing = []
    for animation_name in ANIMATIONS:
        path = f"{ANIMATION_ROOT}/{animation_name}"
        animation = unreal.load_asset(path)
        if not animation:
            missing.append(path)
            continue
        unreal.log(f"HERO_AUDIT animation={animation.get_path_name()}")
        if animation_name in ("A_Ciberfantasma_Pro_Fire", "A_Ciberfantasma_Pro_FireBack"):
            additive_type = animation.get_editor_property("additive_anim_type")
            reference = animation.get_editor_property("ref_pose_seq")
            unreal.log(
                f"HERO_AUDIT fire_additive={animation_name} type={additive_type} reference={reference.get_path_name() if reference else '<none>'}"
            )
            if additive_type != unreal.AdditiveAnimationType.AAT_LOCAL_SPACE_BASE or not reference:
                raise RuntimeError(f"Fire animation {animation_name} is not a local-space additive layer")
    if missing:
        raise RuntimeError(f"Missing animations: {missing}")

    control_rig = unreal.load_asset(CONTROL_RIG_PATH)
    if not control_rig:
        raise RuntimeError(f"Missing hero foot Control Rig: {CONTROL_RIG_PATH}")
    hierarchy_keys = list(control_rig.hierarchy.get_all_keys())
    bone_names = {
        str(key.name) for key in hierarchy_keys if key.type == unreal.RigElementType.BONE
    }
    control_names = {
        str(key.name) for key in hierarchy_keys if key.type == unreal.RigElementType.CONTROL
    }
    expected_leg_bones = {
        "pelvis", "thigh_l", "calf_l", "foot_l", "toe_l",
        "thigh_r", "calf_r", "foot_r", "toe_r",
    }
    expected_controls = {
        "CTRL_FootIK_L", "CTRL_FootIK_R", "CTRL_KneePole_L", "CTRL_KneePole_R",
    }
    if not expected_leg_bones.issubset(bone_names):
        raise RuntimeError(
            f"Control Rig leg hierarchy incomplete: {sorted(expected_leg_bones - bone_names)}"
        )
    if not expected_controls.issubset(control_names):
        raise RuntimeError(
            f"Control Rig controls incomplete: {sorted(expected_controls - control_names)}"
        )
    graph_controller = control_rig.get_controller_by_name("RigVMModel")
    if not graph_controller:
        raise RuntimeError("Hero Control Rig has no Forward Solve graph")
    node_count = len(graph_controller.get_graph().get_nodes())
    if node_count < 5:
        raise RuntimeError(f"Hero Control Rig graph is incomplete: {node_count} nodes")
    unreal.log(
        f"HERO_AUDIT control_rig={control_rig.get_path_name()} "
        f"bones={len(bone_names)} controls={len(control_names)} nodes={node_count}"
    )

    unreal.log("HERO_AUDIT PASS")


# The Unreal PythonScript commandlet does not consistently expose
# ``__name__ == '__main__'`` across engine versions. This file is a standalone
# audit entry point, so execute it unconditionally.
main()
