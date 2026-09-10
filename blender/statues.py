"""Sculptural, open-mouthed temple entrances. Blender coordinates are Z-up.

Call build_statues(P) from gen_island; importing this module builds nothing.
Decoration has no collision suffix. Only the three-piece passage proxies use
Godot's -colonly suffix: no jaw sill, tongue, or end cap crosses the walkway.
"""
import math

import bpy
from mathutils import Vector

from common import box, join, mat, sphere


class _Sculpt:
    """Local head coordinates, smooth meshes, and material-batched output."""

    def __init__(self, cx, name):
        self.origin = Vector((cx, -6.4, 0))
        self.name = name
        self.groups = {}

    def keep(self, obj, material):
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        self.groups.setdefault(material, []).append(obj)
        return obj

    def mesh(self, name, vertices, faces, material):
        data = bpy.data.meshes.new(name)
        data.from_pydata(vertices, [], faces)
        data.update()
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = self.origin
        data.materials.append(material)
        return self.keep(obj, material)

    def orb(self, name, position, radii, material, tilt=0):
        obj = sphere(name, 1, self.origin + Vector(position), material,
                     segs=24, rings=14, scale=radii)
        obj.rotation_euler.y = tilt
        return self.keep(obj, material)

    def tube(self, name, points, radius, material, taper=None, fine=False):
        data = bpy.data.curves.new(name, "CURVE")
        data.dimensions = "3D"
        data.resolution_u = 2 if fine else 4
        data.bevel_depth = radius
        data.bevel_resolution = 0 if fine else 1
        data.use_fill_caps = True
        spline = data.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for i, (point, co) in enumerate(zip(spline.bezier_points, points)):
            point.co = co
            # Curve splines support AUTO (AUTO_CLAMPED is an F-curve mode).
            point.handle_left_type = point.handle_right_type = "AUTO"
            point.radius = taper[i] if taper is not None else 1
        obj = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(obj)
        obj.location = self.origin
        data.materials.append(material)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        self.keep(bpy.context.object, material)

    def finish(self):
        return [join(objects, self.name + "_" + material.name)
                for material, objects in self.groups.items()]


def _surface(sections, y, angle, offset=0):
    """Rounded U-shaped body surface; angle -1/pi+1 denotes each foot."""
    width, height = sections[-1][1:]
    for (y0, w0, h0), (y1, w1, h1) in zip(sections, sections[1:]):
        if y <= y1:
            t = max(0, min(1, (y - y0) / (y1 - y0)))
            t = t * t * (3 - 2 * t)
            width, height = w0 + (w1 - w0) * t, h0 + (h1 - h0) * t
            break
    if angle < 0:
        return (width * (1 + 0.04 * angle) + offset, y,
                2.6 * (1 + angle))
    if angle > math.pi:
        t = angle - math.pi
        return (-width * (1 - 0.04 * t) - offset, y, 2.6 * (1 - t))
    return ((width + offset) * math.cos(angle), y,
            2.6 + (height - 2.6 + offset) * math.sin(angle))


def _shell(s, sections, outside, inside, lip):
    """Closed wall thickness with open passage ends, not a capped cylinder."""
    angles = [-1, -0.75, -0.5, -0.25]
    angles += [math.pi * i / 24 for i in range(25)]
    angles += [math.pi + i / 4 for i in range(1, 5)]
    ys = []
    for a, b in zip(sections, sections[1:]):
        ys.extend(a[0] + (b[0] - a[0]) * i / 5 for i in range(5))
    ys.append(sections[-1][0])
    outer, inner = [], []
    for y in ys:
        for angle in angles:
            outer.append(_surface(sections, y, angle))
            if angle < 0:
                inner.append((1.30, y, 2.65 * (1 + angle)))
            elif angle > math.pi:
                inner.append((-1.30, y, 2.65 * (1 - (angle - math.pi))))
            else:
                inner.append((1.30 * math.cos(angle), y,
                              2.65 + 0.65 * math.sin(angle)))
    n = len(angles)
    faces = []
    for row in range(len(ys) - 1):
        for j in range(n - 1):
            a = row * n + j
            faces.append((a, a + n, a + n + 1, a + 1))
    s.mesh("rounded hide", outer, faces, outside)
    s.mesh("open throat", inner, [tuple(reversed(f)) for f in faces], inside)
    vertices = outer + inner
    k = len(outer)
    rims = []
    for row in (0, len(ys) - 1):
        for j in range(n - 1):
            a = row * n + j
            face = (a, a + 1, k + a + 1, k + a)
            rims.append(face if row == 0 else tuple(reversed(face)))
    for row in range(len(ys) - 1):
        a, b = row * n, (row + 1) * n
        rims.extend([(a, k + a, k + b, b),
                     (a + n - 1, b + n - 1, k + b + n - 1, k + a + n - 1)])
    s.mesh("arch wall edges", vertices, rims, lip)


