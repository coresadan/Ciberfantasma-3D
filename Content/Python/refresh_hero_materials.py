"""Relink the current versioned hero/effect materials without FBX reimport.

Material graphs are immutable once generated in this commandlet pipeline. Bump
the corresponding revision in ``import_chibi_models.py`` whenever graph values
change, run that importer once, then use this script for cheap relinking.
"""

import unreal

from import_chibi_models import (
    HERO_MATERIAL_NAMES,
    MATERIALS,
    MATERIAL_VERSION,
    assign_materials,
    create_effect_materials,
    create_material,
)


def main():
    materials = {
        name: create_material(name, MATERIALS[name])
        for name in HERO_MATERIAL_NAMES
    }
    create_effect_materials()

    for asset_path in (
        "/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro",
        "/Game/Art/Characters/SM_Ciberfantasma_Chibi",
    ):
        mesh = unreal.load_asset(asset_path)
        if not mesh:
            raise RuntimeError(f"Missing hero mesh: {asset_path}")
        assign_materials(mesh, materials)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"Hero V{MATERIAL_VERSION} materials relinked successfully")


if __name__ == "__main__":
    main()
