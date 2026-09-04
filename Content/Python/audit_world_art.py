"""Audit the non-destructive V3 environment pass across all campaign maps."""

import unreal

from build_campaign import MAP_NAMES


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    failures = []
    for map_name in MAP_NAMES:
        if not levels.load_level(f"/Game/Maps/{map_name}"):
            failures.append(f"{map_name}: load failed")
            continue
        all_actors = actors.get_all_level_actors()
        art = [actor for actor in all_actors if "CF_ArtPass3" in {str(t) for t in actor.tags}]
        windows = [actor for actor in art if actor.get_actor_label().startswith("ArtV3_Window_")]
        facades = [actor for actor in art if actor.get_actor_label().startswith("ArtV3_Facade_")]
        fascia = [actor for actor in art if actor.get_actor_label().startswith("ArtV3_Fascia_")]
        fills = [actor for actor in art if actor.get_actor_label().startswith("ArtV3_GameplayFill_")]
        fog = [actor for actor in art if actor.get_actor_label() == "ArtV3_HeightFog"]
        if len(art) < 180 or len(windows) < 55 or len(facades) != 15 or not fascia or not fills or len(fog) != 1:
            failures.append(
                f"{map_name}: art={len(art)} windows={len(windows)} facades={len(facades)} "
                f"fascia={len(fascia)} fills={len(fills)} fog={len(fog)}"
            )
        unreal.log(
            f"ART_AUDIT {map_name}: art={len(art)} windows={len(windows)} "
            f"facades={len(facades)} fascia={len(fascia)}"
        )
    if failures:
        raise RuntimeError("World art audit failed: " + "; ".join(failures))
    unreal.log("ART_AUDIT PASS: all nine maps contain the V3 environment kit")


main()
