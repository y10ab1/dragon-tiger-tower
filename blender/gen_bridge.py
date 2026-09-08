"""Generate the nine-turn bridge + shore pavilion.
Bridge starts at (0,0) (island side) and zigzags towards -Y (the shore).

Run:  blender -b -P gen_bridge.py
"""
import math
import os
import sys

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
        # railing
        rails.append(box("railT", (L - 2.6, 0.12, 0.12),
                         (cx + ox, cy + oy, RAIL_H), P["red"],
                         rot=(0, 0, ang)))
        n_posts = max(2, int(L / 1.6))
        for p in range(n_posts + 1):
            t = -0.5 + (p / n_posts) * ((L - 2.6) / L)
            t = (p / n_posts - 0.5) * (L - 2.6) / L
            px = cx + t * L * math.cos(ang) + ox
            py = cy + t * L * math.sin(ang) + oy
            rails.append(box("post", (0.12, 0.12, RAIL_H),
                             (px, py, RAIL_H / 2), P["red"],
                             rot=(0, 0, ang)))
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
    deco.append(cyl("proof", 6.8, 2.2, (cx, cy, 4.3), P["roof"], verts=4,
                    radius2=0.3, rot=(0, 0, math.pi / 4)))
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
