"""Build production-ready modular chibi meshes and export them for Unreal.

The models deliberately use clean hard-surface primitives and bevelled silhouettes.
They are original 3D interpretations of the supplied Ciberfantasma Bros artwork,
not image planes or extruded sprites.
"""

from pathlib import Path
import math

import bpy
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "SourceAssets"
BLENDER_OUTPUT = SOURCE_ROOT / "Blender" / "CF_Character_Workfile.blend"
FBX_OUTPUT = SOURCE_ROOT / "FBX"
PREVIEW_OUTPUT = SOURCE_ROOT / "Previews" / "ciberfantasma_chibi_turnaround.png"


PALETTE = {
    "M_CF_Hood": ((0.045, 0.052, 0.064, 1.0), 0.0, 0.38, None),
    "M_CF_Armor": ((0.26, 0.285, 0.32, 1.0), 0.22, 0.32, None),
    "M_CF_Bone": ((1.0, 1.0, 0.98, 1.0), 0.0, 0.22, (0.35, 0.35, 0.32, 0.35)),
    "M_CF_Green": ((0.002, 0.62, 0.012, 1.0), 0.08, 0.2, (0.0, 0.65, 0.01, 0.8)),
    "M_CF_Visor": ((0.001, 0.003, 0.004, 1.0), 0.1, 0.08, None),
    "M_Warden_Ivory": ((0.48, 0.44, 0.36, 1.0), 0.7, 0.24, None),
    "M_Enemy_Dark": ((0.012, 0.016, 0.024, 1.0), 0.8, 0.22, None),
    "M_Enemy_Red": ((0.45, 0.004, 0.018, 1.0), 0.48, 0.16, (1.0, 0.005, 0.02, 8.0)),
    "M_Drone_Silver": ((0.34, 0.39, 0.43, 1.0), 0.88, 0.18, None),
    "M_Drone_Magenta": ((0.38, 0.004, 0.34, 1.0), 0.45, 0.12, (1.0, 0.01, 0.8, 10.0)),
    "M_Drone_Cyan": ((0.005, 0.28, 0.48, 1.0), 0.4, 0.15, (0.01, 0.65, 1.0, 7.0)),
    # Bot (basic ground soldier) - green visor
    "M_Bot_Green": ((0.003, 0.48, 0.012, 1.0), 0.12, 0.22, (0.005, 0.9, 0.02, 7.0)),
    # Crawler - compact heavy enforcer with orange hazard trim
    "M_Crawler_Orange": ((0.55, 0.14, 0.002, 1.0), 0.62, 0.2, (1.0, 0.28, 0.004, 6.0)),
    "M_Crawler_Heavy": ((0.018, 0.022, 0.028, 1.0), 0.85, 0.18, None),
    # Harvester - surveillance drone, teal sensor
    "M_Harvester_Teal": ((0.003, 0.42, 0.38, 1.0), 0.35, 0.15, (0.005, 0.85, 0.75, 9.0)),
    "M_Harvester_Gold": ((0.45, 0.32, 0.02, 1.0), 0.78, 0.2, None),
    # Enforcer - riot police, blue shield
    "M_Enforcer_Blue": ((0.004, 0.06, 0.38, 1.0), 0.25, 0.28, (0.006, 0.08, 0.85, 5.0)),
    "M_Enforcer_Grey": ((0.16, 0.19, 0.22, 1.0), 0.72, 0.24, None),
    # Auditor - bureaucratic robot, yellow accent
    "M_Auditor_Yellow": ((0.52, 0.42, 0.002, 1.0), 0.3, 0.2, (1.0, 0.82, 0.004, 6.0)),
    "M_Auditor_White": ((0.72, 0.74, 0.76, 1.0), 0.15, 0.35, None),
    # CEO-9000 boss - corporate megalith, gold and red
    "M_CEO_Gold": ((0.62, 0.46, 0.02, 1.0), 0.85, 0.16, (1.0, 0.74, 0.03, 12.0)),
    "M_CEO_Dark": ((0.008, 0.008, 0.012, 1.0), 0.92, 0.14, None),
    "M_CEO_Red": ((0.68, 0.003, 0.003, 1.0), 0.35, 0.14, (1.0, 0.006, 0.006, 14.0)),
    # Director - final boss, pure white authority, red eye
    "M_Director_White": ((0.85, 0.88, 0.9, 1.0), 0.12, 0.28, None),
    "M_Director_Red": ((0.72, 0.003, 0.003, 1.0), 0.2, 0.12, (1.0, 0.005, 0.005, 16.0)),
    "M_Director_Black": ((0.004, 0.004, 0.006, 1.0), 0.94, 0.12, None),
}

# Names of all enemy static-mesh FBX outputs (shared with import script).
ALL_ENEMY_FBX = [
    "SM_LicenseWarden_Chibi",
    "SM_PanopticonDrone_Chibi",
    "SM_BotGround_Chibi",
    "SM_Crawler_Chibi",
    "SM_Harvester_Chibi",
    "SM_Enforcer_Chibi",
    "SM_Auditor_Chibi",
    "SM_CEO9000_Chibi",
    "SM_Director_Chibi",
]



def clean_scene():
    if bpy.context.object and bpy.context.object.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            datablocks.remove(block)


def make_material(name, base, metallic, roughness, emission):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    material.diffuse_color = base
    node = material.node_tree.nodes.get("Principled BSDF")
    node.inputs["Base Color"].default_value = base
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    if emission:
        color = (*emission[:3], 1.0)
        emission_input = node.inputs.get("Emission Color") or node.inputs.get("Emission")
        if emission_input:
            emission_input.default_value = color
        strength_input = node.inputs.get("Emission Strength")
        if strength_input:
            strength_input.default_value = emission[3]
    return material


def add_bevel(obj, width=1.8, segments=2):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    modifier = obj.modifiers.new("CF_EdgeBevel", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.select_set(False)
    return obj


def assign(obj, material):
    obj.data.materials.append(material)
    return obj


def cube(name, location, scale, material, bevel=1.5, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    assign(obj, material)
    return add_bevel(obj, min(bevel, min(scale) * 0.45), 2)


def sphere(name, location, scale, material, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    assign(obj, material)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.select_set(False)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0.0, 0.0, 0.0), vertices=24, bevel=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    return add_bevel(obj, bevel, 2)


def cone(name, location, radius1, radius2, depth, material, rotation=(0.0, 0.0, 0.0), vertices=24):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2, depth=depth,
        location=location, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    return add_bevel(obj, 0.8, 2)


def capsule_between(name, start, end, radius, material):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    midpoint = (start_v + end_v) * 0.5
    obj = cylinder(name, midpoint, radius, direction.length, material, bevel=radius * 0.25)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0.0, 0.0, 1.0)).rotation_difference(direction.normalized())
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    sphere(name + "_A", start_v, (radius, radius, radius), material, 20, 12)
    sphere(name + "_B", end_v, (radius, radius, radius), material, 20, 12)


def ring(name, location, major_radius, minor_radius, material, rotation=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius, minor_radius=minor_radius,
        major_segments=32, minor_segments=10, location=location, rotation=rotation
    )
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.select_set(False)
    return obj


def scale_mesh(obj, scale):
    obj.scale = scale
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)
    return obj


def tube_path(name, points, radius, material, cyclic=False):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    assign(obj, material)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj.name = name
    obj.select_set(False)
    return obj


def front_ring(name, location, radius, thickness, material, scale=(1.0, 1.0, 1.0)):
    obj = ring(name, location, radius, thickness, material, (math.radians(90), 0.0, 0.0))
    return scale_mesh(obj, scale)


def prism_xz(name, points, y, depth, material, bevel=0.8):
    """Create a bevelled plate from an authored front-view X/Z contour."""
    signed_area = sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )
    if signed_area < 0.0:
        points = list(reversed(points))
    count = len(points)
    front_y = y - depth * 0.5
    back_y = y + depth * 0.5
    vertices = [(x, front_y, z) for x, z in points] + [(x, back_y, z) for x, z in points]
    faces = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((index, nxt, count + nxt, count + index))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, material)
    return add_bevel(obj, bevel, 3)


def mirrored_points(points):
    return [(-x, z) for x, z in reversed(points)]


