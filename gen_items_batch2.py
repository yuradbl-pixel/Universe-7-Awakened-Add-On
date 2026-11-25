"""Texture pack batch 1 (add-on items, part 2): Dragon Radar, Ki Charger, Hoi-Poi capsules,
Saiyan armour icons, weighted training gi, and the wearable Scouter's model texture."""
import math, os, sys, random, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import *

RP = "/home/claude/dbz/DBZ_RP"
OUT = f"{RP}/textures/items"
MODELS = f"{RP}/textures/models/dbz"
os.makedirs(MODELS, exist_ok=True)
MADE = []
W = (255, 255, 255)

def save(cv, name, folder=OUT):
    p = f"{folder}/{name}.png"; cv.save(p); MADE.append((p, name))

SHELL = ramp((232, 236, 242), 6, hi=W, lo=(40, 50, 90))
METAL = ramp((150, 156, 170), 6, hi=(250, 252, 255), lo=(20, 22, 40))
DMETAL = ramp((70, 74, 92), 5, hi=(170, 176, 200), lo=(10, 10, 20))
GOLD = ramp((236, 170, 40), 6, hi=(255, 250, 200), lo=(90, 40, 10))

# ------------------------------------------------------------ Hoi-Poi capsules (5 colours, numbered)
def capsule(cv, x0, y0, x1, y1, number, cap):
    w = x1 - x0; rr = w / 2; cx = (x0 + x1) / 2
    def inside(x, y):
        if y0 + rr <= y <= y1 - rr:
            return x0 <= x <= x1
        cyy = y0 + rr if y < y0 + rr else y1 - rr
        return (x - cx) ** 2 + (y - cyy) ** 2 <= rr * rr
    def normal(x, y):
        nx = (x - cx) / rr
        cyy = min(max(y, y0 + rr), y1 - rr); ny = (y - cyy) / rr
        return nx, ny, math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    shade_shape(cv, inside, normal, SHELL, gamma=0.8)
    def band_at(yy0, yy1, R):
        for y in range(yy0, yy1):
            for x in range(int(x0), int(x1) + 1):
                if inside(x + 0.5, y + 0.5):
                    cv.put(x, y, band(R, lambert(*normal(x + 0.5, y + 0.5))))
    top_seam = int(y0 + (y1 - y0) * 0.30)
    for x in range(int(x0), int(x1) + 1):                                  # twist seam (two-part shell)
        if inside(x + 0.5, top_seam):
            cv.put(x, top_seam, SHELL[5]); cv.put(x, top_seam + 1, SHELL[0])
    band_at(top_seam + 3, top_seam + 9, cap)                               # coloured band
    band_at(int(y1 - rr * 0.9), int(y1 - rr * 0.9) + 3, cap)               # thin lower band
    for k in range(3):                                                     # grip ridges on the cap
        yy = int(y0 + rr * 0.95) + k * 3
        for x in range(int(x0) + 3, int(x1) - 2):
            if inside(x + 0.5, yy):
                cv.put(x, yy, SHELL[3])
    sphere(cv, cx, y0 + rr * 0.55, rr * 0.34, cap)                         # push button
    soft_spot(cv, cx - rr * 0.12, y0 + rr * 0.42, rr * 0.14, rr * 0.1, W, 230)
    dw = len(str(number)) * 4 * 3 - 3
    digits(cv, str(number), int(cx - dw / 2), int(y0 + (y1 - y0) * 0.56), 3, (36, 40, 66), shadow=SHELL[3])
    soft_spot(cv, cx - rr * 0.48, (y0 + y1) / 2 + 4, rr * 0.2, (y1 - y0) * 0.32, W, 210)
    for i in range(int((y1 - y0) * 0.5)):                                  # crisp vertical gloss line
        cv.put(int(cx - rr * 0.5), int(y0 + rr + 6 + i), W, 170)
    arc_light(cv, cx, y1 - rr, rr, 20, 100, (200, 214, 255), 170, 2)

CAPS = {"red": ((220, 50, 50), 1), "blue": ((60, 140, 230), 2), "yellow": ((240, 190, 30), 3),
        "green": ((70, 190, 90), 4), "purple": ((160, 80, 220), 5)}
for name, (col, num) in CAPS.items():
    cv = Canvas()
    R = ramp(col, 5, hi=(255, 240, 220), lo=tuple(int(v * 0.3) for v in col))
    capsule(cv, 40, 10, 88, 118, num, R)
    outline(cv, color=(30, 36, 70)); save(cv, f"capsule_{name}_{num}")

