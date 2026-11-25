"""Universe 7 texture pack, category 2: UI (icons, HUD bars, panels and buttons)."""
import math, os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageOps
from pixlib import *

RP = "/home/claude/dbz/DBZ_RP"
ICONS = f"{RP}/textures/ui/dbz/icons"
HUD = f"{RP}/textures/ui/dbz/hud"
PANELS = f"{RP}/textures/ui/dbz/panels"
for d in (ICONS, HUD, PANELS):
    os.makedirs(d, exist_ok=True)
MADE = []

NAVY = ramp((34, 42, 74), 5, hi=(110, 130, 190), lo=(6, 8, 20))
GOLD = ramp((236, 170, 40), 6, hi=(255, 250, 200), lo=(90, 40, 10))
WHITE = (255, 255, 255)

# ------------------------------------------------------------------ shared icon pieces
def badge():
    cv = Canvas()
    sphere(cv, 64, 64, 60, GOLD, gamma=0.8)
    sphere(cv, 64, 64, 52, NAVY, gamma=1.2)
    arc_light(cv, 64, 64, 52, 180, 300, (90, 110, 170), 160, 2)
    for a in range(0, 360, 30):
        x, y = 64 + 56 * math.cos(math.radians(a)), 64 + 56 * math.sin(math.radians(a))
        cv.put(int(x), int(y), GOLD[0]); cv.put(int(x) + 1, int(y) + 1, GOLD[4])
    return cv

def energy_ramp(col):
    return ramp(col, 5, hi=(255, 255, 255), lo=tuple(int(v * 0.35) for v in col))

def orb(cv, cx, cy, r, col, core=True):
    sphere(cv, cx, cy, r, energy_ramp(col), gamma=0.7)
    if core:
        soft_spot(cv, cx - r * 0.25, cy - r * 0.3, r * 0.45, r * 0.38, WHITE, 230)
        sparkle(cv, int(cx - r * 0.35), int(cy - r * 0.4), max(1, int(r / 7)))

def beam(cv, p0, p1, w, col, taper_start=True):
    e = energy_ramp(col)
    prof = (lambda t: w * (0.45 + 0.55 * min(1, t * 4))) if taper_start else (lambda t: w)
    def colr(t, s):
        a = abs(s)
        return e[0] if a < 0.3 else e[1] if a < 0.6 else e[2] if a < 0.85 else e[3]
    axis_shape(cv, p0, p1, prof, colr)

def rays(cv, cx, cy, n, r0, r1, w, col, offset=0):
    for i in range(n):
        a = math.radians(offset + i * 360 / n)
        L = r1 if i % 2 == 0 else r1 * 0.72
        axis_shape(cv, (cx + r0 * math.cos(a), cy + r0 * math.sin(a)), (cx + L * math.cos(a), cy + L * math.sin(a)),
                   lambda t: w * (1 - t) + 0.4, lambda t, s: mix(WHITE, col, t))

def flames(cv, cx, base_y, col, spikes=((-20, 30, 8), (-10, 42, 9), (0, 50, 10), (10, 42, 9), (20, 30, 8))):
    F = ramp(col, 5, hi=(255, 255, 230), lo=tuple(int(v * 0.4) for v in col))
    for dx, h, w in spikes:
        axis_shape(cv, (cx + dx * 0.6, base_y), (cx + dx * 1.25, base_y - h), lambda t, w=w: w * (1 - t) ** 0.8 + 0.3,
                   lambda t, s: band(F, 1 - t * 0.7 + (-s) * 0.15))

def finish(fx, glow_col, name, base=None):
    """Glow the effect layer, put it on the badge, outline, save normal + locked versions."""
    glow(fx, glow_col, 5, 0.9)
    cv = base or badge()
    cv.paste(fx)
    outline(cv, color=(18, 12, 6))
    path = f"{ICONS}/{name}.png"
    cv.save(path); MADE.append((path, name))
    save_locked(cv, name)

PADLOCK_BODY = ramp((200, 204, 214), 5, hi=WHITE, lo=(30, 34, 50))
def save_locked(cv, name):
    """Locked version: greyscale, darkened, with a steel padlock in the lower right."""
    g = ImageOps.grayscale(cv.im.convert("RGB")).point(lambda v: int(v * 0.55))
    im = Image.merge("RGBA", (g, g, g, cv.im.split()[3]))
    lk = Canvas(); lk.paste(im)
    for y in range(64, 88):                                              # shackle
        for x in range(80, 113):
            d = math.hypot(x + 0.5 - 96, y + 0.5 - 86)
            if 10 <= d <= 15 and y <= 86:
                lk.put(x, y, band(PADLOCK_BODY, lambert((x - 96) / 15, (y - 86) / 15, 0.6)))
    body = lambda x, y: 78 <= x <= 114 and 84 <= y <= 114
    shade_shape(lk, body, lambda x, y: ((x - 96) / 60, (y - 99) / 60, 0.9), ramp((230, 180, 50), 5, hi=WHITE, lo=(80, 40, 10)))
    sphere(lk, 96, 96, 4, ramp((40, 30, 20), 3));
    for y in range(98, 106):
        lk.put(95, y, (30, 22, 14)); lk.put(96, y, (30, 22, 14))
    outline(lk, color=(10, 8, 6))
    path = f"{ICONS}/{name}_locked.png"
    lk.save(path); MADE.append((path, name + "_locked"))

