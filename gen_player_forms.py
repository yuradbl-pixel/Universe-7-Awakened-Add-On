# Player transformation looks for the non-Saiyan races (v1.36).
# Each form gets a full-body overlay worn in the helmet slot while transformed
# (same system as the Saiyan hair). The overlay is player-shaped, slightly
# inflated over the player's own model, with a 128x128 texture.
# "full" designs cover the player completely; "overlay" designs are mostly
# see-through, so the player's own skin shows with markings/plating on top.
# All designs are original race-themed looks.
import json, os, random
from PIL import Image, ImageDraw

BP = "/home/claude/dbz/DBZ_BP"
RP = "/home/claude/dbz/DBZ_RP"
S = 2  # 64-px UV layout drawn at 2x = 128x128

def w(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(json.dumps(o, indent=2) + "\n")

# ---- Geometry ------------------------------------------------------------------
# Player bone names/pivots so the overlay moves with the player's animations.
PARTS = {  # name: (uv, size, origin, pivot, inflate)
    "head":     ((0, 0),   (8, 8, 8),  (-4, 24, -4), (0, 24, 0),    0.65),
    "body":     ((16, 16), (8, 12, 4), (-4, 12, -2), (0, 24, 0),    0.32),
    "rightArm": ((40, 16), (4, 12, 4), (-8, 12, -2), (-5, 22, 0),   0.3),
    "leftArm":  ((32, 48), (4, 12, 4), (4, 12, -2),  (5, 22, 0),    0.3),
    "rightLeg": ((0, 16),  (4, 12, 4), (-3.9, 0, -2), (-1.9, 12, 0), 0.3),
    "leftLeg":  ((16, 48), (4, 12, 4), (-0.1, 0, -2), (1.9, 12, 0),  0.3),
}
# Rotation convention (same as hairlib, checked in game): +rz tips a part's top toward +x,
# negative rx tips it toward the back (+z).
# Extras on the head (transparent unless a design paints them). v1.38: chained
# segments so antennae, the Majin tendril and horns can curve.
EXTRAS = [  # (name, parent, uv, size, origin, pivot, rotation)
    # Namekian antennae: from the forehead, curving back.
    ("antenna_r", "head", (44, 32), (1, 5, 1), (-2.5, 31.8, -4.2), (-2, 31.8, -3.7), [-20, 0, -12]),
    ("antenna_r2", "antenna_r", (44, 40), (1, 5, 1), (-2.5, 36.8, -4.2), (-2, 36.8, -3.7), [-45, 0, 0]),
    ("antenna_l", "head", (48, 32), (1, 5, 1), (1.5, 31.8, -4.2), (2, 31.8, -3.7), [-20, 0, 12]),
    ("antenna_l2", "antenna_l", (48, 40), (1, 5, 1), (1.5, 36.8, -4.2), (2, 36.8, -3.7), [-45, 0, 0]),
    ("ear_r", "head", (52, 32), (1, 3, 2), (-5.2, 27, -1), (-4.7, 27, 0), [0, 0, 0]),
    ("ear_l", "head", (52, 32), (1, 3, 2), (4.2, 27, -1), (4.7, 27, 0), [0, 0, 0]),
    # Majin head tendril: rises from the top of the head and curls back.
    ("tendril", "head", (32, 0), (2, 3, 2), (-1, 32, -1), (0, 32, 0), [-15, 0, 0]),
    ("tendril2", "tendril", (40, 0), (2, 3, 2), (-1, 35, -1), (0, 35, 0), [-40, 0, 0]),
    ("tendril3", "tendril2", (48, 0), (2, 3, 2), (-1, 38, -1), (0, 38, 0), [-55, 0, 0]),
    # Frieza Race horns: from the upper sides of the head, sweeping up and back.
    ("horn_r", "head", (32, 8), (2, 3, 2), (-5.5, 29, -1), (-4.5, 29, 0), [-20, 0, -40]),
    ("horn_r2", "horn_r", (40, 8), (2, 4, 2), (-5.5, 32, -1), (-4.5, 32, 0), [-25, 0, 30]),
    ("horn_r3", "horn_r2", (48, 8), (1, 3, 1), (-5, 36, -0.5), (-4.5, 36, 0), [-25, 0, 20]),
    ("horn_l", "head", (56, 8), (2, 3, 2), (3.5, 29, -1), (4.5, 29, 0), [-20, 0, 40]),
    ("horn_l2", "horn_l", (0, 48), (2, 4, 2), (3.5, 32, -1), (4.5, 32, 0), [-25, 0, -30]),
    ("horn_l3", "horn_l2", (8, 48), (1, 3, 1), (4, 36, -0.5), (4.5, 36, 0), [-25, 0, -20]),
    # Halo
    ("halo_a", "head", (0, 32), (10, 1, 1), (-5, 35, -5), (0, 35, 0), [0, 0, 0]),
    ("halo_b", "head", (0, 32), (10, 1, 1), (-5, 35, 4), (0, 35, 0), [0, 0, 0]),
    ("halo_c", "head", (0, 36), (1, 1, 8), (-5, 35, -4), (0, 35, 0), [0, 0, 0]),
    ("halo_d", "head", (0, 36), (1, 1, 8), (4, 35, -4), (0, 35, 0), [0, 0, 0]),
]

def tendril_extras(sizes, rots=(-15, -40, -55, -60)):
    """Majin head tendril as a chain of segments (w, h, d, uv)."""
    out, y, parent = [], 32, "head"
    for i, (w_, h, d, uv) in enumerate(sizes):
        name = "tendril" if i == 0 else f"tendril{i+1}"
        out.append((name, parent, uv, (w_, h, d), (-w_ / 2, y, -d / 2), (0, y, 0), [rots[i], 0, 0]))
        parent, y = name, y + h
    return out

# Medium (Super Majin) and large (Kid Majin) tendrils. They reuse the horn UV area,
# so those geometries leave the horns out.
TENDRIL_SIZES = {  # "m" is the base-race size (also the player_tail tendril)
    "m": [(3, 4, 3, (32, 0)), (3, 4, 3, (44, 0)), (2, 3, 2, (56, 0))],
    "l": [(4, 5, 4, (32, 0)), (4, 5, 4, (48, 0)), (3, 4, 3, (32, 9)), (2, 3, 2, (44, 9))],
}

def geometry(ident="geometry.dbz.form_overlay", extras=None):
    extras = EXTRAS if extras is None else extras
    bones = []
    for name, (uv, size, origin, pivot, infl) in PARTS.items():
        b = {"name": name, "pivot": list(pivot), "cubes": [{"origin": list(origin), "size": list(size), "uv": list(uv), "inflate": infl}]}
        if name == "head":
            b["parent"] = "body"
        bones.append(b)
    for name, parent, uv, size, origin, pivot, rot in extras:
        bones.append({"name": name, "parent": parent, "pivot": list(pivot), "rotation": rot,
                      "cubes": [{"origin": list(origin), "size": list(size), "uv": list(uv), "inflate": 0.1}]})
    return {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": ident, "texture_width": 64, "texture_height": 64,
                        "visible_bounds_width": 3, "visible_bounds_height": 3.5, "visible_bounds_offset": [0, 1.5, 0]},
        "bones": bones}]}

# ---- Texture painter -----------------------------------------------------------
class Skin:
    def __init__(self):
        self.im = Image.new("RGBA", (64 * S, 64 * S), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    @staticmethod
    def face(uv, size, side):
        (u, v), (w_, h, d) = uv, size
        r = {"top": (u + d, v, w_, d), "bottom": (u + d + w_, v, w_, d),
             "right": (u, v + d, d, h), "front": (u + d, v + d, w_, h),
             "left": (u + d + w_, v + d, d, h), "back": (u + d + w_ + d, v + d, w_, h)}[side]
        return tuple(x * S for x in r)  # x, y, w, h in texture px

    def fill(self, part, sides, col, rows=None, shade=0.0, seed=0):
        """Fill faces of a part. rows=(from, to) in 64-px units from the top of side faces."""
        uv, size = (PARTS[part][0], PARTS[part][1]) if part in PARTS else part
        rnd = random.Random(seed)
        for side in sides:
            x, y, fw, fh = self.face(uv, size, side)
            y0, y1 = (y, y + fh) if rows is None or side in ("top", "bottom") else (y + rows[0] * S, y + rows[1] * S)
            for py in range(y0, y1):
                for px in range(x, x + fw):
                    c = col
                    if shade:
                        k = 1 + (rnd.random() - 0.5) * shade
                        c = tuple(max(0, min(255, int(v * k))) for v in col[:3]) + ((col[3],) if len(col) == 4 else ())
                    self.d.point((px, py), fill=c if len(c) == 4 else c + (255,))

    def rect(self, part, side, x0, y0, x1, y1, col):
        """Rectangle inside a face, in texture px relative to the face's top-left (128 scale)."""
        uv, size = (PARTS[part][0], PARTS[part][1]) if part in PARTS else part
        x, y, _, _ = self.face(uv, size, side)
        col = col if len(col) == 4 else col + (255,)
        if col[3] == 255:
            self.d.rectangle((x + x0, y + y0, x + x1, y + y1), fill=col)
            return
        # Translucent fills are blended over what is already painted (never punch see-through holes).
        w, h = x1 - x0 + 1, y1 - y0 + 1
        if w <= 0 or h <= 0:
            return
        box = (x + x0, y + y0)
        under = self.im.crop((box[0], box[1], box[0] + w, box[1] + h))
        under.alpha_composite(Image.new("RGBA", (w, h), col))
        self.im.paste(under, box)

    def line(self, part, side, pts, col, width=1):
        uv, size = (PARTS[part][0], PARTS[part][1]) if part in PARTS else part
        x, y, fw, fh = self.face(uv, size, side)
        col = col if len(col) == 4 else col + (255,)
        xy = [(x + a, y + b) for a, b in pts]
        if col[3] == 255:
            self.d.line(xy, fill=col, width=width)
            return
        # Translucent strokes (glows) are blended on top, clipped to this face,
        # so they never punch holes in solid skin.
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).line(xy, fill=col, width=width)
        mask = Image.new("L", self.im.size, 0)
        ImageDraw.Draw(mask).rectangle((x, y, x + fw - 1, y + fh - 1), fill=255)
        clipped = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        clipped.paste(layer, (0, 0), mask)
        self.im.alpha_composite(clipped)
        self.d = ImageDraw.Draw(self.im)

    def eyes(self, white, iris, brow=None, glow=False):
        # Head front is 16x16 px at this scale: eyes on rows 8-9 with a lash line on row 7.
        for x0 in (3, 10):
            self.rect("head", "front", x0, 8, x0 + 2, 9, white)
            ix = x0 + (1 if x0 == 3 else 0)
            self.rect("head", "front", ix, 8, ix + 1, 9, iris)
            self.rect("head", "front", ix, 9, ix + 1, 9, dk(iris, 0.6))
            self.rect("head", "front", ix, 8, ix, 8, (255, 255, 255))   # highlight
            self.rect("head", "front", x0, 7, x0 + 2, 7, (30, 24, 28))   # lash line
            if brow:
                self.rect("head", "front", x0 - 1, 5, x0 + 3, 6, brow)
        if glow:
            for x0 in (2, 9):
                self.rect("head", "front", x0, 10, x0 + 4, 10, glow)

    def mouth(self, col, wide=False):
        self.rect("head", "front", 6 if not wide else 5, 12, 9 if not wide else 10, 12, col)

    def save(self, path):
        self.im.save(path)

SIDES = ("front", "back", "left", "right")
ALL = SIDES + ("top", "bottom")
LIMBS = ("rightArm", "leftArm", "rightLeg", "leftLeg")
ARMS = ("rightArm", "leftArm")
LEGS = ("rightLeg", "leftLeg")
def dk(c, k=0.7): return tuple(int(v * k) for v in c[:3])
def lt(c, k=1.18): return tuple(min(255, int(v * k) + 10) for v in c[:3])

def full_body(sk, skin, seed):
    for p in PARTS:
        sk.fill(p, ALL, skin, shade=0.12, seed=seed + hash(p) % 97)

def ki_lines(sk, col, parts, seed, n=5, glow=True):
    rnd = random.Random(seed)
    for p in parts:
        for side in ("front", "left", "right", "back"):
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(n):
                x = rnd.randrange(1, fw - 1); y = rnd.randrange(2, fh - 6)
                pts = [(x, y)]
                for _ in range(3):
                    x = max(0, min(fw - 1, x + rnd.choice((-1, 0, 1)))); y += rnd.randint(2, 4)
                    pts.append((x, min(fh - 1, y)))
                if glow:
                    sk.line(p, side, pts, col[:3] + (60,), width=3)   # soft glow
                sk.line(p, side, pts, col)

def gi(sk, top, pants, sash, boots, wraps=None, sleeveless=True, torn=False, seed=0):
    sk.fill("body", SIDES, top, shade=0.1, seed=seed)
    sk.fill("body", ("top", "bottom"), top)
    # V-neck opening
    for i in range(3):
        sk.rect("body", "front", 5 + i, i, 10 - i, i, (0, 0, 0, 0))
    sk.fill("body", SIDES, sash, rows=(8, 10))
    for leg in LEGS:
        sk.fill(leg, SIDES + ("top",), pants, shade=0.1, seed=seed + 3)
        sk.fill(leg, SIDES + ("bottom",), boots, rows=(9, 12))
    if not sleeveless:
        for a in ARMS:
            sk.fill(a, SIDES + ("top",), top, rows=(0, 4), shade=0.1, seed=seed + 5)
    if wraps:
        for a in ARMS:
            sk.fill(a, SIDES, wraps, rows=(8, 11), shade=0.15, seed=seed + 7)
    folds(sk, "body", SIDES, top, seed + 11, n=3)
    for leg in LEGS:
        folds(sk, leg, SIDES, pants, seed + 12, n=2)
        sk.fill(leg, SIDES, dk(boots, 0.6), rows=(11, 12))              # sole
        sk.rect(leg, "front", 1, 18, 6, 19, lt(boots, 1.15) + (255,))   # toe cap
    sk.rect("body", "front", 9, 15, 12, 18, dk(sash, 0.85) + (255,))    # sash knot
    sk.line("body", "front", [(10, 19), (9, 23)], sash); sk.line("body", "front", [(11, 19), (12, 23)], sash)
    if torn:
        rnd = random.Random(seed)
        for side in SIDES:
            _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
            for x in range(0, fw, 2):
                if rnd.random() < 0.5:
                    sk.rect("body", side, x, 22 + rnd.randint(0, 1), x + 1, 23, (0, 0, 0, 0))

def plates(sk, base, line, gem, seed):
    full_body(sk, base, seed)
    # plate seams
    for p in PARTS:
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for y in range(5, fh, 7):
                sk.line(p, side, [(0, y - 1), (fw - 1, y - 1)], lt(base, 1.15) + (255,))  # bevel
                sk.line(p, side, [(0, y), (fw - 1, y)], line)
    # chest plate outline + shoulder/chest/head gems
    sk.line("body", "front", [(2, 2), (2, 14), (8, 18), (13, 14), (13, 2)], line)
    sk.rect("body", "front", 5, 5, 10, 10, dk(line, 0.8) + (255,))       # gem rim
    sk.rect("body", "front", 6, 6, 9, 9, gem); sk.rect("body", "front", 6, 6, 7, 7, lt(gem, 1.5))
    sk.rect("body", "front", 8, 8, 9, 9, dk(gem, 0.6))
    for a in ARMS:
        sk.rect(a, "top", 2, 2, 5, 5, gem)
        sk.rect(a, "front", 0, 0, 7, 1, line)
    sk.rect("head", "top", 6, 6, 9, 9, gem)
    sk.rect("head", "front", 2, 0, 13, 2, dk(base, 0.85))
    for side in ("left", "right"):  # cheek ridges
        sk.line("head", side, [(4, 4), (10, 9), (12, 14)], line)


# ---- HD finishing (v1.37) ---------------------------------------------------------
def glow_line(sk, part, side, pts, col, width=1):
    """A bright line with a soft wider glow underneath."""
    sk.line(part, side, pts, col[:3] + (70,), width=width + 2)
    sk.line(part, side, pts, lt(col, 1.25) + (255,), width=width)

def muscles(sk, base):
    """Chest, abs and arm definition for bare-skin designs."""
    sh = dk(base, 0.78) + (255,)
    hi = lt(base, 1.1) + (255,)
    sk.line("body", "front", [(1, 7), (5, 8), (7, 7)], sh)          # pecs
    sk.line("body", "front", [(8, 7), (10, 8), (14, 7)], sh)
    sk.line("body", "front", [(7, 2), (7, 21)], sh)                   # centre line
    for y in (11, 14, 17):                                            # abs
        sk.line("body", "front", [(4, y), (6, y)], sh); sk.line("body", "front", [(9, y), (11, y)], sh)
    sk.line("body", "front", [(2, 3), (5, 3)], hi); sk.line("body", "front", [(10, 3), (13, 3)], hi)
    for a in ARMS:
        sk.line(a, "front", [(1, 4), (2, 9), (1, 12)], sh)            # bicep / forearm
        sk.line(a, "front", [(5, 3), (6, 8)], hi)

def folds(sk, part, sides, col, seed, n=3):
    """Diagonal cloth folds."""
    rnd = random.Random(seed)
    for side in sides:
        _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
        for _ in range(n):
            x = rnd.randrange(1, fw - 2); y = rnd.randrange(1, fh - 6)
            sk.line(part, side, [(x, y), (x + rnd.choice((-2, 2)), y + rnd.randint(3, 6))], dk(col, 0.72) + (255,))

def hd_finish(sk):
    """Top-lit shading, darker face edges and seams between materials."""
    px = sk.im.load()
    parts = [(PARTS[p][0], PARTS[p][1]) for p in PARTS] + [(EXTRA_UV[e], EXTRA_SIZE[e]) for e in EXTRA_UV]
    for uv, size in parts:
        for side in ALL:
            x, y, fw, fh = Skin.face(uv, size, side)
            orig = {(i, j): px[x + i, y + j] for i in range(fw) for j in range(fh)}
            for (i, j), c in orig.items():
                if c[3] == 0:
                    continue
                k = 1.0
                if side not in ("top", "bottom"):
                    k *= 1.1 - 0.22 * (j / max(1, fh - 1))           # light from above
                elif side == "top":
                    k *= 1.12
                else:
                    k *= 0.75
                if i == 0 or j == 0 or i == fw - 1 or j == fh - 1:
                    k *= 0.86                                         # edge shadow
                up = orig.get((i, j - 1))
                if up and up[3] and sum(abs(a - b) for a, b in zip(up[:3], c[:3])) > 90:
                    k *= 0.82                                         # seam under a material change
                px[x + i, y + j] = tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3],)

# ---- Designs ---------------------------------------------------------------------
NAMEK_GREEN = (92, 168, 74)
DESIGNS = {}

def design(form_id, name, kind):
    def wrap(fn):
        DESIGNS[form_id] = (name, kind, fn)
        return fn
    return wrap

@design("human_unlock", "Unlocked Potential", "overlay")
def _(sk):
    sk.eyes((210, 245, 255), (120, 220, 255), glow=(120, 220, 255, 110))
    ki_lines(sk, (130, 225, 255, 200), ARMS, 11, n=3)
    ki_lines(sk, (130, 225, 255, 150), ("body",), 12, n=2)

@design("max_power", "Max Power", "overlay")
def _(sk):
    sk.eyes((255, 236, 200), (255, 150, 40), glow=(255, 120, 30, 120))
    ki_lines(sk, (230, 70, 40, 220), ARMS, 21, n=6)
    ki_lines(sk, (230, 70, 40, 180), ("body",), 22, n=4)
    for a in ARMS:  # torn sleeve stubs
        sk.fill(a, SIDES, (60, 60, 70), rows=(0, 2), shade=0.2, seed=23)

@design("giant", "Namekian Giant", "full")
def _(sk):
    full_body(sk, NAMEK_GREEN, 31)
    muscles(sk, NAMEK_GREEN)
    for p in ("rightArm", "leftArm"):  # darker scale spots
        ki_lines(sk, dk(NAMEK_GREEN, 0.75) + (255,), (p,), 32, n=4)
    gi(sk, (28, 74, 92), (40, 40, 48), (214, 170, 60), (70, 52, 40), wraps=(196, 180, 150), seed=33)
    sk.eyes((255, 255, 255), (30, 30, 30), brow=dk(NAMEK_GREEN, 0.6))
    sk.mouth(dk(NAMEK_GREEN, 0.5))
    paint_extras(sk, ANTENNAE, NAMEK_GREEN, seed=34)
    paint_extras(sk, ["ear_r", "ear_l"], NAMEK_GREEN)

@design("orange", "Orange Namekian", "full")
def _(sk):
    c = (232, 136, 46)
    full_body(sk, c, 41)
    muscles(sk, c)
    ki_lines(sk, dk(c, 0.7) + (255,), ARMS + ("body",), 42, n=4)
    gi(sk, (26, 22, 26), (30, 28, 32), (170, 30, 40), (40, 30, 26), wraps=(120, 100, 80), torn=True, seed=43)
    sk.eyes((255, 240, 160), (255, 210, 60), brow=dk(c, 0.55), glow=(255, 220, 90, 90))
    sk.mouth(dk(c, 0.45), wide=True)
    paint_extras(sk, ANTENNAE + ["ear_r", "ear_l"], c, seed=44)

@design("final_form", "Pearl Form", "full")
def _(sk):
    plates(sk, (236, 236, 242), (170, 170, 186), (40, 190, 180), 51)
    sk.eyes((255, 255, 255), (200, 30, 40))
    sk.mouth((150, 150, 165))
    horns(sk, (236, 236, 242), 56)

@design("golden", "Gilded Form", "full")
def _(sk):
    plates(sk, (238, 192, 62), (150, 104, 30), (40, 170, 90), 61)
    sk.eyes((255, 252, 230), (255, 255, 255), glow=(255, 240, 160, 120))
    sk.mouth((150, 104, 30))
    horns(sk, (238, 192, 62), 66)

@design("black", "Obsidian Form", "full")
def _(sk):
    plates(sk, (36, 32, 42), (200, 40, 60), (220, 40, 60), 71)
    sk.eyes((255, 230, 230), (230, 30, 50), glow=(230, 40, 60, 120))
    sk.mouth((120, 30, 40))
    horns(sk, (36, 32, 42), 76)

@design("super_majin", "Super Majin", "full")
def _(sk):
    c = (236, 140, 178)
    full_body(sk, c, 81)
    # long violet coat with silver trim, grey trousers, black gloves/boots
    coat = (92, 52, 130); trim = (200, 200, 214)
    sk.fill("body", SIDES, coat, shade=0.1, seed=82)
    sk.fill("body", SIDES, trim, rows=(0, 1))
    sk.line("body", "front", [(7, 0), (7, 23)], trim); sk.line("body", "front", [(8, 0), (8, 23)], trim)
    for y in (5, 10, 15):                                                   # buttons
        sk.rect("body", "front", 5, y, 5, y, (230, 200, 90)); sk.rect("body", "front", 10, y, 10, y, (230, 200, 90))
    folds(sk, "body", ("back", "left", "right"), coat, 86, n=3)
    for a in ARMS:
        sk.fill(a, SIDES + ("top",), coat, rows=(0, 7), shade=0.1, seed=83)
        sk.fill(a, SIDES, trim, rows=(7, 8))
        sk.fill(a, SIDES + ("bottom",), (26, 24, 30), rows=(9, 12))
    for l in LEGS:
        sk.fill(l, SIDES + ("top",), (110, 110, 120), shade=0.1, seed=84)
        sk.fill(l, SIDES + ("bottom",), (26, 24, 30), rows=(9, 12))
        sk.fill(l, ("front", "left", "right", "back"), coat, rows=(0, 3))  # coat tails
    sk.eyes((60, 10, 20), (255, 60, 60), brow=dk(c, 0.55))
    sk.mouth(dk(c, 0.45), wide=True)
    paint_tendril(sk, "l", c, 85)  # large head tendril

@design("kid_majin", "Feral Majin", "full")
def _(sk):
    c = (214, 88, 160)
    full_body(sk, c, 91)
    muscles(sk, c)
    ki_lines(sk, (255, 220, 80, 230), ARMS + LEGS + ("body",), 92, n=3)
    for l in LEGS:  # tattered dark red wraps
        sk.fill(l, SIDES + ("top",), (110, 24, 34), rows=(0, 5), shade=0.2, seed=93)
    sk.fill("body", SIDES, (110, 24, 34), rows=(9, 12), shade=0.2, seed=94)
    sk.eyes((255, 255, 255), (20, 20, 20), brow=dk(c, 0.5))
    sk.mouth((40, 10, 20), wide=True)
    paint_extras(sk, TENDRIL, c, tip=lt(c, 1.06), seed=95)  # small head tendril (it's a kid)

@design("power_boost", "Power Boost", "overlay")
def _(sk):
    metal, glow = (150, 156, 168), (90, 230, 255)
    sk.rect("head", "front", 11, 5, 15, 13, metal + (255,))  # cheek plate
    sk.line("head", "front", [(11, 5), (11, 13)], glow)
    sk.rect("head", "front", 11, 8, 12, 9, glow)  # cyber eye
    for a in ARMS:
        sk.fill(a, SIDES, metal, rows=(6, 12), shade=0.08, seed=101)
        for side in SIDES:
            glow_line(sk, a, side, [(0, 13), (7, 13)], glow)
            glow_line(sk, a, side, [(0, 19), (7, 19)], glow)

@design("overclock", "Overclock", "overlay")
def _(sk):
    metal, glow = (110, 114, 126), (255, 110, 40)
    sk.rect("head", "front", 11, 4, 15, 14, metal + (255,))
    sk.rect("head", "front", 11, 8, 12, 9, glow); sk.rect("head", "front", 4, 8, 5, 9, glow)
    for a in ARMS:
        sk.fill(a, SIDES + ("top",), metal, shade=0.08, seed=111)
        for side in SIDES:
            for y in (6, 12, 18):
                glow_line(sk, a, side, [(0, y), (7, y)], glow)
    sk.fill("body", SIDES, metal, rows=(0, 7), shade=0.08, seed=112)  # chest plate
    sk.rect("body", "front", 5, 4, 10, 9, (40, 30, 30)); sk.rect("body", "front", 6, 5, 9, 8, glow)  # exposed core
    sk.rect("body", "front", 7, 6, 8, 7, (255, 230, 160))
    for l in LEGS:
        sk.fill(l, SIDES, metal, rows=(3, 8), shade=0.08, seed=113)
        for side in SIDES:
            sk.line(l, side, [(0, 10), (7, 10)], glow)

@design("divine_aura", "Divine Aura", "overlay")
def _(sk):
    sk.eyes((235, 245, 255), (170, 210, 255), glow=(200, 225, 255, 90))
    ki_lines(sk, (215, 235, 255, 170), ARMS + ("body",), 121, n=2)
    for h in ("halo_a", "halo_b", "halo_c", "halo_d"):
        sk.fill((EXTRA_UV[h], EXTRA_SIZE[h]), ALL, (255, 226, 120))

@design("god_destruction", "Destroyer's Raiment", "overlay")
def _(sk):
    robe, gold = (52, 26, 70), (226, 182, 70)
    sk.fill("body", SIDES, robe, shade=0.1, seed=131)
    sk.fill("body", SIDES, gold, rows=(0, 1)); sk.fill("body", SIDES, gold, rows=(8, 10))
    for side in SIDES:  # geometric trim
        for x in range(0, 16, 4):
            sk.rect("body", side, x, 18, x + 1, 19, gold + (255,))
    for l in LEGS:
        sk.fill(l, SIDES + ("top",), robe, rows=(0, 9), shade=0.1, seed=132)
        sk.fill(l, SIDES, gold, rows=(8, 9))
    for a in ARMS:
        sk.fill(a, SIDES, gold, rows=(8, 11), shade=0.1, seed=133)  # bracers
    sk.eyes((210, 160, 255), (150, 60, 255), glow=(160, 80, 255, 110))


# ---- v1.42: full-detail race textures, one at a time ---------------------------------
def ramp(c, n=4):
    """n shades of a colour: highlight, base, shade, deep shadow."""
    ks = [1.22, 1.0, 0.78, 0.58][:n]
    return [tuple(max(0, min(255, int(v * k) + (12 if k > 1 else 0))) for v in c) for k in ks]

def ribbed(sk, part, sides, col, rows=None, step=3, seed=0):
    """Segmented, plated limb bands: highlight row, body, shadow row per segment."""
    hi, base, sh, deep = ramp(col)
    sk.fill(part, sides, base, rows=rows, shade=0.06, seed=seed)
    for side in sides:
        _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
        y0 = (rows[0] * S) if rows else 0
        y1 = (rows[1] * S) if rows else fh
        for y in range(y0, y1, step * 2):
            sk.line(part, side, [(0, y), (fw - 1, y)], hi)
            if y + step * 2 - 1 < y1:
                sk.line(part, side, [(0, y + step * 2 - 1), (fw - 1, y + step * 2 - 1)], sh)
        sk.line(part, side, [(0, y0), (0, y1 - 1)], deep)            # edge shadow
        sk.line(part, side, [(fw - 1, y0), (fw - 1, y1 - 1)], deep)

def plate(sk, part, side, x0, y0, x1, y1, col, gem=None):
    """A raised armour plate with a lit top edge, shaded bottom edge and optional gem."""
    hi, base, sh, deep = ramp(col)
    sk.rect(part, side, x0, y0, x1, y1, base + (255,))
    sk.rect(part, side, x0, y0, x1, y0, hi + (255,))
    sk.rect(part, side, x0, y0, x0, y1, hi + (255,))
    sk.rect(part, side, x0, y1, x1, y1, deep + (255,))
    sk.rect(part, side, x1, y0, x1, y1, sh + (255,))
    if gem:
        ghi, gb, gsh, gdeep = ramp(gem)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        sk.rect(part, side, cx - 2, cy - 2, cx + 1, cy + 1, gdeep + (255,))
        sk.rect(part, side, cx - 1, cy - 1, cx + 1, cy + 1, gb + (255,))
        sk.rect(part, side, cx - 1, cy - 1, cx - 1, cy - 1, (255, 255, 240, 255))
        sk.rect(part, side, cx + 1, cy + 1, cx + 1, cy + 1, gsh + (255,))

# ---- v1.42c: refined white-and-crimson Frieza Race looks --------------------------------
WHITE, CRIMSON, GOLD_TRIM, STRAP = (236, 234, 240), (172, 30, 46), (226, 182, 74), (54, 32, 28)

def smooth_skin(sk, col, seed):
    """Clean skin: soft vertical gradient, cool shadow on side faces, no noise speckle."""
    hi, base, sh, deep = ramp(col)
    for p in PARTS:
        for side in ALL:
            uv, size = PARTS[p][0], PARTS[p][1]
            x, y, fw, fh = Skin.face(uv, size, side)
            for j in range(fh):
                t = j / max(1, fh - 1)
                c = tuple(int(base[k] * (1.04 - 0.1 * t) + (4 if side in ("left", "right") else 0) * (k == 2)) for k in range(3))
                if side in ("left", "right"):
                    c = tuple(int(v * 0.93) for v in c)
                sk.d.line((x, y + j, x + fw - 1, y + j), fill=tuple(min(255, v) for v in c) + (255,))

def limb_muscles(sk, part, col):
    hi, base, sh, deep = ramp(col)
    for side in ("front", "back"):
        sk.line(part, side, [(1, 3), (2, 8), (1, 12)], sh)
        sk.line(part, side, [(6, 4), (5, 9)], hi)
    for side in ("left", "right"):
        sk.line(part, side, [(3, 2), (4, 10)], sh)

def armor_plate(sk, part, side, x0, y0, x1, y1, col, trim=GOLD_TRIM, rivets=True):
    """Layered plate: dark outline, lit top-left, shaded bottom-right, gold trim and rivets."""
    hi, base, sh, deep = ramp(col)
    outline = tuple(int(v * 0.35) for v in col)
    sk.rect(part, side, x0, y0, x1, y1, outline + (255,))
    sk.rect(part, side, x0 + 1, y0 + 1, x1 - 1, y1 - 1, base + (255,))
    sk.rect(part, side, x0 + 1, y0 + 1, x1 - 1, y0 + 1, hi + (255,))
    sk.rect(part, side, x0 + 1, y0 + 1, x0 + 1, y1 - 1, hi + (255,))
    sk.rect(part, side, x0 + 1, y1 - 1, x1 - 1, y1 - 1, sh + (255,))
    sk.rect(part, side, x1 - 1, y0 + 2, x1 - 1, y1 - 1, sh + (255,))
    if trim and y1 - y0 >= 5:
        sk.rect(part, side, x0 + 1, y1 - 2, x1 - 1, y1 - 2, ramp(trim)[1] + (255,))
    if rivets and x1 - x0 >= 5 and y1 - y0 >= 5:
        for rx in (x0 + 2, x1 - 2):
            sk.rect(part, side, rx, y0 + 2, rx, y0 + 2, ramp(GOLD_TRIM)[0] + (255,))

def warlord_face(sk, skin, crest, eye, glow=False):
    hi, base, sh, deep = ramp(skin)
    line = tuple(int(v * 0.42) for v in skin)
    # crest plate across the brow and up over the skull
    armor_plate(sk, "head", "front", 3, 0, 12, 4, crest, rivets=False)
    sk.rect("head", "top", 5, 0, 10, 15, ramp(crest)[1] + (255,))
    for y in range(1, 16, 3):
        sk.line("head", "top", [(5, y), (10, y)], ramp(crest)[0]); sk.line("head", "top", [(5, y + 1), (10, y + 1)], ramp(crest)[2])
    sk.rect("head", "back", 5, 0, 10, 6, ramp(crest)[1] + (255,)); sk.line("head", "back", [(5, 6), (10, 6)], ramp(crest)[3])
    # sockets, brows, cheekbones, nose, mouth
    for x0 in (2, 9):
        sk.rect("head", "front", x0, 7, x0 + 4, 10, sh + (255,))
    sk.line("head", "front", [(2, 6), (6, 7)], line); sk.line("head", "front", [(13, 6), (9, 7)], line)
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (24, 18, 22, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 8, eye + (255,))
        sk.rect("head", "front", ix, 9, ix + 1, 9, ramp(eye)[2] + (255,))
        if glow:
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, eye + (70,))
    sk.line("head", "front", [(2, 11), (4, 12)], sh); sk.line("head", "front", [(13, 11), (11, 12)], sh)   # cheekbones
    sk.rect("head", "front", 7, 10, 8, 11, sh + (255,))                                                    # nose shadow
    sk.line("head", "front", [(5, 13), (10, 13)], line); sk.line("head", "front", [(10, 13), (11, 12)], line)  # smirk
    sk.line("head", "front", [(3, 15), (12, 15)], sh)                                                      # jaw
    for side in ("left", "right"):
        sk.line("head", side, [(1, 10), (6, 14), (14, 14)], sh)                                            # jawline

def harness(sk):
    for side in ("front", "back"):
        sk.line("body", side, [(1, 0), (14, 20)], STRAP, width=2)
        sk.line("body", side, [(14, 0), (1, 20)], STRAP, width=2)
    sk.rect("body", "front", 6, 9, 9, 12, ramp(GOLD_TRIM)[2] + (255,)); sk.rect("body", "front", 7, 10, 8, 11, ramp(GOLD_TRIM)[0] + (255,))
    sk.fill("body", SIDES, STRAP, rows=(10, 11))
    sk.rect("body", "front", 6, 20, 9, 22, ramp(GOLD_TRIM)[1] + (255,)); sk.rect("body", "front", 7, 21, 8, 21, ramp(GOLD_TRIM)[3] + (255,))

def ivory_horns(sk, col, band=None, seed=0):
    for side in (HORNS_R, HORNS_L):
        for i, n in enumerate(side):
            sk.fill((EXTRA_UV[n], EXTRA_SIZE[n]), ALL, ramp(col)[min(3, i)], shade=0.05, seed=seed + i)
        if band:
            sk.fill((EXTRA_UV[side[0]], EXTRA_SIZE[side[0]]), SIDES, band, rows=(2, 3))

@design("arcosian_base", "Frieza Race: Base Form", "full")
def _(sk):
    """Original warlord look: clean pale-white skin with muscle definition, a crimson
    breastplate on a crossed leather harness, one heavy spiked crimson pauldron, crimson
    gauntlets and knee guards with gold trim and rivets, a ridged crimson crest, amber eyes."""
    AMBER = (255, 176, 48)
    smooth_skin(sk, WHITE, 300)
    for limb in ARMS + LEGS:
        limb_muscles(sk, limb, WHITE)
    muscles(sk, WHITE)
    warlord_face(sk, WHITE, CRIMSON, AMBER)
    armor_plate(sk, "body", "front", 3, 0, 12, 11, CRIMSON)
    armor_plate(sk, "body", "back", 3, 0, 12, 9, CRIMSON)
    harness(sk)
    for y in (3, 6):
        glow_line(sk, "body", "front", [(6, y), (7, y + 2), (8, y + 2), (9, y)], AMBER)
    for side in SIDES:                                                     # heavy right pauldron
        armor_plate(sk, "rightArm", side, 0, 0, 7, 10, CRIMSON)
    armor_plate(sk, "rightArm", "top", 0, 0, 7, 7, CRIMSON, rivets=False)
    for x in (1, 4):
        sk.rect("rightArm", "top", x, 2, x + 1, 3, (40, 10, 14, 255)); sk.rect("rightArm", "top", x, 2, x, 2, (255, 240, 230, 255))
    for arm in ARMS:
        for side in SIDES:
            armor_plate(sk, arm, side, 0, 14, 7, 23, CRIMSON)
        glow_line(sk, arm, "front", [(3, 16), (3, 20)], AMBER)
    for leg in LEGS:
        for side in SIDES:
            armor_plate(sk, leg, side, 0, 7, 7, 14, CRIMSON)
            sk.rect(leg, side, 0, 21, 7, 23, ramp(WHITE)[3] + (255,))
        for x in (1, 3, 5):
            sk.rect(leg, "front", x, 22, x, 23, (250, 246, 236, 255))
    ivory_horns(sk, (230, 222, 200), seed=310)

def cracks(sk, part, side, col, seed, n=3, x0=0, y0=0, x1=None, y1=None):
    """Glowing molten cracks inside an area of a face."""
    rnd = random.Random(seed)
    _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side) if part in PARTS else Skin.face(part[0], part[1], side)
    x1 = fw - 1 if x1 is None else x1
    y1 = fh - 1 if y1 is None else y1
    for _ in range(n):
        x, y = rnd.randint(x0, x1), rnd.randint(y0, y1)
        pts = [(x, y)]
        for _ in range(rnd.randint(2, 4)):
            x = max(x0, min(x1, x + rnd.choice((-2, -1, 1, 2))))
            y = max(y0, min(y1, y + rnd.choice((-2, -1, 1, 2))))
            pts.append((x, y))
        glow_line(sk, part, side, pts, col)

