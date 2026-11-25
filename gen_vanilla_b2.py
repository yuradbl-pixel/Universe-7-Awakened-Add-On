"""Universe 7: Anime Textures - vanilla batch 2: the 8 stone ores + deepslate (side and top)."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *
from PIL import Image

PACK = "/home/claude/u7_textures/textures/blocks"
os.makedirs(f"{PACK}/deepslate", exist_ok=True)
DONE = []
def vsave(cv, name):
    cv.save(f"{PACK}/{name}"); DONE.append(name)

def base_from(path):
    cv = Canvas(); cv.paste(Image.open(path).convert("RGBA")); return cv

# ------------------------------------------------------------ ore pieces
def gem(cv, cx, cy, r, R, outline_c, rot=0.0):
    """Faceted gem: 4-6 flat facets, lit top-left, crisp outline, white glint."""
    lay = Canvas()
    pts = [(64 + r * math.cos(rot + k * math.pi / 3) * (1.0 if k % 3 else 1.25), 64 + r * math.sin(rot + k * math.pi / 3)) for k in range(6)]
    ins = poly_inside(pts)
    for y in range(int(64 - r * 1.4), int(64 + r * 1.4) + 1):
        for x in range(int(64 - r * 1.4), int(64 + r * 1.4) + 1):
            if ins(x + 0.5, y + 0.5):
                a = math.atan2(y - 64, x - 64)
                facet = int(((a - rot) % (2 * math.pi)) / (math.pi / 3))
                L = [0.55, 0.3, 0.2, 0.45, 0.8, 0.95][facet]                     # top-left facets brightest
                if math.hypot(x - 64, y - 64) < r * 0.42:
                    L = 0.75                                                     # table facet
                lay.put(x, y, band(R, L))
    outline(lay, color=outline_c)
    for y in range(lay.h):
        for x in range(lay.w):
            p = lay.get(x, y)
            if p[3]: wput(cv, cx + x - 64, cy + y - 64, p[:3])
    wput(cv, cx - r * 0.35, cy - r * 0.4, WHITE); wput(cv, cx - r * 0.35 + 1, cy - r * 0.4, WHITE, 140)

def nugget(cv, cx, cy, rx, ry, R, outline_c):
    pebble(cv, cx, cy, rx, ry, R, outline_c)

def ore(stone, kind, seed):
    cv = base_from(stone); rnd = random.Random(seed)
    spec = ORES[kind]
    cells = [(gx, gy) for gx in range(3) for gy in range(3)]                # spread clusters over a 3x3 grid
    rnd.shuffle(cells)
    clusters = [(16 + gx * 42 + rnd.uniform(-6, 10), 16 + gy * 42 + rnd.uniform(-6, 10)) for gx, gy in cells[:spec["clusters"]]]
    for (cx, cy) in clusters:
        for _ in range(rnd.randint(2, 4)):
            x, y = cx + rnd.uniform(-9, 9), cy + rnd.uniform(-9, 9)
            s = rnd.uniform(*spec["size"]) * 1.3
            if spec["shape"] == "gem":
                gem(cv, x, y, s, spec["ramp"], spec["out"], rot=rnd.uniform(0, 1))
            else:
                nugget(cv, x, y, s, s * rnd.uniform(0.65, 0.9), spec["ramp"], spec["out"])
        if spec.get("extra"):
            spec["extra"](cv, cx, cy, rnd)
    for (cx, cy) in clusters[:3]:                                          # sparkles near the richest clusters
        if spec.get("sparkle"):
            sx, sy = int(cx + rnd.uniform(-8, 8)) % S, int(cy + rnd.uniform(-8, 8)) % S
            sparkle(cv, sx, sy, 2, spec["sparkle"])
    return cv

def copper_patina(cv, cx, cy, rnd):
    for _ in range(4):
        x, y = cx + rnd.uniform(-8, 8), cy + rnd.uniform(-8, 8)
        wput(cv, x, y, (80, 200, 170)); wput(cv, x + 1, y, (50, 150, 130))

def lapis_flecks(cv, cx, cy, rnd):
    for _ in range(5):
        x, y = cx + rnd.uniform(-9, 9), cy + rnd.uniform(-9, 9)
        wput(cv, x, y, (255, 220, 90))

def redstone_glow(cv, cx, cy, rnd):
    for _ in range(6):
        x, y = cx + rnd.uniform(-11, 11), cy + rnd.uniform(-11, 11)
        wput(cv, x, y, (255, 80, 60), 170)

ORES = {
    "coal": {"shape": "gem", "ramp": ramp((60, 60, 70), 5, hi=(170, 176, 200), lo=(6, 6, 10)), "out": (6, 6, 10), "size": (4, 6.5), "clusters": 6, "sparkle": (200, 210, 230)},
    "iron": {"shape": "nug", "ramp": ramp((222, 170, 140), 5, hi=(255, 240, 225), lo=(110, 70, 60)), "out": (70, 44, 38), "size": (3.2, 5.2), "clusters": 6},
    "copper": {"shape": "nug", "ramp": ramp((230, 120, 70), 5, hi=(255, 220, 180), lo=(110, 40, 20)), "out": (80, 34, 20), "size": (3.2, 5.2), "clusters": 6, "extra": copper_patina},
    "gold": {"shape": "nug", "ramp": ramp((255, 210, 50), 5, hi=(255, 252, 210), lo=(140, 80, 10)), "out": (110, 60, 10), "size": (3.2, 5.0), "clusters": 5, "sparkle": (255, 250, 200)},
    "redstone": {"shape": "gem", "ramp": ramp((240, 40, 40), 5, hi=(255, 190, 170), lo=(100, 0, 10)), "out": (80, 0, 10), "size": (3.0, 4.6), "clusters": 6, "extra": redstone_glow, "sparkle": (255, 200, 190)},
    "lapis": {"shape": "nug", "ramp": ramp((50, 90, 220), 5, hi=(190, 210, 255), lo=(10, 20, 80)), "out": (8, 16, 60), "size": (3.0, 4.8), "clusters": 6, "extra": lapis_flecks},
    "diamond": {"shape": "gem", "ramp": ramp((90, 230, 230), 5, hi=(240, 255, 255), lo=(10, 90, 110)), "out": (6, 60, 80), "size": (4.2, 6.5), "clusters": 4, "sparkle": WHITE},
    "emerald": {"shape": "gem", "ramp": ramp((50, 210, 100), 5, hi=(210, 255, 220), lo=(0, 80, 40)), "out": (0, 60, 30), "size": (4.2, 6.0), "clusters": 3, "sparkle": WHITE},
}
STONE = f"{PACK}/stone.png"
for i, k in enumerate(ORES):
    vsave(ore(STONE, k, 300 + i), f"{k}_ore.png")

# ------------------------------------------------------------ deepslate (layered, chiselled dark slate)
DS = ramp((76, 78, 92), 5, hi=(176, 180, 200), lo=(18, 18, 26))
def deepslate_side():
    cv = Canvas(); n = fbm(400, ((4, 0.4), (16, 0.6))); rnd = random.Random(401)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            k = (y + int(6 * n(x, y))) % 16
            c = DS[1] if v > 0.62 else DS[2] if v > 0.4 else DS[3]
            if k == 0: c = DS[4]                                          # layer split
            elif k == 1: c = mix(c, DS[0], 0.4)                           # lit lip under the split
            cv.put(x, y, c)
    for _ in range(14):                                                    # chisel chips
        x, y = rnd.randrange(S), rnd.randrange(S)
        for dx in range(rnd.randint(3, 7)):
            wput(cv, x + dx, y, DS[4]); wput(cv, x + dx, y + 1, DS[1])
    for _ in range(160):
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, DS[0] if rnd.random() < 0.3 else DS[4])
    return cv

def deepslate_top():
    cv, _ = rocks(410, 10, DS, (14, 14, 20), round_=0.4, crack=1.4, jitter=0.3, n=fbm(411), lift=0.05)
    rnd = random.Random(412)
    for _ in range(140):
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, DS[0] if rnd.random() < 0.3 else DS[4])
    return cv

ds = deepslate_side(); vsave(ds, "deepslate/deepslate.png")
vsave(deepslate_top(), "deepslate/deepslate_top.png")
print("vanilla batch 2:", DONE)
