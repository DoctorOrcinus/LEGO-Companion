bl_info = {
    "name": "Doctor Orcinus LEGO Tweaks",
    "author": "Custom",
    "version": (1, 5, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Doctor Orcinus",
    "description": "Organic Motion, Delta Reset und Shader-Patching fuer LEGO-Projekte",
    "category": "Animation",
}

import bpy
import random
from bpy.props import FloatProperty, BoolProperty, PointerProperty, IntProperty
from bpy.types import PropertyGroup

# ---------------------------------------------------------------------------
# ORGANIC MOTION – Properties & Helpers
# ---------------------------------------------------------------------------

class AxisNoiseSettings(PropertyGroup):
    enabled: BoolProperty(name="", default=True)
    scale: FloatProperty(name="Scale", default=35.0, min=0.1, max=1000.0, precision=2)
    strength: FloatProperty(name="Strength", default=0.025, min=0.0, max=10.0, precision=4)

class CameraNoiseSettings(PropertyGroup):
    x: PointerProperty(type=AxisNoiseSettings)
    y: PointerProperty(type=AxisNoiseSettings)
    z: PointerProperty(type=AxisNoiseSettings)

class BoneNoiseSettings(PropertyGroup):
    x: PointerProperty(type=AxisNoiseSettings)
    y: PointerProperty(type=AxisNoiseSettings)
    z: PointerProperty(type=AxisNoiseSettings)


def _apply_noise_to_fcurve(action, data_path, array_index, scale, strength):
    fcurve = None
    for fc in action.fcurves:
        if fc.data_path == data_path and fc.array_index == array_index:
            fcurve = fc
            break
    if fcurve is None:
        fcurve = action.fcurves.new(data_path=data_path, index=array_index)
    if len(fcurve.keyframe_points) == 0:
        fcurve.keyframe_points.insert(bpy.context.scene.frame_current, 0.0)
        fcurve.keyframe_points.insert(bpy.context.scene.frame_current + 1, 0.0)
    for mod in list(fcurve.modifiers):
        if mod.type == "NOISE":
            fcurve.modifiers.remove(mod)
    noise = fcurve.modifiers.new(type="NOISE")
    noise.scale = scale
    noise.strength = strength
    noise.phase = random.uniform(150, 500)
    noise.offset = random.uniform(0, 100)


def _ensure_action(obj):
    if obj.animation_data is None:
        obj.animation_data_create()
    if obj.animation_data.action is None:
        obj.animation_data.action = bpy.data.actions.new(name=obj.name + "Action")
    return obj.animation_data.action


def draw_axis_row(layout, label, axis_prop):
    row = layout.row(align=True)
    row.prop(axis_prop, "enabled", text="")
    sub = row.row(align=True)
    sub.enabled = axis_prop.enabled
    sub.label(text=label)
    sub.prop(axis_prop, "scale")
    sub.prop(axis_prop, "strength")

# ---------------------------------------------------------------------------
# ORGANIC MOTION – Operators
# ---------------------------------------------------------------------------

class CAMERA_OT_add_noise_motion(bpy.types.Operator):
    bl_idname = "camera.add_noise_motion"
    bl_label = "Apply to Camera"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "CAMERA"

    def execute(self, context):
        obj = context.active_object
        s = context.scene.camera_noise_settings
        frame = context.scene.frame_current
        obj.rotation_mode = "XYZ"
        for idx, ax in enumerate([s.x, s.y, s.z]):
            if ax.enabled:
                obj.keyframe_insert(data_path="rotation_euler", index=idx, frame=frame)
        action = _ensure_action(obj)
        applied = []
        for idx, ax in enumerate([s.x, s.y, s.z]):
            if ax.enabled:
                _apply_noise_to_fcurve(action, "rotation_euler", idx, ax.scale, ax.strength)
                applied.append("XYZ"[idx])
        if applied:
            self.report({"INFO"}, "Organic Motion: {} – Achsen: {}".format(obj.name, ", ".join(applied)))
        else:
            self.report({"WARNING"}, "Keine Achsen ausgewaehlt.")
        return {"FINISHED"}


class CAMERA_OT_reset_noise_defaults(bpy.types.Operator):
    bl_idname = "camera.reset_noise_defaults"
    bl_label = "Reset Camera Defaults"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene.camera_noise_settings
        s.x.enabled = True; s.x.scale = 35.0; s.x.strength = 0.025
        s.y.enabled = True; s.y.scale = 45.0; s.y.strength = 0.025
        s.z.enabled = True; s.z.scale = 30.0; s.z.strength = 0.005
        return {"FINISHED"}


class BONE_OT_add_noise_motion(bpy.types.Operator):
    bl_idname = "pose.add_noise_motion"
    bl_label = "Apply to Selected Bones"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None and obj.type == "ARMATURE"
                and context.mode == "POSE"
                and len(context.selected_pose_bones) > 0)

    def execute(self, context):
        obj = context.active_object
        s = context.scene.bone_noise_settings
        bones = context.selected_pose_bones
        frame = context.scene.frame_current
        for bone in bones:
            bone.rotation_mode = "XYZ"
            dp = "pose.bones[\"{}\"].rotation_euler".format(bone.name)
            for idx, ax in enumerate([s.x, s.y, s.z]):
                if ax.enabled:
                    obj.keyframe_insert(data_path=dp, index=idx, frame=frame)
        action = _ensure_action(obj)
        processed = []
        for bone in bones:
            dp = "pose.bones[\"{}\"].rotation_euler".format(bone.name)
            applied = []
            for idx, ax in enumerate([s.x, s.y, s.z]):
                if ax.enabled:
                    _apply_noise_to_fcurve(action, dp, idx, ax.scale, ax.strength)
                    applied.append("XYZ"[idx])
            if applied:
                processed.append("{} ({})".format(bone.name, ", ".join(applied)))
        if processed:
            self.report({"INFO"}, "Organic Motion: {}".format("; ".join(processed)))
        else:
            self.report({"WARNING"}, "Keine Achsen ausgewaehlt.")
        return {"FINISHED"}


