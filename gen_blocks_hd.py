"""Universe 7 texture pack, category 4: BLOCKS v2 (128x128, seamless, anime cel-shaded, high detail)."""
import math, os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import *

RP = "/home/claude/dbz/DBZ_RP"; BP = "/home/claude/dbz/DBZ_BP"
TEX = f"{RP}/textures/blocks/dbz"
os.makedirs(TEX, exist_ok=True); os.makedirs(f"{BP}/blocks", exist_ok=True)
S = 128
MADE = []
WHITE = (255, 255, 255)

def save(cv, name):
    p = f"{TEX}/{name}.png"; cv.save(p); MADE.append((p, name))

# ------------------------------------------------------------ seamless helpers
def vnoise(seed, cells):
    rnd = random.Random(seed)
    g = [[rnd.random() for _ in range(cells)] for _ in range(cells)]
    def f(x, y):
        fx, fy = (x % S) / S * cells, (y % S) / S * cells
        x0, y0 = int(fx) % cells, int(fy) % cells
        x1, y1 = (x0 + 1) % cells, (y0 + 1) % cells
        tx, ty = fx - int(fx), fy - int(fy)
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[y0][x0] + (g[y0][x1] - g[y0][x0]) * tx
        b = g[y1][x0] + (g[y1][x1] - g[y1][x0]) * tx
        return a + (b - a) * ty
    return f

def fbm(seed, octaves=((4, 0.5), (8, 0.3), (16, 0.2))):
    ns = [(vnoise(seed + i, c), w) for i, (c, w) in enumerate(octaves)]
    return lambda x, y: sum(n(x, y) * w for n, w in ns)

def wput(cv, x, y, c, a=255):
    cv.put(int(x) % S, int(y) % S, c, a)

def wd(ax, ay, bx, by):
    dx = abs(ax - bx) % S; dy = abs(ay - by) % S
    return math.hypot(min(dx, S - dx), min(dy, S - dy))

def wvec(ax, ay, bx, by):
    dx = (ax - bx + S / 2) % S - S / 2; dy = (ay - by + S / 2) % S - S / 2
    return dx, dy

def cel_light(nx, ny, nz):
    return max(0.0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2])

def slab(cv, x0, y0, w, h, R, bevel=3, grout=(0, 0, 0), sheen=True, rnd=None, vein=None, tone=0.0):
    """Anime-style stone/ceramic slab: flat cel face, bevelled rim lit top-left, crisp dark grout,
    a soft diagonal sheen band and optional veins."""
    for y in range(h):
        for x in range(w):
            X, Y = x0 + x, y0 + y
            if x == 0 or y == 0:
                wput(cv, X, Y, grout); continue
            e = min(x - 1, y - 1, w - 1 - x, h - 1 - y)
            if e < bevel:                                                  # bevel: which side are we on?
                if min(x - 1, y - 1) <= min(w - 1 - x, h - 1 - y):
                    c = R[0] if (x - 1 < y - 1 or y - 1 <= x - 1) and (x - 1 == e or y - 1 == e) else R[1]
                    c = R[0] if e == 0 else R[1]
                else:
                    c = R[4] if e == 0 else R[3]
            else:
                c = mix(R[2], R[1], tone) if tone > 0 else mix(R[2], R[3], -tone)
                if sheen:
                    d = (x + (h - y)) / (w + h)                                # diagonal sheen band
                    if 0.58 < d < 0.66 or 0.7 < d < 0.72:
                        c = mix(c, WHITE, 0.45)
                if vein and vein(X, Y):
                    c = mix(c, R[4], 0.55)
            wput(cv, X, Y, c)