def join_named(name, prefix):
    objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name.startswith(prefix)]
    if not objects:
        raise RuntimeError(f"No mesh parts found for {prefix}")
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    result = bpy.context.object
    result.name = name
    bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    result["cf_asset"] = name
    result["cf_style"] = "chibi hard-surface"
    return result


def build_ciberfantasma(materials):
    p = "CFP_"
    armor = materials["M_CF_Armor"]
    hood = materials["M_CF_Hood"]
    bone = materials["M_CF_Bone"]
    green = materials["M_CF_Green"]
    visor = materials["M_CF_Visor"]

    # Blender -Y is character forward and becomes Unreal +X on FBX import.
    # The hood uses a rounded crown plus flared lower panels instead of a sphere.
    sphere(p + "HoodVolume", (0, 2, 128), (42, 35, 39), hood, 64, 40)
    sphere(p + "HoodCrown", (0, 3, 148), (35, 31, 18), armor, 48, 30)
    for side in (-1, 1):
        contour = [(7, 158), (27, 153), (38, 137), (40, 116), (34, 101), (24, 96),
                   (18, 111), (26, 126), (25, 143)]
        if side < 0:
            contour = mirrored_points(contour)
        prism_xz(p + f"HoodSidePanel{side}", contour, -29.0, 7.0, armor, 1.6)
    face_opening = [(-24, 148), (-33, 138), (-34, 120), (-28, 104), (-16, 98),
                    (0, 96), (16, 98), (28, 104), (34, 120), (33, 138), (24, 148),
                    (12, 154), (0, 156), (-12, 154)]
    prism_xz(p + "InnerMask", face_opening, -35.5, 4.2, visor, 1.4)
    tube_path(p + "HoodRim", [(x, -39.0, z) for x, z in face_opening], 2.0, armor, True)
    tube_path(p + "HoodCenterSeam", [(0, -30, 165), (0, -34, 157), (0, -37, 150)], 0.75, hood)

    # Authored skull mask. The eye contours are angular/almond shaped like the concept.
    left_eye = [(-28, 135), (-22, 139), (-13, 139), (-6, 135), (-8, 129),
                (-14, 125), (-23, 126), (-28, 130)]
    right_eye = mirrored_points(left_eye)
    for label, eye in (("L", left_eye), ("R", right_eye)):
        prism_xz(p + f"EyeSocket{label}", eye, -40.2, 3.0, visor, 0.8)
        tube_path(p + f"EyeRim{label}", [(x, -42.3, z) for x, z in eye], 2.15, bone, True)

    left_brow = [(-28, 140), (-24, 147), (-13, 150), (-5, 144), (-8, 141),
                 (-15, 146), (-23, 144)]
    prism_xz(p + "BrowL", left_brow, -42.0, 3.2, bone, 0.9)
    prism_xz(p + "BrowR", mirrored_points(left_brow), -42.0, 3.2, bone, 0.9)
    cube(p + "NoseBridge", (0, -42.0, 132), (2.4, 1.8, 7.0), bone, 0.8)
    prism_xz(p + "Nose", [(-5, 121), (0, 130), (5, 121), (2, 116), (-2, 116)],
             -42.3, 3.4, visor, 0.7)
    left_cheek = [(-29, 122), (-24, 114), (-16, 108), (-8, 112), (-10, 117),
                  (-17, 113), (-23, 118)]
    prism_xz(p + "CheekL", left_cheek, -42.0, 3.4, bone, 1.0)
    prism_xz(p + "CheekR", mirrored_points(left_cheek), -42.0, 3.4, bone, 1.0)
    for index, x in enumerate((-7.5, -2.5, 2.5, 7.5)):
        prism_xz(p + f"Tooth{index}", [(x - 1.6, 106), (x + 1.6, 106),
                                         (x + 1.4, 98), (x - 1.4, 98)], -42.3, 3.0, bone, 0.55)

    # Green power icon and the three parallel circuit traces on each side of the hood.
    tube_path(p + "PowerArc", [(-6, -43.0, 157), (-8, -43.0, 153), (-7, -43.0, 149),
                                (-4, -43.0, 146), (0, -43.0, 145), (4, -43.0, 146),
                                (7, -43.0, 149), (8, -43.0, 153), (6, -43.0, 157)], 1.45, green)
    cube(p + "PowerStem", (0, -43.0, 156), (1.5, 1.3, 7.0), green, 0.65)
    for side in (-1, 1):
        for trace in range(3):
            offset = trace * 3.0
            tube_path(p + f"HoodCircuit{side}_{trace}", [
                (side * (31 + offset), -34.5 + trace, 145),
                (side * (34 + offset), -35.0 + trace, 138),
                (side * (33 + offset), -35.2 + trace, 130),
                (side * (37 + offset), -32.0 + trace, 123)
            ], 0.65, green)

    # Compact armoured torso with the V-shaped layered plate language of the reference.
    sphere(p + "TorsoCore", (0, 0, 78), (29, 20, 31), hood, 40, 26)
    prism_xz(p + "Collar", [(-18, 102), (-5, 98), (0, 92), (5, 98), (18, 102),
                             (12, 108), (0, 104), (-12, 108)], -19.0, 6.0, armor, 1.3)
    left_chest = [(-3, 96), (-10, 101), (-25, 98), (-29, 87), (-21, 78),
                  (-7, 82), (-3, 88)]
    prism_xz(p + "ChestPlateL", left_chest, -22.0, 7.0, armor, 1.6)
    prism_xz(p + "ChestPlateR", mirrored_points(left_chest), -22.0, 7.0, armor, 1.6)
    tube_path(p + "ChestPanelSeamL", [(x, -26.0, z) for x, z in left_chest], 0.42, hood, True)
    tube_path(p + "ChestPanelSeamR", [(x, -26.0, z) for x, z in mirrored_points(left_chest)],
              0.42, hood, True)
    prism_xz(p + "Sternum", [(-4, 96), (4, 96), (6, 82), (0, 76), (-6, 82)],
             -26.0, 5.0, armor, 1.0)
    prism_xz(p + "ChestCore", [(-4, 91), (4, 91), (6, 87), (0, 84), (-6, 87)],
             -29.0, 3.0, green, 0.7)
    for side in (-1, 1):
        tube_path(p + f"ChestGlow{side}", [
            (side * 5, -27.0, 96), (side * 13, -27.0, 95), (side * 21, -26.0, 90)
        ], 1.0, green)
        prism_xz(p + f"RibPlate{side}", [
            (side * 5, 79), (side * 20, 76), (side * 23, 70),
            (side * 12, 67), (side * 5, 71)
        ], -21.5, 6.0, armor, 1.0)
        tube_path(p + f"RibGlow{side}", [
            (side * 22, -25.0, 79), (side * 25, -24.0, 74), (side * 22, -24.0, 69)
        ], 0.8, green)
    for index, z in enumerate((77, 71, 65)):
        width = 12 - index
        prism_xz(p + f"AbPlate{index}", [(-width, z + 3), (width, z + 3),
                                           (width - 2, z - 2), (0, z - 4),
                                           (-width + 2, z - 2)], -25.0, 4.2, armor, 0.9)
    prism_xz(p + "PelvisPlate", [(-21, 62), (-10, 64), (0, 59), (10, 64), (21, 62),
                                  (17, 52), (0, 49), (-17, 52)], -19.0, 6.0, armor, 1.5)
    cube(p + "Belt", (0, 0, 54), (23, 20, 4), hood, 1.8)
    prism_xz(p + "BeltGlow", [(-5, 58), (5, 58), (6, 54), (0, 52), (-6, 54)],
             -22.5, 3.0, green, 0.6)

    # Broad shoulders, short limbs and large hands/boots preserve chibi weight.
    for side in (-1, 1):
        x = side * 32
        sphere(p + f"Shoulder{side}", (x, 0, 88), (17, 15, 15), armor, 28, 18)
        shoulder_plate = [(side * 24, 98), (side * 34, 104), (side * 45, 99),
                          (side * 48, 91), (side * 39, 87), (side * 27, 91)]
        prism_xz(p + f"ShoulderPlate{side}", shoulder_plate, -12.0, 6.0, armor, 1.4)
        tube_path(p + f"ShoulderSeam{side}", [
            (side * 29, -16, 99), (side * 38, -17, 98), (side * 44, -15, 93)
        ], 0.75, green)
        capsule_between(p + f"UpperArm{side}", (side * 34, 0, 82), (side * 37, -2, 66), 8.5, hood)
        prism_xz(p + f"BicepPlate{side}", [(side * 29, 82), (side * 39, 85),
                                            (side * 44, 76), (side * 40, 69),
                                            (side * 31, 72)], -11.0, 5.0, armor, 1.0)
        cylinder(p + f"Elbow{side}", (side * 38, -2, 64), 7.5, 8, armor, (0, math.radians(90), 0), bevel=1.0)
        capsule_between(p + f"Forearm{side}", (side * 38, -2, 61), (side * 39, -6, 48), 9.5, armor)
        prism_xz(p + f"ForearmPlate{side}", [(side * 31, 63), (side * 42, 66),
                                              (side * 47, 54), (side * 43, 46),
                                              (side * 32, 49)], -12.0, 5.0, armor, 1.0)
        sphere(p + f"Fist{side}", (side * 39, -8, 43), (11, 10, 10), hood, 28, 16)
        for finger in range(3):
            cube(p + f"Knuckle{side}_{finger}",
                 (side * (34 + finger * 4), -17.5, 45), (2.0, 2.0, 2.0), armor, 0.8)
        cube(p + f"ForearmGlow{side}", (side * 39, -16, 57), (4.5, 1.2, 2.0), green, 0.5)

        sphere(p + f"Hip{side}", (side * 14, 0, 50), (13, 12, 13), armor, 26, 16)
        capsule_between(p + f"Thigh{side}", (side * 14, 0, 47), (side * 15, 0, 29), 10.5, hood)
        prism_xz(p + f"ThighPlate{side}", [(side * 5, 48), (side * 13, 55),
                                            (side * 25, 48), (side * 24, 35),
                                            (side * 15, 30), (side * 7, 37)],
                 -9.5, 5.0, armor, 1.1)
        tube_path(p + f"ThighSeam{side}", [(side * 9, -12.2, 47),
                                            (side * 15, -12.2, 51),
                                            (side * 22, -12.2, 46)], 0.45, hood)
        sphere(p + f"Knee{side}", (side * 15, -10, 27), (9.5, 6.5, 8.5), armor, 24, 15)
        prism_xz(p + f"KneeCap{side}", [(side * 7, 29), (side * 11, 34),
                                         (side * 20, 34), (side * 24, 28),
                                         (side * 20, 20), (side * 10, 20)],
                 -16.0, 3.5, armor, 0.9)
        tube_path(p + f"KneeGlow{side}", [(side * 9, -18, 25), (side * 15, -18, 21),
                                           (side * 22, -18, 25)], 0.75, green)
        capsule_between(p + f"Shin{side}", (side * 15, 0, 24), (side * 15, 0, 11), 9.5, armor)
        prism_xz(p + f"ShinPlate{side}", [(side * 7, 22), (side * 12, 27),
                                           (side * 23, 23), (side * 22, 10),
                                           (side * 16, 6), (side * 8, 10)],
                 -10.0, 4.5, armor, 1.0)
        tube_path(p + f"ShinSeam{side}", [(side * 10, -13.0, 18),
                                           (side * 16, -13.0, 14),
                                           (side * 21, -13.0, 18)], 0.4, hood)
        sphere(p + f"Boot{side}", (side * 15, -6, 8), (14, 17, 9), hood, 28, 16)
        sphere(p + f"BootToe{side}", (side * 15, -20, 7), (12, 9, 6), armor, 24, 14)
        cube(p + f"BootSole{side}", (side * 15, -7, 2), (15, 19, 2.2), hood, 1.4)
        cube(p + f"BootGlowOuter{side}", (side * 20, -28.0, 8), (2.8, 0.8, 1.0), green, 0.35,
             (0.0, 0.0, side * math.radians(-18)))
        cube(p + f"BootGlowInner{side}", (side * 11, -28.0, 8), (2.8, 0.8, 1.0), green, 0.35,
             (0.0, 0.0, side * math.radians(18)))

    # Wrist computer/pulse emitter from the canonical concept.
    cube(p + "WristComputer", (-40, -14, 58), (8, 5, 7), armor, 1.8,
         (0.0, 0.0, math.radians(-8)))
    cube(p + "WristScreen", (-40, -19.5, 59), (5.5, 1.0, 4.5), green, 0.5,
         (0.0, 0.0, math.radians(-8)))
    cube(p + "RightBracer", (40, -12, 55), (8, 5, 7), armor, 1.8,
         (0.0, 0.0, math.radians(8)))
    tube_path(p + "RightBracerGlow", [(35, -18, 58), (40, -18, 61), (45, -18, 58)], 0.8, green)

    # Back armour seams make the turnaround intentional rather than hollow.
    cube(p + "BackSpine", (0, 19, 79), (5, 3, 24), armor, 1.2)
    for side in (-1, 1):
        tube_path(p + f"BackGlow{side}", [
            (side * 6, 22, 95), (side * 13, 22, 84), (side * 10, 22, 71)
        ], 1.0, green)
    return join_named("SM_Ciberfantasma_Chibi", p)