class BONE_OT_reset_noise_defaults(bpy.types.Operator):
    bl_idname = "pose.reset_noise_defaults"
    bl_label = "Reset Bone Defaults"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        s = context.scene.bone_noise_settings
        s.x.enabled = True; s.x.scale = 35.0; s.x.strength = 0.025
        s.y.enabled = True; s.y.scale = 45.0; s.y.strength = 0.025
        s.z.enabled = True; s.z.scale = 30.0; s.z.strength = 0.005
        return {"FINISHED"}

# ---------------------------------------------------------------------------
# DELTA RESET – Operator
# ---------------------------------------------------------------------------

class DOCORCINUS_OT_reset_lego_delta(bpy.types.Operator):
    bl_idname = "doctor_orcinus.reset_lego_delta"
    bl_label = "Reset LEGO Delta Transform"
    bl_description = "Setzt Delta Location und Delta Rotation aller ausgewaehlten Objekte auf 0"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected = list(context.selected_objects)
        if not selected:
            self.report({"WARNING"}, "Keine Objekte ausgewaehlt.")
            return {"CANCELLED"}
        for obj in selected:
            obj.delta_location = (0.0, 0.0, 0.0)
            if obj.rotation_mode in {"QUATERNION", "AXIS_ANGLE"}:
                obj.rotation_mode = "XYZ"
            obj.delta_rotation_euler = (0.0, 0.0, 0.0)
        self.report({"INFO"}, "Delta Transform fuer {} Objekt(e) zurueckgesetzt.".format(len(selected)))
        return {"FINISHED"}

# ---------------------------------------------------------------------------
# SHADER PATCHER – Helpers
# ---------------------------------------------------------------------------

def find_scale_node(tree):
    for node in tree.nodes:
        if node.bl_idname == "ShaderNodeValue" and node.label == "Scale":
            return node
    return None


def is_auto_scale_multiply(node):
    return (
        node is not None
        and node.bl_idname == "ShaderNodeMath"
        and node.operation == "MULTIPLY"
        and "Scale Multiply (auto)" in node.label
    )


def already_patched(inp):
    if inp.is_linked:
        fn = inp.links[0].from_node
        if fn.bl_idname == "ShaderNodeMath" and "Scale Multiply (auto)" in fn.label:
            return True
    return False


def insert_multiply(tree, existing_link, target_socket, scale_factor):
    mult = tree.nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.label = "Scale Multiply (auto)"
    mult.inputs[1].default_value = scale_factor
    tn = target_socket.node
    mult.location = (tn.location.x - 220, tn.location.y - 40)
    fs = existing_link.from_socket
    tree.links.remove(existing_link)
    tree.links.new(fs, mult.inputs[0])
    tree.links.new(mult.outputs[0], target_socket)
    return mult


def patch_bump_bevel(tree, visited, scale_factor, path="", skip_bevel=False):
    log = []
    if tree.name_full in visited:
        return log
    visited.add(tree.name_full)
    targets = {"ShaderNodeBump": "Distance", "ShaderNodeBevel": "Radius"}
    for node in tree.nodes:
        np = "{} > {}".format(path, node.name)
        if node.bl_idname == "ShaderNodeGroup" and node.node_tree:
            gl = "{} ('{}')".format(node.name, node.node_tree.name)
            next_skip = skip_bevel or (node.node_tree.name.lower().strip() == "mb_config_normal")
            log += patch_bump_bevel(node.node_tree, visited, scale_factor, "{} > {}".format(path, gl), next_skip)
        if node.bl_idname in targets:
            if skip_bevel and node.bl_idname == "ShaderNodeBevel":
                log.append("[SKIP bevel excluded] {}".format(np))
                continue
            iname = targets[node.bl_idname]
            inp = node.inputs.get(iname)
            if not inp:
                continue
            if already_patched(inp):
                log.append("[SKIP] {} | {}".format(np, iname))
                continue
            if inp.is_linked:
                insert_multiply(tree, inp.links[0], inp, scale_factor)
                log.append("[MULTIPLY NODE] {} | {}".format(np, iname))
            else:
                old = inp.default_value
                inp.default_value = old * scale_factor
                log.append("[SET VALUE] {} | {}: {:.5f} -> {:.7f}".format(np, iname, old, inp.default_value))
    return log


def patch_microscratches_multiply(tree, visited, path="", in_micros=False):
    log = []
    key = (tree.name_full, in_micros)
    if key in visited:
        return log
    visited.add(key)
    cur = in_micros or ("thorn_triplanar microscratches" in tree.name.lower())
    for node in tree.nodes:
        np = "{} > {}".format(path, node.name)
        if node.bl_idname == "ShaderNodeGroup" and node.node_tree and not cur:
            gl = "{} ('{}')".format(node.name, node.node_tree.name)
            nxt = "thorn_triplanar microscratches" in node.node_tree.name.lower()
            log += patch_microscratches_multiply(node.node_tree, visited, "{} > {}".format(path, gl), nxt)
        if cur and node.bl_idname == "ShaderNodeMath" and node.operation == "MULTIPLY":
            if "Scale Multiply (auto)" in node.label:
                continue
            if len(node.inputs) < 2:
                continue
            i0, i1 = node.inputs[0], node.inputs[1]
            if not i0.is_linked and i1.is_linked:
                old = i0.default_value
                target = 0.2
                if abs(old - target) > 1e-6:
                    i0.default_value = target
                    log.append("[SCRATCH MULT] {} | Input 0: {:.5f} -> {}".format(np, old, target))
                else:
                    log.append("[SKIP] {} | Input 0: bereits {}".format(np, target))
    return log


