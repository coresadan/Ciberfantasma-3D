"""Audit Ciberfantasma's Blender animation tracks and posed mesh bounds.

Run from the project root with Blender 5.x::

    blender --background SourceAssets/Blender/CF_Character_Workfile.blend \
        --python-exit-code 1 --python Scripts/audit_hero_animation_bounds.py

The script is intentionally read-only: it evaluates the loaded scene but never
saves the workfile.  When no workfile is loaded it opens the project's canonical
``CF_Character_Workfile.blend`` automatically.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import math
from pathlib import Path
import re
import sys
from typing import Iterable

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BLEND = PROJECT_ROOT / "SourceAssets" / "Blender" / "CF_Character_Workfile.blend"

ARMATURE_NAME = "SK_Ciberfantasma_Chibi_Armature"
MESH_NAME = "SM_Ciberfantasma_Chibi"

EXPECTED_ACTIONS = {
    "A_Ciberfantasma_Pro_Idle": (1.0, 96.0),
    "A_Ciberfantasma_Pro_RunStart": (1.0, 17.0),
    "A_Ciberfantasma_Pro_Run": (1.0, 25.0),
    "A_Ciberfantasma_Pro_RunStop": (1.0, 19.0),
    "A_Ciberfantasma_Pro_JumpStart": (1.0, 12.0),
    "A_Ciberfantasma_Pro_JumpRise": (1.0, 24.0),
    "A_Ciberfantasma_Pro_JumpFall": (1.0, 24.0),
    "A_Ciberfantasma_Pro_Land": (1.0, 16.0),
    "A_Ciberfantasma_Pro_Crouch": (1.0, 48.0),
    "A_Ciberfantasma_Pro_CrouchWalk": (1.0, 33.0),
    "A_Ciberfantasma_Pro_Fire": (1.0, 14.0),
    "A_Ciberfantasma_Pro_FireBack": (1.0, 18.0),
    "A_Ciberfantasma_Pro_Shield": (1.0, 48.0),
    "A_Ciberfantasma_Pro_Hit": (1.0, 16.0),
}

# These are deliberately generous production guardrails, not a collision box.
# The rest hero is approximately 92 x 65 x 150 cm. Raised arms and anticipation
# poses may increase its world AABB, but a detached limb or corrupt rotation
# should not be able to turn it into a several-metre-wide/deep silhouette.
DEFAULT_MAX_WIDTH_CM = 160.0
DEFAULT_MAX_DEPTH_CM = 160.0
DEFAULT_MAX_HEIGHT_CM = 235.0
FRAME_EPSILON = 0.001
BOUND_EPSILON_CM = 0.01

BONE_CURVE_PATTERN = re.compile(
    r'^pose\.bones\["([^"\\]+)"\]\.'
    r"(location|rotation_euler|rotation_quaternion|rotation_axis_angle|scale)$"
)


def script_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate all hero actions, complete bone tracks and posed world bounds."
    )
    parser.add_argument(
        "--blend",
        type=Path,
        help="Workfile to open. The already loaded file is used when omitted.",
    )
    parser.add_argument("--max-width-cm", type=float, default=DEFAULT_MAX_WIDTH_CM)
    parser.add_argument("--max-depth-cm", type=float, default=DEFAULT_MAX_DEPTH_CM)
    parser.add_argument("--max-height-cm", type=float, default=DEFAULT_MAX_HEIGHT_CM)
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    return parser.parse_args(args)


class Audit:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)
        print(f"    [ERROR] {message}")

    def warning(self, message: str) -> None:
        self.warnings.append(message)
        print(f"    [WARN]  {message}")

    @staticmethod
    def info(message: str) -> None:
        print(f"    [OK]    {message}")


def load_requested_workfile(arguments: argparse.Namespace) -> Path:
    requested = arguments.blend.resolve() if arguments.blend else None
    current = Path(bpy.data.filepath).resolve() if bpy.data.filepath else None

    if requested:
        if not requested.is_file():
            raise FileNotFoundError(f"Requested Blender workfile does not exist: {requested}")
        if current != requested:
            bpy.ops.wm.open_mainfile(filepath=str(requested))
            current = Path(bpy.data.filepath).resolve()
    elif current is None:
        if not DEFAULT_BLEND.is_file():
            raise FileNotFoundError(f"Canonical Blender workfile does not exist: {DEFAULT_BLEND}")
        bpy.ops.wm.open_mainfile(filepath=str(DEFAULT_BLEND))
        current = Path(bpy.data.filepath).resolve()

    assert current is not None
    return current


def action_fcurves(action: bpy.types.Action, armature: bpy.types.Object):
    """Return F-curves for the armature slot on Blender 4.x or layered 5.x actions."""
    animation_data = armature.animation_data_create()
    animation_data.action = action

    # Blender <= 4.3 legacy action API.
    legacy_curves = getattr(action, "fcurves", None)
    if legacy_curves is not None:
        curves = list(legacy_curves)
        if curves:
            return curves, "legacy Action.fcurves"

    # Blender 4.4+/5.x slotted action API. Assigning the action above lets
    # Blender select the slot associated with this armature object.
    layers = getattr(action, "layers", None)
    if layers is None:
        return None, "no supported F-curve API"

    selected_handle = getattr(animation_data, "action_slot_handle", None)
    matching = []
    fallback = []
    for layer in layers:
        for strip in getattr(layer, "strips", ()):
            for channelbag in getattr(strip, "channelbags", ()):
                fallback.append(channelbag)
                if selected_handle is not None and channelbag.slot_handle == selected_handle:
                    matching.append(channelbag)

    bags = matching
    if not bags and len(fallback) == 1:
        # Some transitional Blender builds expose channel bags but do not expose
        # ``action_slot_handle`` on AnimData. A unique bag is unambiguous.
        bags = fallback
    if not bags:
        return [], "layered Action.channelbags (no armature slot found)"

    curves = [curve for bag in bags for curve in bag.fcurves]
    return curves, "layered Action.channelbags"


def required_transform_channels(bone: bpy.types.PoseBone):
    rotation_mode = bone.rotation_mode
    if rotation_mode == "QUATERNION":
        rotation_property, rotation_count = "rotation_quaternion", 4
    elif rotation_mode == "AXIS_ANGLE":
        rotation_property, rotation_count = "rotation_axis_angle", 4
    else:
        rotation_property, rotation_count = "rotation_euler", 3
    return (
        *(("location", index) for index in range(3)),
        *((rotation_property, index) for index in range(rotation_count)),
        *(("scale", index) for index in range(3)),
    )


def has_frame(frames: Iterable[float], expected: float) -> bool:
    return any(abs(frame - expected) <= FRAME_EPSILON for frame in frames)


def compact_missing_channels(missing: list[tuple[str, int]]) -> str:
    by_property: dict[str, list[int]] = defaultdict(list)
    for property_name, array_index in missing:
        by_property[property_name].append(array_index)
    return ", ".join(
        f"{property_name}[{','.join(str(index) for index in sorted(indices))}]"
        for property_name, indices in sorted(by_property.items())
    )


def inspect_action_tracks(
    audit: Audit,
    armature: bpy.types.Object,
    action: bpy.types.Action,
    expected_range: tuple[float, float],
) -> list[float]:
    curves, api_name = action_fcurves(action, armature)
    if curves is None:
        audit.warning(f"Track inspection skipped: {api_name}.")
        return list(expected_range)
    if not curves:
        audit.error(f"No F-curves available through {api_name}.")
        return list(expected_range)

    actual_range = tuple(float(value) for value in action.frame_range)
    if any(abs(actual - expected) > FRAME_EPSILON
           for actual, expected in zip(actual_range, expected_range)):
        audit.error(
            f"Frame range {actual_range[0]:g}-{actual_range[1]:g}; expected "
            f"{expected_range[0]:g}-{expected_range[1]:g}."
        )

    by_channel: dict[tuple[str, str, int], list] = defaultdict(list)
    keyed_frames: set[float] = set(expected_range)
    unrecognised_pose_paths: set[str] = set()
    for curve in curves:
        match = BONE_CURVE_PATTERN.match(curve.data_path)
        if not match:
            if curve.data_path.startswith("pose.bones["):
                unrecognised_pose_paths.add(curve.data_path)
            continue
        bone_name, property_name = match.groups()
        by_channel[(bone_name, property_name, curve.array_index)].append(curve)
        for point in curve.keyframe_points:
            frame, value = float(point.co[0]), float(point.co[1])
            keyed_frames.add(frame)
            if not math.isfinite(frame) or not math.isfinite(value):
                audit.error(
                    f"Non-finite key on {bone_name}.{property_name}[{curve.array_index}]."
                )

    if unrecognised_pose_paths:
        audit.warning(
            "Unsupported pose channel paths: " + ", ".join(sorted(unrecognised_pose_paths))
        )

    required_count = 0
    complete_count = 0
    start_frame, end_frame = expected_range
    rig_bones = {bone.name for bone in armature.pose.bones}
    for bone in armature.pose.bones:
        missing = []
        for property_name, array_index in required_transform_channels(bone):
            required_count += 1
            found = by_channel.get((bone.name, property_name, array_index), [])
            if not found:
                missing.append((property_name, array_index))
                continue
            if len(found) > 1:
                audit.error(
                    f"{bone.name}.{property_name}[{array_index}] is duplicated in action layers."
                )
                continue
            frames = [float(point.co[0]) for point in found[0].keyframe_points]
            absent_boundaries = [
                frame for frame in (start_frame, end_frame) if not has_frame(frames, frame)
            ]
            if absent_boundaries:
                audit.error(
                    f"{bone.name}.{property_name}[{array_index}] lacks boundary key(s) at "
                    + ", ".join(f"{frame:g}" for frame in absent_boundaries)
                    + "."
                )
                continue
            complete_count += 1
        if missing:
            audit.error(f"Bone {bone.name} lacks {compact_missing_channels(missing)}.")

    curve_bones = {key[0] for key in by_channel}
    unknown_bones = sorted(curve_bones - rig_bones)
    if unknown_bones:
        audit.error("Tracks target bones absent from the rig: " + ", ".join(unknown_bones))

    if complete_count == required_count:
        audit.info(
            f"{complete_count}/{required_count} scalar bone tracks are complete via {api_name}."
        )
    else:
        print(
            f"    [INFO]  Complete scalar tracks: {complete_count}/{required_count} "
            f"via {api_name}."
        )
    return sorted(keyed_frames)


def world_bounds(mesh: bpy.types.Object) -> tuple[Vector, Vector]:
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    evaluated_mesh = evaluated.to_mesh(preserve_all_data_layers=False, depsgraph=depsgraph)
    try:
        if not evaluated_mesh.vertices:
            raise RuntimeError(f"Evaluated mesh {mesh.name} has no vertices")
        matrix = evaluated.matrix_world
        first = matrix @ evaluated_mesh.vertices[0].co
        minimum = first.copy()
        maximum = first.copy()
        for vertex in evaluated_mesh.vertices[1:]:
            position = matrix @ vertex.co
            minimum.x = min(minimum.x, position.x)
            minimum.y = min(minimum.y, position.y)
            minimum.z = min(minimum.z, position.z)
            maximum.x = max(maximum.x, position.x)
            maximum.y = max(maximum.y, position.y)
            maximum.z = max(maximum.z, position.z)
        return minimum, maximum
    finally:
        evaluated.to_mesh_clear()


def scene_units_to_cm() -> float:
    unit_settings = bpy.context.scene.unit_settings
    scale_length = unit_settings.scale_length if unit_settings.system != "NONE" else 1.0
    return scale_length * 100.0


def inspect_action_bounds(
    audit: Audit,
    action: bpy.types.Action,
    armature: bpy.types.Object,
    mesh: bpy.types.Object,
    frames: list[float],
    arguments: argparse.Namespace,
) -> None:
    armature.animation_data.action = action
    cm_per_unit = scene_units_to_cm()
    print(
        "    frame | world min xyz (cm)             | world max xyz (cm)             "
        "| size W/D/H (cm)"
    )
    largest = Vector((0.0, 0.0, 0.0))
    for frame in frames:
        whole_frame = math.floor(frame)
        bpy.context.scene.frame_set(
            int(whole_frame), subframe=float(frame - whole_frame)
        )
        bpy.context.view_layer.update()
        minimum, maximum = world_bounds(mesh)
        minimum *= cm_per_unit
        maximum *= cm_per_unit
        size = maximum - minimum
        largest.x = max(largest.x, size.x)
        largest.y = max(largest.y, size.y)
        largest.z = max(largest.z, size.z)
        print(
            f"    {frame:5.1f} | "
            f"({minimum.x:7.2f}, {minimum.y:7.2f}, {minimum.z:7.2f}) | "
            f"({maximum.x:7.2f}, {maximum.y:7.2f}, {maximum.z:7.2f}) | "
            f"{size.x:7.2f}/{size.y:7.2f}/{size.z:7.2f}"
        )
        limits = (
            ("width X", size.x, arguments.max_width_cm),
            ("depth Y", size.y, arguments.max_depth_cm),
            ("height Z", size.z, arguments.max_height_cm),
        )
        for label, value, maximum_allowed in limits:
            if not math.isfinite(value):
                audit.error(f"Frame {frame:g} has non-finite {label} bounds.")
            elif value > maximum_allowed + BOUND_EPSILON_CM:
                audit.error(
                    f"Frame {frame:g} {label} is {value:.2f} cm; limit is "
                    f"{maximum_allowed:.2f} cm."
                )
    audit.info(
        f"Peak sampled W/D/H: {largest.x:.2f}/{largest.y:.2f}/{largest.z:.2f} cm."
    )


def validate_scene(audit: Audit):
    armature = bpy.data.objects.get(ARMATURE_NAME)
    mesh = bpy.data.objects.get(MESH_NAME)
    if armature is None or armature.type != "ARMATURE":
        audit.error(f"Required armature is missing or invalid: {ARMATURE_NAME}")
    if mesh is None or mesh.type != "MESH":
        audit.error(f"Required hero mesh is missing or invalid: {MESH_NAME}")
    if armature is None or mesh is None or audit.errors:
        return None, None

    rig_modifiers = [
        modifier for modifier in mesh.modifiers
        if modifier.type == "ARMATURE" and modifier.object == armature
    ]
    if not rig_modifiers:
        audit.error(f"{MESH_NAME} has no Armature modifier targeting {ARMATURE_NAME}.")
    else:
        audit.info(
            f"Hero mesh has {len(mesh.data.vertices):,} vertices and is bound to a "
            f"{len(armature.pose.bones)}-bone rig."
        )
    return armature, mesh


def main() -> None:
    arguments = script_arguments()
    audit = Audit()
    workfile = load_requested_workfile(arguments)

    print("\nCF HERO ANIMATION + WORLD BOUNDS AUDIT")
    print(f"  Workfile: {workfile}")
    print(f"  Blender:  {bpy.app.version_string}")
    print(
        "  Limits:   "
        f"width X <= {arguments.max_width_cm:.1f} cm, "
        f"depth Y <= {arguments.max_depth_cm:.1f} cm, "
        f"height Z <= {arguments.max_height_cm:.1f} cm"
    )

    armature, mesh = validate_scene(audit)
    if armature is None or mesh is None:
        raise RuntimeError(
            f"CF_ANIMATION_BOUNDS_AUDIT: FAIL ({len(audit.errors)} error(s))"
        )

    missing_actions = [name for name in EXPECTED_ACTIONS if bpy.data.actions.get(name) is None]
    if missing_actions:
        audit.error("Missing required actions: " + ", ".join(missing_actions))
    else:
        audit.info(f"All {len(EXPECTED_ACTIONS)} required actions exist.")

    animation_data = armature.animation_data_create()
    previous_action = animation_data.action
    previous_use_nla = animation_data.use_nla
    previous_frame = bpy.context.scene.frame_current
    animation_data.use_nla = False
    try:
        for action_name, expected_range in EXPECTED_ACTIONS.items():
            action = bpy.data.actions.get(action_name)
            if action is None:
                continue
            print(f"\n  ACTION {action_name}")
            keyed_frames = inspect_action_tracks(audit, armature, action, expected_range)
            # Evaluate every delivered 60 Hz frame. Corrupt interpolation and
            # Bezier overshoot happen between authored poses, so checking only
            # keyed frames is insufficient for a final animation pass.
            start_frame, end_frame = expected_range
            sampled_frames = [float(frame) for frame in range(
                math.ceil(start_frame), math.floor(end_frame) + 1)]
            print(
                "    [INFO]  Sampling every delivered frame: "
                f"{len(sampled_frames)} frame(s), {len(keyed_frames)} authored pose time(s)."
            )
            inspect_action_bounds(
                audit, action, armature, mesh, sampled_frames, arguments
            )
    finally:
        animation_data.action = previous_action
        animation_data.use_nla = previous_use_nla
        bpy.context.scene.frame_set(previous_frame)

    print("\nCF HERO ANIMATION + WORLD BOUNDS AUDIT SUMMARY")
    print(f"  Actions expected: {len(EXPECTED_ACTIONS)}")
    print(f"  Errors:           {len(audit.errors)}")
    print(f"  Warnings:         {len(audit.warnings)}")
    if audit.errors:
        print("CF_ANIMATION_BOUNDS_AUDIT: FAIL")
        raise RuntimeError(
            f"Animation/bounds audit failed with {len(audit.errors)} error(s)."
        )
    print("CF_ANIMATION_BOUNDS_AUDIT: PASS")


if __name__ == "__main__":
    main()
