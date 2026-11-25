"""Universe 7: Anime Textures - vanilla batch 7 (v2, high detail): swords, pickaxes, axes, shovels
in wood, stone, iron, gold, diamond and netherite. 128x128, light from the top-left."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixlib import *

OUT = "/home/claude/u7_textures/textures/items"
os.makedirs(OUT, exist_ok=True)
DONE = []
W = (255, 255, 255)

MATS = {  # base, outline, surface style, gem colour for pommels / sockets
    "wood": ((200, 150, 90), (58, 32, 16), "grain", (120, 200, 90)),
    "stone": ((150, 150, 160), (34, 34, 44), "speckle", (200, 120, 60)),
    "iron": ((210, 218, 230), (46, 52, 74), "brushed", (90, 160, 255)),
    "gold": ((255, 204, 50), (110, 56, 8), "polish", (230, 40, 60)),
    "diamond": ((96, 232, 232), (6, 70, 92), "facet", (255, 255, 255)),
    "netherite": ((78, 66, 80), (14, 8, 14), "nether", (180, 70, 255)),
}
WOOD = ramp((160, 106, 60), 6, hi=(246, 208, 156), lo=(46, 22, 12))
LEATHER = ramp((120, 64, 40), 5, hi=(220, 160, 120), lo=(36, 16, 10))
STEEL = ramp((176, 182, 196), 5, hi=(255, 255, 255), lo=(40, 44, 60))

def mramp(base):
    return ramp(base, 6, hi=mix(base, (255, 255, 250), 0.75), lo=mix(base, (8, 8, 26), 0.75))

def surface(style, R, x, y, t, s, c):
    """Per-material surface detail on top of the shading."""
    if style == "speckle":
        h = (x * 73 + y * 151) % 97
        if h < 5: return R[4]
        if h > 93: return R[0]
    elif style == "grain":
        if abs(math.sin(t * 60 + s * 2.5)) < 0.12: return mix(c, R[4], 0.5)
    elif style == "brushed":
        if (x + y * 3) % 11 == 0: return mix(c, R[0], 0.35)
    elif style == "polish":
        if (x - y) % 29 in (0, 1): return mix(c, R[0], 0.5)
    elif style == "facet":
        if (int(t * 14) + (1 if s > 0 else 0)) % 2 == 0: return mix(c, R[0], 0.25)
    elif style == "nether":
        if abs(math.sin(t * 40 + s * 4 + x * 0.1)) < 0.08: return mix(c, (140, 110, 150), 0.6)
    return c

def handle(cv, p0, p1, w=4.0, wrap=(0.0, 0.35)):
    """Round wooden haft with grain, a leather spiral grip and a metal end cap."""
    def col(t, s):
        c = cylinder_color(WOOD)(t, s)
        if abs(math.sin(t * 90 + s * 1.5)) < 0.1: c = mix(c, WOOD[4], 0.45)       # grain
        if wrap[0] <= t <= wrap[1]:
            band_ = (t * 70 + s * 1.2) % 2
            c = band(LEATHER, (0.85 - abs(s) * 0.5) if band_ < 1.4 else 0.25)     # spiral leather wrap
            if 1.35 < band_ < 1.55: c = LEATHER[0]
        if t < 0.05: c = cylinder_color(STEEL)(t, s)                               # end cap
        return c
    axis_shape(cv, p0, p1, lambda t: w, col)

def blade_color(R, style, glint_t=0.58):
    """Diamond-section blade: lit bevel / lit face / fuller groove / shaded face / dark bevel + anime glint band."""
    def fn(t, s, x=0, y=0):
        if s < -0.8: c = R[0]
        elif s < -0.12: c = R[1] if t > 0.15 else R[2]
        elif s < -0.04: c = R[3]
        elif s < 0.04: c = R[2]                                                  # fuller (groove) with lit floor
        elif s < 0.12: c = R[4]
        elif s < 0.8: c = R[3]
        else: c = R[2]
        if abs(t - glint_t) < 0.03 and s < 0.6: c = W if s < 0 else R[0]          # sharp reflection band
        if abs(t - glint_t - 0.06) < 0.008 and s < 0.2: c = R[0]
        return c
    return fn

def axis_fill(cv, p0, p1, profile, color_fn, style, R):
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    vx, vy = -uy, ux
    if vx * LIGHT[0] + vy * LIGHT[1] < 0: vx, vy = -vx, -vy
    for y in range(cv.h):
        for x in range(cv.w):
            px_, py_ = x + 0.5 - x0, y + 0.5 - y0
            t = (px_ * ux + py_ * uy) / L
            if not 0 <= t <= 1: continue
            hw = profile(t)
            if not hw: continue
            d = px_ * vx + py_ * vy
            if abs(d) <= hw:
                s = -d / hw
                c = color_fn(t, s)
                cv.put(x, y, surface(style, R, x, y, t, s, c))

def gem(cv, x, y, r, col):
    sphere(cv, x, y, r, ramp(col, 4, hi=W, lo=mix(col, (0, 0, 20), 0.7)), gamma=0.7)
    cv.put(int(x - r * 0.4), int(y - r * 0.4), W)

def socket(cv, cx, cy, ang, w, h, R, gemcol=None):
    """Metal collar / eye block with bevel and rivets, rotated to the handle."""
    ca, sa = math.cos(ang), math.sin(ang)
    for y in range(int(cy - 14), int(cy + 15)):
        for x in range(int(cx - 14), int(cx + 15)):
            u = (x + 0.5 - cx) * ca + (y + 0.5 - cy) * sa
            v = -(x + 0.5 - cx) * sa + (y + 0.5 - cy) * ca
            if abs(u) <= w and abs(v) <= h:
                e = min(w - abs(u), h - abs(v))
                lit = (u * -ca - v * -sa) if False else -(u * 0.6 + v * 0.8)
                c = R[0] if e < 1.2 and lit > 0 else R[4] if e < 1.2 else R[1] if lit > 0 else R[2]
                cv.put(x, y, c)
    for k in (-1, 1):
        rx, ry = cx + ca * w * 0.55 * k, cy + sa * w * 0.55 * k
        sphere(cv, rx, ry, 1.8, STEEL); cv.put(int(rx) - 1, int(ry) - 1, W)
    if gemcol: gem(cv, cx, cy, 2.6, gemcol)

# ============================================================ SWORD
def sword(mat):
    base, out, style, gemcol = MATS[mat]; R = mramp(base); cv = Canvas()
    hilt_R = mramp(base) if mat != "wood" else WOOD
    tip, root = (116, 12), (46, 82)
    handle(cv, (14, 114), (40, 88), 3.6, wrap=(0.12, 0.95))
    sphere(cv, 13, 115, 6.5, hilt_R if mat != "wood" else STEEL); gem(cv, 13, 115, 2.6, gemcol)   # pommel
    def prof(t):
        if t > 0.86: return 8.5 * (1 - (t - 0.86) / 0.14) + 0.4                 # tip
        return 8.5 - t * 1.2                                                     # slight taper
    axis_fill(cv, root, tip, prof, blade_color(R, style), style, R)
    # ricasso and cross-guard with flared ends and a centre gem
    axis_fill(cv, (31, 69), (59, 97), lambda t: 4.2 + 2.2 * abs(t - 0.5) * 2, lambda t, s: band(hilt_R, 0.8 - s * 0.35 - abs(t - 0.5) * 0.3), style, hilt_R)
    for (ex, ey) in ((31, 69), (59, 97)):
        sphere(cv, ex, ey, 3.4, hilt_R)
    gem(cv, 45, 83, 3.4, gemcol)
    sparkle(cv, 100, 26, 3)
    if mat == "diamond":
        sparkle(cv, 72, 54, 2); sparkle(cv, 88, 40, 2)
    outline(cv, color=out); return cv

# ============================================================ PICKAXE
def pickaxe(mat):
    base, out, style, gemcol = MATS[mat]; R = mramp(base); cv = Canvas()
    hx, hy = 86, 42                                                              # where the head sits on the haft
    handle(cv, (18, 112), (hx + 8, hy - 8), 4.0, wrap=(0.05, 0.32))
    dirx, diry = 0.707, -0.707                                                   # haft direction
    px_, py_ = 0.707, 0.707                                                      # head runs perpendicular
    def arm(sign):
        pts = []
        for i in range(4):                                                       # gently curving arm (polyline)
            t = i / 3
            along = 10 + t * 44
            sag = (t ** 1.8) * 16                                                # tips curve down toward the hand
            pts.append((hx + px_ * along * sign - dirx * sag, hy + py_ * along * sign - diry * sag))
        for i in range(3):
            a, b = pts[i], pts[i + 1]
            w0, w1 = 8.0 - i * 2.4, 8.0 - (i + 1) * 2.4
            axis_fill(cv, a, b, lambda t, w0=w0, w1=w1: max(0.6, w0 + (w1 - w0) * t),
                      lambda t, s: (R[0] if s < -0.75 else R[1] if s < -0.1 else R[2] if s < 0.25 else R[3] if s < 0.8 else R[4]),
                      style, R)
        return pts
    a1 = arm(1); a2 = arm(-1)
    for pts in (a1, a2):                                                         # bright ridge line along the top
        for i in range(3):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            for k in range(12):
                t = k / 12
                cv.put(int(ax + (bx - ax) * t - 2), int(ay + (by - ay) * t - 3), R[0])
    socket(cv, hx, hy, math.atan2(py_, px_), 11, 7, STEEL if mat in ("wood", "stone") else R, gemcol)
    sparkle(cv, int(a2[2][0]) + 2, int(a2[2][1]) - 2, 2)
    outline(cv, color=out); return cv

# ============================================================ AXE
def axe(mat):
    base, out, style, gemcol = MATS[mat]; R = mramp(base); cv = Canvas()
    handle(cv, (20, 114), (86, 22), 4.0, wrap=(0.05, 0.3))
    # blade: wide crescent edge, bearded lower horn, cheek bevel
    edge_c = (100, 44); rr = 30
    def inside(x, y):
        dx, dy = x - 82, y - 36
        u = dx * 0.81 + dy * 0.58                                                 # outward from the haft
        v = -dx * 0.58 + dy * 0.81                                                # along the haft
        if u < -4: return False
        reach = 30 + 6 * math.cos(v / 22 * math.pi / 2) if abs(v) < 22 else 0
        width = 10 + max(0, u) * 0.75                                             # flares out to the edge
        return u <= reach and abs(v) <= width
    def uv(x, y):
        dx, dy = x - 82, y - 36
        return dx * 0.81 + dy * 0.58, -dx * 0.58 + dy * 0.81
    for y in range(0, 100):
        for x in range(50, 128):
            if inside(x + 0.5, y + 0.5):
                u, v = uv(x + 0.5, y + 0.5)
                reach = 30 + 6 * math.cos(v / 22 * math.pi / 2)
                k = (reach - u)                                                   # distance from the cutting edge
                if k < 2: c = W if v < 6 else R[0]                                 # honed edge
                elif k < 6: c = R[1] if v < 4 else R[2]                            # edge bevel
                elif u < 8: c = R[3] if v > 0 else R[2]                            # thick cheek near the eye
                else: c = R[2] if v < 0 else R[3]
                if abs(k - 6) < 0.6: c = R[4]                                      # bevel line
                c = surface(style, R, x, y, u / 40, v / 20, c)
                cv.put(x, y, c)
    socket(cv, 82, 36, math.atan2(-0.8, 0.6), 7, 9, STEEL if mat in ("wood", "stone") else R, gemcol)
    sparkle(cv, 100, 46, 3)
    outline(cv, color=out); return cv

# ============================================================ SHOVEL
def shovel(mat):
    base, out, style, gemcol = MATS[mat]; R = mramp(base); cv = Canvas()
    handle(cv, (16, 114), (74, 56), 4.0, wrap=(0.05, 0.3))
    cx, cy = 94, 34
    ca, sa = 0.707, -0.707                                                       # blade points up-right
    def local(x, y):
        dx, dy = x - cx, y - cy
        return dx * ca + dy * sa, -dx * sa + dy * ca                              # u along the blade, v across
    for y in range(0, 80):
        for x in range(50, 128):
            u, v = local(x + 0.5, y + 0.5)
            half = 17 * math.sqrt(max(0, 1 - ((u - 2) / 28) ** 2)) if u > -14 else 0
            if u < -14 or abs(v) > half or u > 30: continue
            rim = half - abs(v)
            dish = (v / max(1, half))                                             # concave dish: lit far side
            c = R[1] if dish > 0.35 else R[2] if dish > -0.35 else R[3]
            if rim < 2.2: c = R[0] if v < 0 else R[4]                              # rolled rim
            if abs(v) < 1.6 and u < 10: c = R[0] if v < 0 else R[3]                # centre spine ridge
            if u > 26: c = R[0]                                                    # bright tip edge
            cv.put(x, y, surface(style, R, x, y, u / 30, v / 17, c))
    socket(cv, 78, 52, math.atan2(-0.707, 0.707), 7, 5, STEEL if mat in ("wood", "stone") else R, gemcol)
    soft_spot(cv, 92, 26, 6, 4, W, 170); sparkle(cv, 90, 24, 2)
    outline(cv, color=out); return cv

for mat in MATS:
    for kind, fn in (("sword", sword), ("pickaxe", pickaxe), ("axe", axe), ("shovel", shovel)):
        cv = fn(mat); name = f"{mat}_{kind}.png"; cv.save(f"{OUT}/{name}"); DONE.append(name)
print("vanilla batch 7 v2:", len(DONE), "textures")