@design("arcosian_final", "Frieza Race: Final Form", "full")
def _(sk):
    """Final Form: crimson armour now encases most of the body in layered, gold-trimmed
    plates; white-gold energy runs along the plate seams; eyes burn gold; twin spiked
    pauldrons and a gold band on each horn."""
    DEEP = (148, 18, 34)
    GLOW = (255, 214, 100)
    smooth_skin(sk, WHITE, 320)
    muscles(sk, WHITE)
    warlord_face(sk, WHITE, DEEP, GLOW, glow=True)
    for side in ("left", "right", "back"):                               # helm sides
        armor_plate(sk, "head", side, 0, 0, 15, 8, DEEP, rivets=False)
    for side in SIDES:                                                     # full cuirass
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        armor_plate(sk, "body", side, 0, 0, fw - 1, 9, DEEP)
        armor_plate(sk, "body", side, 0, 9, fw - 1, 18, DEEP)
        glow_line(sk, "body", side, [(1, 9), (fw - 2, 9)], GLOW)          # energy along the seam
    sk.rect("body", "front", 5, 2, 10, 7, (40, 8, 14, 255))
    glow_line(sk, "body", "front", [(6, 3), (7, 6), (8, 6), (9, 3)], GLOW)
    harness(sk)
    for arm in ARMS:
        for side in SIDES:
            armor_plate(sk, arm, side, 0, 0, 7, 10, DEEP)
            armor_plate(sk, arm, side, 0, 13, 7, 23, DEEP)
            glow_line(sk, arm, side, [(1, 13), (6, 13)], GLOW)
        armor_plate(sk, arm, "top", 0, 0, 7, 7, DEEP, rivets=False)
        for x in (1, 4):
            sk.rect(arm, "top", x, 1, x + 1, 2, (40, 8, 14, 255)); sk.rect(arm, "top", x, 1, x, 1, (255, 240, 230, 255))
    for leg in LEGS:
        for side in SIDES:
            armor_plate(sk, leg, side, 0, 4, 7, 13, DEEP)
            armor_plate(sk, leg, side, 0, 13, 7, 21, DEEP)
            glow_line(sk, leg, side, [(1, 13), (6, 13)], GLOW)
            sk.rect(leg, side, 0, 22, 7, 23, ramp(WHITE)[3] + (255,))
        for x in (1, 3, 5):
            sk.rect(leg, "front", x, 22, x, 23, (255, 250, 240, 255))
    ivory_horns(sk, (236, 230, 212), band=ramp(GLOW)[1], seed=330)

@design("arcosian_golden", "Frieza Race: Golden Form", "full")
def _(sk):
    """Golden Form: the crimson armour turns to radiant polished gold with crimson trim,
    white-hot energy along every seam, a sunburst rune in the chest, glowing white eyes,
    gold-sheened skin and gold-capped horns."""
    GOLDA, TRIM, HOT = (240, 196, 64), (160, 24, 40), (255, 250, 226)
    SKIN = (246, 236, 214)                                                # warm gold-sheened white
    smooth_skin(sk, SKIN, 340)
    muscles(sk, SKIN)
    warlord_face(sk, SKIN, GOLDA, HOT, glow=True)
    for x0 in (3, 10):                                                     # white-hot eyes in dark sockets
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 10, (70, 40, 10, 255))
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (255, 226, 120, 255))
        sk.rect("head", "front", x0 + (1 if x0 == 3 else 0), 8, x0 + (2 if x0 == 3 else 1), 9, HOT + (255,))
        sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, (255, 220, 120, 110))
    for side in ("left", "right", "back"):
        armor_plate(sk, "head", side, 0, 0, 15, 8, GOLDA, trim=TRIM, rivets=False)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        armor_plate(sk, "body", side, 0, 0, fw - 1, 9, GOLDA, trim=TRIM)
        armor_plate(sk, "body", side, 0, 9, fw - 1, 18, GOLDA, trim=TRIM)
        glow_line(sk, "body", side, [(1, 9), (fw - 2, 9)], HOT)
        # polished shine: a diagonal light streak on each plate
        sk.line("body", side, [(2, 6), (5, 2)], (255, 252, 236, 170))
        sk.line("body", side, [(2, 15), (5, 11)], (255, 252, 236, 140))
    # Sunburst rune in the chest.
    sk.rect("body", "front", 5, 2, 10, 7, (120, 70, 10, 255))
    for (x1, y1) in ((7, 1), (7, 8), (4, 4), (11, 4), (5, 2), (10, 2), (5, 7), (10, 7)):
        glow_line(sk, "body", "front", [(7, 4), (x1, y1)], HOT)
    sk.rect("body", "front", 7, 4, 8, 5, (255, 255, 255, 255))
    harness(sk)
    sk.fill("body", SIDES, TRIM, rows=(10, 11))                              # crimson sash over the belt
    for arm in ARMS:
        for side in SIDES:
            armor_plate(sk, arm, side, 0, 0, 7, 10, GOLDA, trim=TRIM)
            armor_plate(sk, arm, side, 0, 13, 7, 23, GOLDA, trim=TRIM)
            glow_line(sk, arm, side, [(1, 13), (6, 13)], HOT)
            sk.line(arm, side, [(1, 8), (4, 2)], (255, 252, 236, 150))
        armor_plate(sk, arm, "top", 0, 0, 7, 7, GOLDA, trim=None, rivets=False)
        for x in (1, 4):
            sk.rect(arm, "top", x, 1, x + 1, 2, ramp(TRIM)[3] + (255,)); sk.rect(arm, "top", x, 1, x, 1, HOT + (255,))
    for leg in LEGS:
        for side in SIDES:
            armor_plate(sk, leg, side, 0, 4, 7, 13, GOLDA, trim=TRIM)
            armor_plate(sk, leg, side, 0, 13, 7, 21, GOLDA, trim=TRIM)
            glow_line(sk, leg, side, [(1, 13), (6, 13)], HOT)
            sk.line(leg, side, [(1, 11), (4, 6)], (255, 252, 236, 150))
            sk.rect(leg, side, 0, 22, 7, 23, ramp(SKIN)[3] + (255,))
        for x in (1, 3, 5):
            sk.rect(leg, "front", x, 22, x, 23, (255, 246, 210, 255))
    # Horns: ivory bases rising into gold caps.
    for side in (HORNS_R, HORNS_L):
        sk.fill((EXTRA_UV[side[0]], EXTRA_SIZE[side[0]]), ALL, ramp((238, 230, 210))[1], shade=0.05, seed=350)
        sk.fill((EXTRA_UV[side[1]], EXTRA_SIZE[side[1]]), ALL, ramp(GOLDA)[1], shade=0.05, seed=351)
        sk.fill((EXTRA_UV[side[2]], EXTRA_SIZE[side[2]]), ALL, ramp(GOLDA)[0], shade=0.05, seed=352)
        sk.fill((EXTRA_UV[side[1]], EXTRA_SIZE[side[1]]), SIDES, ramp(TRIM)[1], rows=(0, 1))

@design("arcosian_black", "Frieza Race: Black Form", "full")
def _(sk):
    """Black Form: glossy obsidian armour and charcoal skin with mirror-like highlights,
    crimson trim, blood-red energy along every seam, a crimson core rune in the chest,
    glowing red eyes and obsidian horns with red veins."""
    OBS, SKIN, TRIM, RED = (30, 28, 36), (58, 54, 64), (150, 20, 34), (255, 46, 60)
    GLOSS = (200, 205, 225, 190)
    smooth_skin(sk, SKIN, 360)
    muscles(sk, SKIN)
    warlord_face(sk, SKIN, OBS, RED, glow=True)
    for x0 in (3, 10):                                                     # red glowing eyes
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 10, (12, 8, 12, 255))
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (200, 20, 34, 255))
        sk.rect("head", "front", x0 + (1 if x0 == 3 else 0), 8, x0 + (2 if x0 == 3 else 1), 8, (255, 150, 150, 255))
        sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, RED + (110,))
    for side in ("left", "right", "back"):
        armor_plate(sk, "head", side, 0, 0, 15, 8, OBS, trim=TRIM, rivets=False)
        sk.line("head", side, [(2, 6), (6, 2)], GLOSS)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        armor_plate(sk, "body", side, 0, 0, fw - 1, 9, OBS, trim=TRIM)
        armor_plate(sk, "body", side, 0, 9, fw - 1, 18, OBS, trim=TRIM)
        glow_line(sk, "body", side, [(1, 9), (fw - 2, 9)], RED)
        sk.line("body", side, [(2, 6), (6, 2)], GLOSS)                     # glossy streaks
        sk.line("body", side, [(3, 6), (6, 3)], (200, 205, 225, 90))
        sk.line("body", side, [(2, 15), (5, 12)], GLOSS)
    # Crimson core rune.
    sk.rect("body", "front", 5, 2, 10, 7, (10, 4, 8, 255))
    sk.rect("body", "front", 6, 3, 9, 6, (150, 10, 24, 255))
    sk.rect("body", "front", 7, 4, 8, 5, RED + (255,)); sk.rect("body", "front", 7, 4, 7, 4, (255, 200, 200, 255))
    for (x1, y1) in ((4, 1), (11, 1), (4, 8), (11, 8)):
        glow_line(sk, "body", "front", [(7, 4), (x1, y1)], RED)
    harness(sk)
    sk.fill("body", SIDES, TRIM, rows=(10, 11))
    for arm in ARMS:
        for side in SIDES:
            armor_plate(sk, arm, side, 0, 0, 7, 10, OBS, trim=TRIM)
            armor_plate(sk, arm, side, 0, 13, 7, 23, OBS, trim=TRIM)
            glow_line(sk, arm, side, [(1, 13), (6, 13)], RED)
            sk.line(arm, side, [(1, 8), (4, 2)], GLOSS); sk.line(arm, side, [(1, 21), (4, 15)], GLOSS)
        armor_plate(sk, arm, "top", 0, 0, 7, 7, OBS, trim=None, rivets=False)
        for x in (1, 4):
            sk.rect(arm, "top", x, 1, x + 1, 2, (150, 10, 24, 255)); sk.rect(arm, "top", x, 1, x, 1, (255, 140, 140, 255))
    for leg in LEGS:
        for side in SIDES:
            armor_plate(sk, leg, side, 0, 4, 7, 13, OBS, trim=TRIM)
            armor_plate(sk, leg, side, 0, 13, 7, 21, OBS, trim=TRIM)
            glow_line(sk, leg, side, [(1, 13), (6, 13)], RED)
            sk.line(leg, side, [(1, 11), (4, 6)], GLOSS)
            sk.rect(leg, side, 0, 22, 7, 23, ramp(SKIN)[3] + (255,))
        for x in (1, 3, 5):
            sk.rect(leg, "front", x, 22, x, 23, (200, 30, 44, 255))         # red claws
    # Obsidian horns with a red vein band and glossy tips.
    for side in (HORNS_R, HORNS_L):
        for i, n in enumerate(side):
            sk.fill((EXTRA_UV[n], EXTRA_SIZE[n]), ALL, ramp(OBS)[min(2, i)], shade=0.05, seed=370 + i)
        sk.fill((EXTRA_UV[side[0]], EXTRA_SIZE[side[0]]), SIDES, RED, rows=(2, 3))
        sk.fill((EXTRA_UV[side[2]], EXTRA_SIZE[side[2]]), ("top",), (150, 150, 170))

# ---- v1.42d: Namekian line - "forest guardian" (original design) ---------------------------
TEAL, CREAM, BRONZE, BARK = (28, 92, 96), (226, 214, 184), (184, 128, 58), (74, 52, 38)

def nk_skin(sk, col, seed):
    """Namekian skin: clean shading plus a ridged texture on forearms and calves."""
    hi, base, sh, deep = ramp(col)
    smooth_skin(sk, col, seed)
    for p in ARMS + LEGS:
        for side in SIDES:
            rows = range(14, 22, 2)
            for y in rows:
                sk.line(p, side, [(1, y), (6, y)], sh)
                sk.line(p, side, [(1, y - 1), (6, y - 1)], hi)
    for y in (4, 8, 12):                                     # skull ridges
        sk.line("head", "top", [(3, y), (12, y)], sh)
        sk.line("head", "top", [(3, y - 1), (12, y - 1)], hi)

def nk_face(sk, col, iris, mood):
    """mood: calm / fierce / rage"""
    hi, base, sh, deep = ramp(col)
    ink = tuple(int(v * 0.3) for v in col)
    # brow ridge and sockets
    sk.rect("head", "front", 2, 5, 13, 5, hi + (255,))
    sk.rect("head", "front", 2, 6, 13, 6, sh + (255,))
    for x0 in (2, 9):
        sk.rect("head", "front", x0, 7, x0 + 4, 10, sh + (255,))
    if mood == "calm":
        sk.line("head", "front", [(2, 6), (6, 6)], ink); sk.line("head", "front", [(9, 6), (13, 6)], ink)
    else:
        sk.line("head", "front", [(2, 5), (6, 7)], ink); sk.line("head", "front", [(13, 5), (9, 7)], ink)
        sk.line("head", "front", [(3, 5), (6, 6)], ink); sk.line("head", "front", [(12, 5), (9, 6)], ink)
    for x0 in (3, 10):
        white = (250, 250, 240) if mood != "rage" else iris
        sk.rect("head", "front", x0, 8, x0 + 2, 9, white + (255,))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, (ramp(iris)[2] if mood == "rage" else iris) + (255,))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))           # upper lid
        if mood != "calm":
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, iris + (90,))
    # nose ridge, cheeks, mouth
    sk.rect("head", "front", 7, 9, 7, 11, hi + (255,)); sk.rect("head", "front", 8, 9, 8, 11, sh + (255,))
    sk.line("head", "front", [(2, 11), (4, 13)], sh); sk.line("head", "front", [(13, 11), (11, 13)], sh)
    if mood == "calm":
        sk.line("head", "front", [(6, 13), (9, 13)], ink)
    elif mood == "fierce":
        sk.rect("head", "front", 5, 12, 10, 13, ink + (255,)); sk.rect("head", "front", 6, 12, 9, 12, (240, 236, 220, 255))
    else:
        sk.rect("head", "front", 4, 12, 11, 15, ink + (255,))
        sk.rect("head", "front", 5, 12, 10, 12, (242, 236, 220, 255)); sk.rect("head", "front", 5, 15, 10, 15, (242, 236, 220, 255))
        sk.rect("head", "front", 5, 13, 5, 13, (242, 236, 220, 255)); sk.rect("head", "front", 10, 13, 10, 13, (242, 236, 220, 255))
    sk.line("head", "front", [(3, 15), (12, 15)], sh)
    for side in ("left", "right"):
        sk.line("head", side, [(2, 10), (7, 14), (14, 14)], sh)

def trim_band(sk, part, side, y, col, accent):
    """A woven trim band: base row, a diamond pattern, darker lower row."""
    _, _, fw, _ = Skin.face(PARTS[part][0], PARTS[part][1], side)
    hi, base, sh, deep = ramp(col)
    sk.rect(part, side, 0, y, fw - 1, y + 2, base + (255,))
    sk.rect(part, side, 0, y + 2, fw - 1, y + 2, deep + (255,))
    for x in range(1, fw, 4):
        sk.rect(part, side, x, y + 1, x, y + 1, accent + (255,))
        sk.rect(part, side, x + 1, y, x + 1, y, ramp(accent)[0] + (255,))

def medallion_belt(sk, belt=BARK):
    sk.fill("body", SIDES, ramp(belt)[1], rows=(9, 10))
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 18, fw - 1, 18, ramp(belt)[0] + (255,))
        sk.rect("body", side, 0, 19, fw - 1, 19, ramp(belt)[3] + (255,))
    b_hi, b_base, b_sh, b_deep = ramp(BRONZE)
    sk.rect("body", "front", 5, 17, 10, 21, b_deep + (255,))
    sk.rect("body", "front", 6, 18, 9, 20, b_base + (255,))
    sk.rect("body", "front", 6, 18, 9, 18, b_hi + (255,))
    sk.rect("body", "front", 7, 19, 8, 19, ramp(TEAL)[0] + (255,))      # inset stone

def robe_torso(sk, mantle=True, torn=False):
    t_hi, t_base, t_sh, t_deep = ramp(TEAL)
    c_hi, c_base, c_sh, c_deep = ramp(CREAM)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 23, t_base + (255,))
        sk.rect("body", side, 0, 0, 0, 23, t_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, t_deep + (255,))
    sk.fill("body", ("top",), t_base)
    # Cream undershirt in a V between the robe's crossed front panels.
    for y in range(0, 12):
        half = max(0, 5 - y // 2)
        sk.rect("body", "front", 7 - half, y, 8 + half, y, c_base + (255,))
    sk.line("body", "front", [(2, 0), (7, 11)], t_hi); sk.line("body", "front", [(13, 0), (8, 11)], t_deep)
    sk.line("body", "front", [(3, 0), (7, 9)], t_sh)
    # Vertical robe panels below the belt with a woven trim.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for x in range(3, fw, 5):
            sk.line("body", side, [(x, 20), (x, 23)], t_sh)
        trim_band(sk, "body", side, 21, TEAL if not torn else t_deep, BRONZE)
    if mantle:
        # Short cream mantle over the shoulders with a bronze clasp.
        for side in SIDES:
            _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
            sk.rect("body", side, 0, 0, fw - 1, 3, c_base + (255,))
            sk.rect("body", side, 0, 4, fw - 1, 4, c_sh + (255,))
            for x in range(0, fw, 3):
                sk.rect("body", side, x, 4, x, 5, c_base + (255,))
        sk.rect("body", "front", 6, 2, 9, 4, ramp(BRONZE)[2] + (255,)); sk.rect("body", "front", 7, 2, 8, 3, ramp(BRONZE)[0] + (255,))
        for arm in ARMS:
            sk.fill(arm, ("top",), c_base)
            for side in SIDES:
                sk.rect(arm, side, 0, 0, 7, 4, c_base + (255,))
                sk.rect(arm, side, 0, 5, 7, 5, c_sh + (255,))
    medallion_belt(sk)

def wrapped_legs(sk, col=TEAL, skin=None, shredded=False):
    t_hi, t_base, t_sh, t_deep = ramp(col)
    for leg in LEGS:
        sk.fill(leg, ("top",), t_base)
        for side in SIDES:
            top = 0
            bottom = 13 if shredded else 23
            sk.rect(leg, side, 0, top, 7, bottom, t_base + (255,))
            sk.rect(leg, side, 0, top, 0, bottom, t_sh + (255,)); sk.rect(leg, side, 7, top, 7, bottom, t_deep + (255,))
            sk.line(leg, side, [(3, 1), (2, 10)], t_sh)                     # crease
            if shredded:
                for x in range(0, 8, 2):
                    sk.rect(leg, side, x, 14, x, 14 + (x * 3) % 4, t_base + (255,))
            else:
                for y in range(14, 21, 3):                                   # shin wraps
                    sk.rect(leg, side, 0, y, 7, y + 1, ramp(CREAM)[1] + (255,))
                    sk.rect(leg, side, 0, y + 1, 7, y + 1, ramp(CREAM)[2] + (255,))
            sk.rect(leg, side, 0, 22, 7, 23, ramp(BARK)[1] + (255,))         # sandal base
            sk.rect(leg, side, 0, 23, 7, 23, ramp(BARK)[3] + (255,))
        sk.fill(leg, ("bottom",), ramp(BARK)[2])

def bracers(sk, glow=None):
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 15, 7, 21, ramp(BARK)[1] + (255,))
            sk.rect(arm, side, 0, 15, 7, 15, ramp(BARK)[0] + (255,))
            sk.rect(arm, side, 0, 21, 7, 21, ramp(BARK)[3] + (255,))
            sk.rect(arm, side, 2, 17, 5, 18, ramp(BRONZE)[1] + (255,))       # bronze plate
            sk.rect(arm, side, 2, 17, 5, 17, ramp(BRONZE)[0] + (255,))
            if glow:
                glow_line(sk, arm, side, [(0, 15), (7, 15)], glow)

@design("namekian_base", "Namekian: Base", "full")
def _(sk):
    """Forest guardian, calm. Green skin with ridged forearms, a layered deep-teal robe
    over a cream undershirt, short cream mantle with a bronze clasp, medallion belt,
    woven trims, leather-and-bronze bracers, wrapped teal leggings, calm eyes."""
    GREEN = (92, 168, 76)
    nk_skin(sk, GREEN, 430)
    nk_face(sk, GREEN, (40, 40, 40), "calm")
    paint_extras(sk, ANTENNAE + ["ear_r", "ear_l"], GREEN, seed=431)
    robe_torso(sk, mantle=True)
    bracers(sk)
    for arm in ARMS:
        limb_muscles(sk, arm, GREEN)
    wrapped_legs(sk)

@design("namekian_super", "Namekian: Super", "full")
def _(sk):
    """Forest guardian, awakened. The mantle is torn away, the robe's sleeves gone; glowing
    green ki runes are carved down both arms and across the brow; eyes glow green."""
    GREEN, KI = (76, 154, 62), (176, 255, 140)
    nk_skin(sk, GREEN, 440)
    nk_face(sk, GREEN, KI, "fierce")
    paint_extras(sk, ANTENNAE + ["ear_r", "ear_l"], GREEN, seed=441)
    for e in ("antenna_r2", "antenna_l2"):
        sk.fill((EXTRA_UV[e], EXTRA_SIZE[e]), ("top",), KI)
    robe_torso(sk, mantle=False)
    for side in ("front", "back"):                                         # torn shoulder edges
        for x in range(0, 16, 3):
            sk.rect("body", side, x, 0, x + 1, 1, ramp(GREEN)[1] + (255,))
    for arm in ARMS:
        limb_muscles(sk, arm, GREEN)
        for side in ("front", "back", "left", "right"):                    # ki runes down the arm
            glow_line(sk, arm, side, [(3, 1), (3, 4)], KI)
            glow_line(sk, arm, side, [(2, 6), (4, 6)], KI)
            glow_line(sk, arm, side, [(3, 8), (3, 11)], KI)
    glow_line(sk, "head", "front", [(6, 2), (7, 3), (8, 3), (9, 2)], KI)   # brow rune
    bracers(sk, glow=KI)
    wrapped_legs(sk)

@design("namekian_orange", "Namekian: Orange", "full")
def _(sk):
    """Forest guardian, unleashed. Bright orange skin with heavy, deeply cut muscle and a
    heat glow, stripped to the lower robe only (shredded at the knee), bronze arm bands,
    blazing amber eyes and a roar."""
    ORANGE, FIRE = (240, 130, 36), (255, 214, 110)
    o_hi, o_base, o_sh, o_deep = ramp(ORANGE)
    nk_skin(sk, ORANGE, 450)
    muscles(sk, ORANGE)
    for y in (8, 12, 15, 18):                                               # deeper abs
        sk.line("body", "front", [(3, y), (6, y)], o_deep); sk.line("body", "front", [(9, y), (12, y)], o_deep)
    sk.line("body", "front", [(1, 7), (6, 9)], o_deep); sk.line("body", "front", [(14, 7), (9, 9)], o_deep)
    sk.line("body", "back", [(7, 2), (7, 18)], o_deep)                      # spine
    sk.line("body", "back", [(2, 4), (6, 8)], o_sh); sk.line("body", "back", [(13, 4), (9, 8)], o_sh)
    nk_face(sk, ORANGE, FIRE, "rage")
    paint_extras(sk, ANTENNAE + ["ear_r", "ear_l"], ORANGE, seed=451)
    for arm in ARMS:
        limb_muscles(sk, arm, ORANGE)
        for side in SIDES:
            sk.line(arm, side, [(1, 2), (3, 7), (1, 12)], o_deep)
            sk.rect(arm, side, 0, 3, 7, 5, ramp(BRONZE)[1] + (255,))         # bronze arm band
            sk.rect(arm, side, 0, 3, 7, 3, ramp(BRONZE)[0] + (255,))
            sk.rect(arm, side, 0, 5, 7, 5, ramp(BRONZE)[3] + (255,))
            sk.line(arm, side, [(1, 14), (6, 14)], FIRE + (120,))            # heat glow on forearms
    medallion_belt(sk)
    for side in SIDES:                                                       # robe skirt below the belt
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 20, fw - 1, 23, ramp(TEAL)[1] + (255,))
        for x in range(0, fw, 3):
            sk.rect("body", side, x, 23, x, 23, ramp(ORANGE)[1] + (255,))   # ragged edge
    wrapped_legs(sk, shredded=True)

# ---- v1.42e: Majin line - "trickster" (original design) -------------------------------------
PINK, MINT, CHAR, GOLDB, RED_SHOE = (238, 146, 182), (120, 214, 180), (52, 50, 60), (240, 196, 80), (214, 44, 52)

def mj_face(sk, col, mood):
    """mood: grin (one eye squinting) / sneer / wild"""
    hi, base, sh, deep = ramp(col)
    ink = tuple(int(v * 0.28) for v in col)
    sk.rect("head", "front", 2, 6, 13, 6, sh + (255,))
    if mood == "grin":
        # Left eye wide, right eye squinting in a wink-like smirk.
        sk.rect("head", "front", 3, 8, 5, 9, (252, 252, 248, 255)); sk.rect("head", "front", 4, 8, 5, 9, (30, 20, 30, 255))
        sk.rect("head", "front", 4, 8, 4, 8, (255, 255, 255, 255)); sk.rect("head", "front", 3, 7, 5, 7, ink + (255,))
        sk.line("head", "front", [(10, 9), (12, 8)], ink); sk.line("head", "front", [(10, 8), (12, 8)], sh)
        sk.line("head", "front", [(2, 6), (6, 5)], ink); sk.line("head", "front", [(9, 6), (13, 6)], ink)
        sk.line("head", "front", [(4, 12), (7, 13), (11, 12), (12, 11)], ink)          # lopsided grin
        sk.rect("head", "front", 6, 13, 9, 13, (252, 250, 245, 255))
    elif mood == "sneer":
        for x0 in (3, 10):
            sk.rect("head", "front", x0 - 1, 7, x0 + 3, 10, deep + (255,))
            sk.rect("head", "front", x0, 8, x0 + 2, 9, (40, 4, 10, 255))
            sk.rect("head", "front", x0 + (1 if x0 == 3 else 0), 8, x0 + (2 if x0 == 3 else 1), 9, (255, 50, 60, 255))
        sk.line("head", "front", [(1, 5), (6, 7)], ink); sk.line("head", "front", [(14, 5), (9, 7)], ink)
        sk.line("head", "front", [(4, 13), (11, 12)], ink); sk.rect("head", "front", 9, 12, 10, 12, (250, 248, 240, 255))
    else:  # wild
        for x0 in (3, 10):
            sk.rect("head", "front", x0, 7, x0 + 2, 10, (252, 252, 240, 255))
            sk.rect("head", "front", x0 + 1, 8, x0 + 1, 9, (10, 10, 10, 255))         # pinprick pupils
        sk.line("head", "front", [(1, 4), (6, 6)], ink); sk.line("head", "front", [(14, 4), (9, 6)], ink)
        sk.rect("head", "front", 3, 11, 12, 15, (60, 10, 20, 255))                   # huge open grin
        for x in range(3, 13, 2):
            sk.rect("head", "front", x, 11, x, 12, (252, 250, 240, 255)); sk.rect("head", "front", x + 1, 14, x + 1, 15, (252, 250, 240, 255))
    sk.rect("head", "front", 7, 10, 8, 10, sh + (255,))
    for side in ("left", "right"):
        sk.line("head", side, [(2, 10), (7, 14), (14, 14)], sh)

def stitch(sk, part, side, x0, y0, x1, y1, col):
    """Dashed stitching line (horizontal or vertical)."""
    if y0 == y1:
        for x in range(x0, x1 + 1, 2):
            sk.rect(part, side, x, y0, x, y0, col + (255,))
    else:
        for y in range(y0, y1 + 1, 2):
            sk.rect(part, side, x0, y, x0, y, col + (255,))

@design("majin_base", "Majin: Base", "full")
def _(sk):
    """Trickster, base (detailed): pink skin with blush and knuckles, ringed medium tendril,
    winking grin; paneled mint jacket with stitched hems, chest pocket, shaded gold buttons,
    rolled gold cuffs and an embroidered star-diamond emblem on the back; pinstriped
    charcoal shirt; fringed checkered sash; plum trousers with seams, stitched knee patches
    and rolled hems; red high-tops with toe caps, criss-cross laces and treaded soles."""
    PLUM = (92, 70, 116)
    p_hi, p_base, p_sh, p_deep = ramp(PINK)
    m_hi, m_base, m_sh, m_deep = ramp(MINT)
    c_hi, c_base, c_sh, c_deep = ramp(CHAR)
    g_hi, g_base, g_sh, g_deep = ramp(GOLDB)
    l_hi, l_base, l_sh, l_deep = ramp(PLUM)
    r_hi, r_base, r_sh, r_deep = ramp(RED_SHOE)
    WHITE_S = (246, 244, 240)
    smooth_skin(sk, PINK, 510)

    # ---- Head: mean (v1.42f) - slanted brows, narrowed glowing eyes, fanged sneer ------
    ink = (54, 10, 28)
    EYE, EYE_DK = (236, 40, 90), (120, 10, 40)
    sk.line("head", "front", [(2, 4), (6, 6)], ink); sk.line("head", "front", [(2, 5), (6, 7)], ink)    # brows slanting
    sk.line("head", "front", [(13, 4), (9, 6)], ink); sk.line("head", "front", [(13, 5), (9, 7)], ink)  # down to the nose
    sk.rect("head", "front", 7, 5, 8, 6, p_deep + (255,))                              # scowl crease
    for x0 in (3, 10):
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 9, p_deep + (255,))                # dark sockets
        sk.rect("head", "front", x0, 8, x0 + 2, 8, EYE + (255,))                       # narrowed slit
        sk.rect("head", "front", x0 + (1 if x0 == 3 else 0), 8, x0 + (2 if x0 == 3 else 1), 8, EYE_DK + (255,))
        sk.rect("head", "front", x0 + (1 if x0 == 3 else 1), 8, x0 + (1 if x0 == 3 else 1), 8, (20, 0, 8, 255))  # pupil
        sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, EYE + (70,))                  # glow under the eyes
    sk.line("head", "front", [(1, 11), (4, 12)], p_deep); sk.line("head", "front", [(14, 11), (11, 12)], p_deep)  # cheekbones
    sk.rect("head", "front", 7, 10, 7, 10, p_deep + (255,)); sk.rect("head", "front", 9, 10, 9, 10, p_deep + (255,))
    # lopsided sneer pulled up on the right
    sk.line("head", "front", [(4, 13), (8, 13), (11, 12), (12, 11)], ink)
    sk.rect("head", "front", 9, 12, 11, 12, (40, 6, 18, 255))                         # closed sneer, no teeth
    sk.line("head", "front", [(5, 15), (10, 15)], p_sh)
    for side in ("left", "right"):
        sk.line("head", side, [(2, 10), (7, 14), (14, 14)], p_sh)
        sk.rect("head", side, 9, 7, 10, 9, p_sh + (255,))
    # Tendril: ring bands and a shine stripe on every segment.
    for e in tendril_extras(TENDRIL_SIZES["m"]):
        _, _, uv, size, *_ = e
        sk.fill((uv, size), ALL, PINK)
        for side in SIDES:
            x, y, fw, fh = Skin.face(uv, size, side)
            for yy in range(1, fh, 3):
                sk.d.line((x, y + yy, x + fw - 1, y + yy), fill=p_sh + (255,))
            sk.d.line((x + 1, y, x + 1, y + fh - 1), fill=p_hi + (255,))

    # ---- Torso ---------------------------------------------------------------------
    # Pinstriped charcoal shirt.
    sk.fill("body", SIDES + ("top",), c_base)
    for x in range(1, 16, 3):
        sk.line("body", "front", [(x, 0), (x, 17)], c_sh)
    sk.rect("body", "front", 6, 0, 9, 1, c_hi + (255,))                               # collar
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        if side == "front":
            for (x0, x1) in ((0, 4), (11, 15)):
                sk.rect("body", side, x0, 0, x1, 16, m_base + (255,))
            sk.rect("body", side, 0, 0, 0, 16, m_sh + (255,)); sk.rect("body", side, 15, 0, 15, 16, m_deep + (255,))
            sk.line("body", side, [(4, 0), (4, 16)], m_deep); sk.line("body", side, [(11, 0), (11, 16)], m_deep)
            sk.line("body", side, [(5, 0), (5, 16)], c_deep)
            # lapels: dark mint with a highlight edge
            for i in range(6):
                sk.rect("body", side, 2 + i // 2, i, 4, i, m_deep + (255,)); sk.rect("body", side, 11, i, 13 - i // 2, i, m_deep + (255,))
            sk.line("body", side, [(2, 0), (4, 5)], m_hi); sk.line("body", side, [(13, 0), (11, 5)], m_hi)
            # chest pocket with flap on the right panel
            sk.rect("body", side, 12, 8, 14, 11, m_sh + (255,)); sk.rect("body", side, 12, 8, 14, 8, m_deep + (255,))
            sk.rect("body", side, 12, 9, 14, 9, m_hi + (255,))
            # shaded gold buttons
            for y in (7, 10, 13):
                sk.rect("body", side, 2, y, 3, y + 1, g_sh + (255,)); sk.rect("body", side, 2, y, 2, y, g_hi + (255,))
            stitch(sk, "body", side, 1, 1, 1, 15, m_sh)
            stitch(sk, "body", side, 14, 1, 14, 7, m_sh)
        else:
            sk.rect("body", side, 0, 0, fw - 1, 16, m_base + (255,))
            sk.rect("body", side, 0, 0, fw - 1, 0, m_hi + (255,))
            sk.rect("body", side, 0, 0, 0, 16, m_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 16, m_deep + (255,))
            if side == "back":
                sk.line("body", side, [(7, 1), (7, 16)], m_sh)                        # back seam
                # embroidered star-diamond emblem
                for (x, y) in ((7, 4), (6, 5), (8, 5), (5, 6), (9, 6), (6, 7), (8, 7), (7, 8)):
                    sk.rect("body", side, x, y, x, y, g_base + (255,))
                sk.rect("body", side, 7, 6, 7, 6, g_hi + (255,))
                for (x, y) in ((7, 3), (4, 6), (10, 6), (7, 9)):
                    sk.rect("body", side, x, y, x, y, g_sh + (255,))
                sk.line("body", side, [(3, 12), (5, 10)], m_sh); sk.line("body", side, [(12, 12), (10, 10)], m_sh)
        sk.rect("body", side, 0, 16, fw - 1, 16, m_deep + (255,))
        stitch(sk, "body", side, 0, 15, fw - 1, 15, m_hi)
    # Fringed checkered sash.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for x in range(0, fw, 2):
            for y in (17, 18, 19):
                c = WHITE_S if (x // 2 + y) % 2 else (34, 30, 40)
                sk.rect("body", side, x, y, x + 1, y, c + (255,))
        sk.rect("body", side, 0, 20, fw - 1, 23, l_base + (255,))
        sk.line("body", side, [(0, 20), (fw - 1, 20)], l_deep)
    for x in (12, 13, 14):                                                              # fringe ends
        sk.rect("body", "front", x, 20, x, 22 + (x % 2), WHITE_S + (255,))

    # ---- Arms ----------------------------------------------------------------------------
    for arm in ARMS:
        sk.fill(arm, ("top",), m_base)
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 10, m_base + (255,))
            sk.rect(arm, side, 0, 0, 7, 0, m_hi + (255,))
            sk.rect(arm, side, 0, 0, 0, 10, m_sh + (255,)); sk.rect(arm, side, 7, 0, 7, 10, m_deep + (255,))
            sk.line(arm, side, [(2, 6), (5, 7)], m_sh); sk.line(arm, side, [(2, 8), (5, 8)], m_deep)   # elbow creases
            sk.rect(arm, side, 0, 10, 7, 12, g_base + (255,))                           # rolled gold cuff
            sk.rect(arm, side, 0, 10, 7, 10, g_hi + (255,)); sk.rect(arm, side, 0, 12, 7, 12, g_deep + (255,))
            sk.line(arm, side, [(1, 15), (2, 21)], p_sh)
            sk.line(arm, side, [(5, 14), (6, 19)], p_hi)
        # hands: knuckle dots on the bottom face
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        for kx in range(1, fw, 2):
            sk.d.point((x + kx, y + 1), fill=p_deep + (255,))

    # ---- Legs ---------------------------------------------------------------------------
    for leg in LEGS:
        sk.fill(leg, ("top",), l_base)
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 16, l_base + (255,))
            sk.rect(leg, side, 0, 0, 0, 16, l_sh + (255,)); sk.rect(leg, side, 7, 0, 7, 16, l_deep + (255,))
            stitch(sk, "body" if False else leg, side, 4, 0, 4, 15, l_sh)                # side seam
            sk.rect(leg, side, 0, 15, 7, 16, l_hi + (255,)); sk.rect(leg, side, 0, 16, 7, 16, l_sh + (255,))  # rolled hem
        # stitched knee patches
        for side, pc in (("front", MINT), ("back", GOLDB)):
            sk.rect(leg, side, 1, 6, 5, 10, ramp(pc)[1] + (255,))
            sk.rect(leg, side, 1, 6, 5, 6, ramp(pc)[0] + (255,)); sk.rect(leg, side, 1, 10, 5, 10, ramp(pc)[2] + (255,))
            for (xx, yy) in ((0, 6), (0, 8), (0, 10), (6, 6), (6, 8), (6, 10), (2, 5), (4, 5), (2, 11), (4, 11)):
                sk.rect(leg, side, xx, yy, xx, yy, WHITE_S + (255,))
        # high-tops
        for side in SIDES:
            sk.rect(leg, side, 0, 17, 7, 23, r_base + (255,))
            sk.rect(leg, side, 0, 17, 7, 17, WHITE_S + (255,))                          # padded collar
            sk.rect(leg, side, 0, 18, 7, 18, r_hi + (255,))
            sk.rect(leg, side, 0, 21, 7, 22, WHITE_S + (255,))                          # sole
            sk.rect(leg, side, 0, 23, 7, 23, (150, 146, 144, 255))
            for x in range(0, 8, 2):
                sk.rect(leg, side, x, 23, x, 23, (96, 92, 92, 255))                     # treads
        sk.rect(leg, "front", 1, 19, 6, 20, WHITE_S + (255,))                           # toe cap
        for (xx, yy) in ((2, 18), (5, 18), (3, 19), (4, 19)):
            sk.rect(leg, "front", xx, yy, xx, yy, (60, 20, 24, 255))                    # criss-cross laces
        for side in ("left", "right"):
            sk.line(leg, side, [(1, 20), (6, 18)], r_deep)                              # side panel
            sk.rect(leg, side, 3, 19, 4, 19, WHITE_S + (255,))                          # star mark
        x, y, fw, fh = Skin.face(PARTS[leg][0], PARTS[leg][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=(120, 116, 114, 255))
        for ty in range(y, y + fh, 2):
            sk.d.line((x, ty, x + fw - 1, ty), fill=(90, 86, 86, 255))

@design("majin_super", "Majin: Super", "full")
def _(sk):
    """Trickster turned brutal: deeper rose skin with heavy muscle, large ringed tendril,
    glowing red eyes and a snarl; a long battle-torn coat (dark mint and charcoal, gold
    trim) open over a bare chest, hanging past the knees and shredded at the hem;
    gold-studded gauntlets, heavy charcoal boots."""
    ROSE = (222, 118, 160)
    COAT, COAT2 = (40, 112, 96), (44, 42, 52)
    r_hi, r_base, r_sh, r_deep = ramp(ROSE)
    k_hi, k_base, k_sh, k_deep = ramp(COAT)
    c_hi, c_base, c_sh, c_deep = ramp(COAT2)
    g_hi, g_base, g_sh, g_deep = ramp(GOLDB)
    smooth_skin(sk, ROSE, 520)
    muscles(sk, ROSE)
    for y in (8, 12, 15, 18):                                               # heavy abs
        sk.line("body", "front", [(4, y), (6, y)], r_deep); sk.line("body", "front", [(9, y), (11, y)], r_deep)
    sk.line("body", "front", [(2, 7), (6, 9)], r_deep); sk.line("body", "front", [(13, 7), (9, 9)], r_deep)
    sk.line("body", "front", [(3, 5), (6, 5)], r_hi); sk.line("body", "front", [(9, 5), (12, 5)], r_hi)
    # ---- Face: deeper scowl, glowing red eyes, snarl --------------------------------
    ink = (46, 6, 22)
    RED = (255, 40, 50)
    for y in (4, 5):
        sk.line("head", "front", [(1, y - 1), (6, y + 2)], ink); sk.line("head", "front", [(14, y - 1), (9, y + 2)], ink)
    sk.rect("head", "front", 7, 4, 8, 6, r_deep + (255,))
    for x0 in (3, 10):
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 9, (60, 10, 26, 255))
        sk.rect("head", "front", x0, 8, x0 + 2, 8, RED + (255,))
        sk.rect("head", "front", x0 + 1, 8, x0 + 1, 8, (255, 210, 210, 255))
        sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, RED + (90,))
    sk.line("head", "front", [(1, 11), (4, 12)], r_deep); sk.line("head", "front", [(14, 11), (11, 12)], r_deep)
    sk.rect("head", "front", 7, 10, 7, 10, r_deep + (255,)); sk.rect("head", "front", 9, 10, 9, 10, r_deep + (255,))
    sk.rect("head", "front", 4, 12, 11, 13, (40, 6, 18, 255))                  # snarl (closed teeth line)
    sk.line("head", "front", [(4, 12), (11, 12)], (60, 14, 28))
    sk.line("head", "front", [(3, 11), (4, 12)], ink); sk.line("head", "front", [(12, 11), (11, 12)], ink)
    sk.line("head", "front", [(5, 15), (10, 15)], r_sh)
    for side in ("left", "right"):
        sk.line("head", side, [(2, 10), (7, 14), (14, 14)], r_sh)
    # Large tendril with ring bands and a shine stripe.
    for e in tendril_extras(TENDRIL_SIZES["l"]):
        _, _, uv, size, *_ = e
        sk.fill((uv, size), ALL, ROSE)
        for side in SIDES:
            x, y, fw, fh = Skin.face(uv, size, side)
            for yy in range(1, fh, 3):
                sk.d.line((x, y + yy, x + fw - 1, y + yy), fill=r_sh + (255,))
            sk.d.line((x + 1, y, x + 1, y + fh - 1), fill=r_hi + (255,))
    # ---- Long coat: open over the bare chest, two-tone, gold trim, torn -----------------
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        if side == "front":
            for (x0, x1) in ((0, 3), (12, 15)):
                sk.rect("body", side, x0, 0, x1, 23, k_base + (255,))
            sk.line("body", side, [(3, 0), (3, 23)], g_base); sk.line("body", side, [(12, 0), (12, 23)], g_base)
            sk.line("body", side, [(0, 0), (0, 23)], k_sh); sk.line("body", side, [(15, 0), (15, 23)], k_deep)
            for y in (3, 9, 15):                                              # gold studs
                sk.rect("body", side, 1, y, 1, y, g_hi + (255,)); sk.rect("body", side, 14, y, 14, y, g_hi + (255,))
        else:
            sk.rect("body", side, 0, 0, fw - 1, 23, k_base + (255,))
            sk.rect("body", side, 0, 0, fw - 1, 0, k_hi + (255,))
            sk.rect("body", side, 0, 0, 0, 23, k_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, k_deep + (255,))
            folds(sk, "body", (side,), COAT, 521, n=2)
            if side == "back":
                sk.rect("body", side, 0, 0, fw - 1, 4, c_base + (255,))       # charcoal yoke
                sk.rect("body", side, 0, 4, fw - 1, 4, g_base + (255,))
                sk.line("body", side, [(7, 5), (7, 23)], k_sh)
                for (x, y) in ((7, 8), (6, 9), (8, 9), (5, 10), (9, 10), (6, 11), (8, 11), (7, 12)):
                    sk.rect("body", side, x, y, x, y, g_base + (255,))        # emblem carried over, larger
                sk.rect("body", side, 7, 10, 7, 10, (255, 60, 70, 255))       # now with a red core
                for x in range(1, fw, 4):                                       # slash damage
                    sk.line("body", side, [(x, 15), (x + 2, 18)], k_deep)
        sk.rect("body", side, 0, 17, fw - 1, 18, c_base + (255,))             # charcoal belt
        sk.rect("body", side, 0, 17, fw - 1, 17, c_hi + (255,))
    sk.rect("body", "front", 4, 19, 11, 23, c_base + (255,))                  # trouser top below the belt
    sk.line("body", "front", [(7, 19), (7, 23)], c_deep)
    sk.rect("body", "front", 6, 17, 9, 18, g_base + (255,)); sk.rect("body", "front", 7, 17, 8, 17, g_hi + (255,))
    # Arms: coat sleeves to the elbow with gold trim, bare forearms, studded gauntlets.
    for arm in ARMS:
        sk.fill(arm, ("top",), c_base)
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 3, c_base + (255,))                    # charcoal shoulder
            sk.rect(arm, side, 0, 3, 7, 3, g_base + (255,))
            sk.rect(arm, side, 0, 4, 7, 9, k_base + (255,))
            sk.rect(arm, side, 0, 9, 7, 9, g_sh + (255,))
            sk.line(arm, side, [(1, 10), (2, 13)], r_deep); sk.line(arm, side, [(5, 10), (6, 12)], r_hi)
            sk.rect(arm, side, 0, 14, 7, 21, c_base + (255,))                  # gauntlet
            sk.rect(arm, side, 0, 14, 7, 14, c_hi + (255,)); sk.rect(arm, side, 0, 21, 7, 21, c_deep + (255,))
            for x in (1, 4, 6):
                sk.rect(arm, side, x, 17, x, 17, g_hi + (255,))
                sk.rect(arm, side, x, 19, x, 19, g_sh + (255,))
    # Legs: coat tails to the knee (torn), charcoal trousers, heavy boots.
    for leg in LEGS:
        sk.fill(leg, ("top",), c_base)
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 23, c_base + (255,))
            sk.rect(leg, side, 0, 0, 0, 23, c_sh + (255,)); sk.rect(leg, side, 7, 0, 7, 23, c_deep + (255,))
            if side != "front":
                sk.rect(leg, side, 0, 0, 7, 9, k_base + (255,))                 # coat tail
                for x in range(0, 8, 2):
                    sk.rect(leg, side, x, 10, x, 10 + (x * 5) % 3, k_base + (255,))   # shredded hem
            sk.rect(leg, side, 0, 15, 7, 23, c_deep + (255,))                   # boots
            sk.rect(leg, side, 0, 15, 7, 15, c_sh + (255,))
            sk.rect(leg, side, 0, 18, 7, 18, g_base + (255,))                   # buckle strap
            sk.rect(leg, side, 3, 18, 4, 18, g_hi + (255,))
            sk.rect(leg, side, 0, 23, 7, 23, (20, 18, 24, 255))
        sk.fill(leg, ("bottom",), (20, 18, 24))