def patch_sss_depth(tree, visited, scale_factor, path="", is_root=True):
    log = []
    if not is_root:
        if tree.name_full in visited:
            return log
        visited.add(tree.name_full)
    for node in tree.nodes:
        np = "{} > {}".format(path, node.name)
        if node.bl_idname == "ShaderNodeGroup" and node.node_tree:
            gl = "{} ('{}')".format(node.name, node.node_tree.name)
            if "mmua_base_solid" in node.node_tree.name.lower():
                inp = node.inputs.get("Sss Depth")
                if inp:
                    if already_patched(inp):
                        log.append("[SKIP] {} | Sss Depth".format(np))
                    elif inp.is_linked:
                        insert_multiply(tree, inp.links[0], inp, scale_factor)
                        log.append("[MULTIPLY NODE] {} | Sss Depth".format(np))
                    else:
                        old = inp.default_value
                        inp.default_value = old * scale_factor
                        log.append("[SET VALUE] {} | Sss Depth: {:.5f} -> {:.7f}".format(np, old, inp.default_value))
                else:
                    log.append("[WARN] {} | Sss Depth nicht gefunden".format(np))
            log += patch_sss_depth(node.node_tree, visited, scale_factor, "{} > {}".format(path, gl), is_root=False)
    return log


def normalize_already_between(link):
    fn = link.from_node
    return (fn.bl_idname == "ShaderNodeVectorMath"
            and fn.operation == "NORMALIZE"
            and "auto" in fn.label.lower())


def insert_normalize_between(tree, existing_link, target_socket):
    norm = tree.nodes.new("ShaderNodeVectorMath")
    norm.operation = "NORMALIZE"
    norm.label = "Auto Normalize"
    tn = target_socket.node
    norm.location = (tn.location.x - 220, tn.location.y - 30)
    fs = existing_link.from_socket
    tree.links.remove(existing_link)
    tree.links.new(fs, norm.inputs[0])
    tree.links.new(norm.outputs[0], target_socket)
    return norm


def patch_triplanar_normalize(tree, visited, path="", in_target=False):
    log = []
    key = (tree.name_full, in_target)
    if key in visited:
        return log
    visited.add(key)
    cur = in_target or ("thorn_triplanar normal map" in tree.name.lower())
    for node in tree.nodes:
        np = "{} > {}".format(path, node.name)
        if node.bl_idname == "ShaderNodeGroup" and node.node_tree:
            gl = "{} ('{}')".format(node.name, node.node_tree.name)
            nxt = cur or ("thorn_triplanar normal map" in node.node_tree.name.lower())
            log += patch_triplanar_normalize(node.node_tree, visited, "{} > {}".format(path, gl), nxt)
        if cur and node.bl_idname == "ShaderNodeVectorMath" and node.operation == "SCALE":
            vi = node.inputs[0]
            if vi.is_linked:
                link = vi.links[0]
                fn = link.from_node
                if fn.bl_idname == "ShaderNodeVectorMath" and fn.operation == "CROSS_PRODUCT":
                    if normalize_already_between(link):
                        log.append("[SKIP] {} | Normalize vorhanden".format(np))
                    else:
                        insert_normalize_between(tree, link, vi)
                        log.append("[NORMALIZE] {} | eingefuegt".format(np))
    return log


def run_all_patches(obj, scale_factor, vb, vm, vs, vn):
    mat = obj.active_material
    if not mat or not mat.use_nodes:
        return "[{}] Kein Material mit Nodes.".format(obj.name)
    if not find_scale_node(mat.node_tree):
        return "[{}] Keine Scale-Node gefunden.".format(obj.name)
    r = []
    r += patch_bump_bevel(mat.node_tree, vb, scale_factor)
    r += patch_microscratches_multiply(mat.node_tree, vm)
    r += patch_sss_depth(mat.node_tree, vs, scale_factor, is_root=True)
    r += patch_triplanar_normalize(mat.node_tree, vn)
    return "[{}] {}: {} Eintraege.".format(obj.name, mat.name, len(r))

# ---------------------------------------------------------------------------
# MECAFACE SCALE PATCHER – Helpers
# ---------------------------------------------------------------------------

import re
MECAFACE_PATCH_FLAG = "mecaface_material_scale_patched"
MECAFACE_PATCH_SCALE_KEY = "mecaface_material_scale_value"
MECAFACE_NUM_SUFFIX_RE = re.compile(r"\.\d{3}$")


def mecaface_base_name(name):
    return MECAFACE_NUM_SUFFIX_RE.sub("", name)


def find_group_node_by_base_name(tree, wanted_name):
    for node in tree.nodes:
        if (
            node.bl_idname == "ShaderNodeGroup"
            and node.node_tree is not None
            and mecaface_base_name(node.node_tree.name) == wanted_name
        ):
            return node
    return None


