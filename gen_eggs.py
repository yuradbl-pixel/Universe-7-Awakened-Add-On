# Detailed 128x128 spawn egg icons built from each NPC's final skin texture.
# Run AFTER gen_npcs.py (it reads textures/entity/npc/<id>.png).
import json, os, sys, math
from PIL import Image, ImageDraw, ImageFilter
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
RP = "/home/claude/dbz/DBZ_RP"
OUT = f"{RP}/textures/items/eggs"
os.makedirs(OUT, exist_ok=True)

def hexrgb(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

def face(skin, box, over=None):
    s = max(1, skin.width // 64)
    f = skin.crop(tuple(v * s for v in box)).convert("RGBA")
    if over:
        o = skin.crop(tuple(v * s for v in over)).convert("RGBA")
        f.alpha_composite(o)
    return f

def affine_face(canvas, img, origin, u, v, shade):
    """Draw img onto canvas so its x axis follows u and y axis follows v (per source pixel)."""
    w, h = img.size
    det = u[0] * v[1] - u[1] * v[0]
    a, b = v[1] / det, -v[0] / det
    d, e = -u[1] / det, u[0] / det
    c = -(a * origin[0] + b * origin[1])
    f = -(d * origin[0] + e * origin[1])
    if shade != 1.0:
        px = img.load()
        img = img.copy(); px = img.load()
        for y in range(h):
            for x in range(w):
                r, g, bb, al = px[x, y]
                px[x, y] = (int(r * shade), int(g * shade), int(bb * shade), al)
    layer = img.transform(canvas.size, Image.AFFINE, (a, b, c, d, e, f), resample=Image.NEAREST)
    canvas.alpha_composite(layer)

def iso_head(skin, size=70, center=(64, 76)):
    """Isometric head from a player-layout skin: top, front (viewer's left) and the
    character's left side (viewer's right), each with its hat-layer overlay."""
    s = max(1, skin.width // 64)
    n = 8 * s  # face size in source pixels
    front = face(skin, (8, 8, 16, 16), (40, 8, 48, 16))
    side = face(skin, (16, 8, 24, 16), (48, 8, 56, 16))
    top = face(skin, (8, 0, 16, 8), (40, 0, 48, 8))
    # Three-quarter view that favours the face: the front is wide and only
    # slightly angled, the side is short and steep.
    fa, sa, side_len = math.radians(14), math.radians(42), 0.5
    kn = size / (math.cos(fa) + side_len * math.cos(sa))  # front edge length on screen
    front_vec = (math.cos(fa) * kn, math.sin(fa) * kn)     # L -> B along the front's top edge
    a = (side_len * math.cos(sa) * kn, -side_len * math.sin(sa) * kn)  # B -> back-right corner
    b = (-front_vec[0], -front_vec[1])                      # B -> L
    B = (center[0] - size / 2 + front_vec[0], center[1] - kn * 0.45)
    L = (B[0] + b[0], B[1] + b[1])
    T = (B[0] + a[0] + b[0], B[1] + a[1] + b[1])
    per = lambda v: (v[0] / n, v[1] / n)
    down = (0, kn / n)
    canvas = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    affine_face(canvas, top, T, per((-b[0], -b[1])), per((-a[0], -a[1])), 1.06)   # top
    affine_face(canvas, front, L, per((-b[0], -b[1])), down, 0.94)                 # front
    affine_face(canvas, side, B, per(a), down, 0.72)                               # side
    return canvas

def egg_base(c1, c2, boss):
    S = 512
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    box = (88, 24, 424, 496)
    # Radial-ish gradient: light center-left to darker edges
    for i in range(60):
        t = i / 60
        col = tuple(int(c1[k] * (0.62 + 0.5 * t)) if c1[k] * (0.62 + 0.5 * t) < 255 else 255 for k in range(3))
        inset = t * 150
        d.ellipse((box[0] + inset * 0.9 - 20 * t, box[1] + inset * 0.8 - 25 * t, box[2] - inset * 1.1 - 20 * t, box[3] - inset * 1.2), fill=col + (255,))
    # Speckles in the overlay color
    import random
    rnd = random.Random(hash(c1 + c2) & 0xffff)
    mask = Image.new("L", (S, S), 0); ImageDraw.Draw(mask).ellipse(box, fill=255)
    spots = Image.new("RGBA", (S, S), (0, 0, 0, 0)); sd = ImageDraw.Draw(spots)
    for _ in range(26):
        x = rnd.randint(box[0], box[2]); y = rnd.randint(box[1], box[3]); r = rnd.randint(9, 26)
        sd.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), fill=c2 + (235,))
    spots.putalpha(Image.composite(spots.getchannel("A"), Image.new("L", (S, S), 0), mask))
    im.alpha_composite(spots)
    # Outline + gloss
    d = ImageDraw.Draw(im)
    d.ellipse(box, outline=(25, 25, 32, 255), width=14)
    if boss:
        d.ellipse((box[0] - 6, box[1] - 6, box[2] + 6, box[3] + 6), outline=(200, 30, 40, 255), width=10)
    gl = Image.new("RGBA", (S, S), (0, 0, 0, 0)); gd = ImageDraw.Draw(gl)
    gd.ellipse((150, 70, 250, 190), fill=(255, 255, 255, 120))
    im.alpha_composite(gl.filter(ImageFilter.GaussianBlur(12)))
    return im.resize((128, 128), Image.LANCZOS)

def badge(role):
    S = 512
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    cx, cy, r = 400, 410, 82
    col = {"ally": (60, 170, 80), "trainer": (60, 120, 220), "boss": (200, 40, 50)}[role]
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (255,), outline=(20, 20, 26, 255), width=12)
    w = (255, 255, 255, 255)
    if role == "ally":      # shield
        d.polygon([(cx - 40, cy - 42), (cx + 40, cy - 42), (cx + 40, cy + 2), (cx, cy + 48), (cx - 40, cy + 2)], fill=w)
    elif role == "trainer":  # star
        pts = []
        for i in range(10):
            a = -math.pi / 2 + i * math.pi / 5; rr = 50 if i % 2 == 0 else 21
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        d.polygon(pts, fill=w)
    else:                    # crown
        d.polygon([(cx - 48, cy + 30), (cx - 48, cy - 30), (cx - 22, cy - 2), (cx, cy - 42), (cx + 22, cy - 2),
                   (cx + 48, cy - 30), (cx + 48, cy + 30)], fill=(255, 215, 70, 255))
    return im.resize((128, 128), Image.LANCZOS)