def dots(cv, pts, col, r=2):
    for x, y in pts:
        orb(cv, x, y, r, col, core=False)

# ------------------------------------------------------------------ MOVE ICONS
C = {"blue": (70, 170, 255), "yellow": (255, 220, 60), "purple": (170, 80, 255), "pink": (255, 110, 190),
     "orange": (255, 140, 40), "red": (240, 50, 40), "white": (230, 240, 255), "green": (90, 230, 110),
     "cyan": (90, 230, 255), "magenta": (230, 60, 200), "gold": (255, 200, 60)}

def mv_ki_blast():
    fx = Canvas()
    for i in range(6):                                                    # comet trail
        orb(fx, 34 + i * 7, 92 - i * 7, 3 + i, C["blue"], core=False)
    orb(fx, 80, 48, 16, C["blue"])
    return fx, C["blue"]

def mv_death_beam():
    fx = Canvas(); beam(fx, (24, 100), (108, 30), 3.2, C["magenta"])
    rays(fx, 26, 98, 8, 2, 12, 2, C["pink"]); orb(fx, 26, 98, 6, C["pink"])
    return fx, C["magenta"]

def mv_candy_beam():
    fx = Canvas()
    pts = [(22 + i * 9, 92 - i * 7 + (6 if i % 2 else -6)) for i in range(8)]
    for a, b in zip(pts, pts[1:]):
        beam(fx, a, b, 4, C["pink"], taper_start=False)
    cv = fx                                                               # a wrapped candy at the end
    ellipsoid(cv, 92, 40, 12, 8, ramp((255, 120, 200), 5, hi=WHITE), rot=-0.6)
    for sx in (-1, 1):
        tip = (92 + sx * 16 * math.cos(-0.6), 40 + sx * 16 * math.sin(-0.6))
        axis_shape(cv, (92 + sx * 9 * math.cos(-0.6), 40 + sx * 9 * math.sin(-0.6)), tip, lambda t: 2 + t * 5,
                   lambda t, s: band(ramp((255, 200, 230), 4, hi=WHITE), 0.8 - s * 0.2))
    for i in range(-8, 9, 4):
        cv.put(92 + i, 40 - int(i * 0.7), (255, 255, 255))
    return fx, C["pink"]

def mv_masenko():
    fx = Canvas(); beam(fx, (30, 34), (110, 96), 10, C["yellow"])
    for p in ((22, 26), (30, 22), (22, 36)):
        orb(fx, *p, 5, C["yellow"], core=False)
    orb(fx, 26, 30, 9, C["yellow"])
    return fx, C["yellow"]

def mv_kamehameha():
    fx = Canvas(); beam(fx, (38, 82), (112, 40), 13, C["blue"])
    orb(fx, 36, 84, 20, C["blue"]); rays(fx, 36, 84, 10, 18, 28, 2.4, C["cyan"])
    return fx, C["blue"]

def mv_hells_flash():
    fx = Canvas(); beam(fx, (20, 64), (112, 64), 15, C["orange"])
    for x in range(36, 110, 16):
        sparks_ = [(x, 44), (x + 4, 40), (x + 2, 36), (x + 6, 32)]
        fx.draw().line(sparks_, fill=(255, 240, 160, 255))
    orb(fx, 22, 64, 14, C["orange"])
    return fx, C["orange"]

def mv_destructo_disc():
    fx = Canvas()
    E = energy_ramp(C["yellow"])
    for y in range(fx.h):                                                 # flat spinning disc with a serrated rim
        for x in range(fx.w):
            u, v = (x - 64) / 40, (y - 60) / 13
            d = u * u + v * v
            if d <= 1:
                ang = math.atan2(v, u)
                teeth = 0.88 + 0.12 * (1 if int((ang + math.pi) * 10) % 2 else 0)
                if d <= teeth:
                    fx.put(x, y, E[0] if d < 0.25 else E[1] if d < 0.6 else E[2])
    for r in (46, 52):                                                    # motion arcs
        for a in range(200, 320, 3):
            fx.put(int(64 + r * math.cos(math.radians(a))), int(60 + r * 0.35 * math.sin(math.radians(a)) + 18), (255, 240, 170), 200)
    orb(fx, 64, 96, 8, C["yellow"])                                        # held up on a fingertip
    axis_shape(fx, (64, 96), (64, 76), lambda t: 1.5, lambda t, s: E[1])
    return fx, C["yellow"]

def mv_galick_gun():
    fx = Canvas(); beam(fx, (30, 40), (112, 98), 14, C["purple"])
    orb(fx, 30, 40, 18, C["purple"])
    for i in range(5):                                                    # crackle along the beam
        x = 46 + i * 13; y = 52 + i * 9
        fx.draw().line([(x, y - 14), (x + 3, y - 18), (x + 1, y - 22)], fill=(240, 200, 255, 255))
    return fx, C["purple"]

def mv_special_beam_cannon():
    fx = Canvas(); beam(fx, (20, 104), (108, 24), 4, C["yellow"])
    for i in range(70):                                                   # purple helix around the drill beam
        t = i / 70; ang = t * 9 * math.pi
        bx, by = 20 + 88 * t, 104 - 80 * t
        off = 9 * math.sin(ang)
        x, y = bx + off * 0.67, by + off * 0.74
        orb(fx, x, y, 2.2 if math.cos(ang) > 0 else 1.6, C["purple"] if math.cos(ang) > 0 else (120, 50, 200), core=False)
    return fx, C["yellow"]