def build_warden(materials):
    p = "WRD_"
    dark = materials["M_Enemy_Dark"]
    ivory = materials["M_Warden_Ivory"]
    red = materials["M_Enemy_Red"]

    cube(p + "VaultBody", (0, 0, 78), (34, 28, 37), ivory, 5.0)
    cube(p + "BackCasing", (-8, 0, 82), (33, 31, 39), dark, 5.0)
    cube(p + "Head", (3, 0, 126), (28, 27, 15), dark, 4.0)
    cube(p + "Visor", (30, 0, 127), (3, 19, 8), dark, 1.2)
    for side in (-1, 1):
        cylinder(p + f"Eye{side}", (34, side * 9, 129), 4.5, 3, red, (0, math.radians(90), 0), bevel=0.5)
        sphere(p + f"Shoulder{side}", (0, side * 40, 94), (19, 16, 20), ivory, 24, 14)
        capsule_between(p + f"Arm{side}", (0, side * 40, 86), (10, side * 42, 56), 11, dark)
        if side < 0:
            sphere(p + "Clamp", (19, side * 42, 45), (13, 12, 13), dark, 24, 14)
        else:
            cube(p + "Stamp", (21, side * 42, 47), (15, 13, 10), red, 2.5)
        sphere(p + f"Hip{side}", (0, side * 17, 40), (13, 13, 12), dark, 24, 14)
        capsule_between(p + f"Leg{side}", (0, side * 17, 38), (4, side * 18, 16), 11, dark)
        cube(p + f"Foot{side}", (10, side * 18, 7), (17, 14, 7), dark, 3.0)
        cylinder(p + f"Joint{side}", (6, side * 31, 67), 5, 6, red, (math.radians(90), 0, 0), bevel=0.5)
        cube(p + f"SideArmor{side}", (1, side * 32, 82), (24, 3, 26), ivory, 3.0)
        cylinder(p + f"SideEye{side}", (8, side * 36, 128), 5, 3, red, (math.radians(90), 0, 0), bevel=0.5)
    cube(p + "LockPlate", (36, 0, 77), (3.5, 14, 17), dark, 2.0)
    cylinder(p + "LockCore", (40, 0, 80), 6, 3, red, (0, math.radians(90), 0), bevel=0.5)
    return join_named("SM_LicenseWarden_Chibi", p)


def build_drone(materials):
    p = "DRN_"
    dark = materials["M_Enemy_Dark"]
    silver = materials["M_Drone_Silver"]
    magenta = materials["M_Drone_Magenta"]
    cyan = materials["M_Drone_Cyan"]

    sphere(p + "Core", (0, 0, 62), (35, 29, 34), dark, 40, 24)
    ring(p + "EyeHousing", (31, 0, 64), 19, 5, silver, (0, math.radians(90), 0))
    cylinder(p + "Eye", (36, 0, 64), 14, 5, magenta, (0, math.radians(90), 0), 32, 0.7)
    sphere(p + "EyeLens", (40, 0, 64), (3, 9, 9), magenta, 24, 14)
    for side in (-1, 1):
        capsule_between(p + f"WingArm{side}", (0, side * 25, 61), (2, side * 47, 52), 7, dark)
        cube(p + f"Wing{side}", (2, side * 61, 49), (9, 24, 7), dark, 2.5, (math.radians(side * 18), 0, 0))
        cube(p + f"WingGlow{side}", (8, side * 67, 50), (2, 15, 2), magenta, 0.6, (math.radians(side * 18), 0, 0))
        cylinder(p + f"Thruster{side}", (-4, side * 47, 50), 8, 12, silver, (math.radians(90), 0, 0), bevel=1.0)
        ring(p + f"SideEyeHousing{side}", (9, side * 30, 66), 16, 4, silver, (math.radians(90), 0, 0))
        cylinder(p + f"SideEye{side}", (9, side * 34, 66), 11, 4, magenta, (math.radians(90), 0, 0), 28, 0.6)
    cone(p + "Antenna", (0, 0, 103), 13, 2, 40, dark)
    cube(p + "AntennaGlow", (8, 0, 104), (2, 5, 8), magenta, 0.6, (0, math.radians(-12), 0))
    ring(p + "LowerRing", (0, 0, 31), 27, 3, silver)
    cylinder(p + "LowerThruster", (0, 0, 28), 10, 13, dark, bevel=1.0)
    cylinder(p + "LowerGlow", (0, 0, 20), 6, 2, cyan, bevel=0.5)
    return join_named("SM_PanopticonDrone_Chibi", p)


