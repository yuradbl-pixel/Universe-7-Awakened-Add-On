"""pixlib: a tiny pixel-art toolkit for the Universe 7 texture pack.

Everything is drawn pixel by pixel at the final size (no downscaling), so edges stay crisp.
One shared style for the whole pack:
  * light always comes from the top-left (LIGHT)
  * colours are cel-shaded in 4-6 hue-shifted bands (warm highlights, cool shadows)
  * every shape gets a 1 px dark "selective" outline (a darkened version of the colour it touches)
  * glossy things get a soft highlight, a hard specular dot and a rim light
  * energy things get a soft glow halo
"""
import math, random
from PIL import Image, ImageDraw, ImageFilter

LIGHT = (-0.55, -0.62, 0.56)          # top-left, towards the viewer
_l = math.sqrt(sum(v * v for v in LIGHT)); LIGHT = tuple(v / _l for v in LIGHT)


# ---------------------------------------------------------------- colour
def clamp(v): return max(0, min(255, int(round(v))))

def mix(a, b, t):
    return tuple(clamp(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))

def ramp(base, n=6, hi=(255, 250, 225), lo=(30, 18, 60)):
    """n shades, brightest first. Highlights drift warm, shadows drift cool (anime-style hue shift)."""
    out = []
    for i in range(n):
        t = i / (n - 1)                      # 0 = highlight, 1 = deepest shadow
        if t < 0.35:
            out.append(mix(base, hi, (0.35 - t) / 0.35 * 0.62))
        else:
            out.append(mix(base, lo, (t - 0.35) / 0.65 * 0.68))
    return out

def dark(c, k=0.38): return tuple(clamp(v * k) for v in c[:3])


# ---------------------------------------------------------------- canvas
class Canvas:
    def __init__(self, w=128, h=None):
        self.w, self.h = w, h or w
        self.im = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        self.px = self.im.load()

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def put(self, x, y, c, a=255):
        """Blend a colour over the pixel (alpha a)."""
        if not (0 <= x < self.w and 0 <= y < self.h):
            return
        c = tuple(c[:3]); a = c[3] if len(c) == 4 else a
        if a >= 255:
            self.px[x, y] = c + (255,)
            return
        r, g, b, al = self.px[x, y]
        t = a / 255
        na = al + (255 - al) * t
        if na <= 0:
            return
        nc = tuple(clamp((c[i] * t * 255 + (r, g, b)[i] * al * (1 - t)) / na) for i in range(3))
        self.px[x, y] = nc + (clamp(na),)

    def draw(self): return ImageDraw.Draw(self.im)

    def paste(self, other, x=0, y=0):
        self.im.alpha_composite(other.im if isinstance(other, Canvas) else other, (x, y))
        self.px = self.im.load()

    def save(self, path): self.im.save(path)


# ---------------------------------------------------------------- shading
def band(ramp_, light, gamma=1.0):
    """Map a light value 0..1 to one of the ramp's bands (cel shading)."""
    n = len(ramp_)
    light = max(0.0, min(1.0, light)) ** gamma
    i = int((1 - light) * n)
    return ramp_[min(n - 1, max(0, i))]

def lambert(nx, ny, nz):
    d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
    return max(0.0, d) * 0.85 + 0.15

def shade_shape(cv, inside, normal, ramp_, gamma=1.0, alpha=255):
    """inside(x, y) -> bool, normal(x, y) -> (nx, ny, nz). Cel-shades every pixel of the shape."""
    for y in range(cv.h):
        for x in range(cv.w):
            if inside(x + 0.5, y + 0.5):
                n = normal(x + 0.5, y + 0.5)
                cv.put(x, y, band(ramp_, lambert(*n), gamma), alpha)

def sphere(cv, cx, cy, r, ramp_, gamma=1.0, alpha=255):
    def inside(x, y): return (x - cx) ** 2 + (y - cy) ** 2 <= r * r
    def normal(x, y):
        nx, ny = (x - cx) / r, (y - cy) / r
        return nx, ny, math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
    shade_shape(cv, inside, normal, ramp_, gamma, alpha)

def ellipsoid(cv, cx, cy, rx, ry, ramp_, rot=0.0, gamma=1.0, cut=None):
    """Rotated ellipse shaded like a 3D ellipsoid. cut(x, y) -> True removes pixels (notches)."""
    cs, sn = math.cos(rot), math.sin(rot)
    def local(x, y):
        dx, dy = x - cx, y - cy
        return (dx * cs + dy * sn) / rx, (-dx * sn + dy * cs) / ry
    def inside(x, y):
        u, v = local(x, y)
        return u * u + v * v <= 1 and not (cut and cut(x, y))
    def normal(x, y):
        u, v = local(x, y)
        nz = math.sqrt(max(0.0, 1 - u * u - v * v))
        return u * cs - v * sn, u * sn + v * cs, nz
    shade_shape(cv, inside, normal, ramp_, gamma)