def mark(sk, part, side, pts, col=(255, 224, 70), edge=(214, 110, 20)):
    """Crisp tribal mark: a 1px bright line with a thin darker edge below it (no blur)."""
    sk.line(part, side, [(x, y + 1) for x, y in pts], edge)
    sk.line(part, side, pts, col)

def round_shade(sk, parts, col):
    """Cylindrical shading: brighter centre column, darker outer columns on each side face."""
    hi, base, sh, deep = ramp(col)
    px = sk.im.load()
    for p in parts:
        for side in SIDES:
            x, y, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for i in range(fw):
                t = abs((i + 0.5) / fw - 0.5) * 2          # 0 centre .. 1 edge
                k = 1.08 - 0.2 * t * t
                for j in range(fh):
                    c = px[x + i, y + j]
                    if c[3] == 0:
                        continue
                    px[x + i, y + j] = tuple(max(0, min(255, int(v * k))) for v in c[:3]) + (c[3],)

def contact_shadow(sk, part, side, y, col):
    """Soft shadow on the skin just below a clothing edge."""
    _, _, fw, _ = Skin.face(PARTS[part][0], PARTS[part][1], side)
    sk.rect(part, side, 0, y, fw - 1, y, ramp(col)[2] + (255,))

@design("majin_kid", "Majin: Kid", "full")
def _(sk):
    """Kid Majin (v2): wiry kid build (ribs, bony shoulders, knobby knees) in hot magenta,
    crisp symmetric yellow tribal marks, small ringed tendril, big crazed eyes with pinprick
    pupils and a wide grin with a few big jagged teeth; layered crimson waist wraps with a
    side knot and tails, a torn scarf, clean bandages with pins, bare clawed feet."""
    MAG = (222, 82, 166)
    WRAP = (164, 30, 46)
    BAND = (232, 222, 200)
    m_hi, m_base, m_sh, m_deep = ramp(MAG)
    w_hi, w_base, w_sh, w_deep = ramp(WRAP)
    b_hi, b_base, b_sh, b_deep = ramp(BAND)
    smooth_skin(sk, MAG, 540)
    # ---- Wiry body: ribs, collarbones, bony shoulders, knobby knees ----------------------
    sk.line("body", "front", [(2, 1), (6, 2)], m_sh); sk.line("body", "front", [(13, 1), (9, 2)], m_sh)   # collarbones
    sk.line("body", "front", [(2, 0), (6, 1)], m_hi); sk.line("body", "front", [(13, 0), (9, 1)], m_hi)
    for y in (6, 8, 10, 12):                                                   # ribs
        sk.line("body", "front", [(2, y), (5, y + 1)], m_sh); sk.line("body", "front", [(13, y), (10, y + 1)], m_sh)
    sk.line("body", "front", [(7, 4), (7, 14)], m_sh)
    sk.rect("body", "front", 7, 14, 8, 14, m_deep + (255,))                    # navel
    for y in (4, 8, 12):
        sk.line("body", "back", [(7, y), (8, y)], m_sh)                        # spine bumps
    sk.line("body", "back", [(2, 3), (5, 6)], m_sh); sk.line("body", "back", [(13, 3), (10, 6)], m_sh)   # shoulder blades
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 1, m_hi + (255,))                      # bony shoulder highlight
            sk.line(arm, side, [(3, 9), (4, 10)], m_sh)                        # elbow
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        for kx in range(1, fw, 2):
            sk.d.point((x + kx, y + 1), fill=m_deep + (255,))                  # knuckles
    for leg in LEGS:
        for side in ("front",):
            sk.rect(leg, side, 2, 12, 5, 13, m_hi + (255,)); sk.rect(leg, side, 2, 14, 5, 14, m_sh + (255,))  # knobby knee
    # ---- Crisp symmetric tribal marks ------------------------------------------------------
    mark(sk, "body", "front", [(3, 4), (5, 6), (7, 4)]); mark(sk, "body", "front", [(8, 4), (10, 6), (12, 4)])
    mark(sk, "body", "front", [(5, 10), (7, 12), (8, 12), (10, 10)])
    mark(sk, "body", "back", [(7, 1), (7, 13)])
    mark(sk, "body", "back", [(2, 9), (5, 11)]); mark(sk, "body", "back", [(13, 9), (10, 11)])
    for arm in ARMS:
        for side in ("front", "back"):
            mark(sk, arm, side, [(1, 3), (3, 5), (5, 3)])
            mark(sk, arm, side, [(1, 7), (6, 7)])
    for leg in LEGS:
        for side in ("front", "back"):
            mark(sk, leg, side, [(1, 17), (3, 19), (5, 17)])
    # ---- Face (v2.3): mean, matching the Super Majin's scowl, with yellow slit eyes ------
    ink = (46, 4, 26)
    EYE = (255, 222, 60)
    for y in (4, 5):                                                          # heavy slanted brows
        sk.line("head", "front", [(1, y - 1), (6, y + 2)], ink); sk.line("head", "front", [(14, y - 1), (9, y + 2)], ink)
    sk.rect("head", "front", 7, 4, 8, 6, m_deep + (255,))                     # scowl crease
    for x0 in (3, 10):
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 9, (56, 8, 30, 255))      # dark sockets
        sk.rect("head", "front", x0, 8, x0 + 2, 8, EYE + (255,))              # narrowed glowing slit
        sk.rect("head", "front", x0 + 1, 8, x0 + 1, 8, (30, 4, 14, 255))      # slit pupil
        sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, EYE + (80,))         # glow underneath
    mark(sk, "head", "front", [(6, 1), (7, 2), (8, 2), (9, 1)])               # forehead mark
    sk.line("head", "front", [(1, 11), (4, 12)], m_deep); sk.line("head", "front", [(14, 11), (11, 12)], m_deep)  # sunken cheeks
    sk.rect("head", "front", 7, 10, 7, 10, m_deep + (255,)); sk.rect("head", "front", 9, 10, 9, 10, m_deep + (255,))
    # tight snarl: clenched teeth showing between drawn-back lips
    sk.rect("head", "front", 4, 12, 11, 13, (44, 4, 20, 255))
    sk.rect("head", "front", 5, 12, 10, 13, (244, 240, 230, 255))
    for x in (6, 8, 10):
        sk.rect("head", "front", x, 12, x, 13, (176, 166, 160, 255))          # tooth gaps
    sk.line("head", "front", [(5, 12), (10, 12)], (214, 206, 196))
    sk.line("head", "front", [(3, 11), (4, 12)], ink); sk.line("head", "front", [(12, 11), (11, 12)], ink)   # drawn-back corners
    sk.line("head", "front", [(5, 15), (10, 15)], m_sh)
    for side in ("left", "right"):
        sk.line("head", side, [(2, 10), (7, 14), (14, 14)], m_sh)
        mark(sk, "head", side, [(4, 3), (6, 5), (4, 7)])
    # ---- Small tendril with rings -----------------------------------------------------------
    for n in TENDRIL:
        uv, size = EXTRA_UV[n], EXTRA_SIZE[n]
        sk.fill((uv, size), ALL, MAG)
        for side in SIDES:
            x, y, fw, fh = Skin.face(uv, size, side)
            for yy in range(1, fh, 2):
                sk.d.line((x, y + yy, x + fw - 1, y + yy), fill=m_sh + (255,))
            sk.d.line((x + 1, y, x + 1, y + fh - 1), fill=m_hi + (255,))
    # ---- Torn scarf ---------------------------------------------------------------------------
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 1, w_base + (255,)); sk.rect("body", side, 0, 0, fw - 1, 0, w_hi + (255,))
        sk.rect("body", side, 0, 2, fw - 1, 2, w_deep + (255,))
        for x in range(1, fw, 3):
            sk.rect("body", side, x, 3, x, 3, w_base + (255,))
    sk.rect("body", "back", 10, 2, 12, 8, w_base + (255,)); sk.line("body", "back", [(11, 3), (11, 7)], w_sh)
    sk.rect("body", "back", 10, 9, 10, 9, w_base + (255,)); sk.rect("body", "back", 12, 9, 12, 10, w_base + (255,))
    # ---- Layered waist wraps with a side knot and tails ------------------------------------------
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 16, fw - 1, 23, w_base + (255,))
        for y in (16, 19, 22):
            sk.line("body", side, [(0, y), (fw - 1, y + 1)], w_hi)
            sk.line("body", side, [(0, y + 2), (fw - 1, y + 3)], w_sh)
    sk.rect("body", "front", 11, 17, 13, 19, w_deep + (255,)); sk.rect("body", "front", 12, 18, 12, 18, w_hi + (255,))  # knot
    for leg in LEGS:
        sk.fill(leg, ("top",), w_base)
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 7, w_base + (255,))
            sk.line(leg, side, [(0, 2), (7, 3)], w_hi); sk.line(leg, side, [(0, 4), (7, 5)], w_sh)
            for x in range(0, 8, 2):
                sk.rect(leg, side, x, 8, x, 8 + (x * 3) % 3, w_base + (255,))   # frayed hem
                sk.rect(leg, side, x + 1, 8, x + 1, 8, w_deep + (255,))
    sk.rect("rightLeg", "front", 6, 8, 7, 13, w_base + (255,)); sk.line("rightLeg", "front", [(6, 9), (6, 12)], w_sh)   # knot tails
    # ---- Clean bandages with safety pins -------------------------------------------------------------
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 15, 7, 21, b_base + (255,))
            for y in (16, 18, 20):
                sk.line(arm, side, [(0, y), (7, y)], b_sh)
            sk.rect(arm, side, 0, 15, 7, 15, b_hi + (255,))
        sk.rect(arm, "front", 5, 17, 6, 17, (200, 204, 214, 255))              # safety pin
        sk.rect(arm, "front", 6, 21, 6, 23, b_base + (255,))                    # loose end
    for leg in LEGS:
        for side in SIDES:
            sk.rect(leg, side, 0, 17, 7, 20, b_base + (255,))
            sk.line(leg, side, [(0, 18), (7, 18)], b_sh); sk.line(leg, side, [(0, 20), (7, 20)], b_sh)
            sk.rect(leg, side, 0, 22, 7, 23, m_sh + (255,))
        for x in (1, 3, 5):
            sk.rect(leg, "front", x, 22, x, 23, (252, 246, 236, 255))           # claws
            sk.rect(leg, "front", x + 1, 21, x + 1, 23, m_deep + (255,))        # toe gaps
        sk.fill(leg, ("bottom",), m_deep)
    # ---- v2.1 detail pass -------------------------------------------------------------------
    GOLDK = (236, 186, 64)
    for side in SIDES:                                                          # woven band on the wrap
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 21, fw - 1, 21, w_deep + (255,))
        for x in range(0, fw, 3):
            sk.rect("body", side, x, 21, x + 1, 21, ramp(GOLDK)[1] + (255,))
        contact_shadow(sk, "body", side, 3, MAG)                                # under the scarf
        contact_shadow(sk, "body", side, 15, MAG)                               # above the wraps
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 22, 7, 23, ramp(GOLDK)[1] + (255,))           # wrist cuff
            sk.rect(arm, side, 0, 22, 7, 22, ramp(GOLDK)[0] + (255,))
            contact_shadow(sk, arm, side, 14, MAG)
    for leg in LEGS:
        for side in SIDES:
            contact_shadow(sk, leg, side, 9, MAG)
            contact_shadow(sk, leg, side, 21, MAG)
    for (part, side, x, y) in (("body", "front", 4, 7), ("body", "front", 11, 7), ("body", "back", 7, 15),
                               ("leftArm", "front", 3, 9), ("rightArm", "front", 3, 9)):
        sk.rect(part, side, x, y, x, y, (255, 230, 90, 255))                    # dot accents on the marks
    round_shade(sk, list(ARMS) + list(LEGS) + ["body"], MAG)

# ---- v1.42g: Human line - "disciplined fighter" (original design) ----------------------------
SKIN_H, GI, GI_TRIM, SASH, PANTS, WRAP_H, HAIR_H, BAND_H = (232, 188, 150), (88, 98, 112), (236, 234, 228), (150, 28, 36), (34, 34, 40), (226, 216, 196), (54, 36, 26), (240, 238, 232)

def human_base_body(sk, seed, hair=HAIR_H, gi=GI, sash=SASH, skin=SKIN_H):
    s_hi, s_base, s_sh, s_deep = ramp(skin)
    g_hi, g_base, g_sh, g_deep = ramp(gi)
    smooth_skin(sk, skin, seed)
    # Hair: short, swept, with strands and a hairline.
    h_hi, h_base, h_sh, h_deep = ramp(hair)
    sk.fill("head", ("top",), h_base, shade=0.08, seed=seed + 1)
    for side in ("left", "right", "back"):
        sk.rect("head", side, 0, 0, 15, 6 if side != "back" else 10, h_base + (255,))
        for x in range(0, 16, 3):
            sk.line("head", side, [(x, 0), (x + 1, 5 if side != "back" else 9)], h_sh)
            sk.rect("head", side, x + 1, 0, x + 1, 2, h_hi + (255,))
    sk.rect("head", "front", 0, 0, 15, 3, h_base + (255,))
    for x in (1, 4, 7, 10, 13):                                              # fringe spikes
        sk.rect("head", "front", x, 4, x + 1, 4, h_base + (255,)); sk.rect("head", "front", x, 5, x, 5, h_sh + (255,))
    for x in range(0, 16, 2):
        sk.rect("head", "front", x, 1, x, 1, h_hi + (255,))
    for x in range(1, 15, 3):
        sk.line("head", "top", [(x, 0), (x + 1, 15)], h_sh)
    # Gi top: crossed lapels with white trim, sleeves to the elbow, belt/sash.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 23, g_base + (255,))
        sk.rect("body", side, 0, 0, 0, 23, g_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, g_deep + (255,))
        if side != "front":
            folds(sk, "body", (side,), gi, seed + 2, n=2)
    for y in range(0, 10):                                                    # V of skin at the chest
        half = max(0, 4 - y // 2)
        sk.rect("body", "front", 7 - half, y, 8 + half, y, s_base + (255,))
    sk.line("body", "front", [(2, 0), (7, 10)], GI_TRIM); sk.line("body", "front", [(3, 0), (8, 10)], ramp(GI_TRIM)[2])
    sk.line("body", "front", [(13, 0), (8, 10)], GI_TRIM)
    sk.line("body", "front", [(9, 12), (12, 16)], g_sh); sk.line("body", "front", [(4, 13), (6, 16)], g_sh)
    sk.line("body", "front", [(6, 4), (9, 4)], s_sh)                         # chest line
    sk.fill("body", ("top",), g_base)
    sash_r = ramp(sash)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 16, fw - 1, 19, sash_r[1] + (255,))
        sk.rect("body", side, 0, 16, fw - 1, 16, sash_r[0] + (255,)); sk.rect("body", side, 0, 19, fw - 1, 19, sash_r[3] + (255,))
        sk.rect("body", side, 0, 20, fw - 1, 23, ramp(PANTS)[1] + (255,))
    sk.rect("body", "front", 9, 16, 11, 19, sash_r[2] + (255,))              # knot
    sk.line("body", "front", [(10, 20), (9, 23)], sash_r[1]); sk.line("body", "front", [(11, 20), (12, 23)], sash_r[1])
    for arm in ARMS:
        sk.fill(arm, ("top",), g_base)
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 8, g_base + (255,))
            sk.rect(arm, side, 0, 8, 7, 8, GI_TRIM + (255,))
            sk.line(arm, side, [(2, 2), (4, 6)], g_sh)
            sk.line(arm, side, [(1, 10), (2, 14)], s_sh); sk.line(arm, side, [(5, 10), (6, 13)], s_hi)
            for y in (16, 18, 20, 22):                                        # hand wraps
                sk.rect(arm, side, 0, y, 7, y + 1, ramp(WRAP_H)[1] + (255,))
                sk.line(arm, side, [(0, y + 1), (7, y)], ramp(WRAP_H)[2])
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=ramp(WRAP_H)[1] + (255,))
    for leg in LEGS:
        sk.fill(leg, ("top",), ramp(PANTS)[1])
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 23, ramp(PANTS)[1] + (255,))
            sk.rect(leg, side, 0, 0, 0, 23, ramp(PANTS)[2] + (255,)); sk.rect(leg, side, 7, 0, 7, 23, ramp(PANTS)[3] + (255,))
            sk.line(leg, side, [(3, 1), (2, 12)], ramp(PANTS)[0])
            for y in (16, 18, 20):                                            # ankle wraps
                sk.rect(leg, side, 0, y, 7, y + 1, ramp(WRAP_H)[1] + (255,))
                sk.line(leg, side, [(0, y + 1), (7, y)], ramp(WRAP_H)[2])
            sk.rect(leg, side, 0, 22, 7, 23, ramp((60, 44, 34))[1] + (255,))  # flat shoes
        sk.fill(leg, ("bottom",), ramp((60, 44, 34))[2])
    # ---- detail pass (v1.42h) -------------------------------------------------------------
    trim_hi, trim_sh = ramp(GI_TRIM)[0], ramp(GI_TRIM)[2]
    sk.line("body", "front", [(3, 1), (7, 9)], g_deep)                      # inner shadow under the lapel
    for (x, y) in ((3, 2), (4, 4), (5, 6), (12, 2), (11, 4), (10, 6)):
        sk.rect("body", "front", x, y, x, y, trim_sh + (255,))               # lapel stitching
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        if side in ("left", "right"):
            stitch(sk, "body", side, 3, 1, 3, 15, g_sh)                     # side seams
        for x in range(0, fw, 2):                                           # woven sash
            sk.rect("body", side, x, 17 + (x // 2) % 2, x, 17 + (x // 2) % 2, sash_r[2] + (255,))
            sk.rect("body", side, x + 1, 18 - (x // 2) % 2, x + 1, 18 - (x // 2) % 2, sash_r[0] + (255,))
    sk.line("body", "back", [(1, 1), (14, 1)], g_sh)                        # shoulder seam
    # back crest: a simple circle-and-bar emblem
    for (x, y) in ((6, 5), (7, 4), (8, 4), (9, 5), (10, 6), (10, 7), (9, 8), (8, 9), (7, 9), (6, 8), (5, 7), (5, 6)):
        sk.rect("body", "back", x, y, x, y, GI_TRIM + (255,))
    sk.line("body", "back", [(7, 5), (8, 8)], sash_r[1])
    for arm in ARMS:
        for side in SIDES:
            sk.line(arm, side, [(0, 1), (7, 1)], g_sh)                      # shoulder seam
            sk.line(arm, side, [(1, 5), (5, 4)], g_deep)                    # sleeve fold
            for y in (16, 18, 20, 22):
                sk.rect(arm, side, 0, y, 7, y, ramp(WRAP_H)[0] + (255,))    # crisp wrap highlight
    for leg in LEGS:
        for side in SIDES:
            stitch(sk, leg, side, 4, 1, 4, 14, ramp(PANTS)[0])               # side seam stitching
            sk.line(leg, side, [(1, 10), (3, 11), (6, 10)], ramp(PANTS)[3])   # knee crease
            sk.rect(leg, side, 0, 15, 7, 15, ramp(PANTS)[3] + (255,))         # gathered hem
            for y in (16, 18, 20):
                sk.rect(leg, side, 0, y, 7, y, ramp(WRAP_H)[0] + (255,))
        sk.line(leg, "front", [(2, 22), (5, 22)], ramp((60, 44, 34))[0])     # shoe strap
    round_shade(sk, list(ARMS) + list(LEGS) + ["body"], gi)

def human_face(sk, mood, eye=(70, 50, 36), glow=None, skin=SKIN_H):
    s_hi, s_base, s_sh, s_deep = ramp(skin)
    ink = (50, 32, 24)
    if mood == "determined":
        sk.line("head", "front", [(2, 6), (6, 7)], ink); sk.line("head", "front", [(13, 6), (9, 7)], ink)
    else:
        sk.line("head", "front", [(1, 5), (6, 7)], ink); sk.line("head", "front", [(14, 5), (9, 7)], ink)
        sk.line("head", "front", [(2, 5), (6, 6)], ink); sk.line("head", "front", [(13, 5), (9, 6)], ink)
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (250, 250, 246, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, eye + (255,))
        sk.rect("head", "front", ix + (1 if x0 == 3 else 0), 9, ix + (1 if x0 == 3 else 0), 9, (20, 14, 10, 255))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))
        if glow:
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, glow + (90,))
    sk.rect("head", "front", 7, 10, 8, 11, s_sh + (255,)); sk.rect("head", "front", 7, 11, 7, 11, s_deep + (255,))  # soft nose shadow
    sk.line("head", "front", [(2, 11), (4, 13)], s_sh); sk.line("head", "front", [(13, 11), (11, 13)], s_sh)
    if mood == "determined":
        sk.line("head", "front", [(6, 13), (9, 13)], (150, 84, 70))
    else:
        sk.rect("head", "front", 5, 12, 10, 13, (60, 20, 20, 255)); sk.rect("head", "front", 6, 12, 9, 12, (244, 240, 230, 255))
    sk.line("head", "front", [(4, 15), (11, 15)], s_sh)
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 10, x0 + 2, 10, s_sh + (255,))          # lower lash shadow
    sk.rect("head", "front", 6, 14, 9, 14, s_hi + (255,))                    # lower-lip highlight
    sk.rect("head", "front", 0, 6, 15, 6, s_sh + (255,))                     # hairline shadow
    for side in ("left", "right"):
        sk.rect("head", side, 9, 8, 10, 11, s_sh + (255,))                  # ear
        sk.rect("head", side, 9, 8, 9, 8, s_hi + (255,))
        sk.rect("head", side, 0, 7, 15, 7, s_sh + (255,))

def headband(sk, col=BAND_H, tail=SASH):
    for side in ("front", "left", "right", "back"):
        sk.rect("head", side, 0, 4, 15, 5, ramp(col)[1] + (255,))
        sk.rect("head", side, 0, 4, 15, 4, ramp(col)[0] + (255,)); sk.rect("head", side, 0, 5, 15, 5, ramp(col)[2] + (255,))
    sk.rect("head", "back", 6, 4, 9, 6, ramp(tail)[1] + (255,))               # knot
    sk.rect("head", "back", 6, 7, 7, 12, ramp(tail)[1] + (255,)); sk.rect("head", "back", 8, 7, 9, 10, ramp(tail)[2] + (255,))

@design("human_base", "Human: Base", "full")
def _(sk):
    """Disciplined fighter: short dark hair, white headband with red tails, determined face,
    slate-gray gi with white-trimmed crossed lapels, red sash with a knot, black trousers,
    cream hand and ankle wraps, flat shoes."""
    human_base_body(sk, 600)
    human_face(sk, "determined")
    headband(sk)

def tint_skin(sk, from_col, to_col, tol=60):
    """Recolour pixels close to a skin ramp toward another colour, keeping their shading."""
    px = sk.im.load()
    W, H = sk.im.size
    base = from_col
    for x in range(W):
        for y in range(H):
            c = px[x, y]
            if c[3] == 0:
                continue
            # match by hue-ish ratio to the original skin tone
            if all(abs(c[i] * base[0] / max(1, c[0]) - base[i]) < tol for i in range(3)) and c[0] > 60:
                k = c[0] / base[0]
                px[x, y] = tuple(max(0, min(255, int(to_col[i] * k))) for i in range(3)) + (c[3],)