def gather_mecaface_material_trees():
    found = []
    seen = set()
    for mat in bpy.data.materials:
        if not mat.use_nodes or not mat.node_tree:
            continue
        mecaface_node = find_group_node_by_base_name(mat.node_tree, "MecaFace.Material")
        if not mecaface_node:
            continue
        mecaface_tree = mecaface_node.node_tree
        key = mecaface_tree.as_pointer()
        if key in seen:
            continue
        seen.add(key)
        found.append((mat, mecaface_tree))
    return found


def mecaface_is_locked(mecaface_tree):
    return bool(mecaface_tree.get(MECAFACE_PATCH_FLAG, False))


def mecaface_store_patch_lock(mecaface_tree, scale_value):
    mecaface_tree[MECAFACE_PATCH_FLAG] = True
    mecaface_tree[MECAFACE_PATCH_SCALE_KEY] = float(scale_value)


def find_target_noise_node(tree, expected_scale=3.75, ignore_scale=50.0, eps=1e-6):
    for node in tree.nodes:
        if node.bl_idname != "ShaderNodeTexNoise":
            continue
        scale_input = node.inputs.get("Scale")
        if not scale_input:
            continue
        value = float(scale_input.default_value)
        if abs(value - ignore_scale) <= eps:
            continue
        if abs(value - expected_scale) <= eps:
            return node
    return None


def find_target_bevel_node(tree):
    for node in tree.nodes:
        if node.bl_idname != "ShaderNodeBevel":
            continue
        radius_in = node.inputs.get("Radius")
        if not radius_in or not radius_in.is_linked:
            continue
        from_node = radius_in.links[0].from_node
        if (
            from_node
            and from_node.bl_idname == "ShaderNodeMath"
            and from_node.operation == "MULTIPLY"
        ):
            return node
    return None


def is_mecaface_auto_scale_multiply(node):
    return (
        node is not None
        and node.bl_idname == "ShaderNodeMath"
        and node.operation == "MULTIPLY"
        and "MecaFace Scale Multiply (auto)" in node.label
    )


def insert_mecaface_multiply(tree, existing_link, target_socket, scale_factor):
    mult = tree.nodes.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    mult.label = "MecaFace Scale Multiply (auto)"
    mult.inputs[1].default_value = scale_factor
    tn = target_socket.node
    mult.location = (tn.location.x - 220, tn.location.y - 40)
    fs = existing_link.from_socket
    tree.links.remove(existing_link)
    tree.links.new(fs, mult.inputs[0])
    tree.links.new(mult.outputs[0], target_socket)
    return mult


def mecaface_patch_material_tree_once(mecaface_tree, scale_value):
    log = []

    noise = find_target_noise_node(mecaface_tree)
    if noise:
        scale_in = noise.inputs.get("Scale")
        old_scale = float(scale_in.default_value)
        new_scale = 3.75 * scale_value
        scale_in.default_value = new_scale
        log.append("[{}] Noise Scale: {:.6f} -> {:.6f}".format(mecaface_tree.name, old_scale, new_scale))
    else:
        log.append("[{}] Keine passende Noise Texture mit Scale 3.75 gefunden.".format(mecaface_tree.name))

    bevel = find_target_bevel_node(mecaface_tree)
    if bevel:
        radius_in = bevel.inputs.get("Radius")
        existing_link = radius_in.links[0]
        from_node = existing_link.from_node
        if is_mecaface_auto_scale_multiply(from_node):
            from_node.inputs[1].default_value = scale_value
            log.append("[{}] Bevel Radius Multiply schon vorhanden -> Scale {}".format(mecaface_tree.name, scale_value))
        else:
            insert_mecaface_multiply(mecaface_tree, existing_link, radius_in, scale_value)
            log.append("[{}] Bevel Radius Multiply eingefuegt mit Scale {}".format(mecaface_tree.name, scale_value))
    else:
        log.append("[{}] Keine passende Bevel-Node mit verkabeltem Multiply-Radius gefunden.".format(mecaface_tree.name))

    return log

# ---------------------------------------------------------------------------
# SHADER PATCHER – Properties & Operators
# ---------------------------------------------------------------------------

class MMUAPatcherProperties(bpy.types.PropertyGroup):
    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Skalierungsfaktor fuer Shader-Patching (z.B. 0.001)",
        default=0.01, min=0.000001, max=1000.0, precision=6,
    )
    node_scale_value: FloatProperty(
        name="Node Scale",
        description="Wert fuer die Scale-Value-Node im Shader",
        default=0.01, min=0.000001, max=1000.0, precision=6,
    )
    mecaface_scale_value: FloatProperty(
        name="MecaFace Scale",
        description="Scale-Wert fuer den MecaFace Scale Patcher",
        default=0.01, min=0.000001, max=1000.0, precision=6,
    )
    mecaface_force_repatch: BoolProperty(
        name="Force Repatch",
        description="Ignoriert vorhandene Patch-Sperren auf Printed-NodeTrees",
        default=False,
    )


class MMUA_OT_PatchShaders(bpy.types.Operator):
    bl_idname = "mmua.patch_shaders"
    bl_label = "Shader patchen"
    bl_description = "Patcht MMUA-Shader aller ausgewaehlten Objekte"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.mmua_patcher
        sf = props.scale_factor
        selected = [o for o in context.selected_objects if o.type == "MESH"]
        if not selected:
            self.report({"WARNING"}, "Keine Mesh-Objekte ausgewaehlt.")
            return {"CANCELLED"}
        vb, vm, vs, vn = set(), set(), set(), set()
        log = [run_all_patches(o, sf, vb, vm, vs, vn) for o in selected]
        print("")
        print("===== DOCTOR ORCINUS – SHADER PATCHER =====")
        print("Scale Factor: {}".format(sf))
        for l in log: print(l)
        print("============================================")
        print("")
        self.report({"INFO"}, "{} Objekt(e) gepatcht.".format(len(selected)))
        return {"FINISHED"}


