"""Generate the Lotus Pond island: stone platform, twin 7-story octagonal
pagodas (Dragon & Tiger Towers), dragon/tiger entrance statues, lantern posts.

Run:  blender -b -P gen_island.py
"""
import math
import os
import sys
import bpy
from mathutils import Vector

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (clear_scene, palette, box, cyl, sphere, join,
                    set_mat, export_glb)
from statues import build_statues

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "game", "assets", "models", "island.glb")

TIERS = 7
TIER_H = 3.4
R0 = 4.3          # circumradius of ground tier
R_STEP = 0.1      # shrink per tier
WALL_T = 0.3

P = None  # palette dict


# ----------------------------------------------------------------------------
def wall_side(parts, cx, cy, z0, angle, half_r, height, opening=None,
              arched=False):
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
    if arched:
        # Fill above a semicircular opening, leaving a real hole, not a decal.
        radius = ow / 2
        spring = ozt - radius
        verts, faces = [], []
        for j in range(17):
            t = math.pi - j * math.pi / 16
            along = radius * math.cos(t)
            bottom = spring + radius * math.sin(t)
            for depth, z in ((-WALL_T / 2, bottom), (-WALL_T / 2, height),
                             (WALL_T / 2, bottom), (WALL_T / 2, height)):
                verts.append((wx + depth * ca - along * sa,
                              wy + depth * sa + along * ca, z0 + z))
        for j in range(16):
            a = 4 * j
            faces += [(a, a + 4, a + 5, a + 1),
                      (a + 2, a + 3, a + 7, a + 6),
                      (a, a + 2, a + 6, a + 4)]
        parts.append(mesh_object("arch_wall", verts, faces, P["wall"]))
    elif ozt < height:
        piece(0, ow, ozt, height)         # lintel


def mesh_object(name, vertices, faces, material):
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    set_mat(obj, material)
    return obj


