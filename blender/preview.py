"""Quick preview render of the generated GLBs."""
import bpy
import math
import os
import sys

d = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 "..", "game", "assets", "models")
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

bpy.ops.import_scene.gltf(filepath=os.path.join(d, "island.glb"))
bpy.ops.import_scene.gltf(filepath=os.path.join(d, "bridge.glb"))
# bridge glTF local -> place at island south edge (blender z-up after import)
for obj in bpy.context.selected_objects:
    if obj.parent is None:
        obj.location.y -= 10.5

# ghost + talisman for scale check
bpy.ops.import_scene.gltf(filepath=os.path.join(d, "ghost.glb"))
for obj in bpy.context.selected_objects:
    if obj.parent is None:
        obj.location = (0, -20, 0)

# sun + camera
bpy.ops.object.light_add(type="SUN", location=(30, -40, 50))
bpy.context.active_object.data.energy = 3.0
bpy.context.active_object.rotation_euler = (math.radians(50),
                                            math.radians(10),
                                            math.radians(30))
bpy.ops.object.camera_add(location=(38, -58, 26),
                          rotation=(math.radians(72), 0, math.radians(33)))
bpy.context.scene.camera = bpy.context.active_object

sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE"
sc.render.resolution_x = 1280
sc.render.resolution_y = 720
sc.render.filepath = "/tmp/opencode/preview_far.png"
bpy.ops.render.render(write_still=True)

# close-up of the statues
cam = bpy.context.scene.camera
cam.location = (6, -22, 5)
cam.rotation_euler = (math.radians(85), 0, math.radians(15))
sc.render.filepath = "/tmp/opencode/preview_close.png"
bpy.ops.render.render(write_still=True)
print("PREVIEW DONE")