class DOCORCINUS_OT_SetNodeScale(bpy.types.Operator):
    bl_idname = "doctor_orcinus.set_node_scale"
    bl_label = "Node Scale setzen"
    bl_description = "Setzt den Wert der Scale-Value-Node im aktiven Material aller ausgewaehlten Objekte"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        value = context.scene.mmua_patcher.node_scale_value
        selected = [o for o in context.selected_objects if o.type == "MESH"]
        if not selected:
            self.report({"WARNING"}, "Keine Mesh-Objekte ausgewaehlt.")
            return {"CANCELLED"}
        hit, miss = 0, 0
        for obj in selected:
            mat = obj.active_material
            if not mat or not mat.use_nodes:
                miss += 1
                continue
            node = find_scale_node(mat.node_tree)
            if node:
                node.outputs[0].default_value = value
                hit += 1
            else:
                miss += 1
        self.report({"INFO"}, "Scale-Node gesetzt: {} Objekte. Nicht gefunden: {}.".format(hit, miss))
        return {"FINISHED"}

# ---------------------------------------------------------------------------
# PANELS (eingeklappbar via Sub-Panels)
# ---------------------------------------------------------------------------


class DOCORCINUS_OT_SelectMMUAObjects(bpy.types.Operator):
    bl_idname = "doctor_orcinus.select_mmua_objects"
    bl_label = "Select MMUA Objects"
    bl_description = "Waehlt alle Mesh-Objekte in der Szene aus, deren Material die Nodegruppe mmua_base_solid enthaelt"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected = select_mmua_objects(context)
        if not selected:
            self.report({"WARNING"}, "Keine MMUA-Objekte gefunden.")
            return {"CANCELLED"}
        self.report({"INFO"}, "{} MMUA-Objekt(e) ausgewaehlt.".format(len(selected)))
        return {"FINISHED"}

class DOCORCINUS_OT_MecaFaceScalePatch(bpy.types.Operator):
    bl_idname = "doctor_orcinus.mecaface_scale_patch"
    bl_label = "MecaFace Scale patchen"
    bl_description = "Patcht MecaFace.Material-NodeTrees global und nur einmal pro NodeTree"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        props = context.scene.mmua_patcher
        scale_value = props.mecaface_scale_value
        force_repatch = props.mecaface_force_repatch
        targets = gather_mecaface_material_trees()

        if not targets:
            self.report({"WARNING"}, "Keine passenden MecaFace-Materialien gefunden.")
            return {"CANCELLED"}

        patched = 0
        skipped = 0

        print("")
        print("===== DOCTOR ORCINUS – MECAFACE SCALE PATCHER =====")
        print("Scale Value: {}".format(scale_value))
        print("Force Repatch: {}".format(force_repatch))
        print("MecaFace.Material Trees: {}".format(len(targets)))

        for mat, mecaface_tree in targets:
            print("")
            print("Material: {} -> MecaFace.Material Tree: {}".format(mat.name, mecaface_tree.name))
            if mecaface_is_locked(mecaface_tree) and not force_repatch:
                prev_scale = mecaface_tree.get(MECAFACE_PATCH_SCALE_KEY, "?")
                print("[SKIP LOCKED] Bereits gepatcht mit Scale {}".format(prev_scale))
                skipped += 1
                continue

            for line in mecaface_patch_material_tree_once(mecaface_tree, scale_value):
                print(line)

            mecaface_store_patch_lock(mecaface_tree, scale_value)
            print("[LOCKED] {} mit Scale {}".format(mecaface_tree.name, scale_value))
            patched += 1

        print("")
        print("---------------------------------------------------")
        print("Gepatcht: {}".format(patched))
        print("Uebersprungen (locked): {}".format(skipped))
        print("===================================================")
        print("")

        self.report({"INFO"}, "MecaFace Scale Patcher: {} gepatcht, {} uebersprungen.".format(patched, skipped))
        return {"FINISHED"}


class DOCORCINUS_PT_main_panel(bpy.types.Panel):
    bl_label = "Doctor Orcinus LEGO Tweaks"
    bl_idname = "DOCORCINUS_PT_main_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Doctor Orcinus"

    def draw(self, context):
        pass


