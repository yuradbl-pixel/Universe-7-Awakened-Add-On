"""Universe 7: Anime Textures - vanilla batch 5: leaves for all 8 trees.
Tinted leaves are greyscale (Minecraft colours them per biome); *_carried are full colour for the
inventory; *_opaque have no see-through gaps (used when Fancy Leaves is off)."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *
from PIL import Image

PACK = "/home/claude/u7_textures/textures/blocks"
DONE = []

def leaf(lay, cx, cy, length, width, ang, R, outline_c, style):
    """One cel-shaded leaf with a midrib (or a needle / petal)."""
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(int(cy - length - 2), int(cy + length + 3)):
        for x in range(int(cx - length - 2), int(cx + length + 3)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            u = (dx * ca + dy * sa) / length                              # along the leaf, -1..1
            v = (-dx * sa + dy * ca) / width                              # across
            if style == "needle":
                if abs(u) <= 1 and abs(v) <= 1:
                    lay.put(x % S, y % S, R[1] if v < 0 else R[3])
                continue
            half = (1 - u * u) ** (0.8 if style == "broad" else 1.0)
            if abs(u) <= 1 and abs(v) <= half:
                k = v / max(0.05, half)
                c = R[1] if k < -0.2 else R[2] if k < 0.45 else R[3]      # lit side / mid / shaded side
                if abs(k) < 0.12 and abs(u) < 0.8: c = R[0] if k < 0 else R[3]   # midrib
                if style == "petal" and u < -0.6: c = R[0]
                lay.put(x % S, y % S, c)

def leaves(R, outline_c, style, seed, count, size):
    lay = Canvas(); rnd = random.Random(seed)
    for _ in range(count):
        cx, cy = rnd.uniform(0, S), rnd.uniform(0, S)
        L = rnd.uniform(*size); ang = rnd.uniform(0, math.pi)
        if style == "needle":
            for k in range(5):                                            # needle sprigs
                leaf(lay, cx + math.cos(ang + k * 1.25) * L, cy + math.sin(ang + k * 1.25) * L, L, 1.1, ang + k * 1.25, R, outline_c, style)
        else:
            leaf(lay, cx, cy, L, L * (0.55 if style != "long" else 0.32), ang, R, outline_c, style if style != "long" else "leaf")
    outline(lay, color=outline_c)
    return lay

GREY = ramp((206, 206, 206), 5, hi=(255, 255, 255), lo=(70, 70, 70))
TYPES = {   # name: (style, count, size range, carried colour)
    "oak": ("leaf", 260, (5, 8), (72, 181, 24)),
    "spruce": ("needle", 150, (3.5, 5), (97, 153, 97)),
    "birch": ("leaf", 300, (4, 6.5), (128, 167, 85)),
    "jungle": ("broad", 120, (8, 12), (48, 187, 11)),
    "acacia": ("leaf", 320, (3.5, 5.5), (174, 164, 42)),
    "big_oak": ("leaf", 300, (5, 8.5), (72, 181, 24)),
}
def save_tga(im, name):
    im.save(f"{PACK}/{name}"); DONE.append(name)

for i, (name, (style, count, size, carried)) in enumerate(TYPES.items()):
    lay = leaves(GREY, (40, 40, 40), style, 800 + i, count, size)
    im = lay.im
    save_tga(im, f"leaves_{name}.tga")                                   # greyscale + see-through gaps
    C = ramp(carried, 5, hi=mix(carried, (255, 255, 220), 0.6), lo=mix(carried, (10, 30, 10), 0.7))
    col = leaves(C, mix(carried, (0, 20, 0), 0.75), style, 800 + i, count, size)
    save_tga(col.im, f"leaves_{name}_carried.tga")
    op = Image.new("RGBA", im.size, (52, 52, 52, 255)); op.alpha_composite(im)      # opaque: dark depth behind
    op.save(f"{PACK}/leaves_{name}_opaque.png"); DONE.append(f"leaves_{name}_opaque.png")

# mangrove: long leaves, greyscale (tinted); cherry: pink blossoms + petals, full colour
m = leaves(GREY, (40, 40, 40), "long", 830, 260, (6, 9))
m.save(f"{PACK}/mangrove_leaves.png"); DONE.append("mangrove_leaves.png")
PINK = ramp((246, 170, 200), 5, hi=(255, 240, 246), lo=(160, 70, 110))
ch = leaves(PINK, (130, 50, 90), "petal", 840, 300, (4, 6.5))
rnd = random.Random(841)
for _ in range(30):                                                       # yellow flower centres
    x, y = rnd.randrange(S), rnd.randrange(S)
    if ch.get(x, y)[3]: ch.put(x, y, (255, 220, 120))
ch.save(f"{PACK}/cherry_leaves.png"); DONE.append("cherry_leaves.png")
print("vanilla batch 5:", len(DONE), "textures")