def build_all(npcs):
    """npcs: dict id -> spec with 'egg' (two hex colors) and 'role'."""
    it_path = f"{RP}/textures/item_texture.json"
    it = json.load(open(it_path))
    for nid, spec in npcs.items():
        skin_path = f"{RP}/textures/entity/npc/{nid}.png"
        if not os.path.exists(skin_path):
            continue
        skin = Image.open(skin_path).convert("RGBA")
        c1, c2 = hexrgb(spec["egg"][0]), hexrgb(spec["egg"][1])
        icon = egg_base(c1, c2, spec["role"] == "boss")
        head = iso_head(skin)
        # soft drop shadow under the head
        sh = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        sh.paste((0, 0, 0, 120), (0, 0), head.getchannel("A"))
        icon.alpha_composite(sh.filter(ImageFilter.GaussianBlur(3)), (2, 3))
        icon.alpha_composite(head)
        icon.alpha_composite(badge(spec["role"]))
        icon.save(f"{OUT}/{nid}.png")
        it["texture_data"][f"dbz_egg_{nid}"] = {"textures": f"textures/items/eggs/{nid}"}
        ce_path = f"{RP}/entity/npcs/{nid}.entity.json"
        ce = json.load(open(ce_path))
        ce["minecraft:client_entity"]["description"]["spawn_egg"] = {"texture": f"dbz_egg_{nid}", "texture_index": 0}
        json.dump(ce, open(ce_path, "w"), indent=2)
    json.dump(it, open(it_path, "w"), indent=2)
