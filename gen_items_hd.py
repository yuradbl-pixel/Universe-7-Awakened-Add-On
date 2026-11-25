"""Universe 7 texture pack, category 1: ITEMS (128x128, drawn pixel by pixel with pixlib)."""
import math, os, random, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
from pixlib import *

RP = "/home/claude/dbz/DBZ_RP"
OUT = f"{RP}/textures/items"
EGG_OUT = f"{OUT}/eggs"
os.makedirs(EGG_OUT, exist_ok=True)
MADE = []

def save(cv, name, folder=OUT):
    path = f"{folder}/{name}.png"
    cv.save(path); MADE.append((path, name))

# ============================================================ Dragon Balls
ORANGE = ramp((248, 150, 30), 6, hi=(255, 248, 200), lo=(120, 30, 20))
STAR = ramp((228, 36, 30), 4, hi=(255, 150, 120), lo=(90, 0, 20))
LAYOUT = {
    1: ([(0, 0)], 15),
    2: ([(-10, -9), (10, 9)], 11),
    3: ([(0, -12), (-12, 8), (12, 8)], 10),
    4: ([(-11, -11), (11, -11), (-11, 11), (11, 11)], 9),
    5: ([(0, 0), (-14, -14), (14, -14), (-14, 14), (14, 14)], 8),
    6: ([(-9, -16), (9, -16), (-17, 0), (17, 0), (-9, 16), (9, 16)], 7.5),
    7: ([(0, 0)] + [(round(17 * math.cos(math.radians(a))), round(17 * math.sin(math.radians(a)))) for a in range(-90, 270, 60)], 7),
}

def dragon_ball(n):
    cv = Canvas(); cx, cy, r = 64, 66, 52
    sphere(cv, cx, cy, r, ORANGE, gamma=0.9)
    soft_spot(cv, cx + 16, cy + 20, 26, 18, (255, 226, 120), 170)            # light focused through the glass
    soft_spot(cv, cx + 22, cy + 26, 12, 8, (255, 246, 190), 150)
    pts, size = LAYOUT[n]
    for sx, sy in pts:
        x0, y0 = cx + sx, cy + sy - 2
        poly = star_poly(x0, y0, size, size * 0.45)
        ins = poly_inside(poly)
        for y in range(int(y0 - size) - 2, int(y0 + size) + 3):
            for x in range(int(x0 - size) - 2, int(x0 + size) + 3):
                if ins(x + 0.5, y + 0.5):
                    lx, ly = (x - x0) / size, (y - y0) / size
                    cv.put(x, y, band(STAR, 0.75 - 0.45 * (lx + ly) * 0.5))
        inner_line(cv, lambda x, y: ins(x + 0.5, y + 0.5), STAR[3])
        cv.put(int(x0 - size * 0.2), int(y0 - size * 0.35), (255, 190, 170))      # tiny glint on the star
    # glass finish: broad soft shine, window reflection, hard specular, rim light
    soft_spot(cv, cx - 18, cy - 20, 22, 15, (255, 255, 240), 175)
    for t in range(0, 40):                                                     # curved window streak
        a = math.radians(200 + t * 1.6)
        x, y = cx + (r - 8) * math.cos(a), cy + (r - 8) * math.sin(a)
        for w in range(3):
            cv.put(int(x + w * 0.7), int(y + w * 0.7), (255, 255, 255), 210 - w * 60)
    sparkle(cv, cx - 24, cy - 26, 4)
    cv.put(cx - 15, cy - 31, (255, 255, 255)); cv.put(cx - 14, cy - 31, (255, 255, 255), 160)
    arc_light(cv, cx, cy, r, 10, 120, (255, 214, 140), 190, 2.2)                # bounced rim light
    outline(cv, color=(100, 34, 10))
    save(cv, f"dragonball_{n}star")

for n in range(1, 8):
    dragon_ball(n)