def rocks(seed, count, R, outline_c, round_=1.0, crack=1.6, jitter=0.25, n=None, lip=True, lift=0.0):
    """Seamless cel-shaded boulders/plates: wrapped Voronoi cells shaded as domes (round_) or tilted plates."""
    rnd = random.Random(seed)
    pts, tries = [], 0
    min_d = S / math.sqrt(count) * 0.6                                     # keep seeds apart (no degenerate cells)
    while len(pts) < count and tries < 5000:
        tries += 1
        p_ = (rnd.uniform(0, S), rnd.uniform(0, S))
        if all(wd(p_[0], p_[1], q[0], q[1]) >= min_d for q in pts):
            pts.append(p_)
    tilt = [(rnd.uniform(-jitter, jitter), rnd.uniform(-jitter, jitter), rnd.uniform(-0.12, 0.12)) for _ in pts]
    cv = Canvas()
    for y in range(S):
        for x in range(S):
            best = sorted(((wd(x + 0.5, y + 0.5, px_, py_), i) for i, (px_, py_) in enumerate(pts)))[:2]
            (d1, i1), (d2, _) = best
            gap = d2 - d1                                                   # distance to the cell edge (approx x2)
            if gap < crack:
                cv.put(x, y, outline_c); continue
            px_, py_ = pts[i1]
            dx, dy = wvec(x + 0.5, y + 0.5, px_, py_)
            r = max(1.0, d1 + gap / 2)
            edge = min(1.0, gap / (r * 0.9))                                # 0 at edge, 1 at centre
            nx = dx / r * round_ * (1 - edge * 0.5) + tilt[i1][0]
            ny = dy / r * round_ * (1 - edge * 0.5) + tilt[i1][1]
            nz = math.sqrt(max(0.05, 1 - min(0.95, nx * nx + ny * ny)))
            L = cel_light(nx, ny, nz) + tilt[i1][2] + (n(x, y) - 0.5) * 0.18 if n else cel_light(nx, ny, nz) + tilt[i1][2]
            c = band(R, L * 1.05 + lift)
            if lip and gap < crack + 1.4:
                c = R[0] if nx + ny < -0.05 else R[min(len(R) - 1, 4)]      # crisp rim light / rim shadow
            cv.put(x, y, c)
    return cv, pts

def tuft(cv, x, y, h, R, outline_c, rnd, blades=5, lean=0.0):
    """Anime grass tuft: pointed blades, lit left faces, shadowed right faces, dark outline."""
    lay = Canvas()
    for b in range(blades):
        bx = x + (b - blades / 2) * 2.2 + rnd.uniform(-0.6, 0.6)
        bh = h * rnd.uniform(0.6, 1.0)
        ang = lean + (b - blades / 2) * 0.18 + rnd.uniform(-0.1, 0.1)
        tip = (bx + math.sin(ang) * bh, y - math.cos(ang) * bh)
        w = 2.4
        for t in range(int(bh * 2)):
            k = t / (bh * 2)
            cx = bx + (tip[0] - bx) * k; cy = y + (tip[1] - y) * k
            half = w * (1 - k)
            for o in range(-int(half + 0.5), int(half + 0.5) + 1):
                c = R[0] if o < 0 and k > 0.25 else R[1] if o <= 0 else R[3]
                if k > 0.85:
                    c = R[0]
                lay.put(int(cx + o) % S, int(cy) % S, c)
    outline(lay, color=outline_c)
    # wrap-safe paste
    for yy in range(S):
        for xx in range(S):
            p = lay.get(xx, yy)
            if p[3]:
                cv.put(xx, yy, p[:3])

def slab(cv, x0, y0, w, h, R, bevel=3, grout=(0, 0, 0), sheen=0.45, vein=None, tone=0.0, bands=None):
    """Anime slab: flat cel face, bevel lit top-left / shadowed bottom-right, crisp grout, sheen band."""
    for y in range(h):
        for x in range(w):
            X, Y = x0 + x, y0 + y
            if x == 0 or y == 0:
                wput(cv, X, Y, grout); continue
            tl = min(x - 1, y - 1); br = min(w - 1 - x, h - 1 - y)
            if tl < bevel and tl <= br:
                c = R[0] if tl == 0 else R[1]
            elif br < bevel:
                c = R[4] if br == 0 else R[3]
            else:
                c = R[2]
                if tone:
                    c = mix(c, R[1] if tone > 0 else R[3], abs(tone))
                if bands:                                                   # soft cel gradient: lighter towards top-left
                    k = (x + y) / (w + h)
                    if k < 0.33: c = mix(c, R[1], 0.5)
                if sheen:
                    d = (x + (h - y)) / (w + h)
                    if 0.56 < d < 0.63 or 0.67 < d < 0.69:
                        c = mix(c, WHITE, sheen)
                if vein and vein(X, Y):
                    c = mix(c, R[4], 0.45)
            wput(cv, X, Y, c)

