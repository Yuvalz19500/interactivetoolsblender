import bpy
from ..utils import itools as itools
from .. utils import dictionaries as dic
from .. utils.user_prefs import get_quickhplp_hp_suffix, get_quickhplp_lp_suffix, get_enable_wireshaded_cs


class TransformModeCycle(bpy.types.Operator):
    bl_idname = "mesh.transform_mode_cycle"
    bl_label = "Transform Mode Cycle"
    bl_description = "Cycle between Move/Rotate/Scale modes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        areas = bpy.context.workspace.screens[0].areas

        for area in areas:
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # Make active tool is set to select
                    override = bpy.context.copy()
                    override["space_data"] = area.spaces[0]
                    override["area"] = area
                    bpy.ops.wm.tool_set_by_id(override, name="builtin.select_box")

                    if space.show_gizmo_object_translate:
                        space.show_gizmo_object_translate = False
                        space.show_gizmo_object_rotate = True

                    elif space.show_gizmo_object_rotate:
                        space.show_gizmo_object_rotate = False
                        space.show_gizmo_object_scale = True

                    elif space.show_gizmo_object_scale:
                        space.show_gizmo_object_scale = False
                        space.show_gizmo_object_translate = True

                    else:
                        space.show_gizmo_object_translate = True

        return{'FINISHED'}


class TransformOrientationCycle(bpy.types.Operator):
    bl_idname = "mesh.transform_orientation_cycle"
    bl_label = "Transform Orientation Cycle"
    bl_description = "Cycles trough transform orientation modes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        space = bpy.context.scene.transform_orientation_slots[0].type

        if space == 'GLOBAL':
            new_space = 'LOCAL'

        elif space == 'LOCAL':
            new_space = 'NORMAL'

        elif space == 'NORMAL':
            new_space = 'GIMBAL'

        elif space == 'GIMBAL':
            new_space = 'VIEW'

        elif space == 'VIEW':
            new_space = 'CURSOR'

        elif space == 'CURSOR':
            new_space = 'GLOBAL'

        bpy.context.scene.transform_orientation_slots[0].type = new_space

        return {'FINISHED'}


class CSBevel(bpy.types.Operator):
    bl_idname = "mesh.context_sensitive_bevel"
    bl_label = "Context Sensistive Bevel"
    bl_description = "Context Sensitive Bevels and Inset"
    bl_options = {'REGISTER', 'UNDO'}

    def cs_bevel(self):

        mode = itools.get_mode()

        if mode == 'VERT':
            bpy.ops.mesh.bevel('INVOKE_DEFAULT', vertex_only=True)

        if mode == 'EDGE':
            bpy.ops.mesh.bevel('INVOKE_DEFAULT', vertex_only=False)

        if mode == 'FACE':
            bpy.ops.mesh.inset('INVOKE_DEFAULT')

    def execute(self, context):
        self.cs_bevel()
        return{'FINISHED'}


class ContextSensitiveSlide(bpy.types.Operator):
    bl_idname = "mesh.context_sensitive_slide"
    bl_label = "Context Sensitive Slide"
    bl_description = "Slide vert or edge based on selection"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        bm = itools.get_bmesh()
        mode = itools.get_mode()

        if mode == 'VERT':
            bpy.ops.transform.vert_slide('INVOKE_DEFAULT')

        elif mode == 'EDGE':
            bpy.ops.transform.edge_slide('INVOKE_DEFAULT')

        return{'FINISHED'}


class TargetWeldToggle(bpy.types.Operator):
    bl_idname = "mesh.target_weld_toggle"
    bl_label = "Target Weld On / Off"
    bl_description = "Toggles snap to vertex and automerge editing on and off"
    bl_options = {'REGISTER', 'UNDO'}

    def toggle_target_weld(self, context):
        if context.scene.tool_settings.use_mesh_automerge and bpy.context.scene.tool_settings.use_snap:
            context.scene.tool_settings.use_mesh_automerge = False
            bpy.context.scene.tool_settings.use_snap = False
        else:
            context.scene.tool_settings.snap_elements |= {'VERTEX'}
            context.scene.tool_settings.use_mesh_automerge = True
            bpy.context.scene.tool_settings.use_snap = True

    def execute(self, context):
        self.toggle_target_weld(context)
        return{'FINISHED'}