def aura_edges(sk, col, alpha=150):
    """A glowing aura outline: bright translucent band on the outer edge of every side face."""
    for p in PARTS:
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(0, 0), (0, fh - 1)], col + (alpha,))
            sk.line(p, side, [(fw - 1, 0), (fw - 1, fh - 1)], col + (alpha,))
            sk.line(p, side, [(1, 0), (1, fh - 1)], col + (alpha // 3,))
            sk.line(p, side, [(fw - 2, 0), (fw - 2, fh - 1)], col + (alpha // 3,))

def flame_aura(sk, col, seed, alpha=170):
    """Flickering flame tongues rising along the outer edges of every side face."""
    rnd = random.Random(seed)
    for p in PARTS:
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge in (0, fw - 1):
                y = fh - 1
                while y > 0:
                    h = rnd.randint(2, 5)
                    sk.line(p, side, [(edge, y), (edge, max(0, y - h))], col + (alpha,))
                    inner = 1 if edge == 0 else fw - 2
                    sk.line(p, side, [(inner, y), (inner, max(0, y - h // 2))], col + (alpha // 2,))
                    y -= h + rnd.randint(1, 2)
            sk.line(p, side, [(0, 0), (fw - 1, 0)], col + (alpha // 2,))

@design("human_kaioken", "Human: Kaioken", "full")
def _(sk):
    """Kaioken (detailed): red-flushed skin (wraps stay cream), flickering flame-shaped red
    aura along every edge, heat embers, burning red eyes, gritted teeth, bulging veins,
    red light on the gi trims."""
    RED, RED_HI = (255, 40, 40), (255, 150, 120)
    FLUSH = (236, 136, 116)
    human_base_body(sk, 610, skin=FLUSH)
    human_face(sk, "fierce", eye=(230, 30, 30), glow=RED, skin=FLUSH)
    headband(sk)
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (220, 20, 24, 255))
        sk.rect("head", "front", x0 + 1, 8, x0 + 1, 8, (255, 210, 190, 255))
    for (x, y) in ((1, 7), (2, 8), (1, 9), (14, 7), (13, 8), (14, 9)):
        sk.rect("head", "front", x, y, x, y, (176, 46, 46, 255))              # temple veins
    for arm in ARMS:
        for side in ("front", "back", "left", "right"):
            sk.line(arm, side, [(2, 10), (3, 12), (2, 14), (3, 15)], (176, 46, 46))
            sk.line(arm, side, [(5, 11), (5, 14)], (176, 46, 46))
    glow_line(sk, "body", "front", [(2, 0), (7, 10)], RED_HI)
    glow_line(sk, "body", "front", [(13, 0), (8, 10)], RED_HI)
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 8), (7, 8)], RED_HI)
    rnd = random.Random(611)
    for p in ("body",) + tuple(ARMS) + tuple(LEGS):                          # heat embers
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(2):
                sk.rect(p, side, rnd.randrange(1, fw - 1), rnd.randrange(0, fh), rnd.randrange(1, fw - 1) if False else 0, 0, (0, 0, 0, 0)) if False else None
                x, y = rnd.randrange(2, fw - 2), rnd.randrange(0, fh)
                sk.line(p, side, [(x, y), (x, y)], (255, 190, 120, 200))
    flame_aura(sk, RED, 612)

@design("human_unlocked", "Human: Unlocked Potential", "full")
def _(sk):
    """Unlocked Potential: the fighter calm and composed at a new level - silver-streaked
    hair, pale glowing silver-blue eyes, faint silver ki lines on the arms and chest, a
    silver sheen on every trim and a white-silver aura outlining the body."""
    SILVER, PALE = (226, 232, 244), (190, 220, 255)
    human_base_body(sk, 620)
    human_face(sk, "determined", eye=(150, 200, 255))
    headband(sk, col=(246, 246, 250), tail=(150, 160, 180))
    # silver streaks through the hair
    for side in ("left", "right", "back"):
        for x in range(1, 16, 4):
            sk.line("head", side, [(x, 0), (x + 1, 3)], SILVER)
    for x in range(2, 16, 5):
        sk.line("head", "top", [(x, 0), (x + 2, 15)], SILVER)
    sk.line("head", "front", [(2, 1), (6, 0)], SILVER)                       # one silver swoop in the fringe
    sk.line("head", "front", [(3, 2), (7, 1)], ramp(SILVER)[2])
    # calm glowing eyes: pale iris with a bright core
    for x0 in (3, 10):
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, PALE + (255,))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
    # faint silver ki lines
    for arm in ARMS:
        for side in ("front", "back"):
            glow_line(sk, arm, side, [(2, 10), (3, 12), (2, 15)], SILVER)
    glow_line(sk, "body", "front", [(6, 2), (7, 4), (8, 4), (9, 2)], SILVER)
    # silver sheen on the gi trims and sash edges
    glow_line(sk, "body", "front", [(2, 0), (7, 10)], SILVER)
    glow_line(sk, "body", "front", [(13, 0), (8, 10)], SILVER)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.line("body", side, [(0, 16), (fw - 1, 16)], (255, 200, 200, 180))
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 8), (7, 8)], SILVER)
    aura_edges(sk, (240, 244, 255), alpha=150)
    rnd = random.Random(621)
    for p in PARTS:                                                         # sparkle points on the aura
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(2):
                x = rnd.choice((0, fw - 1)); y = rnd.randrange(0, fh)
                sk.rect(p, side, x, y, x, y, (255, 255, 255, 255))
                if 0 < y < fh - 1:
                    sk.line(p, side, [(x, y - 1), (x, y + 1)], (255, 255, 255, 130))
    for side in ("left", "right", "back", "front"):                           # hair sheen
        sk.line("head", side, [(4, 1), (9, 0)], (255, 255, 255, 120))

# ---- v1.42i: Android line - "synthetic fighter" (original design) -----------------------------
SYN, SUIT, PLATE, CYAN, HAIR_A = (226, 184, 148), (30, 38, 62), (124, 132, 146), (80, 230, 255), (46, 48, 56)

def android_body(sk, seed, light=CYAN, suit=SUIT, damage=0):
    k_hi, k_base, k_sh, k_deep = ramp(SYN)
    u_hi, u_base, u_sh, u_deep = ramp(suit)
    p_hi, p_base, p_sh, p_deep = ramp(PLATE)
    smooth_skin(sk, SYN, seed)
    # Hair: short charcoal undercut, sides shaved.
    h_hi, h_base, h_sh, h_deep = ramp(HAIR_A)
    sk.fill("head", ("top",), h_base, shade=0.06, seed=seed + 1)
    for x in range(1, 15, 3):
        sk.line("head", "top", [(x, 0), (x + 1, 15)], h_sh)
    sk.rect("head", "front", 0, 0, 15, 3, h_base + (255,))
    sk.line("head", "front", [(0, 3), (5, 4), (9, 3), (15, 4)], h_sh)
    for side in ("left", "right", "back"):
        sk.rect("head", side, 0, 0, 15, 3, h_base + (255,))
        rows = 15 if side == "back" else 7
        sk.rect("head", side, 0, 4, 15, rows, (138, 116, 100, 255))            # shaved stubble
        for yy in range(4, rows + 1, 2):
            for xx in range((yy // 2) % 2, 16, 2):
                sk.rect("head", side, xx, yy, xx, yy, (104, 86, 74, 255))
        sk.rect("head", side, 0, 4, 15, 4, h_sh + (255,))                       # fade line
    # Panel seams on face and head.
    sk.line("head", "front", [(1, 6), (1, 14)], k_sh); sk.line("head", "front", [(14, 6), (14, 14)], k_sh)
    sk.line("head", "front", [(1, 14), (5, 15)], k_sh); sk.line("head", "front", [(14, 14), (10, 15)], k_sh)
    for side in ("left", "right"):
        sk.line("head", side, [(3, 8), (12, 8)], k_sh)
        sk.rect("head", side, 4, 10, 7, 12, p_base + (255,))                  # cheek vent grille
        for x in (4, 6):
            sk.line("head", side, [(x, 10), (x, 12)], p_deep)
    # Eyes: natural steel-gray left, cybernetic cyan right.
    ink = (40, 40, 48)
    sk.line("head", "front", [(2, 6), (6, 6)], ink); sk.line("head", "front", [(9, 6), (13, 6)], ink)
    sk.rect("head", "front", 3, 8, 5, 9, (248, 248, 250, 255)); sk.rect("head", "front", 4, 8, 5, 9, (110, 120, 134, 255))
    sk.rect("head", "front", 5, 9, 5, 9, (30, 32, 40, 255)); sk.rect("head", "front", 4, 8, 4, 8, (255, 255, 255, 255))
    sk.rect("head", "front", 3, 7, 5, 7, ink + (255,))
    sk.rect("head", "front", 9, 7, 13, 10, p_deep + (255,))                   # cyber eye housing
    sk.rect("head", "front", 10, 8, 12, 9, ramp(light)[2] + (255,))
    sk.rect("head", "front", 11, 8, 11, 8, (255, 255, 255, 255))
    sk.line("head", "front", [(9, 10), (13, 10)], light + (120,))
    sk.rect("head", "front", 7, 10, 8, 11, k_sh + (255,))
    sk.line("head", "front", [(6, 13), (9, 13)], (168, 104, 92))
    # Bodysuit with cyan light strips and an armoured collar.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 23, u_base + (255,))
        sk.rect("body", side, 0, 0, 0, 23, u_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, u_deep + (255,))
        sk.rect("body", side, 0, 0, fw - 1, 2, p_base + (255,))               # raised collar
        sk.rect("body", side, 0, 0, fw - 1, 0, p_hi + (255,)); sk.rect("body", side, 0, 2, fw - 1, 2, p_deep + (255,))
    sk.fill("body", ("top",), p_base)
    glow_line(sk, "body", "front", [(3, 3), (3, 15)], light); glow_line(sk, "body", "front", [(12, 3), (12, 15)], light)
    sk.line("body", "front", [(7, 3), (7, 15)], u_sh); sk.line("body", "front", [(8, 3), (8, 15)], u_hi)   # centre seam
    for y in (6, 10):
        sk.line("body", "front", [(4, y), (11, y)], u_sh)                       # chest panel lines
    glow_line(sk, "body", "back", [(7, 3), (7, 15)], light)
    sk.line("body", "back", [(2, 5), (6, 9)], u_sh); sk.line("body", "back", [(13, 5), (9, 9)], u_sh)
    # Utility belt with hex plates and a power cell.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 16, fw - 1, 18, p_sh + (255,))
        for x in range(1, fw, 4):
            sk.rect("body", side, x, 16, x + 2, 18, p_base + (255,)); sk.rect("body", side, x, 16, x + 2, 16, p_hi + (255,))
    sk.rect("body", "front", 6, 15, 9, 19, p_deep + (255,))
    sk.rect("body", "front", 7, 16, 8, 18, light + (255,)); sk.rect("body", "front", 7, 16, 7, 16, (255, 255, 255, 255))
    # Arms: hex-plate shoulder guards, suit to the elbow, synthetic forearms with seams.
    for arm in ARMS:
        sk.fill(arm, ("top",), p_base)
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 4, p_base + (255,))
            sk.rect(arm, side, 0, 0, 7, 0, p_hi + (255,)); sk.rect(arm, side, 0, 4, 7, 4, p_deep + (255,))
            sk.line(arm, side, [(3, 1), (2, 2), (3, 3), (5, 3), (6, 2), (5, 1), (3, 1)], p_sh)   # hex
            sk.rect(arm, side, 0, 5, 7, 11, u_base + (255,))
            glow_line(sk, arm, side, [(0, 11), (7, 11)], light)
            sk.line(arm, side, [(0, 15), (7, 15)], k_sh); sk.line(arm, side, [(3, 12), (3, 22)], k_sh)  # panel seams
            sk.rect(arm, side, 0, 20, 7, 23, p_base + (255,))                    # wrist plate
            sk.rect(arm, side, 0, 20, 7, 20, p_hi + (255,))
    # Legs: suit with a light strip, armoured boots.
    for leg in LEGS:
        sk.fill(leg, ("top",), u_base)
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 23, u_base + (255,))
            sk.rect(leg, side, 0, 0, 0, 23, u_sh + (255,)); sk.rect(leg, side, 7, 0, 7, 23, u_deep + (255,))
            sk.rect(leg, side, 1, 8, 6, 11, u_sh + (255,)); sk.rect(leg, side, 1, 8, 6, 8, u_hi + (255,))   # knee pad
            sk.rect(leg, side, 0, 14, 7, 23, p_base + (255,))                    # boot
            sk.rect(leg, side, 0, 14, 7, 14, p_hi + (255,)); sk.rect(leg, side, 0, 23, 7, 23, p_deep + (255,))
            sk.line(leg, side, [(0, 18), (7, 18)], p_sh)
        glow_line(sk, leg, "left", [(3, 1), (3, 12)], light); glow_line(sk, leg, "right", [(3, 1), (3, 12)], light)
        sk.fill(leg, ("bottom",), p_deep)
    # ---- detail pass (v1.42j) ----------------------------------------------------------------
    # Face: brow panel, lip and chin seams, temple data port, circuit traces from the cyber eye.
    sk.line("head", "front", [(2, 5), (13, 5)], k_sh)
    sk.line("head", "front", [(5, 14), (10, 14)], k_sh)
    sk.line("head", "front", [(7, 15), (8, 15)], k_sh)
    sk.line("head", "front", [(13, 9), (15, 9)], ramp(light)[2]); sk.line("head", "front", [(13, 11), (14, 12)], ramp(light)[2])
    sk.rect("head", "front", 14, 12, 14, 12, light + (255,))
    for side in ("right",):
        sk.rect("head", side, 1, 9, 3, 11, p_deep + (255,)); sk.rect("head", side, 2, 10, 2, 10, light + (255,))   # data port
    # Torso: chest plate with a circuit emblem, zipper seam, hex-mesh sides, rivets, spine plates.
    sk.rect("body", "front", 4, 3, 11, 9, p_base + (255,))
    sk.rect("body", "front", 4, 3, 11, 3, p_hi + (255,)); sk.rect("body", "front", 4, 9, 11, 9, p_deep + (255,))
    sk.rect("body", "front", 11, 3, 11, 9, p_sh + (255,))
    for (x, y) in ((7, 4), (6, 5), (8, 5), (5, 6), (9, 6), (5, 7), (6, 7), (7, 7), (8, 7), (9, 7)):   # triangle emblem
        sk.rect("body", "front", x, y, x, y, p_deep + (255,))
    sk.rect("body", "front", 7, 6, 7, 6, light + (255,))
    for (x, y) in ((4, 3), (11, 3), (4, 9), (11, 9)):
        sk.rect("body", "front", x, y, x, y, p_hi + (255,))                     # rivets
    for y in range(10, 16, 2):
        sk.rect("body", "front", 7, y, 8, y, p_sh + (255,))                     # zipper teeth
    for side in ("left", "right"):
        for yy in range(4, 15, 2):
            for xx in range((yy // 2) % 2, 8, 2):
                sk.rect("body", side, xx, yy, xx, yy, u_deep + (255,))          # hex mesh
    for y in range(3, 16, 3):
        sk.rect("body", "back", 5, y, 10, y + 1, p_base + (255,))               # vertebra plates
        sk.rect("body", "back", 5, y, 10, y, p_hi + (255,))
        sk.rect("body", "back", 7, y, 8, y + 1, light + (200,))
    # Belt pouches.
    for x0 in (1, 11):
        sk.rect("body", "front", x0, 17, x0 + 3, 20, ramp((70, 66, 60))[1] + (255,))
        sk.rect("body", "front", x0, 17, x0 + 3, 17, ramp((70, 66, 60))[0] + (255,))
        sk.rect("body", "front", x0 + 1, 18, x0 + 2, 18, p_hi + (255,))
    # Arms: ribbed elbow joints, circuit traces on forearms, segmented gloved hands.
    for arm in ARMS:
        for side in SIDES:
            for y in (12, 13, 14):
                sk.line(arm, side, [(0, y), (7, y)], p_sh if y % 2 else p_base)
            sk.line(arm, side, [(1, 16), (1, 18), (3, 18)], ramp(light)[2])
            sk.rect(arm, side, 3, 18, 3, 18, light + (255,))
            sk.rect(arm, side, 0, 21, 7, 23, ramp((44, 46, 54))[1] + (255,))     # glove
            for x in (2, 4, 6):
                sk.line(arm, side, [(x, 21), (x, 23)], ramp((44, 46, 54))[3])
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=ramp((44, 46, 54))[1] + (255,))
        for gx in range(1, fw, 2):
            sk.d.line((x + gx, y, x + gx, y + fh - 1), fill=ramp((44, 46, 54))[3] + (255,))
    # Legs: thigh strap, bolted knee armour, ankle joints, treaded soles.
    for leg in LEGS:
        for side in SIDES:
            sk.rect(leg, side, 0, 3, 7, 4, ramp((70, 66, 60))[1] + (255,))     # thigh strap
            sk.rect(leg, side, 3, 3, 4, 4, p_hi + (255,))
            sk.rect(leg, side, 1, 8, 6, 12, p_base + (255,))                    # knee armour
            sk.rect(leg, side, 1, 8, 6, 8, p_hi + (255,)); sk.rect(leg, side, 1, 12, 6, 12, p_deep + (255,))
            sk.rect(leg, side, 1, 9, 1, 9, (210, 214, 224, 255)); sk.rect(leg, side, 6, 9, 6, 9, (210, 214, 224, 255))   # bolts
            sk.rect(leg, side, 0, 19, 7, 19, p_deep + (255,))                   # ankle joint
            sk.rect(leg, side, 0, 20, 7, 20, p_sh + (255,))
        x, y, fw, fh = Skin.face(PARTS[leg][0], PARTS[leg][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=p_deep + (255,))
        for ty in range(y, y + fh, 2):
            sk.d.line((x, ty, x + fw - 1, ty), fill=(30, 32, 38, 255))
    round_shade(sk, list(ARMS) + list(LEGS) + ["body"], suit)

@design("android_base", "Android: Base", "full")
def _(sk):
    """Synthetic fighter: pale synthetic skin with panel seams and a cheek vent, a natural
    steel-gray eye and a cybernetic cyan eye, charcoal undercut, navy bodysuit with cyan
    light strips, armoured collar, hex-plate shoulder guards, utility belt with a glowing
    power cell, wrist plates, knee pads and armoured boots."""
    android_body(sk, 700)

def scratches(sk, part, side, seed, n=3, col=(214, 220, 232)):
    rnd = random.Random(seed)
    _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
    for _ in range(n):
        x, y = rnd.randrange(0, fw - 3), rnd.randrange(0, fh - 3)
        sk.line(part, side, [(x, y), (x + 2, y + rnd.choice((1, 2)))], col + (210,))

@design("android_power", "Android: Powered Up", "full")
def _(sk):
    """Powered-up Android: the same unit at full output - brighter branching energy lines,
    both eyes lit, scratched and dented plates, a cracked chest plate exposing glowing
    circuitry, a torn sleeve showing machinery underneath, scorch marks."""
    HOT = (150, 250, 255)
    android_body(sk, 710, light=HOT)
    p_hi, p_base, p_sh, p_deep = ramp(PLATE)
    u_hi, u_base, u_sh, u_deep = ramp(SUIT)
    # Both eyes lit: the natural eye is overtaken by the glow.
    sk.rect("head", "front", 3, 8, 5, 9, ramp(HOT)[2] + (255,))
    sk.rect("head", "front", 4, 8, 4, 8, (255, 255, 255, 255))
    sk.line("head", "front", [(2, 10), (6, 10)], HOT + (110,))
    glow_line(sk, "head", "front", [(2, 9), (0, 11)], HOT)                     # trace from the left eye too
    # Cracked chest plate exposing circuitry.
    sk.rect("body", "front", 5, 4, 10, 8, (14, 20, 30, 255))
    for (x, y) in ((5, 5), (6, 6), (7, 5), (8, 7), (9, 6), (10, 5), (6, 8), (9, 8)):
        sk.rect("body", "front", x, y, x, y, HOT + (255,))
    sk.line("body", "front", [(5, 5), (7, 6), (9, 6)], ramp(HOT)[1])
    sk.line("body", "front", [(4, 3), (6, 4)], p_deep); sk.line("body", "front", [(11, 3), (9, 4)], p_deep)   # crack lines
    sk.line("body", "front", [(4, 9), (6, 8)], p_deep)
    # Branching energy lines across the suit.
    glow_line(sk, "body", "front", [(3, 10), (1, 13), (2, 15)], HOT)
    glow_line(sk, "body", "front", [(12, 10), (14, 13), (13, 15)], HOT)
    glow_line(sk, "body", "back", [(6, 9), (3, 13)], HOT); glow_line(sk, "body", "back", [(9, 9), (12, 13)], HOT)
    for leg in LEGS:
        glow_line(sk, leg, "front", [(2, 1), (3, 4), (2, 7)], HOT)
    # Torn left sleeve showing machinery underneath.
    sk.rect("leftArm", "front", 1, 6, 6, 10, (40, 44, 54, 255))
    for y in (7, 9):
        sk.line("leftArm", "front", [(1, y), (6, y)], p_sh)
    sk.rect("leftArm", "front", 3, 8, 4, 8, HOT + (255,))
    for x in (1, 3, 5):
        sk.rect("leftArm", "front", x, 5, x, 5, u_base + (255,)); sk.rect("leftArm", "front", x + 1, 11, x + 1, 11, u_base + (255,))  # torn edge
    # Scratches and dents on every plate, scorch marks.
    seed = 720
    for part in ("body",) + tuple(ARMS) + tuple(LEGS):
        for side in SIDES:
            if side in ("front", "back"):
                scratches(sk, part, side, seed, n=1); seed += 1
    for (part, side, x, y) in (("rightArm", "front", 2, 2), ("leftLeg", "front", 3, 10), ("rightLeg", "left", 4, 16),
                               ("body", "back", 3, 1), ("leftArm", "back", 5, 21)):
        sk.rect(part, side, x, y, x + 1, y + 1, p_deep + (255,))               # dents
        sk.rect(part, side, x, y, x, y, (30, 30, 36, 255))
    for (part, side, x, y) in (("body", "front", 12, 12), ("rightLeg", "front", 1, 4), ("body", "back", 10, 17)):
        sk.rect(part, side, x, y, x + 2, y + 1, (20, 20, 24, 150))             # scorch
    aura_edges(sk, HOT, alpha=60)

# ---- v1.47: Saiyan line - reusable builders (original outfit design) -------------------------
SAI_SKIN = (232, 186, 146)
SAI_GI, SAI_TRIM, SAI_UNDER, SAI_SASH, SAI_BAND, SAI_BOOT = (54, 56, 66), (226, 180, 70), (150, 30, 40), (150, 30, 40), (30, 30, 36), (40, 36, 40)

def ramp6(c):
    """6 shades: rim highlight, highlight, base, shade, deep, outline."""
    ks = [1.32, 1.15, 1.0, 0.8, 0.62, 0.42]
    return [tuple(max(0, min(255, int(v * k) + (14 if k > 1.2 else 0))) for v in c) for k in ks]

def saiyan_body(sk, seed, skin=SAI_SKIN, gi=SAI_GI, trim=SAI_TRIM, under=SAI_UNDER, sash=SAI_SASH, torn=0):
    """Gi-clad Saiyan body. torn: 0 = intact, 1 = battle-damaged, 2 = shredded (upper gi gone)."""
    s6 = ramp6(skin); g6 = ramp6(gi); t6 = ramp6(trim); u6 = ramp6(under); h6 = ramp6(sash)
    smooth_skin(sk, skin, seed)
    muscles(sk, skin)
    # ---- Torso: open-front gi over a crimson undershirt, gold-trimmed lapels ----
    if torn < 2:
        for side in SIDES:
            _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
            sk.rect("body", side, 0, 0, fw - 1, 23, g6[2] + (255,))
            sk.rect("body", side, 0, 0, fw - 1, 0, g6[1] + (255,))
            sk.rect("body", side, 0, 0, 0, 23, g6[3] + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, g6[4] + (255,))
        sk.fill("body", ("top",), g6[2])
        for y in range(0, 12):                                   # crimson undershirt V
            half = max(0, 5 - y // 2)
            sk.rect("body", "front", 7 - half, y, 8 + half, y, u6[2] + (255,))
        sk.line("body", "front", [(6, 2), (9, 2)], u6[3])
        sk.line("body", "front", [(2, 0), (7, 11)], t6[1]); sk.line("body", "front", [(3, 0), (7, 10)], t6[3])
        sk.line("body", "front", [(13, 0), (8, 11)], t6[2]); sk.line("body", "front", [(12, 0), (8, 10)], t6[4])
        for (x, y) in ((4, 4), (5, 6), (11, 4), (10, 6)):
            sk.rect("body", "front", x, y, x, y, t6[0] + (255,))          # trim glints
        for (a, b) in (((2, 14), (5, 12)), ((13, 14), (10, 12)), ((3, 19), (6, 17))):
            sk.line("body", "front", [a, b], g6[3])                    # folds
        sk.line("body", "back", [(7, 1), (7, 15)], g6[3])
        for (a, b) in (((2, 4), (5, 9)), ((13, 4), (10, 9)), ((4, 13), (6, 17))):
            sk.line("body", "back", [a, b], g6[3])
        # back emblem: original gold ring with a flame mark
        for (x, y) in ((6, 4), (7, 3), (8, 3), (9, 4), (10, 5), (10, 6), (9, 7), (8, 8), (7, 8), (6, 7), (5, 6), (5, 5)):
            sk.rect("body", "back", x, y, x, y, t6[2] + (255,))
        sk.rect("body", "back", 7, 5, 8, 6, h6[1] + (255,)); sk.rect("body", "back", 7, 4, 7, 4, h6[0] + (255,))
    # ---- Sash ----
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 16, fw - 1, 19, h6[2] + (255,))
        sk.rect("body", side, 0, 16, fw - 1, 16, h6[1] + (255,)); sk.rect("body", side, 0, 19, fw - 1, 19, h6[4] + (255,))
        for x in range(0, fw, 3):
            sk.rect("body", side, x, 17, x + 1, 17, h6[3] + (255,))
        sk.rect("body", side, 0, 20, fw - 1, 23, g6[3] + (255,))
    sk.rect("body", "back", 6, 16, 9, 19, h6[3] + (255,))                   # knot at the back
    sk.line("body", "back", [(7, 20), (6, 23)], h6[2]); sk.line("body", "back", [(8, 20), (9, 23)], h6[2])
    # ---- Arms: gi sleeves to mid-upper-arm, muscle, wristbands ----
    for arm in ARMS:
        if torn < 2:
            sk.fill(arm, ("top",), g6[2])
        for side in SIDES:
            if torn < 2:
                sk.rect(arm, side, 0, 0, 7, 6, g6[2] + (255,))
                sk.rect(arm, side, 0, 0, 7, 0, g6[1] + (255,))
                sk.rect(arm, side, 0, 6, 7, 6, t6[2] + (255,))                # gold cuff
                sk.line(arm, side, [(1, 2), (4, 4)], g6[3])
            sk.line(arm, side, [(1, 8), (2, 12)], s6[3]); sk.line(arm, side, [(5, 8), (6, 11)], s6[1])   # bicep
            sk.line(arm, side, [(2, 14), (3, 18)], s6[3])                    # forearm
            sk.rect(arm, side, 0, 19, 7, 22, ramp6(SAI_BAND)[2] + (255,))      # wristband
            sk.rect(arm, side, 0, 19, 7, 19, ramp6(SAI_BAND)[0] + (255,)); sk.rect(arm, side, 0, 22, 7, 22, t6[3] + (255,))
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        for kx in range(1, fw, 2):
            sk.d.point((x + kx, y + 1), fill=s6[4] + (255,))
    # ---- Legs: gi trousers, ankle gathers, boots with gold toe caps ----
    b6 = ramp6(SAI_BOOT)
    for leg in LEGS:
        sk.fill(leg, ("top",), g6[2])
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 16, g6[2] + (255,))
            sk.rect(leg, side, 0, 0, 0, 16, g6[3] + (255,)); sk.rect(leg, side, 7, 0, 7, 16, g6[4] + (255,))
            sk.line(leg, side, [(3, 1), (2, 9)], g6[1]); sk.line(leg, side, [(1, 10), (3, 11), (6, 10)], g6[4])
            sk.rect(leg, side, 0, 15, 7, 16, g6[4] + (255,))                 # gathered above the boot
            sk.rect(leg, side, 0, 17, 7, 23, b6[2] + (255,))                 # boot
            sk.rect(leg, side, 0, 17, 7, 17, b6[0] + (255,)); sk.rect(leg, side, 0, 23, 7, 23, b6[5] + (255,))
            sk.line(leg, side, [(1, 18), (1, 22)], b6[1])
        sk.rect(leg, "front", 1, 20, 6, 22, t6[2] + (255,)); sk.rect(leg, "front", 1, 20, 6, 20, t6[0] + (255,))   # toe cap
        sk.fill(leg, ("bottom",), b6[4])
    # ---- Battle damage ----
    if torn >= 1:
        rnd = random.Random(seed + 9)
        for part in ("body",) + tuple(ARMS) + tuple(LEGS):
            for side in ("front", "back"):
                _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
                for _ in range(2):                                           # tears showing skin
                    x, y = rnd.randrange(1, fw - 3), rnd.randrange(1, fh - 4)
                    sk.rect(part, side, x, y, x + 1, y + 2, s6[2] + (255,))
                    sk.line(part, side, [(x - 1, y), (x + 2, y)], g6[4])
                x, y = rnd.randrange(1, fw - 2), rnd.randrange(1, fh - 2)  # bruise / scratch
                sk.line(part, side, [(x, y), (x + 2, y + 1)], (150, 60, 60))
    round_shade(sk, list(ARMS) + list(LEGS) + ["body"], gi)

def saiyan_head(sk, hair, skin=SAI_SKIN, eye=(30, 26, 26), mood="smirk", brows=True, glow=None, heavy_brow=False):
    """Face + scalp. The 3D spikes come from the hair attachable; this paints the scalp,
    sideburns and hairline so nothing shows through underneath."""
    s6 = ramp6(skin); h6 = ramp6(hair)
    ink = tuple(int(v * 0.3) for v in skin)
    # scalp and sides
    sk.fill("head", ("top",), h6[2])
    for y in range(0, 16, 3):
        sk.line("head", "top", [(0, y), (15, y + 1)], h6[3])
    for side in ("left", "right", "back"):
        sk.rect("head", side, 0, 0, 15, 7 if side != "back" else 13, h6[2] + (255,))
        for x in range(0, 16, 3):
            sk.line("head", side, [(x, 0), (x + 1, 6 if side != "back" else 12)], h6[3])
            sk.rect("head", side, x + 1, 1, x + 1, 2, h6[1] + (255,))
        if side != "back":
            sk.rect("head", side, 11, 7, 14, 10, h6[2] + (255,))             # sideburn
            sk.rect("head", side, 3, 8, 6, 11, s6[3] + (255,))               # ear
            sk.rect("head", side, 4, 9, 5, 10, s6[4] + (255,))
    # hairline: jagged fringe across the forehead
    sk.rect("head", "front", 0, 0, 15, 2, h6[2] + (255,))
    for x, depth in ((0, 5), (2, 3), (4, 4), (6, 2), (8, 4), (10, 3), (12, 5), (14, 4)):
        sk.rect("head", "front", x, 3, x + 1, 2 + depth, h6[2] + (255,))
        sk.rect("head", "front", x, 2 + depth, x, 2 + depth, h6[3] + (255,))
    for x in range(0, 16, 2):
        sk.rect("head", "front", x, 0, x, 0, h6[1] + (255,))
    if glow:
        for side in ("front", "left", "right", "back", "top"):
            _, _, fw, fh = Skin.face(PARTS["head"][0], PARTS["head"][1], side)
            sk.line("head", side, [(0, 0), (fw - 1, 0)], glow + (200,))
    # brows
    if heavy_brow:
        sk.rect("head", "front", 1, 6, 14, 7, s6[3] + (255,))                # heavy brow ridge, no eyebrows
        sk.line("head", "front", [(1, 6), (14, 6)], s6[4])
    elif brows:
        if mood in ("angry", "fierce"):
            sk.line("head", "front", [(1, 5), (6, 7)], ink); sk.line("head", "front", [(14, 5), (9, 7)], ink)
            sk.line("head", "front", [(2, 5), (6, 6)], ink); sk.line("head", "front", [(13, 5), (9, 6)], ink)
        elif mood == "calm":
            sk.line("head", "front", [(2, 6), (6, 6)], ink); sk.line("head", "front", [(9, 6), (13, 6)], ink)
        else:  # smirk: one brow raised
            sk.line("head", "front", [(2, 6), (6, 5)], ink); sk.line("head", "front", [(9, 6), (13, 7)], ink)
    # eyes
    for x0 in (3, 10):
        if mood == "blank":
            sk.rect("head", "front", x0, 8, x0 + 2, 9, eye + (255,))
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, eye + (100,))
            continue
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (250, 250, 246, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, eye + (255,))
        sk.rect("head", "front", ix + (1 if x0 == 3 else 0), 9, ix + (1 if x0 == 3 else 0), 9, ramp6(eye)[4] + (255,))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))
        if mood in ("angry", "fierce"):
            sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,)); sk.rect("head", "front", x0, 8, x0 + 2, 8, ink[:3] + (255,)) if False else None
        if glow:
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, glow + (80,))
    # nose, cheeks, jaw
    sk.rect("head", "front", 7, 10, 8, 11, s6[3] + (255,)); sk.rect("head", "front", 7, 11, 7, 11, s6[4] + (255,))
    sk.line("head", "front", [(2, 11), (4, 13)], s6[3]); sk.line("head", "front", [(13, 11), (11, 13)], s6[3])
    sk.line("head", "front", [(4, 15), (11, 15)], s6[3])
    # mouth
    if mood == "smirk":
        sk.line("head", "front", [(5, 13), (9, 13), (10, 12)], (130, 70, 60))
    elif mood == "calm":
        sk.line("head", "front", [(6, 13), (9, 13)], (150, 84, 70))
    elif mood == "grin":
        sk.rect("head", "front", 4, 12, 11, 13, (70, 20, 24, 255)); sk.rect("head", "front", 5, 12, 10, 12, (246, 242, 234, 255))
        sk.line("head", "front", [(3, 11), (4, 12)], ink); sk.line("head", "front", [(12, 11), (11, 12)], ink)
    else:  # angry / fierce / blank: gritted teeth
        sk.rect("head", "front", 5, 12, 10, 13, (70, 20, 24, 255)); sk.rect("head", "front", 6, 12, 9, 12, (246, 242, 234, 255))
        for x in (7, 9):
            sk.rect("head", "front", x, 12, x, 12, (190, 184, 176, 255))

@design("saiyan_base", "Saiyan: Base", "full")
def _(sk):
    """Base Saiyan: original outfit - charcoal gi with gold-trimmed lapels over a crimson
    undershirt, crimson sash with a back knot, black-and-gold wristbands, dark boots with
    gold toe caps, a gold ring emblem on the back; black spiky hairline, confident smirk."""
    saiyan_body(sk, 800)
    saiyan_head(sk, (34, 30, 36), mood="smirk")

# ---- v1.47: Saiyan line - "saiyan warrior" (original design) ------------------------------------
SKIN_S = (230, 186, 146)
SGI, SGI_TRIM, SUNDER, SSASH, SBOOT = (24, 96, 104), (232, 190, 72), (26, 26, 32), (232, 190, 72), (52, 52, 60)

def saiyan_hair_paint(sk, col, glow=None):
    """Hair painted on the head (the 3D spikes come from the hair model). Spiky hairline."""
    h = ramp(col)
    sk.fill("head", ("top",), h[1], shade=0.08, seed=801)
    for x in range(0, 16, 2):
        sk.line("head", "top", [(x, 0), (x + 1, 15)], h[2])
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        sk.rect("head", side, 0, 0, 15, rows, h[1] + (255,))
        for x in range(0, 16, 3):                                         # jagged lower edge
            sk.rect("head", side, x, rows + 1, x + 1, rows + 2, h[1] + (255,))
            sk.line("head", side, [(x, 0), (x + 1, rows)], h[2])
            sk.rect("head", side, x + 1, 1, x + 1, 3, h[0] + (255,))
    sk.rect("head", "front", 0, 0, 15, 3, h[1] + (255,))
    for x, depth in ((0, 5), (2, 4), (4, 5), (6, 4), (8, 5), (10, 4), (12, 5), (14, 4)):   # spiky fringe (stays above the brows)
        sk.line("head", "front", [(x, 3), (x + 1, depth)], h[1])
        sk.rect("head", "front", x, 4, x, 4, h[2] + (255,))
    for x in range(1, 16, 4):
        sk.rect("head", "front", x, 1, x, 2, h[0] + (255,))
    if glow:
        for side in ("left", "right", "back", "front"):
            sk.line("head", side, [(0, 0), (15, 0)], glow + (200,))

def saiyan_face(sk, mood, eye=(30, 26, 24), skin=SKIN_S, brows=True, glow=None, eye_white=(250, 250, 246), brow_col=None):
    """mood: smirk / intense / calm / fierce_grin / blank. brow_col tints the eyebrows to match the hair."""
    s_hi, s_base, s_sh, s_deep = ramp(skin)
    ink = brow_col or (36, 26, 22)
    if brows:
        if mood in ("smirk", "calm"):
            sk.line("head", "front", [(2, 6), (6, 6)], ink); sk.line("head", "front", [(9, 6), (13, 6)], ink)
            if mood == "smirk":
                sk.rect("head", "front", 12, 5, 13, 5, ink + (255,))        # one brow cocked
        else:
            sk.line("head", "front", [(1, 5), (6, 7)], ink); sk.line("head", "front", [(14, 5), (9, 7)], ink)
            sk.line("head", "front", [(2, 5), (6, 6)], ink); sk.line("head", "front", [(13, 5), (9, 6)], ink)
    else:
        sk.line("head", "front", [(1, 6), (6, 7)], s_deep); sk.line("head", "front", [(14, 6), (9, 7)], s_deep)   # heavy brow ridge
        sk.line("head", "front", [(1, 5), (6, 6)], s_hi); sk.line("head", "front", [(14, 5), (9, 6)], s_hi)
    for x0 in (3, 10):
        if mood == "blank":
            sk.rect("head", "front", x0, 8, x0 + 2, 9, eye + (255,))
            sk.rect("head", "front", x0 + 1, 8, x0 + 1, 8, (255, 255, 240, 255))
        else:
            sk.rect("head", "front", x0, 8, x0 + 2, 9, eye_white + (255,))
            ix = x0 + (1 if x0 == 3 else 0)
            sk.rect("head", "front", ix, 8, ix + 1, 9, eye + (255,))
            sk.rect("head", "front", ix + (1 if x0 == 3 else 0), 9, ix + (1 if x0 == 3 else 0), 9, tuple(int(v * 0.4) for v in eye) + (255,))
            sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))
        sk.rect("head", "front", x0, 10, x0 + 2, 10, s_sh + (255,))
        if glow:
            sk.rect("head", "front", x0 - 1, 10, x0 + 3, 10, glow + (90,))
    sk.rect("head", "front", 7, 10, 8, 11, s_sh + (255,)); sk.rect("head", "front", 7, 11, 7, 11, s_deep + (255,))
    sk.line("head", "front", [(2, 11), (4, 13)], s_sh); sk.line("head", "front", [(13, 11), (11, 13)], s_sh)
    if mood == "smirk":
        sk.line("head", "front", [(6, 13), (9, 13), (10, 12)], (140, 80, 66))
    elif mood == "calm":
        sk.line("head", "front", [(6, 13), (9, 13)], (150, 90, 76))
    elif mood == "fierce_grin":
        sk.rect("head", "front", 4, 12, 11, 13, (60, 18, 22, 255)); sk.rect("head", "front", 5, 12, 10, 12, (248, 244, 236, 255))
        sk.line("head", "front", [(3, 11), (4, 12)], ink); sk.line("head", "front", [(12, 11), (11, 12)], ink)
    else:  # intense / blank
        sk.rect("head", "front", 5, 12, 10, 13, (60, 18, 22, 255)); sk.rect("head", "front", 6, 12, 9, 12, (244, 240, 230, 255))
    sk.line("head", "front", [(4, 15), (11, 15)], s_sh)
    sk.rect("head", "front", 6, 14, 9, 14, s_hi + (255,))
    for side in ("left", "right"):
        sk.rect("head", side, 9, 9, 10, 12, s_sh + (255,)); sk.rect("head", side, 9, 9, 9, 9, s_hi + (255,))   # ear