def pebble(cv, x, y, rx, ry, R, outline_c):
    lay = Canvas()
    ellipsoid(lay, 64, 64, rx, ry, R, rot=0.3)
    soft = lay.get(int(64 - rx * 0.3), int(64 - ry * 0.4))
    outline(lay, color=outline_c)
    for yy in range(int(64 - ry - 2), int(64 + ry + 3)):
        for xx in range(int(64 - rx - 2), int(64 + rx + 3)):
            p = lay.get(xx, yy)
            if p[3]:
                wput(cv, x + xx - 64, y + yy - 64, p[:3])
    wput(cv, x - rx * 0.35, y - ry * 0.45, WHITE, 200)                     # glint

# ============================================================ Capsule Corp-style floor
FL = ramp((222, 228, 238), 5, hi=(255, 255, 255), lo=(110, 124, 160))
cv = Canvas(); rnd = random.Random(1)
for ty in (0, 64):
    for tx in (0, 64):
        slab(cv, tx, ty, 64, 64, FL, bevel=3, grout=(58, 80, 124), sheen=0.5, tone=rnd.uniform(-0.15, 0.15), bands=True)
        for i in range(8, 20):                                             # sharp anime reflection glints
            wput(cv, tx + 10 + i, ty + 30 - i, WHITE); wput(cv, tx + 11 + i, ty + 30 - i, WHITE, 150)
for gx in (0, 64):                                                         # light-blue inner grout line + chrome caps
    for i in range(S):
        wput(cv, gx + 1, i, (150, 196, 240), 150); wput(cv, i, gx + 1, (150, 196, 240), 150)
for (cx, cy) in ((0, 0), (64, 0), (0, 64), (64, 64)):
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if dx * dx + dy * dy <= 9:
                c = band(ramp((200, 206, 220), 4, hi=WHITE), cel_light(dx / 3, dy / 3, 0.6))
                wput(cv, cx + dx, cy + dy, c)
    wput(cv, cx - 1, cy - 1, WHITE)
save(cv, "capsule_floor")

# ============================================================ Capsule Corp-style wall
WL = ramp((238, 236, 230), 5, hi=WHITE, lo=(120, 124, 140))
NAVY = ramp((44, 64, 120), 5, hi=(140, 170, 230), lo=(10, 16, 40))
YEL = ramp((250, 196, 50), 5, hi=(255, 248, 190), lo=(140, 80, 10))
cv = Canvas(); rnd = random.Random(2)
for ty in (0, 72):
    for tx in (0, 64):
        slab(cv, tx, ty, 64, 56, WL, bevel=3, grout=(90, 96, 120), sheen=0.35, tone=rnd.uniform(-0.1, 0.1), bands=True)