# ============================================================ Senzu Bean & Bag
BEAN = ramp((96, 186, 60), 6, hi=(236, 255, 190), lo=(10, 50, 40))

def bean(cv, cx, cy, s, rot):
    rx, ry = 13 * s, 22 * s
    nx, ny = math.cos(rot), math.sin(rot)
    cut = lambda x, y: (x - (cx + nx * rx * 1.25)) ** 2 + (y - (cy + ny * rx * 1.25)) ** 2 < (rx * 0.62) ** 2   # kidney notch
    ellipsoid(cv, cx, cy, rx, ry, BEAN, rot=rot, gamma=0.85, cut=cut)
    soft_spot(cv, cx - 4 * s, cy - 8 * s, 4 * s, 7 * s, (250, 255, 220), 190)
    cv.put(int(cx - 4 * s), int(cy - 11 * s), (255, 255, 255))

cv = Canvas(); bean(cv, 64, 64, 2.3, 0.0)
for y in range(40, 92, 6):                                                    # faint fibre lines
    for x in range(48, 82):
        p = cv.get(x, y)
        if p[3] and (x + y) % 7 == 0:
            cv.put(x, y, BEAN[3], 70)
outline(cv, color=(20, 60, 30)); save(cv, "senzu_bean")

CLOTH = ramp((176, 120, 70), 6, hi=(255, 236, 190), lo=(50, 20, 30))
ROPE = ramp((222, 196, 130), 4, hi=(255, 250, 220), lo=(100, 70, 40))
cv = Canvas()
# beans peeking out of the open top (behind the cloth)
bean(cv, 52, 30, 0.8, -0.4); bean(cv, 66, 26, 0.85, 0.3); bean(cv, 78, 32, 0.8, 0.9)
body_c = (64, 82);
def bag_inside(x, y):
    if (x - 64) ** 2 / 40 ** 2 + (y - 84) ** 2 / 34 ** 2 <= 1 and y > 56:
        return True
    if 46 <= y <= 60:                                                          # neck
        half = 14 + (60 - y) * 0.9 if y < 52 else 14
        return abs(x - 64) <= half
    return False
def bag_normal(x, y):
    nx = (x - 64) / 42; ny = (y - 84) / 40 if y > 56 else -0.4
    return nx, ny, math.sqrt(max(0.05, 1 - nx * nx - ny * ny))
shade_shape(cv, bag_inside, bag_normal, CLOTH, gamma=0.9)
for (x0, y0, x1, y1) in ((48, 66, 44, 100), (58, 64, 56, 112), (72, 64, 76, 112), (82, 68, 88, 100)):   # cloth folds
    d = cv.draw(); d.line((x0, y0, x1, y1), fill=CLOTH[4] + (255,)); d.line((x0 + 1, y0, x1 + 1, y1), fill=CLOTH[1] + (255,))
for x in range(30, 99, 4):                                                    # stitched hem
    if bag_inside(x, 104):
        cv.put(x, 104, CLOTH[0]); cv.put(x + 1, 104, CLOTH[0])
d = cv.draw()
d.line((46, 56, 82, 56), fill=ROPE[2] + (255,), width=4); d.line((46, 55, 82, 55), fill=ROPE[0] + (255,))
for x in range(46, 83, 3):
    cv.put(x, 57, ROPE[3])                                                    # twisted rope
d.ellipse((60, 52, 70, 62), fill=ROPE[1] + (255,)); d.ellipse((62, 54, 66, 57), fill=ROPE[0] + (255,))   # knot
d.line((64, 62, 58, 80), fill=ROPE[2] + (255,), width=2); d.line((66, 62, 72, 78), fill=ROPE[2] + (255,), width=2)
cv.put(57, 81, ROPE[3]); cv.put(72, 79, ROPE[3])
soft_spot(cv, 50, 76, 9, 12, (255, 240, 210), 110)
# small bean emblem on the cloth
bean(cv, 66, 90, 0.45, 0.2)
outline(cv); save(cv, "senzu_bag")

