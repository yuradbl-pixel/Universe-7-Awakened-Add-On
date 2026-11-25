"""v1.53: transformation "tint" looks. Instead of replacing the player's skin, each look is a
see-through colour layer laid over the player's own skin (alpha-blended), so the player keeps
their face and outfit but their colour changes and their outline glows. Saiyan-type forms add the
3D hair; Frieza-race forms add horns and coloured plates; god forms keep their halo.
Majin, Namekian and Android keep their full skins (unchanged)."""
import json, os, sys, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import gen_player_forms as G

RP = "/home/claude/dbz/DBZ_RP"; BP = "/home/claude/dbz/DBZ_BP"
OUT = f"{RP}/textures/entity/forms/tint"
os.makedirs(OUT, exist_ok=True)
SIDES = ("top", "bottom", "right", "front", "left", "back")
BODY = ("body", "rightArm", "leftArm", "rightLeg", "leftLeg")

def faces(part):
    uv, size = G.PARTS[part][0], G.PARTS[part][1]
    return {s: G.Skin.face(uv, size, s) for s in SIDES}

def put(im, x, y, c, a):
    im.putpixel((x, y), tuple(c) + (a,))

def tint_layer(col, alpha, rim=None, rim_alpha=0, head_alpha=None, glow_top=True):
    """col over every face; a brighter rim (2 px) around each side face = glowing outline."""
    im = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
    for part in G.PARTS:
        a_part = head_alpha if (part == "head" and head_alpha is not None) else alpha
        for side, (x, y, w, h) in faces(part).items():
            for yy in range(h):
                for xx in range(w):
                    e = min(xx, yy, w - 1 - xx, h - 1 - yy)
                    if rim and side not in ("top", "bottom") and e < 2 and not (part == "head" and side == "front" and 0 < yy < h - 1 and 0 < xx < w - 1):
                        put(im, x + xx, y + yy, rim, rim_alpha if e == 0 else (rim_alpha + a_part) // 2)
                    else:
                        put(im, x + xx, y + yy, col, a_part)
    return im

def region(im, part, side, rows, cols, col, a, fur=False, seed=0):
    """Paint a patch on one face: rows/cols as (from, to) fractions of the face."""
    x, y, w, h = faces(part)[side]
    rnd = random.Random(seed)
    for yy in range(int(h * rows[0]), int(math.ceil(h * rows[1]))):
        for xx in range(int(w * cols[0]), int(math.ceil(w * cols[1]))):
            c = col
            if fur:
                k = (xx * 3 + yy + rnd.randint(0, 2)) % 6
                c = tuple(int(v * (0.72 if k == 0 else 1.15 if k == 3 else 1.0)) for v in col)
                c = tuple(min(255, v) for v in c)
            put(im, x + xx, y + yy, c, a)

def copy_extras(im, src_name, names):
    """Copy the horn / halo / antenna parts from an existing full-skin design."""
    src = Image.open(f"{RP}/textures/entity/forms/{src_name}.png").convert("RGBA")
    for n in names:
        uv, size = G.EXTRA_UV[n], G.EXTRA_SIZE[n]
        for s in SIDES:
            x, y, w, h = G.Skin.face(uv, size, s)
            for yy in range(h):
                for xx in range(w):
                    p = src.getpixel((x + xx, y + yy))
                    if p[3]:
                        im.putpixel((x + xx, y + yy), p[:3] + (255,))

HORNS = G.HORNS_R + G.HORNS_L
HALO = [e[0] for e in G.EXTRAS if e[0].startswith("halo")]

def arcosian_plates(im, plate, gem):
    """Frieza-race plates on top of the tint: head dome, shoulders, forearms, shins, chest gem."""
    for s in ("top",): region(im, "head", s, (0, 1), (0, 1), plate, 235)
    for s in ("front", "left", "right", "back"): region(im, "head", s, (0, 0.25), (0, 1), plate, 235)
    for arm in ("rightArm", "leftArm"):
        region(im, arm, "top", (0, 1), (0, 1), plate, 235)
        for s in ("front", "left", "right", "back"):
            region(im, arm, s, (0, 0.25), (0, 1), plate, 235)            # shoulder pads
            region(im, arm, s, (0.62, 0.86), (0, 1), plate, 235)         # forearm plates
    for leg in ("rightLeg", "leftLeg"):
        for s in ("front", "left", "right", "back"):
            region(im, leg, s, (0.45, 0.75), (0, 1), plate, 235)         # shin plates
    region(im, "body", "front", (0.0, 0.34), (0.2, 0.8), plate, 235)     # chest plate
    x, y, w, h = faces("body")["front"]
    cx, cy = x + w // 2, y + int(h * 0.17)
    for yy in range(-3, 4):
        for xx in range(-4, 4):
            if (xx + 0.5) ** 2 / 16 + yy ** 2 / 9 <= 1:
                c = gem if (xx < 0 and yy < 0) else tuple(int(v * 0.8) for v in gem)
                put(im, cx + xx, cy + yy, c, 255)
    put(im, cx - 2, cy - 2, (255, 255, 255), 255)

# id: (builder, hair key or None)
LOOKS = {}
def look(tid, hair=None):
    def deco(fn):
        LOOKS[tid] = (fn, hair); return fn
    return deco

GOLD = (255, 214, 80)
@look("ssj", "gold")
def _(): return tint_layer(GOLD, 38, (255, 236, 140), 150, head_alpha=30)
@look("ssj2", "gold_sharp")
def _():
    im = tint_layer(GOLD, 48, (255, 246, 170), 175, head_alpha=36)
    rnd = random.Random(2)
    for part in BODY:                                                     # tiny electric sparks on the glow
        for s in ("front", "back", "left", "right"):
            x, y, w, h = faces(part)[s]
            for _ in range(2):
                sx, sy = x + rnd.randrange(w), y + rnd.randrange(2, h - 2)
                for i, (dx, dy) in enumerate(((0, 0), (1, 1), (0, 2))):
                    if x <= sx + dx < x + w: put(im, sx + dx, sy + dy, (240, 250, 255), 220)
    return im
@look("ssj3", "gold_long")
def _(): return tint_layer(GOLD, 55, (255, 246, 170), 185, head_alpha=40)
@look("lssj", "green")
def _(): return tint_layer((170, 240, 90), 60, (200, 255, 140), 185, head_alpha=40)
@look("ssj4", "black_long")
def _():
    im = tint_layer((255, 120, 90), 22, (255, 120, 100), 120, head_alpha=10)
    FUR = (186, 40, 52)
    for arm in ("rightArm", "leftArm"):
        for s in ("front", "back", "left", "right", "top"):
            region(im, arm, s, (0, 0.66) if s != "top" else (0, 1), (0, 1), FUR, 215, fur=True, seed=1)
    for s in ("back", "left", "right"):
        region(im, "body", s, (0, 1), (0, 1), FUR, 215, fur=True, seed=2)
    for c0, c1 in ((0, 0.2), (0.8, 1)):
        region(im, "body", "front", (0, 1), (c0, c1), FUR, 215, fur=True, seed=3)
    region(im, "body", "top", (0, 1), (0, 1), FUR, 215, fur=True, seed=4)
    for leg in ("rightLeg", "leftLeg"):
        for s in ("front", "back", "left", "right"):
            region(im, leg, s, (0, 0.35), (0, 1), FUR, 200, fur=True, seed=5)
    x, y, w, h = faces("head")["front"]                                   # red eye-liner glow around the eyes
    for xx in list(range(2, 7)) + list(range(9, 14)):
        put(im, x + xx, y + 7, (200, 40, 50), 120)
    return im
@look("ssj_god", "red")
def _(): return tint_layer((255, 110, 110), 34, (255, 150, 140), 150, head_alpha=26)
@look("ssj_blue", "blue")
def _(): return tint_layer((90, 200, 255), 40, (170, 235, 255), 165, head_alpha=30)
@look("blue_kaioken", "blue")
def _(): return tint_layer((255, 70, 60), 95, (150, 230, 255), 200, head_alpha=80)
@look("divine_bloom", "pink")
def _(): return tint_layer((255, 140, 200), 40, (255, 200, 230), 165, head_alpha=30)
@look("ui_sign", "black")
def _(): return tint_layer((190, 210, 255), 28, (220, 232, 255), 150, head_alpha=20)
@look("ui_mastered", "silver")
def _(): return tint_layer((220, 228, 255), 42, (255, 255, 255), 190, head_alpha=30)
@look("ultra_ego", "purple")
def _(): return tint_layer((150, 70, 220), 70, (230, 110, 255), 190, head_alpha=55)
@look("potential_unleashed")
def _(): return tint_layer((240, 244, 255), 26, (255, 255, 255), 160, head_alpha=18)
@look("beast", "silver")
def _(): return tint_layer((190, 150, 255), 42, (230, 200, 255), 185, head_alpha=30)
@look("kaioken")
def _(): return tint_layer((255, 50, 40), 100, (255, 140, 120), 190, head_alpha=85)
@look("human_unlock")
def _(): return tint_layer((210, 230, 255), 32, (240, 248, 255), 160, head_alpha=22)
@look("max_power")
def _(): return tint_layer((255, 160, 80), 55, (255, 210, 150), 175, head_alpha=40)
PURPLE = (150, 60, 200)
@look("arcosian_base")
def _():
    im = tint_layer((242, 238, 236), 190, (200, 190, 210), 220)
    arcosian_plates(im, PURPLE, (170, 70, 230)); copy_extras(im, "arcosian_base", HORNS); return im
@look("final_form")
def _():
    im = tint_layer((246, 244, 248), 205, (220, 200, 240), 225)
    arcosian_plates(im, (160, 70, 220), (190, 90, 255)); copy_extras(im, "arcosian_final", HORNS); return im
@look("golden")
def _():
    im = tint_layer((250, 196, 50), 200, (255, 236, 140), 230)
    arcosian_plates(im, (130, 50, 190), (190, 90, 255)); copy_extras(im, "arcosian_golden", HORNS); return im
@look("black")
def _():
    im = tint_layer((40, 36, 52), 205, (150, 90, 220), 225)
    arcosian_plates(im, (210, 160, 50), (230, 60, 80)); copy_extras(im, "arcosian_black", HORNS); return im
@look("divine_aura")
def _():
    im = tint_layer((170, 210, 255), 40, (220, 236, 255), 175, head_alpha=28)
    copy_extras(im, "divine_aura", HALO); return im
@look("god_destruction")
def _():
    im = tint_layer((150, 60, 230), 65, (210, 140, 255), 190, head_alpha=50)
    copy_extras(im, "god_destruction", HALO); return im

def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=2)

