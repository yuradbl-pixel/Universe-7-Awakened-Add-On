"""Texture pack batch 2: Kame House wood, King Kai's planet grass, wasteland stone, Shenron altar,
plus the 3D model textures for the wearable Saiyan Armor and Weighted Training Gi."""
import math, os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *

MODELS = f"{RP}/textures/models/dbz"
os.makedirs(MODELS, exist_ok=True)
def save(cv, name, folder=TEX):
    p = f"{folder}/{name}.png"; cv.save(p); MADE.append((p, name))

# ============================================================ Kame House wood planks
WOOD = ramp((196, 132, 74), 5, hi=(255, 226, 170), lo=(70, 36, 24))
def planks(paint=None, seed=1):
    cv = Canvas(); rnd = random.Random(seed); gn = fbm(seed + 10, ((2, 0.5), (16, 0.5)))
    R = paint or WOOD
    for row in range(8):                                                   # 8 boards, 16 px tall
        y0 = row * 16
        cut = rnd.randrange(S)                                             # staggered end joint
        tone = rnd.uniform(-0.18, 0.18)
        for y in range(16):
            for x in range(S):
                X, Y = x, y0 + y
                if y == 0:
                    c = R[4]                                               # gap between boards
                elif y == 1:
                    c = R[0]                                               # lit top edge
                elif y >= 14:
                    c = R[3]                                               # shadowed lower edge
                else:
                    c = mix(R[2], R[1] if tone > 0 else R[3], abs(tone))
                    g = gn(x, row * 16)                                    # slow wobble along the board
                    gv = math.sin(y * 1.25 + g * 9 + row * 2)
                    if not paint and abs(gv) < 0.22:
                        c = mix(c, R[3], 0.65)                               # dark grain line
                    elif not paint and 0.9 < gv:
                        c = mix(c, R[1], 0.35)                               # light grain
                    if paint and rnd.random() < 0.004:
                        c = WOOD[2]                                        # paint chip showing wood
                if (x - cut) % S in (0,):
                    c = R[4]
                if (x - cut) % S in (1,):
                    c = R[0] if 1 < y < 14 else c
                cv.put(X, Y, c)
        for nx in ((cut + 4) % S, (cut - 5) % S):                          # nail heads by the joint
            for ny in (y0 + 5, y0 + 10):
                cv.put(nx, ny, (70, 70, 80)); cv.put(nx, ny - 1, (200, 200, 210))
        if not paint and rnd.random() < 0.6:                               # a knot
            kx, ky = rnd.randrange(S), y0 + rnd.randint(5, 10)
            for dy in range(-2, 3):
                for dx in range(-4, 5):
                    d = (dx / 4) ** 2 + (dy / 2) ** 2
                    if d <= 1:
                        wput(cv, kx + dx, ky + dy, R[4] if d < 0.35 else R[3])
            wput(cv, kx - 1, ky - 1, R[1])
    return cv

save(planks(), "kame_house_wood")
PINK = ramp((240, 140, 168), 5, hi=(255, 232, 240), lo=(110, 40, 70))
cv = planks(PINK, 2)
save(cv, "kame_house_wall")

# ============================================================ King Kai's planet grass
KG = ramp((110, 210, 70), 5, hi=(236, 255, 180), lo=(20, 80, 30))
KGO = (24, 70, 26)
KS = ramp((170, 104, 70), 5, hi=(240, 196, 150), lo=(60, 30, 26))
def kk_base(seed):
    cv = Canvas(); n = fbm(seed)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, KG[1] if v > 0.62 else KG[2] if v > 0.42 else KG[3])
    return cv

cv = kk_base(90); rnd = random.Random(91)
for _ in range(80):
    tuft(cv, rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(6, 10), KG, KGO, rnd, blades=rnd.randint(3, 5), lean=rnd.uniform(-0.4, 0.4))
for _ in range(10):                                                        # little yellow flowers
    x, y = rnd.randrange(S), rnd.randrange(S)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        wput(cv, x + dx, y + dy, (255, 236, 90)); wput(cv, x + dx * 2, y + dy * 2, KGO)
    wput(cv, x, y, (255, 150, 40))
save(cv, "king_kai_grass_top")

def kk_soil(seed):
    cv = Canvas(); n = fbm(seed); rnd = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, KS[1] if v > 0.64 else KS[2] if v > 0.4 else KS[3])
    for _ in range(30):
        pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(2, 4), rnd.uniform(1.6, 3), ramp((190, 150, 120), 4, hi=WHITE), (60, 34, 26))
    for _ in range(120):
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, KS[4] if rnd.random() < 0.5 else KS[0])
    return cv

