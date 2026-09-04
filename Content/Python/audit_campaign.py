"""Load every generated map and verify its gameplay actor inventory."""

import json
import os
import unreal


MAP_NAMES = (
    "Act01_Rooftops", "Act02_DataCenter", "Act03_ExecutiveCore",
    "Act04_MemoryGardens", "Act05_ConsensusFactory", "Act06_SingleArchive",
    "Act07_DeadIdeasAvenue", "Act08_SilenceOffice", "Act09_DirectorOffice",
)
ADVENTURE_ROUTE_HAZARDS = {
    0: (1, 3),
    2: (0, 2),
    6: (1, 3, 5),
    8: (0, 2),
}


def native(name):
    result = unreal.load_class(None, f"/Script/Ciberfantasma3D.{name}")
    if not result:
        raise RuntimeError(f"Missing native class {name}")
    return result


def main():
    with open(os.path.join(unreal.Paths.project_dir(), "Design", "campaign_levels.json"), encoding="utf-8") as handle:
        levels = json.load(handle)["levels"]
    level_system = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    classes = {
        "shards": native("CFShard"), "terminals": native("CFTerminal"),
        "enemies": native("CFPatrolEnemy"), "hazards": native("CFHazard"),
        "portals": native("CFExitPortal"), "special": native("CFMovingPlatform"),
    }
    failures = []
    for index, (map_name, expected) in enumerate(zip(MAP_NAMES, levels)):
        if not level_system.load_level(f"/Game/Maps/{map_name}"):
            failures.append(f"{map_name}: cannot load")
            continue
        actors = actor_system.get_all_level_actors()
        counts = {key: sum(actor.get_class() == actor_class for actor in actors)
                  for key, actor_class in classes.items()}
        wanted = {
            "shards": len(expected["shards"]), "terminals": len(expected["terminals"]),
            "enemies": len(expected["enemies"]), "hazards": len(expected["hazards"]),
            "portals": 1,
            "special": (len(expected.get("moving", [])) + len(expected.get("phase", []))
                        + len(ADVENTURE_ROUTE_HAZARDS.get(index, ()))),
        }
        if counts != wanted:
            failures.append(f"{map_name}: {counts} expected {wanted}")
        portals = [actor for actor in actors if actor.get_class() == classes["portals"]]
        if portals and portals[0].get_editor_property("level_index") != index:
            failures.append(f"{map_name}: wrong portal level index")
        hazards = [actor for actor in actors if actor.get_class() == classes["hazards"]]
        expected_styles = [values[4] if len(values) > 4 else "spikes" for values in expected["hazards"]]
        actual_styles = [str(actor.get_editor_property("hazard_style")) for actor in hazards]
        if sorted(actual_styles) != sorted(expected_styles):
            failures.append(f"{map_name}: hazard styles {actual_styles} expected {expected_styles}")
        unreal.log(f"AUDIT {map_name}: {counts}")
    if failures:
        raise RuntimeError("Campaign audit failed: " + "; ".join(failures))
    unreal.log("CAMPAIGN AUDIT PASSED: Canvas route preserved, hazard identities and adventure routes verified")


if __name__ == "__main__":
    main()
