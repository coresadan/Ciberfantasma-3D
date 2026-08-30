"""Read-only audit for the generated player asset and runtime presentation."""

import unreal


def object_path(value):
    return value.get_path_name() if value else "None"


def main():
    skeletal = unreal.load_asset("/Game/Art/Characters/SK_Ciberfantasma_Chibi")
    static = unreal.load_asset("/Game/Art/Characters/SM_Ciberfantasma_Chibi")
    if not skeletal or not static:
        raise RuntimeError("Generated Ciberfantasma meshes are missing")

    unreal.log("=== Ciberfantasma skeletal material audit ===")
    for index, slot in enumerate(skeletal.get_editor_property("materials")):
        unreal.log(
            f"SK slot {index}: {slot.get_editor_property('material_slot_name')} -> "
            f"{object_path(slot.get_editor_property('material_interface'))}"
        )

    unreal.log("=== Ciberfantasma static material audit ===")
    for index, slot in enumerate(static.get_editor_property("static_materials")):
        unreal.log(
            f"SM slot {index}: {slot.get_editor_property('material_slot_name')} -> "
            f"{object_path(slot.get_editor_property('material_interface'))}"
        )

    bounds = skeletal.get_bounds()
    unreal.log(f"SK bounds origin={bounds.origin} extent={bounds.box_extent} radius={bounds.sphere_radius}")
    skeletal_tools = unreal.get_editor_subsystem(unreal.SkeletalMeshEditorSubsystem)
    section_count = skeletal_tools.get_num_sections(skeletal, 0)
    for section_index in range(section_count):
        unreal.log(
            f"SK LOD0 section {section_index} uses slot "
            f"{skeletal_tools.get_lod_material_slot(skeletal, 0, section_index)}"
        )

    unreal.log("=== Generated material constants ===")
    for name in ("M_CF_Hood", "M_CF_Armor", "M_CF_Visor", "M_CF_Bone", "M_CF_Green"):
        material = unreal.load_asset(f"/Game/Art/Materials/{name}_V3")
        node = unreal.MaterialEditingLibrary.get_material_property_input_node(
            material, unreal.MaterialProperty.MP_BASE_COLOR
        )
        value = node.get_editor_property("constant") if node else "None"
        unreal.log(f"{name}_V3 base={value}")


if __name__ == "__main__":
    main()