# ============================================================ Scouter
METAL = ramp((150, 156, 170), 6, hi=(250, 252, 255), lo=(20, 22, 40))
DMETAL = ramp((70, 74, 92), 5, hi=(170, 176, 200), lo=(10, 10, 20))
LENS = ramp((70, 230, 110), 5, hi=(230, 255, 230), lo=(0, 70, 40))
cv = Canvas()
# ear module (round), arm, lens frame, lens
sphere(cv, 92, 74, 22, METAL, gamma=0.9)
sphere(cv, 92, 74, 12, DMETAL)
for a in range(0, 360, 45):
    cv.put(int(92 + 17 * math.cos(math.radians(a))), int(74 + 17 * math.sin(math.radians(a))), METAL[4])   # screws ring
axis_shape(cv, (30, 52), (80, 66), lambda t: 6, cylinder_color(DMETAL))           # arm
axis_shape(cv, (34, 50), (76, 62), lambda t: 2, cylinder_color(METAL))
frame = [(10, 30), (54, 22), (60, 62), (16, 70)]
fin = poly_inside(frame)
shade_shape(cv, fin, lambda x, y: (-0.2, -0.3, 0.9), DMETAL)
lens = [(15, 34), (51, 27), (56, 58), (20, 64)]
lin = poly_inside(lens)
for y in range(20, 72):
    for x in range(8, 62):
        if lin(x + 0.5, y + 0.5):
            t = (x - 15) / 41 * 0.5 + (y - 27) / 37 * 0.5
            cv.px[x, y] = band(LENS, 1 - t) + (215,)                            # translucent glass
for y in range(30, 64, 4):                                                    # scan lines
    for x in range(16, 56):
        if lin(x + 0.5, y + 0.5):
            cv.put(x, y, LENS[3], 90)
d = cv.draw()
d.line((22, 50, 32, 44, 38, 48, 48, 38), fill=(220, 255, 220, 255))          # readout graph
for (x, y) in ((24, 36), (28, 36), (32, 36)):
    cv.put(x, y, (255, 255, 255)); cv.put(x + 1, y, (200, 255, 200))
cv.put(46, 54, (255, 80, 60)); cv.put(47, 54, (255, 80, 60)); cv.put(46, 55, (200, 30, 30))   # target blip
soft_spot(cv, 24, 34, 7, 4, (255, 255, 255), 170, mask=lambda x, y: lin(x + 0.5, y + 0.5))
for x, y, c in ((100, 92, (220, 40, 40)), (106, 86, (240, 200, 40))):        # buttons on the module
    sphere(cv, x, y, 3, ramp(c, 4))
axis_shape(cv, (104, 56), (114, 26), lambda t: 1.6, cylinder_color(METAL))      # antenna
sphere(cv, 114, 25, 3, ramp((90, 240, 120), 4))
sparkle(cv, 84, 64, 2)
outline(cv, color=(18, 20, 30)); save(cv, "scouter")

# ============================================================ Capsules & case
WHITE = ramp((232, 236, 242), 6, hi=(255, 255, 255), lo=(40, 50, 90))
CAPRED = ramp((220, 50, 50), 4, hi=(255, 180, 160), lo=(90, 10, 30))

def capsule(cv, x0, y0, x1, y1, number=None, scale=2, cap=CAPRED):
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
    shade_shape(cv, inside, normal, WHITE, gamma=0.8)
    seam = int(y0 + (y1 - y0) * 0.3)
    for x in range(int(x0), int(x1) + 1):                                     # cap seam + coloured band
        if inside(x + 0.5, seam):
            cv.put(x, seam, WHITE[4]); cv.put(x, seam + 1, WHITE[0])
            for yy in range(seam + 3, seam + 3 + max(2, int(w / 8))):
                if inside(x + 0.5, yy):
                    nx = (x + 0.5 - cx) / rr
                    cv.put(x, yy, band(cap, lambert(nx, 0, math.sqrt(max(0, 1 - nx * nx)))))
    bx, by, br = cx, y0 + rr * 0.55, max(2, rr * 0.32)                         # push button on top
    sphere(cv, bx, by, br, cap)
    if number is not None:
        dw = len(str(number)) * 4 * scale - scale
        digits(cv, str(number), int(cx - dw / 2), int(y0 + (y1 - y0) * 0.55), scale, (40, 44, 70))
    soft_spot(cv, cx - rr * 0.45, (y0 + y1) / 2, rr * 0.25, (y1 - y0) * 0.3, (255, 255, 255), 200)

