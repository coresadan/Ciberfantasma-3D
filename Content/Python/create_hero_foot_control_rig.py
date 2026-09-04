"""Build the editable production foot Control Rig for Ciberfantasma.

Runtime grounding mirrors this graph in native code so the existing custom
locomotion mixer remains deterministic. This asset is the artist-facing rig for
Sequencer/Animation Mode and future hand-authored corrective passes.
"""

import unreal


ASSET_PATH = "/Game/Art/Characters/Rigs/CR_Ciberfantasma_FootIK"
MESH_PATH = "/Game/Art/Characters/SK_Ciberfantasma_Chibi_Pro"


def require(value, message):
    if value is None or value is False:
        raise RuntimeError(message)
    return value


def make_key(name, element_type):
    return unreal.RigElementKey(type=element_type, name=name)


def add_transform_control(hierarchy, controller, name, world_transform, color):
    settings = unreal.RigControlSettings()
    settings.control_type = unreal.RigControlType.EULER_TRANSFORM
    settings.display_name = name
    settings.shape_color = color
    value = hierarchy.make_control_value_from_euler_transform(
        unreal.EulerTransform(scale=[1.0, 1.0, 1.0]))
    key = controller.add_control(
        name, unreal.RigElementKey(), settings, value, False, False)
    hierarchy.set_control_offset_transform(key, world_transform, True)
    return key


def add_two_bone_chain(graph_controller, hierarchy, side, foot_control, pole_control, position):
    thigh_key = make_key(f"thigh_{side}", unreal.RigElementType.BONE)
    calf_key = make_key(f"calf_{side}", unreal.RigElementType.BONE)
    foot_key = make_key(f"foot_{side}", unreal.RigElementType.BONE)

    thigh = hierarchy.get_global_transform(thigh_key, True)
    calf = hierarchy.get_global_transform(calf_key, True)
    foot = hierarchy.get_global_transform(foot_key, True)
    primary_axis = calf.make_relative(thigh).translation.normal()
    pole = hierarchy.get_global_transform(pole_control, True)
    secondary_axis = pole.make_relative(calf).translation
    secondary_axis = secondary_axis - primary_axis * primary_axis.dot(secondary_axis)

    ik_defaults = unreal.RigUnit_TwoBoneIKSimplePerItem()
    ik_defaults.item_a = thigh_key
    ik_defaults.item_b = calf_key
    ik_defaults.effector_item = foot_key
    ik_defaults.effector = foot
    ik_defaults.primary_axis = primary_axis
    ik_defaults.item_a_length = calf.make_relative(thigh).translation.length()
    ik_defaults.item_b_length = foot.make_relative(calf).translation.length()
    ik_defaults.secondary_axis_weight = 1.0
    ik_defaults.secondary_axis = secondary_axis
    ik_defaults.pole_vector = unreal.Vector()
    ik_defaults.pole_vector_kind = unreal.ControlRigVectorKind.LOCATION
    ik_defaults.pole_vector_space = pole_control

    ik_node = graph_controller.add_unit_node_with_defaults(
        ik_defaults.static_struct(), ik_defaults.export_text(), "Execute",
        position, f"FootIK_{side.upper()}", False)
    require(ik_node, f"No se pudo crear TwoBoneIK {side}")

    get_defaults = unreal.RigUnit_GetTransform()
    get_defaults.item = foot_control
    get_defaults.space = unreal.RigVMTransformSpace.GLOBAL_SPACE
    get_defaults.initial = False
    get_node = graph_controller.add_unit_node_with_defaults(
        get_defaults.static_struct(), get_defaults.export_text(), "Execute",
        unreal.Vector2D(position.x - 360.0, position.y + 180.0),
        f"GetFootControl_{side.upper()}", False)
    require(get_node, f"No se pudo crear GetTransform {side}")
    require(graph_controller.add_link(
        get_node.find_pin("Transform").get_pin_path(),
        ik_node.find_pin("Effector").get_pin_path(), False),
        f"No se pudo conectar el efector {side}")
    return ik_node