w(f"{RP}/render_controllers/dbz_tint.render_controllers.json", {"format_version": "1.8.0", "render_controllers": {
    "controller.render.dbz_tint": {"geometry": "Geometry.default", "materials": [{"*": "Material.default"}], "textures": ["Texture.default"]},
    "controller.render.dbz_tint_hair": {"geometry": "Geometry.hair", "materials": [{"*": "Material.hair"}], "textures": ["Texture.hair"]}}})

for tid, (fn, hair) in LOOKS.items():
    fn().save(f"{OUT}/{tid}.png")
    desc = {"identifier": f"dbz:tint_{tid}",
            "materials": {"default": "entity_alphablend", "hair": "armor", "enchanted": "armor_enchanted"},
            "textures": {"default": f"textures/entity/forms/tint/{tid}", "enchanted": "textures/misc/enchanted_item_glint"},
            "geometry": {"default": "geometry.dbz.form_overlay"},
            "scripts": {"parent_setup": "variable.helmet_layer_visible = 0.0;"},
            "render_controllers": ["controller.render.dbz_tint"]}
    if hair:
        h = json.load(open(f"{RP}/attachables/hair_{hair}.json"))["minecraft:attachable"]["description"]
        desc["textures"]["hair"] = h["textures"]["default"]; desc["geometry"]["hair"] = h["geometry"]["default"]
        desc["render_controllers"].append("controller.render.dbz_tint_hair")
    w(f"{RP}/attachables/tint_{tid}.json", {"format_version": "1.10.0", "minecraft:attachable": {"description": desc}})
    w(f"{BP}/items/tint_{tid}.json", {"format_version": "1.21.50", "minecraft:item": {
        "description": {"identifier": f"dbz:tint_{tid}", "menu_category": {"category": "none"}},
        "components": {"minecraft:icon": "dbz_hair", "minecraft:display_name": {"value": "Transformation"},
                       "minecraft:max_stack_size": 1, "minecraft:wearable": {"slot": "slot.armor.head", "protection": 0}}}})
print("tint looks:", len(LOOKS))