def saiyan_body(sk, seed, skin=SKIN_S, gi=SGI, trim=SGI_TRIM, under=SUNDER, sash=SSASH, damage=0):
    """Original Saiyan warrior outfit: teal gi with gold trim over a black undershirt, gold sash,
    black wristbands, dark boots with gold toe caps. damage 0..2 adds tears, scratches, bruises."""
    s_hi, s_base, s_sh, s_deep = ramp(skin)
    g_hi, g_base, g_sh, g_deep = ramp(gi)
    u_hi, u_base, u_sh, u_deep = ramp(under)
    t_hi, t_base, t_sh, t_deep = ramp(trim)
    b_hi, b_base, b_sh, b_deep = ramp(SBOOT)
    smooth_skin(sk, skin, seed)
    muscles(sk, skin)
    # Gi top: black undershirt V, teal panels with gold trim, folds, back crest.
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 23, g_base + (255,))
        sk.rect("body", side, 0, 0, 0, 23, g_sh + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 23, g_deep + (255,))
        if side != "front":
            folds(sk, "body", (side,), gi, seed + 1, n=2)
    sk.fill("body", ("top",), g_base)
    for y in range(0, 11):
        half = max(0, 4 - y // 2)
        sk.rect("body", "front", 7 - half, y, 8 + half, y, u_base + (255,))
    sk.line("body", "front", [(2, 0), (7, 11)], t_base); sk.line("body", "front", [(3, 0), (8, 11)], t_sh)
    sk.line("body", "front", [(13, 0), (8, 11)], t_base)
    sk.line("body", "front", [(3, 1), (7, 9)], g_deep)
    sk.line("body", "front", [(4, 13), (6, 16)], g_sh); sk.line("body", "front", [(11, 13), (9, 16)], g_sh)
    for (x, y) in ((6, 4), (7, 3), (8, 3), (9, 4), (10, 5), (10, 6), (9, 7), (8, 8), (7, 8), (6, 7), (5, 6), (5, 5)):
        sk.rect("body", "back", x, y, x, y, t_base + (255,))                 # ring crest on the back
    sk.rect("body", "back", 7, 5, 8, 6, (200, 40, 40, 255))
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        if side in ("left", "right"):
            stitch(sk, "body", side, 3, 1, 3, 15, g_sh)
        sk.rect("body", side, 0, 16, fw - 1, 19, t_base + (255,))             # gold sash
        sk.rect("body", side, 0, 16, fw - 1, 16, t_hi + (255,)); sk.rect("body", side, 0, 19, fw - 1, 19, t_deep + (255,))
        for x in range(0, fw, 2):
            sk.rect("body", side, x, 17 + (x // 2) % 2, x, 17 + (x // 2) % 2, t_sh + (255,))
        sk.rect("body", side, 0, 20, fw - 1, 23, g_base + (255,))
    sk.rect("body", "front", 10, 16, 12, 19, t_sh + (255,))                  # sash knot
    sk.line("body", "front", [(11, 20), (10, 23)], t_base); sk.line("body", "front", [(12, 20), (13, 23)], t_base)
    # Arms: short teal sleeves with trim, bare muscular forearms, black wristbands.
    for arm in ARMS:
        sk.fill(arm, ("top",), g_base)
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 6, g_base + (255,))
            sk.rect(arm, side, 0, 0, 7, 0, g_hi + (255,))
            sk.rect(arm, side, 0, 6, 7, 6, t_base + (255,))
            sk.line(arm, side, [(1, 2), (4, 5)], g_sh)
            sk.line(arm, side, [(1, 8), (2, 12)], s_sh); sk.line(arm, side, [(5, 8), (6, 12)], s_hi)   # biceps / forearm
            sk.line(arm, side, [(3, 13), (3, 16)], s_sh)
            sk.rect(arm, side, 0, 17, 7, 21, u_base + (255,))                # wristband
            sk.rect(arm, side, 0, 17, 7, 17, u_hi + (255,)); sk.rect(arm, side, 0, 21, 7, 21, u_deep + (255,))
            sk.line(arm, side, [(0, 19), (7, 19)], u_sh)
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        for kx in range(1, fw, 2):
            sk.d.point((x + kx, y + 1), fill=s_deep + (255,))                # knuckles
    # Legs: teal trousers with creases, dark boots with gold toe caps.
    for leg in LEGS:
        sk.fill(leg, ("top",), g_base)
        for side in SIDES:
            sk.rect(leg, side, 0, 0, 7, 14, g_base + (255,))
            sk.rect(leg, side, 0, 0, 0, 14, g_sh + (255,)); sk.rect(leg, side, 7, 0, 7, 14, g_deep + (255,))
            sk.line(leg, side, [(3, 1), (2, 9)], g_hi); sk.line(leg, side, [(1, 10), (3, 11), (6, 10)], g_deep)
            sk.rect(leg, side, 0, 14, 7, 15, g_deep + (255,))                # tucked hem
            sk.rect(leg, side, 0, 16, 7, 23, b_base + (255,))                # boots
            sk.rect(leg, side, 0, 16, 7, 16, b_hi + (255,)); sk.rect(leg, side, 0, 23, 7, 23, b_deep + (255,))
            sk.line(leg, side, [(0, 19), (7, 19)], t_base)                   # gold boot band
        sk.rect(leg, "front", 1, 21, 6, 22, t_base + (255,)); sk.rect(leg, "front", 1, 21, 6, 21, t_hi + (255,))   # toe cap
        sk.fill(leg, ("bottom",), b_deep)
    # Battle damage.
    if damage:
        rnd = random.Random(seed + 9)
        for part in ("body",) + tuple(ARMS) + tuple(LEGS):
            for side in SIDES:
                _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
                for _ in range(damage):
                    x, y = rnd.randrange(1, fw - 3), rnd.randrange(2, fh - 4)
                    sk.rect(part, side, x, y, x + 2, y + 2, s_base + (255,))         # torn hole showing skin
                    sk.line(part, side, [(x, y), (x + 2, y + 1)], s_deep)
                    sk.line(part, side, [(x + 1, y + 3), (x + 3, y + 5)], (170, 40, 40, 200))   # scratch
                bx, by = rnd.randrange(1, fw - 2), rnd.randrange(2, fh - 3)
                sk.rect(part, side, bx, by, bx + 1, by + 1, (120, 80, 120, 140))      # bruise
    round_shade(sk, list(ARMS) + list(LEGS) + ["body"], gi)

@design("saiyan_base", "Saiyan: Base", "full")
def _(sk):
    """Base Saiyan (original outfit): black spiky hair, confident smirk with dark eyes, teal gi
    with gold trim over a black undershirt, gold woven sash with a knot, ring crest on the back,
    bare muscular forearms, black wristbands, teal trousers, dark boots with gold toe caps."""
    saiyan_body(sk, 800)
    saiyan_hair_paint(sk, (30, 28, 34))
    saiyan_face(sk, "smirk")

def fire_aura(sk, seed, base=(170, 14, 24), mid=(255, 70, 40), tip=(255, 214, 90), head_flames=False, skip_head=True):
    """Three-tone flame tongues on every outer edge, plus flames along the top of the head."""
    rnd = random.Random(seed)
    for p in PARTS:
        if skip_head and p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge, inner in ((0, 1), (fw - 1, fw - 2)):
                y = fh - 1
                while y > 1:
                    h = rnd.randint(3, 6)
                    top = max(0, y - h)
                    sk.line(p, side, [(edge, y), (edge, top + 2)], base + (220,))
                    sk.line(p, side, [(edge, top + 2), (edge, top + 1)], mid + (230,))
                    sk.line(p, side, [(edge, top), (edge, top)], tip + (240,))
                    sk.line(p, side, [(inner, y), (inner, y - h // 2)], mid + (110,))
                    y -= h + rnd.randint(1, 2)
    if head_flames:
        for side in SIDES:                                                 # flames licking over the head
            for x in range(0, 16, 3):
                h = rnd.randint(1, 3)
                sk.line("head", side, [(x, h), (x, 0)], mid + (200,))
                sk.rect("head", side, x, 0, x, 0, tip + (230,))

def rim_light(sk, col, alpha=110):
    """A coloured rim light down the right edge of every side face."""
    for p in PARTS:
        for side in SIDES:
            if p == "head":
                continue                                                  # never on the head (hair/face stay clean)
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(fw - 3, 0), (fw - 3, fh - 1)], col + (alpha // 2,))

def vein(sk, part, side, pts, col=(255, 70, 60)):
    sk.line(part, side, pts, (120, 10, 16))
    sk.line(part, side, [(x, y - 1) for x, y in pts], col + (220,))

@design("saiyan_kaioken", "Saiyan: Kaioken", "full")
def _(sk):
    """Kaioken (v2): red-flushed skin with crimson rim light, three-tone flame aura (crimson ->
    red-orange -> yellow tips) on every edge and over the head, glowing branching veins,
    steam rising from shoulders and head, sweat beads, fully glowing red eyes, clenched teeth."""
    FLUSH = (240, 128, 108)
    RED = (255, 40, 40)
    f_hi, f_base, f_sh, f_deep = ramp(FLUSH)
    saiyan_body(sk, 810, skin=FLUSH)
    saiyan_hair_paint(sk, (34, 26, 30))
    # ---- face (v3): determined hero, not demonic ------------------------------------------
    ink = (52, 20, 18)
    sk.line("head", "front", [(2, 5), (6, 7)], ink); sk.line("head", "front", [(13, 5), (9, 7)], ink)   # single furrowed brows
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (252, 246, 242, 255))            # normal whites
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, (170, 26, 32, 255))              # dark-red iris
        sk.rect("head", "front", ix + (1 if x0 == 3 else 0), 9, ix + (1 if x0 == 3 else 0), 9, (50, 8, 10, 255))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))
        sk.rect("head", "front", x0, 10, x0 + 2, 10, f_sh + (255,))
    sk.rect("head", "front", 7, 10, 8, 11, f_sh + (255,))
    sk.line("head", "front", [(2, 11), (4, 13)], f_sh); sk.line("head", "front", [(13, 11), (11, 13)], f_sh)
    sk.rect("head", "front", 5, 12, 10, 13, (60, 16, 18, 255))                       # determined gritted grin
    sk.rect("head", "front", 6, 12, 9, 12, (248, 242, 234, 255))
    sk.line("head", "front", [(4, 12), (5, 12)], ink); sk.line("head", "front", [(10, 12), (11, 11)], ink)
    sk.rect("head", "front", 13, 6, 13, 7, (220, 240, 255, 230))                      # one sweat bead
    for arm in ARMS:
        for side in SIDES:
            vein(sk, arm, side, [(2, 8), (3, 11), (2, 13), (3, 16)])
    # ---- red light on the gold trim, rim light, fire aura, steam ---------------------------------
    glow_line(sk, "body", "front", [(2, 0), (7, 11)], (255, 150, 120)); glow_line(sk, "body", "front", [(13, 0), (8, 11)], (255, 150, 120))
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 6), (7, 6)], (255, 150, 120))
    rim_light(sk, RED, alpha=180)
    fire_aura(sk, 811)
    rnd = random.Random(812)
    for part, sides_ in (("rightArm", ("top",)), ("leftArm", ("top",))):         # steam off the shoulders only
        for side in sides_:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for _ in range(3):                                                  # steam wisps
                x, y = rnd.randrange(1, fw - 2), rnd.randrange(0, min(fh, 6))
                sk.line(part, side, [(x, y + 2), (x + 1, y + 1), (x, y)], (255, 230, 230, 120))

def gold_aura(sk, col, seed, alpha=130):
    """A gentle aura: soft wisps rising along the edges (no flames)."""
    rnd = random.Random(seed)
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge in (0, fw - 1):
                y = fh - 1
                while y > 2:
                    h = rnd.randint(2, 4)
                    sk.line(p, side, [(edge, y), (edge, y - h)], col + (alpha,))
                    y -= h + rnd.randint(2, 4)

@design("saiyan_ssj", "Saiyan: Super Saiyan", "full")
def _(sk):
    """Super Saiyan: blazing gold hair with bright roots and glow pixels on the edges, teal
    eyes under sharp angled brows, an intense focused look, a soft golden rim light and
    gentle golden aura wisps along the body."""
    GOLD = (255, 212, 60)
    TEAL = (40, 200, 190)
    saiyan_body(sk, 820)
    saiyan_hair_paint(sk, GOLD, glow=(255, 250, 200))
    for side in ("left", "right", "back"):                                     # bright roots near the scalp
        sk.line("head", side, [(0, 1), (15, 1)], (255, 246, 180))
    saiyan_face(sk, "intense", eye=TEAL)
    # sharper intense brows (single line, angled), slight squint
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 7, x0 + 2, 7, (40, 30, 24, 255))
    sk.line("head", "front", [(2, 5), (6, 7)], (196, 150, 40)); sk.line("head", "front", [(13, 5), (9, 7)], (196, 150, 40))   # golden brows
    rim_light(sk, (255, 220, 90), alpha=150)
    gold_aura(sk, (255, 226, 110), 821)

def hair_glow_edges(sk, col, alpha=170):
    """Glow pixels along the hair's lower edges and hairline (head sides/back/front)."""
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        for x in range(0, 16, 3):
            sk.rect("head", side, x, rows + 2, x + 1, rows + 2, col + (alpha,))
        sk.line("head", side, [(0, 1), (15, 1)], col + (alpha // 2,))
    for x in range(0, 16, 2):
        sk.rect("head", "front", x, 5, x, 5, col + (alpha // 2,))

@design("saiyan_ssj", "Saiyan: Super Saiyan", "full")
def _(sk):
    """Super Saiyan: bright gold hair with lit strands and soft gold glow on its edges, teal
    eyes, intense focused face, faint gold aura outline and gold light on the trim."""
    GOLD, GLOW, TEAL = (255, 212, 64), (255, 236, 140), (40, 200, 190)
    saiyan_body(sk, 820)
    saiyan_hair_paint(sk, GOLD)
    hair_glow_edges(sk, GLOW)
    saiyan_face(sk, "intense", eye=TEAL, brow_col=(176, 122, 28))
    for x0 in (3, 10):                                                       # teal irises with a lit rim
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 9, ix + 1, 9, (20, 120, 116, 255))
    # gold aura: soft outline on body edges (not the head) + gold light on the trim
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(0, 0), (0, fh - 1)], GLOW + (130,))
            sk.line(p, side, [(fw - 1, 0), (fw - 1, fh - 1)], GLOW + (130,))
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 6), (7, 6)], GLOW)

def sparks(sk, seed, col=(170, 230, 255), n=2, parts=None):
    """Small zig-zag electric sparks with a bright core."""
    rnd = random.Random(seed)
    for p in parts or [pp for pp in PARTS if pp != "head"]:
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(n):
                x, y = rnd.randrange(1, fw - 3), rnd.randrange(1, fh - 4)
                pts = [(x, y), (x + 1, y + 1), (x, y + 2), (x + 1, y + 3)]        # small crisp zig-zag
                sk.line(p, side, pts, col + (255,))
                sk.rect(p, side, x, y, x, y, (255, 255, 255, 255))

@design("saiyan_ssj2", "Saiyan: Super Saiyan 2", "full")
def _(sk):
    """Super Saiyan 2: brighter, stiffer gold hair with sharper jagged edges and stronger glow,
    crackling electric sparks over the body, a stronger gold aura, narrowed teal eyes and a
    hard, cold expression."""
    GOLD, GLOW, TEAL = (255, 222, 84), (255, 244, 170), (36, 214, 200)
    saiyan_body(sk, 830)
    saiyan_hair_paint(sk, GOLD)
    for side in ("left", "right", "back"):                                   # sharper, longer jagged edge
        rows = 14 if side == "back" else 8
        for x in range(1, 16, 3):
            sk.line("head", side, [(x, rows), (x, rows + 3)], ramp(GOLD)[1])
            sk.rect("head", side, x, rows + 3, x, rows + 3, GLOW + (220,))
    hair_glow_edges(sk, GLOW, alpha=210)
    # face: narrowed eyes, hard brows, tight jaw
    saiyan_face(sk, "intense", eye=TEAL, brow_col=(176, 122, 28))
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 7, x0 + 2, 7, (176, 122, 28, 255))      # heavier upper lids: narrowed
        sk.rect("head", "front", x0, 9, x0 + 2, 9, ramp(SKIN_S)[2] + (255,))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 8, TEAL + (255,))
        sk.rect("head", "front", ix, 8, ix, 8, (255, 255, 255, 255))
    sk.rect("head", "front", 5, 12, 10, 13, ramp(SKIN_S)[1] + (255,))         # tight closed jaw
    sk.line("head", "front", [(5, 12), (10, 12)], (120, 70, 56))
    sk.line("head", "front", [(3, 14), (5, 15)], ramp(SKIN_S)[2]); sk.line("head", "front", [(12, 14), (10, 15)], ramp(SKIN_S)[2])
    # stronger aura + electricity
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(0, 0), (0, fh - 1)], GLOW + (190,)); sk.line(p, side, [(1, 0), (1, fh - 1)], GLOW + (70,))
            sk.line(p, side, [(fw - 1, 0), (fw - 1, fh - 1)], GLOW + (190,)); sk.line(p, side, [(fw - 2, 0), (fw - 2, fh - 1)], GLOW + (70,))
    sparks(sk, 832, col=(120, 210, 255), n=1)
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 6), (7, 6)], GLOW)

@design("saiyan_ssj3", "Saiyan: Super Saiyan 3", "full")
def _(sk):
    """Super Saiyan 3: long gold hair painted down the back of the head and over the upper back
    (matching the mane model), no eyebrows with a heavy brow ridge, intense teal eyes, a
    two-layer gold aura with sparks."""
    GOLD, GLOW, TEAL = (255, 214, 66), (255, 240, 150), (34, 210, 196)
    g = ramp(GOLD)
    saiyan_body(sk, 840)
    saiyan_hair_paint(sk, GOLD)
    sk.fill("head", ("back",), g[1], shade=0.06, seed=841)                  # back of the head fully hair
    for x in range(0, 16, 2):
        sk.line("head", "back", [(x, 0), (x + 1, 15)], g[2])
        sk.rect("head", "back", x, 2, x, 6, g[0] + (255,))
    # long mane over the upper back: strands to mid-back with pointed ends
    for x in range(0, 16, 2):
        end = 12 + (x * 7) % 5
        sk.rect("body", "back", x, 0, x + 1, end, g[1] + (255,))
        sk.line("body", "back", [(x, 0), (x, end)], g[2])
        sk.rect("body", "back", x + 1, 1, x + 1, 5, g[0] + (255,))
        sk.rect("body", "back", x, end + 1, x, end + 1, GLOW + (200,))
    for side in ("left", "right"):                                          # strands over the shoulder backs
        sk.rect("body", side, 2, 0, 3, 8, g[1] + (255,)); sk.line("body", side, [(2, 0), (2, 8)], g[2])
    hair_glow_edges(sk, GLOW, alpha=210)
    saiyan_face(sk, "intense", eye=TEAL, brows=False)
    # heavier brow ridge: deep shadow band and a lit ridge line above the eyes
    for x0 in (2, 9):                                                        # ridge over each eye only
        sk.line("head", "front", [(x0, 6), (x0 + 4, 6)], ramp(SKIN_S)[3])
        sk.line("head", "front", [(x0 + 1, 5), (x0 + 3, 5)], ramp(SKIN_S)[0])
    sk.rect("head", "front", 7, 6, 8, 7, ramp(SKIN_S)[2] + (255,))
    for x0 in (3, 10):
        sk.rect("head", "front", x0 - 1, 7, x0 + 3, 7, ramp(SKIN_S)[3] + (255,))
    # two-layer gold aura with sparks
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for xx, a in ((0, 210), (1, 90), (fw - 1, 210), (fw - 2, 90)):
                sk.line(p, side, [(xx, 0), (xx, fh - 1)], GLOW + (a,))
    sparks(sk, 842, col=(255, 236, 140), n=1)
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 6), (7, 6)], GLOW)

def fur(sk, part, side, col, rows=None, x0=0, x1=None, seed=0):
    """Crimson fur: base fill with short downward strand marks in 4 tones."""
    hi, base, sh, deep = ramp(col)
    _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
    y0, y1 = (rows[0] * 2, rows[1] * 2) if rows else (0, fh)
    x1 = fw - 1 if x1 is None else x1
    sk.rect(part, side, x0, y0, x1, y1 - 1, base + (255,))
    rnd = random.Random(seed)
    for _ in range((x1 - x0 + 1) * (y1 - y0) // 6):
        x, y = rnd.randint(x0, x1), rnd.randint(y0, max(y0, y1 - 3))
        c = rnd.choice((hi, sh, sh, deep))
        sk.line(part, side, [(x, y), (x + rnd.choice((-1, 0, 0, 1)), y + 2)], c)

def fur_tufts(sk, part, side, col, x0, y0, x1, y1, seed):
    """Layered fur: base, then rows of downward V-tufts (lit tip, shadow beneath)."""
    hi, base, sh, deep = ramp(col)
    sk.rect(part, side, x0, y0, x1, y1, sh + (255,))
    rnd = random.Random(seed)
    for row, y in enumerate(range(y0, y1 + 1, 3)):
        off = (row % 2) * 2
        for x in range(x0 + off - 2, x1 + 1, 4):
            for dx, dy in ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
                xx, yy = x + dx, y + dy
                if x0 <= xx <= x1 and y0 <= yy <= y1:
                    c = base if dy < 2 else sh
                    sk.rect(part, side, xx, yy, xx, yy, c + (255,))
            if x0 <= x + 1 <= x1 and y0 <= y <= y1:
                sk.rect(part, side, x + 1, y, x + 1, y, hi + (255,))         # lit tip
            if x0 <= x + 1 <= x1 and y0 <= y + 3 <= y1:
                sk.rect(part, side, x + 1, y + 3, x + 1, y + 3, deep + (255,))  # shadow under the tuft
        if rnd.random() < 0.5 and x1 - x0 > 4:
            xx = rnd.randint(x0, x1)
            sk.rect(part, side, xx, y, xx, y, hi + (255,))

@design("saiyan_ssj4", "Saiyan: Super Saiyan 4", "full")
def _(sk):
    """Super Saiyan 4 (v2, original warrior): layered crimson fur tufts over shoulders, arms, back
    and sides with a fur collar, jagged tufts framing a heavily muscled bare chest with rim light,
    a fur ridge down the back, wild black hair breaking over the face, a fierce scowl with narrowed
    amber eyes, a bold swept red outline and bared teeth; crimson wristbands, teal trousers, gold sash."""
    FUR, HAIR4, AMBER = (186, 32, 44), (24, 20, 26), (250, 184, 36)
    f_hi, f_base, f_sh, f_deep = ramp(FUR)
    s_hi, s_base, s_sh, s_deep = ramp(SKIN_S)
    saiyan_body(sk, 850)
    # ---- bare muscled chest (v3: fully sculpted) ------------------------------------------
    S0, S1, S2, S3, S4, S5 = (255, 232, 200), (246, 206, 168), s_base, tuple(int(v * 0.9) for v in s_base), s_sh, s_deep
    def px(x, y, c):
        sk.rect("body", "front", x, y, x, y, c + (255,))
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for y in range(0, 16):
            t = y / 15
            sk.rect("body", side, 0, y, fw - 1, y, tuple(int(s_base[k] * (1.04 - 0.12 * t)) for k in range(3)) + (255,))
    sk.fill("body", ("top",), s_base)
    # traps / collarbones
    for x in range(4, 12):
        px(x, 0, S3)
    for x in (4, 5, 10, 11):
        px(x, 1, S4)
    # pecs: x 4-7 (right) and 8-11 (left); rows 1..7, lit top-outer, curved deep shadow at the bottom
    for x0, x1, outer in ((4, 7, 4), (8, 11, 11)):
        for y in range(2, 7):
            for x in range(x0, x1 + 1):
                c = S2
                if y == 2: c = S0 if x != (x1 if outer == x0 else x0) else S1
                elif y == 3: c = S1
                elif y == 5: c = S3
                elif y == 6: c = S4
                px(x, y, c)
        for x in range(x0, x1 + 1):
            px(x, 7, S5 if x != outer else S4)                               # curved underside
        px(outer, 6, S5)
    for y in range(1, 8):                                                      # sternum
        px(7, y, S4); px(8, y, S3)
    # abs: chunky rounded blocks, 3 rows tall (lit top, solid middle, soft shaded bottom)
    for y0 in (8, 11):
        for x0, x1 in ((4, 6), (9, 11)):
            for x in range(x0, x1 + 1):
                px(x, y0, S1); px(x, y0 + 1, S2); px(x, y0 + 2, S3)
            px(x0, y0, S0)                                                     # shine on the top corner
    for x0, x1 in ((4, 6), (9, 11)):                                          # lower abs into the sash
        for x in range(x0, x1 + 1):
            px(x, 14, S2); px(x, 15, S3)
    for y in range(8, 16):
        px(7, y, S4); px(8, y, S4)                                             # linea alba
    # serratus (finger-like shading under the pecs at the sides) and obliques
    for y in (8, 10, 12):
        px(4, y, S4); px(4, y + 1, S2); px(11, y, S4); px(11, y + 1, S2)
    # V-lines into the sash
    px(5, 14, S4); px(6, 15, S4); px(10, 14, S4); px(9, 15, S4)
    # warm rim light along the top of the pecs and shoulders
    sk.line("body", "front", [(4, 2), (6, 1)], (255, 236, 210)); sk.line("body", "front", [(9, 1), (11, 2)], (255, 236, 210))
    # back: muscle shading (lats/spine) under the fur, visible below the fur line handled by fur pass
    # ---- fur: back, sides, chest frame, collar, shoulders/arms --------------------------------
    fur_tufts(sk, "body", "back", FUR, 0, 0, 15, 15, 860)
    for y in range(1, 15, 2):                                                # fur ridge down the spine
        sk.rect("body", "back", 7, y, 8, y, f_hi + (255,)); sk.rect("body", "back", 7, y + 1, 8, y + 1, f_deep + (255,))
    for side in ("left", "right"):
        fur_tufts(sk, "body", side, FUR, 0, 0, 7, 15, 861 + len(side))
    fur_tufts(sk, "body", "front", FUR, 0, 0, 2, 15, 863); fur_tufts(sk, "body", "front", FUR, 13, 0, 15, 15, 864)
    sk.line("body", "front", [(3, 0), (3, 15)], f_deep); sk.line("body", "front", [(12, 0), (12, 15)], f_deep)   # clean fur border
    for x in range(3, 13, 2):                                                # fur collar at the neck
        sk.rect("body", "front", x, 0, x, 0, f_base + (255,))
    sk.rect("body", "front", 6, 0, 9, 0, s_sh + (255,))
    for arm in ARMS:
        sk.fill(arm, ("top",), f_base)
        for side in SIDES:
            fur_tufts(sk, arm, side, FUR, 0, 0, 7, 16, 870 + len(side) + len(arm))
            # deltoid: rounded lit cap
            sk.rect(arm, side, 1, 0, 6, 1, f_hi + (230,)); sk.rect(arm, side, 0, 3, 7, 3, f_deep + (200,))
            if side in ("front", "back"):
                # bicep (front) / tricep (back): a bulge with a lit centre and shadow beneath
                sk.rect(arm, side, 2, 5, 5, 8, f_base + (255,)); sk.rect(arm, side, 3, 5, 4, 6, f_hi + (255,))
                sk.rect(arm, side, 1, 9, 6, 9, f_deep + (255,))
                # forearm swell
                sk.rect(arm, side, 2, 11, 5, 14, f_base + (255,)); sk.rect(arm, side, 3, 11, 3, 12, f_hi + (255,))
                sk.line(arm, side, [(1, 15), (6, 16)], f_deep)
            else:
                sk.line(arm, side, [(3, 4), (4, 9)], f_deep); sk.line(arm, side, [(2, 11), (3, 15)], f_sh)
            sk.rect(arm, side, 0, 17, 7, 21, ramp((110, 16, 26))[1] + (255,))
            sk.rect(arm, side, 0, 17, 7, 17, ramp((110, 16, 26))[0] + (255,)); sk.rect(arm, side, 0, 21, 7, 21, ramp((110, 16, 26))[3] + (255,))
            sk.line(arm, side, [(0, 19), (7, 19)], ramp((110, 16, 26))[2])
    # ---- wild black hair ----------------------------------------------------------------------------
    saiyan_hair_paint(sk, HAIR4)
    h = ramp(HAIR4)
    sk.fill("head", ("back",), h[1], shade=0.08, seed=856)
    for x in range(0, 16, 2):
        sk.line("head", "back", [(x, 0), (x + 1, 15)], h[2]); sk.rect("head", "back", x, 2, x, 5, (64, 60, 76, 255))
    for x in range(0, 16, 2):                                                # long strands over the upper back fur
        end = 9 + (x * 5) % 6
        sk.rect("body", "back", x, 0, x + 1, end, h[1] + (255,))
        sk.line("body", "back", [(x, 0), (x, end)], h[2]); sk.rect("body", "back", x + 1, 1, x + 1, 4, (64, 60, 76, 255))
    for x, depth in ((0, 7), (1, 6), (14, 7), (15, 6)):                      # tufts breaking over the face edges
        sk.line("head", "front", [(x, 4), (x, depth)], h[1])
    # ---- fierce face ---------------------------------------------------------------------------------
    ink = (24, 18, 22)
    for x0 in (2, 9):
        sk.rect("head", "front", x0, 7, x0 + 4, 10, s_sh + (255,))            # deep sockets
    sk.line("head", "front", [(1, 4), (6, 7)], ink); sk.line("head", "front", [(2, 4), (6, 6)], ink)
    sk.line("head", "front", [(14, 4), (9, 7)], ink); sk.line("head", "front", [(13, 4), (9, 6)], ink)
    sk.rect("head", "front", 7, 5, 8, 6, s_deep + (255,))                    # scowl crease
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (246, 236, 220, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, AMBER + (255,))
        sk.rect("head", "front", ix + (1 if x0 == 3 else 0), 8, ix + (1 if x0 == 3 else 0), 9, (60, 26, 8, 255))   # pupil
        sk.rect("head", "front", ix, 8, ix, 8, (255, 250, 220, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))              # narrowed upper lid
        sk.rect("head", "front", x0, 10, x0 + 2, 10, (180, 24, 36, 255))       # bold red lower outline
        outer = x0 - 1 if x0 == 3 else x0 + 3
        sk.rect("head", "front", outer, 7, outer, 10, (180, 24, 36, 255))     # swept outer corner
        sk.rect("head", "front", outer - 1 if x0 == 3 else outer + 1, 6, outer - 1 if x0 == 3 else outer + 1, 7, (150, 18, 30, 255))
    sk.rect("head", "front", 7, 10, 8, 11, s_sh + (255,))
    sk.line("head", "front", [(1, 11), (4, 13)], s_deep); sk.line("head", "front", [(14, 11), (11, 13)], s_deep)
    sk.rect("head", "front", 4, 12, 11, 14, (58, 14, 16, 255))                # bared teeth
    sk.rect("head", "front", 5, 12, 10, 13, (248, 242, 232, 255))
    for x in (6, 8, 10):
        sk.rect("head", "front", x, 12, x, 13, (190, 178, 170, 255))
    sk.rect("head", "front", 5, 13, 5, 13, (255, 255, 255, 255)); sk.rect("head", "front", 10, 13, 10, 13, (255, 255, 255, 255))   # canines
    sk.line("head", "front", [(3, 11), (4, 12)], ink); sk.line("head", "front", [(12, 10), (11, 12)], ink)
    for side in ("left", "right"):
        fur_tufts(sk, "head", side, FUR, 0, 12, 15, 15, 880 + len(side))       # sideburn fur at the jaw
    # ---- v3 detail pass -------------------------------------------------------------------------
    F5 = [tuple(min(255, int(v * k)) for v in FUR) for k in (1.35, 1.15, 1.0, 0.8, 0.6)]
    rnd = random.Random(890)
    # flowing fur strokes: down and slightly outward, 5 tones, glossy highlights
    for part, sides_ in (("body", ("left", "right")),) + tuple((arm, SIDES) for arm in ARMS):   # not the back: the mane covers it
        for side in sides_:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            ymax = 15 if part == "body" else 16
            for _ in range(fw * ymax // 3):
                x, y = rnd.randrange(0, fw), rnd.randrange(0, ymax - 2)
                lean = 1 if x > fw // 2 else -1
                c = F5[rnd.choice((0, 1, 2, 2, 3, 3, 4))]
                sk.line(part, side, [(x, y), (x + lean * rnd.choice((0, 1)), y + 2)], c)
            for _ in range(3):                                                 # glossy sheen streaks
                x, y = rnd.randrange(1, fw - 2), rnd.randrange(0, ymax - 4)
                sk.line(part, side, [(x, y), (x + 1, y + 3)], (255, 150, 150, 160))
    # jagged fur ends over the sash (body) and above the wristbands (arms)
    for side in ("back", "left", "right"):
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for x in range(0, fw, 2):
            sk.rect("body", side, x, 15, x, 15 + (x * 3) % 3, F5[3] + (255,))
            sk.rect("body", side, x, 15, x, 15, F5[1] + (255,))
    for arm in ARMS:
        for side in SIDES:
            for x in range(0, 8, 2):
                sk.rect(arm, side, x, 16, x, 16 + (x % 4) // 2, F5[3] + (255,))
    # chest: collarbones, neck tendons, two pale battle scars, stronger rim light
    sk.line("body", "front", [(4, 1), (7, 2)], s_sh); sk.line("body", "front", [(11, 1), (8, 2)], s_sh)
    sk.line("body", "front", [(6, 0), (7, 1)], s_deep); sk.line("body", "front", [(9, 0), (8, 1)], s_deep)
    sk.line("body", "front", [(9, 4), (11, 7)], (240, 206, 186)); sk.line("body", "front", [(10, 4), (12, 7)], s_sh)
    sk.line("body", "front", [(5, 10), (6, 12)], (240, 206, 186))
    sk.line("body", "front", [(4, 2), (4, 6)], (255, 226, 196)); sk.line("body", "front", [(11, 2), (11, 6)], (255, 226, 196))
    # face: iris rings, catch-lights, nose bridge, cheekbones, lip line, chin cleft
    for x0 in (3, 10):
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 9, ix + 1, 9, (190, 120, 20, 255))            # darker lower iris ring
        sk.rect("head", "front", ix + 1 if x0 == 3 else ix, 8, ix + 1 if x0 == 3 else ix, 8, (255, 255, 255, 255))
    sk.line("head", "front", [(2, 10), (4, 10)], s_hi); sk.line("head", "front", [(11, 10), (13, 10)], s_hi)
    sk.line("head", "front", [(5, 14), (10, 14)], (150, 80, 66))
    sk.rect("head", "front", 7, 15, 8, 15, s_deep + (255,))
    # hair: finer strand highlights on the back mane and head
    for x in range(1, 16, 2):
        sk.line("head", "back", [(x, 6), (x, 13)], (70, 66, 84))
        sk.line("body", "back", [(x, 5), (x, 8)], (62, 58, 74))
    # trousers: extra folds; sash tassels; laced boots
    for leg in LEGS:
        for side in ("front", "back"):
            sk.line(leg, side, [(1, 3), (2, 6)], ramp(SGI)[3]); sk.line(leg, side, [(5, 5), (6, 9)], ramp(SGI)[3])
        for y in (17, 19):                                                     # thin criss-cross laces
            sk.rect(leg, "front", 2, y, 2, y, (120, 118, 126, 255)); sk.rect(leg, "front", 5, y, 5, y, (120, 118, 126, 255))
            sk.rect(leg, "front", 3, y + 1, 4, y + 1, (120, 118, 126, 255))
    for x in (9, 12):
        sk.line("body", "front", [(x, 20), (x, 23)], ramp(SSASH)[0])
        sk.rect("body", "front", x, 23, x, 23, ramp(SSASH)[2] + (255,))
    # ---- muscle pass (v6): deeper pecs, delt-pec cut, lit abs, neck, triceps, lats, legs --------
    def soft_px(part, side, x, y, k):
        _, base_, _, _ = ramp(SKIN_S)
        sk.rect(part, side, x, y, x, y, tuple(max(0, min(255, int(v * k))) for v in base_) + (255,))
    for x0, x1 in ((4, 7), (8, 11)):                                          # pecs: 3-tone depth
        for x in range(x0, x1 + 1):
            soft_px("body", "front", x, 3, 1.08); soft_px("body", "front", x, 4, 1.0); soft_px("body", "front", x, 5, 0.93)
    for y in range(1, 5):                                                     # delt-pec cut at the shoulders
        soft_px("body", "front", 4, y, 0.86); soft_px("body", "front", 11, y, 0.86)
    for y in (8, 10, 12):                                                     # lit centre on each ab block
        soft_px("body", "front", 5, y, 1.1); soft_px("body", "front", 10, y, 1.1)
    soft_px("body", "front", 7, 15, 0.84); soft_px("body", "front", 8, 15, 0.84)   # navel
    for side in ("left", "right"):                                            # neck muscles on the jaw sides
        sk.line("head", side, [(4, 15), (8, 12)], tuple(int(v * 0.9) for v in s_base))
        sk.line("head", side, [(5, 15), (9, 12)], tuple(min(255, int(v * 1.06)) for v in s_base))
    for arm in ARMS:                                                          # tricep horseshoe (back of arm, under the fur)
        sk.line(arm, "back", [(2, 6), (2, 10), (5, 10), (5, 6)], f_deep)
        sk.line(arm, "back", [(3, 7), (4, 7)], f_hi)
    for side in ("left", "right"):                                            # lats taper the torso into a V
        sk.line("body", side, [(1, 2), (2, 14)], f_deep); sk.line("body", side, [(6, 2), (5, 14)], f_deep)
        sk.line("body", side, [(3, 3), (4, 12)], f_hi)
    g = ramp(SGI)
    for leg in LEGS:                                                          # quads, knee and calf through the trousers
        sk.line(leg, "front", [(1, 2), (2, 8), (3, 10)], g[3]); sk.line(leg, "front", [(6, 2), (5, 8), (4, 10)], g[3])
        sk.line(leg, "front", [(3, 3), (4, 7)], g[0])
        sk.rect(leg, "front", 2, 11, 5, 11, g[0] + (255,)); sk.rect(leg, "front", 2, 12, 5, 12, g[3] + (255,))   # knee
        sk.line(leg, "back", [(2, 9), (1, 12), (2, 14)], g[3]); sk.line(leg, "back", [(5, 9), (6, 12), (5, 14)], g[3])  # calf
        sk.line(leg, "back", [(3, 10), (4, 12)], g[0])
    # ---- final face (v5): the user's chosen face (the earlier smirk), with subtle detail ---------
    for y in range(5, 16):                                                    # clean skin below the fringe
        t = (y - 5) / 10
        sk.rect("head", "front", 0, y, 15, y, tuple(int(s_base[k] * (1.03 - 0.08 * t)) for k in range(3)) + (255,))
    saiyan_face(sk, "smirk", eye=AMBER)                                       # same base face as the reference
    soft = tuple(int(v * 0.9) for v in s_base)                                 # gentle shades: no banding
    for x0 in (3, 10):                                                         # slim red outline (as in the reference)
        sk.rect("head", "front", x0, 10, x0 + 2, 10, (176, 24, 36, 255))
        outer = x0 - 1 if x0 == 3 else x0 + 3
        sk.rect("head", "front", outer, 8, outer, 9, (150, 20, 30, 255))
        sk.rect("head", "front", outer, 7, outer, 7, (120, 18, 28, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 9, ix + 1, 9, (200, 128, 24, 255))         # darker lower iris
        sk.rect("head", "front", ix, 8, ix, 8, (255, 252, 232, 255))           # catch-light
    sk.line("head", "front", [(1, 5), (6, 6)], (24, 20, 24)); sk.line("head", "front", [(14, 5), (9, 6)], (24, 20, 24))   # black slanted brows
    sk.rect("head", "front", 7, 8, 7, 9, tuple(min(255, int(v * 1.06)) for v in s_base) + (255,))   # soft nose bridge
    sk.rect("head", "front", 1, 11, 2, 11, soft + (255,)); sk.rect("head", "front", 13, 11, 14, 11, soft + (255,))   # cheekbones
    sk.rect("head", "front", 6, 14, 8, 14, tuple(min(255, int(v * 1.05)) for v in s_base) + (255,))  # lower-lip highlight
    sk.rect("head", "front", 6, 15, 9, 15, soft + (255,))                     # soft chin
    for x in (0, 15):
        sk.rect("head", "front", x, 5, x, 6, ramp(HAIR4)[1] + (255,))         # hair at the temples
    # ---- v6 muscle pass: stronger chest, sculpted fur arms, quads/calves, neck --------------
    def px(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    deepest = tuple(int(v * 0.62) for v in s_base)
    lit = (255, 230, 198)
    # chest: double-depth pec shadow, rounded highlights on abs, stronger obliques
    for x in range(4, 12):
        if x not in (7, 8):
            px("body", "front", x, 7, deepest)
    for x0 in (4, 9):
        px("body", "front", x0, 3, lit); px("body", "front", x0 + 1, 2, lit)  # pec highlight cores
    for y in (8, 11):
        for x in (4, 9):
            px("body", "front", x, y, lit)                                    # top-left shine on each ab block
    sk.line("body", "front", [(4, 8), (4, 14)], s_sh); sk.line("body", "front", [(11, 8), (11, 14)], s_sh)   # smooth obliques
    # neck muscles on the sides of the head (lower area)
    for side in ("left", "right"):
        sk.line("head", side, [(9, 13), (13, 15)], s_sh); sk.line("head", side, [(8, 14), (11, 15)], lit[:3])
    # arms: heavier sculpting in the fur
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 2, 0, 5, 1, f_hi + (120,))                      # deltoid highlight, blended into the fur
        sk.rect(arm, "front", 2, 4, 5, 8, f_base + (255,))                    # bicep peak
        sk.rect(arm, "front", 3, 4, 4, 5, (255, 150, 150, 230))
        sk.line(arm, "front", [(1, 9), (6, 9)], f_deep); sk.line(arm, "front", [(1, 8), (1, 5)], f_sh)
        sk.line(arm, "back", [(2, 4), (2, 8), (5, 8), (5, 4)], f_deep)        # tricep horseshoe
        sk.rect(arm, "back", 3, 5, 4, 7, f_hi + (230,))
        for side in ("front", "back"):
            sk.rect(arm, side, 2, 11, 5, 15, f_base + (255,))                 # forearm swell
            sk.line(arm, side, [(2, 11), (2, 14)], f_hi); sk.line(arm, side, [(5, 12), (5, 15)], f_deep)
    # legs: quads and calves through the trousers
    g = ramp(SGI)
    for leg in LEGS:
        sk.rect(leg, "front", 2, 2, 5, 7, g[0] + (180,))                     # quad sweep
        sk.line(leg, "front", [(1, 8), (3, 9), (6, 8)], g[3])                 # above the knee
        sk.line(leg, "front", [(4, 2), (4, 7)], g[2])                         # quad split
        sk.rect(leg, "back", 2, 10, 5, 13, g[0] + (150,))                    # calf
        sk.line(leg, "back", [(2, 14), (5, 14)], g[3])
    # ---- v7 full detail pass ----------------------------------------------------------------
    F = [tuple(min(255, int(v * k)) for v in FUR) for k in (1.4, 1.18, 1.0, 0.78, 0.55, 0.4)]
    rnd = random.Random(900)
    # fur clumps flowing down-and-out with lit tips and dark undercoat gaps
    for part, sides_, ymax in (("body", ("left", "right", "back"), 15),) + tuple((arm, SIDES, 16) for arm in ARMS):
        for side in sides_:
            _, _, fw, _ = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for cy in range(0, ymax, 4):
                for cx in range((cy // 4) % 2 * 2, fw, 4):
                    lean = 1 if cx >= fw // 2 else -1
                    sk.line(part, side, [(cx, cy), (cx + lean, cy + 3)], F[4])          # gap/undercoat
                    sk.line(part, side, [(cx + 1, cy), (cx + 1 + lean, cy + 3)], F[1])  # clump body
                    sk.rect(part, side, cx + 1, cy, cx + 1, cy, F[0] + (255,))        # rim-lit tip
    # shoulder blades and spine shaped into the back fur (under the mane's ends)
    sk.line("body", "back", [(2, 4), (5, 7), (6, 11)], F[5]); sk.line("body", "back", [(13, 4), (10, 7), (9, 11)], F[5])
    sk.line("body", "back", [(3, 4), (5, 6)], F[0]); sk.line("body", "back", [(12, 4), (10, 6)], F[0])
    # hands: fingers and knuckles (bottom face + lowest rows of the arms)
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 22, 7, 23, s_base + (255,))
            for x in (1, 3, 5):
                sk.line(arm, side, [(x, 22), (x, 23)], s_sh)
            sk.rect(arm, side, 0, 22, 7, 22, s_hi + (255,))
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=s_base + (255,))
        for kx in range(1, fw, 2):
            sk.d.line((x + kx, y, x + kx, y + fh - 1), fill=s_sh + (255,))
        # stitched wristbands with gold studs
        for side in SIDES:
            for xx in range(0, 8, 2):
                sk.rect(arm, side, xx, 18, xx, 18, (150, 60, 64, 255))
            for xx in (1, 4, 6):
                sk.rect(arm, side, xx, 20, xx, 20, (250, 210, 90, 255))
    # sash: woven texture, folded knot, fringed tassels
    t = ramp(SSASH)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for xx in range(0, fw, 2):
            sk.rect("body", side, xx, 17, xx, 17, t[2] + (255,)); sk.rect("body", side, xx + 1, 18, xx + 1, 18, t[0] + (255,))
    sk.rect("body", "front", 9, 16, 12, 19, t[1] + (255,)); sk.line("body", "front", [(9, 16), (12, 19)], t[3])
    sk.line("body", "front", [(10, 16), (12, 18)], t[0])
    for xx in (9, 10, 11, 12, 13):
        sk.line("body", "front", [(xx, 20), (xx, 22 + xx % 2)], t[1 if xx % 2 else 2])
    # trousers: stitched seams, deep folds, knee crease, wrapped ankles
    g = ramp(SGI)
    for leg in LEGS:
        for side in SIDES:
            stitch(sk, leg, side, 4 if side in ("left", "right") else 0, 1, 4 if side in ("left", "right") else 0, 13, g[0])
            sk.line(leg, side, [(1, 2), (2, 6), (1, 9)], g[3]); sk.line(leg, side, [(6, 3), (5, 8)], g[3])
            sk.line(leg, side, [(2, 10), (4, 11), (6, 10)], g[3])
            for yy in (13, 15):
                sk.line(leg, side, [(0, yy), (7, yy + 1)], ramp((220, 210, 190))[1])       # ankle wraps
    # boots: lit toe, buckled straps, treaded soles
    b6 = ramp(SBOOT)
    for leg in LEGS:
        sk.rect(leg, "front", 1, 20, 6, 21, b6[0] + (255,))
        for side in SIDES:
            sk.rect(leg, side, 0, 18, 7, 18, (150, 120, 60, 255)); sk.rect(leg, side, 3, 18, 4, 18, (250, 214, 100, 255))
            for xx in range(0, 8, 2):
                sk.rect(leg, side, xx, 23, xx, 23, (18, 18, 22, 255))
    # hair: strand highlights on the head and the long back strands
    for xx in range(1, 16, 3):
        sk.line("head", "back", [(xx, 1), (xx, 12)], (82, 78, 98))
        sk.line("head", "top", [(xx, 1), (xx + 1, 14)], (70, 66, 84))
    # ---- v7 detailed abs (hand-placed pixels, body front x 4-11, rows 8-15) -----------------
    AB = {"L": (255, 236, 206), "H": (248, 214, 178), "B": s_base, "M": tuple(int(v * 0.93) for v in s_base),
          "S": tuple(int(v * 0.84) for v in s_base), "D": tuple(int(v * 0.72) for v in s_base), "G": tuple(int(v * 0.9) for v in s_base)}
    # one 3x3 block: rounded corners (M), lit core (L/H), shaded lower-right (S/D)
    BLOCK_R = ["MHM",
               "HLB",
               "MSD"]
    BLOCK_L = ["MHM",
               "BLH",
               "DSM"]
    def stamp(x0, y0, pat):
        for dy, row in enumerate(pat):
            for dx, ch in enumerate(row):
                c = AB[ch]
                sk.rect("body", "front", x0 + dx, y0 + dy, x0 + dx, y0 + dy, c + (255,))
    for y0 in (8, 11):                                                        # two rows of full blocks
        stamp(4, y0, BLOCK_R); stamp(9, y0, BLOCK_L)
    for x0, pat in ((4, ["HBM", "MSS"]), (9, ["MBH", "SSM"])):               # lower abs tapering down
        for dy, row in enumerate(pat):
            for dx, ch in enumerate(row):
                sk.rect("body", "front", x0 + dx, 14 + dy, x0 + dx, 14 + dy, AB[ch] + (255,))
    for y in range(8, 16):                                                     # linea alba: soft centre groove
        sk.rect("body", "front", 7, y, 7, y, AB["S"] + (255,)); sk.rect("body", "front", 8, y, 8, y, AB["G"] + (255,))
    sk.rect("body", "front", 7, 13, 8, 13, AB["D"] + (255,))                   # navel
    sk.rect("body", "front", 7, 12, 8, 12, AB["M"] + (255,))
    sk.rect("body", "front", 5, 15, 5, 15, AB["S"] + (255,)); sk.rect("body", "front", 10, 15, 10, 15, AB["S"] + (255,))   # V-lines
    # ---- v7 chest: wider bare chest with clearly outlined pecs and six-pack ------------------
    B = s_base
    def sh(k):
        return tuple(max(0, min(255, int(v * k))) for v in B)
    L1, L0, M, D1, D2, D3 = sh(1.1), (255, 236, 206), B, sh(0.87), sh(0.75), sh(0.6)
    def P(x, y, c):
        sk.rect("body", "front", x, y, x, y, c + (255,))
    # base: soft top-lit gradient over x 2..13, rows 0..15
    for y in range(0, 16):
        for x in range(2, 14):
            P(x, y, sh(1.05 - 0.1 * y / 15))
    # fur pulled back to the outer edges, with a dark border
    fur_tufts(sk, "body", "front", FUR, 0, 0, 1, 15, 901); fur_tufts(sk, "body", "front", FUR, 14, 0, 15, 15, 902)
    for y in range(0, 16):
        P(2, y, D2); P(13, y, D2)
    # collarbones / traps
    for x in range(3, 13):
        P(x, 0, D1)
    P(4, 1, L1); P(5, 1, L1); P(10, 1, L1); P(11, 1, L1)
    # pecs: x 3-7 and 8-12, rows 1-6, lit upper edge, curved dark underside
    for x0, x1 in ((3, 7), (8, 12)):
        for x in range(x0, x1 + 1):
            P(x, 2, L1); P(x, 3, M); P(x, 4, M); P(x, 5, M)
        P(x0 + 1, 2, L0); P(x0 + 2, 2, L0) if x0 == 3 else P(x1 - 1, 2, L0)
        for x in range(x0, x1 + 1):
            P(x, 6, D2)                                                          # underside line
        P(x0 if x0 == 3 else x1, 5, D2); P(x0 if x0 == 3 else x1, 4, D1)       # curve up at the outer edge
    for y in range(1, 7):
        P(7, y, D2); P(8, y, D1)                                                 # sternum
    # six-pack: x 4-6 and 9-11; blocks at rows 8-9, 11-12, 14-15; separators (gentle) at 10 and 13
    for y0 in (8, 11, 14):
        for x0, x1 in ((4, 6), (9, 11)):
            for x in range(x0, x1 + 1):
                P(x, y0, M); P(x, y0 + 1, sh(0.95) if y0 < 14 else M)
            P(x0, y0, L0)                                                        # lit corner
            P(x1, y0 + 1, D1)                                                    # shaded corner
    for y in (10, 13):
        for x in (4, 5, 6, 9, 10, 11):
            P(x, y, D1)                                                          # gentle separators (no seam doubling)
    for y in range(7, 16):
        P(7, y, D2); P(8, y, D1)                                                 # linea alba
    for x in (4, 5, 6, 9, 10, 11):
        P(x, 7, D2)                                                              # under-pec shadow
    # obliques and serratus down the sides; V-lines into the sash
    for y in range(7, 16):
        P(3, y, D1); P(12, y, D1)
    for y in (8, 10, 12):
        P(3, y, D2); P(12, y, D2)
    P(4, 15, D2); P(11, 15, D2)
    # rim light on the shoulders' edge of the pecs
    P(3, 2, L0); P(12, 2, L0)
    # ---- final: black hair over the back of the head and upper back (drawn last, no red) ----
    hb = ramp(HAIR4)
    sk.fill("head", ("back",), hb[1], shade=0.06, seed=905)
    for x in range(0, 16, 2):
        sk.line("head", "back", [(x, 0), (x + 1, 15)], hb[2])
        sk.rect("head", "back", x + 1, 2, x + 1, 6, (64, 60, 76, 255))
    for x in range(0, 16, 2):
        end = 9 + (x * 5) % 6
        sk.rect("body", "back", x, 0, x + 1, end, hb[1] + (255,))
        sk.line("body", "back", [(x, 0), (x, end)], hb[2])
        sk.rect("body", "back", x + 1, 1, x + 1, 5, (64, 60, 76, 255))
        sk.rect("body", "back", x, end, x + 1, end, hb[2] + (255,))             # pointed dark tip
    round_shade(sk, list(ARMS), FUR)

def saiyan_detail(sk, accent, seed, skin=SKIN_S):
    """High-detail pass for the Saiyan warrior outfit and body (reused by the divine forms).
    accent = the form's light colour for the rim light, trim glints and aura wisps."""
    rnd = random.Random(seed)
    g = ramp(SGI); t = ramp(SGI_TRIM); u = ramp(SUNDER); b = ramp(SBOOT); sk_ = ramp(skin)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    # gi: deeper folds with lit ridges, stitched seams, patterned trim
    for side in ("back", "left", "right"):
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for _ in range(3):
            x, y = rnd.randrange(1, fw - 3), rnd.randrange(1, 12)
            sk.line("body", side, [(x, y), (x + 2, y + 4)], g[3]); sk.line("body", side, [(x + 1, y), (x + 3, y + 4)], g[0])
        stitch(sk, "body", side, 0, 15, fw - 1, 15, g[0])
    sk.line("body", "front", [(4, 12), (6, 15)], g[3]); sk.line("body", "front", [(5, 12), (7, 15)], g[0])
    sk.line("body", "front", [(11, 12), (9, 15)], g[3]); sk.line("body", "front", [(12, 12), (10, 15)], g[0])
    for i, (x, y) in enumerate(((2, 0), (3, 2), (4, 4), (5, 6), (6, 8), (13, 0), (12, 2), (11, 4), (10, 6), (9, 8))):
        P("body", "front", x, y, t[0] if i % 2 == 0 else t[3])                  # patterned lapel trim
    # back crest: detailed ring with inner glow and spokes
    for (x, y) in ((7, 3), (8, 3), (9, 4), (10, 5), (10, 6), (9, 7), (8, 8), (7, 8), (6, 7), (5, 6), (5, 5), (6, 4)):
        P("body", "back", x, y, t[1])
    for (x, y) in ((7, 2), (8, 2), (11, 5), (11, 6), (4, 5), (4, 6), (7, 9), (8, 9)):
        P("body", "back", x, y, t[3])
    P("body", "back", 7, 5, accent); P("body", "back", 8, 6, accent); P("body", "back", 7, 6, (255, 255, 255))
    # sash: woven texture, fringed tails
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        for x in range(0, fw):
            P("body", side, x, 17 + (x % 2), t[0] if x % 3 == 0 else t[2])
    for x in (10, 11, 12, 13):
        P("body", "front", x, 23, t[0]); P("body", "front", x, 22, t[2])
    # arms: lean forearms with tendons, layered wristbands with stitching, cuff trim pattern
    for arm in ARMS:
        for side in SIDES:
            sk.line(arm, side, [(2, 9), (3, 15)], sk_[2]); sk.line(arm, side, [(4, 10), (5, 15)], sk_[0])
            P(arm, side, 3, 12, sk_[3])
            sk.rect(arm, side, 0, 17, 7, 17, u[0] + (255,)); sk.rect(arm, side, 0, 18, 7, 20, u[1] + (255,))
            sk.rect(arm, side, 0, 21, 7, 21, u[3] + (255,)); stitch(sk, arm, side, 0, 19, 7, 19, u[0])
            for x in range(0, 8, 2):
                P(arm, side, x, 6, t[0])                                        # patterned cuff
    # legs: fold highlights, cuff band, boots with straps and buckles
    for leg in LEGS:
        for side in SIDES:
            sk.line(leg, side, [(2, 2), (3, 7)], g[0]); sk.line(leg, side, [(5, 4), (5, 10)], g[3])
            sk.rect(leg, side, 0, 13, 7, 13, t[2] + (255,))                    # cuff band
            sk.rect(leg, side, 0, 17, 7, 17, b[3] + (255,)); sk.rect(leg, side, 0, 20, 7, 20, b[3] + (255,))   # straps
        for y in (17, 20):
            sk.rect(leg, "front", 3, y, 4, y, t[0] + (255,))                   # buckles
            P(leg, "front", 3, y, (255, 250, 220))
        for x in range(0, 8, 2):
            P(leg, "front", x, 23, b[0])                                        # sole welt
    # warm rim light (no head) and a soft divine aura with rising wisps
    rim_light(sk, accent, alpha=150)
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(0, 0), (0, fh - 1)], accent + (130,)); sk.line(p, side, [(fw - 1, 0), (fw - 1, fh - 1)], accent + (130,))
            if p in LEGS:
                continue
            x = rnd.choice((0, fw - 1)); y = rnd.randrange(2, fh - 3)
            sk.line(p, side, [(x, y + 2), (x, y)], (255, 245, 245, 140))        # one soft rising wisp
    for arm in ARMS:
        for side in SIDES:
            glow_line(sk, arm, side, [(0, 6), (7, 6)], accent)

@design("saiyan_god", "Saiyan: Super Saiyan God", "full")
def _(sk):
    """Super Saiyan God (detailed): the calm face kept; red-magenta hair with fine strands and a
    glowing hairline; lean, toned build; high-detail gi (folds, stitching, patterned trim, detailed
    back crest), woven sash with fringe, layered wristbands, booted legs with straps and buckles,
    warm rim light and a soft divine aura with rising wisps."""
    HAIRG, GLOWG, EYEG = (210, 40, 86), (255, 140, 150), (200, 30, 56)
    saiyan_body(sk, 860)
    s_hi, s_base, s_sh, s_deep = ramp(SKIN_S)
    for arm in ARMS:                                                         # lean, toned forearms
        for side in SIDES:
            sk.rect(arm, side, 0, 7, 7, 16, s_base + (255,))
            sk.line(arm, side, [(1, 8), (1, 15)], s_sh); sk.line(arm, side, [(6, 8), (6, 15)], s_hi)
    saiyan_detail(sk, GLOWG, 861)
    # hair: base paint, then finer strands and a glowing hairline
    saiyan_hair_paint(sk, HAIRG)
    h = ramp(HAIRG)
    for side in ("left", "right", "back", "top"):
        for x in range(1, 16, 2):
            sk.line("head", side, [(x, 0), (x, 6 if side != "back" else 12)], h[2] if x % 4 == 1 else h[0])
    hair_glow_edges(sk, GLOWG, alpha=200)
    # the calm face, unchanged from the approved version
    saiyan_face(sk, "calm", eye=EYEG, brow_col=(120, 20, 46))
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 10, x0 + 2, 10, ramp(SKIN_S)[1] + (255,))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix, 8, (255, 236, 240, 255))

