"""Print rest-pose local axes for the procedural hero rig."""

import bpy


armature = bpy.data.objects["SK_Ciberfantasma_Chibi_Armature"]
for name in (
    "upperarm_l", "lowerarm_l", "upperarm_r", "lowerarm_r",
    "thigh_l", "calf_l", "thigh_r", "calf_r", "spine_02",
):
    matrix = armature.data.bones[name].matrix_local.to_3x3()
    print(
        "CF_AXIS",
        name,
        "X", tuple(round(value, 4) for value in matrix.col[0]),
        "Y", tuple(round(value, 4) for value in matrix.col[1]),
        "Z", tuple(round(value, 4) for value in matrix.col[2]),
    )