cv = Canvas(); capsule(cv, 42, 12, 86, 116, 1, 3)
outline(cv, color=(40, 46, 80)); save(cv, "capsule")
cv = Canvas(); capsule(cv, 42, 12, 86, 116, 2, 3, cap=ramp((60, 140, 230), 4, hi=(200, 230, 255), lo=(10, 30, 80)))
outline(cv, color=(40, 46, 80)); save(cv, "capsule_2")

CASE = ramp((60, 90, 150), 6, hi=(210, 230, 255), lo=(10, 14, 40))
cv = Canvas()
def case_in(x, y): return 10 <= x <= 118 and 30 <= y <= 112 and not ((x < 16 or x > 112) and (y < 36 or y > 106) and (min(abs(x - 16), abs(x - 112)) + min(abs(y - 36), abs(y - 106)) > 6))
shade_shape(cv, case_in, lambda x, y: ((x - 64) / 160, (y - 70) / 120, 0.95), CASE)
lid = lambda x, y: 14 <= x <= 114 and 14 <= y <= 30
shade_shape(cv, lid, lambda x, y: (0, -0.6, 0.8), ramp((90, 120, 180), 5))     # open lid seen edge-on
for x in range(14, 115):
    cv.put(x, 30, CASE[5]); cv.put(x, 31, CASE[0])
for x in range(18, 112):
    cv.put(x, 104, CASE[5])
tray = lambda x, y: 18 <= x <= 110 and 40 <= y <= 100
for y in range(40, 101):
    for x in range(18, 111):
        cv.put(x, y, CASE[4] if (y - 40) < 3 or (x - 18) < 3 else CASE[3])     # recessed tray
for i, col in enumerate(((220, 50, 50), (60, 140, 230), (240, 190, 40), (90, 200, 90), (200, 90, 220))):
    x0 = 22 + i * 18
    capsule(cv, x0, 46, x0 + 13, 96, i + 1, 1, cap=ramp(col, 4))
for x in (24, 104):                                                             # latches
    sphere(cv, x, 110, 4, METAL)
d = cv.draw(); d.line((60, 22, 68, 22), fill=(230, 200, 90, 255), width=3)    # lid handle
outline(cv, color=(10, 14, 36)); save(cv, "capsule_case")

# ============================================================ Menu items (badge style shared with the UI)
NAVY = ramp((34, 42, 74), 5, hi=(110, 130, 190), lo=(6, 8, 20))
GOLD = ramp((236, 170, 40), 6, hi=(255, 250, 200), lo=(90, 40, 10))

def badge(cv, cx=64, cy=64, r=54):
    sphere(cv, cx, cy, r, GOLD, gamma=0.8)                                      # gold rim
    sphere(cv, cx, cy, r - 8, NAVY, gamma=1.2)                                  # dark face
    arc_light(cv, cx, cy, r - 8, 180, 300, (90, 110, 170), 160, 2)
    for a in range(0, 360, 30):                                                 # rim studs
        x, y = cx + (r - 4) * math.cos(math.radians(a)), cy + (r - 4) * math.sin(math.radians(a))
        cv.put(int(x), int(y), GOLD[0]); cv.put(int(x) + 1, int(y) + 1, GOLD[4])