def export_fbx(obj):
    FBX_OUTPUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    path = FBX_OUTPUT / f"{obj.name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y", axis_up="Z", bake_anim=False,
        add_leaf_bones=False, mesh_smooth_type="FACE"
    )
    print(f"Exported {path}")


def rig_player(mesh):
    """Create a layered chibi rig with separate torso, clavicle, hand and toe controls."""
    armature_data = bpy.data.armatures.new("SK_Ciberfantasma_Chibi_Skeleton")
    armature = bpy.data.objects.new("SK_Ciberfantasma_Chibi_Armature", armature_data)
    bpy.context.collection.objects.link(armature)
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")

    definitions = {
        "root": ((0, 0, 0), (0, 0, 12), None),
        "pelvis": ((0, 0, 49), (0, 0, 62), "root"),
        "spine_01": ((0, 0, 62), (0, 0, 80), "pelvis"),
        "spine_02": ((0, 0, 80), (0, 0, 101), "spine_01"),
        "neck": ((0, 0, 101), (0, 0, 112), "spine_02"),
        "head": ((0, 0, 112), (0, 0, 151), "neck"),
        "clavicle_l": ((-3, 0, 97), (-25, 0, 94), "spine_02"),
        "upperarm_l": ((-25, 0, 94), (-36, 0, 68), "clavicle_l"),
        "lowerarm_l": ((-36, 0, 68), (-39, -5, 49), "upperarm_l"),
        "hand_l": ((-39, -5, 49), (-39, -9, 39), "lowerarm_l"),
        "weapon_l": ((-39, -10, 63), (-39, -18, 55), "lowerarm_l"),
        "clavicle_r": ((3, 0, 97), (25, 0, 94), "spine_02"),
        "upperarm_r": ((25, 0, 94), (36, 0, 68), "clavicle_r"),
        "lowerarm_r": ((36, 0, 68), (39, -5, 49), "upperarm_r"),
        "hand_r": ((39, -5, 49), (39, -9, 39), "lowerarm_r"),
        "thigh_l": ((-14, 0, 54), (-15, 0, 29), "pelvis"),
        "calf_l": ((-15, 0, 29), (-15, 0, 10), "thigh_l"),
        "foot_l": ((-15, 0, 10), (-15, -16, 5), "calf_l"),
        "toe_l": ((-15, -16, 5), (-15, -27, 5), "foot_l"),
        "thigh_r": ((14, 0, 54), (15, 0, 29), "pelvis"),
        "calf_r": ((15, 0, 29), (15, 0, 10), "thigh_r"),
        "foot_r": ((15, 0, 10), (15, -16, 5), "calf_r"),
        "toe_r": ((15, -16, 5), (15, -27, 5), "foot_r"),
    }
    created = {}
    for name, (head_position, tail_position, parent_name) in definitions.items():
        bone = armature_data.edit_bones.new(name)
        bone.head = head_position
        bone.tail = tail_position
        if parent_name:
            bone.parent = created[parent_name]
        created[name] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.select_set(False)

    groups = {name: mesh.vertex_groups.new(name=name) for name in definitions}
    for vertex in mesh.data.vertices:
        x, y, z = vertex.co
        side = "l" if x < 0 else "r"
        if z >= 108:
            bone_name = "head"
        elif abs(x) >= 25 and z >= 84:
            bone_name = f"clavicle_{side}"
        elif x < -31 and y < -9 and 49 <= z <= 66:
            bone_name = "weapon_l"
        elif abs(x) >= 27 and z >= 65:
            bone_name = f"upperarm_{side}"
        elif abs(x) >= 27 and z >= 47:
            bone_name = f"lowerarm_{side}"
        elif abs(x) >= 27:
            bone_name = f"hand_{side}"
        elif z < 8 and y < -13 and abs(x) > 2:
            bone_name = f"toe_{side}"
        elif z < 12 and abs(x) > 2:
            bone_name = f"foot_{side}"
        elif z < 30 and abs(x) > 3:
            bone_name = f"calf_{side}"
        elif z < 55 and abs(x) > 3:
            bone_name = f"thigh_{side}"
        elif z < 64:
            bone_name = "pelvis"
        elif z < 81:
            bone_name = "spine_01"
        elif z < 101:
            bone_name = "spine_02"
        else:
            bone_name = "neck"
        groups[bone_name].add([vertex.index], 1.0, "REPLACE")

    modifier = mesh.modifiers.new("CiberfantasmaRig", "ARMATURE")
    modifier.object = armature
    mesh.parent = armature
    return armature


def export_skeletal_fbx(mesh, armature):
    bpy.ops.object.select_all(action="DESELECT")
    mesh.select_set(True)
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    path = FBX_OUTPUT / "SK_Ciberfantasma_Chibi_Pro.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"MESH", "ARMATURE"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Y", axis_up="Z", bake_anim=False,
        add_leaf_bones=False, mesh_smooth_type="FACE", use_armature_deform_only=True
    )
    print(f"Exported {path}")