def molding(name, points, radius, material):
    """Small polygonal tube, used for tile rolls and architectural trim."""
    verts, faces = [], []
    for j, point in enumerate(points):
        tangent = Vector(points[min(j + 1, len(points) - 1)]) - Vector(
            points[max(0, j - 1)])
        tangent.normalize()
        u = tangent.cross(Vector((0, 0, 1)))
        if u.length < 0.01:
            u = tangent.cross(Vector((0, 1, 0)))
        u.normalize()
        v = tangent.cross(u)
        for k in range(6):
            a = k * math.tau / 6
            verts.append(Vector(point) + radius * (math.cos(a) * u + math.sin(a) * v))
    for j in range(len(points) - 1):
        for k in range(6):
            a, b = j * 6 + k, j * 6 + (k + 1) % 6
            faces.append((a, b, b + 6, a + 6))
    faces += [tuple(reversed(range(6))), tuple(range(len(verts) - 6, len(verts)))]
    obj = mesh_object(name, verts, faces, material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def eaves(parts, cx, cy, radius, z, crown=False):
    """Eight continuous curved roof facets, rolled tiles and green hip ridges."""
    inner = 0.35 if crown else radius - 0.06
    outer = radius + 1.65
    rise = 1.95 if crown else 0.72

    def point(side, u, t):
        a, b = math.pi / 8 + side * math.pi / 4, math.pi / 8 + (side + 1) * math.pi / 4
        r = inner + (outer - inner) * t
        x = (1 - u) * math.cos(a) + u * math.cos(b)
        y = (1 - u) * math.sin(a) + u * math.sin(b)
        # Downward sweep turns upward at the outer edge, strongest at hips.
        height = rise * (1 - t) ** 2 + 0.18 * t ** 8
        height += 0.42 * abs(2 * u - 1) ** 6 * t ** 4
        return (cx + r * x, cy + r * y, z + height)

    for side in range(8):
        verts = [point(side, j / 16, k / 8) for k in range(9) for j in range(17)]
        faces = []
        for k in range(8):
            for j in range(16):
                n = k * 17 + j
                faces.append((n, n + 17, n + 18, n + 1))
        parts.append(mesh_object("curved_tiles", verts, faces, P["roof"]))
        for j in range(17):
            points = [point(side, j / 16, k / 8) for k in range(9)]
            parts.append(molding("tile_roll", points, 0.045, P["tile_light"]))
        for t in (0.35, 0.65, 0.85):
            parts.append(molding("tile_course", [point(side, j / 16, t)
                                                  for j in range(17)], 0.018, P["roof_dk"]))
        edge = [point(side, j / 16, 1) for j in range(17)]
        parts.append(molding("green_fascia", [(x, y, z - 0.12) for x, y, z in edge],
                             0.12, P["jade"]))
        parts.append(molding("eave_lip", edge, 0.065, P["tile_light"]))
        hip = [point(side, 0, k / 8) for k in range(9)]
        x, y, tip = hip[-1]
        dx, dy = x - cx, y - cy
        hip += [(x + dx * 0.035, y + dy * 0.035, tip + 0.22),
                (x + dx * 0.045, y + dy * 0.045, tip + 0.43)]
        parts.append(molding("upturned_hip", hip, 0.095, P["jade"]))


def gallery(parts, deco, cx, cy, r, z0, tier):
    """Open white balustrades and painted brackets outside the existing stairs."""
    outer = r + (1.05 if tier == 0 else 0.65)
    for k in range(8):
        a = k * math.pi / 4
        ca, sa = math.cos(a), math.sin(a)
        ri = outer * math.cos(math.pi / 8)
        length = 2 * outer * math.sin(math.pi / 8)
        x, y = cx + ri * ca, cy + ri * sa
        # Thin annular deck never covers the tower's interior stair openings.
        parts.append(box("gallery_deck", (outer - r + 0.25, length, 0.18),
                         (cx + (ri - (outer - r) / 2) * ca,
                          cy + (ri - (outer - r) / 2) * sa, z0 - 0.09),
                         P["white"], rot=(0, 0, a)))
        if tier > 0 or k != 6:
            for h in (0.22, 0.8):
                parts.append(box("white_rail", (0.13, length, 0.12),
                                 (x, y, z0 + h), P["white"], rot=(0, 0, a)))
            for j in range(7):
                offset = (j / 6 - 0.5) * length
                parts.append(box("baluster", (0.13, 0.13, 0.82),
                                 (x - offset * sa, y + offset * ca, z0 + 0.41), P["white"]))
        # Colorful beam courses and paired bracket blocks under each roof.
        for h, material, width in ((2.28, "red", 0.20), (2.48, "jade", 0.27),
                                    (2.64, "blue", 0.32)):
            deco.append(box("painted_beam", (width, length, 0.13),
                            (x, y, z0 + h), P[material], rot=(0, 0, a)))
        for offset in (-length * 0.38, 0, length * 0.38):
            for j in range(3):
                deco.append(box("dougong", (0.3 + j * 0.18, 0.24 + j * 0.18, 0.13),
                                (x - offset * sa, y + offset * ca, z0 + 2.03 + j * 0.17),
                                P["jade" if j % 2 else "white"], rot=(0, 0, a)))
    for k in range(8):
        a = math.pi / 8 + k * math.pi / 4
        x, y = cx + outer * math.cos(a), cy + outer * math.sin(a)
        if tier == 0:
            parts.append(cyl("vermilion_pillar", 0.20, 2.65,
                             (x, y, z0 + 1.325), P["red"], verts=16))
        parts.append(box("balcony_post", (0.22, 0.22, 1.0), (x, y, z0 + 0.5), P["white"]))


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
                opening = (1.65, 0.4, 2.5) if k % 2 else (1.3, 1.0, 2.3)
            arched = opening is not None and (i > 0 or k != 6)
            wall_side(body, cx, cy, z0, a, r, TIER_H, opening, arched)
            if arched:
                ow, bottom, top = opening
                points = [(-ow / 2, bottom), (-ow / 2, top - ow / 2)]
                points += [(ow / 2 * math.cos(math.pi - j * math.pi / 16),
                            top - ow / 2 + ow / 2 * math.sin(math.pi - j * math.pi / 16))
                           for j in range(17)]
                points += [(ow / 2, bottom)]
                deco.append(molding("window_arch", [
                    (cx + (ri + 0.17) * math.cos(a) - u * math.sin(a),
                     cy + (ri + 0.17) * math.sin(a) + u * math.cos(a), z0 + h)
                    for u, h in points], 0.065, P["white"]))

        gallery(body, deco, cx, cy, r, z0, i)

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

        # Keep the center hollow so the roof does not cross the stair flight.
        if i < TIERS - 1:
            eaves(roofs, cx, cy, r, z0 + TIER_H - 0.85)

    # --- top roof + spire
    z_top = TIERS * TIER_H
    r_top = R0 - R_STEP * (TIERS - 1)
    eaves(roofs, cx, cy, r_top, z_top - 0.85, crown=True)
    deco.append(cyl("spire", 0.09, 4.3, (cx, cy, z_top + 3.05), P["gold"], verts=12))
    for j in range(7):
        radius = 0.68 - j * 0.075
        height = z_top + 1.35 + j * 0.43
        deco.append(cyl("finial_bell", radius, 0.22, (cx, cy, height),
                        P["roof_dk"], verts=8, radius2=radius * 0.5))
        deco.append(cyl("finial_lip", radius, 0.055, (cx, cy, height - 0.11),
                        P["tile_light"], verts=8))

    join(body, f"{prefix}Body-col")
    # Decorative tile rolls do not need thousands of physics triangles.
    join(roofs, f"{prefix}Roof")
    join(stairs_vis, f"{prefix}Stairs")
    join(ramps, f"{prefix}Ramps-colonly")
    join(deco, f"{prefix}Deco")


# ----------------------------------------------------------------------------
def build_platform():
    parts = []
    parts.append(box("plat", (34, 22, 0.55), (0, 0.5, -0.275), P["stone"]))
    parts.append(box("plinth_trim", (34.4, 22.4, 0.13), (0, 0.5, -0.18), P["white"]))
    for x in range(-15, 16, 5):
        for y in (-9, 10):
            parts.append(box("platform_pile", (0.55, 0.55, 2.7),
                             (x, y, -1.7), P["stone"]))
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
        parts.append(box(f"parapet{j}", (sx, sy, 0.58), (ex, ey, 0.4),
                          P["stone_dk"]))
        parts.append(box("parapet_cap", (sx, sy, 0.13), (ex, ey, 0.85), P["stone"]))
        count = max(1, round(max(sx, sy) / 1.8))
        for i in range(count + 1):
            u = i / count - 0.5
            x, y = ex + (sx * u if sx > sy else 0), ey + (sy * u if sy > sx else 0)
            parts.append(box("stone_post", (0.3, 0.3, h), (x, y, h / 2), P["stone"]))
            parts.append(box("stone_cap", (0.36, 0.36, 0.1), (x, y, h), P["white"]))
        for i in range(count):
            u = (i + 0.5) / count - 0.5
            x, y = ex + (sx * u if sx > sy else 0), ey + (sy * u if sy > sx else 0)
            size = (sx / count - 0.42, sy + 0.025, 0.30) if sx > sy else (sx + 0.025, sy / count - 0.42, 0.30)
            parts.append(box("recessed_panel", size, (x, y, 0.4), P["stone"]))
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
    build_statues(P, R0)
    build_lanterns()
    export_glb(os.path.abspath(OUT))


main()