save(kk_soil(92), "king_kai_dirt")
cv = kk_soil(92); top = kk_base(90); rnd = random.Random(93)
for x in range(S):
    depth = 18 + int(4 * math.sin(x / S * 2 * math.pi * 2))
    for y in range(depth):
        cv.put(x, y, top.get(x, y))
for _ in range(34):
    x = rnd.uniform(0, S); d = 18 + 4 * math.sin(x / S * 2 * math.pi * 2)
    tuft(cv, x, d - 3, rnd.uniform(7, 13), KG, KGO, rnd, blades=rnd.randint(3, 5), lean=math.pi + rnd.uniform(-0.3, 0.3))
for _ in range(20):
    tuft(cv, rnd.uniform(0, S), 10, rnd.uniform(5, 9), KG, KGO, rnd, blades=3)
for x in range(S):
    cv.put(x, 0, KG[1])
save(cv, "king_kai_grass_side")

# ============================================================ Rocky wasteland stone (layered mesa rock)
WS = ramp((214, 150, 96), 6, hi=(255, 232, 190), lo=(80, 40, 30))
cv = Canvas(); n = fbm(100); rnd = random.Random(101)
LAYERS = [(0, 22, 0.15), (22, 40, -0.1), (40, 64, 0.05), (64, 80, -0.2), (80, 104, 0.12), (104, 128, -0.05)]
for y in range(S):
    for x in range(S):
        wob = int(3 * math.sin(x / S * 2 * math.pi * 2 + y * 0.05) + 2 * (n(x, y) - 0.5) * 4)
        yy = (y + wob) % S
        for (a, b, tone) in LAYERS:
            if a <= yy < b:
                k = (yy - a) / (b - a)
                c = WS[1] if k < 0.15 else WS[2] if k < 0.75 else WS[3]     # each ledge: lit top, mid, shaded underside
                if k > 0.92:
                    c = WS[5]                                               # dark undercut line
                c = mix(c, WS[1] if tone > 0 else WS[4], abs(tone))
                if n(x * 2 % S, yy) > 0.66 and 0.2 < k < 0.8:
                    c = mix(c, WS[0], 0.3)                                  # sandy speckle
                cv.put(x, y, c)
                break
for _ in range(9):                                                          # vertical weathering cracks
    x, y = rnd.uniform(0, S), rnd.uniform(0, S)
    for i in range(rnd.randint(8, 18)):
        x += rnd.uniform(-0.6, 0.6); y += 1
        wput(cv, x, y, WS[5]); wput(cv, x + 1, y, WS[0], 140)
for _ in range(20):
    pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(1.5, 3), rnd.uniform(1.2, 2.4), WS, (70, 36, 26))
save(cv, "wasteland_stone")

# ============================================================ Shenron summoning altar (top + side)
AS = ramp((96, 120, 110), 6, hi=(220, 236, 220), lo=(16, 26, 26))
GOLD = ramp((236, 176, 50), 5, hi=(255, 248, 200), lo=(110, 60, 10))
ORB = ramp((255, 150, 40), 5, hi=(255, 248, 210), lo=(150, 50, 10))
def stone_base(seed):
    cv = Canvas(); n = fbm(seed)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, AS[1] if v > 0.64 else AS[2] if v > 0.4 else AS[3])
    return cv

def frame_border(cv):
    for i in range(S):
        for t, c in ((0, AS[5]), (1, GOLD[0]), (2, GOLD[1]), (3, GOLD[2]), (4, GOLD[4]), (5, AS[4])):
            for (x, y) in ((i, t), (t, i), (i, S - 1 - t), (S - 1 - t, i)):
                if c in (GOLD[0], GOLD[1]) and (x == S - 1 - t or y == S - 1 - t):
                    c2 = GOLD[3]                                           # bottom/right trim in shadow
                else:
                    c2 = c
                cv.put(x, y, c2)

cv = stone_base(110); frame_border(cv)
for y in range(S):                                                          # carved summoning circle
    for x in range(S):
        d = math.hypot(x + 0.5 - 64, y + 0.5 - 64)
        if 44 <= d <= 47: cv.put(x, y, GOLD[1] if y < 64 else GOLD[3])
        elif 47 < d <= 48.5: cv.put(x, y, AS[5])
        elif 24 <= d <= 25.5: cv.put(x, y, GOLD[2])