def mv_sphere_of_destruction():
    fx = Canvas()
    sphere(fx, 64, 62, 34, ramp((200, 40, 60), 6, hi=(255, 160, 140), lo=(20, 0, 20)), gamma=1.1)
    arc_light(fx, 64, 62, 34, 0, 360, (255, 90, 200), 200, 3)
    soft_spot(fx, 52, 48, 10, 7, (255, 200, 200), 170)
    return fx, C["magenta"]

def mv_big_bang_attack():
    fx = Canvas(); rays(fx, 64, 64, 4, 10, 58, 4, C["cyan"], offset=45); rays(fx, 64, 64, 4, 10, 44, 3, C["white"])
    orb(fx, 64, 64, 22, C["cyan"])
    return fx, C["cyan"]

def mv_supernova():
    fx = Canvas(); rays(fx, 64, 60, 16, 30, 52, 3.5, C["orange"])
    sphere(fx, 64, 60, 32, ramp((255, 120, 40), 6, hi=(255, 250, 200), lo=(140, 20, 10)), gamma=0.8)
    for i in range(10):                                                   # surface swirls
        a = math.radians(i * 36); fx.put(int(64 + 20 * math.cos(a)), int(60 + 20 * math.sin(a)), (255, 230, 140))
    soft_spot(fx, 54, 48, 12, 9, WHITE, 180)
    return fx, C["orange"]

def mv_final_flash():
    fx = Canvas(); beam(fx, (18, 96), (112, 40), 18, C["yellow"])
    rays(fx, 22, 94, 8, 10, 34, 3, C["yellow"]); orb(fx, 22, 94, 12, C["yellow"])
    return fx, C["yellow"]

def mv_spirit_bomb():
    fx = Canvas()
    rnd = random.Random(5)
    for _ in range(14):                                                   # energy gathering in from all around
        a = rnd.uniform(0, 2 * math.pi); r = rnd.uniform(44, 54)
        x, y = 64 + r * math.cos(a), 58 + r * math.sin(a)
        axis_shape(fx, (x, y), (64 + 38 * math.cos(a), 58 + 38 * math.sin(a)), lambda t: 1.4, lambda t, s: mix((200, 230, 255), (120, 190, 255), t))
        orb(fx, x, y, 2, C["white"], core=False)
    orb(fx, 64, 58, 34, (130, 200, 255))
    return fx, (150, 210, 255)

def mv_solar_flare():
    fx = Canvas(); rays(fx, 64, 64, 16, 8, 56, 5, C["yellow"]); rays(fx, 64, 64, 8, 6, 40, 3, C["white"], offset=11)
    orb(fx, 64, 64, 18, (255, 250, 210))
    return fx, (255, 250, 200)

def mv_majin_rage():
    fx = Canvas()
    for (x, y, r) in ((40, 84, 12), (54, 74, 14), (70, 80, 12), (86, 70, 14), (60, 92, 10)):   # steam puffs
        sphere(fx, x, y, r, ramp((255, 200, 230), 5, hi=WHITE, lo=(160, 80, 120)))
    for dx, dy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):                    # anger burst mark
        axis_shape(fx, (78 + dx * 4, 36 + dy * 4), (78 + dx * 14, 36 + dy * 14), lambda t: 3.5 * (1 - t * 0.5),
                   lambda t, s: band(ramp((255, 60, 120), 4, hi=(255, 200, 220)), 0.8 - s * 0.2))
    return fx, C["pink"]

