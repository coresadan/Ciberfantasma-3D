"""Print armature-space joint positions for one generated animation pose."""

import sys

import bpy


args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
action_name = args[0]
frame = int(args[1])
armature = bpy.data.objects["SK_Ciberfantasma_Chibi_Armature"]
armature.animation_data.action = bpy.data.actions[action_name]
bpy.context.scene.frame_set(frame)
bpy.context.view_layer.update()
for name in (
    "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r",
):
    bone = armature.pose.bones[name]
    print("CF_POSE", name, "head", tuple(round(v, 2) for v in bone.head),
          "tail", tuple(round(v, 2) for v in bone.tail))

mesh = bpy.data.objects["SM_Ciberfantasma_Chibi"]
evaluated_mesh = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
for group_name in ("hand_l", "hand_r", "lowerarm_l", "lowerarm_r"):
    group_index = mesh.vertex_groups[group_name].index
    indices = [vertex.index for vertex in mesh.data.vertices
               if any(item.group == group_index and item.weight > 0.99 for item in vertex.groups)]
    if indices:
        base = [mesh.data.vertices[index].co for index in indices]
        posed = [evaluated_mesh.vertices[index].co for index in indices]
        print("CF_BOUNDS", group_name,
              "base", tuple(round(v, 1) for v in (*map(min, zip(*base)), *map(max, zip(*base)))),
              "posed", tuple(round(v, 1) for v in (*map(min, zip(*posed)), *map(max, zip(*posed)))))