for y in range(56, 72):                                                    # navy structural band with gold pinstripes
    for x in range(S):
        k = y - 56
        c = NAVY[0] if k == 0 else NAVY[1] if k < 3 else NAVY[2] if k < 12 else NAVY[3] if k < 15 else NAVY[4]
        if k in (5, 10):
            c = YEL[1] if (x // 2) % 2 == 0 else YEL[2]
        cv.put(x, y, c)
for x in range(4, S, 32):                                                  # band bolts
    sphere(cv, x + 12, 63, 2.2, ramp((200, 206, 220), 4, hi=WHITE))
for tx in (0, 64):                                                         # vent grilles on the lower panels
    for k in range(5):
        y = 86 + k * 6
        for x in range(tx + 14, tx + 50):
            cv.put(x, y, WL[4]); cv.put(x, y + 1, WL[3]); cv.put(x, y + 2, WL[0])
    for (rx, ry) in ((6, 78), (57, 78), (6, 121), (57, 121), (6, 6), (57, 6), (6, 49), (57, 49)):
        sphere(cv, tx + rx, ry, 1.8, ramp((200, 206, 220), 4, hi=WHITE))
for tx in (0, 64):                                                         # status light and access panel on the upper panels
    for y in range(14, 40):
        for x in range(tx + 40, tx + 54):
            e = min(x - tx - 40, y - 14, tx + 53 - x, 39 - y)
            cv.put(x, y, WL[4] if e == 0 else WL[3] if e == 1 else WL[2])
    sphere(cv, tx + 47, 20, 2.6, ramp((90, 230, 140), 4, hi=WHITE))
    for y in (28, 31, 34):
        for x in range(tx + 43, tx + 52):
            cv.put(x, y, WL[4])
save(cv, "capsule_wall")

# ============================================================ Lookout tile (pale temple stone)
ST = ramp((234, 230, 218), 5, hi=WHITE, lo=(130, 122, 110))
cv = Canvas(); rnd = random.Random(3); vn = fbm(30, ((8, 0.6), (16, 0.4)))
vein = lambda x, y: abs(vn(x, y) - 0.5) < 0.012                            # thin marble veins
for row, ty in enumerate((0, 32, 64, 96)):
    off = 0 if row % 2 == 0 else 32
    for tx in (0, 64):
        slab(cv, tx + off, ty, 64, 32, ST, bevel=2, grout=(150, 140, 122), sheen=0.3, vein=vein, tone=rnd.uniform(-0.2, 0.2), bands=True)
for _ in range(40):                                                        # tiny weathering chips
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, ST[3]); wput(cv, x + 1, y, ST[1])
GO = ramp((236, 180, 60), 5, hi=(255, 248, 200), lo=(110, 60, 10))
for (cx, cy) in ((0, 0), (64, 64)):                                        # small gold inlaid medallions at a few corners
    for dy in range(-5, 6):
        for dx in range(-5, 6):
            d = abs(dx) + abs(dy)
            if d <= 5:
                wput(cv, cx + dx, cy + dy, band(GO, cel_light(dx / 5, dy / 5, 0.7)) if d < 5 else GO[4])
    wput(cv, cx - 1, cy - 2, WHITE)
save(cv, "lookout_tile")

# ============================================================ Hyperbolic Time Chamber floor (animated 4 frames)
TC = ramp((244, 246, 252), 5, hi=WHITE, lo=(200, 206, 228))
frames = []
for f in range(4):
    cv = Canvas()
    for ty in (0, 64):
        for tx in (0, 64):
            slab(cv, tx, ty, 64, 64, TC, bevel=2, grout=(214, 220, 238), sheen=0)
    for y in range(S):                                                     # pearly light band sweeping across
        for x in range(S):
            ph = ((x + y) / S + f / 4) % 1
            k = math.exp(-((ph - 0.5) / 0.08) ** 2)
            if k > 0.05:
                cv.put(x, y, (255, 255, 255), int(180 * k))
            k2 = math.exp(-((ph - 0.62) / 0.02) ** 2)
            if k2 > 0.3:
                cv.put(x, y, (226, 236, 255), int(120 * k2))
    rnd = random.Random(40 + f)
    for _ in range(6):                                                     # twinkles
        x, y = rnd.randrange(S), rnd.randrange(S)
        for dx, dy, a in ((0, 0, 255), (1, 0, 140), (-1, 0, 140), (0, 1, 140), (0, -1, 140)):
            wput(cv, x + dx, y + dy, (200, 220, 255), a)
    frames.append(cv)
anim = Canvas(S, S * 4)
for i, fr in enumerate(frames):
    anim.paste(fr, 0, i * S)
save(anim, "time_chamber_floor")

# ============================================================ Namek grass / dirt / stone
NG = ramp((84, 196, 160), 5, hi=(214, 255, 226), lo=(14, 70, 76))
NGO = (16, 62, 64)
SOIL = ramp((210, 192, 132), 5, hi=(255, 246, 206), lo=(96, 80, 60))
SOILO = (82, 66, 50)

