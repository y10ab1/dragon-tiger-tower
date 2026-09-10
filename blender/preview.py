"""Daylight, preview-only views of the generated GLBs; never exports assets."""
import math
import os

import bpy
from mathutils import Vector


def look_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


d = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "game", "assets", "models")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=os.path.join(d, "island.glb"))
bpy.ops.import_scene.gltf(filepath=os.path.join(d, "bridge.glb"))
# Bridge glTF local -> island south edge (Blender Z-up after import).
for obj in bpy.context.selected_objects:
    if obj.parent is None:
        obj.location.y -= 10.5

# Godot import hints do not hide collision proxies in Blender.
visible = []
for obj in bpy.context.scene.objects:
    ancestor = obj
    while ancestor is not None:
        if "-colonly" in ancestor.name:
            obj.hide_render = True
            break
        ancestor = ancestor.parent
    if obj.type == "MESH" and not obj.hide_render:
        visible.append(obj)
bpy.context.view_layer.update()


def bounds(objects):
    return [obj.matrix_world @ Vector(corner)
            for obj in objects for corner in obj.bound_box]


# Lake and lighting exist only in this temporary render scene.
bpy.ops.mesh.primitive_plane_add(size=2000, location=(0, -15, -0.65))
lake = bpy.context.object
lake.name = "PreviewLake"
water = bpy.data.materials.new("PreviewLakeWater")
water.use_nodes = True
shader = water.node_tree.nodes["Principled BSDF"]
shader.inputs["Base Color"].default_value = (0.075, 0.23, 0.20, 1)
shader.inputs["Roughness"].default_value = 0.24
shader.inputs["Metallic"].default_value = 0.15
lake.data.materials.append(water)

sc = bpy.context.scene
sc.world = bpy.data.worlds.new("PreviewDaylight")
sc.world.use_nodes = True
background = sc.world.node_tree.nodes["Background"]
background.inputs["Color"].default_value = (0.55, 0.70, 0.85, 1)
background.inputs["Strength"].default_value = 0.65

bpy.ops.object.light_add(type="SUN", location=(-30, -40, 55))
sun = bpy.context.object
sun.data.energy = 2.5
sun.data.angle = math.radians(12)
look_at(sun, (0, 0, 0))
bpy.ops.object.light_add(type="AREA", location=(18, -28, 22))
fill = bpy.context.object
fill.data.energy = 2200
fill.data.shape = "DISK"
fill.data.size = 25
look_at(fill, (0, -4, 6))

bpy.ops.object.camera_add()
cam = bpy.context.object
cam.data.type = "ORTHO"
cam.data.clip_end = 500
sc.camera = cam
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 32
sc.render.resolution_x = 1440
sc.render.resolution_y = 1000
sc.render.resolution_percentage = 100
sc.render.image_settings.file_format = "PNG"
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"


def render_view(name, points, offset):
    lower = Vector(tuple(min(p[i] for p in points) for i in range(3)))
    upper = Vector(tuple(max(p[i] for p in points) for i in range(3)))
    target = (lower + upper) / 2
    cam.location = target + Vector(offset)
    look_at(cam, target)
    rotation = cam.rotation_euler.to_quaternion()
    projected = [rotation.inverted() @ (p - target) for p in points]
    xmin, xmax = min(p.x for p in projected), max(p.x for p in projected)
    ymin, ymax = min(p.y for p in projected), max(p.y for p in projected)
    # Center in camera space and fit both axes, with margin for horns and spires.
    cam.location += rotation @ Vector(((xmin + xmax) / 2, (ymin + ymax) / 2, 0))
    aspect = sc.render.resolution_x / sc.render.resolution_y
    cam.data.ortho_scale = max(xmax - xmin, (ymax - ymin) * aspect) * 1.16
    sc.render.filepath = f"/tmp/opencode/preview_{name}.png"
    bpy.ops.render.render(write_still=True)


far_points = bounds(visible) + [Vector((-8, 3, 29)), Vector((8, 3, 29))]
render_view("far", far_points, (18, -85, 40))
statues = [obj for obj in visible if obj.name.startswith(("DragonStatue", "TigerStatue"))]
render_view("close", bounds(statues), (1, -35, 10))
for name, prefix, offset in (("dragon", "DragonStatue", (-7, -20, 7)),
                             ("tiger", "TigerStatue", (7, -20, 7))):
    render_view(name, bounds([obj for obj in statues if obj.name.startswith(prefix)]), offset)
print("PREVIEW DONE")