# ------------------------------------------------------------ Dragon Radar
cv = Canvas()
CASE = ramp((236, 238, 244), 6, hi=W, lo=(60, 70, 110))
axis_shape(cv, (64, 26), (64, 6), lambda t: 8, cylinder_color(METAL))      # crown stem
sphere(cv, 64, 7, 7, METAL)                                                # push button on top
sphere(cv, 64, 70, 52, CASE, gamma=0.85)                                   # round white casing
sphere(cv, 64, 70, 44, DMETAL, gamma=1.2)                                  # dark bezel
SCR = ramp((90, 220, 110), 6, hi=(230, 255, 220), lo=(0, 50, 30))
for y in range(cv.h):                                                      # green screen, glowing centre
    for x in range(cv.w):
        d = math.hypot(x + 0.5 - 64, y + 0.5 - 70)
        if d <= 39:
            c = band(SCR, 0.95 - d / 39 * 0.75)
            if (x - 64) % 10 == 0 or (y - 70) % 10 == 0:
                c = mix(c, (20, 90, 50), 0.55)                              # grid
            cv.put(x, y, c)
for r in (13, 26):                                                         # range rings
    for a in range(0, 360, 2):
        cv.put(int(64 + r * math.cos(math.radians(a))), int(70 + r * math.sin(math.radians(a))), (40, 130, 70))
tri = poly_inside([(64, 64), (59, 75), (69, 75)])                          # you-are-here arrow
for y in range(62, 77):
    for x in range(57, 72):
        if tri(x + 0.5, y + 0.5): cv.put(x, y, (240, 50, 40))
for (bx, by) in ((88, 52), (44, 92), (80, 96)):                            # dragon ball blips
    sphere(cv, bx, by, 3.5, ramp((255, 200, 50), 4, hi=W)); cv.put(bx - 1, by - 1, W)
for x in range(30, 98):                                                     # glass reflection
    y = int(48 + (x - 30) * 0.25)
    if math.hypot(x - 64, y - 70) < 38: cv.put(x, y, W, 120)
soft_spot(cv, 46, 50, 10, 6, W, 150)
arc_light(cv, 64, 70, 52, 20, 120, (200, 214, 255), 190, 2.5)
sparkle(cv, 34, 36, 3)
outline(cv, color=(30, 36, 60)); save(cv, "dragon_radar")

# ------------------------------------------------------------ Ki Charger (energy crystal in a metal cradle)
cv = Canvas()
KI = ramp((90, 200, 255), 6, hi=W, lo=(10, 40, 120))
gem = [(64, 12), (88, 44), (78, 92), (50, 92), (40, 44)]
gin = poly_inside(gem)
facets = [((64, 12), (64, 52)), ((40, 44), (64, 52)), ((88, 44), (64, 52)), ((50, 92), (64, 52)), ((78, 92), (64, 52))]
for y in range(8, 96):
    for x in range(36, 92):
        if gin(x + 0.5, y + 0.5):
            nx = (x - 64) / 26; ny = (y - 52) / 40
            # flat facets: each quadrant gets its own light value (gem look)
            L = 0.85 if (x < 64 and y < 52) else 0.6 if (x >= 64 and y < 52) else 0.45 if x < 64 else 0.3
            cv.put(x, y, band(KI, L + 0.1 * (1 - abs(nx))))
d = cv.draw()
for a, b in facets:
    d.line((a, b), fill=KI[1] + (255,))
