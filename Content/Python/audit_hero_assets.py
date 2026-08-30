"""Report the imported hero skeleton, material slots and gameplay animations."""

import unreal


HERO_PATH = "/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro"
ANIMATION_ROOT = "/Game/Art/Characters/Animations"
ANIMATIONS = (
    "A_Ciberfantasma_Pro_Idle",
    "A_Ciberfantasma_Pro_Run",
    "A_Ciberfantasma_Pro_JumpStart",
    "A_Ciberfantasma_Pro_JumpRise",
    "A_Ciberfantasma_Pro_JumpFall",
    "A_Ciberfantasma_Pro_Land",
    "A_Ciberfantasma_Pro_Crouch",
    "A_Ciberfantasma_Pro_Fire",
    "A_Ciberfantasma_Pro_Shield",
    "A_Ciberfantasma_Pro_Hit",
)


def main():
    hero = unreal.load_asset(HERO_PATH)
    if not hero:
        raise RuntimeError(f"Missing hero asset: {HERO_PATH}")

    materials = hero.get_editor_property("materials")
    unreal.log(f"HERO_AUDIT material_slots={len(materials)}")
    for index, slot in enumerate(materials):
        interface = slot.get_editor_property("material_interface")
        slot_name = slot.get_editor_property("material_slot_name")
        try:
            imported_name = slot.get_editor_property("imported_material_slot_name")
        except Exception:
            imported_name = "<unavailable>"
        material_path = interface.get_path_name() if interface else "<none>"
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
        if animation_name == "A_Ciberfantasma_Pro_Fire":
            additive_type = animation.get_editor_property("additive_anim_type")
            reference = animation.get_editor_property("ref_pose_seq")
            unreal.log(
                f"HERO_AUDIT fire_additive={additive_type} reference={reference.get_path_name() if reference else '<none>'}"
            )
            if additive_type != unreal.AdditiveAnimationType.AAT_LOCAL_SPACE_BASE or not reference:
                raise RuntimeError("Fire animation is not configured as a local-space additive layer")
    if missing:
        raise RuntimeError(f"Missing animations: {missing}")

    unreal.log("HERO_AUDIT PASS")


if __name__ == "__main__":
    main()
