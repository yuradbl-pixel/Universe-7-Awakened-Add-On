# Player tails (v1.34).
# A tail is a small entity with no body of its own that rides one of the player's
# two built-in shoulder seats (the same ones parrots use). It is drawn at the
# lower back, moves and turns with the player, and is visible to everyone.
# The script (tails.js) picks the tail style from the player's race and form.
import json, os, random
from PIL import Image, ImageDraw

BP = "/home/claude/dbz/DBZ_BP"
RP = "/home/claude/dbz/DBZ_RP"
ID = "dbz:player_tail"

def w(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w").write(json.dumps(o, indent=2) + "\n")

# style index -> (shape, base colour)   (index 0 = no tail; never used on the entity)
STYLES = {
    1: ("fur", (120, 72, 40)),      # Saiyan / Half-Saiyan
    2: ("fur", (170, 52, 40)),      # Super Saiyan 4: red fur
    3: ("scaled", (222, 214, 236)), # Frieza Race base
    4: ("scaled", (240, 240, 246)), # Final Form
    5: ("scaled", (242, 196, 58)),  # Golden
    6: ("scaled", (58, 42, 76)),    # Black
    7: ("tendril", (232, 138, 176)),  # Majin (base race): medium head tendril
    8: ("antennae", (92, 168, 74)),   # Namekian (base race): antennae
}
# v1.41: the Frieza Race base (style 3) also gets horns; when transformed the form look has its own.

# ---- Behavior entity -----------------------------------------------------------
w(f"{BP}/entities/player_tail.json", {
    "format_version": "1.21.60",
    "minecraft:entity": {
        "description": {
            "identifier": ID, "is_spawnable": False, "is_summonable": True,
            "properties": {
                "dbz:style": {"type": "int", "range": [1, len(STYLES)], "default": 1, "client_sync": True},
                # Where the tail root sits relative to this entity, in model pixels (body frame).
                "dbz:ox": {"type": "float", "range": [-64.0, 64.0], "default": -6.4, "client_sync": True},
                "dbz:oy": {"type": "float", "range": [-64.0, 64.0], "default": -11.0, "client_sync": True},
                "dbz:oz": {"type": "float", "range": [-64.0, 64.0], "default": 2.5, "client_sync": True},
                # Head pitch (degrees, + = looking down), used by the head tendril.
                "dbz:pitch": {"type": "float", "range": [-90.0, 90.0], "default": 0.0, "client_sync": True},
            },
        },
        "components": {
            # "parrot_tame" lets it ride the player's shoulder seats; "inanimate"
            # keeps it out of ki attacks and mob targeting.
            "minecraft:type_family": {"family": ["parrot_tame", "dbz_tail", "inanimate"]},
            "minecraft:collision_box": {"width": 0.01, "height": 0.01},
            "minecraft:custom_hit_test": {"hitboxes": [{"pivot": [0, -100, 0], "width": 0, "height": 0}]},
            "minecraft:health": {"value": 1, "max": 1},
            "minecraft:damage_sensor": {"triggers": {"cause": "all", "deals_damage": "no"}},
            "minecraft:fire_immune": {},
            "minecraft:breathable": {"total_supply": 15, "suffocate_time": 0, "breathes_water": True, "breathes_air": True,
                                     "generates_bubbles": False},
            "minecraft:physics": {"has_gravity": False, "has_collision": False},
            "minecraft:pushable": {"is_pushable": False, "is_pushable_by_piston": False},
            "minecraft:knockback_resistance": {"value": 1.0},
            "minecraft:movement": {"value": 0},
            # The tail's body always faces where the script turns it (the player's body direction).
            "minecraft:body_rotation_always_follows_head": {},
            "minecraft:conditional_bandwidth_optimization": {},
        },
    },
})

# ---- Geometry: one model per shape, root bone at the entity origin ---------------
def chain(seg, rots, inflate, taper):
    bones = [{"name": "root", "pivot": [0, 0, 0]}]
    parent = "root"
    for i, rot in enumerate(rots):
        z0 = i * seg[2]
        name = "tail" if i == 0 else f"tail{i+1}"
        bones.append({"name": name, "parent": parent, "pivot": [0, 0, z0], "rotation": rot,
                      "cubes": [{"origin": [-seg[0] / 2, -seg[1] / 2, z0], "size": list(seg),
                                 "inflate": round(max(0.0, inflate - taper * i), 2), "uv": [0, 0]}]})
        parent = name
    return bones

def tendril_chain():
    # Root at the neck (the head's pivot); the tendril starts on top of the head (8 px up)
    # and curls back. Medium size: 3x4x3, 3x4x3, 2x3x2.
    bones = [{"name": "head_root", "pivot": [0, 0, 0]}]
    parent, y = "head_root", 8
    for i, ((w_, h, d), rot) in enumerate(zip([(3, 4, 3), (3, 4, 3), (2, 3, 2)], [[-15, 0, 0], [-40, 0, 0], [-55, 0, 0]])):
        name = "tendril" if i == 0 else f"tendril{i+1}"
        bones.append({"name": name, "parent": parent, "pivot": [0, y, 0], "rotation": rot,
                      "cubes": [{"origin": [-w_ / 2, y, -d / 2], "size": [w_, h, d], "uv": [0, 0], "inflate": 0.1}]})
        parent, y = name, y + h
    return bones

def head_chain(name, parts):
    """parts: [(size, origin, pivot, rotation)] chained from the neck pivot (head top = y 8)."""
    bones, parent = [], "head_root"
    for i, (size, origin, pivot, rot) in enumerate(parts):
        n = name if i == 0 else f"{name}{i+1}"
        bones.append({"name": n, "parent": parent, "pivot": pivot, "rotation": rot,
                      "cubes": [{"origin": origin, "size": size, "uv": [0, 0], "inflate": 0.1}]})
        parent = n
    return bones

# Same shapes as the form looks (head-space y 24 there = 0 here). +rz tips a part's top
# toward +x, negative rx tips it back.
HORNS = (head_chain("horn_r", [([2, 3, 2], [-5.5, 5, -1], [-4.5, 5, 0], [-20, 0, -40]),
                               ([2, 4, 2], [-5.5, 8, -1], [-4.5, 8, 0], [-25, 0, 30]),
                               ([1, 3, 1], [-5, 12, -0.5], [-4.5, 12, 0], [-25, 0, 20])])
         + head_chain("horn_l", [([2, 3, 2], [3.5, 5, -1], [4.5, 5, 0], [-20, 0, 40]),
                                 ([2, 4, 2], [3.5, 8, -1], [4.5, 8, 0], [-25, 0, -30]),
                                 ([1, 3, 1], [4, 12, -0.5], [4.5, 12, 0], [-25, 0, -20])]))
ANTENNAE = (head_chain("antenna_r", [([1, 5, 1], [-2.5, 7.8, -4.2], [-2, 7.8, -3.7], [-20, 0, -12]),
                                     ([1, 5, 1], [-2.5, 12.8, -4.2], [-2, 12.8, -3.7], [-45, 0, 0])])
            + head_chain("antenna_l", [([1, 5, 1], [1.5, 7.8, -4.2], [2, 7.8, -3.7], [-20, 0, 12]),
                                       ([1, 5, 1], [1.5, 12.8, -4.2], [2, 12.8, -3.7], [-45, 0, 0])]))
HEAD_ROOT = [{"name": "head_root", "pivot": [0, 0, 0]}]

# ---- v1.43: fixed offsets baked into the models -----------------------------------------
# The rider sits on the player's left shoulder seat. In model pixels (body frame, -x = right,
# +z = back): the butt is 6.4 px to the right, 11 px down and 2.5 px back; the neck (head
# pivot) is 6.4 px right and 1.5 px up.
TAIL_OFFSET = (-6.4, -11.0, 0.5)  # v1.45: base starts 2 px inside the body so the join is hidden
HEAD_OFFSET = (-6.4, 1.5, 0.0)

def shift(bones, off):
    out = []
    for b in bones:
        b = json.loads(json.dumps(b))
        b["pivot"] = [round(b["pivot"][i] + off[i], 3) for i in range(3)]
        for c in b.get("cubes", []):
            c["origin"] = [round(c["origin"][i] + off[i], 3) for i in range(3)]
        out.append(b)
    return out

def place(bones):
    """Shift tail bones (under 'root') to the butt and head bones (under 'head_root') to the neck."""
    head_names, out = set(), []
    for b in bones:
        if b["name"] == "head_root" or b.get("parent") in head_names:
            head_names.add(b["name"])
    for b in bones:
        out += shift([b], HEAD_OFFSET if b["name"] in head_names else TAIL_OFFSET)
    return out

def tapered(segs, rots):
    """Tail chain with a size per segment: [(w, h, length)], centred on the chain axis."""
    bones = [{"name": "root", "pivot": [0, 0, 0]}]
    parent, z = "root", 0.0
    for i, ((w_, h, l), rot) in enumerate(zip(segs, rots)):
        name = "tail" if i == 0 else f"tail{i+1}"
        bones.append({"name": name, "parent": parent, "pivot": [0, 0, round(z, 3)], "rotation": rot,
                      "cubes": [{"origin": [-w_ / 2, -h / 2, round(z, 3)], "size": [w_, h, l], "uv": [0, 0]}]})
        parent, z = name, z + l
    return bones

GEOS = {
    # Furry tail: rises from the lower back and curls to one side.
    "fur": chain((2, 2, 4), [[35, 0, 0], [22, 20, 0], [18, 28, 0], [14, 30, 0], [10, 28, 0], [8, 24, 0]], 0.35, 0.03),
    # Thick scaled tail: drops toward the ground and sweeps back.
    # v1.44: slimmer (2x2 sections instead of 3x3) but the same length.
    # v1.44: slimmer, tapering to a point, slightly longer overall (~32 px).
    "scaled": tapered([(2.6, 2.6, 6), (2.2, 2.2, 6), (1.8, 1.8, 6), (1.4, 1.4, 5), (1.0, 1.0, 5), (0.5, 0.5, 4)],
                      [[-50, 0, 0], [18, 0, 0], [14, 8, 0], [10, 10, 0], [8, 10, 0], [6, 8, 0]]),
    "tendril": tendril_chain(),
    "antennae": HEAD_ROOT + ANTENNAE,
}
GEOS["scaled_horns"] = GEOS["scaled"] + HEAD_ROOT + HORNS
GEOS = {k: place(v) for k, v in GEOS.items()}
for shape, bones in GEOS.items():
    w(f"{RP}/models/entity/player_tail_{shape}.geo.json", {"format_version": "1.12.0", "minecraft:geometry": [{
        "description": {"identifier": f"geometry.dbz.player_tail_{shape}", "texture_width": 32, "texture_height": 32,
                        "visible_bounds_width": 4, "visible_bounds_height": 4, "visible_bounds_offset": [0, 0, 0]},
        "bones": bones}]})

# ---- Textures (32x32, HD-ish fur/scales) ----------------------------------------
os.makedirs(f"{RP}/textures/entity/player_tail", exist_ok=True)
for idx, (shape, col) in STYLES.items():
    rnd = random.Random(idx)
    im = Image.new("RGBA", (32, 32), col + (255,))
    d = ImageDraw.Draw(im)
    dk = tuple(int(v * 0.72) for v in col)
    lt = tuple(min(255, int(v * 1.12) + 12) for v in col)
    if shape in ("tendril", "antennae"):  # smooth skin with soft shading
        for y in range(32):
            k = 1.08 - 0.2 * y / 31
            d.line((0, y, 31, y), fill=tuple(min(255, int(v * k)) for v in col) + (255,))
    elif shape == "fur":
        for _ in range(120):  # fur strands
            x, y = rnd.randrange(32), rnd.randrange(32)
            d.line((x, y, x + rnd.choice((-1, 0, 1)), y + 2), fill=(dk if rnd.random() < 0.55 else lt) + (255,))
    else:
        for y in range(0, 32, 3):  # scale bands with a light belly stripe
            d.line((0, y, 31, y), fill=dk + (255,))
            for x in range((y // 3) % 2 * 2, 32, 4):
                d.point((x, y + 1), fill=lt + (255,))
    im.save(f"{RP}/textures/entity/player_tail/style_{idx}.png")

# ---- Client entity, render controller, animations -------------------------------
tex = {f"style_{i}": f"textures/entity/player_tail/style_{i}" for i in STYLES}
w(f"{RP}/entity/player_tail.entity.json", {"format_version": "1.10.0", "minecraft:client_entity": {
    "description": {
        "identifier": ID,
        "materials": {"default": "entity_alphatest"},
        "textures": tex,
        "geometry": {k: f"geometry.dbz.player_tail_{k}" for k in ("fur", "scaled", "scaled_horns", "tendril", "antennae")},
        "animations": {"place": "animation.dbz.player_tail.place", "sway": "animation.dbz.player_tail.sway"},
        "scripts": {"animate": ["place", "sway"]},
        "render_controllers": ["controller.render.dbz.player_tail"],
    }}})

n = len(STYLES)
w(f"{RP}/render_controllers/player_tail.render_controllers.json", {"format_version": "1.8.0", "render_controllers": {
    "controller.render.dbz.player_tail": {
        "arrays": {
            "textures": {"Array.styles": [f"Texture.style_{i}" for i in STYLES]},
            "geometries": {"Array.shapes": ["Geometry.fur", "Geometry.scaled", "Geometry.scaled_horns", "Geometry.tendril", "Geometry.antennae"]},
        },
        "geometry": ("Array.shapes[q.property('dbz:style') == 3 ? 2 : (q.property('dbz:style') >= 8 ? 4 : "
                     "(q.property('dbz:style') >= 7 ? 3 : (q.property('dbz:style') >= 4 ? 1 : 0)))]"),
        "materials": [{"*": "Material.default"}],
        "textures": [f"Array.styles[math.clamp(q.property('dbz:style') - 1, 0, {n - 1})]"],
    }}})

w(f"{RP}/animations/player_tail.animation.json", {"format_version": "1.8.0", "animations": {
    "animation.dbz.player_tail.place": {"loop": True, "bones": {
        # Placement is baked into the models (v1.43); only the head pitch is animated.
        "head_root": {"rotation": ["q.property('dbz:pitch')", 0, 0]}}},
    "animation.dbz.player_tail.sway": {"loop": True, "bones": {
        "tail2": {"rotation": [0, "math.sin(q.life_time * 90) * 10", 0]},
        "tail3": {"rotation": [0, "math.sin(q.life_time * 90 - 40) * 9", 0]},
        "tail4": {"rotation": ["math.sin(q.life_time * 60) * 4", "math.sin(q.life_time * 90 - 80) * 8", 0]},
        "tail5": {"rotation": [0, "math.sin(q.life_time * 90 - 120) * 7", 0]}}}}})

# Name (shown nowhere, but keeps the lang file complete)
lang = f"{RP}/texts/en_US.lang"
s = open(lang).read()
if "entity.dbz:player_tail.name" not in s:
    open(lang, "a").write("\nentity.dbz:player_tail.name=Tail\n")
print("player tail: entity, 2 models,", len(STYLES), "textures")