def build_player_actions(armature):
    """Author a complete, readable 2.5D gameplay animation set at 60 fps."""
    scene = bpy.context.scene
    armature.animation_data_create()
    actions = {}

    def new_action(name, end_frame):
        action = bpy.data.actions.new(name)
        armature.animation_data.action = action
        scene.frame_start = 1
        scene.frame_end = end_frame
        for bone in armature.pose.bones:
            bone.rotation_mode = "XYZ"
            bone.location = (0.0, 0.0, 0.0)
            bone.rotation_euler = (0.0, 0.0, 0.0)
            bone.scale = (1.0, 1.0, 1.0)
        actions[name] = action
        return action

    def key(frame, values):
        scene.frame_set(frame)
        for bone_name, channels in values.items():
            bone = armature.pose.bones[bone_name]
            if "location" in channels:
                bone.location = channels["location"]
                bone.keyframe_insert(data_path="location", frame=frame, group=bone_name)
            if "rotation" in channels:
                bone.rotation_euler = tuple(math.radians(value) for value in channels["rotation"])
                bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone_name)
            if "scale" in channels:
                bone.scale = channels["scale"]
                bone.keyframe_insert(data_path="scale", frame=frame, group=bone_name)

    # Idle: asymmetrical breathing, a small weight shift and a scanning hood.
    new_action("A_Ciberfantasma_Pro_Idle", 96)
    idle_poses = (
        (1, 0.0, -1.5, -1.0, -2.0, 2.0),
        (24, 0.8, 0.2, 0.5, 1.0, -1.0),
        (48, 1.6, 1.4, 1.2, 2.5, -2.0),
        (72, 0.7, 0.0, 0.3, -1.0, 1.0),
        (96, 0.0, -1.5, -1.0, -2.0, 2.0),
    )
    for frame, lift, pelvis_roll, chest_roll, head_turn, hand_turn in idle_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, lift * 0.35), "rotation": (0, 0, pelvis_roll)},
            "spine_01": {"rotation": (0, 0, -pelvis_roll * 0.55)},
            "spine_02": {"location": (0, 0, lift), "rotation": (0, 0, chest_roll)},
            "neck": {"rotation": (0, head_turn * 0.35, -chest_roll * 0.35)},
            "head": {"location": (0, 0, lift * 0.3), "rotation": (0, head_turn, -chest_roll * 0.5)},
            "clavicle_l": {"rotation": (0, 0, -1.5 - lift)},
            "clavicle_r": {"rotation": (0, 0, 1.5 + lift)},
            "hand_l": {"rotation": (0, hand_turn, -2)},
            "hand_r": {"rotation": (0, -hand_turn, 2)},
        })

    # Run: contact, compression, passing and flight poses with planted feet.
    new_action("A_Ciberfantasma_Pro_Run", 25)
    run_poses = (
        (1, 29, -25, 8, 28, -10, -28, 22, 1.0, -3.0),
        (4, 18, -13, 24, 15, -6, -18, 13, -1.5, -1.0),
        (7, 0, 4, 36, 5, 3, 0, 0, 1.2, 1.0),
        (10, -15, 18, 18, 6, 18, 15, -14, 3.4, 2.5),
        (13, -25, 29, 10, 8, 28, 22, -28, 1.0, 3.0),
        (16, -13, 18, 15, 24, 15, 13, -18, -1.5, 1.0),
        (19, 4, 0, 5, 36, 0, 0, 3, 1.2, -1.0),
        (22, 18, -15, 6, 18, -14, -14, 15, 3.4, -2.5),
        (25, 29, -25, 8, 28, -10, -28, 22, 1.0, -3.0),
    )
    for frame, thigh_l, thigh_r, calf_l, calf_r, foot_l, foot_r, arm_l, bob, roll in run_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, bob), "rotation": (0, 0, roll)},
            "spine_01": {"rotation": (0, -5, -roll * 0.5)},
            "spine_02": {"rotation": (0, -7, -roll * 0.35)},
            "neck": {"rotation": (0, 4, roll * 0.2)},
            "head": {"location": (0, 0, -bob * 0.2), "rotation": (0, 4, -roll * 0.45)},
            "thigh_l": {"rotation": (0, 0, thigh_l)},
            "thigh_r": {"rotation": (0, 0, thigh_r)},
            "calf_l": {"rotation": (0, 0, calf_l)},
            "calf_r": {"rotation": (0, 0, calf_r)},
            "foot_l": {"rotation": (0, 0, foot_l)},
            "foot_r": {"rotation": (0, 0, foot_r)},
            "toe_l": {"rotation": (0, 0, -foot_l * 0.4)},
            "toe_r": {"rotation": (0, 0, -foot_r * 0.4)},
            "clavicle_l": {"rotation": (0, 0, arm_l * 0.16)},
            "clavicle_r": {"rotation": (0, 0, arm_l * -0.16)},
            "upperarm_l": {"rotation": (0, 0, arm_l)},
            "upperarm_r": {"rotation": (0, 0, -arm_l)},
            "lowerarm_l": {"rotation": (0, 0, -18 - arm_l * 0.22)},
            "lowerarm_r": {"rotation": (0, 0, 18 + arm_l * 0.22)},
        })

    new_action("A_Ciberfantasma_Pro_JumpStart", 12)
    jump_start = (
        (1, 0, 0, 0, 0),
        (6, -5, -16, 30, -16),
        (12, 5, 12, 12, 28),
    )
    for frame, pelvis_z, chest, legs, arms in jump_start:
        key(frame, {
            "pelvis": {"location": (0, 0, pelvis_z), "rotation": (0, 0, 0)},
            "spine_01": {"rotation": (0, 0, chest * 0.35)},
            "spine_02": {"rotation": (0, 0, chest * 0.65)},
            "head": {"rotation": (0, 0, -chest * 0.25)},
            "thigh_l": {"rotation": (0, 0, legs)}, "thigh_r": {"rotation": (0, 0, -legs)},
            "calf_l": {"rotation": (0, 0, -34)}, "calf_r": {"rotation": (0, 0, 34)},
            "upperarm_l": {"rotation": (0, 0, arms)}, "upperarm_r": {"rotation": (0, 0, -arms)},
        })

    new_action("A_Ciberfantasma_Pro_JumpRise", 24)
    for frame, lift, spread in ((1, 1.0, 18), (12, 3.0, 23), (24, 1.0, 18)):
        key(frame, {
            "pelvis": {"location": (0, 0, lift), "rotation": (0, 0, -2)},
            "spine_01": {"rotation": (0, -5, 3)}, "spine_02": {"rotation": (0, -7, 2)},
            "head": {"rotation": (0, 4, -2)},
            "thigh_l": {"rotation": (0, 0, spread)}, "thigh_r": {"rotation": (0, 0, -spread)},
            "calf_l": {"rotation": (0, 0, -28)}, "calf_r": {"rotation": (0, 0, 28)},
            "foot_l": {"rotation": (0, 0, -15)}, "foot_r": {"rotation": (0, 0, 15)},
            "upperarm_l": {"rotation": (0, 0, 34)}, "upperarm_r": {"rotation": (0, 0, -34)},
            "lowerarm_l": {"rotation": (0, 0, -20)}, "lowerarm_r": {"rotation": (0, 0, 20)},
        })

    new_action("A_Ciberfantasma_Pro_JumpFall", 24)
    for frame, lift, spread in ((1, 1.0, 10), (12, -1.0, 15), (24, 1.0, 10)):
        key(frame, {
            "pelvis": {"location": (0, 0, lift), "rotation": (0, 0, 2)},
            "spine_01": {"rotation": (0, 5, -2)}, "spine_02": {"rotation": (0, 8, -3)},
            "head": {"rotation": (0, -5, 3)},
            "thigh_l": {"rotation": (0, 0, spread)}, "thigh_r": {"rotation": (0, 0, -spread)},
            "calf_l": {"rotation": (0, 0, 18)}, "calf_r": {"rotation": (0, 0, -18)},
            "foot_l": {"rotation": (0, 0, 12)}, "foot_r": {"rotation": (0, 0, -12)},
            "upperarm_l": {"rotation": (0, 0, -22)}, "upperarm_r": {"rotation": (0, 0, 22)},
        })

    new_action("A_Ciberfantasma_Pro_Land", 16)
    land_poses = ((1, 2, 4, 0), (5, -7, -17, 26), (10, -4, -9, 15), (16, 0, 0, 0))
    for frame, pelvis_z, chest, knee in land_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, pelvis_z), "rotation": (0, 0, 0)},
            "spine_01": {"rotation": (0, 0, chest * 0.4)},
            "spine_02": {"rotation": (0, 0, chest * 0.6)},
            "head": {"location": (0, 0, -pelvis_z * 0.25), "rotation": (0, 0, -chest * 0.25)},
            "thigh_l": {"rotation": (0, 0, knee)}, "thigh_r": {"rotation": (0, 0, -knee)},
            "calf_l": {"rotation": (0, 0, -knee * 1.2)}, "calf_r": {"rotation": (0, 0, knee * 1.2)},
            "upperarm_l": {"rotation": (0, 0, -chest)}, "upperarm_r": {"rotation": (0, 0, chest)},
        })

    new_action("A_Ciberfantasma_Pro_Crouch", 48)
    for frame, breath in ((1, 0.0), (24, 1.2), (48, 0.0)):
        key(frame, {
            "pelvis": {"location": (0, 0, -10 + breath * 0.25)},
            "spine_01": {"rotation": (0, 0, -8)}, "spine_02": {"rotation": (0, 0, -7)},
            "head": {"location": (0, 0, breath), "rotation": (0, 0, 6)},
            "thigh_l": {"rotation": (0, 0, 35)}, "thigh_r": {"rotation": (0, 0, -35)},
            "calf_l": {"rotation": (0, 0, -42)}, "calf_r": {"rotation": (0, 0, 42)},
            "upperarm_l": {"rotation": (0, 0, 16)}, "upperarm_r": {"rotation": (0, 0, -16)},
            "lowerarm_l": {"rotation": (0, 0, -24)}, "lowerarm_r": {"rotation": (0, 0, 24)},
        })

    new_action("A_Ciberfantasma_Pro_Fire", 14)
    fire_poses = ((1, 0, 0), (4, -24, -4), (7, -14, 2), (14, 0, 0))
    for frame, recoil, body in fire_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, body * 0.2)},
            "spine_01": {"rotation": (0, 0, body * 0.35)}, "spine_02": {"rotation": (0, 0, body)},
            "head": {"rotation": (0, 0, -body * 0.4)},
            "clavicle_l": {"rotation": (0, 0, -22 + recoil * 0.25)},
            "upperarm_l": {"rotation": (0, 0, -58 + recoil)},
            "lowerarm_l": {"rotation": (0, 0, 72 - recoil * 0.35)},
            "hand_l": {"rotation": (0, 0, recoil * 0.3)},
            "weapon_l": {"location": (0, recoil * 0.06, 0), "rotation": (0, 0, recoil * 0.15)},
            "upperarm_r": {"rotation": (0, 0, 18)}, "lowerarm_r": {"rotation": (0, 0, 22)},
        })

    new_action("A_Ciberfantasma_Pro_Shield", 48)
    shield_poses = ((1, -3, 0.96), (9, 4, 1.04), (24, 1, 1.0), (36, 4, 1.04), (48, -3, 0.96))
    for frame, pulse, scale in shield_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, -3)},
            "spine_01": {"rotation": (0, 0, -5)}, "spine_02": {"rotation": (0, 0, -4)},
            "head": {"location": (0, 0, pulse * 0.15), "rotation": (0, 0, 4)},
            "clavicle_l": {"rotation": (0, 0, 14)}, "clavicle_r": {"rotation": (0, 0, -14)},
            "upperarm_l": {"rotation": (0, 0, 48)}, "upperarm_r": {"rotation": (0, 0, -48)},
            "lowerarm_l": {"rotation": (0, 0, -68)}, "lowerarm_r": {"rotation": (0, 0, 68)},
            "hand_l": {"scale": (scale, scale, scale)}, "hand_r": {"scale": (scale, scale, scale)},
        })

    new_action("A_Ciberfantasma_Pro_Hit", 16)
    hit_poses = ((1, 0, 0), (4, 7, -16), (9, -3, 8), (16, 0, 0))
    for frame, shift, bend in hit_poses:
        key(frame, {
            "pelvis": {"location": (shift, 0, 0), "rotation": (0, 0, bend * 0.3)},
            "spine_01": {"rotation": (0, 0, bend * 0.4)}, "spine_02": {"rotation": (0, 0, bend)},
            "head": {"rotation": (0, 0, -bend * 0.65)},
            "upperarm_l": {"rotation": (0, 0, -30 - bend)}, "upperarm_r": {"rotation": (0, 0, 30 + bend)},
            "lowerarm_l": {"rotation": (0, 0, -18)}, "lowerarm_r": {"rotation": (0, 0, 18)},
        })
    return actions