cv = Canvas(); badge(cv)
orb = Canvas(); sphere(orb, 64, 64, 18, ramp((255, 170, 50), 5, hi=(255, 255, 230), lo=(160, 40, 10)))
for a in range(0, 360, 30):                                                     # ki burst spikes
    L = 36 if a % 60 == 0 else 28
    p0 = (64 + 14 * math.cos(math.radians(a)), 64 + 14 * math.sin(math.radians(a)))
    p1 = (64 + L * math.cos(math.radians(a)), 64 + L * math.sin(math.radians(a)))
    axis_shape(orb, p0, p1, lambda t: 3.2 * (1 - t) + 0.4, lambda t, s: mix((255, 240, 160), (255, 120, 30), t))
sphere(orb, 64, 64, 18, ramp((255, 170, 50), 5, hi=(255, 255, 230), lo=(160, 40, 10)))
soft_spot(orb, 58, 57, 7, 5, (255, 255, 255), 220); sparkle(orb, 57, 56, 2)
glow(orb, (255, 160, 40), 5, 0.8)
cv.paste(orb); outline(cv, color=(40, 20, 6)); save(cv, "menu_abilities")

cv = Canvas(); badge(cv)
fl = Canvas()
FLAME = ramp((255, 200, 40), 5, hi=(255, 255, 220), lo=(200, 70, 10))
for i, (dx, h, w) in enumerate(((-18, 30, 8), (-9, 40, 9), (0, 48, 10), (9, 40, 9), (18, 30, 8))):   # rising aura spikes
    axis_shape(fl, (64 + dx * 0.6, 92), (64 + dx * 1.2, 92 - h), lambda t, w=w: w * (1 - t) ** 0.8 + 0.3,
               lambda t, s: band(FLAME, 1 - t * 0.7 + (-s) * 0.15))
for k, yy in enumerate((70, 58, 46)):                                           # power-up chevrons
    pts = [(48, yy + 10), (64, yy), (80, yy + 10), (80, yy + 15), (64, yy + 5), (48, yy + 15)]
    ins = poly_inside(pts)
    for y in range(yy - 1, yy + 17):
        for x in range(46, 82):
            if ins(x + 0.5, y + 0.5):
                fl.put(x, y, (255, 255, 255) if k == 2 else (255, 246, 200))
glow(fl, (255, 200, 60), 5, 0.9)
cv.paste(fl); outline(cv, color=(40, 20, 6)); save(cv, "menu_transformations")

# ============================================================ Power Pole
POLE = ramp((206, 40, 36), 6, hi=(255, 190, 160), lo=(60, 0, 30))
cv = Canvas()
p0, p1 = (14, 116), (114, 12)
def pole_color(t, s):
    if t < 0.12 or t > 0.88:                                                    # gold caps with ridges
        g = cylinder_color(GOLD)(t, s)
        if any(abs(t - c) < 0.006 for c in (0.04, 0.08, 0.92, 0.96)):
            return GOLD[4]
        return g
    if abs(t - 0.12) < 0.008 or abs(t - 0.88) < 0.008:
        return GOLD[5]
    return cylinder_color(POLE)(t, s)
axis_shape(cv, p0, p1, lambda t: 5.2, pole_color)
outline(cv, color=(50, 6, 14)); save(cv, "power_pole")

# ============================================================ Z Sword
STEEL = ramp((176, 190, 210), 6, hi=(255, 255, 255), lo=(30, 40, 70))
GRIP = ramp((70, 40, 110), 5, hi=(170, 140, 220), lo=(14, 6, 30))
GUARD = ramp((60, 90, 200), 5, hi=(190, 210, 255), lo=(10, 16, 60))
cv = Canvas()
a, b = (22, 106), (114, 14)                                                     # full sword axis
def sword_profile(t):
    if t < 0.13: return 3.2                                                     # grip
    if t < 0.165: return 3.6                                                    # collar
    if t < 0.19: return 12                                                      # cross-guard
    if t < 0.86: return 9.5                                                     # broad blade
    return 9.5 * (1 - (t - 0.86) / 0.14) + 0.3                                  # tip