def main():
    unreal.load_module("ControlRigDeveloper")
    mesh = require(unreal.load_asset(MESH_PATH), f"No existe {MESH_PATH}")
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        rig = require(unreal.load_asset(ASSET_PATH), f"No se pudo cargar {ASSET_PATH}")
        unreal.log(f"CF_CONTROL_RIG: el asset ya existe; se conserva {ASSET_PATH}")
        return

    rig = require(
        unreal.ControlRigBlueprintFactory.create_new_control_rig_asset(ASSET_PATH),
        "No se pudo crear el Control Rig")
    rig.set_auto_vm_recompile(False)
    hierarchy = rig.hierarchy
    hierarchy_controller = hierarchy.get_controller()
    imported = hierarchy_controller.import_bones_from_asset(
        mesh.get_path_name(), "", True, True, False, False)
    require(len(imported) >= 26, f"Jerarquía incompleta: {len(imported)} huesos")

    foot_l = hierarchy.get_global_transform(make_key("foot_l", unreal.RigElementType.BONE), True)
    foot_r = hierarchy.get_global_transform(make_key("foot_r", unreal.RigElementType.BONE), True)
    calf_l = hierarchy.get_global_transform(make_key("calf_l", unreal.RigElementType.BONE), True)
    calf_r = hierarchy.get_global_transform(make_key("calf_r", unreal.RigElementType.BONE), True)
    pole_l_transform = unreal.Transform(
        location=calf_l.translation + unreal.Vector(0.0, -48.0, 2.0))
    pole_r_transform = unreal.Transform(
        location=calf_r.translation + unreal.Vector(0.0, -48.0, 2.0))

    cyan = unreal.LinearColor(0.03, 0.82, 1.0, 1.0)
    magenta = unreal.LinearColor(1.0, 0.10, 0.62, 1.0)
    foot_ctrl_l = add_transform_control(
        hierarchy, hierarchy_controller, "CTRL_FootIK_L", foot_l, cyan)
    foot_ctrl_r = add_transform_control(
        hierarchy, hierarchy_controller, "CTRL_FootIK_R", foot_r, magenta)
    pole_ctrl_l = add_transform_control(
        hierarchy, hierarchy_controller, "CTRL_KneePole_L", pole_l_transform, cyan)
    pole_ctrl_r = add_transform_control(
        hierarchy, hierarchy_controller, "CTRL_KneePole_R", pole_r_transform, magenta)

    graph_controller = require(
        rig.get_controller_by_name("RigVMModel"), "No existe RigVMModel")
    graph = graph_controller.get_graph()
    begin_node = None
    for node in graph.get_nodes():
        if node.find_pin("ExecuteContext"):
            begin_node = node
            break
    if begin_node is None:
        begin_defaults = unreal.RigUnit_BeginExecution()
        begin_node = graph_controller.add_unit_node_with_defaults(
            begin_defaults.static_struct(), begin_defaults.export_text(), "Execute",
            unreal.Vector2D(-760.0, 0.0), "ForwardSolve", False)
    require(begin_node, "No existe el evento Forward Solve")

    left_ik = add_two_bone_chain(
        graph_controller, hierarchy, "l", foot_ctrl_l, pole_ctrl_l,
        unreal.Vector2D(-160.0, -120.0))
    right_ik = add_two_bone_chain(
        graph_controller, hierarchy, "r", foot_ctrl_r, pole_ctrl_r,
        unreal.Vector2D(320.0, -120.0))
    require(graph_controller.add_link(
        begin_node.find_pin("ExecuteContext").get_pin_path(),
        left_ik.find_pin("ExecuteContext").get_pin_path(), False),
        "No se pudo conectar Forward Solve a IK_L")
    require(graph_controller.add_link(
        left_ik.find_pin("ExecuteContext").get_pin_path(),
        right_ik.find_pin("ExecuteContext").get_pin_path(), False),
        "No se pudo encadenar IK_L con IK_R")

    rig.set_auto_vm_recompile(True)
    rig.request_auto_vm_recompilation()
    unreal.EditorAssetLibrary.save_asset(ASSET_PATH, only_if_is_dirty=False)
    unreal.log(
        f"CF_CONTROL_RIG_CREATED bones={len(imported)} controls=4 nodes={len(graph.get_nodes())} asset={ASSET_PATH}")


if __name__ == "__main__":
    main()