for k in range(7):                                                          # seven glowing star sockets
    a = math.radians(-90 + k * 360 / 7)
    sx, sy = 64 + 35 * math.cos(a), 64 + 35 * math.sin(a)
    for y in range(int(sy) - 8, int(sy) + 9):
        for x in range(int(sx) - 8, int(sx) + 9):
            if math.hypot(x - sx, y - sy) <= 7.5: cv.put(x, y, AS[5])
    sphere(cv, sx, sy, 6, ORB, gamma=0.8)
    ins = poly_inside(star_poly(sx, sy + 0.5, 3.2, 1.4))
    for y in range(int(sy) - 4, int(sy) + 5):
        for x in range(int(sx) - 4, int(sx) + 5):
            if ins(x + 0.5, y + 0.5): cv.put(x, y, (210, 30, 30))
    cv.put(int(sx) - 3, int(sy) - 3, WHITE)
for a in range(0, 360, 30):                                                 # central sunburst emblem
    axis_shape(cv, (64 + 6 * math.cos(math.radians(a)), 64 + 6 * math.sin(math.radians(a))),
               (64 + 20 * math.cos(math.radians(a)), 64 + 20 * math.sin(math.radians(a))),
               lambda t: 2.6 * (1 - t) + 0.4, lambda t, s: band(GOLD, 0.8 - t * 0.5 - s * 0.15))
sphere(cv, 64, 64, 7, GOLD); cv.put(61, 61, WHITE)
for (cx, cy) in ((14, 14), (113, 14), (14, 113), (113, 113)):               # corner studs
    sphere(cv, cx, cy, 4, GOLD); cv.put(cx - 1, cy - 2, WHITE)
save(cv, "shenron_altar_top")

cv = stone_base(120); frame_border(cv)
for y in range(52, 60):                                                     # gold band across the middle
    for x in range(6, S - 6):
        cv.put(x, y, GOLD[0] if y == 52 else GOLD[1] if y < 55 else GOLD[2] if y < 58 else GOLD[4])
for x in range(10, S - 10, 12):
    sphere(cv, x + 4, 56, 2, ramp((255, 150, 40), 4, hi=WHITE))
for (cy, flip) in ((28, 1), (88, -1)):                                      # carved cloud-scroll reliefs
    for k in range(4):
        cx = 22 + k * 28
        for a in range(0, 300, 3):
            r = 8 * (1 - a / 400)
            x = cx + r * math.cos(math.radians(a * flip)); y = cy + r * math.sin(math.radians(a * flip))
            cv.put(int(x), int(y), AS[5]); cv.put(int(x) - 1, int(y) - 1, AS[0])
sphere(cv, 64, 56, 11, ORB, gamma=0.8)                                       # orange orb emblem on the band
ins = poly_inside(star_poly(64, 56.5, 5.5, 2.3))
for y in range(48, 64):
    for x in range(56, 73):
        if ins(x + 0.5, y + 0.5): cv.put(x, y, (210, 30, 30))
soft_spot(cv, 60, 51, 4, 3, WHITE, 220)
save(cv, "shenron_altar_side")

