"""Generate the nine-turn bridge + shore pavilion.
Bridge starts at (0,0) (island side) and zigzags towards -Y (the shore).

Run:  blender -b -P gen_bridge.py
"""
import math
import os
import sys

import bpy

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (clear_scene, palette, box, cyl, sphere, join, export_glb)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "game", "assets", "models", "bridge.glb")

P = None
DECK_W = 2.8
RAIL_H = 1.05

# zigzag path vertices (x, y)
PATH = [(0, 0), (0, -6), (4, -6), (4, -13), (-2.5, -13), (-2.5, -20),
        (3, -20), (3, -27), (0, -27), (0, -33)]


def segment(parts, rails, x0, y0, x1, y1):
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy)
    ang = math.atan2(dy, dx)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    # deck
    parts.append(box("deck", (L + DECK_W, DECK_W, 0.3), (cx, cy, -0.15),
                     P["stone"], rot=(0, 0, ang)))
    # side kerbs
    for s in (-1, 1):
        ox = -s * math.sin(ang) * (DECK_W / 2 - 0.1)
        oy = s * math.cos(ang) * (DECK_W / 2 - 0.1)
        rails.append(box("kerb", (L - 2.6, 0.2, 0.25),
                         (cx + ox, cy + oy, 0.12), P["stone_dk"],
                         rot=(0, 0, ang)))
        # Stone balustrades stay inside the kerb and stop before turn overlaps.
        span = L - 2.6
        rails.append(box("railCap", (span, 0.2, 0.12),
                         (cx + ox, cy + oy, RAIL_H), P["stone"],
                         rot=(0, 0, ang)))
        n_posts = max(1, math.ceil(span / 1.5))
        spacing = (span - 0.2) / n_posts
        for p in range(n_posts + 1):
            along = (p / n_posts - 0.5) * (span - 0.2)
            px = cx + along * math.cos(ang) + ox
            py = cy + along * math.sin(ang) + oy
            rails.append(box("stonePost", (0.18, 0.18, RAIL_H),
                             (px, py, RAIL_H / 2), P["stone"],
                             rot=(0, 0, ang)))
            rails.append(box("postCap", (0.2, 0.2, 0.08),
                             (px, py, RAIL_H + 0.02), P["stone"],
                             rot=(0, 0, ang)))
            if p == n_posts:
                continue
            mx = px + spacing * 0.5 * math.cos(ang)
            my = py + spacing * 0.5 * math.sin(ang)
            # Thin inset field leaves a real recess on both faces of the frame.
            rails.append(box("recessedPanel", (spacing - 0.18, 0.09, 0.58),
                             (mx, my, 0.6), P["stone_dk"], rot=(0, 0, ang)))
            rails.append(box("panelField", (spacing - 0.27, 0.11, 0.43),
                             (mx, my, 0.6), P["stone"], rot=(0, 0, ang)))
            for z in (0.3, 0.91):
                rails.append(box("panelMoulding", (spacing, 0.18, 0.1),
                                 (mx, my, z), P["stone"], rot=(0, 0, ang)))
    # piles into the water
    for t in (-0.3, 0.3):
        px = cx + t * L * math.cos(ang)
        py = cy + t * L * math.sin(ang)
        for s in (-1, 1):
            ox = -s * math.sin(ang) * (DECK_W / 2 - 0.25)
            oy = s * math.cos(ang) * (DECK_W / 2 - 0.25)
            parts.append(cyl("pile", 0.22, 2.6, (px + ox, py + oy, -1.4),
                             P["stone_dk"], verts=8))


def corner_lanterns(deco):
    for j, (x, y) in enumerate(PATH[1:-1]):
        deco.append(cyl(f"cpost{j}", 0.1, 2.6, (x, y, 1.3), P["wood_dk"],
                        verts=8))
        deco.append(sphere(f"clamp{j}", 0.32, (x, y, 2.35), P["lantern"],
                           segs=12, rings=8, scale=(1, 1, 1.3)))
        print(f"BRIDGE_LANTERN local=({x}, 2.35, {-y})")