def sword_color(t, s):
    if t < 0.13:
        c = cylinder_color(GRIP)(t, s)
        return GRIP[0] if int(t * 260) % 4 == 0 and abs(s) < 0.6 else c         # diamond wrap
    if t < 0.165:
        return cylinder_color(GOLD)(t, s)
    if t < 0.19:
        return band(GUARD, 0.8 - s * 0.35 - (t - 0.165) * 6)
    # blade: two bevelled faces, a dark fuller groove in the middle, bright edges
    if abs(s) < 0.12 and t < 0.8:
        return STEEL[4]
    if abs(s) > 0.86:
        return STEEL[0] if s < 0 else STEEL[2]
    return band(STEEL, 0.82 if s < 0 else 0.42)
axis_shape(cv, a, b, sword_profile, sword_color)
sphere(cv, 22, 106, 6, GOLD)                                                    # pommel
sphere(cv, 22, 106, 2.4, ramp((230, 40, 60), 4))
for i in range(6):                                                              # glint running down the blade
    cv.put(78 + i, 48 - i, (255, 255, 255))
sparkle(cv, 98, 32, 3)
outline(cv, color=(14, 18, 40)); save(cv, "z_sword")

# ============================================================ Potara Earrings
JADE = ramp((150, 220, 60), 6, hi=(250, 255, 200), lo=(20, 70, 40))
cv = Canvas()
for cx in (38, 90):
    for y in range(14, 40):                                                     # gold hook
        for x in range(cx - 14, cx + 15):
            d_ = math.hypot(x + 0.5 - cx, y + 0.5 - 28)
            if 9 <= d_ <= 13 and y < 34:
                nx = (x + 0.5 - cx) / 13
                cv.put(x, y, band(GOLD, lambert(nx, (y - 28) / 13, 0.6)))
    axis_shape(cv, (cx, 38), (cx, 54), lambda t: 3, cylinder_color(GOLD))       # post
    sphere(cv, cx, 56, 6, GOLD)                                                 # cap
    sphere(cv, cx, 78, 20, JADE, gamma=0.85)                                    # bead
    soft_spot(cv, cx - 7, 70, 7, 5, (255, 255, 235), 200); sparkle(cv, cx - 8, 69, 3)
    arc_light(cv, cx, 78, 20, 20, 110, (230, 255, 170), 170, 2)
outline(cv, color=(30, 40, 10)); save(cv, "potara_earrings")

# ============================================================ Time Ring
RING = ramp((60, 190, 110), 6, hi=(220, 255, 230), lo=(0, 50, 50))
cv = Canvas(); cx, cy, R, rt = 64, 70, 34, 13                                   # torus: major radius R, tube rt
for y in range(cv.h):
    for x in range(cv.w):
        dx, dy = x + 0.5 - cx, y + 0.5 - cy
        d_ = math.hypot(dx, dy)
        q = d_ - R
        if abs(q) <= rt:
            nz = math.sqrt(max(0.0, 1 - (q / rt) ** 2))
            nx, ny = (dx / d_) * (q / rt), (dy / d_) * (q / rt)
            cv.put(x, y, band(RING, lambert(nx, ny, nz), 0.85))
for a in range(0, 360, 4):                                                      # carved groove around the ring
    x, y = cx + R * math.cos(math.radians(a)), cy + R * math.sin(math.radians(a))
    cv.put(int(x), int(y), RING[4], 150)
soft_spot(cv, cx - 26, cy - 22, 8, 5, (255, 255, 255), 210)
sparkle(cv, cx - 27, cy - 24, 3)
arc_light(cv, cx, cy, R + rt, 0, 100, (180, 255, 210), 170, 2)
for y in range(10, 24):                                                         # silver hook
    for x in range(54, 75):
        d_ = math.hypot(x + 0.5 - 64, y + 0.5 - 22)
        if 7 <= d_ <= 10 and y < 24:
            cv.put(x, y, band(METAL, lambert((x - 64) / 10, (y - 22) / 10, 0.6)))