def _stripe(s, name, path, width, material):
    """A tapered painted ribbon on an explicitly sampled curved surface."""
    vertices = []
    for i in range(21):
        t = i / 20
        half_width = width * (0.06 + 0.94 * math.sin(math.pi * t) ** 0.7)
        vertices.extend((path(t, -half_width), path(t, half_width)))
    faces = [(2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2) for i in range(20)]
    obj = s.mesh(name, vertices, faces, material)
    # The material is double-sided in glTF; no duplicated coplanar faces.
    obj.data.materials[0].use_backface_culling = False


def _head_point(x, z, offset=0.025):
    """Front of the shared cranial ellipsoid, for painted facial markings."""
    q = max(0.001, 1 - (x / 1.85) ** 2 - ((z - 4.15) / 1.25) ** 2)
    return (x, -1.30 * math.sqrt(q) - offset, z)


def build_statues(P, tower_radius=4.3):
    """Build dragon at (-8,-6.4) and tiger at (8,-6.4), facing -Y.

    P is common.palette(), including jade and blue. Tower centers are at Y=3.
    Returns the created, material-batched mesh objects and collision proxies.
    Passage inner collision faces are X=cx+/-1.25 and Z=2.60; its floor is
    the existing platform at Z=0. The dragon win point (-8,-6.8,0) stays clear.
    This function does not clear the scene, export assets, or change materials
    in P. Call once per island build.
    """
    end = 3 - tower_radius * math.cos(math.pi / 8) + 6.4 + 0.15
    if end <= 2.5:
        raise ValueError("tower_radius leaves insufficient room for the statues")
    ivory = mat("statue_ivory", (0.94, 0.90, 0.73), rough=0.48)
    cream = mat("statue_cream", (0.96, 0.86, 0.63), rough=0.65)
    enamel = mat("statue_scale_outline", (0.76, 0.91, 0.79), rough=0.42)
    scarlet = mat("statue_lip_red", (0.64, 0.035, 0.035), rough=0.48)
    black = mat("statue_ink", (0.018, 0.023, 0.021), rough=0.63)
    amber = mat("statue_iris", (0.93, 0.54, 0.07), rough=0.32)
    blue_light = mat("statue_mane_highlight", (0.08, 0.43, 0.63), rough=0.48)
    objects = []

    for dragon, cx, name in ((True, -8, "DragonStatue"),
                             (False, 8, "TigerStatue")):
        s = _Sculpt(cx, name)
        hide = P["jade"] if dragon else P["tiger"]
        sections = [(-1.30, 1.92, 4.35), (-0.15, 2.06, 4.90),
                    (1.30, 1.96, 4.40), (end * 0.66, 1.85, 4.12),
                    (end, 1.55, 3.72)]
        _shell(s, sections, hide, P["mouth"], scarlet)
        s.orb("cranial dome", (0, 0, 4.15), (1.85, 1.30, 1.25), hide)

        # No floor or cross-mouth bottom lip: the ground-level exit is open.
        lip_path = [(-1.56, -1.42, 0.18), (-1.62, -1.48, 1.3),
                    (-1.57, -1.51, 2.50), (-1.08, -1.53, 3.13),
                    (0, -1.55, 3.38), (1.08, -1.53, 3.13),
                    (1.57, -1.51, 2.50), (1.62, -1.48, 1.3),
                    (1.56, -1.42, 0.18)]
        s.tube("continuous open lip", lip_path, 0.16, scarlet)
        for side in (-1, 1):
            s.orb("jaw hinge", (side * 1.80, -0.60, 1.80),
                  (0.43, 0.86, 1.18), hide, side * -0.12)
            s.orb("lower jaw rail", (side * 1.80, -0.40, 0.25),
                  (0.48, 1.25, 0.25), hide)
            s.tube("long curved canine",
                   [(side * 1.43, -1.60, 3.04),
                    (side * 1.49, -1.73, 2.70),
                    (side * 1.43, -1.70, 2.26)],
                   0.17, ivory, [1, 0.72, 0.025])
            s.tube("lower side canine",
                   [(side * 1.54, -1.51, 0.25),
                    (side * 1.52, -1.64, 0.60),
                    (side * 1.43, -1.65, 0.90)],
                   0.12, ivory, [1, 0.7, 0.025])
            for y in (1.45, end - 1.05):
                s.orb("haunch", (side * 1.96, y, 1.26),
                      (0.54, 0.70, 1.23), hide, side * 0.10)
                s.orb("planted paw", (side * 2.02, y - 0.36, 0.31),
                      (0.65, 0.88, 0.31), hide)
                for toe in (-1, 0, 1):
                    x = side * 2.02 + toe * 0.30
                    s.orb("rounded toe", (x, y - 0.96, 0.24),
                          (0.20, 0.31, 0.22), hide)
                    if dragon:
                        s.tube("ivory claw", [(x, y - 1.06, 0.28),
                                               (x, y - 1.35, 0.17),
                                               (x, y - 1.44, 0.07)],
                               0.10, ivory, [1, 0.6, 0.025])
            # Eyes are layered sculpture, not emissive floating spheres.
            s.orb("eye socket", (side * 1.10, -1.01, 4.45),
                  (0.55, 0.27, 0.38), black, side * -0.20)
            s.orb("eye white", (side * 1.10, -1.24, 4.45),
                  (0.40, 0.12, 0.25), ivory, side * -0.20)
            s.orb("amber iris", (side * 1.06, -1.35, 4.44),
                  (0.18, 0.06, 0.20), amber)
            s.orb("vertical pupil", (side * 1.06, -1.40, 4.44),
                  (0.065, 0.035, 0.17), black)
            s.orb("eye glint", (side * 1.06 - 0.045, -1.43, 4.52),
                  (0.038, 0.018, 0.045), ivory)
        for x in (-0.86, -0.43, 0, 0.43, 0.86):
            s.tube("upper incisor", [(x, -1.63, 3.27),
                                      (x, -1.72, 3.08),
                                      (x * 0.97, -1.70, 2.82)],
                   0.095, ivory, [1, 0.8, 0.025])

        if dragon:
            for side in (-1, 1):
                s.orb("long muzzle lobe", (side * 0.52, -1.22, 3.68),
                      (0.78, 0.84, 0.39), hide)
                s.orb("red nostril scroll", (side * 0.44, -1.94, 3.94),
                      (0.48, 0.35, 0.38), scarlet, side * 0.2)
                s.orb("nostril hollow", (side * 0.48, -2.23, 3.98),
                      (0.20, 0.075, 0.13), black, side * 0.25)
                s.tube("fierce brow", [(side * 0.59, -1.22, 4.62),
                                       (side * 1.08, -1.17, 4.85),
                                       (side * 1.60, -0.76, 4.87)],
                       0.18, hide, [0.7, 1, 0.06])
                s.tube("branching antler", [(side * 1.08, 0.12, 4.96),
                                            (side * 1.23, 0.40, 5.53),
                                            (side * 1.44, 0.96, 6.16),
                                            (side * 1.83, 1.37, 6.58)],
                       0.29, ivory, [1, 0.85, 0.45, 0.015])
                s.tube("antler tine", [(side * 1.25, 0.48, 5.62),
                                       (side * 1.68, 0.30, 5.99),
                                       (side * 1.96, 0.41, 6.38)],
                       0.17, ivory, [1, 0.70, 0.015])
                s.tube("antler rear tine", [(side * 1.43, 0.94, 6.12),
                                            (side * 1.39, 1.51, 6.36),
                                            (side * 1.49, 1.91, 6.47)],
                       0.12, ivory, [1, 0.60, 0.015])
                s.orb("mane root", (side * 1.82, 0.35, 3.85),
                      (0.52, 0.83, 1.14), P["blue"], side * -0.2)
                for j in range(7):
                    z = 2.50 + j * 0.37
                    points = [(side * 1.69, -0.40, z),
                              (side * (2.03 + j * 0.025), 0.12, z + 0.12),
                              (side * (2.42 + j * 0.025), 0.83, z + 0.35),
                              (side * (2.39 + j * 0.035), 1.51, z + 0.82)]
                    s.tube("swept blue mane", points, 0.27, P["blue"],
                           [0.75, 1, 0.7, 0.015])
                    s.tube("mane raised vein",
                           [(x, y - 0.17, zz + 0.06) for x, y, zz in points],
                           0.036, blue_light, [0.5, 1, 0.7, 0.015], fine=True)
                s.tube("curling moustache",
                       [(side * 0.83, -1.98, 3.57),
                        (side * 1.59, -1.94, 3.60),
                        (side * 2.43, -1.66, 3.83),
                        (side * 2.87, -1.19, 4.35),
                        (side * 2.62, -1.05, 4.64),
                        (side * 2.37, -1.22, 4.45)],
                       0.075, ivory, [1, 1, 0.9, 0.7, 0.45, 0.03])
                for j in range(3):
                    s.tube("cheek tendril",
                           [(side * 1.63, -1.00, 2.3 + j * 0.38),
                            (side * 2.10, -1.00, 2.45 + j * 0.38),
                            (side * 2.28, -0.64, 2.75 + j * 0.38)],
                           0.10, hide, [1, 0.75, 0.025])
            # Staggered scallops follow the actual rounded hide, including flanks.
            for row in range(12):
                y = 0.95 + (end - 1.2) * row / 12
                for col in range(13):
                    angle = -0.62 + col * (math.pi + 1.24) / 12
                    yc = y + (0.12 if col % 2 else 0)
                    points = [_surface(sections,
                                       yc + 0.23 * math.sin(math.pi * k / 6),
                                       angle + (k / 6 - 0.5) * 0.29, 0.028)
                              for k in range(7)]
                    s.tube("outlined jade scale", points, 0.022, enamel, fine=True)
            for j in range(6):
                y = 1.1 + j * (end - 1.6) / 6
                z = _surface(sections, y, math.pi / 2)[2]
                points = [(0, y, z - 0.05), (0, y + 0.20, z + 0.45),
                          (0, y + 0.56, z + 0.86)]
                s.tube("flame dorsal crest", points, 0.22, scarlet, [1, 0.75, 0.015])
                s.tube("crest ivory edge", [(0, yy - 0.13, zz) for _, yy, zz in points],
                       0.035, ivory, [1, 0.8, 0.015], fine=True)
            s.tube("coiling dragon tail",
                   [(-1.65, end - 0.7, 2.1), (-2.70, end - 1.5, 1.3),
                    (-3.32, end - 2.5, 1.4), (-3.25, end - 3.4, 2.05),
                    (-2.90, end - 3.65, 2.67), (-2.51, end - 3.30, 2.86)],
                   0.38, hide, [1, 1, 0.85, 0.65, 0.38, 0.025])
        else:
            for side in (-1, 1):
                s.orb("cream cheek ruff", (side * 1.67, -0.93, 2.87),
                      (0.39, 0.48, 0.76), cream, side * -0.18)
                s.orb("rounded muzzle pad", (side * 0.57, -1.29, 3.67),
                      (0.72, 0.65, 0.47), cream, side * 0.1)
                s.orb("rounded black ear", (side * 1.37, 0.03, 5.14),
                      (0.51, 0.32, 0.60), black, side * -0.22)
                s.orb("ochre ear rim", (side * 1.37, -0.17, 5.16),
                      (0.41, 0.19, 0.47), hide, side * -0.22)
                s.orb("cream inner ear", (side * 1.37, -0.32, 5.17),
                      (0.26, 0.07, 0.32), cream, side * -0.22)
                s.tube("cream eyebrow",
                       [(side * 0.64, -1.16, 4.67), (side * 1.06, -1.13, 4.79),
                        (side * 1.47, -0.91, 4.73)], 0.115, cream, [0.5, 1, 0.1])
                for j in range(3):
                    for k in range(3):
                        x, z = 0.36 + j * 0.22, 3.59 + k * 0.12
                        q = 1 - ((x - 0.57) / 0.72) ** 2 - ((z - 3.67) / 0.47) ** 2
                        s.orb("whisker follicle",
                              (side * x, -1.29 - 0.65 * math.sqrt(q) - 0.025, z),
                              (0.030, 0.022, 0.030), black)
                for j in range(4):
                    def facial(t, w, j=j, side=side):
                        x = side * (1.67 - 0.06 * j - 0.76 * t
                                    + 0.14 * math.sin(t * math.pi))
                        z = 4.00 + j * 0.24 + 0.18 * math.sin(t * math.pi) + w
                        return _head_point(x, z, 0.04)
                    _stripe(s, "curved facial stripe", facial, 0.085, black)
                # Short stripes on the cream ruff are curved, not box bands.
                for j in range(3):
                    s.tube("ruff stripe",
                           [(side * 1.85, -1.17, 2.52 + j * 0.31),
                            (side * 1.69, -1.43, 2.61 + j * 0.31),
                            (side * 1.47, -1.34, 2.70 + j * 0.31)],
                           0.045, black, [0.05, 1, 0.04], fine=True)
            s.orb("nose bridge", (0, -1.15, 4.05), (0.43, 0.48, 0.49), hide)
            # A rounded triangular feline nose with the narrower point below.
            s.tube("feline nose", [(-0.29, -1.89, 3.97), (0, -2.01, 3.85),
                                   (0.29, -1.89, 3.97)], 0.16, black, [0.7, 1, 0.7])
            s.tube("philtrum", [(0, -1.94, 3.86), (0, -1.93, 3.62),
                                (0, -1.83, 3.42)], 0.04, black, fine=True)
            # Traditional king marking, fitted to the forehead's curvature.
            for z, width in ((4.68, 0.42), (4.94, 0.53), (5.17, 0.64)):
                s.tube("forehead king bar",
                       [_head_point(width * (i / 3 - 1), z + 0.04 * abs(i / 3 - 1))
                        for i in range(7)], 0.066, black,
                       [0.08, 0.8, 1, 1, 1, 0.8, 0.08], fine=True)
            s.tube("forehead king stem", [_head_point(0, z) for z in (4.57, 4.8, 5.04, 5.25)],
                   0.065, black, [0.06, 1, 1, 0.08], fine=True)
            for j in range(10):
                y = 0.85 + j * (end - 1.05) / 10
                for side in (-1, 1):
                    def flank(t, w, y=y, j=j, side=side):
                        angle = -0.88 + t * 2.44
                        if side < 0:
                            angle = math.pi - angle
                        yy = y + 0.18 * math.sin(t * 2 * math.pi + j * 0.8) + w
                        return _surface(sections, yy, angle, 0.023)
                    _stripe(s, "flowing flank stripe", flank, 0.12, black)
            tail = [(1.60, end - 0.5, 2.6), (2.35, end - 1.0, 2.4),
                    (2.80, end - 1.8, 2.8), (2.91, end - 2.35, 3.5),
                    (2.66, end - 2.50, 3.91), (2.37, end - 2.30, 3.93)]
            s.tube("upturned tiger tail", tail, 0.17, hide, [1, 1, 1, 0.9, 0.8, 0.5])
            s.tube("black tail tip", tail[-3:], 0.16, black, [0.95, 0.85, 0.35])

        objects.extend(s.finish())
        # Independent, invisible collision: precise clearance without ornate
        # concave collision meshes, and no floor seam at the win trigger.
        y0, y1 = -7.5, end - 6.4
        length, middle = y1 - y0, (y0 + y1) / 2
        collision = [box(name + " passage side", (0.30, length, 2.85),
                         (cx + side * 1.40, middle, 1.425)) for side in (-1, 1)]
        collision.append(box(name + " passage ceiling", (3.10, length, 0.25),
                             (cx, middle, 2.725)))
        objects.append(join(collision, name + "Tunnel-colonly"))
    return objects