@design("saiyan_blue_v1", "Saiyan: Super Saiyan Blue (v1)", "full")
def _(sk):
    """Super Saiyan Blue (original warrior, detailed): bright cyan-blue hair with fine strands and a
    glowing white-blue hairline, clear blue eyes and a cool confident half-smirk, crisp cyan rim
    light and aura with small sparkles, full high-detail outfit."""
    HAIRB, GLOWB, EYEB = (60, 176, 255), (170, 236, 255), (40, 130, 255)
    saiyan_body(sk, 870)
    saiyan_detail(sk, GLOWB, 871)
    saiyan_hair_paint(sk, HAIRB)
    h = ramp(HAIRB)
    for side in ("left", "right", "back", "top"):
        for x in range(1, 16, 2):
            sk.line("head", side, [(x, 0), (x, 6 if side != "back" else 12)], h[2] if x % 4 == 1 else h[0])
    hair_glow_edges(sk, GLOWB, alpha=220)
    saiyan_face(sk, "smirk", eye=EYEB, brow_col=(30, 80, 150))
    for x0 in (3, 10):
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 9, ix + 1, 9, (20, 70, 170, 255))          # deeper lower iris
        sk.rect("head", "front", ix, 8, ix, 8, (235, 250, 255, 255))           # bright catch-light
    sparks(sk, 872, col=(190, 240, 255), n=1, parts=list(ARMS) + ["body"])       # small divine sparkles

def saiyan_detail_plus(sk, accent, hair_col, seed, skin=SKIN_S):
    """Second, finer detail layer: fabric weave, sleeve folds, undershirt collar shading, layered
    sash knot, knee creases, boot shine, forearm definition, knuckle wraps, painted spike tips,
    refined aura flecks."""
    rnd = random.Random(seed)
    g = ramp(SGI); t = ramp(SGI_TRIM); u = ramp(SUNDER); b = ramp(SBOOT); k = ramp(skin); h = ramp(hair_col)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    weave = tuple(int(v * 0.92) for v in g[1])
    # fabric weave on the gi (body sides/back, sleeves, trousers)
    for part in ("body",) + tuple(LEGS):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            ymax = 15 if part == "body" else 12
            for y in range(1, ymax, 4):
                for x in range((y // 4) % 2 * 2, fw, 4):
                    if part == "body" and side == "front" and 3 <= x <= 12 and y <= 11:
                        continue                                                # keep the open chest V clean
                    P(part, side, x, y, weave, 110)
    # undershirt collar shading and inner V edge
    for y in range(0, 10):
        half = max(0, 4 - y // 2)
        P("body", "front", 7 - half, y, u[0]); P("body", "front", 8 + half, y, u[3])
    # sleeve folds and inner cuff shadow
    for arm in ARMS:
        for side in SIDES:
            sk.line(arm, side, [(1, 1), (3, 3)], g[3]); sk.line(arm, side, [(2, 1), (4, 3)], g[0])
            sk.line(arm, side, [(0, 7), (7, 7)], k[3])
            # forearm definition: brachioradialis bulge and a vein
            sk.line(arm, side, [(1, 9), (2, 12)], k[0]); sk.line(arm, side, [(5, 9), (6, 13)], k[2])
        # knuckle wraps on the hands (bottom face)
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=(236, 228, 210, 255))
        for yy in range(y, y + fh, 2):
            sk.d.line((x, yy, x + fw - 1, yy), fill=(200, 190, 170, 255))
    # layered sash knot with shading
    sk.rect("body", "front", 9, 16, 12, 19, t[2] + (255,)); sk.rect("body", "front", 10, 16, 11, 17, t[0] + (255,))
    sk.rect("body", "front", 10, 18, 11, 19, t[3] + (255,))
    sk.line("body", "front", [(10, 20), (9, 22)], t[1]); sk.line("body", "front", [(11, 20), (12, 22)], t[1])
    # knee creases and boot shine
    for leg in LEGS:
        for side in ("front", "back"):
            sk.line(leg, side, [(1, 9), (3, 10), (6, 9)], g[3]); sk.line(leg, side, [(2, 8), (5, 8)], g[0])
            P(leg, side, 2, 18, (190, 196, 210)); P(leg, side, 2, 21, (190, 196, 210))   # boot shine
            P(leg, side, 3, 18, b[0])
    # painted spike tips: brighter points along the hair's lower edge and the fringe
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        for x in range(0, 16, 3):
            P("head", side, x, rows + 2, h[0]); P("head", side, x + 1, rows + 1, h[0])
    for x in range(0, 16, 2):
        P("head", "front", x, 4, h[0])
    # refined aura flecks (small 2-pixel glints just inside the outline)
    for part in ("body",) + tuple(ARMS):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for _ in range(2):
                x = rnd.choice((1, fw - 2)); y = rnd.randrange(1, fh - 2)
                P(part, side, x, y, accent, 230); P(part, side, x, y + 1, (255, 255, 255), 200)

@design("saiyan_blue", "Saiyan: Super Saiyan Blue", "full")
def _(sk):
    """Super Saiyan Blue (high detail): same face as approved; bright cyan-blue hair with fine
    strands, painted spike tips and a glowing hairline; full outfit detail plus a finer layer
    (fabric weave, sleeve folds, collar shading, layered sash knot, knee creases, boot shine,
    forearm definition with a vein, knuckle wraps), crisp cyan rim light, aura flecks and sparkles."""
    HAIRB, GLOWB, EYEB = (60, 176, 255), (170, 236, 255), (40, 130, 255)
    saiyan_body(sk, 870)
    saiyan_detail(sk, GLOWB, 871)
    saiyan_hair_paint(sk, HAIRB)
    h = ramp(HAIRB)
    for side in ("left", "right", "back", "top"):
        for x in range(1, 16, 2):
            sk.line("head", side, [(x, 0), (x, 6 if side != "back" else 12)], h[2] if x % 4 == 1 else h[0])
    hair_glow_edges(sk, GLOWB, alpha=220)
    saiyan_detail_plus(sk, GLOWB, HAIRB, 873)
    # the approved face, unchanged
    saiyan_face(sk, "smirk", eye=EYEB, brow_col=(30, 80, 150))
    for x0 in (3, 10):
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 9, ix + 1, 9, (20, 70, 170, 255))
        sk.rect("head", "front", ix, 8, ix, 8, (235, 250, 255, 255))
    sparks(sk, 872, col=(190, 240, 255), n=1, parts=list(ARMS) + ["body"])

def big_flames(sk, seed):
    """Fewer, larger flame tongues (2 px wide) shaded crimson -> red -> orange -> yellow tip."""
    rnd = random.Random(seed)
    C = [(150, 10, 22), (230, 40, 36), (255, 120, 40), (255, 222, 100)]
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge in (0, fw - 1):
                y = fh - 1
                while y > 3:
                    h = rnd.randint(5, 8)
                    top = max(0, y - h)
                    seg = max(1, (y - top) // 4)
                    for i, c in enumerate(C):
                        y1 = y - i * seg
                        y0 = max(top, y1 - seg + 1) if i < 3 else top
                        sk.line(p, side, [(edge, y1), (edge, y0)], c + (235,))
                    inner = 1 if edge == 0 else fw - 2
                    sk.line(p, side, [(inner, y), (inner, y - h // 2)], C[1] + (120,))
                    y -= h + rnd.randint(2, 3)

@design("saiyan_blue_kaioken", "Saiyan: Super Saiyan Blue Kaioken", "full")
def _(sk):
    """Super Saiyan Blue Kaioken (original warrior): cyan-blue hair with a glowing hairline, red-
    flushed skin, a two-layer aura (thin cyan core line inside crimson flame tongues), determined
    gritted face with blue eyes and a red under-glow, glowing forearm veins, full detailed outfit."""
    HAIRB, GLOWB, EYEB, FLUSH, RED = (60, 176, 255), (170, 236, 255), (40, 130, 255), (240, 132, 112), (255, 50, 50)
    saiyan_body(sk, 880, skin=FLUSH)
    saiyan_detail(sk, (255, 120, 110), 881, skin=FLUSH)
    saiyan_hair_paint(sk, HAIRB)
    h = ramp(HAIRB)
    for side in ("left", "right", "back", "top"):
        for x in range(1, 16, 2):
            sk.line("head", side, [(x, 0), (x, 6 if side != "back" else 12)], h[2] if x % 4 == 1 else h[0])
    hair_glow_edges(sk, GLOWB, alpha=220)
    saiyan_detail_plus(sk, (255, 120, 110), HAIRB, 882, skin=FLUSH)
    # determined, gritted face with blue eyes and a red under-glow
    f = ramp(FLUSH)
    ink = (40, 40, 90)
    sk.line("head", "front", [(2, 5), (6, 7)], ink); sk.line("head", "front", [(13, 5), (9, 7)], ink)
    for x0 in (3, 10):
        sk.rect("head", "front", x0, 8, x0 + 2, 9, (250, 246, 244, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", "front", ix, 8, ix + 1, 9, EYEB + (255,))
        sk.rect("head", "front", ix, 9, ix + 1, 9, (20, 70, 170, 255))
        sk.rect("head", "front", ix, 8, ix, 8, (235, 250, 255, 255))
        sk.rect("head", "front", x0, 7, x0 + 2, 7, ink + (255,))
        sk.rect("head", "front", x0, 10, x0 + 2, 10, (236, 120, 104, 255))      # soft red under each eye only
    sk.rect("head", "front", 7, 10, 8, 11, f[2] + (255,))
    sk.line("head", "front", [(2, 11), (4, 13)], f[2]); sk.line("head", "front", [(13, 11), (11, 13)], f[2])
    sk.rect("head", "front", 5, 12, 10, 13, (60, 16, 18, 255)); sk.rect("head", "front", 6, 12, 9, 12, (248, 242, 234, 255))
    sk.line("head", "front", [(4, 12), (5, 12)], ink); sk.line("head", "front", [(10, 12), (11, 11)], ink)
    sk.rect("head", "front", 13, 6, 13, 7, (220, 240, 255, 230))
    for arm in ARMS:
        for side in SIDES:
            vein(sk, arm, side, [(2, 8), (3, 11), (2, 13), (3, 16)])
    # two-layer aura: cyan core line inside the crimson flames
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(1, 0), (1, fh - 1)], GLOWB + (200,)); sk.line(p, side, [(fw - 2, 0), (fw - 2, fh - 1)], GLOWB + (200,))
    big_flames(sk, 883)
    rnd = random.Random(884)
    # white energy points along the cyan core line
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(2):
                x = rnd.choice((1, fw - 2)); y = rnd.randrange(1, fh - 1)
                sk.rect(p, side, x, y, x, y, (255, 255, 255, 255))
    # flushed skin highlights and forearm muscle definition
    for arm in ARMS:
        for side in ("front", "back"):
            sk.line(arm, side, [(5, 8), (6, 12)], (255, 186, 166)); sk.line(arm, side, [(1, 9), (2, 14)], (196, 92, 80))
            sk.rect(arm, side, 2, 22, 5, 22, (180, 236, 255, 220))                # energy ring at the wrist
            sk.rect(arm, side, 3, 22, 3, 22, (255, 255, 255, 255))
    # steam off the shoulders
    for arm in ARMS:
        _, _, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "top")
        for x in (1, 4, 6):
            sk.line(arm, "top", [(x, 6), (x + 1, 4), (x, 2)], (255, 232, 228, 150))
    # red light catching folds and edges of the outfit
    for side in ("left", "right", "back"):
        sk.line("body", side, [(1, 2), (1, 14)], (255, 120, 100, 110))
    for leg in LEGS:
        for side in SIDES:
            sk.line(leg, side, [(1, 1), (1, 12)], (255, 120, 100, 100))

def silver_stream_aura(sk, seed, core=(200, 214, 255), deep=(110, 130, 200)):
    """Calm, flowing aura: thin wavy silver-blue streams rising up the outer edges (no flames),
    with a few drifting light motes."""
    rnd = random.Random(seed)
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge, inner in ((0, 1), (fw - 1, fw - 2)):
                sk.line(p, side, [(edge, 0), (edge, fh - 1)], deep + (120,))
                phase = rnd.randrange(4)
                for y in range(fh):
                    if (y + phase) % 6 in (0, 1):
                        sk.rect(p, side, inner, y, inner, y, core + (170,))   # stream bends inward
                    elif (y + phase) % 6 == 2:
                        sk.rect(p, side, edge, y, edge, y, (245, 250, 255, 230))
            for _ in range(2):
                x, y = rnd.randrange(2, fw - 2), rnd.randrange(1, fh - 1)
                sk.rect(p, side, x, y, x, y, core + (140,))                   # drifting mote

@design("saiyan_ui_sign", "Saiyan: Ultra Instinct Sign", "full")
def _(sk):
    """Ultra Instinct Sign (v2, high detail): black hair lit silver-blue with layered strands and
    glints; calm focused face with sculpted cheekbones, jaw shadow and silver eyes with a dark rim;
    torn undershirt showing a defined chest; sculpted muscular forearms with a vein; controlled
    battle tears (ragged sleeve, torn knee) and scuffs; layered silver-blue stream aura with white
    crests, heat shimmer and drifting motes."""
    HAIRK, SHIM, GLOW, EYE = (28, 28, 38), (150, 164, 204), (200, 214, 255), (140, 152, 184)
    k = ramp(SKIN_S); K0, K1, K2, K3 = k
    u = ramp(SUNDER); g = ramp(SGI)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    saiyan_body(sk, 890, damage=0)
    saiyan_detail(sk, GLOW, 891)
    saiyan_detail_plus(sk, GLOW, (70, 74, 96), 892)

    # ---- hair: layered strands, cool silver light from above, glints and dark tips
    saiyan_hair_paint(sk, HAIRK)
    h = ramp(HAIRK)
    MID, LIT = (56, 60, 82), (96, 104, 140)
    for side in ("left", "right", "back", "top"):
        rows = 15 if side == "top" else (14 if side == "back" else 8)
        for x in range(16):
            n = (x * 7 + len(side)) % 5
            top = 0
            sk.line("head", side, [(x, top), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], MID if n in (1, 3) else h[1])
            if n == 1:
                sk.line("head", side, [(x, 0), (x, 2)], LIT); P("head", side, x, 0, SHIM)
            if n == 4:
                sk.line("head", side, [(x, 3), (x, rows - 1)], h[3])               # deep partings between locks
        if side != "top":
            for x in range(1, 16, 5):
                P("head", side, x, 1, (236, 242, 255))                             # small bright glints
    for x in range(16):
        P("head", "front", x, 0, LIT if x % 3 else SHIM)
        if x % 3 == 1:
            P("head", "front", x, 1, MID)
    hair_glow_edges(sk, GLOW, alpha=150)

    # ---- face: calm, focused, sculpted
    saiyan_face(sk, "calm", eye=EYE, brow_col=(36, 38, 54))
    F = "front"
    for x0 in (3, 10):
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", F, ix, 8, ix + 1, 9, EYE + (255,))
        P("head", F, ix + (1 if x0 == 3 else 0), 9, (64, 72, 100))                # darker lower iris
        P("head", F, ix + (0 if x0 == 3 else 1), 9, (96, 106, 140))
        P("head", F, ix, 8, (252, 253, 255))                                      # catch-light
        P("head", F, x0 + (2 if x0 == 3 else 0), 8, (214, 218, 228))              # shaded eye corner
        sk.rect("head", F, x0, 7, x0 + 2, 7, (30, 30, 44, 255))                    # upper lash line
        P("head", F, x0 + (0 if x0 == 3 else 2), 7, (60, 56, 70))
        sk.rect("head", F, x0, 10, x0 + 2, 10, (214, 160, 140, 255))               # soft lower lid
    P("head", F, 7, 6, K2); P("head", F, 8, 6, K2)                                # slight brow crease
    S1 = tuple(int(v * 0.9) for v in K1); S2 = tuple(int(v * 0.82) for v in K1)   # gentle face shades
    sk.rect("head", F, 7, 8, 7, 10, lt(K1, 1.06) + (255,))                         # nose bridge light
    P("head", F, 8, 10, S1); P("head", F, 8, 11, S2); P("head", F, 7, 11, S1)     # nose shadow
    for x in (1, 2, 13, 14):
        P("head", F, x, 11, S1)                                                    # under the cheekbones
    sk.rect("head", F, 1, 12, 2, 15, S1 + (255,)); sk.rect("head", F, 13, 12, 14, 15, S1 + (255,))   # jaw planes
    sk.rect("head", F, 0, 11, 0, 15, S2 + (255,)); sk.rect("head", F, 15, 11, 15, 15, S2 + (255,))
    sk.rect("head", F, 3, 12, 12, 15, K1 + (255,))                                 # clean mouth/chin area
    sk.rect("head", F, 6, 13, 9, 13, (156, 100, 86, 255))                          # closed mouth
    P("head", F, 5, 13, S2); P("head", F, 10, 13, S2)
    sk.rect("head", F, 7, 14, 8, 14, S1 + (255,))                                  # under-lip shadow
    sk.rect("head", F, 5, 15, 10, 15, S1 + (255,))                                 # chin
    P("head", F, 12, 11, (196, 96, 90)); P("head", F, 13, 10, (220, 130, 118))    # small cheek cut
    for side in ("left", "right"):
        sk.rect("head", side, 11, 12, 15, 15, K2 + (90,))                         # jaw shadow on the sides

    # ---- torn gi: the top is ripped open showing a defined chest
    t = ramp(SGI_TRIM)
    C1 = K1; C2 = tuple(int(v * 0.78) for v in K1); C0 = lt(K1, 1.1)
    for y in range(0, 12):
        x0, x1 = 3 + y // 4, 12 - y // 4
        sk.rect("body", F, x0, y, x1, y, C1 + (255,))
        P("body", F, x0 - 1, y, t[1]); P("body", F, x1 + 1, y, t[1])                 # lapel edge trim
        if y % 3 == 1:
            P("body", F, x0, y, u[1]); P("body", F, x1, y, u[1])                       # torn undershirt remnants
    for x in range(4, 12):
        P("body", F, x, 11, u[2] if x % 2 else u[1])                                 # ragged lower edge
    P("body", F, 6, 10, u[1]); P("body", F, 9, 10, u[1])
    # pecs: lit upper planes, soft underlines
    sk.rect("body", F, 4, 1, 6, 2, C0 + (255,)); sk.rect("body", F, 9, 1, 11, 2, C0 + (255,))
    sk.line("body", F, [(4, 4), (5, 5), (7, 5)], C2); sk.line("body", F, [(11, 4), (10, 5), (8, 5)], C2)
    sk.line("body", F, [(7, 1), (7, 4)], C2); sk.line("body", F, [(8, 1), (8, 4)], C2)   # sternum groove
    # abs: two rows of blocks with gentle separators
    sk.line("body", F, [(7, 6), (7, 10)], C2); sk.line("body", F, [(8, 6), (8, 10)], C2)
    sk.line("body", F, [(5, 8), (10, 8)], C2)
    for x in (6, 9):
        P("body", F, x, 6, C0); P("body", F, x, 9, C0)
    P("body", F, 5, 6, C2); P("body", F, 10, 6, C2)                                # obliques
    sk.line("body", F, [(10, 2), (11, 4)], (190, 84, 80))                          # scratch on the chest
    P("body", F, 3, 1, u[3]); P("body", F, 12, 1, u[3])                            # frayed threads

    # ---- sculpted, muscular forearms with a vein and elbow light
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 7, 7, 16, K1 + (255,))
            sk.rect(arm, side, 0, 7, 1, 16, K2 + (255,)); P(arm, side, 0, 12, K3); P(arm, side, 0, 13, K3)
            sk.rect(arm, side, 5, 8, 6, 13, K0 + (255,)); P(arm, side, 7, 9, K0)   # lit muscle belly
            sk.line(arm, side, [(2, 8), (3, 11), (2, 15)], K2)                    # muscle split
            sk.line(arm, side, [(4, 13), (6, 16)], K2)                            # tapering to the wrist
            P(arm, side, 4, 9, K0); P(arm, side, 3, 7, K3); P(arm, side, 4, 7, K3)  # elbow crease / bulge
            sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (176, 120, 104))      # vein
            P(arm, side, 5, 10, (224, 170, 150))
            sk.line(arm, side, [(7, 8), (7, 15)], (214, 224, 255, 160))           # silver rim
    # ragged left sleeve hem and a torn right knee
    for side in SIDES:
        for x in (1, 3, 4, 6):
            P("leftArm", side, x, 6, K1); P("leftArm", side, x, 5, g[3])
        P("leftArm", side, 2, 7, g[2]); P("leftArm", side, 5, 7, g[2])           # dangling threads
    for side in ("front", "left"):
        sk.rect("rightLeg", side, 2, 8, 5, 10, K1 + (255,))
        P("rightLeg", side, 3, 9, K0); P("rightLeg", side, 4, 10, (176, 64, 64))
        for x in (1, 2, 3, 4, 5, 6):
            P("rightLeg", side, x, 7 + (x % 2), g[3]); P("rightLeg", side, x, 11 - (x % 2), g[3])
    # scuffs and dust on the gi
    rnd = random.Random(895)
    for part in ("body", "leftLeg", "rightLeg"):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for _ in range(2):
                x, y = rnd.randrange(2, fw - 4), rnd.randrange(12 if part == "body" else 1, fh - 6 if part != "body" else 15)
                sk.rect(part, side, x, y, x + 1, y, (140, 150, 150, 70))
                P(part, side, x + 1, y + 1, g[3], 120)

    # ---- layered aura: deep edge, wavy silver streams, white crests, inner shimmer, motes
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            ph = rnd.randrange(8)
            for edge, inner, inner2 in ((0, 1, 2), (fw - 1, fw - 2, fw - 3)):
                sk.line(p, side, [(edge, 0), (edge, fh - 1)], (96, 116, 196, 150))
                for y in range(fh):
                    w = (y + ph) % 8
                    if w in (0, 1, 2):
                        P(p, side, inner, y, GLOW, 170)
                    if w == 1:
                        P(p, side, inner2, y, GLOW, 90)
                    if w == 3:
                        P(p, side, edge, y, (248, 252, 255), 235)                 # bright crest
                ph += 3
            for _ in range(2):
                x, y = rnd.randrange(3, fw - 3), rnd.randrange(1, fh - 3)
                if p in ARMS and 7 <= y <= 16:
                    continue
                sk.line(p, side, [(x, y), (x, y + 2)], (220, 230, 255, 45))        # faint heat shimmer
            x, y = rnd.randrange(2, fw - 2), rnd.randrange(1, fh - 1)
            P(p, side, x, y, (236, 242, 255), 150)                                 # drifting mote
    for arm in ARMS:
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "top")
        for xx in (1, 4, 6):
            sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (220, 232, 255, 110))   # light rising off the shoulders