class QuickModifierToggle(bpy.types.Operator):
    bl_idname = "mesh.modifier_toggle"
    bl_label = "Modifiers On / Off"
    bl_description = "Toggles the modifiers on and off for selected objects"
    bl_options = {'REGISTER', 'UNDO'}

    def modifier_toggle(self, context):
        mode = itools.get_mode()

        if mode in ['VERT', 'EDGE', 'FACE']:
            itools.set_mode('OBJECT')

        selected = itools.get_selected()

        for obj in selected:
            if all(modifier.show_in_editmode and modifier.show_viewport for modifier in obj.modifiers):
                for modifier in obj.modifiers:
                    modifier.show_in_editmode = False
                    modifier.show_viewport = False

            else:
                for modifier in obj.modifiers:
                    modifier.show_in_editmode = True
                    modifier.show_viewport = True

        if mode in ['VERT', 'EDGE', 'FACE']:
            itools.set_mode(mode)

    def execute(self, context):
        self.modifier_toggle(context)
        return {'FINISHED'}


class QuickWireToggle(bpy.types.Operator):
    bl_idname = "mesh.wire_toggle"
    bl_label = "Wireframe On / Off"
    bl_description = "Toggles wire mode on and off on all objects"
    bl_options = {'REGISTER', 'UNDO'}

    def wire_toggle(self, context):
        if context.space_data.overlay.show_wireframes:
            context.space_data.overlay.show_wireframes = False
        else:
            context.space_data.overlay.show_wireframes = True

    def execute(self, context):
        self.wire_toggle(context)
        return{'FINISHED'}


class QuickTransformOrientation(bpy.types.Operator):
    bl_idname = "mesh.quick_transform_orientation"
    bl_label = "Quick Transform Orientation"
    bl_description = "Sets up a transform orientation from selected"
    bl_options = {'REGISTER', 'UNDO'}

    def make_orientation(self, context):
        space = bpy.context.scene.transform_orientation_slots[0].type
        selection = itools.get_selected()

        if space != 'Custom':
            dic.write("stored_transform_orientation", space)
            bpy.ops.transform.create_orientation(name="Custom", use=True, overwrite=True)

        else:
            if len(selection) < 1:
                new_space = dic.read("stored_transform_orientation")
                bpy.context.scene.transform_orientation_slots[0].type = new_space
            else:
                bpy.ops.transform.create_orientation(name="Custom", use=True, overwrite=True)

    def execute(self, context):
        self.make_orientation(context)
        return{'FINISHED'}


class WireShadedToggle(bpy.types.Operator):
    bl_idname = "mesh.wire_shaded_toggle"
    bl_label = "Wireframe / Shaded Toggle"
    bl_description = "Toggles between wireframe and shaded mode"
    bl_options = {'REGISTER', 'UNDO'}

    def wire_shaded_toggle(self, context):
        selection = itools.get_selected('OBJECT')

        if len(selection) > 0 and get_enable_wireshaded_cs():
            if all(obj.display_type == 'WIRE' for obj in selection):
                for obj in selection:
                    obj.display_type = 'TEXTURED'

            else:
                for obj in selection:
                    obj.display_type = 'WIRE'

        else:
            areas = context.workspace.screens[0].areas
            for area in areas:
                for space in area.spaces:
                    if space.type == 'VIEW_3D':
                        if space.shading.type == 'WIREFRAME':
                            space.shading.type = dic.read("shading_mode")
                        else:
                            dic.write("shading_mode", space.shading.type)
                            space.shading.type = 'WIREFRAME'

    def execute(self, context):
        self.wire_shaded_toggle(context)
        return{'FINISHED'}


class FlexiBezierToolsCreate(bpy.types.Operator):
    bl_idname = "curve.flexitool_create"
    bl_label = "Flexi Bezier Tools Create"
    bl_description = "Executes Flexi Bezier Tools Create"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                bpy.ops.wm.tool_set_by_id(name='flexi_bezier.draw_tool')
        return{'FINISHED'}

class QuickHpLpNamer(bpy.types.Operator):
    bl_idname = "mesh.quick_hplp_namer"
    bl_label = "Quick HP Lp Namer"
    bl_description = "Helps with naming the hp and lp for name matching baking"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selection = []
        selection = itools.get_selected()
        lp_suffix = get_quickhplp_lp_suffix()
        hp_suffix = get_quickhplp_hp_suffix()

        lp = [obj for obj in selection if obj.name.endswith(lp_suffix)]
        if len(lp) != 1:
            polycount_list = [len(obj.data.polygons) for obj in selection]
            lowest_index = polycount_list.index(min(polycount_list))
            lp = selection[lowest_index]
            lp.name = lp.name + lp_suffix

        elif lp[0].name.endswith(lp_suffix):
            lp = lp[0]

        for obj in selection:
            if obj is not lp:
                obj.name = lp.name[:-len(lp_suffix)] + hp_suffix

        return{'FINISHED'}
