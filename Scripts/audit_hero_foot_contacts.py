"""Audit authored foot contacts on the generated Ciberfantasma rig.

Run through Blender so the armature modifier and every interpolated frame are
evaluated exactly as they are before FBX export.
"""

import math

import bpy


ARMATURE_NAME = "SK_Ciberfantasma_Chibi_Armature"
MESH_NAME = "SM_Ciberfantasma_Chibi"
ACTION_FRAMES = {
    "A_Ciberfantasma_Pro_Run": (1, 13, 25),
    "A_Ciberfantasma_Pro_CrouchWalk": (1, 17, 33),
    "A_Ciberfantasma_Pro_Land": (3, 5, 7, 10),
}


def weighted_indices(mesh, names):
    group_indices = {mesh.vertex_groups[name].index for name in names}
    return [
        vertex.index
        for vertex in mesh.data.vertices
        if any(item.group in group_indices and item.weight > 0.25 for item in vertex.groups)
    ]


def foot_floor(mesh, evaluated_mesh, indices):
    transform = mesh.matrix_world
    values = [(transform @ evaluated_mesh.vertices[index].co).z for index in indices]
    if not values or not all(math.isfinite(value) for value in values):
        raise RuntimeError("Foot contact contains no finite evaluated vertices")
    return min(values)


def close_enough(a, b, tolerance, label):
    if abs(a - b) > tolerance:
        raise RuntimeError(f"{label}: {a:.3f} vs {b:.3f}, tolerance {tolerance:.3f}")


armature = bpy.data.objects[ARMATURE_NAME]
mesh = bpy.data.objects[MESH_NAME]
armature.animation_data_create()
indices = {
    "left": weighted_indices(mesh, ("foot_l", "toe_l")),
    "right": weighted_indices(mesh, ("foot_r", "toe_r")),
}
samples = {}

for action_name, frames in ACTION_FRAMES.items():
    action = bpy.data.actions[action_name]
    armature.animation_data.action = action
    samples[action_name] = {}
    for frame in frames:
        bpy.context.scene.frame_set(frame)
        bpy.context.view_layer.update()
        evaluated_mesh = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
        left = foot_floor(mesh, evaluated_mesh, indices["left"])
        right = foot_floor(mesh, evaluated_mesh, indices["right"])
        samples[action_name][frame] = (left, right)
        print(f"CF_FOOT_CONTACT {action_name} frame={frame} left={left:.3f} right={right:.3f}")

for action_name in ("A_Ciberfantasma_Pro_Run", "A_Ciberfantasma_Pro_CrouchWalk"):
    frames = ACTION_FRAMES[action_name]
    first = samples[action_name][frames[0]]
    middle = samples[action_name][frames[1]]
    last = samples[action_name][frames[-1]]
    close_enough(first[0], last[0], 0.05, f"{action_name} left loop closure")
    close_enough(first[1], last[1], 0.05, f"{action_name} right loop closure")
    first_bias = first[0] - first[1]
    middle_bias = middle[0] - middle[1]
    if abs(first_bias) < 0.5 or abs(middle_bias) < 0.5 or first_bias * middle_bias >= 0.0:
        raise RuntimeError(
            f"{action_name} does not alternate planted feet: "
            f"first={first_bias:.3f}, middle={middle_bias:.3f}"
        )

for frame in (5, 7):
    left, right = samples["A_Ciberfantasma_Pro_Land"][frame]
    close_enough(left, right, 0.1, f"Land frame {frame} bilateral contact")

print("CF_FOOT_CONTACT_AUDIT: PASS")