def grass_base(seed):
    cv = Canvas(); n = fbm(seed)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, NG[1] if v > 0.62 else NG[2] if v > 0.42 else NG[3])   # flat anime colour patches
    return cv

def grass_top():
    cv = grass_base(50); rnd = random.Random(51)
    for _ in range(70):                                                    # tufts all over
        tuft(cv, rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(6, 10), NG, NGO, rnd, blades=rnd.randint(3, 5), lean=rnd.uniform(-0.4, 0.4))
    for _ in range(9):                                                     # little blue-and-white Namek flowers
        x, y = rnd.randrange(S), rnd.randrange(S)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            wput(cv, x + dx, y + dy, (170, 220, 255)); wput(cv, x + dx * 2, y + dy * 2, NGO)
        wput(cv, x, y, (255, 240, 140))
    return cv

def soil(seed, pebbles=34):
    cv = Canvas(); n = fbm(seed); rnd = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, SOIL[1] if v > 0.64 else SOIL[2] if v > 0.4 else SOIL[3])
    for _ in range(pebbles):
        pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(2, 4.5), rnd.uniform(1.6, 3.2),
               ramp((176, 186, 170), 4, hi=WHITE, lo=(70, 76, 70)), (60, 60, 54))
    for _ in range(120):                                                   # grit
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, SOIL[4] if rnd.random() < 0.5 else SOIL[0])
    return cv

save(grass_top(), "namek_grass_top")
save(soil(60), "namek_dirt")
cv = soil(60); top = grass_base(50); rnd = random.Random(62)
for x in range(S):                                                         # grass cap across the top
    depth = 18 + int(4 * math.sin(x / S * 2 * math.pi * 2))
    for y in range(depth):
        cv.put(x, y, top.get(x, y))
for _ in range(34):                                                        # hanging tufts along the edge
    x = rnd.uniform(0, S); d = 18 + 4 * math.sin(x / S * 2 * math.pi * 2)
    tuft(cv, x, d - 3, rnd.uniform(7, 13), NG, NGO, rnd, blades=rnd.randint(3, 5), lean=math.pi + rnd.uniform(-0.3, 0.3))
for _ in range(20):                                                        # upright tufts on top
    tuft(cv, rnd.uniform(0, S), 10, rnd.uniform(5, 9), NG, NGO, rnd, blades=3)
for x in range(S):
    cv.put(x, 0, NG[1])
save(cv, "namek_grass_side")

NS = ramp((116, 176, 168), 5, hi=(226, 255, 246), lo=(24, 56, 66))
cv, _ = rocks(70, 13, NS, (14, 40, 48), round_=0.95, crack=1.7, jitter=0.15, n=fbm(71))
rnd = random.Random(72)
for _ in range(10):                                                        # hairline fractures + moss spots
    x, y, a = rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(0, 6.28)
    for _ in range(rnd.randint(5, 10)):
        a += rnd.uniform(-0.5, 0.5); x += math.cos(a); y += math.sin(a)
        wput(cv, x, y, NS[4])
for _ in range(16):
    x, y = rnd.randrange(S), rnd.randrange(S)
    for dx, dy in ((0, 0), (1, 0), (0, 1)):
        wput(cv, x + dx, y + dy, NG[1] if (dx + dy) else NG[2])
save(cv, "namek_stone")

# ============================================================ Cracked battle ground
RK = ramp((186, 160, 120), 5, hi=(255, 240, 206), lo=(70, 50, 40))
cv, pts = rocks(80, 15, RK, (40, 26, 22), round_=0.3, crack=2.2, jitter=0.3, n=fbm(81), lift=0.18)
rnd = random.Random(82)
for _ in range(14):                                                        # loose rubble chunks
    pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(2, 4), rnd.uniform(1.5, 3), RK, (40, 26, 22))