def export_player_actions(mesh, armature, actions):
    for action_name, action in actions.items():
        armature.animation_data.action = action
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.ops.object.select_all(action="DESELECT")
        mesh.select_set(True)
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
        path = FBX_OUTPUT / f"{action_name}.fbx"
        bpy.ops.export_scene.fbx(
            filepath=str(path), use_selection=True, object_types={"MESH", "ARMATURE"},
            apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
            axis_forward="-Y", axis_up="Z", bake_anim=True,
            bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
            bake_anim_simplify_factor=0.0, add_leaf_bones=False,
            mesh_smooth_type="FACE", use_armature_deform_only=True
        )
        print(f"Exported {path}")


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_preview(models):
    # Front, three-quarter and back views of the exact exported player mesh.
    player = models[0]
    for other in models[1:]:
        other.hide_render = True
    player.location = (-115, 0, 0)
    three_quarter = player.copy()
    three_quarter.data = player.data
    three_quarter.location = (0, 0, 0)
    three_quarter.rotation_euler.z = math.radians(-42)
    bpy.context.collection.objects.link(three_quarter)
    back = player.copy()
    back.data = player.data
    back.location = (115, 0, 0)
    back.rotation_euler.z = math.radians(180)
    bpy.context.collection.objects.link(back)

    floor_mat = make_material("M_PreviewFloor", (0.16, 0.17, 0.18, 1), 0.0, 0.62, None)
    cube("PREVIEW_Floor", (0, 0, -7), (235, 130, 7), floor_mat, 2.0)

    bpy.ops.object.light_add(type="AREA", location=(0, -240, 260))
    key = bpy.context.object
    key.data.energy = 9500
    key.data.shape = "DISK"
    key.data.size = 180
    look_at(key, (0, 0, 80))
    bpy.ops.object.light_add(type="AREA", location=(180, 100, 190))
    rim = bpy.context.object
    rim.data.energy = 5200
    rim.data.color = (0.65, 0.78, 1.0)
    rim.data.size = 130
    look_at(rim, (80, 0, 90))
    bpy.ops.object.light_add(type="AREA", location=(-180, -80, 130))
    fill = bpy.context.object
    fill.data.energy = 5600
    fill.data.color = (0.82, 0.88, 1.0)
    fill.data.size = 100
    look_at(fill, (-80, 0, 80))
    bpy.ops.object.light_add(type="AREA", location=(0, -300, 95))
    front_fill = bpy.context.object
    front_fill.data.energy = 7200
    front_fill.data.size = 240
    look_at(front_fill, (0, 0, 82))

    bpy.ops.object.camera_add(location=(0, -650, 125))
    camera = bpy.context.object
    camera.data.lens = 62
    look_at(camera, (0, 0, 78))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.12, 0.125, 0.135, 1.0)
    background.inputs["Strength"].default_value = 0.45
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.05
    PREVIEW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(PREVIEW_OUTPUT)
    bpy.ops.render.render(write_still=True)


def build_bot_ground(materials):
    """Standard ground soldier - chibi humanoid with green visor, dark armour."""
    p = "BOT_"
    dark = materials["M_Enemy_Dark"]
    red = materials["M_Enemy_Red"]
    bot_green = materials["M_Bot_Green"]

    # Body
    cube(p + "Torso", (0, 0, 80), (28, 24, 30), dark, 4.0)
    cube(p + "Chest", (18, 0, 85), (6, 22, 18), red, 2.0)
    cube(p + "Waist", (0, 0, 55), (22, 20, 12), dark, 3.0)
    # Head
    cube(p + "Head", (0, 0, 120), (26, 24, 22), dark, 4.0)
    cube(p + "Visor", (22, 0, 121), (3, 18, 8), bot_green, 0.8)
    for side in (-1, 1):
        cylinder(p + f"EarPort{side}", (0, side * 15, 122), 4, 4, red,
                 (math.radians(90), 0, 0), bevel=0.5)
    # Arms
    for side in (-1, 1):
        sphere(p + f"Shoulder{side}", (0, side * 36, 88), (14, 12, 14), dark, 20, 12)
        capsule_between(p + f"Arm{side}", (0, side * 35, 80), (6, side * 37, 57), 9, dark)
        cube(p + f"Fist{side}", (8, side * 37, 46), (10, 10, 10), red, 2.5)
    # Legs
    for side in (-1, 1):
        sphere(p + f"Hip{side}", (0, side * 13, 44), (10, 10, 10), dark, 16, 10)
        capsule_between(p + f"Thigh{side}", (0, side * 13, 42), (2, side * 14, 22), 9, dark)
        cube(p + f"Knee{side}", (3, side * 14, 20), (8, 8, 8), red, 2.0)
        capsule_between(p + f"Shin{side}", (2, side * 14, 20), (4, side * 15, 8), 8, dark)
        cube(p + f"Boot{side}", (8, side * 15, 4), (16, 12, 7), dark, 3.0)
    # Accent circuits on torso
    for side in (-1, 1):
        tube_path(p + f"Circuit{side}", [
            (side * 6, -27, 92), (side * 10, -27, 83), (side * 7, -27, 74)
        ], 0.9, bot_green)
    return join_named("SM_BotGround_Chibi", p)


