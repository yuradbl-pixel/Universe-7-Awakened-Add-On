# Player transformation hair, v2 (v1.46).
# Original spike arrangements in the general anime style of each tier; tapered
# spikes from hairlib.spike(). Rotation convention (checked in game):
#   +rx tips a spike's top toward the FRONT (-z); -rx sweeps it BACK (+z)
#   +rz tips a spike's top toward +x;            -rz toward -x
# Head cube: x,z in [-4, 4], y in [24, 32].
import json, os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hairlib import spike
from PIL import Image, ImageDraw

RP = "/home/claude/dbz/DBZ_RP"
BP = "/home/claude/dbz/DBZ_BP"
UV_SPIKE, UV_CAP = [0, 0], [32, 0]

def w(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(json.dumps(o, indent=2) + "\n")

def shell():
    """Hair coverage hugging the head: top + hairline, and the sides/back behind the ears."""
    return [
        {"origin": [-4.4, 29.4, -4.4], "size": [8.8, 2.9, 8.8], "uv": UV_CAP},
        {"origin": [-4.4, 24.6, -1.2], "size": [8.8, 4.9, 5.6], "uv": UV_CAP},
    ]

def S(x, y, z, rx, rz, L, wd):
    return spike(x, y, z, rx, rz, L, wd, UV_SPIKE)

def crown(L, wd, tilt=-22, spread=1.0, rows=((-2.6, -1.6), (-0.9, -2.0), (0.9, -2.0), (2.6, -1.6), (-1.8, 1.4), (1.8, 1.4), (0, 0.2))):
    out = []
    for x, z in rows:
        out += S(x, 32.0, z, tilt - (8 if z > 0 else 0), round(x * 7 * spread), L * (1.08 if abs(x) < 1 else 1.0), wd)
    return out

def sides(L, wd, up=55, ys=(30.4, 28.6)):
    out = []
    for sx in (-1, 1):
        for i, y in enumerate(ys):
            out += S(sx * 4.2, y, -0.4 + i * 1.6, -12, sx * (up + i * 8), L - i, wd)
    return out

def back(L, wd, angle=-58, ys=(30.6, 28.2), xs=(-2.6, 0, 2.6)):
    out = []
    for j, y in enumerate(ys):
        for x in xs:
            out += S(x, y, 4.2, angle - j * 12, round(x * 6), L - j * 0.8, wd)
    return out

def bangs(items):
    out = []
    for x, rz, L, wd in items:
        out += S(x, 31.6, -4.4, 166, rz, L, wd)
    return out

STYLES = {
    # Tier 1: full upswept spikes, short layered bangs.
    "flare": lambda: shell() + crown(8.5, 3.0) + sides(5.5, 2.6) + back(6.5, 3.0)
                     + bangs([(-2.4, -10, 2.6, 2.2), (0.2, 4, 3.0, 2.2), (2.6, 12, 2.4, 2.0)]),
    # Tier 2: sharper and denser, slightly taller, one longer hanging bang.
    "flare_sharp": lambda: shell() + crown(10.0, 2.6, tilt=-18, spread=1.15)
                     + crown(7.0, 2.2, tilt=-34, rows=((-3.2, 0.2), (3.2, 0.2), (0, 2.6)))
                     + sides(6.5, 2.2, up=50) + back(7.5, 2.6)
                     + bangs([(-2.6, -12, 2.4, 1.9), (-0.6, 2, 5.2, 1.6), (2.4, 12, 2.4, 1.9)]),
    # Tier 3: crown spikes plus a long mane falling down the back.
    "mane": lambda: shell() + crown(7.5, 2.8, tilt=-30)
                     + back(16.0, 3.4, angle=-165, ys=(31.0, 29.0, 27.0), xs=(-3.0, -1.0, 1.0, 3.0))
                     + sides(9.0, 2.6, up=150, ys=(30.0, 28.0))
                     + bangs([(-2.4, -10, 3.0, 2.2), (0.4, 4, 3.4, 2.2), (2.6, 12, 2.8, 2.0)]),
    # Legendary: huge, wild spikes in every direction.
    "wild": lambda: shell() + crown(11.5, 3.4, tilt=-14, spread=1.4)
                     + crown(8.0, 3.0, tilt=-40, rows=((-3.4, 1.0), (3.4, 1.0), (0, 3.2), (-1.6, -3.4), (1.6, -3.4)))
                     + sides(8.0, 3.0, up=62) + back(8.5, 3.4)
                     + bangs([(-2.6, -16, 3.0, 2.4), (0.0, 0, 3.4, 2.4), (2.6, 16, 3.0, 2.4)]),
    # Wild and long: shaggy spikes on top and a long, ragged mane down the back.
    "wild_long": lambda: shell() + crown(9.0, 3.2, tilt=-26, spread=1.3)
                     + back(14.0, 3.6, angle=-160, ys=(31.0, 28.6, 26.6), xs=(-3.0, -1.0, 1.0, 3.0))
                     + sides(7.0, 3.0, up=110)
                     + bangs([(-2.8, -14, 3.2, 2.4), (-0.6, -2, 3.8, 2.2), (1.8, 10, 3.4, 2.2), (3.4, 18, 2.4, 2.0)]),
    # Divine tiers: neater, shorter spikes with a soft fringe.
    "short": lambda: shell() + crown(5.0, 2.6, tilt=-26, spread=0.9) + sides(3.5, 2.2, up=45) + back(4.5, 2.6)
                     + bangs([(-2.4, -8, 2.2, 2.2), (0.0, 2, 2.6, 2.2), (2.4, 10, 2.2, 2.0)]),
    # Swept back: long spikes pointing backward, a couple of loose front strands.
    "sleek": lambda: shell() + crown(9.0, 2.8, tilt=-78, spread=0.6) + back(8.0, 2.8, angle=-80)
                     + sides(6.0, 2.4, up=95) + bangs([(-1.8, -6, 2.2, 1.6), (2.0, 8, 2.0, 1.6)]),
}

# hair key -> (style, colour)
HAIRS = {
    "gold": ("flare", (255, 214, 60)),          # Super Saiyan
    "gold_sharp": ("flare_sharp", (255, 222, 80)),  # Super Saiyan 2
    "gold_long": ("mane", (255, 210, 58)),      # Super Saiyan 3
    "green": ("wild", (186, 240, 96)),           # Legendary
    "black_long": ("wild_long", (30, 28, 34)),   # Super Saiyan 4
    "red": ("short", (220, 44, 64)),             # Super Saiyan God
    "blue": ("flare", (72, 190, 255)),           # Super Saiyan Blue
    "black": ("short", (30, 30, 36)),            # Ultra Instinct -Sign-
    "silver": ("flare_sharp", (226, 232, 242)),  # Mastered Ultra Instinct / Beast
    "purple": ("sleek", (150, 72, 222)),         # Ultra Ego
    "pink": ("flare", (238, 110, 176)),          # Divine Bloom (original form)
}

def texture(col):
    """128x64: spike region (0..64) shaded root->tip with strands and a highlight band;
    cap region (64..128) with strands and a lit top edge."""
    hi = tuple(min(255, int(v * 1.2) + 30) for v in col)
    base = col
    sh = tuple(int(v * 0.72) for v in col)
    deep = tuple(int(v * 0.5) for v in col)
    im = Image.new("RGBA", (128, 64), base + (255,))
    d = ImageDraw.Draw(im)
    for y in range(64):
        t = y / 63
        c = tuple(int(hi[k] * (1 - t) + sh[k] * t) if t < 0.85 else int(deep[k]) for k in range(3))
        d.line((0, y, 63, y), fill=c + (255,))
    rnd = random.Random(sum(col))
    for x in range(0, 64, 3):
        d.line((x, 0, x + rnd.choice((-1, 0, 1)), 63), fill=sh + (255,))
    for x in range(1, 64, 6):
        d.line((x, 4, x, 26), fill=hi + (255,))                      # highlight streaks
    for y in range(64):
        t = y / 63
        c = tuple(int(base[k] * (1 - t * 0.3)) for k in range(3))
        d.line((64, y, 127, y), fill=c + (255,))
    for x in range(66, 128, 4):
        d.line((x, 0, x + 1, 63), fill=sh + (255,))
    d.rectangle((64, 0, 127, 3), fill=hi + (255,))
    return im

if __name__ == "__main__":
    for style, fn in STYLES.items():
        w(f"{RP}/models/entity/hair_{style}.geo.json", {"format_version": "1.12.0", "minecraft:geometry": [{
            "description": {"identifier": f"geometry.dbz.hair_{style}", "texture_width": 64, "texture_height": 32,
                            "visible_bounds_width": 4, "visible_bounds_height": 5, "visible_bounds_offset": [0, 1.5, 0]},
            "bones": [{"name": "head", "pivot": [0, 24, 0]},
                      {"name": "dbz_hair", "parent": "head", "pivot": [0, 24, 0], "cubes": fn()}]}]})
    template_att = json.load(open(f"{RP}/attachables/hair_gold.json"))
    template_item = json.load(open(f"{BP}/items/hair_gold.json"))
    for key, (style, col) in HAIRS.items():
        att_path = f"{RP}/attachables/hair_{key}.json"
        a = json.load(open(att_path)) if os.path.exists(att_path) else json.loads(json.dumps(template_att))
        desc = a["minecraft:attachable"]["description"]
        desc["identifier"] = f"dbz:hair_{key}"
        desc["textures"]["default"] = f"textures/entity/hair/{key}"
        desc["geometry"] = {"default": f"geometry.dbz.hair_{style}"}
        w(att_path, a)
        item_path = f"{BP}/items/hair_{key}.json"
        if not os.path.exists(item_path):
            it = json.loads(json.dumps(template_item))
            it["minecraft:item"]["description"]["identifier"] = f"dbz:hair_{key}"
            w(item_path, it)
        texture(col).save(f"{RP}/textures/entity/hair/{key}.png")
    print("hair v2:", ", ".join(f"{k}={v[0]}" for k, v in HAIRS.items()))
