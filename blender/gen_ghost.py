"""Generate the ghost (tiger-spirit wraith) and the talisman prop.

Run:  blender -b -P gen_ghost.py
"""
import math
import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from common import (clear_scene, mat, box, cyl, cone, sphere, join,
                    set_mat, export_glb)

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "..", "game", "assets", "models")


def build_ghost():
    pale = mat("pale", (0.75, 0.8, 0.82), rough=0.6,
               emission=(0.45, 0.55, 0.6), emission_strength=0.7)
    hairm = mat("hair", (0.03, 0.03, 0.04), rough=0.95)
    eyem = mat("geye", (0.02, 0.02, 0.02), rough=0.3,
               emission=(0.9, 0.1, 0.05), emission_strength=5.0)

    parts = []
    # robe: tapered, hovering above the ground
    parts.append(cyl("robe", 0.72, 1.55, (0, 0, 1.0), pale, verts=14,
                     radius2=0.26))
    # ragged hem: few hanging strips
    for k in range(7):
        a = k * 2 * math.pi / 7
        parts.append(cone(f"hem{k}", 0.16, 0.55,
                          (0.58 * math.cos(a), 0.58 * math.sin(a), 0.12),
                          pale, verts=5, rot=(math.pi, 0, 0)))
    # shoulders / chest
    parts.append(sphere("chest", 0.34, (0, 0, 1.78), pale, segs=12, rings=8,
                        scale=(1.15, 0.8, 0.9)))
    # head
    parts.append(sphere("head", 0.24, (0, 0, 2.12), pale, segs=14, rings=10))
    # long hair: cap + back curtain + face strands
    parts.append(sphere("hairCap", 0.27, (0, 0.05, 2.17), hairm, segs=12,
                        rings=8))
    parts.append(box("hairBack", (0.5, 0.14, 1.1), (0, 0.2, 1.6), hairm))
    parts.append(box("hairL", (0.12, 0.1, 0.75), (-0.24, -0.1, 1.85), hairm))
    parts.append(box("hairR", (0.12, 0.1, 0.75), (0.24, -0.1, 1.85), hairm))
    # eyes (glow through the hair)
    parts.append(sphere("eyeL", 0.045, (-0.09, -0.21, 2.14), eyem, segs=8,
                        rings=6))
    parts.append(sphere("eyeR", 0.045, (0.09, -0.21, 2.14), eyem, segs=8,
                        rings=6))
    # arms reaching forward (-Y)
    for s in (-1, 1):
        parts.append(cyl(f"arm{s}", 0.07, 0.85,
                         (s * 0.3, -0.42, 1.62), pale, verts=8,
                         rot=(math.pi / 2.4, 0, s * 0.25)))
        parts.append(sphere(f"hand{s}", 0.09, (s * 0.34, -0.8, 1.5), pale,
                            segs=8, rings=6))
        # claw fingers
        for f in range(3):
            parts.append(cone(f"claw{s}{f}", 0.02, 0.16,
                              (s * (0.28 + f * 0.06), -0.9, 1.47), pale,
                              verts=4, rot=(math.pi / 2, 0, 0)))
    join(parts, "Ghost")
    export_glb(os.path.join(os.path.abspath(DIR), "ghost.glb"))


def build_talisman():
    paper = mat("paper", (0.95, 0.8, 0.25), rough=0.7,
                emission=(0.9, 0.7, 0.2), emission_strength=0.8)
    ink = mat("ink", (0.6, 0.02, 0.02), rough=0.6,
              emission=(1.0, 0.1, 0.05), emission_strength=2.0)
    parts = []
    parts.append(box("sheet", (0.3, 0.02, 0.52), (0, 0, 0), paper))
    # red sigil strokes
    parts.append(box("s1", (0.05, 0.025, 0.4), (0, 0, 0), ink))
    parts.append(box("s2", (0.2, 0.025, 0.05), (0, 0, 0.16), ink))
    parts.append(box("s3", (0.16, 0.025, 0.04), (0, 0, 0.02), ink))
    parts.append(box("s4", (0.12, 0.025, 0.04), (0, 0, -0.13), ink))
    join(parts, "Talisman")
    export_glb(os.path.join(os.path.abspath(DIR), "talisman.glb"))


def main():
    clear_scene()
    build_ghost()
    clear_scene()
    build_talisman()


main()
