"""Solve approximate two-bone arm rotations for authored gameplay targets."""

import math

import bpy
from mathutils import Vector


armature = bpy.data.objects["SK_Ciberfantasma_Chibi_Armature"]
armature.animation_data_create()
armature.animation_data.action = None
for bone in armature.pose.bones:
    bone.rotation_mode = "XYZ"
    bone.location = (0.0, 0.0, 0.0)
    bone.rotation_euler = (0.0, 0.0, 0.0)
    bone.scale = (1.0, 1.0, 1.0)
bpy.context.view_layer.update()


def solve(label, side, wrist_target, elbow_target, starts):
    upper = armature.pose.bones[f"upperarm_{side}"]
    lower = armature.pose.bones[f"lowerarm_{side}"]
    hand = armature.pose.bones[f"hand_{side}"]
    wrist_target = Vector(wrist_target)
    elbow_target = Vector(elbow_target)

    def apply(values):
        upper.rotation_euler = tuple(math.radians(value) for value in (values[0], 0.0, values[1]))
        lower.rotation_euler = tuple(math.radians(value) for value in (values[2], 0.0, values[3]))
        bpy.context.view_layer.update()

    def score(values):
        apply(values)
        wrist_error = (hand.head - wrist_target).length_squared
        elbow_error = (lower.head - elbow_target).length_squared
        return wrist_error + elbow_error * 0.22

    best_values = None
    best_score = float("inf")
    for start in starts:
        values = list(start)
        current_score = score(values)
        for step in (32.0, 16.0, 8.0, 4.0, 2.0, 1.0):
            improved = True
            while improved:
                improved = False
                for index in range(4):
                    for direction in (-1.0, 1.0):
                        candidate = values.copy()
                        candidate[index] = max(-150.0, min(150.0, candidate[index] + step * direction))
                        candidate_score = score(candidate)
                        if candidate_score + 0.0001 < current_score:
                            values = candidate
                            current_score = candidate_score
                            improved = True
        if current_score < best_score:
            best_values = values
            best_score = current_score

    apply(best_values)
    print(
        "CF_SOLVE", label, side,
        "upper_xz", tuple(round(value, 1) for value in best_values[:2]),
        "lower_xz", tuple(round(value, 1) for value in best_values[2:]),
        "wrist", tuple(round(value, 2) for value in hand.head),
        "elbow", tuple(round(value, 2) for value in lower.head),
        "score", round(best_score, 3),
    )
    upper.rotation_euler = (0.0, 0.0, 0.0)
    lower.rotation_euler = (0.0, 0.0, 0.0)
    bpy.context.view_layer.update()


starts = (
    (0, 0, 0, 0), (-60, 0, 20, 0), (0, -80, 0, 60),
    (-40, -50, 40, 40), (-20, 70, 20, -90),
)
solve("fire", "l", (-4, -43, 82), (-19, -25, 88), starts)
solve("fire_screen", "r", (4, 43, 82), (19, 25, 88), starts)
solve("fire_forward", "r", (4, -43, 82), (19, -25, 88), starts)
solve("shield", "l", (-6, -29, 80), (-31, -18, 83), starts)
solve("shield", "r", (6, -29, 80), (31, -18, 83), starts)
solve("jump", "l", (-27, -13, 113), (-43, -8, 103), starts)
solve("jump", "r", (27, -13, 113), (43, -8, 103), starts)
