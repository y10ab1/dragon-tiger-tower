"""Generate the Lotus Pond island: stone platform, twin 7-story octagonal
pagodas (Dragon & Tiger Towers), dragon/tiger entrance statues, lantern posts.

Run:  blender -b -P gen_island.py
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (clear_scene, palette, box, cyl, cone, sphere, join,
                    set_mat, export_glb)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "game", "assets", "models", "island.glb")

TIERS = 7
TIER_H = 3.4
R0 = 4.3          # circumradius of ground tier
R_STEP = 0.1      # shrink per tier
WALL_T = 0.3

P = None  # palette dict


# ----------------------------------------------------------------------------
def wall_side(parts, cx, cy, z0, angle, half_r, height, opening=None):
    """One octagon side wall. angle = outward normal direction.
    opening = (width, z_bottom, z_top) relative to z0, or None."""
    ri = half_r * math.cos(math.pi / 8)          # inradius
    L = 2 * half_r * math.sin(math.pi / 8)       # side length
    ca, sa = math.cos(angle), math.sin(angle)
    wx, wy = cx + ri * ca, cy + ri * sa          # wall center
    rot = (0, 0, angle)

    def piece(off_along, width, zb, zt):
        # off_along: offset along wall direction (perpendicular to normal)
        px = wx - off_along * sa
        py = wy + off_along * ca
        h = zt - zb
        b = box("wp", (WALL_T, width, h), (px, py, z0 + zb + h / 2),
                P["wall"], rot=rot)
        parts.append(b)

    if opening is None:
        piece(0, L, 0, height)
        return
    ow, ozb, ozt = opening
    side_w = (L - ow) / 2
    piece(-(ow + side_w) / 2, side_w, 0, height)
    piece((ow + side_w) / 2, side_w, 0, height)
    if ozb > 0:
        piece(0, ow, 0, ozb)              # sill
    if ozt < height:
        piece(0, ow, ozt, height)         # lintel


def build_pagoda(cx, cy, prefix):
    """Build one 7-story octagonal pagoda at (cx, cy). Door faces -Y."""
    body, roofs, stairs_vis, ramps, deco = [], [], [], [], []

    for i in range(TIERS):
        r = R0 - R_STEP * i
        z0 = i * TIER_H
        ri = r * math.cos(math.pi / 8)
        w = 0.92 * ri                      # interior slab half-width

        # --- walls (8 sides), k=0 east, k=2 north, k=4 west, k=6 south
        for k in range(8):
            a = k * math.pi / 4
            opening = None
            if i == 0:
                if k == 6:
                    opening = (2.0, 0.0, 2.5)          # door to statue tunnel
                elif k in (0, 4):
                    opening = (1.3, 1.2, 2.3)
            else:
                if (k + i) % 2 == 0:
                    opening = (1.3, 1.1, 2.3)
            wall_side(body, cx, cy, z0, a, r, TIER_H, opening)

        # --- corner columns
        for k in range(8):
            a = math.pi / 8 + k * math.pi / 4
            px = cx + (r - 0.05) * math.cos(a)
            py = cy + (r - 0.05) * math.sin(a)
            body.append(cyl("col", 0.17, TIER_H,
                            (px, py, z0 + TIER_H / 2), P["red"], verts=8))

        # --- floor slab with stair hole (tiers 1..6)
        if i > 0:
            rot_prev = -(i - 1) * math.pi / 2
            # corridor hole over the stair flight below (ends before the
            # far edge so the player lands onto solid floor)
            hole = (-1.0, 2.7, -2.25, -0.55)  # x0,x1,y0,y1 prev-stair frame
            ca, sa = math.cos(rot_prev), math.sin(rot_prev)

            def slab_piece(x0, x1, y0, y1):
                lx, ly = (x0 + x1) / 2, (y0 + y1) / 2
                gx = cx + lx * ca - ly * sa
                gy = cy + lx * sa + ly * ca
                b = box("slab", (x1 - x0, y1 - y0, 0.22),
                        (gx, gy, z0 - 0.11), P["wall_in"],
                        rot=(0, 0, rot_prev))
                body.append(b)

            hx0, hx1, hy0, hy1 = hole
            slab_piece(-w, hx0, -w, w)
            slab_piece(hx1, w, -w, w)
            slab_piece(hx0, hx1, -w, hy0)
            slab_piece(hx0, hx1, hy1, w)
            # guard rail on inner edge of the hole (stops short of the
            # landing so the walk path around the hole stays clear)
            rl = (hx1 - 0.45) - hx0
            gx = cx + ((hx0 + hx1 - 0.45) / 2) * ca - (hy1 + 0.12) * sa
            gy = cy + ((hx0 + hx1 - 0.45) / 2) * sa + (hy1 + 0.12) * ca
            body.append(box("rail", (rl, 0.1, 0.9), (gx, gy, z0 + 0.45),
                            P["wood_dk"], rot=(0, 0, rot_prev)))

        # --- stairs (tiers 0..5) going up along local +X at y=-1.4
        if i < TIERS - 1:
            rot_i = -i * math.pi / 2
            ca, sa = math.cos(rot_i), math.sin(rot_i)
            n_steps = 14
            run0, run1 = -2.2, 2.2
            step_run = (run1 - run0) / n_steps
            for s in range(n_steps):
                lx = run0 + (s + 0.5) * step_run
                ly = -1.4
                gx = cx + lx * ca - ly * sa
                gy = cy + lx * sa + ly * ca
                h = (s + 1) * TIER_H / n_steps
                stairs_vis.append(box(
                    "step", (step_run, 1.2, h),
                    (gx, gy, z0 + h / 2), P["wood"], rot=(0, 0, rot_i)))
            # collision ramp (invisible in game)
            mx, my = 0.0, -1.4
            gx = cx + mx * ca - my * sa
            gy = cy + mx * sa + my * ca
            ang = math.atan2(TIER_H, run1 - run0)
            L = math.hypot(TIER_H, run1 - run0)
            ramps.append(box("ramp", (L, 1.2, 0.18),
                             (gx, gy, z0 + TIER_H / 2),
                             None, rot=(0, ang, rot_i + math.pi)))
            # landing plate bridging flight top and the slab hole end
            lgx = cx + 2.5 * ca - (-1.4) * sa
            lgy = cy + 2.5 * sa + (-1.4) * ca
            ramps.append(box("landing", (0.7, 1.7, 0.2),
                             (lgx, lgy, z0 + TIER_H - 0.1), None,
                             rot=(0, 0, rot_i)))
            stairs_vis.append(box("landing_vis", (0.7, 1.7, 0.08),
                                  (lgx, lgy, z0 + TIER_H - 0.05),
                                  P["wood"], rot=(0, 0, rot_i)))

        # --- eaves: 8 tilted slabs around the perimeter (hollow ring, so
        #     the tower interior stays clear)
        if i < TIERS - 1:
            ri_w = r * math.cos(math.pi / 8)
            for k in range(8):
                a = k * math.pi / 4
                L = 2 * (ri_w + 1.7) * math.tan(math.pi / 8)
                ex = cx + (ri_w + 0.7) * math.cos(a)
                ey = cy + (ri_w + 0.7) * math.sin(a)
                roofs.append(box("eave", (2.0, L, 0.14),
                                 (ex, ey, z0 + TIER_H - 0.55), P["roof"],
                                 rot=(0, 0.32, a)))
                # fascia strip under the eave edge
                fx = cx + (ri_w + 1.55) * math.cos(a)
                fy = cy + (ri_w + 1.55) * math.sin(a)
                roofs.append(box("fascia", (0.1, L, 0.3),
                                 (fx, fy, z0 + TIER_H - 1.0), P["roof_dk"],
                                 rot=(0, 0, a)))

    # --- top roof + spire
    z_top = TIERS * TIER_H
    r_top = R0 - R_STEP * (TIERS - 1)
    roofs.append(cyl("toproof", r_top + 1.25, 2.4, (cx, cy, z_top + 1.1),
                     P["roof"], verts=8, radius2=0.25))
    roofs.append(cyl("fasciaT", r_top + 1.28, 0.16, (cx, cy, z_top - 0.2),
                     P["roof_dk"], verts=8))
    deco.append(cyl("spire", 0.12, 2.2, (cx, cy, z_top + 3.2), P["gold"],
                    verts=8))
    for j in range(3):
        deco.append(sphere("orb", 0.32 - j * 0.07,
                           (cx, cy, z_top + 2.6 + j * 0.65), P["gold"],
                           segs=10, rings=6))

    join(body, f"{prefix}Body-col")
    join(roofs, f"{prefix}Roof-col")
    join(stairs_vis, f"{prefix}Stairs")
    join(ramps, f"{prefix}Ramps-colonly")
    join(deco, f"{prefix}Deco")


# ----------------------------------------------------------------------------
def build_tunnel(cx, head_y, tower_wall_y, body_mat, prefix):
    """Corridor from statue head into the tower door. Walk axis = Y."""
    parts = []
    y0, y1 = head_y + 1.1, tower_wall_y + 0.4
    ymid, ylen = (y0 + y1) / 2, (y1 - y0)
    parts.append(box("twL", (0.35, ylen, 2.6), (cx - 1.25, ymid, 1.3),
                     body_mat))
    parts.append(box("twR", (0.35, ylen, 2.6), (cx + 1.25, ymid, 1.3),
                     body_mat))
    parts.append(box("twT", (2.9, ylen, 0.3), (cx, ymid, 2.75), body_mat))
    return parts


def build_dragon(cx, prefix):
    """Dragon entrance statue, head faces -Y (towards the bridge)."""
    P_ = P
    col, deco = [], []
    head_y = -6.4
    tower_wall_y = 3 - (R0 * math.cos(math.pi / 8))   # tower front wall

    col += build_tunnel(cx, head_y, tower_wall_y, P_["dragon"], prefix)

    # skull above the mouth
    col.append(box("skull", (3.2, 2.4, 1.9), (cx, head_y, 3.55),
                   P_["dragon"]))
    # cheeks framing the mouth
    col.append(box("cheekL", (0.9, 2.2, 2.6), (cx - 1.6, head_y, 1.3),
                   P_["dragon"]))
    col.append(box("cheekR", (0.9, 2.2, 2.6), (cx + 1.6, head_y, 1.3),
                   P_["dragon"]))
    # lower jaw step
    col.append(box("jaw", (3.4, 2.6, 0.24), (cx, head_y - 0.2, 0.12),
                   P_["mouth"]))
    # snout / nose
    deco.append(box("snout", (2.2, 0.9, 0.8), (cx, head_y - 1.5, 2.95),
                    P_["dragon"]))
    deco.append(sphere("noseL", 0.18, (cx - 0.5, head_y - 1.95, 3.1),
                       P_["tiger_st"], segs=8, rings=6))
    deco.append(sphere("noseR", 0.18, (cx + 0.5, head_y - 1.95, 3.1),
                       P_["tiger_st"], segs=8, rings=6))
    # eyes (emissive)
    deco.append(sphere("eyeL", 0.3, (cx - 0.85, head_y - 1.22, 3.9),
                       P_["eye"], segs=10, rings=6))
    deco.append(sphere("eyeR", 0.3, (cx + 0.85, head_y - 1.22, 3.9),
                       P_["eye"], segs=10, rings=6))
    # horns
    for sx in (-1, 1):
        deco.append(cone("horn", 0.28, 1.6,
                         (cx + sx * 0.9, head_y + 0.9, 5.1), P_["gold"],
                         verts=8, rot=(-0.5, 0, 0)))
    # whiskers
    for sx in (-1, 1):
        deco.append(cyl("whisker", 0.045, 2.6,
                        (cx + sx * 1.5, head_y - 1.7, 2.2),
                        P_["dragon_belly"], verts=6,
                        rot=(0.5, sx * 0.5, 0)))
    # teeth: upper hanging + lower corner fangs (clear of walkway center)
    for tx in (-1.0, -0.5, 0.0, 0.5, 1.0):
        deco.append(cone("toothU", 0.11, 0.45,
                         (cx + tx, head_y - 1.05, 2.4), P_["white"],
                         verts=6, rot=(math.pi, 0, 0)))
    for tx in (-1.05, 1.05):
        deco.append(cone("fang", 0.13, 0.55, (cx + tx, head_y - 1.0, 0.5),
                         P_["white"], verts=6))
    # serpent body over the tunnel + dorsal fins
    deco.append(cyl("bodyTube", 1.05, 5.4, (cx, -2.6, 3.35), P_["dragon"],
                    verts=12, rot=(math.pi / 2, 0, 0)))
    for j in range(5):
        deco.append(cone("fin", 0.35, 0.9, (cx, -4.6 + j * 1.1, 4.5),
                         P_["red"], verts=6))
    # coiled tail arcs beside the tower
    for j, (ox, oy) in enumerate([(-3.4, 1.0), (3.4, 1.0)]):
        bpy_obj = cyl("coil", 1.5, 0.8, (cx + ox, oy, 0.6), P_["dragon"],
                      verts=10)
        deco.append(bpy_obj)

    join(col, f"{prefix}-col")
    join(deco, f"{prefix}Deco")


def build_tiger(cx, prefix):
    """Tiger entrance statue, head faces -Y."""
    P_ = P
    col, deco = [], []
    head_y = -6.4
    tower_wall_y = 3 - (R0 * math.cos(math.pi / 8))

    col += build_tunnel(cx, head_y, tower_wall_y, P_["tiger"], prefix)

    col.append(box("skullT", (3.4, 2.5, 2.0), (cx, head_y, 3.6), P_["tiger"]))
    col.append(box("cheekTL", (0.95, 2.3, 2.6), (cx - 1.62, head_y, 1.3),
                   P_["tiger"]))
    col.append(box("cheekTR", (0.95, 2.3, 2.6), (cx + 1.62, head_y, 1.3),
                   P_["tiger"]))
    col.append(box("jawT", (3.5, 2.7, 0.24), (cx, head_y - 0.2, 0.12),
                   P_["mouth"]))
    # muzzle
    deco.append(box("muzzle", (1.9, 0.8, 1.0), (cx, head_y - 1.5, 3.0),
                    P_["white"]))
    deco.append(box("noseT", (0.6, 0.3, 0.35), (cx, head_y - 1.95, 3.35),
                    P_["tiger_st"]))
    # eyes
    deco.append(sphere("eyeTL", 0.28, (cx - 0.8, head_y - 1.28, 4.0),
                       P_["eye"], segs=10, rings=6))
    deco.append(sphere("eyeTR", 0.28, (cx + 0.8, head_y - 1.28, 4.0),
                       P_["eye"], segs=10, rings=6))
    # ears
    for sx in (-1, 1):
        deco.append(cone("ear", 0.45, 0.8, (cx + sx * 1.15, head_y + 0.5, 5.0),
                         P_["tiger"], verts=6))
    # king mark 王 on forehead
    for j, (wz, ww) in enumerate([(4.75, 1.1), (4.45, 0.8), (4.15, 1.1)]):
        deco.append(box(f"wang{j}", (ww, 0.1, 0.16),
                        (cx, head_y - 1.28, wz), P_["tiger_st"]))
    deco.append(box("wangV", (0.16, 0.1, 0.75), (cx, head_y - 1.28, 4.45),
                    P_["tiger_st"]))
    # fangs
    for tx in (-1.05, 1.05):
        deco.append(cone("fangT", 0.14, 0.6, (cx + tx, head_y - 1.05, 0.55),
                         P_["white"], verts=6))
    for tx in (-0.9, 0.9):
        deco.append(cone("fangTU", 0.13, 0.5,
                         (cx + tx, head_y - 1.05, 2.35), P_["white"],
                         verts=6, rot=(math.pi, 0, 0)))
    # body over tunnel with stripes
    deco.append(box("bodyT", (2.6, 5.2, 1.5), (cx, -2.7, 3.45), P_["tiger"]))
    for j in range(4):
        deco.append(box(f"stripe{j}", (2.7, 0.35, 1.55),
                        (cx, -4.4 + j * 1.15, 3.45), P_["tiger_st"]))
    # legs
    for sx, sy in ((-1.05, -4.9), (1.05, -4.9), (-1.05, -0.8), (1.05, -0.8)):
        col.append(cyl("legT", 0.38, 2.7, (cx + sx * 1.35, sy, 1.35),
                       P_["tiger"], verts=8))
    # tail
    deco.append(cyl("tail", 0.16, 2.4, (cx + 1.2, 0.6, 3.4), P_["tiger"],
                    verts=6, rot=(0.9, 0.7, 0)))

    join(col, f"{prefix}-col")
    join(deco, f"{prefix}Deco")


# ----------------------------------------------------------------------------
def build_platform():
    parts = []
    parts.append(box("plat", (34, 22, 2.0), (0, 0.5, -1.0), P["stone"]))
    # perimeter parapet with a gap at the bridge landing (south center)
    t, h = 0.3, 1.0
    edges = [
        # (cx, cy, sx, sy)
        (0, 11.35, 34.6, t),                 # north
        (-17.15, 0.5, t, 22),                # west
        (17.15, 0.5, t, 22),                 # east
        (-10.1, -10.35, 13.5, t),            # south-west of gap
        (10.1, -10.35, 13.5, t),             # south-east of gap
    ]
    for j, (ex, ey, sx, sy) in enumerate(edges):
        parts.append(box(f"parapet{j}", (sx, sy, h), (ex, ey, h / 2),
                         P["stone_dk"]))
    join(parts, "Platform-col")


def build_lanterns():
    spots = [(-13, -7), (13, -7), (-13, 8), (13, 8), (-3.4, -9.3), (3.4, -9.3)]
    deco = []
    for j, (lx, ly) in enumerate(spots):
        deco.append(cyl(f"post{j}", 0.12, 3.2, (lx, ly, 1.6), P["wood_dk"],
                        verts=8))
        deco.append(cyl(f"cap{j}", 0.4, 0.15, (lx, ly, 3.25), P["roof_dk"],
                        verts=8))
        deco.append(sphere(f"lamp{j}", 0.38, (lx, ly, 2.85), P["lantern"],
                           segs=12, rings=8, scale=(1, 1, 1.25)))
        # Godot light position (Blender (x,y,z) -> Godot (x,z,-y))
        print(f"LANTERN godot=({lx}, 2.85, {-ly})")
    join(deco, "Lanterns")


# ----------------------------------------------------------------------------
def main():
    global P
    clear_scene()
    P = palette()
    build_platform()
    build_pagoda(-8, 3, "DragonTower")   # dragon = west tower
    build_pagoda(8, 3, "TigerTower")     # tiger  = east tower
    build_dragon(-8, "DragonStatue")
    build_tiger(8, "TigerStatue")
    build_lanterns()
    export_glb(os.path.abspath(OUT))


main()
