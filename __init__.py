bl_info = {
    "name": "Gear Up",
    "author": "Daniel Hong",
    "version": (0, 1, 0),
    "blender": (5, 0, 0),
    "location": "View3D > Add > Mesh",
    "description": "Adds a customizable gear",
    "category": "Add Mesh",
}

import bpy, os, bmesh
import bpy.utils.previews
from math import tau, cos, sin

preview_collections = {}


# Operator to add the gear (currently just a cylinder)
class MESH_OT_add_gear(bpy.types.Operator):
    bl_idname = "mesh.add_gear"
    bl_label = "Add Gear"
    bl_description = "Add a gear"
    bl_options = {'REGISTER', 'UNDO'}

    # Basic properties (you can expand later)
    outer_radius: bpy.props.FloatProperty(
        name="Outer Radius",
        default=1.0,
        min=0.1
    )

    inner_radius: bpy.props.FloatProperty(
        name="Inner Radius",
        default=0.5,
        min=0.0
    )

    depth: bpy.props.FloatProperty(
        name="Depth",
        default=0.5,
        min=0.1
    )
    
    teeth: bpy.props.IntProperty(
        name="Teeth",
        default=12,
        min=3
    )

    tooth_depth: bpy.props.FloatProperty(
        name="Tooth Depth",
        default=0.2,
        min=0.0
    )

    def execute(self, context):

        # Validate input
        if self.inner_radius >= self.outer_radius:
            self.report({'ERROR'}, "Inner radius must be smaller than outer radius")
            return {'CANCELLED'}

        if self.teeth < 3:
            self.report({'ERROR'}, "Teeth must be at least 3")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("Gear")
        obj = bpy.data.objects.new("Gear", mesh)
        context.collection.objects.link(obj)
        context.view_layer.objects.active = obj

        bm = bmesh.new()

        half_depth = self.depth / 2.0
        segments = self.teeth * 2  # tooth tip + valley

        verts_top_outer = []
        verts_bottom_outer = []
        verts_top_inner = []
        verts_bottom_inner = []

        root_radius = self.outer_radius - self.tooth_depth

        # --- Create vertices ---
        for i in range(segments):
            angle = i * tau / segments
            cos_a = cos(angle)
            sin_a = sin(angle)

            # Alternate between tooth tip and root
            if i % 2 == 0:
                r = self.outer_radius
            else:
                r = root_radius

            # Outer verts (with teeth)
            verts_top_outer.append(
                bm.verts.new((r * cos_a, r * sin_a, half_depth))
            )
            verts_bottom_outer.append(
                bm.verts.new((r * cos_a, r * sin_a, -half_depth))
            )

        # Inner ring stays smooth
        for i in range(segments):
            angle = i * tau / segments
            cos_a = cos(angle)
            sin_a = sin(angle)

            verts_top_inner.append(
                bm.verts.new((self.inner_radius * cos_a, self.inner_radius * sin_a, half_depth))
            )
            verts_bottom_inner.append(
                bm.verts.new((self.inner_radius * cos_a, self.inner_radius * sin_a, -half_depth))
            )

        bm.verts.ensure_lookup_table()

        # --- Create faces ---
        for i in range(segments):
            next_i = (i + 1) % segments

            # Outer wall (tooth profile)
            bm.faces.new((
                verts_bottom_outer[i],
                verts_bottom_outer[next_i],
                verts_top_outer[next_i],
                verts_top_outer[i],
            ))

            # Inner wall (flip normals)
            bm.faces.new((
                verts_bottom_inner[next_i],
                verts_bottom_inner[i],
                verts_top_inner[i],
                verts_top_inner[next_i],
            ))

            # Top face ring
            bm.faces.new((
                verts_top_outer[i],
                verts_top_outer[next_i],
                verts_top_inner[next_i],
                verts_top_inner[i],
            ))

            # Bottom face ring
            bm.faces.new((
                verts_bottom_outer[next_i],
                verts_bottom_outer[i],
                verts_bottom_inner[i],
                verts_bottom_inner[next_i],
            ))

        # Finalize mesh
        bm.to_mesh(mesh)
        bm.free()

        return {'FINISHED'}


# Add to the Add Mesh menu
def menu_func(self, context):
    pcoll = preview_collections["main"]
    icon_id = pcoll["gear_icon"].icon_id

    self.layout.operator(
        MESH_OT_add_gear.bl_idname,
        text="Gear",
        icon_value=icon_id
    )


# Register / Unregister
def register():
    import bpy.utils.previews

    pcoll = bpy.utils.previews.new()
    addon_dir = os.path.dirname(__file__)
    icon_path = os.path.join(addon_dir, "gear_icon.png")

    pcoll.load("gear_icon", icon_path, 'IMAGE')
    preview_collections["main"] = pcoll

    bpy.utils.register_class(MESH_OT_add_gear)
    bpy.types.VIEW3D_MT_mesh_add.append(menu_func)


def unregister():
    bpy.types.VIEW3D_MT_mesh_add.remove(menu_func)
    bpy.utils.unregister_class(MESH_OT_add_gear)

    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()


if __name__ == "__main__":
    unregister()
    register()