class DOCORCINUS_PT_organic_motion(bpy.types.Panel):
    bl_label = "Organic Motion"
    bl_idname = "DOCORCINUS_PT_organic_motion"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Doctor Orcinus"
    bl_parent_id = "DOCORCINUS_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        obj = context.active_object
        mode = context.mode

        cam_box = layout.box()
        cam_box.label(text="Camera", icon="CAMERA_DATA")
        if obj and obj.type == "CAMERA":
            cam_box.label(text=" {}".format(obj.name), icon="CHECKMARK")
        else:
            cam_box.label(text=" No camera selected", icon="INFO")
        s = scene.camera_noise_settings
        col = cam_box.column(align=True)
        draw_axis_row(col, "X", s.x)
        draw_axis_row(col, "Y", s.y)
        draw_axis_row(col, "Z", s.z)
        cam_box.separator(factor=0.5)
        row = cam_box.row(align=True)
        row.operator("camera.reset_noise_defaults", icon="LOOP_BACK", text="Reset")
        r = row.row()
        r.enabled = (obj is not None and obj.type == "CAMERA")
        r.operator("camera.add_noise_motion", icon="MOD_NOISE", text="Apply")

        bone_box = layout.box()
        bone_box.label(text="Pose Bones", icon="BONE_DATA")
        in_pose = (obj is not None and obj.type == "ARMATURE" and mode == "POSE")
        sel_bones = context.selected_pose_bones if in_pose else []
        if in_pose and sel_bones:
            bone_box.label(text=" {} bone(s) selected".format(len(sel_bones)), icon="CHECKMARK")
        elif in_pose:
            bone_box.label(text=" No bones selected", icon="INFO")
        else:
            bone_box.label(text=" Enter Pose Mode on Armature", icon="INFO")
        bs = scene.bone_noise_settings
        col2 = bone_box.column(align=True)
        draw_axis_row(col2, "X", bs.x)
        draw_axis_row(col2, "Y", bs.y)
        draw_axis_row(col2, "Z", bs.z)
        bone_box.separator(factor=0.5)
        row2 = bone_box.row(align=True)
        row2.operator("pose.reset_noise_defaults", icon="LOOP_BACK", text="Reset")
        r2 = row2.row()
        r2.enabled = (in_pose and len(sel_bones) > 0)
        r2.operator("pose.add_noise_motion", icon="MOD_NOISE", text="Apply")



# ---------------------------------------------------------------------------
# ANIMATION ON 2s – Properties, Helpers & Operators
# ---------------------------------------------------------------------------

class On2sSettings(PropertyGroup):
    step_size: IntProperty(
        name="Step Size",
        default=2,
        min=1,
        max=24,
        description="Hold each pose for this many frames",
    )
    include_camera_markers: BoolProperty(
        name="Respect Camera Switches",
        default=True,
        description="Restart stepping at camera-bound timeline markers so the switch frame is not skipped",
    )
    selected_bones_only: BoolProperty(
        name="Selected Bones Only",
        default=False,
        description="Only affect selected pose bones on the active armature",
    )
    clear_existing: BoolProperty(
        name="Replace Existing On2s",
        default=True,
        description="Remove previously created On2s stepped modifiers before applying",
    )


def get_camera_marker_frames(scene):
    frames = set()
    for marker in scene.timeline_markers:
        if marker.camera is not None:
            frames.add(int(marker.frame))
    return frames


def is_on2s_modifier(mod, label_prefix="On2s"):
    return mod.type == 'STEPPED' and (mod.name.startswith(label_prefix) or label_prefix in mod.name)


def remove_existing_stepped_modifiers(fcurve, label_prefix="On2s"):
    removed = 0
    for mod in list(fcurve.modifiers):
        if is_on2s_modifier(mod, label_prefix):
            fcurve.modifiers.remove(mod)
            removed += 1
    return removed


def add_segmented_stepped_modifiers(fcurve, scene, step_size=2, marker_frames=None, label_prefix="On2s"):
    start = int(scene.frame_start)
    end = int(scene.frame_end)
    marker_frames = sorted(f for f in (marker_frames or set()) if start <= f <= end)

    boundaries = [start]
    for mf in marker_frames:
        if mf not in boundaries:
            boundaries.append(mf)
    if end + 1 not in boundaries:
        boundaries.append(end + 1)
    boundaries = sorted(set(boundaries))

    created = 0
    for i in range(len(boundaries) - 1):
        seg_start = boundaries[i]
        seg_end_exclusive = boundaries[i + 1]
        if seg_start >= seg_end_exclusive:
            continue

        mod = fcurve.modifiers.new(type='STEPPED')
        mod.name = f"{label_prefix}_{seg_start}_{seg_end_exclusive-1}"
        mod.frame_step = float(step_size)
        mod.frame_offset = float((seg_start - start) % step_size)
        mod.use_frame_start = True
        mod.frame_start = float(seg_start)
        mod.use_frame_end = True
        mod.frame_end = float(seg_end_exclusive - 0.001)
        created += 1
    return created


def fcurve_matches_selected_bones(fcurve, selected_bone_names):
    if not selected_bone_names:
        return False
    dp = fcurve.data_path
    if not dp.startswith('pose.bones['):
        return False
    for bone_name in selected_bone_names:
        token = f'pose.bones["{bone_name}"]'
        if dp.startswith(token):
            return True
    return False


def process_action(action, scene, marker_frames, step_size, selected_bone_names=None, selected_bones_only=False, clear_existing=True):
    removed = 0
    created = 0
    touched = 0

    for fcurve in action.fcurves:
        if selected_bones_only and not fcurve_matches_selected_bones(fcurve, selected_bone_names):
            continue
        if clear_existing:
            removed += remove_existing_stepped_modifiers(fcurve)
        created += add_segmented_stepped_modifiers(fcurve, scene, step_size, marker_frames)
        touched += 1

    return touched, removed, created


def clear_on2s_from_action(action, selected_bone_names=None, selected_bones_only=False):
    touched = 0
    removed = 0
    for fcurve in action.fcurves:
        if selected_bones_only and not fcurve_matches_selected_bones(fcurve, selected_bone_names):
            continue
        count = remove_existing_stepped_modifiers(fcurve)
        if count > 0:
            touched += 1
            removed += count
    return touched, removed


