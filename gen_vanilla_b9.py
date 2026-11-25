"""Universe 7: Anime Textures - sky & HUD v2 (high detail).
Sun / moon / clouds in textures/environment, hotbar / hearts / hunger / XP in textures/ui.
Icons are drawn at 128x128 (the game scales them into its small HUD slots); bars and slots keep
vanilla proportions at 8x size."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import *
from PIL import Image, ImageFilter

ROOT = "/home/claude/u7_textures/textures"
DONE = []
W = (255, 255, 255)
def save(cv, rel):
    cv.save(f"{ROOT}/{rel}"); DONE.append(rel)

def thick_outline(cv, color, steps=3):
    """Outline several pixels thick so icons stay readable when the HUD shrinks them."""
    for i in range(steps):
        outline(cv, color=mix(color, (0, 0, 0), i / max(1, steps)), diagonal=i > 0)

# ============================================================ SUN
def sun():
    cv = Canvas(); c = 64
    CORE = ramp((255, 214, 80), 6, hi=W, lo=(240, 110, 20))
    rnd = random.Random(1)
    for k in range(18):                                                      # curved flame flares (corona)
        a0 = k * 20 + rnd.uniform(-4, 4); L = rnd.uniform(46, 60); curl = rnd.choice((-1, 1)) * rnd.uniform(6, 12)
        pts = []
        for i in range(12):
            t = i / 11
            a = math.radians(a0 + curl * t)
            r = 26 + (L - 26) * t
            pts.append((c + r * math.cos(a), c + r * math.sin(a)))
        for i in range(11):
            t = i / 11
            axis_shape(cv, pts[i], pts[i + 1], lambda _t, t=t: 6.5 * (1 - t) ** 0.9 + 0.5,
                       lambda _t, s, t=t: mix((255, 250, 200), (255, 140, 30), t) if abs(s) < 0.6 else mix((255, 200, 80), (230, 90, 20), t))
    for a in range(0, 360, 45):                                              # four-point star glints
        L = 62 if a % 90 == 0 else 40
        axis_shape(cv, (c, c), (c + L * math.cos(math.radians(a)), c + L * math.sin(math.radians(a))),
                   lambda t: 2.2 * (1 - t) + 0.3, lambda t, s: mix(W, (255, 236, 160), t))
    sphere(cv, c, c, 30, CORE, gamma=0.5)
    for y in range(cv.h):                                                    # banded inner rings + white-hot centre
        for x in range(cv.w):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if 27 <= d <= 28.5: cv.put(x, y, (255, 250, 210))
            if d < 18: cv.put(x, y, (255, 250, 220), int(120 * (1 - d / 18)))
            if d < 9: cv.put(x, y, W, int(220 * (1 - d / 9)))
    soft_spot(cv, 52, 50, 10, 7, W, 200)
    for y in range(cv.h):                                                    # thin outer halo ring
        for x in range(cv.w):
            d = math.hypot(x + 0.5 - c, y + 0.5 - c)
            if 34 <= d <= 35.5: cv.put(x, y, (255, 240, 180), 170)
    glow(cv, (255, 190, 70), 6, 1.1)
    return cv
save(sun(), "environment/sun.png")

# ============================================================ MOON PHASES (8 x 128px in a 4x2 grid)
MOON = ramp((224, 230, 242), 6, hi=W, lo=(96, 106, 140))
rnd = random.Random(31)
craters = [(rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(0.05, 0.17)) for _ in range(16)]
maria = [(-0.25, -0.15, 0.35), (0.2, 0.25, 0.28), (0.3, -0.35, 0.18)]
PHASE = [1.0, 0.75, 0.5, 0.25, 0.0, -0.25, -0.5, -0.75]                   # vanilla order, + = lit on the right
def moon_disc(k):
    cv = Canvas(); cx = cy = 64; r = 44
    for y in range(128):
        for x in range(128):
            u, v = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            if u * u + v * v > 1: continue
            nz = math.sqrt(max(0, 1 - u * u - v * v))
            L = lambert(u, v, nz) * 0.85 + 0.25
            c = band(MOON, L)
            for (a, b, mr) in maria:                                          # darker "seas"
                if (u - a) ** 2 + (v - b) ** 2 < mr * mr: c = mix(c, MOON[3], 0.45)
            for (a, b, cr) in craters:
                d = math.hypot(u - a, v - b)
                if d < cr:
                    rim = d > cr * 0.75
                    side = (u - a) + (v - b)
                    c = (MOON[0] if side > 0 else MOON[4]) if rim else (MOON[2] if side > 0 else MOON[3])
            edge = math.sqrt(max(0, 1 - v * v))
            if k == 1.0: lit = 1
            elif k == 0.0: lit = 0
            else:
                term = edge * (1 - 2 * abs(k))                                 # terminator ellipse
                pos = u if k > 0 else -u
                lit = 1 if pos > term + 0.06 else (0.5 if pos > term - 0.06 else 0)
            if lit == 0: c = mix(c, (30, 36, 76), 0.84)                         # earthshine side
            elif lit == 0.5: c = mix(c, (90, 96, 150), 0.5)                     # soft terminator band
            cv.put(x, y, c)
    if k != 0:
        arc_light(cv, cx, cy, r, 300 if k > 0 else 120, 60 if k > 0 else 240, W, 200, 2)
        glow(cv, (190, 210, 255), 5, 0.7)
    else:
        arc_light(cv, cx, cy, r, 0, 360, (120, 130, 190), 160, 1.5)
    return cv
moon = Canvas(512, 256)
for i, k in enumerate(PHASE):
    moon.paste(moon_disc(k), (i % 4) * 128, (i // 4) * 128)
save(moon, "environment/moon_phases.png")

# ============================================================ CLOUDS (cell map: each pixel becomes one cloud block)
cl = Canvas(256, 256); rnd = random.Random(41)
def puff(cx, cy, r):
    for y in range(int(cy - r), int(cy + r) + 1):
        for x in range(int(cx - r * 1.7), int(cx + r * 1.7) + 1):
            if ((x - cx) / 1.7) ** 2 + (y - cy) ** 2 <= r * r:
                cl.put(x % 256, y % 256, W)
for _ in range(34):                                                          # big cumulus banks made of many puffs
    cx, cy = rnd.uniform(0, 256), rnd.uniform(0, 256)
    big = rnd.uniform(6, 11)
    for j in range(rnd.randint(6, 12)):
        puff(cx + rnd.uniform(-big * 2.4, big * 2.4), cy + rnd.uniform(-big * 0.6, big * 0.6), big * rnd.uniform(0.45, 0.85))
for _ in range(40):                                                          # small wisps between them
    puff(rnd.uniform(0, 256), rnd.uniform(0, 256), rnd.uniform(1.5, 3.5))
save(cl, "environment/clouds.png")

# ============================================================ HUD
NAVY = ramp((30, 40, 76), 6, hi=(110, 130, 200), lo=(4, 6, 18))
GOLD = ramp((236, 172, 44), 6, hi=(255, 252, 210), lo=(96, 44, 6))

# ---- hotbar slots (vanilla 20x22 -> 160x176), caps, selection (24x24 -> 192x192)
def slot(w=160, h=176):
    """Translucent navy glass well in a slim gold frame with corner brackets."""
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            lit = (x + y) < (w + h) / 2
            if e < 2: c = (6, 4, 2)
            elif e < 5: c = GOLD[1] if lit else GOLD[3]
            elif e < 6: c = GOLD[0] if lit else GOLD[4]
            elif e < 7: c = (14, 10, 6)
            elif e < 8: cv.put(x, y, W, 90); continue                            # inner hairline highlight
            else:
                t = y / h
                c = mix((70, 90, 150), (16, 22, 46), t ** 0.7)                     # lighter at the top
                a = int(150 + 60 * t)
                if y < h * 0.32: c = mix(c, (150, 170, 230), 0.25 * (1 - y / (h * 0.32)))   # soft top sheen
                cv.put(x, y, c, a); continue
            cv.put(x, y, c)
    for (sx, sy, dx, dy) in ((10, 10, 1, 1), (w - 11, 10, -1, 1), (10, h - 11, 1, -1), (w - 11, h - 11, -1, -1)):
        for i in range(16):                                                       # gold L-brackets in the corners
            for k in range(3):
                cv.put(sx + dx * i, sy + dy * k, GOLD[1] if k < 2 else GOLD[4])
                cv.put(sx + dx * k, sy + dy * i, GOLD[1] if k < 2 else GOLD[4])
        sphere(cv, sx + dx * 2, sy + dy * 2, 2.6, GOLD); cv.put(sx + dx * 2 - 1, sy + dy * 2 - 1, W)
    return cv

def cap(w=8, h=176, start=True):
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            e = min(y, h - 1 - y)
            if e < 3 or (x < 3 if start else x > w - 4): c = (6, 4, 2)
            else: c = GOLD[0] if y < h / 2 else GOLD[3]
            cv.put(x, y, c)
    return cv

def selected(w=192, h=192):
    """Glowing ki selection frame: white-hot inner line, gold double frame, smooth aura, corner gems."""
    cv = Canvas(w, h)
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 2: c = (60, 26, 0)
            elif e < 5: c = (255, 214, 70)
            elif e < 6: c = (200, 110, 10)
            elif e < 8: c = (255, 250, 220)
            elif e < 9: c = (200, 110, 10)
            elif e < 12: c = (255, 196, 50)
            elif e < 34:
                k = 1 - (e - 12) / 22
                cv.put(x, y, mix((255, 160, 30), (255, 240, 150), k), int(200 * k ** 2.2)); continue
            else:
                continue
            cv.put(x, y, c)
    for (sx, sy) in ((7, 7), (w - 8, 7), (7, h - 8), (w - 8, h - 8)):          # diamond gems on the corners
        ins = poly_inside([(sx, sy - 9), (sx + 9, sy), (sx, sy + 9), (sx - 9, sy)])
        for yy in range(sy - 10, sy + 11):
            for xx in range(sx - 10, sx + 11):
                if ins(xx + 0.5, yy + 0.5):
                    c = (255, 255, 230) if (xx - sx) + (yy - sy) < -3 else (255, 200, 60) if (xx - sx) < (yy - sy) else (220, 120, 20)
                    cv.put(xx, yy, c)
        sparkle(cv, sx, sy, 12, W)
    for (mx, my) in ((w // 2, 6), (w // 2, h - 7), (6, h // 2), (w - 7, h // 2)):  # mid-edge glints
        sparkle(cv, mx, my, 7, (255, 250, 220))
    return cv

for i in range(9):
    save(slot(), f"ui/hotbar_{i}.png")
save(cap(start=True), "ui/hotbar_start_cap.png")
save(cap(start=False), "ui/hotbar_end_cap.png")
save(selected(), "ui/selected_hotbar_slot.png")

# ---- energy-orb hearts (128x128): glass ki orbs with a heart inside, like a Dragon Ball's star
def heart_inside(cx, cy, size):
    def f(x, y):
        u, v = (x - cx) / size, -(y - cy) / size
        return (u * u + v * v - 1) ** 3 - u * u * v ** 3 < 0
    return f

def ki_orb(col, mode="full", seed=0):
    cv = Canvas(); c = 64; r = 52
    if mode == "empty":                                                         # dark glass socket, engraved heart
        sphere(cv, c, c, r, ramp((44, 36, 66), 5, hi=(120, 108, 150), lo=(6, 4, 12)), gamma=1.4)
        hin = heart_inside(c, c + 2, 24)
        for y in range(30, 100):
            for x in range(30, 100):
                if hin(x + 0.5, y + 0.5):
                    edge = not (hin(x + 2.5, y + 2.5) and hin(x - 1.5, y - 1.5))
                    cv.put(x, y, (70, 60, 96) if edge else (26, 20, 40))
        arc_light(cv, c, c, r, 200, 320, (130, 120, 170), 200, 3)
        soft_spot(cv, c - 18, c - 22, 13, 9, (160, 150, 200), 120)
        thick_outline(cv, (8, 4, 12), 5)
        return cv
    R = ramp(col, 6, hi=W, lo=mix(col, (20, 0, 20), 0.72))
    glass = ramp(mix(col, W, 0.25), 6, hi=W, lo=mix(col, (30, 0, 20), 0.6))
    sphere(cv, c, c, r, glass, gamma=0.8)
    soft_spot(cv, c + 16, c + 20, 26, 18, mix(col, (255, 250, 200), 0.65), 170)   # light focused through the glass
    # the heart "star" inside: deep colour, lit top-left lobe, white edge glints, dark outline
    hin = heart_inside(c - 1, c + 1, 26)
    for y in range(24, 104):
        for x in range(24, 104):
            if hin(x + 0.5, y + 0.5):
                u, v = (x - c) / 26, (y - c) / 26
                L = 0.85 - (u + v) * 0.35
                cv.put(x, y, band(R, L))
    hl = Canvas(); 
    for y in range(24, 104):
        for x in range(24, 104):
            if hin(x + 0.5, y + 0.5): hl.put(x, y, W)
    for y in range(128):                                                         # dark rim around the heart
        for x in range(128):
            if not hin(x + 0.5, y + 0.5) and any(hin(x + 0.5 + dx, y + 0.5 + dy) for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2))):
                cv.put(x, y, mix(col, (0, 0, 0), 0.7))
    soft_spot(cv, c - 12, c - 8, 7, 5, W, 230, mask=lambda x, y: hin(x + 0.5, y + 0.5))   # gloss on the heart
    rnd = random.Random(seed)
    for k in range(2):                                                           # faint ki swirl around the heart
        for i in range(120):
            t = i / 119; a = k * 3.1 + t * 3.6
            rr = r * (0.62 + 0.25 * t)
            cv.put(int(c + rr * math.cos(a)), int(c + rr * math.sin(a) * 0.9), mix(col, W, 0.7), 110)
    soft_spot(cv, c - 18, c - 22, 18, 12, W, 235)                               # glass highlight over everything
    for t in range(34):                                                          # curved window streak
        a = math.radians(194 + t * 1.7)
        for w in range(4):
            cv.put(int(c + (r - 8) * math.cos(a) + w * 0.6), int(c + (r - 8) * math.sin(a) + w * 0.6), W, 230 - w * 50)
    sparkle(cv, c - 24, c - 28, 8)
    arc_light(cv, c, c, r, 10, 120, mix(col, W, 0.6), 230, 4)
    if mode == "flash":
        for y in range(128):
            for x in range(128):
                if cv.get(x, y)[3]: cv.put(x, y, W, 150)
    thick_outline(cv, mix(col, (0, 0, 0), 0.82), 5)
    if mode == "half":
        for y in range(128):
            for x in range(64, 128): cv.px[x, y] = (0, 0, 0, 0)
        for y in range(128):
            for x in range(59, 64):
                if cv.get(x, y)[3]: cv.put(x, y, mix(col, (0, 0, 0), 0.82))
    return cv

HEARTS = {"heart": (240, 50, 60), "poison_heart": (150, 200, 50), "wither_heart": (100, 70, 50), "absorption_heart": (255, 206, 50)}
for name, col in HEARTS.items():
    save(ki_orb(col, "full", 1), f"ui/{name}.png")
    save(ki_orb(col, "half", 1), f"ui/{name}_half.png")
save(ki_orb(HEARTS["heart"], "empty"), "ui/heart_background.png")
save(ki_orb(HEARTS["heart"], "flash", 1), "ui/heart_flash.png")
save(ki_orb(HEARTS["heart"], "flash", 1), "ui/heart_flash_half.png")
fh = ki_orb(HEARTS["heart"], "flash", 1)
for y in range(128):
    for x in range(64, 128): fh.px[x, y] = (0, 0, 0, 0)
save(fh, "ui/heart_flash_half.png")

# ---- Senzu bean hunger (128x128)
def senzu(col=(96, 186, 60), mode="full"):
    cv = Canvas(); cx, cy, rx, ry, rot = 64, 64, 30, 50, -0.35
    nx, ny = math.cos(rot), math.sin(rot)
    cut = lambda x, y: (x - (cx + nx * rx * 1.25)) ** 2 + (y - (cy + ny * rx * 1.25)) ** 2 < (rx * 0.62) ** 2
    if mode == "empty":
        ellipsoid(cv, cx, cy, rx, ry, ramp((60, 50, 50), 4, hi=(120, 104, 100), lo=(10, 6, 6)), rot=rot, gamma=1.3, cut=cut)
        thick_outline(cv, (10, 6, 4), 4); return cv
    R = ramp(col, 6, hi=(244, 255, 210), lo=mix(col, (0, 30, 20), 0.75))
    ellipsoid(cv, cx, cy, rx, ry, R, rot=rot, gamma=0.8, cut=cut)
    for i in range(40):                                                         # faint vein lines
        t = i / 39
        x = cx - 8 + 14 * math.sin(t * 3) ; y = cy - 36 + 72 * t
        if cv.get(int(x), int(y))[3]: cv.put(int(x), int(y), R[3], 140)
    soft_spot(cv, cx - 12, cy - 20, 9, 16, W, 220); sparkle(cv, cx - 14, cy - 28, 6)
    arc_light(cv, cx, cy, 44, 20, 110, mix(col, W, 0.5), 160, 3)
    thick_outline(cv, mix(col, (0, 0, 0), 0.8), 4)
    if mode == "half":
        for y in range(0, 64):
            for x in range(128): cv.px[x, y] = (0, 0, 0, 0)
    return cv
save(senzu(), "ui/hunger_full.png")
save(senzu(mode="half"), "ui/hunger_half.png")
save(senzu(mode="empty"), "ui/hunger_background.png")
save(senzu((150, 120, 60)), "ui/hunger_effect_full.png")
save(senzu((150, 120, 60), "half"), "ui/hunger_effect_half.png")

# ---- ki XP bar (vanilla 182x5 -> 1456x40)
def ki_bar(full):
    w, h = 1456, 40; cv = Canvas(w, h); rnd = random.Random(7)
    E = ramp((70, 180, 255), 6, hi=W, lo=(8, 30, 110))
    for y in range(h):
        for x in range(w):
            e = min(x, y, w - 1 - x, h - 1 - y)
            if e < 3: c = (4, 6, 16)
            elif e < 6: c = GOLD[0] if y < h / 2 else GOLD[3]
            elif e < 7: c = (20, 12, 4)
            elif not full:
                t = (y - 7) / (h - 14)
                c = mix(NAVY[3], NAVY[5], t)
                if (x - 7) % 72 < 2: c = NAVY[1]                                 # segment ticks (5% each)
            else:
                t = (y - 7) / (h - 14)
                c = E[1] if t < 0.18 else E[2] if t < 0.45 else E[3] if t < 0.75 else E[4]
                if 0.3 < t < 0.42: c = mix(c, W, 0.7)                             # white-hot core line
                wave = math.sin(x * 0.045 + t * 6)
                if abs(wave) < 0.08 and 0.15 < t < 0.85: c = mix(c, W, 0.45)    # flowing energy streaks
                if (x - 7) % 72 < 2: c = mix(c, E[4], 0.35)                      # faint segment dividers
                if t < 0.08: c = mix(c, W, 0.5)                                  # bright inner top edge
            cv.put(x, y, c)
    if full:
        for _ in range(40):
            sparkle(cv, rnd.randrange(16, w - 16), rnd.randrange(10, h - 10), 3, W)
    for x in range(7, w - 7, 364):                                               # gold rivets on the frame
        sphere(cv, x + 4, 4, 2.4, GOLD); sphere(cv, x + 4, h - 5, 2.4, GOLD)
    return cv
save(ki_bar(False), "ui/experiencebarempty.png")
save(ki_bar(True), "ui/experiencebarfull.png")
nub = Canvas(8, 40)
for y in range(40):
    for x in range(8): nub.put(x, y, W if 2 < x < 6 else (150, 220, 255))
save(nub, "ui/experiencenub.png")
print("sky & HUD v2:", len(set(DONE)), "files")
