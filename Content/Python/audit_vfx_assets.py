"""Validate that campaign VFX are real Niagara systems with runtime emitters."""

import os

import unreal


SYSTEMS = (
    "/Game/Art/VFX/NS_PulseImpact_Runtime",
    "/Game/Art/VFX/NS_EnemyDeath_Runtime",
    "/Game/Art/VFX/NS_MuzzleFlash_Runtime",
    "/Game/Art/VFX/NS_ShieldAbsorb_Runtime",
    "/Game/Art/VFX/NS_BossExplosion_Runtime",
)


def main():
    failures = []
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    dependency_options = unreal.AssetRegistryDependencyOptions()
    for path in SYSTEMS:
        system = unreal.load_asset(path)
        if not system:
            failures.append(f"missing {path}")
            continue
        relative_path = path.removeprefix("/Game/") + ".uasset"
        filename = os.path.join(unreal.Paths.project_content_dir(), relative_path)
        disk_size = os.path.getsize(filename) if os.path.isfile(filename) else 0
        version = unreal.EditorAssetLibrary.get_metadata_tag(system, "CFVFXVersion")
        dependencies = [str(value) for value in registry.get_dependencies(path, dependency_options)]
        obsolete_dependencies = [value for value in dependencies if "_Obsolete" in value]
        unreal.log(
            f"VFX_AUDIT system={path} bytes={disk_size} version={version} "
            f"dependencies={len(dependencies)}"
        )
        # Factory-created empty systems are roughly 48 KB in this project. The
        # authored templates are all over 500 KB and carry our generation tag.
        if disk_size < 100_000 or version != "4":
            failures.append(f"stub or obsolete system {path}")
        if obsolete_dependencies:
            failures.append(f"obsolete dependencies in {path}: {obsolete_dependencies}")

    if failures:
        raise RuntimeError("VFX audit failed: " + "; ".join(failures))
    unreal.log("VFX_AUDIT PASS")


if __name__ == "__main__":
    main()