outline(cv, color=(6, 40, 30)); save(cv, "time_ring")

# ============================================================ Spawn eggs (colour scheme of each NPC; no faces)
def palette_of(npc_id):
    p = f"{RP}/textures/entity/npc/{npc_id}.png"
    if not os.path.exists(p):
        return (200, 120, 40), (60, 60, 80)
    im = Image.open(p).convert("RGBA")
    im = im.crop((0, im.height // 4, im.width, im.height))                      # body & legs (outfit colours)
    q = im.convert("RGB").quantize(8)
    counts = sorted(q.getcolors(), reverse=True); pal = q.getpalette()
    cols = [tuple(pal[i * 3:i * 3 + 3]) for _, i in counts]
    alpha = im.split()[3]
    cols = [c for c in cols if sum(c) > 40] or [(200, 120, 40)]
    base = cols[0]
    spot = next((c for c in cols[1:] if sum(abs(a - b) for a, b in zip(c, base)) > 120), (40, 40, 50))
    return base, spot

def egg(npc_id, role):
    base, spot = palette_of(npc_id)
    E = ramp(base, 6); Sp = ramp(spot, 4)
    cv = Canvas(); cx, cy, a, b = 64, 68, 38, 50
    def rx(y): return a * (1 - 0.2 * max(-1, min(1, (cy - y) / b)))                 # narrower top
    inside = lambda x, y: ((x - cx) / rx(y)) ** 2 + ((y - cy) / b) ** 2 <= 1
    def normal(x, y):
        nx, ny = (x - cx) / rx(y), (y - cy) / b
        return nx, ny, math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    shade_shape(cv, inside, normal, E, 0.9)
    rnd = random.Random(npc_id)
    for _ in range(9):                                                              # spots, shaded like the shell
        sx, sy, sr = rnd.uniform(36, 92), rnd.uniform(24, 108), rnd.uniform(4, 8.5)
        for y in range(int(sy - sr), int(sy + sr) + 1):
            for x in range(int(sx - sr), int(sx + sr) + 1):
                if (x - sx) ** 2 + ((y - sy) * 1.2) ** 2 <= sr * sr and inside(x + 0.5, y + 0.5):
                    cv.put(x, y, band(Sp, lambert(*normal(x + 0.5, y + 0.5)), 0.9))
    if role == "trainer":                                                           # gold band for trainers
        for y in range(76, 82):
            for x in range(20, 110):
                if inside(x + 0.5, y + 0.5):
                    cv.put(x, y, band(GOLD, lambert(*normal(x + 0.5, y + 0.5))))
    elif role == "boss":                                                            # red zig-zag for bosses
        for x in range(20, 110):
            y = 78 + (abs((x % 8) - 4) - 2)
            for t in range(3):
                if inside(x + 0.5, y + t + 0.5):
                    cv.put(x, y + t, band(CAPRED, lambert(*normal(x + 0.5, y + t + 0.5))))
    soft_spot(cv, cx - 14, cy - 24, 9, 13, (255, 255, 255), 170)
    sparkle(cv, cx - 16, cy - 30, 3)
    outline(cv)
    save(cv, f"egg_{npc_id}", EGG_OUT)

import re
src = open("/home/claude/dbz/DBZ_BP/scripts/npc_data.js").read()
npcs = re.findall(r'id:\s*"([a-z0-9_]+)",\s*name:\s*"[^"]*",\s*color:\s*"[^"]*",\s*role:\s*"([a-z_]+)"', src)
for nid, role in npcs:
    egg(nid, role)
print(f"items: {len([m for m in MADE if '/eggs/' not in m[0]])} item textures, {len(npcs)} eggs")