class DOCORCINUS_OT_animation_on_2s(bpy.types.Operator):
    bl_idname = "doctor_orcinus.animation_on_2s"
    bl_label = "Apply Animation on 2s"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        scene = context.scene
        settings = scene.doctor_orcinus_on2s
        marker_frames = get_camera_marker_frames(scene) if settings.include_camera_markers else set()

        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        total_actions = 0
        total_fcurves = 0
        total_removed = 0
        total_created = 0
        processed_actions = set()

        armature = context.active_object if context.active_object and context.active_object.type == 'ARMATURE' else None
        selected_bone_names = {b.name for b in context.selected_pose_bones} if context.selected_pose_bones else set()

        print("")
        print("===== DOCTOR ORCINUS - ANIMATION ON 2s =====")
        print("Step Size: {}".format(settings.step_size))
        print("Respect Camera Switches: {}".format(settings.include_camera_markers))
        print("Camera Switch Frames: {}".format(sorted(marker_frames)))
        print("Selected Bones Only: {}".format(settings.selected_bones_only))

        for obj in selected_objects:
            if not obj.animation_data or not obj.animation_data.action:
                print("[{}] No action found.".format(obj.name))
                continue

            action = obj.animation_data.action
            action_key = action.as_pointer()
            if action_key in processed_actions:
                print("[{}] Action '{}' already processed, skipped.".format(obj.name, action.name))
                continue
            processed_actions.add(action_key)

            use_selected_bones_only = False
            bone_names_for_action = set()
            if settings.selected_bones_only and obj == armature and selected_bone_names:
                use_selected_bones_only = True
                bone_names_for_action = selected_bone_names

            touched, removed, created = process_action(
                action,
                scene,
                marker_frames,
                settings.step_size,
                bone_names_for_action,
                use_selected_bones_only,
                settings.clear_existing,
            )

            total_actions += 1
            total_fcurves += touched
            total_removed += removed
            total_created += created
            print("[{}] Action '{}': {} F-Curves, {} old modifiers removed, {} new modifiers created.".format(
                obj.name, action.name, touched, removed, created
            ))

        print("--------------------------------------------")
        print("Processed Actions: {}".format(total_actions))
        print("Affected F-Curves: {}".format(total_fcurves))
        print("Removed Modifiers: {}".format(total_removed))
        print("Created Modifiers: {}".format(total_created))
        print("============================================")
        print("")

        self.report({'INFO'}, "Animation on 2s applied. See console for details.")
        return {'FINISHED'}


class DOCORCINUS_OT_clear_animation_on_2s(bpy.types.Operator):
    bl_idname = "doctor_orcinus.clear_animation_on_2s"
    bl_label = "Remove Step Modifiers"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        settings = context.scene.doctor_orcinus_on2s
        selected_objects = context.selected_objects
        if not selected_objects:
            self.report({'WARNING'}, "No objects selected.")
            return {'CANCELLED'}

        total_actions = 0
        total_fcurves = 0
        total_removed = 0
        processed_actions = set()

        armature = context.active_object if context.active_object and context.active_object.type == 'ARMATURE' else None
        selected_bone_names = {b.name for b in context.selected_pose_bones} if context.selected_pose_bones else set()

        print("")
        print("===== DOCTOR ORCINUS - CLEAR ON 2s =====")
        print("Selected Bones Only: {}".format(settings.selected_bones_only))

        for obj in selected_objects:
            if not obj.animation_data or not obj.animation_data.action:
                print("[{}] No action found.".format(obj.name))
                continue

            action = obj.animation_data.action
            action_key = action.as_pointer()
            if action_key in processed_actions:
                print("[{}] Action '{}' already processed, skipped.".format(obj.name, action.name))
                continue
            processed_actions.add(action_key)

            use_selected_bones_only = False
            bone_names_for_action = set()
            if settings.selected_bones_only and obj == armature and selected_bone_names:
                use_selected_bones_only = True
                bone_names_for_action = selected_bone_names

            touched, removed = clear_on2s_from_action(
                action,
                bone_names_for_action,
                use_selected_bones_only,
            )

            total_actions += 1
            total_fcurves += touched
            total_removed += removed
            print("[{}] Action '{}': {} F-Curves bereinigt, {} Modifier entfernt.".format(
                obj.name, action.name, touched, removed
            ))

        print("----------------------------------------")
        print("Processed Actions: {}".format(total_actions))
        print("Affected F-Curves: {}".format(total_fcurves))
        print("Removed Modifiers: {}".format(total_removed))
        print("========================================")
        print("")

        self.report({'INFO'}, "Step modifiers removed. See console for details.")
        return {'FINISHED'}


class DOCORCINUS_PT_animation_on_2s(bpy.types.Panel):
    bl_label = "Animation on 2s"
    bl_idname = "DOCORCINUS_PT_animation_on_2s"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Doctor Orcinus"
    bl_parent_id = "DOCORCINUS_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        settings = context.scene.doctor_orcinus_on2s

        col = layout.column(align=True)
        col.prop(settings, "step_size")
        col.prop(settings, "include_camera_markers")
        col.prop(settings, "selected_bones_only")
        col.prop(settings, "clear_existing")
        layout.separator()
        op_col = layout.column()
        op_col.scale_y = 1.3
        op_col.operator("doctor_orcinus.animation_on_2s", icon='MOD_TIME')
        op_col.operator("doctor_orcinus.clear_animation_on_2s", icon='PANEL_CLOSE')