for i in range(14):
    cv.put(52 + i // 2, 24 + i, W)                                         # bright facet edge
glow(cv, (90, 200, 255), 6, 1.0)
cr = Canvas()                                                              # cradle: two prongs and a base
for k in (-1, 1):
    axis_shape(cr, (64 + 18 * k, 112), (64 + 30 * k, 58), lambda t: 4 - t * 1.5, cylinder_color(METAL))
shade_shape(cr, lambda x, y: 32 <= x <= 96 and 104 <= y <= 120 and abs(x - 64) <= 32 - (y - 104) * 0.4,
            lambda x, y: ((x - 64) / 50, (y - 112) / 20, 0.8), DMETAL)
for x in (44, 64, 84):
    sphere(cr, x, 112, 3, ramp((90, 230, 255), 4, hi=W))                    # charge lights
cv.paste(cr)
for (sx, sy) in ((30, 30), (98, 24), (100, 70), (26, 76)):
    sparkle(cv, sx, sy, 3, (200, 240, 255))
outline(cv, color=(10, 30, 70)); save(cv, "ki_charger")

# ------------------------------------------------------------ Saiyan battle armour (chest plate)
cv = Canvas()
PLATE = ramp((240, 238, 228), 6, hi=W, lo=(70, 70, 90))
PAD = ramp((236, 196, 70), 6, hi=(255, 250, 210), lo=(100, 60, 10))
SUIT = ramp((40, 50, 90), 5, hi=(110, 130, 190), lo=(8, 10, 24))
torso = [(16, 34), (30, 22), (98, 22), (112, 34), (104, 46), (94, 70), (86, 112), (42, 112), (34, 70), (24, 46)]
tin = poly_inside(torso)
shade_shape(cv, lambda x, y: tin(x, y), lambda x, y: ((x - 64) / 50, (y - 66) / 90, 0.85), PLATE, 0.9)
for y in range(10, 30):                                                    # navy body-suit collar
    for x in range(48, 81):
        if (x - 64) ** 2 / 16 ** 2 + (y - 22) ** 2 / 10 ** 2 <= 1:
            cv.put(x, y, band(SUIT, lambert((x - 64) / 16, (y - 22) / 10, 0.6)))
for y in range(22, 34):                                                    # neck opening
    for x in range(54, 75):
        if (x - 64) ** 2 / 10 ** 2 + (y - 22) ** 2 / 8 ** 2 <= 1:
            cv.put(x, y, SUIT[4])
d = cv.draw()
d.line((64, 34, 64, 66), fill=PLATE[4] + (255,))                          # centre seam of the breast plate
d.arc((34, 36, 64, 70), 0, 180, fill=PLATE[4] + (255,)); d.arc((64, 36, 94, 70), 0, 180, fill=PLATE[4] + (255,))   # pec plates
for k in (-1, 1):                                                          # shoulder straps
    d.line((64 + 34 * k, 24, 64 + 44 * k, 44), fill=PAD[3] + (255,), width=5); d.line((64 + 34 * k, 23, 64 + 44 * k, 43), fill=PAD[1] + (255,))
for k, y in enumerate((72, 84, 96)):                                       # segmented gold abdomen bands
    for yy in range(y, y + 9):
        for x in range(30, 100):
            if tin(x + 0.5, yy + 0.5):
                cv.put(x, yy, band(PAD, lambert((x - 64) / 40, (yy - y - 4) / 8, 0.7)))
    for x in range(30, 100):
        if tin(x + 0.5, y + 0.5): cv.put(x, y, PAD[5])
for x, y in ((40, 40), (88, 40)):                                          # rivets
    sphere(cv, x, y, 2.5, METAL)
soft_spot(cv, 46, 44, 9, 12, W, 170); sparkle(cv, 44, 40, 2)
outline(cv, color=(30, 30, 50)); save(cv, "saiyan_chestplate")

# ------------------------------------------------------------ Saiyan shoulder pads
cv = Canvas()
for cx, flip in ((38, -1), (90, 1)):
    for y in range(cv.h):
        for x in range(cv.w):
            u, v = (x + 0.5 - cx) / 30, (y + 0.5 - 66) / 28
            if u * u + v * v <= 1 and v < 0.75:                             # rounded pad
                nz = math.sqrt(max(0, 1 - u * u - v * v))
                cv.put(x, y, band(PAD, lambert(u, v, nz), 0.85))
    for y in range(84, 100):                                               # white strap plate under each pad
        for x in range(cx - 18, cx + 19):
            cv.put(x, y, band(PLATE, lambert((x - cx) / 20, (y - 92) / 10, 0.8)))
    for k in range(3):                                                     # ridges
        d = cv.draw(); d.arc((cx - 24 + k * 4, 34 + k * 5, cx + 24 - k * 4, 90 - k * 3), 200, 340, fill=PAD[4] + (255,))
    sphere(cv, cx, 92, 2.6, METAL)
    soft_spot(cv, cx - 9, 46, 8, 6, W, 190); sparkle(cv, cx - 10, 44, 2)
outline(cv, color=(60, 34, 6)); save(cv, "saiyan_shoulder_pads")

# ------------------------------------------------------------ Weighted training gi
cv = Canvas()
GI = ramp((240, 120, 40), 6, hi=(255, 236, 190), lo=(90, 30, 20))
BLUE = ramp((40, 70, 160), 5, hi=(150, 180, 255), lo=(8, 14, 50))
shirt = [(20, 30), (46, 18), (82, 18), (108, 30), (100, 54), (88, 50), (90, 112), (38, 112), (40, 50), (28, 54)]
sin_ = poly_inside(shirt)
n = lambda x, y: (math.sin(x * 0.4) * 0.05 + math.sin((x + y) * 0.2) * 0.05)
shade_shape(cv, lambda x, y: sin_(x, y), lambda x, y: ((x - 64) / 60 + n(x, y), (y - 64) / 90, 0.85), GI, 0.9)
d = cv.draw()
for (a, b) in (((46, 18), (64, 52)), ((82, 18), (64, 52))):                # blue wrap collar
    d.line((a, b), fill=BLUE[1] + (255,), width=5); d.line((a, b), fill=BLUE[0] + (255,), width=1)
for x in range(40, 90):                                                     # blue belt
    for y in range(96, 104):
        if sin_(x + 0.5, y + 0.5): cv.put(x, y, band(BLUE, lambert((x - 64) / 30, (y - 100) / 6, 0.8)))
for (fx, fy, tx, ty) in ((50, 60, 46, 92), (76, 60, 82, 92), (60, 70, 58, 94)):   # cloth folds
    d.line((fx, fy, tx, ty), fill=GI[4] + (255,)); d.line((fx + 1, fy, tx + 1, ty), fill=GI[1] + (255,))
IRON = ramp((90, 94, 106), 5, hi=(210, 214, 230), lo=(16, 16, 24))
for (wx, wy) in ((44, 64), (72, 64), (44, 80), (72, 80)):                   # strapped iron weight plates
    shade_shape(cv, lambda x, y, wx=wx, wy=wy: wx <= x <= wx + 13 and wy <= y <= wy + 11,
                lambda x, y, wx=wx, wy=wy: ((x - wx - 6) / 20, (y - wy - 5) / 20, 0.9), IRON)
    for x in range(wx - 2, wx + 16):
        cv.put(x, wy + 5, (70, 50, 30)); cv.put(x, wy + 6, (110, 80, 50))       # leather strap
    cv.put(wx + 2, wy + 2, W); cv.put(wx + 3, wy + 2, IRON[0])
    digits(cv, "9", wx + 4, wy + 3, 1, (240, 220, 120))                         # weight marking
soft_spot(cv, 50, 36, 10, 8, W, 140)
outline(cv, color=(60, 24, 10)); save(cv, "weighted_training_gi")

# ------------------------------------------------------------ Wearable Scouter model texture (32x32)
cv = Canvas(32, 32)
for y in range(0, 8):                                                       # metal frame strip (0..15, 0..7)
    for x in range(0, 16):
        cv.put(x, y, band(DMETAL, 0.9 - y / 8 * 0.7))
for x in range(16):
    cv.put(x, 0, DMETAL[0])
for y in range(0, 16):                                                      # green lens (16..31, 0..15)
    for x in range(16, 32):
        t = (x - 16) / 16 * 0.5 + y / 16 * 0.5
        c = band(SCR, 1 - t * 0.8)
        if y % 3 == 0: c = mix(c, (20, 100, 50), 0.35)                       # scan lines
        cv.put(x, y, c)
for (x, y) in ((19, 4), (21, 4), (23, 4)):
    cv.put(x, y, W)
cv.put(28, 11, (255, 70, 60)); cv.put(29, 11, (255, 70, 60))                # target blip
for x in range(17, 30):
    cv.put(x, 1, (230, 255, 230))
for y in range(8, 16):                                                      # ear module (0..15, 8..15)
    for x in range(0, 16):
        cv.put(x, y, band(METAL, 0.9 - math.hypot(x - 5, y - 10) / 14))
cv.put(10, 12, (230, 50, 50)); cv.put(12, 12, (240, 200, 40))              # buttons
for y in range(16, 24):                                                     # antenna / tip (0..7, 16..23)
    for x in range(0, 8):
        cv.put(x, y, band(METAL, 0.8 - x / 10))
cv.put(1, 16, (110, 255, 140)); cv.put(2, 16, (110, 255, 140))
save(cv, "scouter_model", MODELS)

print("batch:", [m[1] for m in MADE])