def build_crawler(materials):
    """Crawler - low, wide, heavily armoured melee bot with orange hazard stripe."""
    p = "CRL_"
    heavy = materials["M_Crawler_Heavy"]
    orange = materials["M_Crawler_Orange"]

    # Wide squat body
    cube(p + "Chassis", (0, 0, 44), (42, 38, 28), heavy, 6.0)
    cube(p + "FrontArmor", (28, 0, 46), (12, 36, 20), heavy, 4.0)
    cube(p + "HazardStripe", (30, 0, 45), (8, 32, 4), orange, 1.5)
    # Head turret
    cube(p + "Turret", (10, 0, 72), (28, 28, 16), heavy, 4.0)
    cylinder(p + "Optic", (28, 0, 73), 9, 6, orange, (0, math.radians(90), 0), 28, 0.8)
    sphere(p + "OpticLens", (34, 0, 73), (4, 6, 6), orange, 20, 12)
    # Arms / claws
    for side in (-1, 1):
        cube(p + f"UpperArm{side}", (0, side * 46, 54), (16, 8, 14), heavy, 3.0)
        cube(p + f"ForeArm{side}", (10, side * 50, 40), (14, 7, 12), heavy, 2.5)
        for finger in range(3):
            cube(p + f"Claw{side}_{finger}", (22 + finger * 5, side * 52 + finger * 4, 34),
                 (8, 4, 4), orange, 1.2)
    # Legs / treads (stylised as thick pads)
    for side in (-1, 1):
        cube(p + f"Tread{side}", (0, side * 38, 14), (38, 10, 12), heavy, 3.0)
        cube(p + f"TreadGlow{side}", (0, side * 44, 14), (34, 2, 6), orange, 0.8)
    # Orange hazard circles on shoulders
    for side in (-1, 1):
        ring(p + f"HazardRing{side}", (4, side * 44, 60), 9, 2, orange, (math.radians(90), 0, 0))
    return join_named("SM_Crawler_Chibi", p)


def build_harvester(materials):
    """Harvester - large aerial surveillance drone, teal sensors, golden body."""
    p = "HRV_"
    dark = materials["M_Enemy_Dark"]
    teal = materials["M_Harvester_Teal"]
    gold = materials["M_Harvester_Gold"]

    # Central oval core
    sphere(p + "Core", (0, 0, 72), (40, 32, 36), dark, 48, 28)
    sphere(p + "Belly", (0, 0, 56), (26, 22, 18), gold, 32, 18)
    # Large forward sensor array
    cylinder(p + "SensorRing", (32, 0, 72), 24, 6, gold, (0, math.radians(90), 0), 36, 0.8)
    cylinder(p + "Sensor", (38, 0, 72), 18, 5, teal, (0, math.radians(90), 0), 32, 0.6)
    sphere(p + "SensorLens", (44, 0, 72), (5, 12, 12), teal, 24, 14)
    # Four articulated antenna arms
    for index, angle in enumerate((45, 135, 225, 315)):
        ax = math.cos(math.radians(angle)) * 34
        ay = math.sin(math.radians(angle)) * 34
        capsule_between(p + f"Arm{index}", (ax * 0.4, ay * 0.4, 72), (ax, ay, 72 + 8), 6, dark)
        sphere(p + f"ArmTip{index}", (ax * 1.08, ay * 1.08, 72 + 10), (7, 7, 7), teal, 16, 10)
    # Bottom scanning laser emitter
    cylinder(p + "Emitter", (0, 0, 38), 8, 16, dark, bevel=1.0)
    cylinder(p + "EmitterGlow", (0, 0, 30), 5, 3, teal, bevel=0.5)
    # Upper comm dishes
    cone(p + "DishTop", (0, 0, 112), 16, 3, 28, gold)
    cylinder(p + "DishPole", (0, 0, 96), 3, 30, dark, bevel=0.4)
    # Side thrusters
    for side in (-1, 1):
        cylinder(p + f"Thruster{side}", (-8, side * 38, 65), 11, 18, dark,
                 (math.radians(90), 0, 0), bevel=1.2)
        ring(p + f"ThrustRing{side}", (-8, side * 38, 65), 13, 2.5, teal,
             (math.radians(90), 0, 0))
    return join_named("SM_Harvester_Chibi", p)


def build_enforcer(materials):
    """Enforcer - riot-police heavy trooper with a blue energy shield on the left arm."""
    p = "ENF_"
    grey = materials["M_Enforcer_Grey"]
    dark = materials["M_Enemy_Dark"]
    blue = materials["M_Enforcer_Blue"]

    # Bulky body
    cube(p + "Torso", (0, 0, 88), (34, 30, 36), grey, 5.0)
    cube(p + "ChestPlate", (20, 0, 92), (8, 26, 24), dark, 3.5)
    cube(p + "Waist", (0, 0, 60), (28, 24, 16), dark, 4.0)
    # Helmet
    cube(p + "Helmet", (0, 0, 130), (30, 28, 26), dark, 5.0)
    cube(p + "Visor", (22, 0, 131), (3, 22, 10), blue, 0.8)
    for side in (-1, 1):
        cube(p + f"EarGuard{side}", (2, side * 16, 132), (14, 6, 16), grey, 3.0)
    # Shield arm (left)
    sphere(p + "ShieldShoulder", (0, -40, 96), (16, 14, 16), grey, 22, 14)
    capsule_between(p + "ShieldUpperArm", (0, -40, 88), (4, -42, 64), 10, grey)
    cube(p + "Shield", (4, -56, 82), (6, 6, 48), blue, 1.0)
    # Weapon arm (right)
    sphere(p + "WeaponShoulder", (0, 40, 96), (16, 14, 16), grey, 22, 14)
    capsule_between(p + "WeaponArm", (0, 40, 88), (6, 44, 60), 10, grey)
    cylinder(p + "Baton", (10, 46, 46), 5, 32, dark, (math.radians(28), 0, 0), bevel=0.8)
    cylinder(p + "BatonGlow", (10, 46, 47), 3, 28, blue, (math.radians(28), 0, 0), bevel=0.5)
    # Legs
    for side in (-1, 1):
        sphere(p + f"Hip{side}", (0, side * 15, 50), (12, 12, 12), dark, 18, 11)
        capsule_between(p + f"Thigh{side}", (0, side * 15, 48), (3, side * 16, 26), 11, grey)
        cube(p + f"KneeGuard{side}", (4, side * 16, 24), (10, 10, 10), dark, 2.5)
        capsule_between(p + f"Shin{side}", (3, side * 16, 24), (5, side * 17, 10), 10, grey)
        cube(p + f"Boot{side}", (10, side * 17, 5), (20, 14, 9), dark, 4.0)
    # Blue accent stripes
    for side in (-1, 1):
        cube(p + f"Stripe{side}", (4, side * 32, 94), (26, 3, 6), blue, 1.0)
    return join_named("SM_Enforcer_Chibi", p)


def build_auditor(materials):
    """Auditor - floating bureaucratic robot with yellow optical sensors and clipboard."""
    p = "AUD_"
    white = materials["M_Auditor_White"]
    dark = materials["M_Enemy_Dark"]
    yellow = materials["M_Auditor_Yellow"]

    # Floating body - ovoid
    sphere(p + "Body", (0, 0, 80), (32, 28, 42), white, 40, 24)
    sphere(p + "BodyBack", (0, 8, 80), (30, 24, 38), dark, 36, 22)
    # Head - rectangular with four yellow lenses
    cube(p + "Head", (2, 0, 130), (28, 26, 22), white, 4.0)
    for row in range(2):
        for col in range(2):
            ox = col * 10 - 5
            oz = row * 8 - 2
            cylinder(p + f"Lens_{row}_{col}", (24, ox, 131 + oz), 5, 4,
                     yellow, (0, math.radians(90), 0), 20, 0.6)
    # Clipboard arm (right side)
    capsule_between(p + "ClipArm", (0, 32, 86), (6, 38, 62), 8, white)
    cube(p + "Clipboard", (10, 42, 60), (3, 18, 22), white, 2.0)
    cube(p + "ClipText", (12, 42, 59), (1.5, 14, 18), yellow, 0.5)
    # Scanner arm (left side)
    capsule_between(p + "ScanArm", (0, -32, 86), (4, -38, 64), 8, white)
    cylinder(p + "Scanner", (8, -42, 60), 8, 14, dark, bevel=1.2)
    cylinder(p + "ScannerBeam", (16, -42, 60), 4, 4, yellow, bevel=0.5)
    # Bottom hover emitter
    cone(p + "HoverBase", (0, 0, 36), 22, 2, 24, dark)
    cylinder(p + "HoverGlow", (0, 0, 28), 10, 5, yellow, bevel=0.8)
    # Side number labels (stylised cubes)
    for side in (-1, 1):
        cube(p + f"NumberPlate{side}", (6, side * 30, 80), (16, 3, 20), white, 2.5)
        cube(p + f"NumberText{side}", (8, side * 32, 80), (10, 1.5, 14), yellow, 0.5)
    return join_named("SM_Auditor_Chibi", p)