@design("saiyan_mui", "Saiyan: Mastered Ultra Instinct", "full")
def _(sk):
    """Mastered Ultra Instinct (high detail): glowing silver hair with white highlights, blue-gray
    depth and a bright hairline; serene face with glowing silver eyes and silver brows; heavily
    ripped gi (chest and abs exposed, left sleeve torn away to a bare muscular arm, torn back and
    knees); calm white-silver aura with blue edges, bright crests, motes and rising light."""
    HAIR, GLOW, EYE = (206, 214, 234), (226, 234, 255), (176, 190, 226)
    k = ramp(SKIN_S); K0, K1, K2, K3 = k
    u = ramp(SUNDER); g = ramp(SGI); t = ramp(SGI_TRIM)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    F = "front"
    saiyan_body(sk, 900, damage=0)
    saiyan_detail(sk, GLOW, 901)
    saiyan_detail_plus(sk, GLOW, HAIR, 902)

    # ---- glowing silver hair: layered locks, blue-gray partings, white highlights
    saiyan_hair_paint(sk, HAIR)
    h = ramp(HAIR)
    PART_C, MIDC, WHITE = (124, 136, 176), (176, 186, 214), (250, 252, 255)
    for side in ("left", "right", "back", "top"):
        rows = 15 if side == "top" else (14 if side == "back" else 8)
        for x in range(16):
            n = (x * 7 + len(side)) % 5
            sk.line("head", side, [(x, 0), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], MIDC if n in (1, 3) else h[1])
            if n == 1:
                sk.line("head", side, [(x, 0), (x, 2)], WHITE)
            if n == 4:
                sk.line("head", side, [(x, 3), (x, rows - 1)], PART_C)              # cool partings between locks
        if side != "top":
            for x in range(2, 16, 5):
                P("head", side, x, 1, (255, 255, 255))
    for x in range(16):
        P("head", F, x, 0, WHITE if x % 3 == 0 else h[0])
        if x % 3 == 1:
            P("head", F, x, 1, MIDC)
    hair_glow_edges(sk, (180, 210, 255), alpha=200)

    # ---- serene face: silver brows, glowing silver eyes, sculpted shading
    saiyan_face(sk, "calm", eye=EYE, brow_col=(150, 160, 190))
    for x0 in (3, 10):
        sk.rect("head", F, x0, 8, x0 + 2, 9, (236, 242, 255, 255))                 # whites lit by the glow
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", F, ix, 8, ix + 1, 9, EYE + (255,))
        P("head", F, ix + (1 if x0 == 3 else 0), 9, (92, 106, 152))                # iris depth
        P("head", F, ix + (0 if x0 == 3 else 1), 9, (140, 156, 200))
        P("head", F, ix + (1 if x0 == 3 else 0), 8, (150, 166, 210))
        P("head", F, ix, 8, (255, 255, 255))
        sk.rect("head", F, x0, 7, x0 + 2, 7, (60, 64, 86, 255))                    # upper lid
        sk.rect("head", F, x0 - 1, 10, x0 + 3, 10, (210, 220, 255, 80))           # faint silver under-glow
    S1 = tuple(int(v * 0.9) for v in K1); S2 = tuple(int(v * 0.82) for v in K1)
    P("head", F, 7, 6, S1); P("head", F, 8, 6, S1)
    sk.rect("head", F, 7, 8, 7, 10, lt(K1, 1.06) + (255,))
    P("head", F, 8, 10, S1); P("head", F, 8, 11, S2); P("head", F, 7, 11, S1)
    for x in (1, 2, 13, 14):
        P("head", F, x, 11, S1)
    sk.rect("head", F, 1, 12, 2, 15, S1 + (255,)); sk.rect("head", F, 13, 12, 14, 15, S1 + (255,))
    sk.rect("head", F, 0, 11, 0, 15, S2 + (255,)); sk.rect("head", F, 15, 11, 15, 15, S2 + (255,))
    sk.rect("head", F, 3, 12, 12, 15, K1 + (255,))
    sk.rect("head", F, 6, 13, 9, 13, (156, 100, 86, 255)); P("head", F, 5, 13, S2); P("head", F, 10, 13, S2)
    sk.rect("head", F, 7, 14, 8, 14, S1 + (255,)); sk.rect("head", F, 5, 15, 10, 15, S1 + (255,))
    P("head", F, 3, 11, (200, 104, 96)); P("head", F, 2, 12, (190, 96, 90))       # scrape on the cheek
    for side in ("left", "right"):
        sk.rect("head", side, 11, 12, 15, 15, K2 + (90,))

    # ---- heavily ripped gi top: chest and abs bare
    C1 = K1; C2 = tuple(int(v * 0.78) for v in K1); C0 = lt(K1, 1.1)
    for y in range(0, 15):
        x0, x1 = 2 + y // 5, 13 - y // 5
        if y >= 12:
            x0, x1 = 4 + (y % 2), 11 - (y % 2)                                    # ragged bottom of the tear
        sk.rect("body", F, x0, y, x1, y, C1 + (255,))
        P("body", F, x0 - 1, y, g[3]); P("body", F, x1 + 1, y, g[3])               # torn cloth edge
        if y % 3 == 0:
            P("body", F, x0 - 1, y, t[1])                                          # shreds of gold trim
    for x in range(4, 12):
        P("body", F, x, 15, g[3] if x % 2 else g[2])
    sk.rect("body", F, 3, 1, 6, 2, C0 + (255,)); sk.rect("body", F, 9, 1, 12, 2, C0 + (255,))   # lit pec tops
    sk.line("body", F, [(3, 4), (4, 5), (7, 5)], C2); sk.line("body", F, [(12, 4), (11, 5), (8, 5)], C2)
    sk.line("body", F, [(7, 1), (7, 13)], C2); sk.line("body", F, [(8, 1), (8, 13)], C2)       # centre line
    for y in (8, 11):
        sk.line("body", F, [(5, y), (10, y)], C2)                                  # three rows of abs
    for y in (6, 9, 12):
        P("body", F, 6, y, C0); P("body", F, 9, y, C0)
    for y in (6, 8, 10):
        P("body", F, 4, y, C2); P("body", F, 11, y, C2)                            # serratus / obliques
    sk.line("body", F, [(4, 7), (5, 10)], C2); sk.line("body", F, [(11, 7), (10, 10)], C2)
    sk.line("body", F, [(10, 2), (12, 5)], (190, 84, 80)); sk.line("body", F, [(4, 9), (5, 11)], (190, 84, 80))   # scratches
    # torn holes on the back and sides
    for side, (x, y) in (("back", (1, 11)), ("back", (11, 12)), ("left", (2, 6)), ("right", (3, 10))):
        sk.rect("body", side, x, y, x + 2, y + 2, C1 + (255,)); P("body", side, x, y, C2)
        for dx in (-1, 3):
            P("body", side, x + dx, y + 1, g[3])

    # ---- arms: left sleeve torn away (bare shoulder and bicep), sculpted forearms
    for arm in ARMS:
        for side in SIDES:
            top = 0 if arm == "leftArm" else 7
            sk.rect(arm, side, 0, top, 7, 16, K1 + (255,))
            sk.rect(arm, side, 0, top, 1, 16, C2 + (255,))
            if arm == "leftArm":
                sk.rect(arm, side, 4, 1, 6, 3, C0 + (255,))                          # shoulder cap
                sk.line(arm, side, [(1, 4), (6, 4)], C2)                             # deltoid line
                sk.rect(arm, side, 4, 5, 6, 6, C0 + (255,)); sk.line(arm, side, [(2, 7), (6, 7)], C2)   # bicep
                P(arm, side, 0, 0, g[3]); P(arm, side, 3, 0, g[3]); P(arm, side, 7, 0, g[3])   # sleeve remnant
            sk.rect(arm, side, 5, 8, 6, 13, C0 + (255,))
            sk.line(arm, side, [(2, 8), (3, 11), (2, 15)], C2); sk.line(arm, side, [(4, 13), (6, 16)], C2)
            sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (180, 126, 110))
            sk.line(arm, side, [(7, top), (7, 16)], (226, 234, 255, 170))             # silver rim
        if arm == "leftArm":
            sk.fill(arm, ("top",), K1)
    # torn knees
    for leg in LEGS:
        for side in ("front",):
            sk.rect(leg, side, 2, 8, 5, 10, K1 + (255,)); P(leg, side, 3, 9, C0)
            for x in range(1, 7):
                P(leg, side, x, 7 + (x % 2), g[3]); P(leg, side, x, 11 - (x % 2), g[3])
    rnd = random.Random(905)
    for part in ("body", "leftLeg", "rightLeg"):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for _ in range(2):
                x, y = rnd.randrange(2, fw - 4), rnd.randrange(16 if part == "body" else 1, 21 if part == "body" else 6)
                sk.rect(part, side, x, y, x + 1, y, (150, 158, 160, 70))

    # ---- v2 detail pass: anatomy, fabric fraying, hair locks, face finish, sweat
    C3 = tuple(int(v * 0.68) for v in K1); CS = tuple(int(v * 0.9) for v in K1)
    # collarbones, neck base and traps
    sk.line("body", F, [(3, 0), (6, 1)], C2); sk.line("body", F, [(12, 0), (9, 1)], C2)
    P("body", F, 7, 0, C3); P("body", F, 8, 0, C3)
    sk.fill("body", ("top",), K1)
    x, y, fw, fh = Skin.face(PARTS["body"][0], PARTS["body"][1], "top")
    sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=K1 + (255,))
    sk.d.rectangle((x + 5, y, x + fw - 6, y + fh - 1), fill=C2 + (255,))           # neck shadow on the shoulders
    # pecs: rounded with shadow below and a lit inner edge
    P("body", F, 3, 3, C2); P("body", F, 12, 3, C2); P("body", F, 6, 3, C0); P("body", F, 9, 3, C0)
    P("body", F, 5, 4, K1); P("body", F, 10, 4, K1)
    # abs: lit top-left of each block, shadowed bottom, navel, outer lines
    for y0 in (6, 9, 12):
        for xx in (5, 10):
            P("body", F, xx, y0, C0)
        for xx in (6, 9):
            P("body", F, xx, y0 + 1, K1)
    sk.rect("body", F, 7, 13, 8, 13, C3 + (255,)); P("body", F, 7, 14, C2)        # navel
    for xx in range(4, 12, 2):
        P("body", F, xx, 14, g[3])
    # sweat glints
    P("body", F, 5, 2, (255, 255, 255), 200)
    # left arm: deltoid striations, bicep/triceps, elbow; right sleeve ragged hem
    for side in SIDES:
        sk.line("leftArm", side, [(2, 1), (3, 3)], C2); sk.line("leftArm", side, [(5, 1), (5, 3)], CS)
        P("leftArm", side, 3, 5, C0); P("leftArm", side, 5, 6, C0); P("leftArm", side, 2, 6, C2)
        P("leftArm", side, 4, 8, C3); P("leftArm", side, 3, 8, C2)                  # elbow
        P("leftArm", side, 6, 2, (255, 255, 255), 180)                            # sweat glint on the shoulder
        for xx in range(0, 8, 2):
            P("rightArm", side, xx, 6, K1); P("rightArm", side, xx + 1, 7, g[3])   # ragged sleeve hem
        for arm in ARMS:
            sk.line(arm, side, [(1, 9), (1, 14)], C3)                              # forearm underside shadow
            P(arm, side, 6, 9, (255, 255, 255), 150)
    for side in ("back",):
        sk.line("leftArm", side, [(2, 2), (2, 7)], C2); sk.line("leftArm", side, [(5, 3), (5, 6)], C0)   # triceps
    # hair: diagonal lock highlights and blue-shadowed spike tips
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        for x in range(0, 16, 4):
            sk.line("head", side, [(x, 2), (x + 2, rows - 2)], (240, 244, 255, 170))
            sk.line("head", side, [(x + 3, 3), (x + 3, rows - 1)], PART_C)
        for x in range(0, 16, 3):
            P("head", side, x, rows + 2, (150, 168, 220)); P("head", side, x + 1, rows + 2, (196, 214, 255))
    for x in range(1, 16, 3):
        sk.line("head", "top", [(x, 0), (x + 1, 15)], (240, 244, 255, 150))
    # face finish: eye corners, second catch-light, lips, ears
    for x0 in (3, 10):
        P("head", F, x0 - 1 if x0 == 3 else x0 + 3, 7, (60, 64, 86))                # outer lash corner
        ix = x0 + (1 if x0 == 3 else 0)
        P("head", F, ix + 1, 9, (220, 232, 255))                                    # small lower glint
    sk.rect("head", F, 6, 13, 9, 13, (140, 86, 74, 255)); P("head", F, 7, 13, (120, 70, 62)); P("head", F, 8, 13, (120, 70, 62))
    P("head", F, 7, 14, lt(K1, 1.05)); P("head", F, 8, 14, S1)                     # lower lip light
    for side in ("left", "right"):
        sk.rect("head", side, 9, 9, 10, 12, K2 + (255,)); P("head", side, 9, 10, K3); P("head", side, 10, 9, K0)
    # sash tails fluttering and boot scuffs
    for xx, yy in ((13, 21), (14, 22), (12, 23)):
        P("body", F, xx, yy, t[1])
    for leg in LEGS:
        for side in ("front", "left", "right"):
            P(leg, side, 2, 20, (110, 114, 126)); P(leg, side, 5, 22, (110, 114, 126))

    # ---- white-silver aura: blue outer edge, bright streams and crests, motes
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            ph = rnd.randrange(8)
            for edge, inner, inner2 in ((0, 1, 2), (fw - 1, fw - 2, fw - 3)):
                sk.line(p, side, [(edge, 0), (edge, fh - 1)], (120, 150, 230, 170 if p not in LEGS else 120))
                for y in range(fh):
                    if p in LEGS and y > 14:
                        continue                                                  # keep the boots clean
                    w = (y + ph) % 7
                    if w in (0, 1, 2):
                        P(p, side, inner, y, GLOW, 190)
                    if w == 1:
                        P(p, side, inner2, y, (255, 255, 255), 100)
                    if w == 3:
                        P(p, side, edge, y, (255, 255, 255), 245)
                ph += 3
            x, y = rnd.randrange(2, fw - 2), rnd.randrange(1, fh - 1)
            P(p, side, x, y, (255, 255, 255), 170)
    for arm in ARMS:
        for xx in (1, 3, 6):
            sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (236, 242, 255, 140))

def ego_flames(sk, seed, cols=((60, 10, 90), (120, 30, 170), (190, 60, 220), (250, 150, 255))):
    """Destructive violet flame tongues (2 px wide), dark violet -> purple -> magenta -> pink tip."""
    rnd = random.Random(seed)
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge, inner in ((0, 1), (fw - 1, fw - 2)):
                y = fh - 1
                while y > 3:
                    hgt = rnd.randint(5, 8)
                    top = max(0, y - hgt)
                    seg = max(1, (y - top) // 4)
                    for i, c in enumerate(cols):
                        y1 = y - i * seg
                        y0 = max(top, y1 - seg + 1) if i < 3 else top
                        sk.line(p, side, [(edge, y1), (edge, y0)], c + (235,))
                    sk.line(p, side, [(inner, y), (inner, y - hgt // 2)], cols[1] + (130,))
                    y -= hgt + rnd.randint(2, 3)

@design("saiyan_ultra_ego", "Saiyan: Ultra Ego", "full")
def _(sk):
    """Ultra Ego (high detail): purple-violet hair with magenta highlights and dark partings,
    fierce grin with glowing magenta eyes and heavy purple brows; bulkier build: skin-tight black
    undershirt sculpted over the pecs and abs (violet sheen), sleeves torn off for bare, veined
    biceps; detailed gi and boots; dark violet flame aura with pink tips and purple sparks."""
    HAIR, HI, PARTC, EYE, GLOW = (140, 52, 196), (226, 120, 240), (64, 16, 96), (236, 60, 200), (220, 110, 255)
    k = ramp(SKIN_S); K0, K1, K2, K3 = k
    u = ramp(SUNDER); g = ramp(SGI); t = ramp(SGI_TRIM)
    C2 = tuple(int(v * 0.78) for v in K1); C0 = lt(K1, 1.1); C3 = tuple(int(v * 0.68) for v in K1)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    F = "front"
    saiyan_body(sk, 910, damage=0)
    saiyan_detail(sk, GLOW, 911)
    saiyan_detail_plus(sk, GLOW, HAIR, 912)

    # ---- skin-tight black undershirt over a sculpted chest (wide open gi)
    SH0, SH1, SH2, SH3 = (112, 90, 146), (52, 46, 68), (36, 32, 50), (18, 16, 26)
    for y in range(0, 16):
        x0, x1 = 2 + y // 6, 13 - y // 6
        sk.rect("body", F, x0, y, x1, y, SH1 + (255,))
        P("body", F, x0 - 1, y, t[1]); P("body", F, x1 + 1, y, t[2])              # gi lapels pushed open
    sk.rect("body", F, 3, 1, 6, 2, SH0 + (255,)); sk.rect("body", F, 9, 1, 12, 2, SH0 + (255,))   # violet sheen on pecs
    P("body", F, 4, 1, (130, 100, 170)); P("body", F, 10, 1, (130, 100, 170))
    sk.line("body", F, [(3, 4), (4, 5), (7, 5)], SH3); sk.line("body", F, [(12, 4), (11, 5), (8, 5)], SH3)
    sk.line("body", F, [(7, 1), (7, 14)], SH3); sk.line("body", F, [(8, 1), (8, 14)], SH2)
    for y in (8, 11):
        sk.line("body", F, [(5, y), (6, y)], SH3); sk.line("body", F, [(9, y), (10, y)], SH3)
    for y in (6, 9, 12):
        P("body", F, 5, y, SH0); P("body", F, 10, y, SH0); P("body", F, 6, y, (80, 66, 106)); P("body", F, 9, y, (80, 66, 106))
        P("body", F, 5, y + 1, (70, 60, 92)); P("body", F, 10, y + 1, (70, 60, 92))
    sk.line("body", F, [(3, 7), (4, 13)], SH2); sk.line("body", F, [(12, 7), (11, 13)], SH2)
    sk.rect("body", F, 6, 0, 9, 0, K1 + (255,)); P("body", F, 7, 0, C2); P("body", F, 8, 0, C2)   # collar of skin
    sk.line("body", F, [(10, 3), (12, 6)], (110, 50, 120))                          # rip in the undershirt
    P("body", F, 11, 4, K1); P("body", F, 11, 5, C2)

    # ---- bulky bare arms: sleeves torn off, veined biceps and forearms
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 1, 7, 16, K1 + (255,))
            sk.rect(arm, side, 0, 1, 1, 16, C2 + (255,)); sk.line(arm, side, [(0, 2), (0, 15)], C3)
            for x in range(0, 8):
                P(arm, side, x, 0, g[3] if x % 2 else g[2])                          # torn sleeve stub
                if x % 3 == 0:
                    P(arm, side, x, 1, g[3])
            sk.rect(arm, side, 4, 2, 6, 3, C0 + (255,)); sk.line(arm, side, [(2, 4), (6, 4)], C2)   # deltoid
            sk.rect(arm, side, 3, 5, 6, 6, C0 + (255,)); P(arm, side, 5, 5, lt(K1, 1.2))          # bicep peak
            sk.line(arm, side, [(2, 7), (6, 7)], C2); P(arm, side, 4, 8, C3)                    # elbow crease
            sk.rect(arm, side, 5, 9, 6, 13, C0 + (255,))
            sk.line(arm, side, [(2, 9), (3, 12), (2, 15)], C2); sk.line(arm, side, [(4, 13), (6, 16)], C2)
            sk.line(arm, side, [(4, 3), (3, 5), (4, 7)], (178, 120, 104))                   # bicep vein
            sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (178, 120, 104))                # forearm vein
            sk.line(arm, side, [(7, 1), (7, 16)], GLOW + (150,))                            # violet rim light
        sk.fill(arm, ("top",), K1)
    # ---- back: undershirt seams shaped over the lats, crest kept
    for side in ("back",):
        sk.line("body", side, [(1, 2), (3, 12)], g[3]); sk.line("body", side, [(14, 2), (12, 12)], g[3])
        sk.line("body", side, [(2, 2), (4, 12)], g[0]); sk.line("body", side, [(13, 2), (11, 12)], g[0])

    # ---- hair: violet locks, magenta highlights, dark partings, glowing tips
    saiyan_hair_paint(sk, HAIR)
    h = ramp(HAIR)
    for side in ("left", "right", "back", "top"):
        rows = 15 if side == "top" else (14 if side == "back" else 8)
        for x in range(16):
            n = (x * 7 + len(side)) % 5
            sk.line("head", side, [(x, 0), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], h[0] if n in (1, 3) else h[1])
            if n == 1:
                sk.line("head", side, [(x, 0), (x, 2)], HI)
            if n == 4:
                sk.line("head", side, [(x, 3), (x, rows - 1)], PARTC)
        if side != "top":
            for x in range(0, 16, 4):
                sk.line("head", side, [(x, 2), (x + 2, rows - 2)], HI + (150,))
            for x in range(0, 16, 3):
                P("head", side, x, (14 if side == "back" else 8) + 2, (255, 160, 255)); P("head", side, x + 1, (14 if side == "back" else 8) + 2, GLOW)
    for x in range(16):
        P("head", F, x, 0, HI if x % 3 == 0 else h[0])
    hair_glow_edges(sk, GLOW, alpha=200)

    # ---- fierce grin, glowing magenta eyes, heavy purple brows
    saiyan_face(sk, "fierce_grin", eye=EYE, brow_col=(84, 24, 110))
    S1 = tuple(int(v * 0.9) for v in K1); S2 = tuple(int(v * 0.82) for v in K1)
    BR = (90, 26, 120)
    sk.rect("head", F, 0, 5, 15, 7, K1 + (255,))                                   # clear, then clean brows
    sk.line("head", F, [(2, 5), (6, 7)], BR); sk.line("head", F, [(13, 5), (9, 7)], BR)
    P("head", F, 1, 5, BR); P("head", F, 14, 5, BR)
    for x0 in (3, 10):
        sk.rect("head", F, x0, 8, x0 + 2, 9, (252, 238, 250, 255))
        ix = x0 + (1 if x0 == 3 else 0)
        sk.rect("head", F, ix, 8, ix + 1, 9, EYE + (255,))
        P("head", F, ix + (1 if x0 == 3 else 0), 9, (140, 20, 110))
        P("head", F, ix, 8, (255, 236, 255))
        P("head", F, x0 + (2 if x0 == 3 else 0), 7, BR)
        sk.rect("head", F, x0, 10, x0 + 2, 10, K1 + (255,))
        sk.rect("head", F, x0, 10, x0 + 2, 10, (240, 120, 230, 60))                    # faint magenta under-glow
    P("head", F, 7, 7, C2); P("head", F, 8, 7, C2); P("head", F, 7, 6, S1); P("head", F, 8, 6, S1)   # scowl crease
    sk.rect("head", F, 7, 8, 7, 10, lt(K1, 1.06) + (255,)); P("head", F, 8, 10, S1); P("head", F, 8, 11, S2)
    for x in (1, 14):
        sk.rect("head", F, x, 11, x, 14, S1 + (255,))
    sk.rect("head", F, 4, 12, 11, 13, K1 + (255,))
    sk.rect("head", F, 5, 12, 10, 12, (248, 244, 236, 255))                         # confident toothy grin
    P("head", F, 7, 12, (226, 220, 212)); P("head", F, 4, 12, (120, 60, 56)); P("head", F, 11, 11, (120, 60, 56))
    sk.rect("head", F, 6, 13, 9, 13, (120, 60, 56, 255))                            # lower lip shadow
    sk.line("head", F, [(3, 11), (4, 12)], C3); sk.line("head", F, [(12, 11), (11, 12)], C3)
    sk.rect("head", F, 5, 14, 10, 14, S1 + (255,)); sk.rect("head", F, 5, 15, 10, 15, S2 + (255,))
    for side in ("left", "right"):
        sk.line("head", side, [(2, 6), (3, 8), (2, 9)], (160, 100, 90))            # temple vein
        sk.rect("head", side, 11, 12, 15, 15, K2 + (90,))

    # ==== v2 extreme-detail pass ===============================================
    S3 = tuple(int(v * 0.7) for v in K1)
    # face sculpting: cheekbones, nose, jaw planes, lips, eye depth, lighter under-eyes
    for x0 in (3, 10):
        sk.rect("head", F, x0, 10, x0 + 2, 10, lt(K1, 1.16) + (255,))              # offsets the seam darkening
        P("head", F, x0 + (0 if x0 == 3 else 2), 8, (210, 190, 206))                 # shaded outer eye corner
        P("head", F, x0 + (2 if x0 == 3 else 0), 9, (255, 120, 230))                 # inner glow pixel
    for x in (1, 2, 13, 14):
        P("head", F, x, 10, lt(K1, 1.08))                                          # cheekbone light
    sk.rect("head", F, 0, 11, 0, 15, S2 + (255,)); sk.rect("head", F, 15, 11, 15, 15, S2 + (255,))
    sk.rect("head", F, 1, 12, 2, 15, S1 + (255,)); sk.rect("head", F, 13, 12, 14, 15, S1 + (255,))
    P("head", F, 7, 11, S1); P("head", F, 8, 11, S2); P("head", F, 6, 11, S1)     # nose base
    P("head", F, 7, 9, lt(K1, 1.1))
    sk.line("head", F, [(3, 11), (4, 12)], S3); sk.line("head", F, [(12, 10), (11, 11)], S3)   # smile creases
    sk.rect("head", F, 5, 14, 10, 14, S1 + (255,)); sk.rect("head", F, 6, 15, 9, 15, S2 + (255,))   # chin
    P("head", F, 7, 14, lt(K1, 1.06))
    P("head", F, 12, 13, (196, 90, 86)); P("head", F, 13, 14, (196, 90, 86))      # small cut on the jaw
    for side in ("left", "right"):
        sk.rect("head", side, 9, 9, 10, 12, K2 + (255,)); P("head", side, 9, 10, K3); P("head", side, 10, 9, K0)   # ear
        sk.rect("head", side, 0, 12, 4, 15, S1 + (255,))                         # jaw on the side
    # hair: extra lock shading, bright magenta tips, darker roots at the hairline
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        for x in range(1, 16, 4):
            sk.line("head", side, [(x, 3), (x + 1, rows)], (96, 30, 140))
            P("head", side, x + 2, 2, (255, 190, 255))
        sk.line("head", side, [(0, rows), (15, rows)], (110, 36, 160))
    for x in range(0, 16, 2):
        P("head", F, x, 4, (96, 30, 140)); P("head", F, x + 1, 3, HI)
    for x in range(2, 16, 4):
        sk.line("head", "top", [(x, 0), (x + 2, 15)], (96, 30, 140)); sk.line("head", "top", [(x + 1, 0), (x + 3, 15)], HI + (170,))
    # chest: rounded pec sheen, ab highlights, fabric stretch lines, rip showing skin
    for (x, y) in ((4, 2), (5, 3), (10, 2), (11, 3)):
        P("body", F, x, y, (96, 78, 128))
    P("body", F, 4, 1, (170, 140, 210)); P("body", F, 11, 1, (170, 140, 210))      # bright sheen points
    for y in (6, 9, 12):
        for x in (5, 10):
            P("body", F, x, y, (124, 100, 160))
    for (x0, y0) in ((3, 6), (12, 6), (3, 10), (12, 10)):
        P("body", F, x0, y0, SH3); P("body", F, x0, y0 + 1, (66, 56, 88))            # serratus
    sk.line("body", F, [(4, 13), (6, 15)], (62, 52, 84)); sk.line("body", F, [(11, 13), (9, 15)], (62, 52, 84))   # stretch lines
    sk.rect("body", F, 10, 3, 11, 5, K1 + (255,)); P("body", F, 10, 3, C0); P("body", F, 11, 5, C2)   # skin through the rip
    sk.line("body", F, [(9, 2), (10, 6)], SH3); sk.line("body", F, [(12, 3), (12, 6)], SH3)
    sk.line("body", F, [(10, 4), (11, 5)], (190, 84, 80))
    # open gi: lapel folds with gold-trim shading
    for y in range(0, 16, 2):
        x0, x1 = 2 + y // 6, 13 - y // 6
        P("body", F, x0 - 2, y, g[3]); P("body", F, x1 + 2, y, g[3])
        P("body", F, x0 - 1, y + 1, t[0]); P("body", F, x1 + 1, y + 1, t[3])
    # back: torn gi over the shoulder blades showing the black undershirt and lats
    for (cx, cy) in ((3, 2), (10, 2)):
        sk.rect("body", "back", cx, cy, cx + 2, cy + 3, SH1 + (255,))
        P("body", "back", cx + 1, cy + 1, SH0); P("body", "back", cx, cy + 3, SH3)
        for dx in (-1, 3):
            P("body", "back", cx + dx, cy + 1, g[3]); P("body", "back", cx + dx, cy + 3, g[2])
    # top of the shoulders: traps and neck shadow
    x, y, fw, fh = Skin.face(PARTS["body"][0], PARTS["body"][1], "top")
    sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=g[1] + (255,))
    sk.d.rectangle((x + 4, y + 1, x + fw - 5, y + fh - 2), fill=K1 + (255,))
    sk.d.rectangle((x + 6, y + 2, x + fw - 7, y + fh - 3), fill=C2 + (255,))
    # arms: triceps, forearm flexors, branching veins, scratches, sweat, wrapped knuckles
    for arm in ARMS:
        for side in SIDES:
            P(arm, side, 5, 4, lt(K1, 1.18)); P(arm, side, 4, 6, C2)
            sk.line(arm, side, [(3, 5), (2, 4)], (178, 120, 104))                  # vein branch
            sk.line(arm, side, [(4, 12), (3, 13)], (178, 120, 104))
            P(arm, side, 6, 11, lt(K1, 1.2))
            sk.line(arm, side, [(1, 10), (1, 14)], S3)
        sk.line(arm, "back", [(2, 2), (2, 7)], C2); sk.line(arm, "back", [(5, 2), (5, 6)], C0)   # triceps horseshoe
        sk.line(arm, "back", [(3, 7), (4, 7)], C2)
        P(arm, "front", 6, 3, (255, 255, 255), 190)                                 # sweat glint
    for side in ("front", "right"):
        sk.line("rightArm", side, [(2, 9), (4, 11)], (190, 84, 80))                 # scratch
    # trousers: deep folds, torn knee, boot scuffs
    for leg in LEGS:
        for side in SIDES:
            sk.line(leg, side, [(1, 3), (3, 6)], g[3]); sk.line(leg, side, [(2, 3), (4, 6)], g[0])
            sk.line(leg, side, [(6, 1), (5, 5)], g[3])
            P(leg, side, 2, 20, (110, 114, 126)); P(leg, side, 6, 22, (110, 114, 126))
    for side in ("front", "left"):
        sk.rect("leftLeg", side, 3, 8, 5, 10, K1 + (255,)); P("leftLeg", side, 4, 9, (190, 84, 80))
        for x in range(2, 7):
            P("leftLeg", side, x, 7 + (x % 2), g[3]); P("leftLeg", side, x, 11 - (x % 2), g[3])
    # sash tails
    for (xx, yy) in ((12, 21), (13, 22), (11, 23), (14, 23)):
        P("body", F, xx, yy, t[1])

    # ---- aura: violet flames, purple sparks, dark smoke at the feet
    for p in ("body",):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            sk.line(p, side, [(2, 0), (2, fh - 1)], (210, 90, 240, 60)); sk.line(p, side, [(fw - 3, 0), (fw - 3, fh - 1)], (210, 90, 240, 60))
    ego_flames(sk, 913)
    rnd = random.Random(915)
    for p in ("body",):
        for side in ("left", "right"):
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            x, y = rnd.randrange(2, fw - 4), rnd.randrange(2, fh - 6)
            pts = [(x, y), (x + 1, y + 1), (x, y + 2), (x + 2, y + 3), (x + 1, y + 4)]
            sk.line(p, side, pts, (60, 10, 80, 230)); sk.line(p, side, [(px + 1, py) for px, py in pts], (240, 140, 255, 200))   # destruction crackle
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            x, y = rnd.randrange(2, fw - 2), rnd.randrange(1, fh - 1)
            P(p, side, x, y, (255, 200, 255), 150)                                  # floating ember
    sparks(sk, 914, col=(230, 140, 255), n=1, parts=list(ARMS) + ["body"])
    for leg in LEGS:
        for side in SIDES:
            sk.rect(leg, side, 0, 22, 7, 23, (60, 20, 80, 120))
    for arm in ARMS:
        for xx in (1, 4, 6):
            sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (220, 140, 255, 130))