# ============================================================ Saiyan Armor model texture (64x64 layout drawn at 128)
def box_faces(u, v, w, h, d):
    """Bedrock box-UV face rectangles (in 64-scale units)."""
    return {"top": (u + d, v, w, d), "bottom": (u + d + w, v, w, d), "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h), "left": (u + d + w, v + d, d, h), "back": (u + 2 * d + w, v + d, w, h)}

def paint_face(cv, rect, fn):
    u, v, w, h = rect
    for y in range(v * 2, (v + h) * 2):
        for x in range(u * 2, (u + w) * 2):
            c = fn((x - u * 2) / (w * 2), (y - v * 2) / (h * 2))           # 0..1 face-local
            if c is not None:
                cv.put(x, y, c[:3], c[3] if len(c) == 4 else 255)

PLATE = ramp((240, 238, 228), 6, hi=WHITE, lo=(70, 70, 90))
PAD = ramp((236, 196, 70), 6, hi=(255, 250, 210), lo=(100, 60, 10))
SUIT = ramp((40, 54, 100), 5, hi=(120, 140, 200), lo=(8, 10, 24))

def armor_front(fx, fy, back=False):
    if fy < 0.06: return SUIT[1]                                          # suit collar
    edge = min(fx, 1 - fx, fy, 1 - fy)
    if fy >= 0.56:                                                         # gold abdomen bands
        k = (fy - 0.56) / 0.44 * 3
        c = PAD[1] if k % 1 < 0.2 else PAD[2] if k % 1 < 0.75 else PAD[4]
        return mix(c, PAD[3], 0.3) if fx > 0.8 else c
    c = PLATE[1] if fx < 0.45 else PLATE[2]
    if not back and abs(fy - (0.42 + 0.12 * abs(fx - 0.5))) < 0.035 and 0.12 < fx < 0.88:
        c = PLATE[4]                                                        # pec plate line
    if not back and abs(fx - 0.5) < 0.03 and fy < 0.45: c = PLATE[4]       # centre seam
    if back and abs(fx - 0.5) < 0.03: c = PLATE[3]
    if edge < 0.05: c = PLATE[4]
    if not back and 0.1 < fx < 0.3 and 0.1 < fy < 0.25: c = mix(c, WHITE, 0.6)   # gloss
    return c

cv = Canvas(128, 128)
B = box_faces(16, 16, 8, 12, 4)
paint_face(cv, B["front"], lambda fx, fy: armor_front(fx, fy))
paint_face(cv, B["back"], lambda fx, fy: armor_front(fx, fy, True))
for side in ("right", "left"):
    paint_face(cv, B[side], lambda fx, fy: PAD[2] if fy >= 0.56 else PLATE[3] if fx > 0.5 else PLATE[2])
paint_face(cv, B["top"], lambda fx, fy: PLATE[1] if 0.25 < fx < 0.75 else PLATE[0])
paint_face(cv, B["bottom"], lambda fx, fy: PAD[4])
A = box_faces(40, 16, 4, 12, 4)                                            # arms: navy body-suit sleeves + white gloves
for k, rect in A.items():
    paint_face(cv, rect, lambda fx, fy, k=k: (PLATE[1] if fx < 0.5 else PLATE[2]) if fy > 0.72 and k not in ("top",)
               else PLATE[4] if 0.68 < fy <= 0.72 and k not in ("top", "bottom") else (SUIT[1] if fx < 0.4 else SUIT[2]))
P = box_faces(0, 32, 5, 4, 6)                                              # shoulder pads
for k, rect in P.items():
    def padc(fx, fy, k=k):
        if k == "top":
            r = math.hypot(fx - 0.5, fy - 0.5)
            return PAD[0] if r < 0.18 else PAD[1] if r < 0.38 else PAD[2]
        if k == "bottom": return PAD[4]
        c = PAD[2] if fy < 0.6 else PAD[3]
        if fy > 0.85: c = PAD[5]
        if fy < 0.15: c = PAD[1]
        return c
    paint_face(cv, rect, padc)
save(cv, "saiyan_armor_model", MODELS)

# ============================================================ Weighted Training Gi model texture
GI = ramp((240, 120, 40), 6, hi=(255, 236, 190), lo=(90, 30, 20))
BLU = ramp((40, 70, 160), 5, hi=(150, 180, 255), lo=(8, 14, 50))
IRON = ramp((90, 94, 106), 5, hi=(210, 214, 230), lo=(16, 16, 24))
def gi_body(fx, fy, back=False):
    if fy > 0.78 and fy < 0.9: return BLU[1] if fy < 0.83 else BLU[2]      # belt
    c = GI[1] if fx < 0.45 else GI[2]
    if not back and abs(fx - (0.5 - (0.5 - fy) * 0.8 if fy < 0.5 else 0.5)) < 0.06 and fy < 0.5: c = BLU[1]   # wrap collar
    if not back and abs(fx - (0.5 + (0.5 - fy) * 0.8 if fy < 0.5 else 0.5)) < 0.06 and fy < 0.5: c = BLU[1]
    for (wx, wy) in ((0.12, 0.52), (0.6, 0.52)):                           # iron weights (front and back)
        if wx <= fx <= wx + 0.28 and wy <= fy <= wy + 0.22:
            ex, ey = (fx - wx) / 0.28, (fy - wy) / 0.22
            c = IRON[0] if ex < 0.15 or ey < 0.15 else IRON[3] if ex > 0.85 or ey > 0.85 else IRON[2]
            if 0.45 < ey < 0.6: c = (110, 80, 50)                          # strap
    if min(fx, 1 - fx) < 0.05: c = GI[4]
    return c

cv = Canvas(128, 128)
paint_face(cv, B["front"], lambda fx, fy: gi_body(fx, fy))
paint_face(cv, B["back"], lambda fx, fy: gi_body(fx, fy, True))
for side in ("right", "left"):
    paint_face(cv, B[side], lambda fx, fy: BLU[2] if 0.78 < fy < 0.9 else GI[3])
paint_face(cv, B["top"], lambda fx, fy: GI[1]); paint_face(cv, B["bottom"], lambda fx, fy: GI[4])
for k, rect in A.items():                                                  # short sleeves only (rest transparent)
    paint_face(cv, rect, lambda fx, fy, k=k: None if (fy > 0.42 and k not in ("top",)) or k == "bottom"
               else GI[4] if fy > 0.36 else (GI[1] if fx < 0.5 else GI[2]))
save(cv, "weighted_gi_model", MODELS)

print("batch 2:", [m[1] for m in MADE])
