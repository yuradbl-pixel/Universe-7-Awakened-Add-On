"""blockkit: shared seamless-texture helpers (noise, slabs, rocks, tufts, pebbles) for all block textures."""
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