def pavilion(cx, cy):
    parts, deco = [], []
    parts.append(box("pfloor", (9, 9, 0.5), (cx, cy, -0.25), P["stone"]))
    parts.append(box("pstep", (3.2, 1.4, 0.24), (cx, cy + 5.0, -0.32),
                     P["stone"]))
    for sx in (-1, 1):
        for sy in (-1, 1):
            parts.append(cyl("pcol", 0.28, 3.4,
                             (cx + sx * 3.4, cy + sy * 3.4, 1.7), P["red"],
                             verts=10))
    # Square hip roof: concave slopes, lifted corners, and a pale tiled lip.
    profile = [(0.1, 5.45), (0.9, 5.12), (2.0, 4.48), (3.1, 3.95),
               (4.1, 3.68), (4.7, 3.72), (4.8, 3.76)]
    vertices, faces, materials = [], [], []
    ring_size = 48
    for half_w, z in profile:
        for side in range(4):
            angle = side * math.pi / 2
            for j in range(12):
                t = -1 + j / 6
                x, y = half_w, half_w * t
                lift = 0.48 * abs(t) ** 6 * (half_w / 4.8) ** 4
                vertices.append((cx + x * math.cos(angle) - y * math.sin(angle),
                                 cy + x * math.sin(angle) + y * math.cos(angle),
                                 z + lift))
    top_count = len(vertices)
    vertices += [(x, y, z - 0.12) for x, y, z in vertices]
    faces.extend((tuple(range(ring_size)),
                  tuple(top_count + j for j in reversed(range(ring_size)))))
    materials.extend((0, 2))
    for ring in range(len(profile) - 1):
        for j in range(ring_size):
            a = ring * ring_size + j
            b = ring * ring_size + (j + 1) % ring_size
            face = (a, a + ring_size, b + ring_size, b)
            faces.append(face)
            materials.append(1 if ring == len(profile) - 2 else 0)
            faces.append(tuple(v + top_count for v in reversed(face)))
            materials.append(2)
    for j in range(ring_size):
        a = top_count - ring_size + j
        b = top_count - ring_size + (j + 1) % ring_size
        faces.append((a, a + top_count, b + top_count, b))
        materials.append(1)
    mesh = bpy.data.meshes.new("pavilionCurvedRoof")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    roof = bpy.data.objects.new("pavilionCurvedRoof", mesh)
    bpy.context.collection.objects.link(roof)
    for material in (P["roof"], P["tile_light"], P["roof_dk"]):
        mesh.materials.append(material)
    for face, material_index in zip(mesh.polygons, materials):
        face.material_index = material_index
    deco.append(roof)
    deco.append(box("pbeamN", (7.4, 0.3, 0.5), (cx, cy - 3.4, 3.3), P["red"]))
    deco.append(box("pbeamS", (7.4, 0.3, 0.5), (cx, cy + 3.4, 3.3), P["red"]))
    deco.append(box("pbeamW", (0.3, 7.4, 0.5), (cx - 3.4, cy, 3.3), P["red"]))
    deco.append(box("pbeamE", (0.3, 7.4, 0.5), (cx + 3.4, cy, 3.3), P["red"]))
    deco.append(sphere("porb", 0.4, (cx, cy, 5.6), P["gold"], segs=10,
                       rings=6))
    # stone bench
    parts.append(box("bench", (2.6, 0.6, 0.45), (cx, cy - 2.6, 0.22),
                     P["stone_dk"]))
    return parts, deco


def main():
    global P
    clear_scene()
    P = palette()
    parts, rails, deco = [], [], []
    for i in range(len(PATH) - 1):
        x0, y0 = PATH[i]
        x1, y1 = PATH[i + 1]
        segment(parts, rails, x0, y0, x1, y1)
    corner_lanterns(deco)
    pv_parts, pv_deco = pavilion(0, -37.5)
    parts += pv_parts
    deco += pv_deco
    join(parts, "BridgeDeck-col")
    join(rails, "BridgeRails-col")
    join(deco, "BridgeDeco")
    export_glb(os.path.abspath(OUT))


main()