def axis_shape(cv, p0, p1, profile, color_fn):
    """Draw a shape laid along the axis p0->p1.
    profile(t) -> half-width in px at t (0..1 along the axis) or None (nothing there).
    color_fn(t, s) -> RGBA/RGB or None, s = -1..1 across the width (-1 = lit side)."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0); ux, uy = (x1 - x0) / L, (y1 - y0) / L
    vx, vy = -uy, ux
    if vx * LIGHT[0] + vy * LIGHT[1] < 0:      # make s = -1 the side facing the light
        vx, vy = -vx, -vy
    for y in range(cv.h):
        for x in range(cv.w):
            px_, py_ = x + 0.5 - x0, y + 0.5 - y0
            t = (px_ * ux + py_ * uy) / L
            if t < 0 or t > 1:
                continue
            hw = profile(t)
            if not hw:
                continue
            d = px_ * vx + py_ * vy
            if abs(d) <= hw:
                c = color_fn(t, -d / hw if hw else 0)
                if c is not None:
                    cv.put(x, y, c)

def cylinder_color(ramp_):
    """color_fn for axis_shape: a round rod (lit stripe on the light side, dark on the far side)."""
    def fn(t, s):
        nz = math.sqrt(max(0.0, 1 - s * s))
        return band(ramp_, max(0, -s * 0.75 + nz * 0.55) * 0.9 + 0.1)
    return fn


# ---------------------------------------------------------------- finishing
def outline(cv, k=0.36, color=None, diagonal=False):
    """1 px selective outline: each empty pixel next to the shape takes a darkened neighbour colour."""
    src = cv.im.copy(); sp = src.load()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, -1), (1, -1), (-1, 1)] if diagonal else [])
    for y in range(cv.h):
        for x in range(cv.w):
            if sp[x, y][3] > 40:
                continue
            for dx, dy in nb:
                xx, yy = x + dx, y + dy
                if 0 <= xx < cv.w and 0 <= yy < cv.h and sp[xx, yy][3] > 140:
                    cv.px[x, y] = (color or dark(sp[xx, yy], k)) + (255,)
                    break

def inner_line(cv, inside, color):
    """Dark line just inside a region boundary (used for separations: caps, seams)."""
    for y in range(cv.h):
        for x in range(cv.w):
            if inside(x, y) and not all(inside(x + dx, y + dy) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                cv.put(x, y, color)

def glow(cv, color, radius=6, strength=1.0, behind=True):
    """Soft halo around the opaque shape (put behind it)."""
    a = cv.im.split()[3].filter(ImageFilter.GaussianBlur(radius))
    a = a.point(lambda v: clamp(v * 1.6 * strength))
    halo = Image.new("RGBA", cv.im.size, tuple(color[:3]) + (0,)); halo.putalpha(a)
    if behind:
        halo.alpha_composite(cv.im); cv.im = halo
    else:
        cv.im.alpha_composite(halo)
    cv.px = cv.im.load()

def soft_spot(cv, cx, cy, rx, ry, color, alpha=200, mask=None):
    """Soft-edged highlight (glossy shine), only on existing pixels."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1 and cv.get(x, y)[3] > 0 and (mask is None or mask(x, y)):
                cv.put(x, y, color, int(alpha * (1 - d) ** 0.6))

def sparkle(cv, x, y, size=3, color=(255, 255, 255)):
    """Hard specular glint: a bright pixel with a small 4-point cross."""
    cv.put(x, y, color)
    for i in range(1, size + 1):
        a = int(255 * (1 - i / (size + 1)))
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            cv.put(x + dx, y + dy, color, a)

def arc_light(cv, cx, cy, r, a0, a1, color, alpha=200, width=1.5):
    """Thin rim light along part of a circle (angles in degrees, 0 = right, 90 = down)."""
    for y in range(cv.h):
        for x in range(cv.w):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if r - width <= d <= r and cv.get(x, y)[3] > 0:
                ang = math.degrees(math.atan2(dy, dx)) % 360
                if (a0 <= ang <= a1) if a0 <= a1 else (ang >= a0 or ang <= a1):
                    cv.put(x, y, color, alpha)


# ---------------------------------------------------------------- shapes & glyphs
def star_poly(cx, cy, ro, ri, points=5, rot=-90):
    pts = []
    for i in range(points * 2):
        r = ro if i % 2 == 0 else ri
        a = math.radians(rot + i * 180 / points)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts

def poly_inside(pts):
    def inside(x, y):
        c = False; n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]; x2, y2 = pts[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
                c = not c
        return c
    return inside

DIGITS = {  # 3x5 pixel font
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "2": ["111", "001", "111", "100", "111"], "3": ["111", "001", "011", "001", "111"],
    "4": ["101", "101", "111", "001", "001"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "7": ["111", "001", "010", "010", "010"],
    "8": ["111", "101", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}

def digits(cv, text, x, y, scale, color, shadow=None):
    for i, ch in enumerate(text):
        g = DIGITS[ch]
        for r, row in enumerate(g):
            for c, bit in enumerate(row):
                if bit == "1":
                    for yy in range(scale):
                        for xx in range(scale):
                            px, py = x + (i * 4 + c) * scale + xx, y + r * scale + yy
                            if shadow:
                                cv.put(px + 1, py + 1, shadow)
                            cv.put(px, py, color)


def preview(paths_names, out, cols=6, zoom=2, bg=(36, 38, 46), checker=True):
    """Contact sheet: each texture at 2x on a dark checker, with its name."""
    from PIL import ImageFont
    cell = 128 * zoom + 16
    rows = (len(paths_names) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + 14)), bg)
    d = ImageDraw.Draw(sheet)
    for i, (p, name) in enumerate(paths_names):
        im = Image.open(p).convert("RGBA").resize((128 * zoom, 128 * zoom), Image.NEAREST)
        x, y = (i % cols) * cell + 8, (i // cols) * (cell + 14) + 8
        if checker:
            for yy in range(0, 128 * zoom, 16):
                for xx in range(0, 128 * zoom, 16):
                    if (xx // 16 + yy // 16) % 2:
                        d.rectangle((x + xx, y + yy, x + xx + 15, y + yy + 15), fill=(44, 46, 56))
        sheet.paste(im, (x, y), im)
        d.text((x, y + 128 * zoom + 2), name, fill=(230, 230, 230))
    sheet.save(out)
