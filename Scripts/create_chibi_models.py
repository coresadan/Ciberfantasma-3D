"""Build production-ready modular chibi meshes and export them for Unreal.

The models deliberately use clean hard-surface primitives and bevelled silhouettes.
They are original 3D interpretations of the supplied Ciberfantasma Bros artwork,
not image planes or extruded sprites.
"""

from pathlib import Path
import math
import re

import bpy
import numpy as np
from mathutils import Vector


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "SourceAssets"
BLENDER_OUTPUT = SOURCE_ROOT / "Blender" / "CF_Character_Workfile.blend"
FBX_OUTPUT = SOURCE_ROOT / "FBX"
PREVIEW_OUTPUT = SOURCE_ROOT / "Previews" / "ciberfantasma_chibi_turnaround.png"
TEXTURE_OUTPUT = SOURCE_ROOT / "Textures" / "Hero"


HERO_SURFACE_PROFILES = {
    "Hood": {"metallic": 0.0, "roughness": 0.54, "ao": 0.94, "weave": 1.0, "wear": 0.10},
    "Undersuit": {"metallic": 0.0, "roughness": 0.68, "ao": 0.90, "weave": 1.35, "wear": 0.07},
    "Armor": {"metallic": 0.78, "roughness": 0.27, "ao": 0.96, "weave": 0.0, "wear": 0.24},
    "Bone": {"metallic": 0.02, "roughness": 0.34, "ao": 0.97, "weave": 0.0, "wear": 0.16},
}


PALETTE = {
    "M_CF_Hood": ((0.010, 0.014, 0.021, 1.0), 0.0, 0.54, None),
    "M_CF_Undersuit": ((0.018, 0.024, 0.033, 1.0), 0.0, 0.68, None),
    "M_CF_Armor": ((0.135, 0.155, 0.18, 1.0), 0.78, 0.27, None),
    "M_CF_Bone": ((0.94, 0.96, 0.93, 1.0), 0.02, 0.34, (0.2, 0.24, 0.21, 0.18)),
    "M_CF_Green": ((0.002, 0.48, 0.008, 1.0), 0.08, 0.2, (0.0, 0.72, 0.012, 1.2)),
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


def generate_hero_surface_maps(size=2048):
    """Author deterministic packed PBR and tangent-normal maps for the hero.

    R/G/B stores metallic, roughness and ambient-occlusion respectively.  The
    normal maps carry cloth weave or restrained hard-surface pitting.  Keeping
    this source generation deterministic means Blender and Unreal can rebuild
    the exact same production textures instead of depending on editor state.
    """
    TEXTURE_OUTPUT.mkdir(parents=True, exist_ok=True)

    for surface, profile in HERO_SURFACE_PROFILES.items():
        # Vectorised authoring keeps the 2K source maps practical to regenerate.
        # The patterns are deliberately seamless because the atlas contains many
        # small armour islands that may cross the texture boundary after edits.
        axis = np.linspace(0.0, 1.0, size, dtype=np.float32)
        u, v = np.meshgrid(axis, axis)
        diagonal = np.sin((u + v) * np.float32(math.tau * 52.0))
        diagonal *= np.sin((u - v) * np.float32(math.tau * 52.0))
        grain = np.sin(u * np.float32(math.tau * 17.0)
                       + np.sin(v * np.float32(math.tau * 7.0)))
        grain *= np.sin(v * np.float32(math.tau * 23.0)
                        + np.cos(u * np.float32(math.tau * 5.0)))
        score = np.maximum(
            np.float32(0.0),
            np.sin((u * np.float32(1.7) + v * np.float32(0.35))
                   * np.float32(math.tau * 9.0)) - np.float32(0.94),
        )
        # A broad low-frequency undulation stops close-ups reading as perfectly
        # computer-flat while remaining restrained enough for the clean concept.
        macro = np.sin(u * np.float32(math.tau * 3.0) + np.float32(0.7))
        macro *= np.sin(v * np.float32(math.tau * 4.0) - np.float32(0.35))
        heights = (
            diagonal * np.float32(0.16 * profile["weave"])
            + grain * np.float32(0.055)
            + score * np.float32(profile["wear"])
            + macro * np.float32(0.018 if profile["weave"] else 0.009)
        )

        edge_wear = np.maximum(np.float32(0.0), heights) * np.float32(profile["wear"])
        roughness = np.clip(
            np.float32(profile["roughness"]) + heights * np.float32(0.42) - edge_wear,
            np.float32(0.08), np.float32(0.92),
        )
        ao = np.clip(
            np.float32(profile["ao"]) + np.minimum(np.float32(0.0), heights) * np.float32(0.55),
            np.float32(0.72), np.float32(1.0),
        )
        packed_pixels = np.empty((size, size, 4), dtype=np.float32)
        packed_pixels[..., 0] = np.float32(profile["metallic"])
        packed_pixels[..., 1] = roughness
        packed_pixels[..., 2] = ao
        packed_pixels[..., 3] = np.float32(1.0)

        left = np.roll(heights, 1, axis=1)
        right = np.roll(heights, -1, axis=1)
        down = np.roll(heights, 1, axis=0)
        up = np.roll(heights, -1, axis=0)
        strength = np.float32(5.0 if profile["weave"] else 3.2)
        nx = -(right - left) * strength
        ny = -(up - down) * strength
        inverse_length = np.reciprocal(np.sqrt(nx * nx + ny * ny + np.float32(1.0)))
        normal_pixels = np.empty((size, size, 4), dtype=np.float32)
        normal_pixels[..., 0] = nx * inverse_length * np.float32(0.5) + np.float32(0.5)
        normal_pixels[..., 1] = ny * inverse_length * np.float32(0.5) + np.float32(0.5)
        normal_pixels[..., 2] = inverse_length * np.float32(0.5) + np.float32(0.5)
        normal_pixels[..., 3] = np.float32(1.0)

        for suffix, pixels in (("RMA", packed_pixels), ("Normal", normal_pixels)):
            image = bpy.data.images.new(f"T_CF_{surface}_{suffix}", width=size, height=size, alpha=True)
            image.pixels.foreach_set(pixels.ravel())
            image.file_format = "PNG"
            image.filepath_raw = str(TEXTURE_OUTPUT / f"T_CF_{surface}_{suffix}.png")
            image.save()
            bpy.data.images.remove(image)
            print(f"Generated {surface} {suffix} surface map at {size}x{size}")
        del u, v, diagonal, grain, score, macro, heights
        del edge_wear, roughness, ao, packed_pixels, normal_pixels


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

    surface_lookup = {
        "M_CF_Hood": "Hood",
        "M_CF_Undersuit": "Undersuit",
        "M_CF_Armor": "Armor",
        "M_CF_Bone": "Bone",
    }
    surface = surface_lookup.get(name)
    if surface:
        packed_path = TEXTURE_OUTPUT / f"T_CF_{surface}_RMA.png"
        normal_path = TEXTURE_OUTPUT / f"T_CF_{surface}_Normal.png"
        packed_image = bpy.data.images.load(str(packed_path), check_existing=True)
        packed_image.colorspace_settings.name = "Non-Color"
        packed = material.node_tree.nodes.new("ShaderNodeTexImage")
        packed.name = f"{surface}_PackedRMA"
        packed.image = packed_image
        packed.interpolation = "Linear"
        separate = material.node_tree.nodes.new("ShaderNodeSeparateColor")
        material.node_tree.links.new(packed.outputs["Color"], separate.inputs["Color"])
        material.node_tree.links.new(separate.outputs["Red"], node.inputs["Metallic"])
        material.node_tree.links.new(separate.outputs["Green"], node.inputs["Roughness"])

        normal_image = bpy.data.images.load(str(normal_path), check_existing=True)
        normal_image.colorspace_settings.name = "Non-Color"
        normal_texture = material.node_tree.nodes.new("ShaderNodeTexImage")
        normal_texture.name = f"{surface}_Normal"
        normal_texture.image = normal_image
        normal_texture.interpolation = "Linear"
        normal_map = material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 0.34 if surface in ("Hood", "Undersuit") else 0.22
        material.node_tree.links.new(normal_texture.outputs["Color"], normal_map.inputs["Color"])
        material.node_tree.links.new(normal_map.outputs["Normal"], node.inputs["Normal"])
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
    return add_bevel(obj, min(bevel, min(scale) * 0.45), 3)


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


def tailor_hood_volume(obj, radius_x, radius_y, radius_z):
    """Turn the base ellipsoid into the concept's padded bell-shaped hood.

    The canonical hood has a controlled crown, fuller lower temples and a
    flatter facial plane.  Working directly on the high-density base volume
    avoids adding another overlapping shell, which was the source of the old
    false second-hood silhouette.
    """
    for vertex in obj.data.vertices:
        normalized_z = max(-1.0, min(1.0, vertex.co.z / radius_z))
        lower = max(0.0, -normalized_z)
        middle = max(0.0, 1.0 - normalized_z * normalized_z)
        vertex.co.x *= 0.94 + middle * 0.045 + lower * 0.095
        # Flatten only the facial half.  The rear remains padded and rounded as
        # in the three-quarter and back panels of the turnaround.
        if vertex.co.y < 0.0:
            frontal = min(1.0, -vertex.co.y / radius_y)
            vertex.co.y *= 1.0 - frontal * 0.115
    obj.data.update()
    obj["cf_sculpt_pass"] = "V11 tailored bell hood; unified single volume"
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0.0, 0.0, 0.0), vertices=24, bevel=1.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    assign(obj, material)
    return add_bevel(obj, bevel, 3)


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
        major_segments=40, minor_segments=12, location=location, rotation=rotation
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


def scale_parts_about(prefix, pivot, scale):
    """Scale generated parts and their origins around an authored design pivot."""
    pivot_v = Vector(pivot)
    scale_v = Vector(scale)
    for obj in [item for item in bpy.context.scene.objects if item.type == "MESH" and item.name.startswith(prefix)]:
        offset = obj.location - pivot_v
        obj.location = pivot_v + Vector((offset.x * scale_v.x, offset.y * scale_v.y, offset.z * scale_v.z))
        obj.scale = Vector((obj.scale.x * scale_v.x, obj.scale.y * scale_v.y, obj.scale.z * scale_v.z))
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)


def scale_matching_parts_about(prefix, tokens, pivot, scale):
    """Scale only named feature families around a shared design pivot."""
    pivot_v = Vector(pivot)
    scale_v = Vector(scale)
    full_tokens = tuple(prefix + token for token in tokens)
    for obj in [item for item in bpy.context.scene.objects
                if item.type == "MESH" and item.name.startswith(full_tokens)]:
        offset = obj.location - pivot_v
        obj.location = pivot_v + Vector((offset.x * scale_v.x,
                                         offset.y * scale_v.y,
                                         offset.z * scale_v.z))
        obj.scale = Vector((obj.scale.x * scale_v.x,
                            obj.scale.y * scale_v.y,
                            obj.scale.z * scale_v.z))
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        obj.select_set(False)


