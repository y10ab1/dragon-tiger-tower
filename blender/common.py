"""Shared helpers for procedural asset generation (Blender 5.x / bpy)."""
import bpy
import math


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for block_list in (bpy.data.meshes, bpy.data.materials, bpy.data.curves):
        for block in list(block_list):
            if block.users == 0:
                block_list.remove(block)


_MAT_CACHE = {}


def mat(name, color, rough=0.8, metal=0.0, emission=None, emission_strength=2.0):
    """Create (or fetch) a simple principled material."""
    if name in _MAT_CACHE:
        return _MAT_CACHE[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    _MAT_CACHE[name] = m
    return m


def set_mat(obj, material):
    obj.data.materials.clear()
    obj.data.materials.append(material)


def box(name, size, loc, material=None, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0], size[1], size[2])
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        set_mat(o, material)
    return o


def cyl(name, radius, depth, loc, material=None, verts=16, rot=(0, 0, 0),
        radius2=None):
    if radius2 is not None:
        bpy.ops.mesh.primitive_cone_add(
            vertices=verts, radius1=radius, radius2=radius2, depth=depth,
            location=loc, rotation=rot)
    else:
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=verts, radius=radius, depth=depth, location=loc,
            rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if material:
        set_mat(o, material)
    return o


def cone(name, radius, depth, loc, material=None, verts=8, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(
        vertices=verts, radius1=radius, radius2=0, depth=depth,
        location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    if material:
        set_mat(o, material)
    return o


def sphere(name, radius, loc, material=None, segs=16, rings=8, scale=None):
    bpy.ops.mesh.primitive_uv_sphere_add(
        radius=radius, location=loc, segments=segs, ring_count=rings)
    o = bpy.context.active_object
    o.name = name
    if scale:
        o.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if material:
        set_mat(o, material)
    return o


def join(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    joined = bpy.context.active_object
    joined.name = name
    return joined


def export_glb(filepath):
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.gltf(
        filepath=filepath,
        export_format="GLB",
        export_apply=True,
    )
    print("EXPORTED:", filepath)


# ---- palette ----
def palette():
    return {
        "wall":      mat("wall", (0.88, 0.62, 0.22), rough=0.85),
        "wall_in":   mat("wall_in", (0.45, 0.40, 0.34), rough=0.95),
        "red":       mat("red_col", (0.65, 0.035, 0.025), rough=0.55),
        "roof":      mat("roof", (0.78, 0.29, 0.055), rough=0.42),
        "tile_light": mat("tile_light", (0.95, 0.49, 0.12), rough=0.4),
        "roof_dk":   mat("roof_dk", (0.30, 0.115, 0.035), rough=0.65),
        "jade":      mat("jade", (0.045, 0.28, 0.18), rough=0.45),
        "blue":      mat("blue", (0.025, 0.19, 0.4), rough=0.45),
        "stone":     mat("stone", (0.43, 0.48, 0.43), rough=0.95),
        "stone_dk":  mat("stone_dk", (0.23, 0.29, 0.25), rough=0.95),
        "gold":      mat("gold", (0.8, 0.6, 0.15), rough=0.35, metal=0.8),
        "dragon":    mat("dragon", (0.12, 0.45, 0.28), rough=0.6),
        "dragon_belly": mat("dragon_belly", (0.85, 0.75, 0.4), rough=0.7),
        "tiger":     mat("tiger", (0.8, 0.45, 0.1), rough=0.7),
        "tiger_st":  mat("tiger_st", (0.12, 0.10, 0.08), rough=0.8),
        "white":     mat("white", (0.9, 0.88, 0.8), rough=0.8),
        "mouth":     mat("mouth", (0.3, 0.05, 0.05), rough=0.9),
        "eye":       mat("eye", (0.05, 0.05, 0.05), rough=0.3,
                         emission=(1.0, 0.25, 0.05), emission_strength=3.0),
        "wood":      mat("wood", (0.35, 0.2, 0.1), rough=0.85),
        "wood_dk":   mat("wood_dk", (0.22, 0.12, 0.06), rough=0.9),
        "lantern":   mat("lantern", (0.9, 0.15, 0.08), rough=0.5,
                         emission=(1.0, 0.35, 0.1), emission_strength=4.0),
    }


def octagon_ring(cx, cy, radius, offset_angle=math.pi / 8):
    """8 corner positions + segment angles of an octagon."""
    pts = []
    for i in range(8):
        a = offset_angle + i * math.pi / 4
        pts.append((cx + radius * math.cos(a), cy + radius * math.sin(a), a))
    return pts