for _ in range(3):                                                         # soft scorch smudges from ki blasts
    cx, cy, r = rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(8, 13)
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r), int(cx + r) + 1):
            d = math.hypot(x - cx, y - cy) / r
            if d < 1:
                wput(cv, x, y, (60, 42, 34), int(90 * (1 - d) ** 1.5))
for _ in range(160):                                                       # dust grit
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, RK[0] if rnd.random() < 0.4 else RK[3], 200)
save(cv, "cracked_ground")

# ============================================================ RP: terrain_texture.json, flipbook_textures.json, blocks.json
tt_path = f"{RP}/textures/terrain_texture.json"
tt = json.load(open(tt_path))
for name in ("capsule_floor", "capsule_wall", "lookout_tile", "time_chamber_floor", "namek_grass_top",
             "namek_grass_side", "namek_dirt", "namek_stone", "cracked_ground"):
    tt["texture_data"][f"dbz_{name}"] = {"textures": f"textures/blocks/dbz/{name}"}
json.dump(tt, open(tt_path, "w"), indent=2)
json.dump([{"flipbook_texture": "textures/blocks/dbz/time_chamber_floor", "atlas_tile": "dbz_time_chamber_floor",
            "ticks_per_frame": 10, "blend_frames": True}], open(f"{RP}/textures/flipbook_textures.json", "w"), indent=2)

BLOCKS = {  # id: (name, textures, sound, seconds, category, map colour)
    "capsule_floor": ("Capsule Corp Floor", "dbz_capsule_floor", "stone", 1.5, "construction", "#e2e6ee"),
    "capsule_wall": ("Capsule Corp Wall", "dbz_capsule_wall", "stone", 1.5, "construction", "#ece8de"),
    "lookout_tile": ("Lookout Tile", "dbz_lookout_tile", "stone", 1.5, "construction", "#e8dec4"),
    "time_chamber_floor": ("Time Chamber Floor", "dbz_time_chamber_floor", "stone", 2.5, "construction", "#f4f6fc"),
    "namek_grass": ("Namek Grass", {"up": "dbz_namek_grass_top", "down": "dbz_namek_dirt", "*": "dbz_namek_grass_side"},
                    "grass", 0.6, "nature", "#46aa96"),
    "namek_dirt": ("Namek Dirt", "dbz_namek_dirt", "gravel", 0.5, "nature", "#968c6e"),
    "namek_stone": ("Namek Stone", "dbz_namek_stone", "stone", 1.5, "nature", "#6ea096"),
    "cracked_ground": ("Cracked Battle Ground", "dbz_cracked_ground", "gravel", 0.8, "nature", "#786e64"),
}
blocks_json = {"format_version": [1, 1, 0]}
lang = []
for bid, (name, tex, sound, secs, cat, col) in BLOCKS.items():
    mats = {k: {"texture": v, "render_method": "opaque"} for k, v in (tex.items() if isinstance(tex, dict) else {"*": tex}.items())}
    json.dump({"format_version": "1.21.60", "minecraft:block": {
        "description": {"identifier": f"dbz:{bid}", "menu_category": {"category": cat}},
        "components": {
            "minecraft:geometry": "minecraft:geometry.full_block",
            "minecraft:material_instances": mats,
            "minecraft:destructible_by_mining": {"seconds_to_destroy": secs},
            "minecraft:destructible_by_explosion": {"explosion_resistance": 6 if cat == "construction" else 3},
            "minecraft:map_color": col,
            "minecraft:display_name": f"tile.dbz:{bid}.name"}}}, open(f"{BP}/blocks/{bid}.json", "w"), indent=2)
    blocks_json[f"dbz:{bid}"] = {"sound": sound}
    lang.append(f"tile.dbz:{bid}.name={name}")
json.dump(blocks_json, open(f"{RP}/blocks.json", "w"), indent=2)
lp = f"{RP}/texts/en_US.lang"
cur = open(lp).read().splitlines()
cur = [l for l in cur if not any(l.startswith(f"tile.dbz:{b}.") for b in BLOCKS)]
open(lp, "w").write("\n".join(cur + lang) + "\n")
print(f"blocks: {len(MADE)} textures, {len(BLOCKS)} blocks")
