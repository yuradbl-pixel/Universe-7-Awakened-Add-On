"""Universe 7: Anime Textures - vanilla batch 8: food, bow (4 stages) and arrow. 128x128, top-left light."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import *

OUT = "/home/claude/u7_textures/textures/items"
DONE = []
W = (255, 255, 255)
def save(cv, name, out_c):
    outline(cv, color=out_c); cv.save(f"{OUT}/{name}.png"); DONE.append(name)

def R6(c): return ramp(c, 6, hi=mix(c, (255, 252, 236), 0.7), lo=mix(c, (20, 6, 20), 0.75))

def blob(cv, cx, cy, rx, ry, R, rot=0.0, lumps=None, gamma=0.85, cut=None):
    """Shaded organic shape: an ellipsoid with optional radial lumps (for meat, potatoes...)."""
    cs, sn = math.cos(rot), math.sin(rot)
    lumps = lumps or []
    def rad(a):
        return 1 + sum(amp * math.cos(k * a + ph) for k, amp, ph in lumps)
    def local(x, y):
        dx, dy = x - cx, y - cy
        return (dx * cs + dy * sn) / rx, (-dx * sn + dy * cs) / ry
    def inside(x, y):
        u, v = local(x, y)
        return math.hypot(u, v) <= rad(math.atan2(v, u)) and not (cut and cut(x, y))
    def normal(x, y):
        u, v = local(x, y); r = rad(math.atan2(v, u))
        u, v = u / r, v / r
        nz = math.sqrt(max(0.0, 1 - u * u - v * v))
        return u * cs - v * sn, u * sn + v * cs, nz
    shade_shape(cv, inside, normal, R, gamma)
    return inside

# ------------------------------------------------------------ apples
def apple(golden=False):
    cv = Canvas()
    R = R6((255, 200, 40)) if golden else R6((220, 36, 40))
    blob(cv, 64, 72, 40, 38, R, lumps=[(2, 0.05, 0), (1, 0.03, 1.57)])
    for k in (-1, 1):                                                       # top lobes dip at the stem
        for y in range(28, 44):
            for x in range(58, 71):
                if abs(x - 64) < 6 - (y - 28) * 0.3 and y < 38: cv.put(x, y, R[3])
    axis_shape(cv, (64, 38), (70, 18), lambda t: 2.4 - t * 0.8, cylinder_color(R6((120, 80, 40))))   # stem
    LEAF = R6((90, 190, 60))
    blob(cv, 82, 22, 13, 6, LEAF, rot=-0.5)
    cv.draw().line((72, 28, 92, 16), fill=LEAF[3] + (255,))                 # leaf vein
    soft_spot(cv, 46, 52, 11, 15, W, 200); sparkle(cv, 44, 48, 3)
    rnd = random.Random(3)
    for _ in range(40):                                                     # skin speckles
        x, y = rnd.randrange(30, 100), rnd.randrange(40, 108)
        if cv.get(x, y)[3] and cv.get(x, y)[:3] != W: cv.put(x, y, R[1] if golden else (255, 210, 120), 120)
    if golden:
        for p in ((92, 50), (40, 96), (88, 98)): sparkle(cv, *p, 3, (255, 250, 210))
    return cv
save(apple(), "apple", (70, 6, 14))
save(apple(True), "apple_golden", (110, 60, 6))

# ------------------------------------------------------------ bread
cv = Canvas(); CR = R6((200, 120, 50))
blob(cv, 64, 66, 52, 28, CR, rot=-0.45, lumps=[(3, 0.03, 0.5)])
for k in range(-2, 3):                                                       # scored cuts showing soft crumb
    cx, cy = 64 + k * 16 * 0.9, 66 - k * 16 * 0.43
    for i in range(-9, 10):
        x, y = cx + i * 0.45 + 2, cy + i * 0.9 - 4
        for w in range(3):
            cv.put(int(x + w), int(y), (250, 226, 170) if w else (170, 96, 40))
rnd = random.Random(5)
for _ in range(70):
    x, y = rnd.randrange(14, 116), rnd.randrange(30, 100)
    if cv.get(x, y)[3]: cv.put(x, y, (255, 246, 226), 150)                  # flour dust
soft_spot(cv, 44, 50, 14, 7, W, 120)
save(cv, "bread", (70, 30, 10))

# ------------------------------------------------------------ steak (beef)
def steak(cooked):
    cv = Canvas()
    R = R6((150, 80, 40)) if cooked else R6((214, 60, 70))
    inside = blob(cv, 62, 66, 48, 36, R, rot=-0.25, lumps=[(2, 0.08, 0.4), (3, 0.05, 1.2), (5, 0.03, 0)])
    FAT = R6((250, 236, 220)) if not cooked else R6((230, 190, 120))
    for y in range(cv.h):                                                    # fat rim along the upper edge
        for x in range(cv.w):
            if inside(x + 0.5, y + 0.5) and not inside(x + 0.5, y - 5.5) and y < 70:
                cv.put(x, y, FAT[1] if x < 64 else FAT[2])
    rnd = random.Random(7)
    for _ in range(9):                                                       # marbling
        x, y, a = rnd.uniform(30, 96), rnd.uniform(46, 92), rnd.uniform(0, 6.28)
        for _ in range(rnd.randint(6, 14)):
            a += rnd.uniform(-0.6, 0.6); x += math.cos(a); y += math.sin(a)
            if inside(x, y): cv.put(int(x), int(y), FAT[2] if not cooked else R[1])
    sphere(cv, 84, 74, 6, R6((246, 236, 220)))                               # bone cross-section
    cv.put(84, 74, (200, 160, 150))
    if cooked:
        for k in range(4):                                                   # grill marks
            for i in range(-30, 31):
                x, y = 40 + k * 14 + i * 0.55, 66 + i * 0.83
                if inside(x, y):
                    cv.put(int(x), int(y), (60, 24, 10)); cv.put(int(x) + 1, int(y), (90, 40, 16))
        soft_spot(cv, 44, 54, 12, 7, (255, 220, 160), 140)                   # juicy shine
    else:
        soft_spot(cv, 44, 54, 12, 7, W, 160)
    sparkle(cv, 42, 52, 2)
    return cv
save(steak(False), "beef_raw", (90, 10, 24))
save(steak(True), "beef_cooked", (50, 20, 8))

# ------------------------------------------------------------ porkchop (chop with a bone handle)
def porkchop(cooked):
    cv = Canvas()
    R = R6((216, 140, 80)) if cooked else R6((246, 160, 170))
    axis_shape(cv, (84, 82), (114, 112), lambda t: 4.5 + (3 if t > 0.85 else 0), cylinder_color(R6((246, 238, 222))))   # bone
    sphere(cv, 114, 112, 6, R6((246, 238, 222)))
    inside = blob(cv, 56, 56, 40, 32, R, rot=0.5, lumps=[(2, 0.07, 0), (3, 0.04, 2)])
    FAT = R6((255, 236, 236)) if not cooked else R6((246, 200, 130))
    for y in range(cv.h):
        for x in range(cv.w):
            if inside(x + 0.5, y + 0.5) and not inside(x + 4.5, y + 4.5):
                cv.put(x, y, FAT[2])
    if cooked:
        rnd = random.Random(9)
        for _ in range(60):
            x, y = rnd.randrange(20, 96), rnd.randrange(24, 90)
            if inside(x, y): cv.put(x, y, R[4], 140)                         # seared spots
    soft_spot(cv, 40, 40, 12, 8, W, 170); sparkle(cv, 38, 38, 2)
    return cv
save(porkchop(False), "porkchop_raw", (110, 40, 56))
save(porkchop(True), "porkchop_cooked", (70, 30, 10))

# ------------------------------------------------------------ chicken drumstick
def drumstick(cooked):
    cv = Canvas()
    R = R6((214, 140, 60)) if cooked else R6((246, 196, 180))
    axis_shape(cv, (78, 78), (110, 110), lambda t: 4, cylinder_color(R6((248, 240, 226))))
    for (bx, by) in ((112, 104), (104, 112)):                                # knobbly bone end
        sphere(cv, bx, by, 6, R6((248, 240, 226)))
    blob(cv, 54, 54, 40, 30, R, rot=0.78, lumps=[(2, 0.04, 0)], cut=None)
    rnd = random.Random(11)
    for _ in range(90):                                                      # crispy skin texture / goosebumps
        x, y = rnd.randrange(16, 96), rnd.randrange(16, 96)
        if cv.get(x, y)[3] and cv.get(x, y)[:3] != (0, 0, 0):
            cv.put(x, y, R[1] if rnd.random() < 0.5 else R[3], 170)
    soft_spot(cv, 40, 38, 12, 8, W, 170); sparkle(cv, 38, 36, 2)
    return cv
save(drumstick(False), "chicken_raw", (120, 70, 60))
save(drumstick(True), "chicken_cooked", (80, 40, 10))

# ------------------------------------------------------------ carrot
cv = Canvas(); OR = R6((250, 130, 30))
axis_shape(cv, (96, 34), (20, 110), lambda t: 15 * (1 - t) ** 0.8 + 1, lambda t, s: band(OR, 0.85 - s * 0.45 - t * 0.1))
for k in range(1, 9):                                                         # growth rings
    t = k / 10
    x, y = 96 - 76 * t, 34 + 76 * t
    w = 15 * (1 - t) ** 0.8
    for i in range(int(-w), int(w * 0.6)):
        cv.put(int(x + i * 0.707), int(y + i * 0.707), OR[3])
LEAF = R6((90, 190, 60))
for ang, L in ((-1.9, 30), (-1.3, 34), (-0.7, 26)):                         # leafy top
    axis_shape(cv, (98, 32), (98 + L * math.cos(ang), 32 + L * math.sin(ang)), lambda t: 5 * (1 - t) + 1, lambda t, s: band(LEAF, 0.85 - s * 0.4))
soft_spot(cv, 74, 50, 6, 10, W, 160)
save(cv, "carrot", (100, 40, 6))

# ------------------------------------------------------------ potatoes
def potato(baked):
    cv = Canvas()
    R = R6((214, 170, 100)) if not baked else R6((200, 130, 60))
    inside = blob(cv, 64, 66, 46, 32, R, rot=-0.3, lumps=[(3, 0.06, 0.3), (5, 0.04, 1.0)])
    rnd = random.Random(13 + baked)
    for _ in range(7):                                                       # eyes
        x, y = rnd.uniform(30, 98), rnd.uniform(46, 88)
        if inside(x, y): cv.put(int(x), int(y), R[4]); cv.put(int(x) + 1, int(y), R[3])
    if baked:                                                                # split top, fluffy inside, butter pat
        for y in range(46, 70):
            for x in range(40, 90):
                if abs((x - 64) * 0.35 + (y - 58)) < 6 - abs(x - 64) * 0.12 and inside(x, y):
                    cv.put(x, y, (255, 240, 190) if (x + y) % 3 else (250, 226, 160))
        blob(cv, 62, 54, 8, 6, R6((255, 226, 90)), rot=0.2)
        soft_spot(cv, 60, 52, 3, 2, W, 220)
    soft_spot(cv, 42, 52, 10, 7, W, 140)
    return cv
save(potato(False), "potato", (80, 50, 20))
save(potato(True), "potato_baked", (80, 40, 10))

# ------------------------------------------------------------ cookie
cv = Canvas(); CK = R6((210, 150, 80))
inside = blob(cv, 64, 64, 48, 46, CK, lumps=[(7, 0.02, 0)], gamma=0.7)
rnd = random.Random(17)
for _ in range(8):                                                           # chocolate chips
    x, y = rnd.uniform(30, 98), rnd.uniform(30, 98)
    if inside(x, y): blob(cv, x, y, 6, 5, R6((80, 44, 24)), rot=rnd.uniform(0, 3))
for _ in range(5):                                                           # cracks in the top
    x, y, a = rnd.uniform(36, 92), rnd.uniform(36, 92), rnd.uniform(0, 6.28)
    for _ in range(rnd.randint(6, 12)):
        a += rnd.uniform(-0.6, 0.6); x += math.cos(a); y += math.sin(a)
        if inside(x, y): cv.put(int(x), int(y), CK[4])
soft_spot(cv, 44, 42, 12, 8, W, 120)
save(cv, "cookie", (80, 44, 16))

# ------------------------------------------------------------ cake (whole cake, 3/4 view)
cv = Canvas(); SP = R6((236, 200, 140)); IC = R6((252, 250, 246))
for y in range(56, 104):                                                     # sponge side with a jam layer
    for x in range(16, 113):
        if ((x - 64) / 48) ** 2 + ((y - 100) / 14) ** 2 <= 1 or 56 <= y <= 100:
            nx = (x - 64) / 48
            c = band(SP, lambert(nx, 0.2, math.sqrt(max(0, 1 - nx * nx))))
            if 76 <= y <= 80: c = band(R6((210, 40, 70)), lambert(nx, 0, 0.7))
            cv.put(x, y, c)
for y in range(30, 82):                                                      # icing top (ellipse) with drips
    for x in range(16, 113):
        if ((x - 64) / 48) ** 2 + ((y - 56) / 20) ** 2 <= 1:
            cv.put(x, y, band(IC, 0.9 - ((x - 64) / 48 + (y - 56) / 20) * 0.25))
for k in range(9):
    x = 20 + k * 11; L = 6 + (k * 7) % 9
    for y in range(64, 64 + L):
        for dx in range(4):
            cv.put(x + dx, y + int(abs(x - 64) * 0.0), IC[1] if dx < 2 else IC[2])
    sphere(cv, x + 2, 64 + L, 2.2, IC)
for (x, y) in ((40, 50), (64, 44), (88, 50), (52, 62), (78, 62)):            # cherries
    sphere(cv, x, y, 5, R6((220, 30, 40))); cv.put(x - 2, y - 2, W)
    cv.draw().line((x, y - 5, x + 3, y - 11), fill=(70, 120, 40, 255))
save(cv, "cake", (90, 60, 40))

# ------------------------------------------------------------ melon slice
cv = Canvas()
RED = R6((240, 60, 70)); RIND = R6((60, 160, 60))
for y in range(cv.h):
    for x in range(cv.w):
        dx, dy = x + 0.5 - 64, y + 0.5 - 20
        r = math.hypot(dx, dy); a = math.degrees(math.atan2(dy, dx))
        if 50 <= a <= 130 and r <= 96:
            if r > 90: c = band(RIND, 0.8 - (a - 50) / 160)
            elif r > 84: c = (240, 250, 220)
            else: c = band(RED, 0.95 - r / 140 - (a - 50) / 300)
            cv.put(x, y, c)
rnd = random.Random(19)
for _ in range(12):                                                          # seeds
    r, a = rnd.uniform(30, 76), math.radians(rnd.uniform(60, 120))
    x, y = 64 + r * math.cos(a), 20 + r * math.sin(a)
    blob(cv, x, y, 2.4, 3.6, R6((40, 30, 30)), rot=a)
soft_spot(cv, 52, 60, 6, 14, W, 130)
save(cv, "melon", (90, 14, 20))

# ------------------------------------------------------------ bow (standby + 3 pull stages) and arrow
BW = R6((176, 112, 56)); STR = (236, 236, 226)
def bow(pull):
    cv = Canvas()
    top, bot = (100, 12), (12, 100)
    # limbs: an arc bending away from the string, more when pulled
    bend = 26 + pull * 6
    mid = (56 + bend * 0.707, 56 + bend * 0.707)
    pts = []
    for i in range(41):
        t = i / 40
        x = (1 - t) ** 2 * top[0] + 2 * (1 - t) * t * (mid[0] + bend * 0.5 * 0.707) + t * t * bot[0]
        y = (1 - t) ** 2 * top[1] + 2 * (1 - t) * t * (mid[1] + bend * 0.5 * 0.707) + t * t * bot[1]
        pts.append((x, y))
    for i in range(40):
        a, b = pts[i], pts[i + 1]
        t = i / 40
        w = 3.2 + 2.2 * math.sin(math.pi * t)                                # thicker at the grip
        axis_shape(cv, a, b, lambda _t, w=w: w, lambda _t, s: band(BW, 0.85 - s * 0.45))
    gx, gy = pts[20]
    axis_shape(cv, (gx - 6, gy + 6), (gx + 6, gy - 6), lambda t: 6.2,
               lambda t, s: band(R6((120, 60, 40)), 0.8 - s * 0.4) if int(t * 8) % 2 == 0 else band(R6((90, 40, 26)), 0.6))   # grip wrap
    for (tx, ty) in (top, bot):
        sphere(cv, tx, ty, 3.4, R6((230, 200, 120)))                         # nock tips
    nock = (56 - pull * 10, 56 - pull * 10)
    d = cv.draw()
    d.line((top, nock, bot), fill=STR + (255,), width=1)
    if pull > 0:                                                              # nocked arrow
        arrow(cv, (nock[0] + 2, nock[1] + 2), (gx + 16 - pull * 0, gy + 16), scale=0.8)
    return cv

def arrow(cv, tail, head, scale=1.0):
    SH = R6((200, 160, 100)); FE = R6((240, 240, 246)); HD = R6((180, 186, 200))
    axis_shape(cv, tail, head, lambda t: 1.8 * scale, cylinder_color(SH))
    dx, dy = head[0] - tail[0], head[1] - tail[1]; L = math.hypot(dx, dy); ux, uy = dx / L, dy / L
    tip = (head[0] + ux * 12 * scale, head[1] + uy * 12 * scale)
    axis_shape(cv, head, tip, lambda t: 6 * scale * (1 - t) + 0.4, lambda t, s: band(HD, 0.9 - s * 0.5))
    for k in (-1, 1):                                                         # fletching
        fx, fy = -uy * k, ux * k
        for i in range(int(16 * scale)):
            bx, by = tail[0] + ux * (i + 2), tail[1] + uy * (i + 2)
            w = (16 * scale - i) * 0.45
            for j in range(int(w)):
                cv.put(int(bx + fx * j), int(by + fy * j), FE[1] if k < 0 else FE[3])
    cv.put(int(tip[0] - ux * 4), int(tip[1] - uy * 4), W)

for p, name in ((0, "bow_standby"), (1, "bow_pulling_0"), (2, "bow_pulling_1"), (3, "bow_pulling_2")):
    save(bow(p), name, (50, 26, 10))
cv = Canvas(); arrow(cv, (20, 108), (96, 32), 1.4)
save(cv, "arrow", (40, 30, 30))
print("vanilla batch 8:", len(DONE), DONE)