def mv_barrier():
    fx = Canvas(); E = energy_ramp(C["cyan"])
    for y in range(fx.h):
        for x in range(fx.w):
            d = math.hypot(x - 64, (y - 70) * 1.05)
            if d <= 46 and y <= 98:
                rim = d / 46
                fx.put(x, y, E[0] if rim > 0.93 else E[1], 255 if rim > 0.93 else int(60 + 150 * rim ** 3))
    for i in range(0, 46, 8):                                              # hex sheen
        fx.put(48 + i // 2, 44 + i // 3, WHITE, 200)
    soft_spot(fx, 48, 42, 10, 8, WHITE, 200)
    axis_shape(fx, (16, 98), (112, 98), lambda t: 2, lambda t, s: E[1])
    return fx, C["cyan"]

def mv_kaioken():
    fx = Canvas(); flames(fx, 64, 104, C["red"], ((-30, 44, 10), (-15, 62, 12), (0, 76, 14), (15, 62, 12), (30, 44, 10)))
    for k, yy in enumerate((64, 50)):                                       # x2 style power chevrons
        pts = [(48, yy + 10), (64, yy), (80, yy + 10), (80, yy + 15), (64, yy + 5), (48, yy + 15)]
        ins = poly_inside(pts)
        for y in range(yy - 1, yy + 17):
            for x in range(46, 82):
                if ins(x + 0.5, y + 0.5):
                    fx.put(x, y, WHITE)
    return fx, C["red"]

def mv_instant_transmission():
    fx = Canvas()
    for r, a in ((40, 150), (30, 200), (20, 255)):                         # portal rings
        for ang in range(0, 360, 2):
            x, y = 64 + r * math.cos(math.radians(ang)), 64 + r * 0.42 * math.sin(math.radians(ang))
            fx.put(int(x), int(y), (150, 230, 255), a); fx.put(int(x), int(y) + 1, (60, 140, 230), a)
    for x in range(30, 100, 7):                                            # vertical speed streaks
        L = 18 + (x * 13) % 22
        axis_shape(fx, (x, 64), (x, 64 - L), lambda t: 1.3 * (1 - t) + 0.2, lambda t, s: mix(WHITE, (120, 200, 255), t))
    dots(fx, [(44, 30), (82, 24), (96, 40), (36, 46)], C["cyan"], 2)
    return fx, C["cyan"]

def mv_dragon_fist():
    fx = Canvas(); G = ramp((255, 196, 50), 6, hi=WHITE, lo=(120, 50, 0))
    pts = []
    for i in range(90):                                                    # coiling golden serpent body
        t = i / 89; ang = t * 3.2 * math.pi
        pts.append((26 + 70 * t + 14 * math.cos(ang) * (1 - t * 0.4), 100 - 70 * t + 14 * math.sin(ang) * (1 - t * 0.4)))
    for i, (x, y) in enumerate(pts):
        r = 3 + 6 * (i / 89)
        sphere(fx, x, y, r, G, gamma=0.8)
    hx, hy = pts[-1]
    for k in (-1, 1):                                                      # horns on the head
        axis_shape(fx, (hx, hy - 4), (hx + 10 * k + 6, hy - 18), lambda t: 2.5 * (1 - t) + 0.3, lambda t, s: G[1])
    fx.put(int(hx) + 3, int(hy) - 2, (200, 20, 20)); fx.put(int(hx) + 4, int(hy) - 2, (200, 20, 20))
    rays(fx, 24, 100, 8, 4, 18, 2.4, C["gold"])
    return fx, C["gold"]

def mv_hakai():
    fx = Canvas()
    sphere(fx, 64, 64, 28, ramp((150, 60, 230), 6, hi=(240, 210, 255), lo=(20, 0, 40)), gamma=1.2)
    sphere(fx, 64, 64, 12, ramp((40, 10, 60), 4, lo=(0, 0, 0)))
    rnd = random.Random(9)
    for _ in range(18):                                                    # crumbling fragments drifting up
        x, y = rnd.uniform(30, 100), rnd.uniform(16, 56)
        s = rnd.randint(2, 4)
        for yy in range(s):
            for xx in range(s - yy):
                fx.put(int(x) + xx, int(y) + yy, (190, 130, 255) if (xx + yy) % 2 else (100, 40, 170))
    arc_light(fx, 64, 64, 28, 0, 360, (220, 160, 255), 220, 2.5)
    return fx, C["purple"]

MOVE_ICONS = {
    "ki_blast": mv_ki_blast, "death_beam": mv_death_beam, "candy_beam": mv_candy_beam, "masenko": mv_masenko,
    "kamehameha": mv_kamehameha, "hells_flash": mv_hells_flash, "destructo_disc": mv_destructo_disc,
    "galick_gun": mv_galick_gun, "special_beam_cannon": mv_special_beam_cannon,
    "sphere_of_destruction": mv_sphere_of_destruction, "big_bang_attack": mv_big_bang_attack,
    "supernova": mv_supernova, "final_flash": mv_final_flash, "spirit_bomb": mv_spirit_bomb,
    "solar_flare": mv_solar_flare, "majin_rage": mv_majin_rage, "barrier": mv_barrier, "kaioken": mv_kaioken,
    "instant_transmission": mv_instant_transmission, "dragon_fist": mv_dragon_fist, "hakai": mv_hakai,
}
for mid, fn in MOVE_ICONS.items():
    fx, gc = fn()
    finish(fx, gc, f"icon_{mid}")

# ------------------------------------------------------------------ TRANSFORMATION ICONS
def glyph(cv, kind, cx, cy, col=WHITE):
    """Small white emblems drawn on the form's core orb."""
    d = cv.draw()
    if kind in "1234":
        digits(cv, kind, cx - 5, cy - 8, 4 if kind != "1" else 4, col, shadow=(0, 0, 0))
    elif kind == "halo":
        for a in range(0, 360, 2):
            x, y = cx + 11 * math.cos(math.radians(a)), cy - 2 + 4 * math.sin(math.radians(a))
            cv.put(int(x), int(y), col); cv.put(int(x), int(y) + 1, (255, 230, 140))
    elif kind == "eye":
        for a in range(200, 341, 3):
            cv.put(int(cx + 10 * math.cos(math.radians(a))), int(cy + 6 + 8 * math.sin(math.radians(a))), col)
        for a in range(20, 161, 3):
            cv.put(int(cx + 10 * math.cos(math.radians(a))), int(cy - 6 + 8 * math.sin(math.radians(a))), col)
        sphere(cv, cx, cy, 3, ramp((230, 236, 255), 3))
    elif kind == "bolt":
        pts = [(cx + 2, cy - 12), (cx - 6, cy + 1), (cx, cy + 1), (cx - 3, cy + 12), (cx + 7, cy - 2), (cx + 1, cy - 2)]
        ins = poly_inside(pts)
        for y in range(cy - 13, cy + 13):
            for x in range(cx - 8, cx + 9):
                if ins(x + 0.5, y + 0.5): cv.put(x, y, col)
    elif kind == "horn":
        for k in (-1, 1):
            axis_shape(cv, (cx + 6 * k, cy + 6), (cx + 10 * k, cy - 12), lambda t: 3 * (1 - t) + 0.3, lambda t, s: col)
    elif kind == "drop":
        ins = lambda x, y: (x - cx) ** 2 + (y - cy - 3) ** 2 <= 49 or (abs(x - cx) < (y - (cy - 12)) * 0.5 and y < cy)
        for y in range(cy - 13, cy + 11):
            for x in range(cx - 8, cx + 9):
                if ins(x + 0.5, y + 0.5): cv.put(x, y, col)
    elif kind == "curl":
        for i in range(60):
            t = i / 59; a = t * 1.7 * math.pi
            r = 10 * (1 - t * 0.6)
            sphere(cv, cx + r * math.cos(a), cy + r * math.sin(a), 2.4 * (1 - t * 0.5) + 0.8, ramp(col, 3))
    elif kind == "gear":
        for y in range(cy - 13, cy + 14):
            for x in range(cx - 13, cx + 14):
                dd = math.hypot(x - cx, y - cy); a = math.atan2(y - cy, x - cx)
                R = 11 if int((a + math.pi) / (math.pi / 4)) % 2 else 13
                if 5 <= dd <= R: cv.put(x, y, col)
    elif kind == "star":
        ins = poly_inside(star_poly(cx, cy, 12, 5))
        for y in range(cy - 13, cy + 13):
            for x in range(cx - 13, cx + 13):
                if ins(x + 0.5, y + 0.5): cv.put(x, y, col)
    elif kind == "petal":
        for k in range(5):
            a = math.radians(-90 + k * 72)
            ellipsoid(cv, cx + 7 * math.cos(a), cy + 7 * math.sin(a), 4, 6, ramp((255, 220, 236), 3, hi=WHITE), rot=a + math.pi / 2)
        sphere(cv, cx, cy, 3, ramp((255, 210, 90), 3))
    elif kind == "crown":
        pts = [(cx - 12, cy + 8), (cx - 12, cy - 6), (cx - 6, cy + 1), (cx, cy - 12), (cx + 6, cy + 1), (cx + 12, cy - 6), (cx + 12, cy + 8)]
        ins = poly_inside(pts)
        for y in range(cy - 13, cy + 9):
            for x in range(cx - 13, cx + 13):
                if ins(x + 0.5, y + 0.5): cv.put(x, y, col)
    elif kind == "claw":
        for k in (-7, 0, 7):
            axis_shape(cv, (cx + k - 4, cy + 12), (cx + k + 4, cy - 12), lambda t: 1.8, lambda t, s: col)
    elif kind == "arrow":
        for yy in (cy + 2, cy - 8):
            pts = [(cx - 11, yy + 8), (cx, yy - 2), (cx + 11, yy + 8), (cx + 11, yy + 12), (cx, yy + 2), (cx - 11, yy + 12)]
            ins = poly_inside(pts)
            for y in range(yy - 3, yy + 13):
                for x in range(cx - 12, cx + 13):
                    if ins(x + 0.5, y + 0.5): cv.put(x, y, col)

# form id -> (aura colour, core colour, glyph)
FORM_ICONS = {
    "ssj": ((255, 210, 50), (255, 220, 70), "1"), "ssj2": ((255, 220, 70), (255, 220, 70), "2"),
    "ssj3": ((255, 200, 40), (255, 210, 60), "3"), "lssj": ((120, 240, 90), (190, 240, 90), "bolt"),
    "ssj4": ((240, 50, 50), (60, 30, 36), "4"), "ssj_god": ((240, 60, 90), (220, 50, 80), "halo"),
    "ssj_blue": ((70, 190, 255), (70, 190, 255), "halo"), "divine_bloom": ((255, 120, 190), (240, 110, 176), "petal"),
    "ui_sign": ((180, 200, 255), (60, 64, 90), "eye"), "ui_mastered": ((220, 230, 255), (200, 210, 235), "eye"),
    "ultra_ego": ((170, 70, 240), (150, 60, 210), "crown"), "potential_unleashed": ((240, 244, 255), (220, 226, 245), "star"),
    "beast": ((200, 160, 255), (210, 214, 230), "claw"), "human_unlock": ((210, 230, 255), (120, 170, 240), "star"),
    "max_power": ((255, 160, 80), (240, 130, 60), "bolt"), "giant": ((110, 230, 110), (80, 180, 80), "arrow"),
    "orange": ((255, 150, 40), (240, 130, 40), "drop"), "final_form": ((210, 140, 255), (240, 240, 250), "horn"),
    "golden": ((255, 210, 50), (255, 200, 40), "horn"), "black": ((120, 70, 160), (40, 30, 50), "horn"),
    "super_majin": ((255, 110, 190), (240, 120, 190), "curl"), "kid_majin": ((255, 90, 170), (250, 140, 200), "curl"),
    "power_boost": ((90, 220, 255), (60, 160, 220), "gear"), "overclock": ((70, 255, 220), (50, 200, 180), "bolt"),
    "divine_aura": ((190, 215, 255), (150, 190, 255), "halo"), "god_destruction": ((170, 60, 255), (110, 40, 180), "crown"),
}
for fid, (aura, core, gk) in FORM_ICONS.items():
    fx = Canvas()
    flames(fx, 64, 100, aura, ((-30, 40, 10), (-16, 58, 12), (0, 70, 14), (16, 58, 12), (30, 40, 10)))
    sphere(fx, 64, 74, 20, ramp(core, 6, hi=(255, 255, 240), lo=tuple(int(v * 0.3) for v in core)), gamma=0.8)
    soft_spot(fx, 57, 66, 7, 5, WHITE, 170)
    gl = Canvas(); glyph(gl, gk, 64, 74); outline(gl, color=(10, 10, 20)); fx.paste(gl)
    finish(fx, aura, f"icon_form_{fid}")

# ------------------------------------------------------------------ RACE ICONS
def race_icon(rid):
    fx = Canvas()
    if rid == "saiyan":                                                    # curled tail
        T = ramp((150, 96, 50), 6, hi=(250, 220, 170), lo=(40, 16, 10))
        for i in range(120):
            t = i / 119; a = t * 1.8 * math.pi + 0.6; r = 32 * (1 - t * 0.7)
            sphere(fx, 64 + r * math.cos(a), 64 + r * math.sin(a), 7.5 * (1 - t * 0.45), T, 0.9)
        return fx, (255, 210, 120)
    if rid == "half_saiyan":                                               # half gold, half white orb with a tail curl
        sphere(fx, 64, 64, 30, ramp((255, 210, 60), 6, hi=WHITE, lo=(120, 60, 0)))
        for y in range(34, 95):
            for x in range(64, 95):
                if fx.get(x, y)[3] and x - 64 > (y - 64) * -0.2:
                    p = fx.get(x, y); fx.put(x, y, mix(p[:3], (235, 240, 255), 0.65))
        T = ramp((150, 96, 50), 5, hi=(250, 220, 170))
        for i in range(50):
            t = i / 49; a = t * 1.5 * math.pi; r = 14 * (1 - t * 0.5)
            sphere(fx, 64 + r * math.cos(a), 100 + r * math.sin(a) * 0.5, 4 * (1 - t * 0.4), T)
        return fx, (255, 220, 120)
    if rid == "human":                                                     # glowing ki orb wearing a red headband
        orb(fx, 64, 62, 30, (120, 180, 255))
        for x in range(30, 99):
            for y in range(56, 64):
                if fx.get(x, y)[3]:
                    nx = (x - 64) / 30; fx.put(x, y, band(ramp((220, 40, 40), 5, hi=(255, 170, 150)), lambert(nx, 0, math.sqrt(max(0, 1 - nx * nx)))))
        for k, (ex, ey) in enumerate(((92, 66), (100, 78))):              # knot tails
            axis_shape(fx, (88, 60), (ex + 6, ey + 10), lambda t: 3.2 - t * 1.2, lambda t, s: band(ramp((220, 40, 40), 4), 0.7 - s * 0.2))
        return fx, (130, 190, 255)
    if rid == "namekian":                                                  # green dome with two antennae
        sphere(fx, 64, 80, 30, ramp((100, 200, 90), 6, hi=(240, 255, 210), lo=(10, 60, 40)), 0.9)
        for k in (-1, 1):
            axis_shape(fx, (64 + 10 * k, 54), (64 + 20 * k, 22), lambda t: 3.2 - t * 1.2, cylinder_color(ramp((100, 200, 90), 5)))
            sphere(fx, 64 + 20 * k, 21, 5, ramp((150, 230, 120), 5, hi=WHITE))
        return fx, (140, 240, 120)
    if rid == "arcosian":                                                  # two curved horns and a violet gem
        H = ramp((240, 236, 230), 6, hi=WHITE, lo=(70, 60, 80))
        for k in (-1, 1):
            for i in range(60):
                t = i / 59
                x = 64 + k * (14 + 22 * t + 6 * math.sin(t * math.pi)); y = 90 - 66 * t ** 0.9
                sphere(fx, x, y, 8 * (1 - t) + 1.5, H, 0.9)
        sphere(fx, 64, 76, 14, ramp((170, 70, 230), 6, hi=(250, 220, 255), lo=(30, 0, 50)), 0.8)
        soft_spot(fx, 59, 71, 5, 4, WHITE, 220)
        return fx, (200, 120, 255)
    if rid == "majin":                                                     # pink dome with a curled tendril
        sphere(fx, 64, 84, 28, ramp((255, 140, 200), 6, hi=WHITE, lo=(120, 30, 80)), 0.9)
        for i in range(80):
            t = i / 79
            if t < 0.55:
                x, y = 64 + 8 * math.sin(t * 4), 58 - 40 * t
            else:
                a = (t - 0.55) / 0.45 * 1.6 * math.pi; x, y = 72 + 12 * math.cos(a + math.pi), 30 + 12 * math.sin(a + math.pi)
            sphere(fx, x, y, 7 * (1 - t * 0.6), ramp((255, 140, 200), 5, hi=WHITE), 0.9)
        for k in (-1, 1):
            for yy in range(80, 86):
                fx.put(64 + 12 * k, yy, (255, 240, 250)); fx.put(64 + 12 * k + 1, yy, (255, 240, 250))   # steam holes
        return fx, (255, 140, 200)
    if rid == "android":                                                   # steel gear with a red core light
        M = ramp((170, 176, 190), 6, hi=WHITE, lo=(20, 24, 40))
        for y in range(20, 108):
            for x in range(20, 108):
                d = math.hypot(x - 64, y - 64); a = math.atan2(y - 64, x - 64)
                R = 36 if int((a + math.pi) / (math.pi / 6)) % 2 else 42
                if 14 <= d <= R:
                    fx.put(x, y, band(M, lambert((x - 64) / 42, (y - 64) / 42, 0.75)))
        orb(fx, 64, 64, 11, (255, 60, 50))
        return fx, (255, 80, 70)
    if rid == "god":                                                       # halo over a radiant orb
        orb(fx, 64, 72, 26, (170, 210, 255))
        for a in range(0, 360, 1):
            for w in range(3):
                x, y = 64 + (30 - w) * math.cos(math.radians(a)), 30 + (9 - w * 0.4) * math.sin(math.radians(a))
                fx.put(int(x), int(y), (255, 236, 150) if w else (255, 255, 230))
        return fx, (200, 225, 255)

for rid in ("saiyan", "half_saiyan", "human", "namekian", "arcosian", "majin", "android", "god"):
    fx, gc = race_icon(rid)
    finish(fx, gc, f"icon_race_{rid}")

# ------------------------------------------------------------------ MENU ICONS (main Scouter menu)
def menu_icon(kind):
    fx = Canvas()
    if kind == "stats":
        for i, h in enumerate((26, 40, 56)):
            x0 = 34 + i * 22
            shade_shape(fx, lambda x, y, x0=x0, h=h: x0 <= x <= x0 + 14 and 96 - h <= y <= 96, lambda x, y: (-0.3, -0.3, 0.9),
                        energy_ramp([(90, 230, 110), (255, 210, 60), (255, 110, 60)][i]))
        beam(fx, (30, 70), (98, 30), 2.4, (255, 255, 255), taper_start=False)
        return fx, (140, 240, 140)
    if kind == "moves":
        orb(fx, 64, 64, 18, (255, 170, 50)); rays(fx, 64, 64, 12, 14, 40, 3, (255, 170, 50))
        return fx, (255, 170, 50)
    if kind == "flight":
        for k, x in enumerate((44, 64, 84)):
            axis_shape(fx, (x, 104), (x, 60 - k % 2 * 12), lambda t: 2 * (1 - t) + 0.3, lambda t, s: mix((120, 200, 255), WHITE, t))
        pts = [(40, 56), (64, 20), (88, 56), (74, 56), (74, 70), (54, 70), (54, 56)]
        ins = poly_inside(pts)
        for y in range(18, 72):
            for x in range(38, 90):
                if ins(x + 0.5, y + 0.5): fx.put(x, y, band(energy_ramp((120, 200, 255)), lambert((x - 64) / 30, (y - 44) / 30, 0.8)))
        return fx, (140, 210, 255)
    if kind == "race_info":
        for y in range(28, 100):
            for x in range(36, 92):
                if 36 <= x <= 92 and 28 <= y <= 100:
                    fx.put(x, y, band(ramp((240, 230, 200), 5, hi=WHITE), 0.8 - (x - 36) / 200))
        for yy in range(42, 92, 10):
            fx.draw().line((44, yy, 84 - (yy % 20), yy), fill=(110, 90, 70, 255))
        sphere(fx, 82, 84, 10, ramp((255, 200, 60), 5, hi=WHITE))
        return fx, (255, 220, 150)
    if kind == "sense":
        for r in (14, 26, 38):
            for a in range(0, 360, 2):
                fx.put(int(64 + r * math.cos(math.radians(a))), int(64 + r * math.sin(math.radians(a))), (100, 255, 140), 230)
        axis_shape(fx, (64, 64), (94, 40), lambda t: 2.5 * (1 - t) + 0.5, lambda t, s: (180, 255, 190))
        orb(fx, 88, 82, 6, (255, 70, 60))
        return fx, (100, 255, 140)
    if kind == "close":
        for a, b in (((40, 40), (88, 88)), ((88, 40), (40, 88))):
            axis_shape(fx, a, b, lambda t: 6, lambda t, s: band(ramp((230, 60, 60), 5, hi=(255, 200, 190)), 0.8 - s * 0.25))
        return fx, (255, 90, 80)
    if kind == "back":
        pts = [(34, 64), (64, 34), (64, 54), (94, 54), (94, 74), (64, 74), (64, 94)]
        ins = poly_inside(pts)
        for y in range(30, 98):
            for x in range(30, 98):
                if ins(x + 0.5, y + 0.5): fx.put(x, y, band(ramp((230, 236, 245), 5, hi=WHITE), lambert((x - 64) / 40, (y - 64) / 40, 0.8)))
        return fx, (200, 220, 255)
    if kind == "power_down":
        orb(fx, 64, 70, 20, (200, 210, 230), core=True)
        pts = [(46, 34), (82, 34), (64, 54)]
        ins = poly_inside(pts)
        for y in range(30, 56):
            for x in range(44, 84):
                if ins(x + 0.5, y + 0.5): fx.put(x, y, WHITE)
        return fx, (200, 210, 230)

for k in ("stats", "moves", "flight", "race_info", "sense", "close", "back", "power_down"):
    fx, gc = menu_icon(k)
    finish(fx, gc, f"icon_menu_{k}")

# ------------------------------------------------------------------ HUD BARS (160x16, nine-slice friendly)
def bar(name, fill_col=None, glowing=False, w=160, h=16):
    cv = Canvas(w, h)
    F = ramp((236, 170, 40), 5, hi=(255, 250, 200), lo=(90, 40, 10))
    for y in range(h):                                                     # gold frame
        for x in range(w):
            edge = min(x, w - 1 - x, y, h - 1 - y)
            if edge < 2:
                cv.put(x, y, F[0] if y < h / 2 and edge == 1 else F[2] if edge == 1 else F[4])
            else:
                cv.put(x, y, mix((14, 16, 30), (34, 38, 60), (h - y) / h))   # recessed dark track
    for x in range(3, w - 3, 8):
        cv.put(x, 2, (40, 46, 72))                                         # track ticks
    if fill_col:
        E = energy_ramp(fill_col)
        for y in range(3, h - 3):
            for x in range(3, w - 3):
                t = (y - 3) / (h - 7)
                c = E[0] if t < 0.15 else E[1] if t < 0.45 else E[2] if t < 0.8 else E[3]
                if (x + y) % 12 < 2 and 0.2 < t < 0.8:
                    c = mix(c, (255, 255, 255), 0.35)                     # energy streaks
                cv.put(x, y, c)
        if glowing:
            for x in range(3, w - 3, 9):
                sparkle(cv, x + (x * 7) % 5, 4 + (x % 3), 1)
            for x in range(3, w - 3):
                cv.put(x, 3, (255, 255, 255)); cv.put(x, h - 4, mix(E[1], (255, 255, 255), 0.3))
    for (x, y) in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        cv.px[x, y] = (0, 0, 0, 0)                                         # rounded corners
    if glowing:
        big = Canvas(w, h + 8); big.paste(cv, 0, 4); glow(big, fill_col, 3, 0.8); cv = big
    path = f"{HUD}/{name}.png"; cv.save(path); MADE.append((path, name))

bar("ki_bar_empty")
bar("ki_bar_full", (80, 180, 255))
bar("ki_bar_glow", (110, 210, 255), glowing=True)
bar("health_bar_empty")
bar("health_bar_full", (240, 60, 60))
bar("stamina_bar_empty")
bar("stamina_bar_full", (140, 230, 80))

# ------------------------------------------------------------------ PANELS & BUTTONS (nine-slice)
def frame(name, w, h, body_top, body_bot, trim, inset=False, glow_col=None, slice_=8):
    cv = Canvas(w, h)
    T = ramp(trim, 5, hi=(255, 250, 210), lo=(70, 30, 6))
    for y in range(h):
        for x in range(w):
            edge = min(x, w - 1 - x, y, h - 1 - y)
            corner = min(x, w - 1 - x) + min(y, h - 1 - y)
            if corner < 2:
                continue                                                   # rounded corner cut
            if edge == 0:
                cv.put(x, y, (8, 6, 4))                                    # dark outline
            elif edge in (1, 2):
                lit = (y < h / 2) != inset
                cv.put(x, y, T[0] if edge == 1 and lit else T[1] if lit else T[3])
            elif edge == 3:
                cv.put(x, y, T[4])
            else:
                t = y / h
                c = mix(body_top, body_bot, t if not inset else 1 - t)
                if (x * 3 + y * 5) % 23 == 0:
                    c = mix(c, (255, 255, 255), 0.06)                      # subtle texture
                cv.put(x, y, c)
    for (cx, cy) in ((4, 4), (w - 5, 4), (4, h - 5), (w - 5, h - 5)):      # gold corner studs
        sphere(cv, cx, cy, 2.2, ramp((255, 200, 60), 3, hi=WHITE))
    if glow_col:
        for x in range(5, w - 5):
            cv.put(x, 4, glow_col, 200)
    path = f"{PANELS}/{name}.png"; cv.save(path); MADE.append((path, name))
    json.dump({"nineslice_size": slice_, "base_size": [w, h]}, open(f"{PANELS}/{name}.json", "w"), indent=2)

frame("panel_dark", 64, 64, (30, 34, 56), (14, 16, 30), (236, 170, 40), slice_=10)
frame("panel_header", 64, 24, (120, 60, 20), (70, 30, 10), (255, 190, 60), slice_=8)
frame("button_default", 64, 32, (44, 50, 80), (24, 28, 48), (226, 150, 40))
frame("button_hover", 64, 32, (70, 76, 116), (36, 40, 66), (255, 200, 70), glow_col=(255, 220, 120))
frame("button_pressed", 64, 32, (24, 28, 48), (40, 44, 72), (200, 120, 30), inset=True)
frame("button_locked", 64, 32, (40, 40, 44), (24, 24, 28), (120, 120, 126))

print(f"ui: {len(MADE)} textures")
json.dump({"icons": sorted(p.split('/')[-1][:-4] for p, _ in MADE if "/icons/" in p)}, open("/tmp/ui_made.json", "w"))