def build_ceo9000(materials):
    """CEO-9000 - mid-game boss. Massive corporate mech in gold and dark armour."""
    p = "CEO_"
    ceo_dark = materials["M_CEO_Dark"]
    gold = materials["M_CEO_Gold"]
    red = materials["M_CEO_Red"]

    # Colossal body (1.8x normal scale for boss presence)
    cube(p + "Torso", (0, 0, 110), (58, 50, 56), ceo_dark, 8.0)
    cube(p + "ChestPlate", (30, 0, 118), (14, 44, 36), gold, 5.0)
    # Gold suit-jacket panels
    for side in (-1, 1):
        cube(p + f"LapelPlate{side}", (20, side * 18, 125), (18, 10, 24), gold, 3.0)
    cube(p + "Tie", (32, 0, 112), (5, 6, 28), red, 1.5)
    cylinder(p + "TieKnot", (32, 0, 130), 7, 6, red, bevel=0.8)
    # Head - boardroom mask
    cube(p + "Head", (0, 0, 178), (44, 40, 34), ceo_dark, 6.0)
    cube(p + "FacePanel", (26, 0, 179), (6, 34, 22), gold, 3.0)
    for side in (-1, 1):
        cylinder(p + f"Eye{side}", (30, side * 9, 182), 8, 5,
                 red, (0, math.radians(90), 0), 28, 0.7)
    # Massive shoulder plates
    for side in (-1, 1):
        sphere(p + f"Shoulder{side}", (0, side * 62, 122), (28, 24, 28), gold, 28, 16)
        cube(p + f"ShoulderSpike{side}", (8, side * 78, 134), (10, 8, 24), gold, 2.5)
    # Arms
    for side in (-1, 1):
        capsule_between(p + f"UpperArm{side}", (0, side * 60, 114), (8, side * 64, 76), 18, ceo_dark)
        cube(p + f"Elbow{side}", (10, side * 64, 70), (18, 18, 14), gold, 3.5)
        capsule_between(p + f"ForeArm{side}", (8, side * 64, 68), (14, side * 66, 40), 16, ceo_dark)
        cube(p + f"Fist{side}", (18, side * 67, 30), (20, 18, 22), ceo_dark, 4.0)
        cylinder(p + f"KnuckleDuster{side}", (26, side * 67, 31), 9, 6,
                 gold, (0, math.radians(90), 0), bevel=1.0)
    # Legs
    for side in (-1, 1):
        sphere(p + f"Hip{side}", (0, side * 24, 60), (18, 18, 18), ceo_dark, 22, 13)
        capsule_between(p + f"Thigh{side}", (0, side * 24, 58), (6, side * 26, 30), 17, ceo_dark)
        cube(p + f"KneePlate{side}", (8, side * 26, 28), (14, 14, 14), gold, 3.0)
        capsule_between(p + f"Shin{side}", (6, side * 26, 28), (10, side * 28, 10), 16, ceo_dark)
        cube(p + f"Boot{side}", (16, side * 28, 5), (28, 22, 10), ceo_dark, 5.0)
        cube(p + f"BootPlate{side}", (20, side * 28, 14), (22, 18, 5), gold, 3.0)
    # Waist / belt
    cube(p + "Belt", (0, 0, 72), (48, 42, 14), gold, 5.0)
    cylinder(p + "BeltBuckle", (30, 0, 72), 10, 7, red, (0, math.radians(90), 0), 24, 0.8)
    # Corporate logo plate on chest
    cube(p + "LogoPlate", (38, 0, 130), (3, 14, 12), red, 1.2)
    return join_named("SM_CEO9000_Chibi", p)


def build_director(materials):
    """Director - final boss. Titanic bureaucratic entity, white robes, single red eye."""
    p = "DIR_"
    white = materials["M_Director_White"]
    black = materials["M_Director_Black"]
    red = materials["M_Director_Red"]

    # Enormous robe-body (2.2x player height)
    # Lower robe - wide bell shape
    cone(p + "Robe", (0, 0, 80), 72, 36, 160, white, vertices=32)
    # Upper torso
    sphere(p + "Chest", (0, 0, 182), (52, 46, 56), white, 48, 28)
    cube(p + "ChestPanel", (32, 0, 188), (8, 38, 32), black, 3.0)
    # Cape / train that flares behind
    for index in range(5):
        angle = -20 + index * 10
        ay = math.sin(math.radians(angle)) * 58
        az = 110 + index * 12
        cube(p + f"CapeFold{index}", (0, ay - 30, az), (8, 14, 18), white, 2.0,
             (math.radians(angle), 0, 0))
    # Head - tall obelisk with single giant eye
    cube(p + "Head", (0, 0, 255), (46, 42, 50), white, 7.0)
    cube(p + "HeadRidge", (0, 0, 302), (28, 26, 16), black, 4.0)
    cylinder(p + "Eye", (30, 0, 262), 22, 7, red, (0, math.radians(90), 0), 36, 1.2)
    sphere(p + "EyePupil", (38, 0, 262), (8, 14, 14), red, 28, 16)
    # White collar / neckline
    ring(p + "Collar", (0, 0, 238), 38, 6, white, (math.radians(10), 0, 0))
    # Long, elegantly thin arms
    for side in (-1, 1):
        sphere(p + f"Shoulder{side}", (0, side * 56, 200), (22, 18, 22), white, 24, 14)
        capsule_between(p + f"UpperArm{side}", (0, side * 56, 194), (4, side * 60, 158), 14, white)
        capsule_between(p + f"ForeArm{side}", (4, side * 60, 158), (8, side * 62, 120), 12, white)
        # Elongated fingers
        for finger in range(4):
            fz = 106 + finger * 7
            capsule_between(p + f"Finger{side}_{finger}",
                            (8, side * 63, fz + 10), (12, side * 66, fz), 3, black)
    # Red circuit lines down the robe
    for side in (-1, 1):
        tube_path(p + f"RobeCircuit{side}", [
            (side * 16, -30, 200), (side * 26, -36, 170),
            (side * 32, -40, 140), (side * 36, -44, 110)
        ], 1.4, red)
    # Red orbs / buttons down chest
    for index in range(4):
        sphere(p + f"Button{index}", (32, 0, 175 - index * 12), (4, 4, 4), red, 14, 8)
    # Large floor-scraping base hem
    ring(p + "Hem", (0, 0, 6), 68, 5, black)
    return join_named("SM_Director_Chibi", p)


def build():
    clean_scene()
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.01
    scene.unit_settings.length_unit = "CENTIMETERS"
    scene.render.fps = 60
    materials = {name: make_material(name, *settings) for name, settings in PALETTE.items()}

    # Player model + rig + animations
    player_model = build_ciberfantasma(materials)
    export_fbx(player_model)
    player_rig = rig_player(player_model)
    export_skeletal_fbx(player_model, player_rig)
    player_actions = build_player_actions(player_rig)
    export_player_actions(player_model, player_rig, player_actions)
    player_rig.animation_data.action = player_actions["A_Ciberfantasma_Pro_Idle"]

    # Enemy static meshes – all 9 types
    enemy_builders = [
        build_warden,       # EnemyKind 0 -> bot / warden display
        build_drone,        # EnemyKind 1 -> panopticon drone
        build_bot_ground,   # EnemyKind 0 -> bot ground variant
        build_crawler,      # EnemyKind 3 -> crawler
        build_harvester,    # EnemyKind 4 -> harvester
        build_enforcer,     # EnemyKind 6 -> enforcer
        build_auditor,      # EnemyKind 7 -> auditor
        build_ceo9000,      # EnemyKind 2/5 -> first two bosses share CEO-9000
        build_director,     # EnemyKind 8  -> final director boss
    ]
    enemy_models = []
    for builder in enemy_builders:
        model = builder(materials)
        export_fbx(model)
        enemy_models.append(model)

    render_preview([player_model] + enemy_models[:2])

    scene["cf_source_project"] = r"D:\Trabajo\Ciberfantasma Bros"
    scene["cf_character_height_cm"] = 160.0
    scene["cf_asset_status"] = "modeled and exported – nine enemy types"
    scene["cf_enemy_count"] = len(enemy_models)
    BLENDER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLENDER_OUTPUT), compress=True)
    print(f"Saved source scene {BLENDER_OUTPUT}")
    print(f"Total enemy models exported: {len(enemy_models)}")


if __name__ == "__main__":
    build()
