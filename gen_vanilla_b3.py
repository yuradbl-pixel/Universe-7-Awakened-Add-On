"""Universe 7: Anime Textures - vanilla batch 3: deepslate ores, bricks, and all 16 wool colours."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_vanilla_b2 as B2          # reuses the ore painter (also re-renders batch 2, which is deterministic)
from blockkit import *

PACK = B2.PACK
DONE = []
def vsave(cv, name):
    cv.save(f"{PACK}/{name}"); DONE.append(name)

# ------------------------------------------------------------ deepslate ores
DEEP = f"{PACK}/deepslate/deepslate.png"
for i, k in enumerate(B2.ORES):
    vsave(B2.ore(DEEP, k, 500 + i), f"deepslate/deepslate_{k}_ore.png")

# ------------------------------------------------------------ bricks
BR = ramp((190, 80, 60), 5, hi=(255, 200, 170), lo=(80, 24, 20))
cv = Canvas(); rnd = random.Random(600)
MORTAR = (200, 192, 176)
for row in range(8):
    off = 0 if row % 2 == 0 else 16
    for col in range(4):
        slab(cv, col * 32 + off, row * 16, 32, 16, BR, bevel=2, grout=MORTAR, sheen=0, tone=rnd.uniform(-0.3, 0.3), bands=True)
for y in range(S):                                                       # mortar shading: lit top edge of each joint
    for x in range(S):
        if cv.get(x, y)[:3] == MORTAR and cv.get(x, (y + 1) % S)[:3] != MORTAR and y % 16 == 0:
            pass
for _ in range(220):                                                     # clay speckle
    x, y = rnd.randrange(S), rnd.randrange(S)
    if cv.get(x, y)[:3] != MORTAR:
        wput(cv, x, y, BR[3] if rnd.random() < 0.6 else BR[1])
for _ in range(10):                                                      # chipped corners
    x, y = rnd.randrange(S), rnd.randrange(S)
    for d in range(3):
        wput(cv, x + d, y, BR[4]); wput(cv, x, y + d, BR[4])
vsave(cv, "brick.png")

# ------------------------------------------------------------ wool (knitted V-stitches, cel shaded)
def knit_light():
    """Light value 0..1 per pixel for knitted fabric: rows of 8x8 V stitches (seamless at 128)."""
    L = [[0.0] * S for _ in range(S)]
    n = fbm(610, ((8, 0.6), (16, 0.4)))
    def seg_d(px, py, ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        t = max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / (vx * vx + vy * vy)))
        return math.hypot(px - ax - t * vx, py - ay - t * vy), t
    for y in range(S):
        for x in range(S):
            sx, sy = (x % 8) + 0.5, (y % 8) + 0.5
            best = None
            for dy in (-8, 0):                                            # this stitch and the one above it overlap
                dl, tl = seg_d(sx, sy, 0.8, dy + 1.0, 3.6, dy + 9.0)      # left leg of the V
                dr, tr = seg_d(sx, sy, 7.2, dy + 1.0, 4.4, dy + 9.0)      # right leg
                for d, t, side in ((dl, tl, 0), (dr, tr, 1)):
                    if d < 1.9 and (best is None or t > best[1]):
                        best = (d, t, side)
            if best is None:
                lit = 0.12                                                # deep gap between loops
            else:
                d, t, side = best
                lit = (0.86 if side == 0 else 0.56) - d * 0.14 - t * 0.12  # left leg lit, right leg shaded
                if t < 0.18: lit += 0.08                                  # top of the loop catches light
            L[y][x] = max(0, min(1, lit + (n(x, y) - 0.5) * 0.1))
    return L

LIGHT_MAP = knit_light()
WOOL = {"white": (236, 236, 240), "orange": (240, 130, 40), "magenta": (200, 70, 200), "light_blue": (100, 180, 240),
        "yellow": (250, 214, 50), "lime": (130, 210, 50), "pink": (245, 150, 190), "gray": (90, 94, 104),
        "silver": (160, 162, 168), "cyan": (40, 160, 170), "purple": (130, 60, 190), "blue": (54, 70, 190),
        "brown": (120, 80, 50), "green": (80, 120, 40), "red": (190, 50, 44), "black": (34, 34, 42)}
for name, col in WOOL.items():
    R = ramp(col, 5, hi=mix(col, (255, 255, 250), 0.7), lo=mix(col, (10, 10, 30), 0.75))
    cv = Canvas(); rnd = random.Random(hash(name) & 0xffff)
    for y in range(S):
        for x in range(S):
            cv.put(x, y, band(R, LIGHT_MAP[y][x]))
    for _ in range(25):                                                   # fuzzy fibres
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, R[0]); wput(cv, x + 1, y - 1, R[1])
    vsave(cv, f"wool_colored_{name}.png")

print("vanilla batch 3:", len(DONE), "textures")