def tube_path(name, points, radius, material, cyclic=False):
    curve = bpy.data.curves.new(name + "Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    coordinates = [Vector(coordinate) for coordinate in points]
    for index, (point, coordinate) in enumerate(zip(spline.bezier_points, coordinates)):
        point.co = coordinate
        # Blender curve points do not expose animation's AUTO_CLAMPED mode.
        # Build bounded Catmull-style handles explicitly so short seams cannot
        # overshoot the hood and create thin silhouette spikes.
        point.handle_left_type = "FREE"
        point.handle_right_type = "FREE"
        previous = coordinates[index - 1] if index > 0 else (
            coordinates[-1] if cyclic else coordinate
        )
        following = coordinates[(index + 1) % len(coordinates)] if (
            cyclic or index + 1 < len(coordinates)
        ) else coordinate
        tangent = following - previous
        if tangent.length_squared > 1.0e-8:
            tangent.normalize()
        left_length = (coordinate - previous).length * 0.28
        right_length = (following - coordinate).length * 0.28
        point.handle_left = coordinate - tangent * left_length
        point.handle_right = coordinate + tangent * right_length
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


def curved_patch_xz(name, points, y, depth, bulge, material, bevel=0.65):
    """Create a convex, fan-topologised armour patch from a front contour.

    Unlike a flat prism, the raised centre catches a moving highlight and gives
    the chest, limbs and mask the hand-sculpted ceramic volume of the concept.
    """
    signed_area = sum(
        points[index][0] * points[(index + 1) % len(points)][1]
        - points[(index + 1) % len(points)][0] * points[index][1]
        for index in range(len(points))
    )
    if signed_area < 0.0:
        points = list(reversed(points))
    count = len(points)
    center_x = sum(point[0] for point in points) / count
    center_z = sum(point[1] for point in points) / count
    front_y = y - depth * 0.5
    back_y = y + depth * 0.5
    vertices = [(center_x, front_y - bulge, center_z)]
    vertices.extend((x, front_y, z) for x, z in points)
    back_center = len(vertices)
    vertices.append((center_x, back_y, center_z))
    back_start = len(vertices)
    vertices.extend((x, back_y, z) for x, z in points)
    faces = []
    for index in range(count):
        nxt = (index + 1) % count
        faces.append((0, 1 + index, 1 + nxt))
        faces.append((back_center, back_start + nxt, back_start + index))
        faces.append((1 + index, back_start + index, back_start + nxt, 1 + nxt))
    mesh = bpy.data.meshes.new(name + "Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    assign(obj, material)
    return add_bevel(obj, bevel, 3)


def ensure_production_uvs(obj):
    """Build a non-overlapping UV0 atlas for every joined hero component."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    # Joined procedural primitives carry incompatible per-primitive layouts.
    # Rebuild the atlas as one asset so packed surface maps have stable density.
    while obj.data.uv_layers:
        obj.data.uv_layers.remove(obj.data.uv_layers[0])
    obj.data.uv_layers.new(name="UV0")
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(58.0), island_margin=0.012)
    bpy.ops.object.mode_set(mode="OBJECT")
    obj.data.uv_layers.active_index = 0
    obj["cf_uv_layout"] = "UV0 smart atlas, 0.012 island margin"
    obj.select_set(False)
    return obj


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


def seed_rigid_weight(obj, bone_name):
    """Keep an authored armour part rigid when the assembled mesh is skinned."""
    group = obj.vertex_groups.get(bone_name) or obj.vertex_groups.new(name=bone_name)
    group.add([vertex.index for vertex in obj.data.vertices], 1.0, "REPLACE")


def seed_player_part_weights(prefix):
    """Assign procedural pieces to their intended deform bones before joining.

    Joining preserves these groups and prevents spatial threshold weights from
    splitting a shoulder plate, hood panel or boot across unrelated bones.
    """
    head_tokens = (
        "Hood", "InnerMask", "Face", "Eye", "Brow", "Nose", "Cheek", "Jaw",
        "Mouth", "Tooth", "Chin", "MaskChin", "MaskVent", "Power", "Temple",
        "Orbital", "Forehead",
    )
    pelvis_tokens = ("Pelvis", "Belt", "Hip")
    upper_torso_tokens = ("Collar", "Chest", "Sternum")
    lower_torso_tokens = ("Torso", "Rib", "Ab", "BackLower")

    for obj in [item for item in bpy.context.scene.objects if item.name.startswith(prefix)]:
        part = obj.name[len(prefix):]
        bone_name = None
        # The turnaround describes one continuous padded hood. Earlier passes
        # rigid-bound the side/rear plates to secondary bones; on impacts those
        # pieces opened like a second detached hood. Keep every visible shell,
        # seam and circuit on the head bone. The secondary controls remain in
        # the rig for a future genuinely deformable cloth/high-poly version.
        if part.startswith(head_tokens):
            bone_name = "head"
        elif part.startswith(pelvis_tokens):
            bone_name = "pelvis"
        elif part.startswith(upper_torso_tokens):
            bone_name = "spine_02"
        elif part.startswith(lower_torso_tokens):
            bone_name = "spine_01"
        else:
            side_match = re.match(r"[A-Za-z]+(-?1)", part)
            side = "l" if side_match and side_match.group(1) == "-1" else "r"
            if part.startswith(("Shoulder",)):
                bone_name = f"clavicle_{side}"
            elif part.startswith(("UpperArm", "Bicep", "ArmBand")):
                bone_name = f"upperarm_{side}"
            elif part.startswith(("Elbow", "Forearm", "Gauntlet")):
                bone_name = f"lowerarm_{side}"
            elif part.startswith(("Fist", "Knuckle", "Finger")):
                bone_name = f"hand_{side}"
            elif part.startswith(("Thigh",)):
                bone_name = f"thigh_{side}"
            elif part.startswith(("Knee", "Shin", "Calf")):
                bone_name = f"calf_{side}"
            elif part.startswith(("BootToe", "BootGlow")):
                bone_name = f"toe_{side}"
            elif part.startswith(("Boot",)):
                bone_name = f"foot_{side}"
            elif part.startswith(("WristComputer", "WristScreen", "WristDisplay")):
                bone_name = "lowerarm_r"
            elif part.startswith(("LeftBracer",)):
                bone_name = "lowerarm_l"
            elif part.startswith(("BackUpper", "BackScapula")):
                bone_name = "spine_02"
        if bone_name:
            seed_rigid_weight(obj, bone_name)


def build_ciberfantasma(materials):
    p = "CFP_"
    armor = materials["M_CF_Armor"]
    hood = materials["M_CF_Hood"]
    bone = materials["M_CF_Bone"]
    green = materials["M_CF_Green"]
    visor = materials["M_CF_Visor"]
    undersuit = materials["M_CF_Undersuit"]

    # Blender -Y is the face normal.  Keep the hood as one uninterrupted shell.
    # The old stacked crown and rear overlay panels intersected the main volume
    # and read as a second hood from the profile/back cameras.  A slightly
    # shallower ellipsoid gives the canonical padded dome without a backpack-like
    # lobe, while the tailored front panels provide the bell-shaped jaw flare.
    hood_volume = sphere(p + "HoodVolume", (0, 1.5, 132.5),
                         (40.5, 27.5, 41.5), hood, 72, 44)
    tailor_hood_volume(hood_volume, 40.5, 27.5, 41.5)
    for side in (-1, 1):
        contour = [(4, 166), (14, 165), (25, 160), (34, 153), (40, 143),
                   (43, 132), (42, 118), (38, 106), (31, 97), (23, 92),
                   (18, 101), (24, 112), (29, 125), (29, 140), (25, 153),
                   (15, 161)]
        if side < 0:
            contour = mirrored_points(contour)
        prism_xz(p + f"HoodSidePanel{side}", contour, -27.5, 7.5, hood, 2.2)
    face_opening = [(-25, 154), (-34, 146), (-38, 132), (-37, 116), (-30, 102),
                    (-18, 94), (0, 91), (18, 94), (30, 102), (37, 116),
                    (38, 132), (34, 146), (25, 154), (12, 160), (0, 162),
                    (-12, 160)]
    prism_xz(p + "InnerMask", face_opening, -36.0, 5.0, visor, 1.8)
    tube_path(p + "HoodRim", [(x, -40.0, z) for x, z in face_opening], 2.25, armor, True)
    tube_path(p + "HoodCenterSeam", [(0, -27.0, 169), (0, -31.5, 162),
                                      (0, -36.0, 154)], 0.65, undersuit)
    for side in (-1, 1):
        tube_path(p + f"HoodCrownSeam{side}", [
            (side * 3, -27.5, 168), (side * 14, -29.5, 166),
            (side * 27, -29.0, 159), (side * 35, -26.0, 149)
        ], 0.55, undersuit)
        # A padded brow and lower cowl give the hood the deep, tailored opening
        # of the turnaround instead of reading as a sphere with a mask glued on.
        tube_path(p + f"HoodBrowPad{side}", [
            (side * 2, -38.1, 162), (side * 14, -39.0, 160),
            (side * 27, -38.2, 154), (side * 35, -35.0, 145)
        ], 1.45, hood)
        tube_path(p + f"HoodLowerCowl{side}", [
            (side * 38, -34.0, 119), (side * 35, -36.5, 107),
            (side * 27, -38.0, 98), (side * 17, -38.4, 92)
        ], 1.65, hood)

    # Sculptural skull mask: oversized black lenses, heavy bone orbital rims and
    # cheek sweeps dominate the face exactly as they do in the supplied design.
    left_eye = [(-34, 139), (-33, 146), (-28, 151), (-20, 153), (-12, 151),
                (-6, 146), (-4, 139), (-6, 132), (-12, 127), (-20, 125),
                (-28, 127), (-33, 133)]
    right_eye = mirrored_points(left_eye)
    for label, eye in (("L", left_eye), ("R", right_eye)):
        prism_xz(p + f"EyeSocket{label}", eye, -41.5, 3.8, visor, 1.15)
        tube_path(p + f"EyeRim{label}", [(x, -44.0, z) for x, z in eye], 2.15, bone, True)
        center_x = -19.0 if label == "L" else 19.0
        # Convex smoked lenses and a second inset bevel replace the previous
        # flat cut-outs with the layered orbital construction in the turnaround.
        sphere(p + f"EyeLens{label}", (center_x, -43.7, 138.5),
               (13.4, 2.4, 11.2), visor, 40, 24)
        inset = [
            (center_x + (x - center_x) * 0.82, 138.5 + (z - 138.5) * 0.82)
            for x, z in eye
        ]
        tube_path(p + f"EyeInset{label}", [(x, -45.2, z) for x, z in inset],
                  0.72, armor, True)

    left_brow = [(-34, 145), (-25, 153), (-14, 153), (-5, 144), (-9, 141),
                 (-18, 147), (-27, 143)]
    curved_patch_xz(p + "BrowL", left_brow, -44.0, 3.0, 1.05, bone, 0.82)
    curved_patch_xz(p + "BrowR", mirrored_points(left_brow), -44.0, 3.0, 1.05, bone, 0.82)
    prism_xz(p + "NoseBridge", [(-4, 143), (0, 139), (4, 143), (4, 129),
                                  (0, 124), (-4, 129)], -44.2, 3.8, bone, 0.95)
    prism_xz(p + "Nose", [(-6, 120), (0, 128), (6, 120), (3, 114),
                            (0, 112), (-3, 114)], -44.6, 3.8, visor, 0.8)
    # Keep the lower skull graphic compact.  The reference has fine cheek rails,
    # not two huge white wedges that swallow the face at gameplay distance.
    left_cheek = [(-30, 124), (-27, 118), (-20, 112), (-13, 110), (-9, 114),
                  (-15, 119), (-23, 116)]
    curved_patch_xz(p + "CheekL", left_cheek, -44.0, 4.0, 1.15, bone, 1.0)
    curved_patch_xz(p + "CheekR", mirrored_points(left_cheek), -44.0, 4.0, 1.15, bone, 1.0)
    tube_path(p + "JawSweepL", [(-31, -44.2, 119), (-28, -45.0, 111),
                                  (-21, -45.2, 103), (-15, -44.8, 98)], 1.7, bone)
    tube_path(p + "JawSweepR", [(31, -44.2, 119), (28, -45.0, 111),
                                  (21, -45.2, 103), (15, -44.8, 98)], 1.7, bone)
    prism_xz(p + "MouthPanel", [(-11, 108), (11, 108), (12, 102),
                                  (8, 96), (-8, 96), (-12, 102)],
             -42.4, 3.2, visor, 0.8)
    for index, x in enumerate((-6.0, -2.0, 2.0, 6.0)):
        prism_xz(p + f"Tooth{index}", [(x - 0.95, 106), (x + 0.95, 106),
                                         (x + 0.78, 98), (x - 0.78, 98)],
                 -45.0, 3.2, bone, 0.42)
    tube_path(p + "ChinArc", [(-16, -44.0, 105), (-12, -45.0, 98),
                                (0, -45.5, 93), (12, -45.0, 98),
                                (16, -44.0, 105)], 1.35, bone)
    for side in (-1, 1):
        tube_path(p + f"JawContour{side}", [
            (side * 29, -44.7, 120), (side * 26, -45.2, 112),
            (side * 20, -45.4, 105), (side * 14, -45.1, 99)
        ], 0.72, armor)
        # Floating temple and mandibular insets reproduce the layered skull-mask
        # construction visible in the canonical close-up.
        prism_xz(p + f"OrbitalTemple{side}", [
            (side * 31, 144), (side * 36, 140), (side * 35, 132),
            (side * 31, 127), (side * 28, 131), (side * 30, 137)
        ], -43.8, 3.5, bone, 0.75)
        prism_xz(p + f"MaskVent{side}", [
            (side * 9, 108), (side * 14, 106), (side * 13, 96),
            (side * 9, 94), (side * 7, 99)
        ], -45.0, 3.4, bone, 0.55)
        tube_path(p + f"CheekInset{side}", [
            (side * 28, -45.7, 119), (side * 22, -46.0, 115),
            (side * 17, -46.1, 111)
        ], 0.52, green)

    prism_xz(p + "ForeheadKeystone", [(-6, 151), (0, 146), (6, 151),
                                        (5, 159), (0, 162), (-5, 159)],
             -43.2, 3.0, armor, 0.8)

    # Green power icon and the three parallel circuit traces on each side of the hood.
    tube_path(p + "PowerArc", [(-7, -44.0, 159), (-9, -44.0, 154), (-8, -44.0, 149),
                                (-4, -44.0, 145), (0, -44.0, 144), (4, -44.0, 145),
                                (8, -44.0, 149), (9, -44.0, 154), (7, -44.0, 159)], 1.65, green)
    cube(p + "PowerStem", (0, -44.0, 158), (1.75, 1.35, 8.0), green, 0.72)
    for side in (-1, 1):
        for trace in range(3):
            offset = trace * 3.0
            tube_path(p + f"HoodCircuit{side}_{trace}", [
                (side * (31 + offset), -35.0 + trace, 148),
                (side * (35 + offset), -36.0 + trace, 140),
                (side * (34 + offset), -36.2 + trace, 131),
                (side * (39 + offset), -32.0 + trace, 122)
            ], 0.72, green)
        # Temple hardware breaks the spherical hood silhouette and gives the mask
        # a believable layered mounting point.
        cylinder(p + f"TempleDisc{side}", (side * 37.0, -39.0, 128), 5.0, 3.4,
                 armor, (math.radians(90), 0.0, 0.0), vertices=32, bevel=0.7)
        cylinder(p + f"TempleCore{side}", (side * 37.0, -41.1, 128), 2.15, 4.0,
                 green, (math.radians(90), 0.0, 0.0), vertices=24, bevel=0.45)
        # Rear traces sit directly on the single shell instead of floating past
        # it.  Their Y coordinates follow the ellipsoid profile at each height.
        for trace in range(2):
            tube_path(p + f"HoodRearCircuit{side}_{trace}", [
                (side * (17 + trace * 4), 25.0 - trace * 0.8, 151),
                (side * (23 + trace * 4), 25.5 - trace * 1.2, 143),
                (side * (22 + trace * 4), 27.0 - trace * 1.0, 133),
                (side * (29 + trace * 4), 23.0 - trace * 1.2, 124)
            ], 0.7, green)
    # A separate lower hood skirt keeps the head from reading as a bare sphere.
    prism_xz(p + "HoodJawSkirt", [(-38, 115), (-34, 102), (-21, 92), (0, 88),
                                    (21, 92), (34, 102), (38, 115), (28, 108),
                                    (0, 98), (-28, 108)], -27.0, 7.0, hood, 2.0)

    # Give the mask breathing room inside the hood like the canonical close-up.
    # Earlier versions filled almost the entire aperture and read as a flat icon.
    scale_matching_parts_about(
        p,
        ("InnerMask", "Eye", "Brow", "Nose", "Cheek", "Jaw", "Mouth",
         "Tooth", "Chin", "Mask", "Power", "Forehead", "Orbital"),
        (0.0, -43.0, 128.0),
        (0.90, 1.0, 1.02),
    )
    # The lower skull is a crisp graphic accent in the source, not a broad grin.
    # Compact it separately after the global mask fit so the eyes remain dominant.
    scale_matching_parts_about(
        p, ("Mouth", "Tooth", "Chin", "MaskVent"),
        (0.0, -43.0, 104.0), (0.88, 1.0, 0.92),
    )

    # The Canvas hero reads as a compact adult, not a bobblehead. Keep the
    # iconic hood width while reducing its vertical dominance around the jaw.
    scale_parts_about(p, (0.0, 0.0, 93.0), (0.96, 0.80, 0.94))

    # Compact armoured torso with a flexible undersuit, broad pectoral shell and
    # layered V plates. The silhouette deliberately narrows toward the belt.
    sphere(p + "TorsoCore", (0, 0, 78), (28.5, 19, 31), undersuit, 48, 28)
    prism_xz(p + "TorsoShell", [(-19, 104), (0, 101), (19, 104), (30, 95),
                                  (28, 81), (23, 66), (16, 54), (0, 48),
                                  (-16, 54), (-23, 66), (-28, 81), (-30, 95)],
             -18.0, 5.5, undersuit, 2.0)
    prism_xz(p + "Collar", [(-18, 102), (-5, 98), (0, 92), (5, 98), (18, 102),
                             (12, 108), (0, 104), (-12, 108)], -19.0, 6.0, armor, 1.3)
    left_chest = [(-3, 97), (-11, 102), (-26, 99), (-31, 90), (-27, 81),
                  (-18, 77), (-7, 82), (-3, 89)]
    prism_xz(p + "ChestPlateL", left_chest, -22.5, 8.5, armor, 2.0)
    prism_xz(p + "ChestPlateR", mirrored_points(left_chest), -22.5, 8.5, armor, 2.0)
    tube_path(p + "ChestPanelSeamL", [(x, -26.0, z) for x, z in left_chest], 0.42, hood, True)
    tube_path(p + "ChestPanelSeamR", [(x, -26.0, z) for x, z in mirrored_points(left_chest)],
              0.42, hood, True)
    prism_xz(p + "Sternum", [(-4.5, 98), (4.5, 98), (6.5, 83), (0, 76), (-6.5, 83)],
             -27.0, 6.0, armor, 1.15)
    prism_xz(p + "ChestCore", [(-4.5, 93), (4.5, 93), (6.5, 87), (0, 83), (-6.5, 87)],
             -30.5, 3.2, green, 0.75)
    for side in (-1, 1):
        tube_path(p + f"ChestGlow{side}", [
            (side * 6, -28.0, 97), (side * 14, -28.0, 96), (side * 23, -27.0, 91)
        ], 1.05, green)
        # Staggered chest facets reproduce the layered ceramic plates of the
        # concept while preserving a clean silhouette for the side camera.
        prism_xz(p + f"ChestFacetTop{side}", [
            (side * 7, 91), (side * 14, 96), (side * 22, 93),
            (side * 20, 87), (side * 12, 85)
        ], -29.0, 2.0, armor, 0.65)
        prism_xz(p + f"ChestFacetOuter{side}", [
            (side * 17, 84), (side * 25, 87), (side * 27, 81),
            (side * 22, 77), (side * 16, 79)
        ], -27.0, 2.1, armor, 0.65)
        prism_xz(p + f"RibPlate{side}", [
            (side * 5, 79), (side * 20, 76), (side * 23, 70),
            (side * 12, 67), (side * 5, 71)
        ], -21.5, 6.0, armor, 1.0)
        tube_path(p + f"RibGlow{side}", [
            (side * 22, -25.0, 79), (side * 25, -24.0, 74), (side * 22, -24.0, 69)
        ], 0.8, green)
    for index, z in enumerate((78, 71, 64)):
        width = 13 - index
        prism_xz(p + f"AbPlate{index}", [(-width, z + 3), (width, z + 3),
                                           (width - 2, z - 2), (0, z - 4),
                                           (-width + 2, z - 2)], -25.5, 5.0, armor, 1.0)
    for side in (-1, 1):
        tube_path(p + f"AbRail{side}", [(side * 15, -27.0, 78),
                                         (side * 17, -26.5, 69),
                                         (side * 14, -26.0, 59)], 0.72, green)
    prism_xz(p + "PelvisPlate", [(-21, 62), (-10, 64), (0, 59), (10, 64), (21, 62),
                                  (17, 52), (0, 49), (-17, 52)], -19.0, 6.0, armor, 1.5)
    cube(p + "Belt", (0, 0, 54), (24, 20, 4), undersuit, 1.8)
    prism_xz(p + "BeltGlow", [(-5, 58), (5, 58), (6, 54), (0, 52), (-6, 54)],
             -22.5, 3.0, green, 0.6)
    # Overlapping sternum and abdominal inserts add readable parallax at
    # gameplay distance without relying on a baked normal map.
    prism_xz(p + "SternumInset", [(-2.8, 88), (0, 91), (2.8, 88), (2.2, 82),
                                    (0, 79.5), (-2.2, 82)], -30.8, 2.2, hood, 0.5)
    for side in (-1, 1):
        # Dark fasteners support the plates without scattering luminous dots.
        # The reference reserves green for coherent energy paths.
        for index, z in enumerate((77, 70, 63)):
            cube(p + f"AbFastener{side}_{index}", (side * (10.5 - index), -28.0, z),
                 (0.75, 0.65, 0.75), hood, 0.26)
        tube_path(p + f"AbPowerSpine{side}", [
            (side * 8.5, -29.2, 78), (side * 10.0, -30.0, 72),
            (side * 9.0, -30.0, 66), (side * 7.0, -29.0, 60)
        ], 0.68, green)
        # Small overlapping ceramic scales supply the dense tailored armour seen
        # in the reference without obscuring the large readable chest forms.
        for row, (z, x_outer) in enumerate(((92, 29), (86, 27), (72, 22), (65, 19))):
            x_inner = max(8.0, x_outer - 7.0)
            prism_xz(p + f"ChestMicroPlate{side}_{row}", [
                (side * x_inner, z + 2.7), (side * x_outer, z + 3.5),
                (side * (x_outer + 2.0), z), (side * x_outer, z - 3.4),
                (side * x_inner, z - 2.5), (side * (x_inner - 1.5), z)
            ], -28.5, 1.6, armor, 0.48)
    tube_path(p + "CollarUnderseal", [(-19, -20.0, 103), (-10, -23.0, 106),
                                        (0, -24.0, 104), (10, -23.0, 106),
                                        (19, -20.0, 103)], 1.1, hood)

    # Broad shoulders, short segmented limbs and large hands/boots preserve the
    # turnaround's chibi weight while keeping every articulation readable.
    for side in (-1, 1):
        x = side * 31
        sphere(p + f"Shoulder{side}", (x, 0, 89), (13.0, 11.5, 13.5), undersuit, 32, 20)
        shoulder_plate = [(side * 23, 98), (side * 31, 103), (side * 41, 99),
                          (side * 45, 91), (side * 38, 86), (side * 26, 90)]
        prism_xz(p + f"ShoulderPlate{side}", shoulder_plate, -13.0, 8.0, armor, 1.8)
        prism_xz(p + f"ShoulderLower{side}", [(side * 27, 91), (side * 39, 89),
                                               (side * 41, 83), (side * 34, 79),
                                               (side * 27, 83)],
                 -10.5, 5.0, armor, 1.2)
        for tile, (tile_x, tile_z) in enumerate(((29, 97), (35, 96), (39, 91), (35, 86))):
            cube(p + f"ShoulderTile{side}_{tile}",
                 (side * tile_x, -18.1, tile_z), (3.0, 1.0, 2.25), armor, 0.55,
                 (0.0, 0.0, side * math.radians(10 - tile * 4)))
        tube_path(p + f"ShoulderSeam{side}", [
            (side * 28, -16, 99), (side * 35, -17, 98), (side * 41, -15, 93)
        ], 0.75, green)
        capsule_between(p + f"UpperArm{side}", (side * 32, 0, 83), (side * 37, -2, 67), 7.4, undersuit)
        prism_xz(p + f"BicepPlate{side}", [(side * 29, 82), (side * 39, 85),
                                            (side * 44, 76), (side * 40, 69),
                                            (side * 31, 72)], -11.0, 5.0, armor, 1.0)
        for tile, (tile_z, tile_x) in enumerate(((80, 34), (74, 39))):
            cube(p + f"BicepTile{side}_{tile}", (side * tile_x, -17.0, tile_z),
                 (4.0, 1.1, 2.7), armor, 0.55,
                 (0.0, 0.0, side * math.radians(9)))
        ring(p + f"ArmBand{side}", (side * 36, -1, 73), 7.5, 1.15, armor,
             (0.0, math.radians(90), 0.0))
        cylinder(p + f"Elbow{side}", (side * 38, -2, 64), 7.0, 7.2, undersuit,
                 (0, math.radians(90), 0), bevel=1.0)
        capsule_between(p + f"Forearm{side}", (side * 38, -2, 61), (side * 40, -6, 48), 8.4, undersuit)
        prism_xz(p + f"ForearmPlate{side}", [(side * 31, 63), (side * 42, 66),
                                              (side * 47, 54), (side * 43, 46),
                                              (side * 32, 49)], -12.0, 5.0, armor, 1.0)
        for tile, tile_z in enumerate((61, 56, 51)):
            cube(p + f"ForearmTile{side}_{tile}",
                 (side * (37.0 + tile * 1.7), -18.0, tile_z),
                 (3.6, 1.0, 1.7), armor, 0.45,
                 (0.0, 0.0, side * math.radians(8)))
        prism_xz(p + f"GauntletCuff{side}", [(side * 32, 57), (side * 39, 63),
                                              (side * 47, 58), (side * 46, 50),
                                              (side * 35, 48)],
                 -10.0, 6.0, armor, 1.25)
        sphere(p + f"Fist{side}", (side * 40, -8, 43), (9.2, 8.8, 8.8), undersuit, 32, 18)
        prism_xz(p + f"FistPalmPlate{side}", [
            (side * 33, 47), (side * 41, 49), (side * 47, 44),
            (side * 45, 37), (side * 36, 37), (side * 32, 42)
        ], -16.0, 2.3, armor, 0.75)
        for finger in range(4):
            finger_x = 35.0 + finger * 2.85
            cube(p + f"Knuckle{side}_{finger}",
                 (side * finger_x, -16.8, 45.2 - abs(1.5 - finger) * 0.35),
                 (1.5, 1.8, 1.55), armor, 0.65)
            cube(p + f"FingerPlate{side}_{finger}",
                 (side * finger_x, -17.4, 41.8 - abs(1.5 - finger) * 0.3),
                 (1.3, 1.5, 1.15), armor, 0.45)
            cube(p + f"FingerTip{side}_{finger}",
                 (side * finger_x, -15.7, 39.4 - abs(1.5 - finger) * 0.25),
                 (1.25, 1.25, 0.95), undersuit, 0.4)
        capsule_between(p + f"FingerThumb{side}",
                        (side * 33.5, -11.5, 44.0), (side * 31.0, -15.0, 40.0),
                        2.2, undersuit)
        cube(p + f"ForearmGlow{side}", (side * 40, -16.5, 57), (4.8, 1.2, 2.0), green, 0.5)
        # Flexible dark joint collars hide hard intersections during bending.
        ring(p + f"ElbowSeal{side}", (side * 38, -2, 64), 7.4, 1.15, hood,
             (0.0, math.radians(90), 0.0))

        sphere(p + f"Hip{side}", (side * 14.5, 0, 50), (13, 12, 13), undersuit, 28, 18)
        capsule_between(p + f"Thigh{side}", (side * 14.5, 0, 47), (side * 15.5, 0, 29), 10.7, undersuit)
        prism_xz(p + f"ThighPlate{side}", [(side * 5, 48), (side * 13, 55),
                                            (side * 25, 48), (side * 24, 35),
                                            (side * 15, 30), (side * 7, 37)],
                 -9.5, 5.0, armor, 1.1)
        for tile, (tile_z, tile_x) in enumerate(((47, 13), (41, 18), (35, 15))):
            cube(p + f"ThighTile{side}_{tile}", (side * tile_x, -15.6, tile_z),
                 (4.8, 1.0, 2.2), armor, 0.5,
                 (0.0, 0.0, side * math.radians(7 if tile != 1 else -7)))
        tube_path(p + f"ThighSeam{side}", [(side * 9, -12.2, 47),
                                            (side * 15, -12.2, 51),
                                            (side * 22, -12.2, 46)], 0.45, hood)
        sphere(p + f"Knee{side}", (side * 15.5, -9, 27), (9.7, 7.0, 8.8), undersuit, 28, 18)
        prism_xz(p + f"KneeCap{side}", [(side * 7, 29), (side * 11, 34),
                                         (side * 20, 34), (side * 24, 28),
                                         (side * 20, 20), (side * 10, 20)],
                 -16.0, 3.5, armor, 0.9)
        tube_path(p + f"KneeGlow{side}", [(side * 9, -18, 25), (side * 15, -18, 21),
                                           (side * 22, -18, 25)], 0.75, green)
        capsule_between(p + f"Shin{side}", (side * 15.5, 0, 24), (side * 15.5, 0, 11), 9.7, undersuit)
        prism_xz(p + f"ShinPlate{side}", [(side * 7, 22), (side * 12, 27),
                                           (side * 23, 23), (side * 22, 10),
                                           (side * 16, 6), (side * 8, 10)],
                 -10.0, 4.5, armor, 1.0)
        for tile, tile_z in enumerate((20, 14, 9)):
            cube(p + f"ShinTile{side}_{tile}", (side * 15.5, -15.2, tile_z),
                 (5.4 - tile * 0.35, 1.0, 1.7), armor, 0.45,
                 (0.0, 0.0, side * math.radians((-1) ** tile * 5)))
        tube_path(p + f"ShinSeam{side}", [(side * 10, -13.0, 18),
                                           (side * 16, -13.0, 14),
                                           (side * 21, -13.0, 18)], 0.4, hood)
        sphere(p + f"Boot{side}", (side * 15.5, -5, 8.5), (11.8, 14.5, 8.8), undersuit, 32, 18)
        prism_xz(p + f"BootAnkleGuard{side}", [
            (side * 7, 14), (side * 10, 20), (side * 21, 20),
            (side * 24, 13), (side * 20, 8), (side * 10, 8)
        ], -10.8, 4.8, armor, 0.9)
        sphere(p + f"BootToe{side}", (side * 15.5, -18, 7.5), (10.8, 9.0, 6.2), armor, 28, 16)
        cube(p + f"BootToeCap{side}", (side * 15.5, -26.1, 8.4),
             (7.6, 1.3, 2.5), armor, 0.65)
        cube(p + f"BootSole{side}", (side * 15.5, -6, 2), (12.5, 16.0, 2.0), hood, 1.5)
        cube(p + f"BootHeel{side}", (side * 15.5, 6.5, 5), (9.8, 6.0, 4.8), armor, 1.2)
        cube(p + f"BootInstep{side}", (side * 15.5, -13.2, 12.0),
             (9.2, 7.5, 2.2), armor, 0.85)
        for tread in (-16, -7, 2, 8):
            cube(p + f"BootTread{side}_{tread}", (side * 15.5, tread, -0.3),
                 (11.0, 1.6, 0.9), armor, 0.35)
        cube(p + f"BootGlowOuter{side}", (side * 20, -28.0, 8), (2.8, 0.8, 1.0), green, 0.35,
             (0.0, 0.0, side * math.radians(-18)))
        cube(p + f"BootGlowInner{side}", (side * 11, -28.0, 8), (2.8, 0.8, 1.0), green, 0.35,
             (0.0, 0.0, side * math.radians(18)))

    # Wrist computer/pulse emitter from the canonical concept.
    cube(p + "WristComputer", (41, -13, 57), (8.8, 5.5, 7.5), armor, 1.9,
         (0.0, 0.0, math.radians(8)))
    cube(p + "WristScreen", (41, -19.0, 58), (6.0, 1.0, 4.7), visor, 0.55,
         (0.0, 0.0, math.radians(8)))
    for index in range(3):
        cube(p + f"WristDisplayLine{index}", (41, -20.2, 55.6 + index * 2.3),
             (4.1 - index * 0.45, 0.45, 0.38), green, 0.18,
             (0.0, 0.0, math.radians(8)))
    cube(p + "LeftBracer", (-40, -12, 55), (8, 5, 7), armor, 1.8,
         (0.0, 0.0, math.radians(-8)))
    tube_path(p + "LeftBracerGlow", [(-35, -18, 58), (-40, -18, 61), (-45, -18, 58)], 0.8, green)

    # Back armour seams make the turnaround intentional rather than hollow.
    cube(p + "BackLowerSpine", (0, 19, 70), (5, 3, 14), armor, 1.2)
    cube(p + "BackUpperSpine", (0, 19, 91), (5.5, 3.2, 10), armor, 1.2)
    for side in (-1, 1):
        tube_path(p + f"BackGlow{side}", [
            (side * 6, 22, 95), (side * 13, 22, 84), (side * 10, 22, 71)
        ], 1.0, green)
        prism_xz(p + f"BackScapula{side}", [
            (side * 5, 101), (side * 17, 99), (side * 27, 91),
            (side * 23, 80), (side * 12, 84)
        ], 17.0, 5.0, armor, 1.25)
        for index, z in enumerate((94, 87, 80)):
            cube(p + f"BackUpperTile{side}_{index}",
                 (side * (12 + index * 3), 23.0, z),
                 (5.0, 1.2, 2.4), armor, 0.55,
                  (0.0, 0.0, side * math.radians(8)))
        prism_xz(p + f"BackLowerPlate{side}", [
            (side * 5, 76), (side * 13, 79), (side * 22, 73),
            (side * 20, 63), (side * 10, 60), (side * 5, 66)
        ], 18.0, 4.2, armor, 0.9)

    # V8 sculpt pass.  Curved overlay shells replace the last flat reads with
    # convex ceramic volumes and a deliberately layered hood/mask silhouette.
    # The broad primary shapes stay faithful to the turnaround while the small
    # facets remain readable from the actual side-scroller camera distance.
    for side in (-1, 1):
        curved_patch_xz(p + f"HoodTempleFlap{side}", [
            (side * 32, 153), (side * 39, 146), (side * 42, 134),
            (side * 41, 119), (side * 36, 106), (side * 30, 99),
            (side * 28, 113), (side * 31, 132)
        ], -34.4, 4.8, 2.0, hood, 1.35)

        chest_points = [
            (side * 4, 96), (side * 12, 101), (side * 23, 99),
            (side * 30, 92), (side * 27, 84), (side * 18, 80),
            (side * 8, 83), (side * 4, 89)
        ]
        curved_patch_xz(p + f"ChestSculpt{side}", chest_points,
                        -30.6, 2.8, 2.7, armor, 0.9)
        tube_path(p + f"ChestSculptEdge{side}",
                  [(x, -34.2, z) for x, z in chest_points], 0.38, hood, True)
        curved_patch_xz(p + f"ShoulderSculpt{side}", [
            (side * 25, 99), (side * 32, 103), (side * 41, 99),
            (side * 46, 92), (side * 42, 86), (side * 32, 88),
            (side * 27, 92)
        ], -19.2, 3.0, 2.2, armor, 0.75)
        curved_patch_xz(p + f"BicepSculpt{side}", [
            (side * 31, 82), (side * 38, 84), (side * 43, 78),
            (side * 42, 70), (side * 35, 69), (side * 31, 75)
        ], -17.8, 2.4, 1.7, armor, 0.65)
        curved_patch_xz(p + f"ForearmSculpt{side}", [
            (side * 33, 62), (side * 41, 65), (side * 47, 58),
            (side * 45, 49), (side * 37, 48), (side * 33, 54)
        ], -19.0, 2.2, 1.9, armor, 0.65)
        curved_patch_xz(p + f"ThighSculpt{side}", [
            (side * 7, 48), (side * 14, 53), (side * 23, 49),
            (side * 25, 40), (side * 20, 32), (side * 12, 31),
            (side * 7, 38)
        ], -16.8, 2.5, 2.0, armor, 0.7)
        curved_patch_xz(p + f"KneeSculpt{side}", [
            (side * 8, 29), (side * 12, 34), (side * 20, 33),
            (side * 24, 27), (side * 20, 21), (side * 11, 21)
        ], -19.0, 2.0, 1.9, armor, 0.65)
        curved_patch_xz(p + f"ShinSculpt{side}", [
            (side * 8, 21), (side * 13, 26), (side * 21, 23),
            (side * 23, 13), (side * 18, 7), (side * 10, 9)
        ], -16.2, 2.1, 1.8, armor, 0.65)
        curved_patch_xz(p + f"BootToeSculpt{side}", [
            (side * 7, 10), (side * 10, 14), (side * 21, 14),
            (side * 25, 9), (side * 22, 4), (side * 9, 4)
        ], -27.7, 2.0, 1.8, armor, 0.6)

        # Articulated floating scales follow the anatomical flow rather than a
        # square grid, producing the tailored exosuit pattern in the concept.
        for region, samples in (
            ("Lat", ((25, 78, -23), (27, 72, -22), (24, 66, -21))),
            ("Arm", ((38, 79, -20), (42, 73, -19), (44, 55, -20))),
            ("Leg", ((20, 45, -18), (22, 38, -18), (20, 17, -18))),
        ):
            for index, (x_abs, z, y) in enumerate(samples):
                cube(p + f"{region}Scale{side}_{index}",
                     (side * x_abs, y, z), (2.4, 0.65, 1.5), armor, 0.42,
                     (0.0, 0.0, side * math.radians(12 - index * 5)))

        # Subtle inset tailoring seams replace the former convex rear plates.
        # The sampled path hugs the ellipsoid and converges toward the crown,
        # matching the three-panel construction visible in the concept art.
        tube_path(p + f"HoodRearSeam{side}", [
            (side * 3, 18.5, 165), (side * 10, 24.2, 157),
            (side * 16, 28.3, 144), (side * 18, 29.5, 130),
            (side * 20, 25.0, 114), (side * 17, 16.5, 101)
        ], 0.52, undersuit)

    curved_patch_xz(p + "SternumSculpt", [(-4, 98), (4, 98), (7, 88),
                                             (4, 78), (0, 74), (-4, 78), (-7, 88)],
                    -34.2, 2.4, 2.4, armor, 0.7)
    curved_patch_xz(p + "PelvisSculpt", [(-20, 61), (-10, 64), (0, 60),
                                            (10, 64), (20, 61), (17, 53),
                                            (0, 49), (-17, 53)],
                    -23.0, 2.5, 2.0, armor, 0.75)
    # Tiny recessed fasteners provide a scale cue in close shots without adding
    # noisy highlights to the primary silhouette.
    for x, z in ((-20, 94), (20, 94), (-25, 85), (25, 85),
                 (-18, 72), (18, 72), (-11, 57), (11, 57)):
        cylinder(p + f"ArmorFastener{x}_{z}", (x, -34.8, z), 0.72, 0.7,
                 hood, (math.radians(90), 0.0, 0.0), vertices=16, bevel=0.2)
    seed_player_part_weights(p)
    return ensure_production_uvs(join_named("SM_Ciberfantasma_Chibi", p))


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
        "hood_l": ((-12, 2, 151), (-31, 1, 112), "head"),
        "hood_r": ((12, 2, 151), (31, 1, 112), "head"),
        "hood_back": ((0, 12, 151), (0, 24, 110), "head"),
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
        if name.startswith(("upperarm_", "lowerarm_", "hand_", "thigh_", "calf_")):
            # Keep local Z aligned with character depth.  Procedural diagonal
            # bones otherwise inherit arbitrary roll and turn a forward swing
            # into a downward/sideways arc.
            bone.align_roll(Vector((0.0, 1.0, 0.0)))
        created[name] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    armature.select_set(False)

    groups = {
        name: mesh.vertex_groups.get(name) or mesh.vertex_groups.new(name=name)
        for name in definitions
    }
    deform_group_indices = {group.index for group in groups.values()}

    def normalized_weights(vertex_index, weighted_bones):
        valid = [(name, max(0.0, weight)) for name, weight in weighted_bones if weight > 0.0001]
        total = sum(weight for _, weight in valid)
        for name, weight in valid:
            groups[name].add([vertex_index], weight / total, "REPLACE")

    def transition(value, lower, upper):
        alpha = max(0.0, min(1.0, (value - lower) / (upper - lower)))
        return alpha * alpha * (3.0 - 2.0 * alpha)

    for vertex in mesh.data.vertices:
        if any(membership.group in deform_group_indices and membership.weight > 0.001
               for membership in vertex.groups):
            continue
        x, y, z = vertex.co
        side = "l" if x < 0 else "r"
        if z >= 108:
            normalized_weights(vertex.index, [("head", 1.0)])
        elif abs(x) >= 27 and z >= 39:
            if x < -31 and y < -9 and 50 <= z <= 66:
                normalized_weights(vertex.index, [("weapon_l", 0.88), ("lowerarm_l", 0.12)])
            elif z >= 87:
                normalized_weights(vertex.index, [(f"clavicle_{side}", 1.0)])
            elif z >= 82:
                alpha = transition(z, 82.0, 87.0)
                normalized_weights(vertex.index, [(f"upperarm_{side}", 1.0 - alpha),
                                                   (f"clavicle_{side}", alpha)])
            elif z >= 69:
                normalized_weights(vertex.index, [(f"upperarm_{side}", 1.0)])
            elif z >= 61:
                alpha = transition(z, 61.0, 69.0)
                normalized_weights(vertex.index, [(f"lowerarm_{side}", 1.0 - alpha),
                                                   (f"upperarm_{side}", alpha)])
            elif z >= 50:
                normalized_weights(vertex.index, [(f"lowerarm_{side}", 1.0)])
            elif z >= 44:
                alpha = transition(z, 44.0, 50.0)
                normalized_weights(vertex.index, [(f"hand_{side}", 1.0 - alpha),
                                                   (f"lowerarm_{side}", alpha)])
            else:
                normalized_weights(vertex.index, [(f"hand_{side}", 1.0)])
        elif abs(x) > 4 and z < 59:
            if z >= 50:
                alpha = transition(z, 50.0, 57.0)
                normalized_weights(vertex.index, [(f"thigh_{side}", 1.0 - alpha), ("pelvis", alpha)])
            elif z >= 34:
                normalized_weights(vertex.index, [(f"thigh_{side}", 1.0)])
            elif z >= 26:
                alpha = transition(z, 26.0, 34.0)
                normalized_weights(vertex.index, [(f"calf_{side}", 1.0 - alpha),
                                                   (f"thigh_{side}", alpha)])
            elif z >= 14:
                normalized_weights(vertex.index, [(f"calf_{side}", 1.0)])
            elif z >= 8:
                alpha = transition(z, 8.0, 14.0)
                normalized_weights(vertex.index, [(f"foot_{side}", 1.0 - alpha),
                                                   (f"calf_{side}", alpha)])
            elif y < -13:
                alpha = transition(-y, 13.0, 24.0)
                normalized_weights(vertex.index, [(f"foot_{side}", 1.0 - alpha),
                                                   (f"toe_{side}", alpha)])
            else:
                normalized_weights(vertex.index, [(f"foot_{side}", 1.0)])
        elif z < 64:
            normalized_weights(vertex.index, [("pelvis", 1.0)])
        elif z < 81:
            alpha = transition(z, 75.0, 81.0)
            normalized_weights(vertex.index, [("spine_01", 1.0 - alpha), ("spine_02", alpha)])
        elif z < 101:
            normalized_weights(vertex.index, [("spine_02", 1.0)])
        else:
            alpha = transition(z, 101.0, 108.0)
            normalized_weights(vertex.index, [("neck", 1.0 - alpha), ("head", alpha)])

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
        action.use_fake_user = True
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
        # Every authored pose starts from rest and writes a complete transform
        # track for every deform bone. Partial actions otherwise inherit the last
        # evaluated pose during sequential FBX export, which was the source of
        # detached wrists and extreme arm silhouettes in jump/shield.
        for bone in armature.pose.bones:
            bone.location = (0.0, 0.0, 0.0)
            bone.rotation_euler = (0.0, 0.0, 0.0)
            bone.scale = (1.0, 1.0, 1.0)
        for bone_name, channels in values.items():
            bone = armature.pose.bones[bone_name]
            if "location" in channels:
                bone.location = channels["location"]
            if "rotation" in channels:
                bone.rotation_euler = tuple(math.radians(value) for value in channels["rotation"])
            if "scale" in channels:
                bone.scale = channels["scale"]
        for bone in armature.pose.bones:
            bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
            bone.keyframe_insert(data_path="rotation_euler", frame=frame, group=bone.name)
            bone.keyframe_insert(data_path="scale", frame=frame, group=bone.name)

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
            "hood_l": {"rotation": (-lift * 0.22, -head_turn * 0.16, 0.7 + chest_roll * 0.22)},
            "hood_r": {"rotation": (-lift * 0.18, -head_turn * 0.12, -0.7 + chest_roll * 0.18)},
            "hood_back": {"rotation": (-lift * 0.42, head_turn * 0.10, -chest_roll * 0.16)},
            "clavicle_l": {"rotation": (0, 0, -1.5 - lift)},
            "clavicle_r": {"rotation": (0, 0, 1.5 + lift)},
            "hand_l": {"rotation": (0, hand_turn, -2)},
            "hand_r": {"rotation": (0, -hand_turn, 2)},
        })

    # Run start: readable anticipation, first push and a contact pose that
    # matches the opening of the looping run.  Keeping this as a dedicated
    # non-looping action removes the instant idle-to-cycle snap in gameplay.
    new_action("A_Ciberfantasma_Pro_RunStart", 17)
    run_start_poses = (
        # frame, pelvis Y/Z, body pitch, thighs L/R, calves L/R, feet L/R, arms L/R, roll
        (1,   0.0,  0.0,  0,   0,   0,  0,  0,   0,   0,   0,   0,  0.0),
        (4,   2.2, -3.5, 14, -18, -22, 42, 48, -16, -18,  10, -12, -1.0),
        (8,   0.4, -1.5, 17,  35, -35, 32, 12, -10,   7, -32,  24, -2.2),
        (12, -1.0,  2.4, 11,  38, -32, 43, 11, -12,   7, -37,  29, -2.2),
        (17, -1.5,  0.5,  8,  40, -36, 48, 10, -14,   8, -42,  34, -2.5),
    )
    for (frame, pelvis_y, pelvis_z, pitch, thigh_l, thigh_r, calf_l, calf_r,
         foot_l, foot_r, arm_l, arm_r, roll) in run_start_poses:
        key(frame, {
            "pelvis": {"location": (0, pelvis_y, pelvis_z), "rotation": (0, -2, roll)},
            "spine_01": {"rotation": (pitch * 0.42, 0, -roll * 0.42)},
            "spine_02": {"rotation": (pitch * 0.58, 0, -roll * 0.30)},
            "neck": {"rotation": (-pitch * 0.18, 0, roll * 0.18)},
            "head": {"location": (0, 0, -pelvis_z * 0.20),
                     "rotation": (-pitch * 0.28, 0, -roll * 0.36)},
            "hood_l": {"rotation": (-pelvis_z * 0.28, arm_l * 0.03, -roll * 0.44)},
            "hood_r": {"rotation": (-pelvis_z * 0.25, arm_l * 0.025, -roll * 0.38)},
            "hood_back": {"location": (0, 0, -pelvis_z * 0.08),
                          "rotation": (-pitch * 0.30 - pelvis_z * 0.25,
                                       -arm_l * 0.035, roll * 0.50)},
            "thigh_l": {"rotation": (thigh_l, 0, -2)},
            "thigh_r": {"rotation": (thigh_r, 0, 2)},
            "calf_l": {"rotation": (calf_l, 0, 0)},
            "calf_r": {"rotation": (calf_r, 0, 0)},
            "foot_l": {"rotation": (foot_l, 0, 0)},
            "foot_r": {"rotation": (foot_r, 0, 0)},
            "toe_l": {"rotation": (-foot_l * 0.35, 0, 0)},
            "toe_r": {"rotation": (-foot_r * 0.35, 0, 0)},
            "clavicle_l": {"rotation": (arm_l * 0.10, 0, -2)},
            "clavicle_r": {"rotation": (arm_r * 0.10, 0, 2)},
            "upperarm_l": {"rotation": (arm_l, 0, -3)},
            "upperarm_r": {"rotation": (arm_r, 0, 3)},
            "lowerarm_l": {"rotation": (48 + abs(arm_l) * 0.16, 0, 0)},
            "lowerarm_r": {"rotation": (48 + abs(arm_r) * 0.16, 0, 0)},
            "hand_l": {"rotation": (-8, -roll * 0.5, 0)},
            "hand_r": {"rotation": (-8, roll * 0.5, 0)},
        })

    # Run: Canvas-authored contact, compression, passing and flight poses.  The
    # primary swing is local X (the character's sagittal plane); local Z is only
    # used for a little chibi asymmetry.  Driving the cycle on Z made both legs
    # fan out/collapse when the mesh was turned to face along the 2.5D lane.
    new_action("A_Ciberfantasma_Pro_Run", 25)
    run_poses = (
        # frame, thighs, knees, feet, opposing arm swing, body bob and roll
        (1, 40, -36, 48, 10, -14, 8, -42, 34, 0.5, -2.5),
        (4, 27, -22, 40, 20, -10, 4, -28, 22, -1.8, -1.2),
        (7, 5, 10, 56, 15, 8, -3, -7, 7, 0.2, 0.6),
        (10, -25, 33, 21, 40, 6, -10, 27, -28, 3.2, 2.3),
        (13, -36, 40, 10, 48, 8, -14, 35, -43, 0.5, 2.5),
        (16, -22, 27, 20, 40, 4, -10, 22, -28, -1.8, 1.2),
        (19, 10, 5, 15, 56, -3, 8, 7, -7, 0.2, -0.6),
        (22, 33, -25, 40, 21, -10, 6, -28, 27, 3.2, -2.3),
        (25, 40, -36, 48, 10, -14, 8, -42, 34, 0.5, -2.5),
    )
    for frame, thigh_l, thigh_r, calf_l, calf_r, foot_l, foot_r, arm_l, arm_r, bob, roll in run_poses:
        key(frame, {
            "pelvis": {"location": (0, -1.5, bob), "rotation": (0, -3, roll)},
            "spine_01": {"rotation": (7, 0, -roll * 0.45)},
            "spine_02": {"rotation": (9, 0, -roll * 0.3)},
            "neck": {"rotation": (-4, 0, roll * 0.2)},
            "head": {"location": (0, 0, -bob * 0.22), "rotation": (-5, 0, -roll * 0.4)},
            "hood_l": {"rotation": (-bob * 0.34, arm_l * 0.035, -roll * 0.48)},
            "hood_r": {"rotation": (-bob * 0.30, arm_l * 0.028, -roll * 0.42)},
            "hood_back": {"location": (0, 0, -bob * 0.10),
                          "rotation": (-bob * 0.60, -arm_l * 0.045, roll * 0.55)},
            "thigh_l": {"rotation": (thigh_l, 0, -2)},
            "thigh_r": {"rotation": (thigh_r, 0, 2)},
            "calf_l": {"rotation": (calf_l, 0, 0)},
            "calf_r": {"rotation": (calf_r, 0, 0)},
            "foot_l": {"rotation": (foot_l, 0, 0)},
            "foot_r": {"rotation": (foot_r, 0, 0)},
            "toe_l": {"rotation": (-foot_l * 0.35, 0, 0)},
            "toe_r": {"rotation": (-foot_r * 0.35, 0, 0)},
            "clavicle_l": {"rotation": (arm_l * 0.10, 0, -2)},
            "clavicle_r": {"rotation": (arm_r * 0.10, 0, 2)},
            "upperarm_l": {"rotation": (arm_l, 0, -3)},
            "upperarm_r": {"rotation": (arm_r, 0, 3)},
            "lowerarm_l": {"rotation": (58 + abs(arm_l) * 0.12, 0, 0)},
            "lowerarm_r": {"rotation": (58 + abs(arm_r) * 0.12, 0, 0)},
            "hand_l": {"rotation": (-9, -roll * 0.6, 0)},
            "hand_r": {"rotation": (-9, roll * 0.6, 0)},
        })

    # Run stop: begin on the opposite run contact, plant the leading foot,
    # counter-rotate the torso and absorb momentum before recovering to idle.
    new_action("A_Ciberfantasma_Pro_RunStop", 19)
    run_stop_poses = (
        # frame, pelvis Y/Z, body pitch, thighs L/R, calves L/R, feet L/R, arms L/R, roll
        (1,  -1.5,  0.5,  8, -36,  40, 10, 48,   8, -14,  35, -43,  2.5),
        (5,   0.5, -1.0, -5, -23,  31, 20, 36,   5, -10,  25, -31,  1.7),
        (9,   2.8, -4.2, -14, -12,  18, 42, 54, -18, -24,  16, -20,  1.1),
        (14,  1.2, -1.8, -6,  -5,   8, 20, 27,  -8, -10,   7,  -9,  0.4),
        (19,  0.0,  0.0,  0,   0,   0,  0,  0,   0,   0,   0,   0,  0.0),
    )
    for (frame, pelvis_y, pelvis_z, pitch, thigh_l, thigh_r, calf_l, calf_r,
         foot_l, foot_r, arm_l, arm_r, roll) in run_stop_poses:
        key(frame, {
            "pelvis": {"location": (0, pelvis_y, pelvis_z), "rotation": (0, -2, roll)},
            "spine_01": {"rotation": (pitch * 0.42, 0, -roll * 0.42)},
            "spine_02": {"rotation": (pitch * 0.58, 0, -roll * 0.30)},
            "neck": {"rotation": (-pitch * 0.18, 0, roll * 0.18)},
            "head": {"location": (0, 0, -pelvis_z * 0.20),
                     "rotation": (-pitch * 0.28, 0, -roll * 0.36)},
            "hood_l": {"rotation": (-pelvis_z * 0.28, arm_l * 0.03, -roll * 0.44)},
            "hood_r": {"rotation": (-pelvis_z * 0.25, arm_l * 0.025, -roll * 0.38)},
            "hood_back": {"location": (0, 0, -pelvis_z * 0.08),
                          "rotation": (-pitch * 0.30 - pelvis_z * 0.25,
                                       -arm_l * 0.035, roll * 0.50)},
            "thigh_l": {"rotation": (thigh_l, 0, -2)},
            "thigh_r": {"rotation": (thigh_r, 0, 2)},
            "calf_l": {"rotation": (calf_l, 0, 0)},
            "calf_r": {"rotation": (calf_r, 0, 0)},
            "foot_l": {"rotation": (foot_l, 0, 0)},
            "foot_r": {"rotation": (foot_r, 0, 0)},
            "toe_l": {"rotation": (-foot_l * 0.35, 0, 0)},
            "toe_r": {"rotation": (-foot_r * 0.35, 0, 0)},
            "clavicle_l": {"rotation": (arm_l * 0.10, 0, -2)},
            "clavicle_r": {"rotation": (arm_r * 0.10, 0, 2)},
            "upperarm_l": {"rotation": (arm_l, 0, -3)},
            "upperarm_r": {"rotation": (arm_r, 0, 3)},
            "lowerarm_l": {"rotation": (48 + abs(arm_l) * 0.16, 0, 0)},
            "lowerarm_r": {"rotation": (48 + abs(arm_r) * 0.16, 0, 0)},
            "hand_l": {"rotation": (-8, -roll * 0.5, 0)},
            "hand_r": {"rotation": (-8, roll * 0.5, 0)},
        })

    new_action("A_Ciberfantasma_Pro_JumpStart", 12)
    jump_start = (
        (1, 0, 0, 0, 0),
        (6, -9, -23, 44, -28),
        (12, 7, 15, 16, 38),
    )
    for frame, pelvis_z, chest, legs, arms in jump_start:
        key(frame, {
            "pelvis": {"location": (0, 0, pelvis_z), "rotation": (0, 0, 0)},
            "spine_01": {"rotation": (-chest * 0.35, 0, 0)},
            "spine_02": {"rotation": (-chest * 0.65, 0, 0)},
            "head": {"rotation": (chest * 0.25, 0, 0)},
            "hood_l": {"rotation": (-chest * 0.16, 0, 1.5)},
            "hood_r": {"rotation": (-chest * 0.14, 0, -1.5)},
            "hood_back": {"rotation": (-chest * 0.35, 0, 0)},
            "thigh_l": {"rotation": (-legs, 0, -3)}, "thigh_r": {"rotation": (-legs, 0, 3)},
            "calf_l": {"rotation": (legs * 1.7, 0, 0)}, "calf_r": {"rotation": (legs * 1.7, 0, 0)},
            "foot_l": {"rotation": (-legs * 0.55, 0, 0)}, "foot_r": {"rotation": (-legs * 0.55, 0, 0)},
            "upperarm_l": {"rotation": (arms, 0, -5)}, "upperarm_r": {"rotation": (arms, 0, 5)},
        })

    new_action("A_Ciberfantasma_Pro_JumpRise", 24)
    for frame, lift, tuck in ((1, 1.0, 40), (12, 3.5, 52), (24, 1.0, 40)):
        key(frame, {
            "pelvis": {"location": (0, 0, lift), "rotation": (0, 0, -2)},
            "spine_01": {"rotation": (8, 0, 3)}, "spine_02": {"rotation": (11, 0, 2)},
            "head": {"rotation": (-5, 0, -2)},
            "hood_l": {"rotation": (-5.5, 1.0, -2.0)},
            "hood_r": {"rotation": (-5.0, 0.7, -1.4)},
            "hood_back": {"rotation": (-9.0, -1.0, 2.5)},
            "thigh_l": {"rotation": (-tuck, 0, -4)}, "thigh_r": {"rotation": (18, 0, 4)},
            "calf_l": {"rotation": (86, 0, 0)}, "calf_r": {"rotation": (12, 0, 0)},
            "foot_l": {"rotation": (-28, 0, 0)}, "foot_r": {"rotation": (8, 0, 0)},
            "upperarm_l": {"rotation": (-24, 0, 100)}, "upperarm_r": {"rotation": (-24, 0, -100)},
            "lowerarm_l": {"rotation": (-31, 0, 138)}, "lowerarm_r": {"rotation": (-31, 0, -138)},
        })

    new_action("A_Ciberfantasma_Pro_JumpFall", 24)
    for frame, lift, spread in ((1, 1.0, 10), (12, -1.0, 15), (24, 1.0, 10)):
        key(frame, {
            "pelvis": {"location": (0, 0, lift), "rotation": (0, 0, 2)},
            "spine_01": {"rotation": (-5, 0, -2)}, "spine_02": {"rotation": (-8, 0, -3)},
            "head": {"rotation": (5, 0, 3)},
            "hood_l": {"rotation": (5.5, -0.8, 2.0)},
            "hood_r": {"rotation": (5.0, -0.5, 1.5)},
            "hood_back": {"rotation": (8.0, 1.0, -2.5)},
            "thigh_l": {"rotation": (-22 - spread, 0, -5)}, "thigh_r": {"rotation": (-22 + spread * 0.25, 0, 5)},
            "calf_l": {"rotation": (42, 0, 0)}, "calf_r": {"rotation": (34, 0, 0)},
            "foot_l": {"rotation": (-12, 0, 0)}, "foot_r": {"rotation": (-8, 0, 0)},
            "upperarm_l": {"rotation": (-12, 0, -22)}, "upperarm_r": {"rotation": (-12, 0, 22)},
            "lowerarm_l": {"rotation": (38, 0, 0)}, "lowerarm_r": {"rotation": (38, 0, 0)},
        })

    new_action("A_Ciberfantasma_Pro_Land", 16)
    # Hand-polished impact timing: pre-contact, two-frame compression hold and
    # two recovery breakdowns. The previous four-pose version crossed the
    # contact too smoothly and read as rubbery at gameplay speed.
    land_poses = (
        (1, 2, 4, 0),
        (3, 0, -4, 8),
        (5, -7, -17, 26),
        (7, -8, -19, 29),
        (10, -4, -9, 15),
        (13, -1, -3, 5),
        (16, 0, 0, 0),
    )
    for frame, pelvis_z, chest, knee in land_poses:
        key(frame, {
            "pelvis": {"location": (0, 1.5, pelvis_z), "rotation": (0, 0, 0)},
            "spine_01": {"rotation": (-chest * 0.4, 0, 0)},
            "spine_02": {"rotation": (-chest * 0.6, 0, 0)},
            "head": {"location": (0, 0, -pelvis_z * 0.25), "rotation": (chest * 0.25, 0, 0)},
            "hood_l": {"rotation": (-chest * 0.18, 0, -pelvis_z * 0.35)},
            "hood_r": {"rotation": (-chest * 0.16, 0, pelvis_z * 0.30)},
            "hood_back": {"location": (0, 0, -pelvis_z * 0.16),
                          "rotation": (-chest * 0.48, 0, 0)},
            "thigh_l": {"rotation": (-knee, 0, -3)}, "thigh_r": {"rotation": (-knee, 0, 3)},
            "calf_l": {"rotation": (knee * 1.8, 0, 0)}, "calf_r": {"rotation": (knee * 1.8, 0, 0)},
            "foot_l": {"rotation": (-knee * 0.55, 0, 0)}, "foot_r": {"rotation": (-knee * 0.55, 0, 0)},
            "upperarm_l": {"rotation": (-chest, 0, -6)}, "upperarm_r": {"rotation": (-chest, 0, 6)},
        })

    new_action("A_Ciberfantasma_Pro_Crouch", 48)
    for frame, breath in ((1, 0.0), (24, 1.2), (48, 0.0)):
        key(frame, {
            "pelvis": {"location": (0, 2.5, -12 + breath * 0.25)},
            "spine_01": {"rotation": (9, 0, -2)}, "spine_02": {"rotation": (10, 0, -2)},
            "head": {"location": (0, 0, breath), "rotation": (-8, 0, 3)},
            "hood_l": {"rotation": (-breath * 0.35, 0.5, -1.3)},
            "hood_r": {"rotation": (-breath * 0.30, 0.3, -1.0)},
            "hood_back": {"rotation": (-3.0 - breath * 0.5, -0.5, 1.0)},
            "thigh_l": {"rotation": (-42, 0, -4)}, "thigh_r": {"rotation": (-42, 0, 4)},
            "calf_l": {"rotation": (78, 0, 0)}, "calf_r": {"rotation": (78, 0, 0)},
            "foot_l": {"rotation": (-32, 0, 0)}, "foot_r": {"rotation": (-32, 0, 0)},
            "upperarm_l": {"rotation": (-8, 0, -5)}, "upperarm_r": {"rotation": (-8, 0, 5)},
            "lowerarm_l": {"rotation": (12, 0, 0)}, "lowerarm_r": {"rotation": (12, 0, 0)},
        })

    # Crouch walk: a low, deliberate eight-pose gait. Both knees remain loaded,
    # but contacts alternate, the pelvis transfers weight and the hood is
    # stabilized against the stronger motion of the short chibi legs.
    new_action("A_Ciberfantasma_Pro_CrouchWalk", 33)
    crouch_walk_poses = (
        # frame, thigh L/R, calf L/R, foot L/R, arm L/R, bob, roll
        (1,  -27, -52, 66, 86, -24, -35,  -8, -20,  0.0, -2.0),
        (5,  -33, -48, 73, 84, -27, -32, -12, -17, -1.0, -1.1),
        (9,  -39, -42, 80, 76, -31, -28, -16, -13, -0.4,  0.0),
        (13, -47, -34, 86, 71, -34, -26, -20,  -9,  0.5,  1.2),
        (17, -52, -27, 86, 66, -35, -24, -20,  -8,  0.0,  2.0),
        (21, -48, -33, 84, 73, -32, -27, -17, -12, -1.0,  1.1),
        (25, -42, -39, 76, 80, -28, -31, -13, -16, -0.4,  0.0),
        (29, -34, -47, 71, 86, -26, -34,  -9, -20,  0.5, -1.2),
        (33, -27, -52, 66, 86, -24, -35,  -8, -20,  0.0, -2.0),
    )
    for frame, thigh_l, thigh_r, calf_l, calf_r, foot_l, foot_r, arm_l, arm_r, bob, roll in crouch_walk_poses:
        key(frame, {
            "pelvis": {"location": (0, 3.2, -13.5 + bob), "rotation": (0, -2.5, roll)},
            "spine_01": {"rotation": (11, 0, -roll * 0.35)},
            "spine_02": {"rotation": (14, 0, -roll * 0.25)},
            "neck": {"rotation": (-5, 0, roll * 0.18)},
            "head": {"location": (0, 0, -bob * 0.18), "rotation": (-9, 0, -roll * 0.3)},
            "hood_l": {"rotation": (-bob * 0.28, arm_l * 0.025, -roll * 0.42)},
            "hood_r": {"rotation": (-bob * 0.25, arm_l * 0.020, -roll * 0.36)},
            "hood_back": {"rotation": (-2.0 - bob * 0.45, -arm_l * 0.03, roll * 0.50)},
            "thigh_l": {"rotation": (thigh_l, 0, -4)},
            "thigh_r": {"rotation": (thigh_r, 0, 4)},
            "calf_l": {"rotation": (calf_l, 0, 0)},
            "calf_r": {"rotation": (calf_r, 0, 0)},
            "foot_l": {"rotation": (foot_l, 0, 0)},
            "foot_r": {"rotation": (foot_r, 0, 0)},
            "toe_l": {"rotation": (-foot_l * 0.28, 0, 0)},
            "toe_r": {"rotation": (-foot_r * 0.28, 0, 0)},
            "clavicle_l": {"rotation": (arm_l * 0.12, 0, -3)},
            "clavicle_r": {"rotation": (arm_r * 0.12, 0, 3)},
            "upperarm_l": {"rotation": (arm_l, 0, -5)},
            "upperarm_r": {"rotation": (arm_r, 0, 5)},
            "lowerarm_l": {"rotation": (38, 0, -4)},
            "lowerarm_r": {"rotation": (38, 0, 4)},
            "hand_l": {"rotation": (-7, -roll * 0.4, 0)},
            "hand_r": {"rotation": (-7, roll * 0.4, 0)},
        })

    new_action("A_Ciberfantasma_Pro_Fire", 14)
    fire_poses = ((1, 0.0, 0, 0), (3, 1.0, -16, -5), (6, 1.0, -9, 2),
                  (10, 0.72, -3, 1), (14, 0.0, 0, 0))
    for frame, reach, recoil, body in fire_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, body * 0.2)},
            "spine_01": {"rotation": (body * 0.3, 0, 0)}, "spine_02": {"rotation": (body, 0, 0)},
            "head": {"rotation": (-body * 0.4, 0, 0)},
            "hood_l": {"rotation": (recoil * 0.10 * reach, 0, -body * 0.18)},
            "hood_r": {"rotation": (recoil * 0.08 * reach, 0, body * 0.14)},
            "hood_back": {"rotation": (recoil * 0.22 * reach, 0, 0)},
            "clavicle_l": {"rotation": (-4, 0, -3)},
            "upperarm_l": {"rotation": (-18, 0, -8)},
            "lowerarm_l": {"rotation": (52, 0, 0)},
            "hand_l": {"rotation": (-8, 0, 0)},
            "weapon_l": {"location": (0, recoil * 0.10, 0), "rotation": (recoil * 0.15, 0, 0)},
            "clavicle_r": {"rotation": ((-7 + recoil * 0.12) * reach, 0, 2 + 3 * reach)},
            "upperarm_r": {"rotation": ((-65 + recoil * 0.40) * reach,
                                              0, (70 - recoil * 0.18) * reach)},
            "lowerarm_r": {"rotation": ((23 - recoil * 0.12) * reach, 0, reach)},
            "hand_r": {"rotation": ((-4 + recoil * 0.18) * reach, 0, 0)},
        })

    # Contralateral fire is an additive upper-body action: locomotion keeps its
    # travel-facing silhouette while the hips stay committed forward and the
    # chest, hood and emitter arm unwind to shoot behind the run direction.
    new_action("A_Ciberfantasma_Pro_FireBack", 18)
    reverse_fire_poses = (
        (1, 0.0, 0.0, 0.0),
        (4, 0.78, 13.0, -8.0),
        (7, 1.0, 22.0, -17.0),
        (10, 1.0, 18.0, -9.0),
        (14, 0.58, 8.0, -3.0),
        (18, 0.0, 0.0, 0.0),
    )
    for frame, reach, twist, recoil in reverse_fire_poses:
        key(frame, {
            "pelvis": {"rotation": (0, -twist * 0.10, 0)},
            "spine_01": {"rotation": (2.0 * reach, twist * 0.42, -2.5 * reach)},
            "spine_02": {"rotation": (4.0 * reach, twist, -5.0 * reach)},
            "neck": {"rotation": (-2.0 * reach, -twist * 0.62, 2.0 * reach)},
            "head": {"rotation": (-3.0 * reach, -twist * 1.28, 4.0 * reach)},
            "hood_l": {"rotation": (recoil * 0.10 * reach, twist * 0.18, -twist * 0.14)},
            "hood_r": {"rotation": (recoil * 0.08 * reach, twist * 0.14, -twist * 0.10)},
            "hood_back": {"rotation": (recoil * 0.20 * reach, twist * 0.24, twist * 0.16)},
            "clavicle_l": {"rotation": (-4.0 * reach, 0, -4.0 * reach)},
            "upperarm_l": {"rotation": (-12.0 * reach, 0, -15.0 * reach)},
            "lowerarm_l": {"rotation": (42.0 * reach, 0, -5.0 * reach)},
            "hand_l": {"rotation": (-8.0 * reach, 0, 0)},
            "weapon_l": {"location": (0, recoil * 0.08, 0),
                         "rotation": (recoil * 0.12, 0, 0)},
            "clavicle_r": {"rotation": (7.0 * reach, 0, 6.0 * reach)},
            "upperarm_r": {"rotation": ((67.0 + recoil * 0.34) * reach,
                                            -8.0 * reach, (28.0 - recoil * 0.12) * reach)},
            "lowerarm_r": {"rotation": ((18.0 - recoil * 0.16) * reach,
                                            4.0 * reach, -6.0 * reach)},
            "hand_r": {"rotation": ((-7.0 + recoil * 0.20) * reach,
                                        -5.0 * reach, 0)},
        })

    new_action("A_Ciberfantasma_Pro_Shield", 48)
    shield_poses = ((1, -3, 0.96), (9, 4, 1.04), (24, 1, 1.0), (36, 4, 1.04), (48, -3, 0.96))
    for frame, pulse, scale in shield_poses:
        key(frame, {
            "pelvis": {"location": (0, 0, -3)},
            "spine_01": {"rotation": (5, 0, -1)}, "spine_02": {"rotation": (6, 0, -1)},
            "head": {"location": (0, 0, pulse * 0.15), "rotation": (-4, 0, 2)},
            "hood_l": {"rotation": (-pulse * 0.18, 0, -1.2)},
            "hood_r": {"rotation": (-pulse * 0.16, 0, -0.9)},
            "hood_back": {"rotation": (-pulse * 0.32, 0, 1.0)},
            "clavicle_l": {"rotation": (-5, 0, 8)}, "clavicle_r": {"rotation": (-5, 0, -8)},
            "upperarm_l": {"rotation": (-60, 0, -17)}, "upperarm_r": {"rotation": (-60, 0, 17)},
            "lowerarm_l": {"rotation": (-6, 0, -66)}, "lowerarm_r": {"rotation": (-6, 0, 66)},
            "hand_l": {"scale": (scale, scale, scale)}, "hand_r": {"scale": (scale, scale, scale)},
        })

    new_action("A_Ciberfantasma_Pro_Hit", 16)
    hit_poses = ((1, 0, 0), (4, 7, -16), (9, -3, 8), (16, 0, 0))
    for frame, shift, bend in hit_poses:
        key(frame, {
            "pelvis": {"location": (shift, 0, 0), "rotation": (0, 0, bend * 0.3)},
            "spine_01": {"rotation": (0, 0, bend * 0.4)}, "spine_02": {"rotation": (0, 0, bend)},
            "head": {"rotation": (0, 0, -bend * 0.65)},
            "hood_l": {"rotation": (abs(bend) * 0.18, 0, -bend * 0.72)},
            "hood_r": {"rotation": (abs(bend) * 0.15, 0, -bend * 0.58)},
            "hood_back": {"rotation": (abs(bend) * 0.32, 0, bend * 0.48)},
            "upperarm_l": {"rotation": (-10, 0, -18 - bend * 0.35)},
            "upperarm_r": {"rotation": (-10, 0, 18 + bend * 0.35)},
            "lowerarm_l": {"rotation": (34, 0, -8)}, "lowerarm_r": {"rotation": (34, 0, 8)},
        })
    # Final curve pass after reviewing the clips frame by frame. Auto-clamped
    # Bezier handles preserve the hand-authored timing while preventing hidden
    # overshoot between keys (especially feet, wrists and the rear hood). FBX
    # then bakes the evaluated result on every frame at the project-native 60 Hz.
    polished_points = 0
    for action in actions.values():
        for layer in getattr(action, "layers", ()):
            for strip in getattr(layer, "strips", ()):
                for channel_bag in getattr(strip, "channelbags", ()):
                    for curve in channel_bag.fcurves:
                        for point in curve.keyframe_points:
                            point.interpolation = "BEZIER"
                            point.handle_left_type = "AUTO_CLAMPED"
                            point.handle_right_type = "AUTO_CLAMPED"
                            polished_points += 1
    print(f"Curve polish: {polished_points} keys use auto-clamped Bezier handles")
    return actions


def export_player_actions(mesh, armature, actions):
    for action_name, action in actions.items():
        armature.animation_data.action = action
        bpy.context.scene.frame_start = int(action.frame_range[0])
        bpy.context.scene.frame_end = int(action.frame_range[1])
        bpy.context.scene.frame_set(int(action.frame_range[0]))
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
    original_location = player.location.copy()
    original_rotation = player.rotation_euler.copy()
    original_hidden = {obj.name: obj.hide_render for obj in bpy.context.scene.objects}
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            obj.hide_render = True
    player.hide_render = False
    player.location = (-115, 0, 0)
    three_quarter = player.copy()
    three_quarter.data = player.data
    three_quarter.location = (0, 0, 0)
    three_quarter.rotation_euler.z = math.radians(-42)
    bpy.context.collection.objects.link(three_quarter)
    three_quarter.hide_render = False
    back = player.copy()
    back.data = player.data
    back.location = (115, 0, 0)
    back.rotation_euler.z = math.radians(180)
    bpy.context.collection.objects.link(back)
    back.hide_render = False

    floor_mat = make_material("M_PreviewFloor", (0.16, 0.17, 0.18, 1), 0.0, 0.62, None)
    preview_floor = cube("PREVIEW_Floor", (0, 0, -7), (235, 130, 7), floor_mat, 2.0)

    bpy.ops.object.light_add(type="AREA", location=(0, -240, 260))
    key = bpy.context.object
    key.data.energy = 12000
    key.data.shape = "DISK"
    key.data.size = 180
    look_at(key, (0, 0, 80))
    bpy.ops.object.light_add(type="AREA", location=(180, 100, 190))
    rim = bpy.context.object
    rim.data.energy = 6800
    rim.data.color = (0.65, 0.78, 1.0)
    rim.data.size = 130
    look_at(rim, (80, 0, 90))
    bpy.ops.object.light_add(type="AREA", location=(-180, -80, 130))
    fill = bpy.context.object
    fill.data.energy = 7600
    fill.data.color = (0.82, 0.88, 1.0)
    fill.data.size = 100
    look_at(fill, (-80, 0, 80))
    bpy.ops.object.light_add(type="AREA", location=(0, -300, 95))
    front_fill = bpy.context.object
    front_fill.data.energy = 10800
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
    background.inputs["Strength"].default_value = 0.68
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.30
    PREVIEW_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(PREVIEW_OUTPUT)
    bpy.ops.render.render(write_still=True)

    # Preview staging must never leak into the canonical rig workfile. In
    # particular, leaving the bound mesh translated -115 cm relative to its
    # armature magnified rotations and made animation-bound audits misleading.
    scene.camera = None
    for preview_object in (three_quarter, back, preview_floor, key, rim, fill, front_fill, camera):
        bpy.data.objects.remove(preview_object, do_unlink=True)
    player.location = original_location
    player.rotation_euler = original_rotation
    for obj in bpy.context.scene.objects:
        obj.hide_render = original_hidden.get(obj.name, False)


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
    generate_hero_surface_maps()
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
    scene["cf_character_height_cm"] = 166.0
    scene["cf_asset_status"] = "hero V11 close-up pass: single tailored bell hood, compact lower skull graphic, refined bevel highlights, 2K packed PBR/normal maps, production UV0, 26-bone rig and 14 actions; grounded run/crouch cycles, dedicated contralateral-fire, auto-clamped curve polish and per-frame 60 Hz bake"
    scene["cf_enemy_count"] = len(enemy_models)
    BLENDER_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLENDER_OUTPUT), compress=True)
    print(f"Saved source scene {BLENDER_OUTPUT}")
    print(f"Total enemy models exported: {len(enemy_models)}")


if __name__ == "__main__":
    build()