@design("saiyan_legendary", "Saiyan: Legendary Super Saiyan", "full")
def _(sk):
    """Legendary Super Saiyan (original, high detail): towering bare-chested build with massive
    pecs, an eight-pack, serratus, traps and a sculpted back; yellow-green wild hair with lime
    highlights; blank glowing pale-green eyes and a roaring grimace; dark-metal bracers with
    green gems; shredded teal trousers under the gold sash; green flame aura with lime lightning."""
    HAIR, HI, PARTC, GLOW = (176, 222, 70), (226, 255, 140), (92, 128, 24), (150, 255, 120)
    k = ramp(SKIN_S); K0, K1, K2, K3 = k
    g = ramp(SGI); t = ramp(SGI_TRIM)
    C0 = lt(K1, 1.12); CH = lt(K1, 1.22); C2 = tuple(int(v * 0.78) for v in K1); C3 = tuple(int(v * 0.64) for v in K1)
    S1 = tuple(int(v * 0.9) for v in K1)
    MET, MET_HI, MET_SH, GEM = (70, 74, 86), (140, 146, 160), (36, 38, 46), (90, 255, 120)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    F = "front"
    saiyan_body(sk, 920, damage=0)
    saiyan_detail(sk, GLOW, 921)
    saiyan_detail_plus(sk, GLOW, HAIR, 922)

    # ---- bare torso (rows 0-15 on every side)
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 0, fw - 1, 15, K1 + (255,))
        sk.rect("body", side, 0, 0, 0, 15, C2 + (255,)); sk.rect("body", side, fw - 1, 0, fw - 1, 15, C3 + (255,))
    x, y, fw, fh = Skin.face(PARTS["body"][0], PARTS["body"][1], "top")
    sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=C0 + (255,))
    sk.d.rectangle((x + 6, y + 1, x + fw - 7, y + fh - 2), fill=C2 + (255,))      # neck base between the traps
    # front: huge pecs, collarbones, eight-pack, obliques
    sk.line("body", F, [(1, 0), (6, 1)], C2); sk.line("body", F, [(14, 0), (9, 1)], C2)
    sk.rect("body", F, 1, 1, 6, 5, C0 + (255,)); sk.rect("body", F, 9, 1, 14, 5, C0 + (255,))
    sk.rect("body", F, 2, 1, 4, 2, CH + (255,)); sk.rect("body", F, 11, 1, 13, 2, CH + (255,))
    sk.line("body", F, [(1, 5), (3, 6), (7, 6)], C3); sk.line("body", F, [(14, 5), (12, 6), (8, 6)], C3)
    sk.line("body", F, [(1, 4), (1, 6)], C2); sk.line("body", F, [(14, 4), (14, 6)], C2)
    sk.line("body", F, [(7, 1), (7, 15)], C3); sk.line("body", F, [(8, 1), (8, 15)], C2)
    for y0 in (7, 10, 13):
        sk.line("body", F, [(4, y0 + 2), (6, y0 + 2)], C2); sk.line("body", F, [(9, y0 + 2), (11, y0 + 2)], C2)
        sk.rect("body", F, 4, y0, 6, y0, C0 + (255,)); sk.rect("body", F, 9, y0, 11, y0, C0 + (255,))
        P("body", F, 5, y0, CH); P("body", F, 10, y0, CH)
    for y0 in (7, 9, 11):
        P("body", F, 2, y0, C2); P("body", F, 2, y0 + 1, C0); P("body", F, 13, y0, C2); P("body", F, 13, y0 + 1, C0)   # serratus
    sk.line("body", F, [(3, 7), (3, 15)], C2); sk.line("body", F, [(12, 7), (12, 15)], C2)
    sk.line("body", F, [(3, 13), (6, 15)], C3); sk.line("body", F, [(12, 13), (9, 15)], C3)                     # v-cut
    sk.line("body", F, [(11, 2), (13, 4)], (190, 84, 80)); sk.line("body", F, [(4, 10), (5, 12)], (190, 84, 80))   # battle scratches
    P("body", F, 3, 2, (255, 255, 255), 200); P("body", F, 10, 8, (255, 255, 255), 180)                         # sweat glints
    # back: traps, shoulder blades, spine, lats
    B = "back"
    sk.rect("body", B, 3, 0, 12, 1, C0 + (255,)); sk.line("body", B, [(4, 2), (11, 2)], C2)
    sk.rect("body", B, 2, 3, 5, 7, C0 + (255,)); sk.rect("body", B, 10, 3, 13, 7, C0 + (255,))
    sk.line("body", B, [(2, 8), (6, 6)], C3); sk.line("body", B, [(13, 8), (9, 6)], C3)
    sk.line("body", B, [(7, 2), (7, 15)], C3); sk.line("body", B, [(8, 2), (8, 15)], C2)
    for y in range(3, 15, 2):
        P("body", B, 7, y, C2)
    sk.line("body", B, [(1, 9), (5, 15)], C2); sk.line("body", B, [(14, 9), (10, 15)], C2)
    sk.rect("body", B, 3, 9, 5, 11, CH + (120,)); sk.rect("body", B, 10, 9, 12, 11, CH + (120,))
    sk.line("body", B, [(10, 4), (12, 7)], (190, 84, 80))
    # sides: ribs/serratus and lat bulge
    for side in ("left", "right"):
        for y in (3, 6, 9, 12):
            sk.line("body", side, [(0, y), (2, y + 1)], C2)
        sk.rect("body", side, 1, 0, 2, 2, C0 + (255,))
    # gold sash now holds up the trousers; frayed gi remnant hanging from it
    for side in SIDES:
        _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
        sk.rect("body", side, 0, 15, fw - 1, 15, C3 + (255,))
    for x in (1, 4, 13):
        sk.rect("body", F, x, 20, x + 1, 23, g[2] + (255,)); P("body", F, x, 23, g[3])

    # ---- massive bare arms with metal bracers
    for arm in ARMS:
        for side in SIDES:
            sk.rect(arm, side, 0, 0, 7, 16, K1 + (255,))
            sk.rect(arm, side, 0, 0, 1, 16, C2 + (255,)); sk.line(arm, side, [(0, 1), (0, 16)], C3)
            sk.rect(arm, side, 3, 0, 6, 3, C0 + (255,)); P(arm, side, 5, 1, CH)              # boulder shoulder
            sk.line(arm, side, [(2, 4), (7, 4)], C2)
            sk.rect(arm, side, 3, 5, 6, 7, C0 + (255,)); sk.rect(arm, side, 4, 5, 5, 5, CH + (255,))   # bicep
            sk.line(arm, side, [(2, 8), (6, 8)], C2); P(arm, side, 4, 9, C3)
            sk.rect(arm, side, 5, 10, 6, 13, C0 + (255,))
            sk.line(arm, side, [(2, 10), (3, 13)], C2)
            sk.line(arm, side, [(4, 2), (3, 5), (4, 7)], (180, 122, 106))               # veins
            sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (180, 122, 106))
            sk.line(arm, side, [(7, 0), (7, 14)], GLOW + (130,))                      # green rim light
            # dark metal bracer with a green gem
            sk.rect(arm, side, 0, 14, 7, 21, MET + (255,))
            sk.rect(arm, side, 0, 14, 7, 14, MET_HI + (255,)); sk.rect(arm, side, 0, 21, 7, 21, MET_SH + (255,))
            sk.line(arm, side, [(0, 17), (7, 17)], MET_SH); sk.line(arm, side, [(0, 18), (7, 18)], MET_HI)
            for x in (1, 6):
                P(arm, side, x, 15, MET_HI); P(arm, side, x, 20, MET_SH)                # rivets
            sk.rect(arm, side, 3, 16, 4, 19, GEM + (255,)); P(arm, side, 3, 16, (220, 255, 220)); P(arm, side, 4, 19, (30, 140, 60))
        sk.fill(arm, ("top",), C0)

    # ---- shredded trousers
    for leg in LEGS:
        for side in SIDES:
            for x in range(0, 8, 2):
                P(leg, side, x, 14 + (x // 2) % 2, K1)                                  # ripped hems over the boots
            sk.line(leg, side, [(1, 2), (3, 7)], g[3]); sk.line(leg, side, [(2, 2), (4, 7)], g[0])
        sk.rect(leg, "front", 2, 8, 5, 11, K1 + (255,)); P(leg, "front", 3, 9, C0)
        for x in range(1, 7):
            P(leg, "front", x, 7 + (x % 2), g[3]); P(leg, "front", x, 12 - (x % 2), g[3])

    # ---- wild yellow-green hair
    saiyan_hair_paint(sk, HAIR)
    h = ramp(HAIR)
    for side in ("left", "right", "back", "top"):
        rows = 15 if side == "top" else (14 if side == "back" else 8)
        for x in range(16):
            n = (x * 7 + len(side)) % 5
            sk.line("head", side, [(x, 0), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], h[0] if n in (1, 3) else h[1])
            if n == 1:
                sk.line("head", side, [(x, 0), (x, 2)], HI)
            if n == 4:
                sk.line("head", side, [(x, 3), (x, rows - 1)], PARTC)
        if side != "top":
            for x in range(0, 16, 4):
                sk.line("head", side, [(x, 2), (x + 2, rows - 2)], HI + (150,))
            r2 = 14 if side == "back" else 8
            for x in range(0, 16, 3):
                P("head", side, x, r2 + 2, (240, 255, 170)); P("head", side, x + 1, r2 + 2, GLOW)
    for x in range(16):
        P("head", F, x, 0, HI if x % 3 == 0 else h[0])
    hair_glow_edges(sk, GLOW, alpha=200)

    # ---- face: blank glowing eyes, heavy brow ridge, roaring grimace
    saiyan_face(sk, "blank", eye=(200, 255, 190), brows=True, brow_col=(120, 150, 40))
    S2 = tuple(int(v * 0.82) for v in K1)
    sk.rect("head", F, 0, 5, 15, 7, K1 + (255,))
    sk.line("head", F, [(1, 5), (6, 7)], (110, 140, 36)); sk.line("head", F, [(14, 5), (9, 7)], (110, 140, 36))
    sk.line("head", F, [(1, 6), (5, 7)], C2); sk.line("head", F, [(14, 6), (10, 7)], C2)
    P("head", F, 7, 7, C3); P("head", F, 8, 7, C3); P("head", F, 7, 6, C2); P("head", F, 8, 6, C2)
    for x0 in (3, 10):
        sk.rect("head", F, x0, 8, x0 + 2, 9, (214, 255, 200, 255))                      # blank glowing eyes
        P("head", F, x0 + 1, 8, (255, 255, 255))
        sk.rect("head", F, x0, 7, x0 + 2, 7, (60, 70, 30, 255))
        sk.rect("head", F, x0 - 1, 10, x0 + 3, 10, lt(K1, 1.12) + (255,))
        sk.rect("head", F, x0 - 1, 10, x0 + 3, 10, (160, 255, 130, 80))
    sk.rect("head", F, 7, 8, 7, 10, C0 + (255,)); P("head", F, 8, 10, S1); P("head", F, 8, 11, S2); P("head", F, 6, 11, S1)
    for x in (1, 2, 13, 14):
        P("head", F, x, 10, C0)
    sk.rect("head", F, 0, 11, 0, 15, S2 + (255,)); sk.rect("head", F, 15, 11, 15, 15, S2 + (255,))
    sk.rect("head", F, 1, 12, 2, 15, S1 + (255,)); sk.rect("head", F, 13, 12, 14, 15, S1 + (255,))
    sk.rect("head", F, 4, 12, 11, 14, (56, 14, 20, 255))                               # roaring mouth
    sk.rect("head", F, 5, 12, 10, 12, (246, 242, 232, 255)); sk.rect("head", F, 5, 14, 10, 14, (230, 224, 214, 255))
    P("head", F, 7, 13, (150, 40, 50)); P("head", F, 8, 13, (150, 40, 50))              # tongue
    sk.line("head", F, [(3, 11), (4, 12)], C3); sk.line("head", F, [(12, 11), (11, 12)], C3)
    sk.rect("head", F, 5, 15, 10, 15, S1 + (255,))
    for side in ("left", "right"):
        sk.rect("head", side, 9, 9, 10, 12, K2 + (255,)); P("head", side, 10, 9, K0)
        sk.line("head", side, [(2, 6), (3, 8), (2, 9)], (160, 100, 90))
        sk.rect("head", side, 0, 12, 4, 15, S1 + (255,))

    # ==== v2 extreme-detail pass (face untouched) ==============================
    C1b = tuple(int(v * 0.88) for v in K1)                                         # soft mid-shadow
    VEIN = (176, 118, 104)
    # front: pec fibres, delt tie-in, graded ab blocks, linea alba light, oblique lines, lower veins
    sk.line("body", F, [(2, 3), (5, 4)], C1b); sk.line("body", F, [(13, 3), (10, 4)], C1b)   # pec fibre line
    P("body", F, 0, 1, C0); P("body", F, 15, 1, C0); P("body", F, 0, 2, C2); P("body", F, 15, 2, C2)
    for y0 in (7, 10, 13):
        for xs in ((4, 6), (9, 11)):
            sk.rect("body", F, xs[0], y0 + 1, xs[1], y0 + 1, K1 + (255,))
            P("body", F, xs[0], y0 + 1, C1b); P("body", F, xs[1], y0 + 1, C1b)
    for y in range(7, 15, 2):
        P("body", F, 6, y, C1b); P("body", F, 9, y, C1b)
    sk.line("body", F, [(1, 7), (2, 13)], C1b); sk.line("body", F, [(14, 7), (13, 13)], C1b)
    sk.line("body", F, [(4, 14), (5, 15)], VEIN); sk.line("body", F, [(11, 14), (10, 15)], VEIN)
    sk.line("body", F, [(12, 8), (14, 11)], (214, 160, 140)); sk.line("body", F, [(13, 8), (12, 11)], (214, 160, 140))   # old crossed scar
    # back: erector columns, rhomboids, teres, scar
    sk.line("body", B, [(6, 6), (6, 15)], C0); sk.line("body", B, [(9, 6), (9, 15)], C0)
    sk.line("body", B, [(5, 3), (6, 5)], C2); sk.line("body", B, [(10, 3), (9, 5)], C2)
    sk.line("body", B, [(1, 3), (2, 5)], C2); sk.line("body", B, [(14, 3), (13, 5)], C2)
    for y in (4, 6):
        P("body", B, 3, y, CH); P("body", B, 12, y, CH)
    sk.line("body", B, [(3, 12), (5, 10)], (214, 160, 140))
    for side in ("left", "right"):
        sk.line("body", side, [(3, 1), (3, 10)], C0); P("body", side, 2, 13, C2)
    # arms: brachialis, forearm muscle split, branching veins, triceps horseshoe
    for arm in ARMS:
        for side in SIDES:
            P(arm, side, 2, 6, C1b); P(arm, side, 2, 7, C2)                            # brachialis
            sk.line(arm, side, [(4, 10), (4, 13)], C1b)
            P(arm, side, 6, 11, CH)
            sk.line(arm, side, [(3, 5), (2, 6)], VEIN); sk.line(arm, side, [(4, 12), (3, 13)], VEIN)
            P(arm, side, 1, 3, C1b)
        sk.line(arm, "back", [(2, 2), (2, 7)], C2); sk.line(arm, "back", [(5, 2), (5, 6)], CH); sk.line(arm, "back", [(3, 7), (4, 7)], C2)
        P(arm, "front", 6, 2, (255, 255, 255), 200)
        # bracers: engraved pattern, scratched metal, faceted gem with a glow halo
        for side in SIDES:
            for x in range(0, 8, 2):
                P(arm, side, x, 16, (96, 100, 114)); P(arm, side, x + 1, 19, (52, 54, 64))
            sk.line(arm, side, [(1, 15), (2, 16)], (170, 176, 190)); P(arm, side, 6, 19, (170, 176, 190))
            sk.rect(arm, side, 3, 16, 4, 19, (60, 220, 100, 255))
            P(arm, side, 3, 16, (230, 255, 230)); P(arm, side, 4, 17, (150, 255, 170)); P(arm, side, 3, 18, (40, 170, 70)); P(arm, side, 4, 19, (20, 110, 50))
            for (gx, gy) in ((2, 16), (5, 16), (2, 19), (5, 19)):
                P(arm, side, gx, gy, (90, 140, 100))                                   # glow halo on the metal
        x, y, fw, fh = Skin.face(PARTS[arm][0], PARTS[arm][1], "bottom")
        sk.d.rectangle((x, y, x + fw - 1, y + fh - 1), fill=C2 + (255,))
        for kx in range(1, fw, 2):
            sk.d.point((x + kx, y + 1), fill=C0 + (255,))                               # knuckles
    # sash: detailed knot and hanging cloth scraps with frayed ends
    sk.rect("body", F, 10, 16, 12, 19, t[2] + (255,)); sk.rect("body", F, 11, 16, 11, 17, t[0] + (255,)); P("body", F, 12, 19, t[3])
    for (x, l) in ((1, 4), (4, 3), (13, 4)):
        sk.rect("body", F, x, 20, x + 1, 19 + l, g[1] + (255,)); P("body", F, x + 1, 20, g[3])
        P("body", F, x, 20 + l, g[2]); P("body", F, x + 1, 19 + l, g[3])
    # trousers: deep folds, second tear with a scratch, cracked toe caps, scuffs
    for leg in LEGS:
        for side in SIDES:
            sk.line(leg, side, [(6, 1), (5, 6)], g[3]); sk.line(leg, side, [(1, 9), (3, 11), (6, 9)], g[3])
            P(leg, side, 2, 20, (110, 114, 126)); P(leg, side, 6, 22, (110, 114, 126))
        P(leg, "front", 3, 21, (90, 70, 40)); P(leg, "front", 4, 22, (90, 70, 40))     # cracked toe cap
    for side in ("back", "right"):
        sk.rect("rightLeg", side, 3, 3, 5, 5, K1 + (255,)); P("rightLeg", side, 4, 4, (190, 84, 80))
        for x in (2, 6):
            P("rightLeg", side, x, 4, g[3])
    # hair: extra flame-like lock edges and a glowing rim
    for side in ("left", "right", "back"):
        rows = 14 if side == "back" else 8
        for x in range(1, 16, 4):
            sk.line("head", side, [(x, 3), (x + 1, rows)], PARTC)
            P("head", side, x + 2, 2, (250, 255, 200))
        sk.line("head", side, [(0, rows), (15, rows)], (130, 180, 50))
    for x in range(2, 16, 4):
        sk.line("head", "top", [(x, 0), (x + 2, 15)], PARTC); sk.line("head", "top", [(x + 1, 0), (x + 3, 15)], HI)

    # ---- green flame aura, lime lightning, embers
    ego_flames(sk, 923, cols=((20, 90, 30), (40, 170, 50), (120, 230, 80), (230, 255, 150)))
    rnd = random.Random(924)
    for p in ("body",) + tuple(ARMS):
        for side in ("left", "right", "back"):
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            if fw < 6:
                continue
            x, y = rnd.randrange(2, fw - 4), rnd.randrange(2, 10)
            pts = [(x, y), (x + 1, y + 1), (x, y + 2), (x + 2, y + 3), (x + 1, y + 4)]
            sk.line(p, side, pts, (20, 90, 30, 220)); sk.line(p, side, [(px + 1, py) for px, py in pts], (200, 255, 150, 230))
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            x, y = rnd.randrange(2, fw - 2), rnd.randrange(1, fh - 1)
            P(p, side, x, y, (220, 255, 180), 150)
    for p in ("body",) + tuple(ARMS):
        for side in (("left", "right") if p == "body" else SIDES):
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for edge in (1, fw - 2):
                for y in range(0, fh, 3):
                    P(p, side, edge, y, (170, 255, 140), 140)                           # inner lime glow line
    for leg in LEGS:
        for side in SIDES:
            sk.rect(leg, side, 0, 23, 7, 23, (40, 110, 40, 150))                         # green haze at the feet
            P(leg, side, 1, 22, (150, 255, 120), 170); P(leg, side, 6, 21, (150, 255, 120), 140)
    for arm in ARMS:
        for xx in (1, 4, 6):
            sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (190, 255, 150, 130))

def petals(sk, seed, n=2, cols=((255, 170, 210), (255, 226, 240), (230, 90, 160))):
    """Small drifting blossom petals: a 2x2 diamond-ish fleck with a bright tip."""
    rnd = random.Random(seed)
    for p in PARTS:
        if p == "head":
            continue
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[p][0], PARTS[p][1], side)
            for _ in range(n):
                x, y = rnd.randrange(1, fw - 2), rnd.randrange(1, fh - 2)
                c = rnd.choice(cols)
                sk.rect(p, side, x, y, x, y, c + (255,)); sk.rect(p, side, x + 1, y + 1, x + 1, y + 1, c + (255,))
                sk.rect(p, side, x + 1, y, x + 1, y, (255, 245, 250, 255))

@design("saiyan_bloom", "Saiyan: Divine Bloom", "full")
def _(sk):
    """Divine Bloom (original pink form): rose-to-blush hair with pearl-white highlights and plum
    partings; composed smirk with glowing pink eyes; deep plum gi with rose-gold trim, pink sash and
    a blossom crest on the back; toned forearms; soft pink flame aura with drifting blossom petals."""
    global SGI, SGI_TRIM, SSASH
    HAIR, HI, PARTC, EYE, GLOW = (238, 110, 176), (255, 208, 234), (140, 36, 96), (236, 70, 150), (255, 160, 210)
    GI, TRIM, SASH = (58, 34, 62), (232, 156, 132), (224, 96, 154)
    old = (SGI, SGI_TRIM, SSASH)
    SGI, SGI_TRIM, SSASH = GI, TRIM, SASH
    try:
        k = ramp(SKIN_S); K0, K1, K2, K3 = k
        g = ramp(GI); t = ramp(TRIM); sh = ramp(SASH)
        C0 = lt(K1, 1.1); CH = lt(K1, 1.2); C2 = tuple(int(v * 0.78) for v in K1); C3 = tuple(int(v * 0.66) for v in K1)
        S1 = tuple(int(v * 0.9) for v in K1); S2 = tuple(int(v * 0.82) for v in K1)
        def P(part, side, x, y, c, a=255):
            sk.rect(part, side, x, y, x, y, c[:3] + (a,))
        F, B = "front", "back"
        saiyan_body(sk, 930, gi=GI, trim=TRIM, sash=SASH)
        saiyan_detail(sk, GLOW, 931)
        saiyan_detail_plus(sk, GLOW, HAIR, 932)
        # pink sash over the rose-gold band, with a bow knot and long tails
        for side in SIDES:
            _, _, fw, _ = Skin.face(PARTS["body"][0], PARTS["body"][1], side)
            sk.rect("body", side, 0, 17, fw - 1, 18, sh[1] + (255,))
            for x in range(0, fw, 3):
                P("body", side, x, 17, sh[0]); P("body", side, x + 1, 18, sh[2])
        sk.rect("body", F, 9, 16, 12, 19, sh[2] + (255,)); sk.rect("body", F, 10, 16, 11, 17, sh[0] + (255,))
        sk.line("body", F, [(10, 20), (9, 23)], sh[1]); sk.line("body", F, [(11, 20), (12, 23)], sh[1]); P("body", F, 12, 23, sh[3])
        # undershirt sculpted over the chest (plum sheen on pecs and abs)
        SH0, SH1, SH3 = (104, 70, 108), (60, 44, 66), (16, 12, 20)
        sk.rect("body", F, 4, 1, 6, 2, SH1 + (255,)); sk.rect("body", F, 9, 1, 11, 2, SH1 + (255,))
        P("body", F, 4, 1, SH0); P("body", F, 11, 1, SH0); P("body", F, 5, 1, (150, 110, 150))
        sk.line("body", F, [(4, 3), (7, 4)], SH3); sk.line("body", F, [(11, 3), (8, 4)], SH3)
        sk.line("body", F, [(7, 1), (7, 10)], SH3)
        for y in (6, 8):
            P("body", F, 6, y, SH0); P("body", F, 8, y, SH1); P("body", F, 6, y + 1, SH3)
        # blossom crest on the back (five petals, gold centre)
        sk.rect("body", B, 4, 2, 11, 10, g[1] + (255,))
        for (cx, cy) in ((7, 3), (10, 5), (9, 8), (5, 8), (4, 5)):
            sk.rect("body", B, cx, cy, cx + 1, cy + 1, sh[0] + (255,)); P("body", B, cx, cy, (255, 230, 242))
        sk.rect("body", B, 7, 6, 8, 7, t[0] + (255,)); P("body", B, 7, 6, (255, 250, 220))
        # lapel rose-gold piping and plum folds
        sk.line("body", F, [(2, 0), (7, 11)], t[0]); sk.line("body", F, [(13, 0), (8, 11)], t[0])
        for side in ("left", "right", B):
            sk.line("body", side, [(2, 12), (4, 15)], g[3]); sk.line("body", side, [(3, 12), (5, 15)], g[0])
        # toned forearms with light and a vein
        for arm in ARMS:
            for side in SIDES:
                sk.rect(arm, side, 0, 7, 7, 16, K1 + (255,))
                sk.rect(arm, side, 0, 7, 1, 16, C2 + (255,))
                sk.rect(arm, side, 5, 8, 6, 13, C0 + (255,)); P(arm, side, 6, 9, CH)
                sk.line(arm, side, [(2, 8), (3, 11), (2, 15)], C2); sk.line(arm, side, [(4, 13), (6, 16)], C2)
                sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (180, 124, 110))
                sk.line(arm, side, [(7, 7), (7, 16)], GLOW + (150,))
                for x in range(0, 8, 2):
                    P(arm, side, x, 6, t[0]); P(arm, side, x + 1, 6, t[2])                 # rose-gold cuff
        # hair: layered rose locks with pearl highlights
        saiyan_hair_paint(sk, HAIR)
        h = ramp(HAIR)
        for side in ("left", "right", "back", "top"):
            rows = 15 if side == "top" else (14 if side == "back" else 8)
            for x in range(16):
                n = (x * 7 + len(side)) % 5
                sk.line("head", side, [(x, 0), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], h[0] if n in (1, 3) else h[1])
                if n == 1:
                    sk.line("head", side, [(x, 0), (x, 2)], HI)
                if n == 4:
                    sk.line("head", side, [(x, 3), (x, rows - 1)], PARTC)
            if side != "top":
                for x in range(0, 16, 4):
                    sk.line("head", side, [(x, 2), (x + 2, rows - 2)], HI + (150,))
                for x in range(0, 16, 3):
                    P("head", side, x, rows + 2, (255, 230, 245)); P("head", side, x + 1, rows + 2, GLOW)
        for x in range(16):
            P("head", F, x, 0, HI if x % 3 == 0 else h[0])
        hair_glow_edges(sk, GLOW, alpha=200)
        # face: composed smirk with glowing pink eyes
        saiyan_face(sk, "smirk", eye=EYE, brow_col=(110, 30, 80))
        for x0 in (3, 10):
            ix = x0 + (1 if x0 == 3 else 0)
            P("head", F, ix + (1 if x0 == 3 else 0), 9, (150, 24, 90))                  # iris depth
            P("head", F, ix, 8, (255, 236, 246))                                        # catch-light
            sk.rect("head", F, x0, 10, x0 + 2, 10, lt(K1, 1.14) + (255,))
            sk.rect("head", F, x0, 10, x0 + 2, 10, (255, 150, 200, 60))
        sk.rect("head", F, 7, 8, 7, 10, lt(K1, 1.06) + (255,)); P("head", F, 8, 11, S2)
        for x in (1, 2, 13, 14):
            P("head", F, x, 10, C0)
        sk.rect("head", F, 0, 11, 0, 15, S2 + (255,)); sk.rect("head", F, 15, 11, 15, 15, S2 + (255,))
        sk.rect("head", F, 1, 12, 2, 15, S1 + (255,)); sk.rect("head", F, 13, 12, 14, 15, S1 + (255,))
        sk.rect("head", F, 5, 15, 10, 15, S1 + (255,))
        for side in ("left", "right"):
            sk.rect("head", side, 9, 9, 10, 12, K2 + (255,)); P("head", side, 10, 9, K0)
            P("head", side, 9, 13, (255, 190, 220)); P("head", side, 9, 14, t[0])       # small rose-gold earring stud
        # boots: rose-gold toe caps
        for leg in LEGS:
            sk.rect(leg, F, 1, 21, 6, 22, t[1] + (255,)); sk.rect(leg, F, 1, 21, 6, 21, t[0] + (255,))
        # aura: soft pink flames, petals, pale motes
        ego_flames(sk, 933, cols=((150, 30, 90), (220, 70, 140), (255, 140, 200), (255, 226, 242)))
        petals(sk, 934, n=1)
        for arm in ARMS:
            for xx in (1, 4, 6):
                sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (255, 190, 225, 130))
    finally:
        SGI, SGI_TRIM, SSASH = old

@design("saiyan_battle_damaged", "Saiyan: Battle Damaged", "full")
def _(sk):
    """Battle-damaged Base Saiyan (high detail): the gi top ripped diagonally from the left shoulder
    to the right hip, showing a sculpted chest and abs; left sleeve torn away, right sleeve ragged;
    one wristband torn; shredded knees and thigh; bruises, scrapes, dust and scorch marks; messy
    dusty black hair; the base smirk with a bruised eye, a cut lip and a cheek scrape; faint smoke."""
    k = ramp(SKIN_S); K0, K1, K2, K3 = k
    g = ramp(SGI); t = ramp(SGI_TRIM); u = ramp(SUNDER)
    C0 = lt(K1, 1.1); CH = lt(K1, 1.2); C2 = tuple(int(v * 0.78) for v in K1); C3 = tuple(int(v * 0.66) for v in K1)
    S1 = tuple(int(v * 0.9) for v in K1); S2 = tuple(int(v * 0.82) for v in K1)
    BRUISE, BRUISE2, SCRAPE, SCRAPE_HI = (150, 104, 120), (124, 84, 104), (176, 62, 58), (214, 110, 100)
    DUST, SCORCH = (150, 136, 116), (40, 36, 34)
    def P(part, side, x, y, c, a=255):
        sk.rect(part, side, x, y, x, y, c[:3] + (a,))
    F, B = "front", "back"
    saiyan_body(sk, 940, damage=0)
    saiyan_detail(sk, (255, 236, 200), 941)
    saiyan_detail_plus(sk, (255, 236, 200), (30, 28, 34), 942)

    # ---- diagonal rip across the gi top: chest and abs exposed
    for y in range(0, 16):
        xa = max(0, 1 + y // 3)                                                  # tear runs left-shoulder -> right-hip
        xb = min(15, 8 + y // 2)
        sk.rect("body", F, xa, y, xb, y, K1 + (255,))
        P("body", F, xa - 1 if xa > 0 else 0, y, g[3]); P("body", F, xb + 1 if xb < 15 else 15, y, g[3])
        if y % 2 == 0 and xb < 14:
            P("body", F, xb + 1, y, u[1])                                         # torn undershirt edge
    sk.rect("body", F, 1, 1, 6, 4, C0 + (255,)); sk.rect("body", F, 9, 1, 10, 3, C0 + (255,))   # pecs
    sk.rect("body", F, 2, 1, 4, 2, CH + (255,))
    sk.line("body", F, [(1, 5), (3, 6), (7, 6)], C3); sk.line("body", F, [(10, 5), (8, 6)], C3)
    sk.line("body", F, [(7, 1), (7, 15)], C3); sk.line("body", F, [(8, 2), (8, 15)], C2)
    for y0 in (7, 10, 13):
        sk.line("body", F, [(4, y0 + 2), (6, y0 + 2)], C2); sk.line("body", F, [(9, y0 + 2), (11, y0 + 2)], C2)
        P("body", F, 5, y0, CH); P("body", F, 10, y0, CH); P("body", F, 4, y0, C0); P("body", F, 9, y0, C0)
    sk.line("body", F, [(3, 8), (3, 14)], C2)
    sk.line("body", F, [(2, 2), (5, 5)], SCRAPE); P("body", F, 3, 3, SCRAPE_HI)              # scrapes across the chest
    sk.line("body", F, [(9, 9), (11, 11)], SCRAPE)
    sk.rect("body", F, 5, 11, 6, 12, BRUISE + (255,)); P("body", F, 6, 12, BRUISE2)        # bruise on the ribs
    P("body", F, 4, 2, (255, 255, 255), 200); P("body", F, 10, 8, (255, 255, 255), 170)     # sweat
    for (x, y) in ((12, 2), (13, 5), (14, 3)):
        P("body", F, x, y, SCORCH)                                                  # scorch on the remaining cloth
    sk.line("body", F, [(12, 3), (14, 6)], (70, 60, 54))
    # back: rips and scorch, crest scratched
    for (x, y, w) in ((2, 11, 3), (10, 12, 3)):
        sk.rect("body", B, x, y, x + w - 1, y + 2, K1 + (255,)); P("body", B, x + 1, y + 1, SCRAPE)
        P("body", B, x - 1, y + 1, g[3]); P("body", B, x + w, y + 1, g[3])
    sk.line("body", B, [(4, 3), (6, 9)], (12, 60, 66)); P("body", B, 12, 4, SCORCH); P("body", B, 13, 5, SCORCH)
    for side in ("left", "right"):
        sk.rect("body", side, 1, 6, 2, 8, K1 + (255,)); P("body", side, 1, 7, BRUISE)

    # ---- arms: left sleeve torn away, right sleeve ragged, left wristband torn
    for arm in ARMS:
        for side in SIDES:
            top = 1 if arm == "leftArm" else 7
            sk.rect(arm, side, 0, top, 7, 16, K1 + (255,))
            sk.rect(arm, side, 0, top, 1, 16, C2 + (255,))
            if arm == "leftArm":
                for x in range(8):
                    P(arm, side, x, 0, g[3] if x % 2 else g[2])
                sk.rect(arm, side, 4, 2, 6, 3, C0 + (255,)); sk.line(arm, side, [(3, 4), (4, 4)], C2)
                sk.rect(arm, side, 4, 5, 6, 6, S1 + (255,)); P(arm, side, 5, 5, C0); P(arm, side, 3, 7, C2)
            else:
                for x in range(0, 8, 2):
                    P(arm, side, x, 6, K1); P(arm, side, x + 1, 7, g[3])              # ragged hem
            sk.rect(arm, side, 5, 9, 6, 13, C0 + (255,))
            sk.line(arm, side, [(2, 9), (3, 12), (2, 15)], C2); sk.line(arm, side, [(4, 13), (6, 16)], C2)
            sk.line(arm, side, [(5, 10), (4, 12), (5, 14)], (180, 124, 110))
        # torn left wristband with a scraped wrist
        for side in SIDES:
            sk.rect("leftArm", side, 0, 17, 7, 18, K1 + (255,)); P("leftArm", side, 3, 17, SCRAPE)
            for x in range(0, 8, 2):
                P("leftArm", side, x, 19, K1)
    for side in ("front", "right"):
        sk.rect("leftArm", side, 4, 9, 5, 10, BRUISE + (255,)); P("leftArm", side, 5, 10, BRUISE2)
        sk.line("rightArm", side, [(2, 10), (4, 13)], SCRAPE); P("rightArm", side, 3, 11, SCRAPE_HI)
    sk.fill("leftArm", ("top",), K1)

    # ---- legs: shredded knees and a torn thigh, dust and scuffed boots
    for leg in LEGS:
        for side in SIDES:
            for _ in range(1):
                pass
            sk.line(leg, side, [(1, 2), (3, 7)], g[3]); sk.line(leg, side, [(2, 2), (4, 7)], g[0])
        for side in ("front", "left" if leg == "leftLeg" else "right"):
            sk.rect(leg, side, 2, 8, 5, 11, K1 + (255,)); P(leg, side, 3, 9, SCRAPE); P(leg, side, 4, 10, C2)
            for x in range(1, 7):
                P(leg, side, x, 7 + (x % 2), g[3]); P(leg, side, x, 12 - (x % 2), g[3])
    sk.rect("rightLeg", F, 4, 2, 6, 4, K1 + (255,)); P("rightLeg", F, 5, 3, BRUISE); P("rightLeg", F, 3, 3, g[3]); P("rightLeg", F, 7, 3, g[3])
    rnd = random.Random(945)
    for part in ("body",) + tuple(LEGS):
        for side in SIDES:
            _, _, fw, fh = Skin.face(PARTS[part][0], PARTS[part][1], side)
            for _ in range(3):
                x = rnd.randrange(1, fw - 3); y = rnd.randrange(16, 23) if part == "body" else rnd.randrange(0, 23)
                sk.rect(part, side, x, y, x + 1, y, DUST + (150,))                      # dust smudges
    for leg in LEGS:
        for side in SIDES:
            P(leg, side, 2, 20, (110, 114, 126)); P(leg, side, 6, 22, (110, 114, 126)); P(leg, side, 4, 18, DUST)
        P(leg, F, 3, 21, (120, 90, 40)); P(leg, F, 4, 22, (120, 90, 40))              # scratched toe cap

    # ---- hair: messy black with dust and stray strands
    saiyan_hair_paint(sk, (30, 28, 34))
    h = ramp((30, 28, 34))
    for side in ("left", "right", "back", "top"):
        rows = 15 if side == "top" else (14 if side == "back" else 8)
        for x in range(16):
            n = (x * 7 + len(side)) % 5
            sk.line("head", side, [(x, 0), (x, min(rows, 2 + n + (6 if side == "back" else 2)))], h[0] if n in (1, 3) else h[1])
            if n == 4:
                sk.line("head", side, [(x, 3), (x, rows - 1)], (12, 10, 16))
        for x in range(2, 16, 5):
            P("head", side, x, 3, (96, 90, 84)); P("head", side, x + 1, 4, (70, 66, 62))   # dust in the hair
    for x in range(0, 16, 3):
        P("head", F, x, 5, (24, 22, 28))                                              # stray strands over the brow

    # ---- the base smirk, now bruised and cut
    saiyan_face(sk, "smirk")
    sk.rect("head", F, 10, 7, 13, 7, BRUISE2 + (255,)); P("head", F, 13, 8, BRUISE); P("head", F, 13, 9, BRUISE)   # bruised eye
    sk.rect("head", F, 10, 10, 12, 10, BRUISE + (255,))
    sk.rect("head", F, 10, 8, 12, 9, (250, 250, 246, 255)); sk.rect("head", F, 10, 8, 11, 9, (30, 26, 24, 255))
    P("head", F, 10, 8, (255, 255, 255)); P("head", F, 12, 8, (226, 210, 206))          # eye squinting slightly
    sk.rect("head", F, 10, 7, 12, 7, (36, 26, 22, 255))
    sk.line("head", F, [(1, 9), (3, 11)], SCRAPE); P("head", F, 2, 10, SCRAPE_HI)        # cheek scrape
    P("head", F, 9, 13, SCRAPE); P("head", F, 9, 14, (150, 40, 40))                     # cut lip
    P("head", F, 2, 6, (255, 255, 255), 200)                                            # sweat
    sk.rect("head", F, 5, 15, 7, 15, DUST + (255,))                                     # dirt on the chin
    for side in ("left", "right"):
        P("head", side, 4, 11, BRUISE); P("head", side, 5, 12, DUST)

    # ---- faint smoke rising from the shoulders
    for arm in ARMS:
        for xx in (1, 4, 6):
            sk.line(arm, "top", [(xx, 6), (xx + 1, 3), (xx, 1)], (180, 176, 170, 140))

EXTRA_UV = {e[0]: e[2] for e in EXTRAS}
EXTRA_SIZE = {e[0]: e[3] for e in EXTRAS}

def paint_extras(sk, names, col, tip=None, seed=0):
    for i, n in enumerate(names):
        c = tip if (tip and i == len(names) - 1) else col
        sk.fill((EXTRA_UV[n], EXTRA_SIZE[n]), ALL, c, shade=0.12, seed=seed + i)

ANTENNAE = ["antenna_r", "antenna_r2", "antenna_l", "antenna_l2"]
TENDRIL = ["tendril", "tendril2", "tendril3"]
HORNS_R = ["horn_r", "horn_r2", "horn_r3"]
HORNS_L = ["horn_l", "horn_l2", "horn_l3"]
IVORY = (232, 224, 204)

def horns(sk, col, seed):
    """Horns in the form's own colour, a shade darker toward the tip."""
    for side in (HORNS_R, HORNS_L):
        for i, n in enumerate(side):
            sk.fill((EXTRA_UV[n], EXTRA_SIZE[n]), ALL, dk(col, 1.0 - 0.12 * i), shade=0.1, seed=seed + i)
        sk.fill((EXTRA_UV[side[1]], EXTRA_SIZE[side[1]]), SIDES, dk(col, 0.8), rows=(3, 4))  # ring

def paint_tendril(sk, size, col, seed):
    for i, ext in enumerate(tendril_extras(TENDRIL_SIZES[size])):
        _, _, uv, sz, *_ = ext
        sk.fill((uv, sz), ALL, col if i < len(TENDRIL_SIZES[size]) - 1 else lt(col, 1.06), shade=0.1, seed=seed + i)

# ---- Write everything ---------------------------------------------------------------
if __name__ == "__main__":
    w(f"{RP}/models/entity/form_overlay.geo.json", geometry())
    no_horns_or_tendril = [e for e in EXTRAS if not e[0].startswith(("horn", "tendril"))]
    for size in TENDRIL_SIZES:
        w(f"{RP}/models/entity/form_overlay_majin_{size}.geo.json",
          geometry(f"geometry.dbz.form_overlay_majin_{size}", no_horns_or_tendril + tendril_extras(TENDRIL_SIZES[size])))
    GEO_FOR = {"super_majin": "geometry.dbz.form_overlay_majin_l", "majin_base": "geometry.dbz.form_overlay_majin_m",
               "majin_super": "geometry.dbz.form_overlay_majin_l"}  # Kid Majin uses the small default tendril
    os.makedirs(f"{RP}/textures/entity/forms", exist_ok=True)
    lang = open(f"{RP}/texts/en_US.lang").read()
    for fid, (name, kind, fn) in DESIGNS.items():
        sk = Skin(); fn(sk); hd_finish(sk); sk.save(f"{RP}/textures/entity/forms/{fid}.png")
        iid = f"dbz:form_{fid}"
        w(f"{BP}/items/form_{fid}.json", {"format_version": "1.21.50", "minecraft:item": {
            "description": {"identifier": iid, "menu_category": {"category": "none"}},
            "components": {"minecraft:icon": "dbz_hair",
                           "minecraft:display_name": {"value": f"{name} (Transformation)"},
                           "minecraft:max_stack_size": 1,
                           "minecraft:wearable": {"slot": "slot.armor.head", "protection": 0}}}})
        w(f"{RP}/attachables/form_{fid}.json", {"format_version": "1.10.0", "minecraft:attachable": {
            "description": {
                "identifier": iid,
                "materials": {"default": "armor", "enchanted": "armor_enchanted"},
                "textures": {"default": f"textures/entity/forms/{fid}", "enchanted": "textures/misc/enchanted_item_glint"},
                "geometry": {"default": GEO_FOR.get(fid, "geometry.dbz.form_overlay")},
                # Full-body looks hide the player's hat layer; see-through ones keep the player's hair.
                "scripts": {"parent_setup": "variable.helmet_layer_visible = 0.0;" if kind == "full" else "variable.helmet_layer_visible = 1.0;"},
                "render_controllers": ["controller.render.armor"]}}})
        key = f"item.{iid}"
        if key not in lang:
            lang += f"\n{key}={name} (Transformation)"
    open(f"{RP}/texts/en_US.lang", "w").write(lang.rstrip("\n") + "\n")
    print("forms:", ", ".join(DESIGNS))