class DOCORCINUS_PT_delta_reset(bpy.types.Panel):
    bl_label = "Reset LEGO Delta Offset"
    bl_idname = "DOCORCINUS_PT_delta_reset"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Doctor Orcinus"
    bl_parent_id = "DOCORCINUS_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        sel = list(context.selected_objects)
        if sel:
            layout.label(text="{} Objekt(e) ausgewaehlt".format(len(sel)), icon="CHECKMARK")
        else:
            layout.label(text="Keine Objekte ausgewaehlt", icon="INFO")
        col = layout.column()
        col.scale_y = 1.3
        col.operator("doctor_orcinus.reset_lego_delta", icon="FILE_REFRESH")
        layout.label(text="Ziel: Delta Loc XYZ = 0, Delta Rot XYZ = 0")


class DOCORCINUS_PT_shader(bpy.types.Panel):
    bl_label = "Shader & Scale"
    bl_idname = "DOCORCINUS_PT_shader"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Doctor Orcinus"
    bl_parent_id = "DOCORCINUS_PT_main_panel"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        props = context.scene.mmua_patcher
        sel = [o for o in context.selected_objects if o.type == "MESH"]

        # --- Node Scale Setter ---
        scale_box = layout.box()
        scale_box.label(text="Node Scale Setter", icon="NODE")
        scale_box.label(text="Wert fuer Scale-Node im Shader:")
        scale_box.prop(props, "node_scale_value", text="")
        col_s = scale_box.column()
        col_s.scale_y = 1.3
        col_s.operator("doctor_orcinus.set_node_scale", icon="DRIVER_TRANSFORM")

        layout.separator()

        # --- MecaFace Scale Patcher ---
        mecaface_box = layout.box()
        mecaface_box.label(text="MecaFace Scale Patcher", icon="SHADERFX")
        mecaface_box.label(text="Scale Value:")
        mecaface_box.prop(props, "mecaface_scale_value", text="")
        mecaface_box.prop(props, "mecaface_force_repatch")
        col_mf = mecaface_box.column()
        col_mf.scale_y = 1.3
        col_mf.operator("doctor_orcinus.mecaface_scale_patch", icon="MODIFIER")

        layout.separator()

        # --- Shader Patcher (MMUA) ---
        patch_box = layout.box()
        patch_box.label(text="Shader Patcher (MMUA)", icon="SHADERFX")
        patch_box.label(text="Scale Factor:")
        patch_box.prop(props, "scale_factor", text="")
        patch_box.separator()

        col_p = patch_box.column(align=True)
        col_p.scale_y = 1.3
        col_p.operator("doctor_orcinus.select_mmua_objects", icon="RESTRICT_SELECT_OFF", text="Select MMUA Objects")
        col_p.operator("mmua.patch_shaders", icon="SHADERFX")

        patch_box.separator()

        if sel:
            patch_box.label(text="{} Objekt(e) ausgewaehlt:".format(len(sel)), icon="OBJECT_DATA")
            box = patch_box.box()
            for o in sel[:10]:
                box.label(text=o.name, icon="MESH_DATA")
            if len(sel) > 10:
                box.label(text="... und {} weitere".format(len(sel) - 10))
        else:
            patch_box.label(text="Keine Mesh-Objekte ausgewaehlt.", icon="ERROR")


def select_mmua_objects(context):
    selected = []
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        found = False
        for mat in obj.data.materials:
            if not mat or not mat.use_nodes or not mat.node_tree:
                continue
            for node in mat.node_tree.nodes:
                if node.bl_idname == "ShaderNodeGroup" and node.node_tree:
                    n = node.node_tree.name.lower()
                    if n == "mmua_base_solid" or n.startswith("mmua_base_solid."):
                        found = True
                        break
            if found:
                break
        if found:
            selected.append(obj)
    for obj in context.selected_objects:
        obj.select_set(False)
    for obj in selected:
        obj.select_set(True)
    if selected:
        context.view_layer.objects.active = selected[0]
    return selected

# ---------------------------------------------------------------------------
# REGISTRATION
# ---------------------------------------------------------------------------

classes = (
    AxisNoiseSettings,
    CameraNoiseSettings,
    BoneNoiseSettings,
    CAMERA_OT_add_noise_motion,
    CAMERA_OT_reset_noise_defaults,
    BONE_OT_add_noise_motion,
    BONE_OT_reset_noise_defaults,
    On2sSettings,
    DOCORCINUS_OT_animation_on_2s,
    DOCORCINUS_OT_clear_animation_on_2s,
    DOCORCINUS_OT_reset_lego_delta,
    MMUAPatcherProperties,
    MMUA_OT_PatchShaders,
    DOCORCINUS_OT_SetNodeScale,
    DOCORCINUS_OT_MecaFaceScalePatch,
    DOCORCINUS_PT_main_panel,
    DOCORCINUS_PT_organic_motion,
    DOCORCINUS_PT_animation_on_2s,
    DOCORCINUS_PT_delta_reset,
    DOCORCINUS_PT_shader,
    DOCORCINUS_OT_SelectMMUAObjects,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.camera_noise_settings = PointerProperty(type=CameraNoiseSettings)
    bpy.types.Scene.bone_noise_settings = PointerProperty(type=BoneNoiseSettings)
    bpy.types.Scene.doctor_orcinus_on2s = PointerProperty(type=On2sSettings)
    bpy.types.Scene.mmua_patcher = bpy.props.PointerProperty(type=MMUAPatcherProperties)


def unregister():
    del bpy.types.Scene.mmua_patcher
    del bpy.types.Scene.doctor_orcinus_on2s
    del bpy.types.Scene.bone_noise_settings
    del bpy.types.Scene.camera_noise_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
