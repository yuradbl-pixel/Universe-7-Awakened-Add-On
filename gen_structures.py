# gen_structures.py
# Builds world-generation structures (.mcstructure), their hidden "core" marker
# blocks, features and feature rules.
#
#   Boss lairs : one per boss, themed (arena, ship, temple, citadel, dome).
#                A hidden dbz:core_<boss> block in the foundation registers the
#                lair with the script when a player comes near.
#   NPC homes  : cottage, dome house, training hut. A hidden dbz:home_core in
#                the foundation brings a resident when a player comes near.
#                The script also places these homes inside villages.
#
# Layout convention for every structure: y=0 foundation (replaces the top
# ground block), y=1 floor, everything above is cleared to air.
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mcstructure

BP = "/home/claude/dbz/DBZ_BP"
RP = "/home/claude/dbz/DBZ_RP"
for d in ["structures/dbz", "features", "feature_rules", "blocks", "loot_tables"]:
    os.makedirs(f"{BP}/{d}", exist_ok=True)

def w(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")

M = lambda n: n if n.startswith("minecraft:") or ":" in n else f"minecraft:{n}"


class Grid:
    def __init__(self, sx, sy, sz):
        self.size = (sx, sy, sz)
        self.g = {}

    def set(self, x, y, z, b):
        if 0 <= x < self.size[0] and 0 <= y < self.size[1] and 0 <= z < self.size[2]:
            self.g[(x, y, z)] = b if isinstance(b, tuple) else M(b)

    def fill(self, x0, y0, z0, x1, y1, z1, b):
        for x in range(min(x0, x1), max(x0, x1) + 1):
            for y in range(min(y0, y1), max(y0, y1) + 1):
                for z in range(min(z0, z1), max(z0, z1) + 1):
                    self.set(x, y, z, b)

    def hemisphere(self, cx, cy, cz, r, b, hollow=True, keep=None):
        for x in range(-r, r + 1):
            for y in range(0, r + 1):
                for z in range(-r, r + 1):
                    d = math.sqrt(x * x + y * y + z * z)
                    if d > r + 0.4 or (hollow and d < r - 0.6):
                        continue
                    if keep and not keep(x, y, z):
                        continue
                    self.set(cx + x, cy + y, cz + z, b)


# =============================================================================
# Shared helpers
# =============================================================================
F = 5  # floor level: y0..y4 is a deep foundation that levels the site, y5 is the floor

def stairs(name, facing):
    """facing = side the stair rises toward: 'east','west','south','north'."""
    d = {"east": 0, "west": 1, "south": 2, "north": 3}[facing]
    return (M(name), {"weirdo_direction": d, "upside_down_bit": False})

BED_COLORS = {"white": 0, "orange": 1, "magenta": 2, "light_blue": 3, "yellow": 4, "lime": 5, "pink": 6,
              "gray": 7, "light_gray": 8, "cyan": 9, "purple": 10, "blue": 11, "brown": 12, "green": 13,
              "red": 14, "black": 15}

def bed(G, x, y, z, color="red"):
    """A real bed: foot at (x, y, z), head at (x, y, z + 1), pointing south."""
    from mcstructure import Tag, BYTE, STRING
    be = {"id": Tag(STRING, "Bed"), "color": Tag(BYTE, BED_COLORS[color]), "isMovable": Tag(BYTE, 1)}
    G.set(x, y, z, ("minecraft:bed", {"direction": 0, "head_piece_bit": False, "occupied_bit": False}, be))
    G.set(x, y, z + 1, ("minecraft:bed", {"direction": 0, "head_piece_bit": True, "occupied_bit": False}, be))

def door(G, x, y, z, name="wooden_door", direction=1, hinge=False):
    """A two-block door (lower at y, upper at y + 1). direction 1/3 = in a wall running along x."""
    st = {"direction": direction, "door_hinge_bit": hinge, "open_bit": False}
    G.set(x, y, z, (M(name), {**st, "upper_block_bit": False}))
    G.set(x, y + 1, z, (M(name), {**st, "upper_block_bit": True}))

def ring(G, cx, cz, r_in, r_out, y, b):
    for x in range(G.size[0]):
        for z in range(G.size[2]):
            d = math.hypot(x - cx, z - cz)
            if r_in <= d <= r_out:
                G.set(x, y, z, b)

def disc(G, cx, cz, r, y, b):
    ring(G, cx, cz, -1, r, y, b)

def foundation(G, b):
    G.fill(0, 0, 0, G.size[0] - 1, F - 1, G.size[2] - 1, b)


# =============================================================================
# Boss lairs (25 x 20 x 25, centre at x=z=12)
# =============================================================================
LAIR_THEMES = {
    "frieza": ("ship", dict(hull="white_concrete", trim="purple_concrete", glass="light_blue_stained_glass", light="sea_lantern", leg="iron_block")),
    "cell": ("arena", dict(base="stone", plaza="stone_bricks", floor="smooth_stone", floor2="light_gray_concrete", pillar="green_concrete", light="sea_lantern", stair="stone_brick_stairs", seat="stone_bricks")),
    "majin_buu": ("dome", dict(base="pink_concrete", wall="pink_concrete", floor="white_concrete", glass="pink_stained_glass", light="glowstone", pillar="white_concrete", accent="magenta_concrete")),
    "broly": ("arena", dict(base="packed_ice", plaza="packed_ice", floor="blue_ice", floor2="snow", pillar="packed_ice", light="sea_lantern", stair="stone_brick_stairs", seat="snow")),
    "beerus": ("temple", dict(base="stone_bricks", floor="purpur_block", trim="gold_block", pillar="purpur_pillar", ruin="purpur_block", light="glowstone", stair="purpur_stairs")),
    "jiren": ("arena", dict(base="stone", plaza="red_sandstone", floor="red_concrete", floor2="black_concrete", pillar="red_nether_brick", light="glowstone", stair="red_sandstone_stairs", seat="red_sandstone")),
    "hit": ("citadel", dict(base="deepslate_bricks", wall="deepslate_bricks", floor="purple_concrete", light="sea_lantern", fire="soul_campfire")),
    "goku_black": ("citadel", dict(base="deepslate_bricks", wall="gray_concrete", floor="pink_concrete", light="glowstone", fire="soul_campfire")),
    "zamasu": ("temple", dict(base="quartz_block", floor="quartz_block", trim="lime_concrete", pillar="quartz_pillar", ruin="chiseled_quartz_block", light="sea_lantern", stair="quartz_stairs")),
    "toppo": ("arena", dict(base="stone", plaza="stone_bricks", floor="red_concrete", floor2="white_concrete", pillar="black_concrete", light="sea_lantern", stair="stone_brick_stairs", seat="stone_bricks")),
    "dyspo": ("arena", dict(base="stone", plaza="stone_bricks", floor="black_concrete", floor2="red_concrete", pillar="white_concrete", light="sea_lantern", stair="stone_brick_stairs", seat="stone_bricks")),
    "kefla": ("arena", dict(base="stone", plaza="mossy_stone_bricks", floor="lime_concrete", floor2="smooth_stone", pillar="gold_block", light="glowstone", stair="mossy_stone_brick_stairs", seat="mossy_stone_bricks")),
    "moro": ("citadel", dict(base="cobbled_deepslate", wall="mossy_cobblestone", floor="gray_concrete", light="glowstone", fire="campfire")),
    "granolah": ("temple", dict(base="red_sandstone", floor="smooth_red_sandstone", trim="green_concrete", pillar="cut_red_sandstone", ruin="red_sandstone", light="glowstone", stair="red_sandstone_stairs")),
    "gas": ("citadel", dict(base="blackstone", wall="polished_blackstone_bricks", floor="green_concrete", light="shroomlight", fire="soul_campfire")),
    "cumber": ("citadel", dict(base="blackstone", wall="red_nether_brick", floor="black_concrete", light="shroomlight", fire="soul_campfire")),
    "fu": ("dome", dict(base="purple_concrete", wall="purple_concrete", floor="white_concrete", glass="purple_stained_glass", light="sea_lantern", pillar="white_concrete", accent="magenta_concrete")),
    "hearts": ("citadel", dict(base="blackstone", wall="black_concrete", floor="magenta_concrete", light="sea_lantern", fire="soul_campfire")),
    "oren": ("arena", dict(base="stone", plaza="stone_bricks", floor="brown_concrete", floor2="smooth_stone", pillar="stone_bricks", light="glowstone", stair="stone_brick_stairs", seat="stone_bricks")),
    "kamin": ("arena", dict(base="stone", plaza="stone_bricks", floor="magenta_concrete", floor2="white_concrete", pillar="quartz_pillar", light="sea_lantern", stair="stone_brick_stairs", seat="stone_bricks")),
}
L, C = 25, 12  # lair footprint and centre


def lair_arena(G, p):
    """Tournament arena: raised two-step stage, stands on four sides, corner braziers."""
    foundation(G, p["base"])
    G.fill(0, F, 0, L - 1, F, L - 1, p["plaza"])
    G.fill(C - 9, F + 1, C - 9, C + 9, F + 1, C + 9, p["plaza"])          # step
    for x in range(C - 8, C + 9):                                           # stage tiles
        for z in range(C - 8, C + 9):
            G.set(x, F + 2, z, p["floor"] if (x + z) % 2 == 0 else p["floor2"])
    for (x, z) in ((C - 8, C - 8), (C + 8, C - 8), (C - 8, C + 8), (C + 8, C + 8)):
        G.set(x, F + 2, z, p["light"])
    # Stands: three rising rows on each side, gap in the middle of the south side.
    for row in range(3):
        y = F + 1 + row
        lo, hi = 2 - row, L - 3 + row
        for i in range(2, L - 2):
            G.fill(i, F + 1, lo, i, y - 1, lo, p["seat"]) if y > F + 1 else None
            G.set(i, y, lo, stairs(p["stair"], "north"))
            if not (C - 2 <= i <= C + 2):
                G.fill(i, F + 1, hi, i, y - 1, hi, p["seat"]) if y > F + 1 else None
                G.set(i, y, hi, stairs(p["stair"], "south"))
            G.fill(lo, F + 1, i, lo, y - 1, i, p["seat"]) if y > F + 1 else None
            G.set(lo, y, i, stairs(p["stair"], "west"))
            G.fill(hi, F + 1, i, hi, y - 1, i, p["seat"]) if y > F + 1 else None
            G.set(hi, y, i, stairs(p["stair"], "east"))
    G.fill(C - 2, F + 1, L - 3, C + 2, F + 6, L - 1, "air")                 # entrance gap
    # Corner pillars with fire on top.
    for (x, z) in ((1, 1), (L - 2, 1), (1, L - 2), (L - 2, L - 2)):
        G.fill(x, F + 1, z, x, F + 8, z, p["pillar"])
        G.set(x, F + 9, z, "campfire")


def lair_ship(G, p):
    """Spaceship on landing legs: lit underside, ramp, glass dome bridge."""
    foundation(G, "stone")
    G.fill(0, F, 0, L - 1, F, L - 1, "smooth_stone")
    for (x, z) in ((C - 8, C - 8), (C + 8, C - 8), (C - 8, C + 8), (C + 8, C + 8)):  # legs
        G.fill(x, F + 1, z, x, F + 2, z, p["leg"])
        G.fill(x - 1, F + 1, z, x + 1, F + 1, z, p["leg"])
        G.fill(x, F + 1, z - 1, x, F + 1, z + 1, p["leg"])
    disc(G, C, C, 3, F + 1, p["hull"]); disc(G, C, C, 3, F + 2, p["hull"])           # central column
    disc(G, C, C, 11.4, F + 3, p["hull"])                                               # lower hull
    ring(G, C, C, 10.2, 11.4, F + 3, p["trim"])
    ring(G, C, C, 6, 6.9, F + 3, p["light"])                                            # underside lights
    disc(G, C, C, 9.4, F + 4, p["hull"])                                                # deck
    ring(G, C, C, 8.4, 9.4, F + 5, p["trim"])                                           # rail
    G.hemisphere(C, F + 5, C, 7, p["glass"], keep=lambda x, y, z: y > 0)
    G.fill(C - 1, F + 5, C - 9, C + 1, F + 7, C - 6, "air")                            # dome door
    for i, (y, z) in enumerate(((F + 1, 2), (F + 2, 3), (F + 3, 4), (F + 4, 5))):    # ramp
        G.fill(C - 1, y, z, C + 1, y, z, stairs("quartz_stairs", "south"))
        G.fill(C - 1, F + 1, z, C + 1, y - 1, z, p["hull"]) if y > F + 1 else None
    G.fill(C - 1, F + 4, 6, C + 1, F + 4, C - 9, p["hull"])                            # walkway to the deck
    for (x, z) in ((C - 3, C), (C + 3, C), (C, C + 3)):                                # consoles
        G.set(x, F + 5, z, p["light"])
    G.set(C, F + 4, C, p["light"])


def lair_temple(G, p, rnd):
    """Overgrown temple: stepped platform, ring of (broken) columns, raised altar."""
    foundation(G, p["base"])
    G.fill(0, F, 0, L - 1, F, L - 1, p["base"])
    G.fill(1, F + 1, 1, L - 2, F + 1, L - 2, p["trim"])
    G.fill(2, F + 1, 2, L - 3, F + 1, L - 3, p["floor"])
    for i in range(12):                                          # column ring
        a = i / 12 * math.pi * 2
        px, pz = C + round(math.cos(a) * 9), C + round(math.sin(a) * 9)
        h = 3 + rnd.randint(0, 5)
        G.fill(px, F + 2, pz, px, F + 1 + h, pz, p["pillar"])
        if h < 7:
            G.set(px, F + 2 + h, pz, p["ruin"])
        else:
            G.set(px, F + 2 + h, pz, p["light"])
    for _ in range(3):                                           # fallen column pieces
        x, z = rnd.randint(3, L - 4), rnd.randint(3, L - 4)
        if abs(x - C) > 5 or abs(z - C) > 5:
            G.fill(x, F + 2, z, min(L - 3, x + 3), F + 2, z, p["ruin"])
    G.fill(C - 4, F + 2, C - 4, C + 4, F + 2, C + 4, p["trim"])  # altar tiers
    G.fill(C - 3, F + 3, C - 3, C + 3, F + 3, C + 3, p["floor"])
    G.fill(C - 1, F + 4, C - 1, C + 1, F + 4, C + 1, p["trim"])
    for (dx, f) in ((-5, "east"), (5, "west")):                  # stairs up the altar (4 sides)
        G.fill(C + dx, F + 2, C - 1, C + dx, F + 2, C + 1, stairs(p["stair"], f))
    for (dz, f) in ((-5, "south"), (5, "north")):
        G.fill(C - 1, F + 2, C + dz, C + 1, F + 2, C + dz, stairs(p["stair"], f))
    for (x, z) in ((C - 3, C - 3), (C + 3, C - 3), (C - 3, C + 3), (C + 3, C + 3)):  # braziers
        G.set(x, F + 4, z, p["pillar"]); G.set(x, F + 5, z, "campfire")
    for _ in range(40):                                          # moss overgrowth
        x, z = rnd.randint(2, L - 3), rnd.randint(2, L - 3)
        if (x, F + 2, z) not in G.g or G.g[(x, F + 2, z)] == "minecraft:air":
            G.set(x, F + 2, z, "moss_carpet")
    G.set(C, F + 4, C, p["light"])


def lair_citadel(G, p):
    """Walled citadel: corner towers, gatehouse, courtyard and an inner keep."""
    foundation(G, p["base"])
    G.fill(0, F, 0, L - 1, F, L - 1, p["floor"])
    G.fill(1, F + 1, 1, L - 2, F + 9, L - 2, p["wall"])          # outer walls
    G.fill(2, F + 1, 2, L - 3, F + 9, L - 3, "air")
    for i in range(1, L - 1, 2):                                 # crenellations
        for (x, z) in ((i, 1), (i, L - 2), (1, i), (L - 2, i)):
            G.set(x, F + 10, z, p["wall"])
    for (x0, z0) in ((0, 0), (L - 5, 0), (0, L - 5), (L - 5, L - 5)):  # towers
        G.fill(x0, F + 1, z0, x0 + 4, F + 14, z0 + 4, p["wall"])
        G.fill(x0 + 1, F + 1, z0 + 1, x0 + 3, F + 13, z0 + 3, "air")
        for y in (F + 5, F + 10):                                # arrow slits
            G.set(x0 + 2, y, z0, "iron_bars"); G.set(x0 + 2, y, z0 + 4, "iron_bars")
            G.set(x0, y, z0 + 2, "iron_bars"); G.set(x0 + 4, y, z0 + 2, "iron_bars")
        for (cx, cz) in ((x0, z0), (x0 + 4, z0), (x0, z0 + 4), (x0 + 4, z0 + 4)):
            G.set(cx, F + 15, cz, p["wall"])
        G.set(x0 + 2, F + 14, z0 + 2, p["light"]); G.set(x0 + 2, F + 15, z0 + 2, p["fire"])
    G.fill(C - 1, F + 1, 1, C + 1, F + 5, 1, "air")             # gate
    G.fill(C - 1, F + 6, 1, C + 1, F + 7, 1, "iron_bars")
    G.fill(C - 4, F + 1, C - 4, C + 4, F + 7, C + 4, p["wall"])  # inner keep
    G.fill(C - 3, F + 1, C - 3, C + 3, F + 6, C + 3, "air")
    G.fill(C - 4, F + 8, C - 4, C + 4, F + 8, C + 4, p["wall"])
    G.fill(C - 1, F + 1, C - 4, C + 1, F + 3, C - 4, "air")      # keep door
    for (x, z) in ((C - 3, C - 3), (C + 3, C - 3), (C - 3, C + 3), (C + 3, C + 3)):
        G.set(x, F + 6, z, p["light"])
    for (x, z) in ((5, C), (L - 6, C), (C, L - 6)):              # courtyard fire posts
        G.set(x, F + 1, z, p["wall"]); G.set(x, F + 2, z, p["fire"])


def lair_dome(G, p):
    """Great dome: window band, inner pillar ring, skylight and an entrance tunnel."""
    foundation(G, p["base"])
    disc(G, C, C, 12, F, p["floor"])
    win = lambda x, y, z: y == 3 and (x + z) % 3 == 0
    sky = lambda x, y, z: abs(x) <= 1 and abs(z) <= 1 and y >= 9
    G.hemisphere(C, F + 1, C, 10, p["wall"], keep=lambda x, y, z: not win(x, y, z) and not sky(x, y, z))
    G.hemisphere(C, F + 1, C, 10, p["glass"], keep=lambda x, y, z: win(x, y, z) or sky(x, y, z))
    ring(G, C, C, 10, 10.6, F + 1, p["accent"])
    for i in range(8):                                           # pillar ring
        a = i / 8 * math.pi * 2
        x, z = C + round(math.cos(a) * 6), C + round(math.sin(a) * 6)
        G.fill(x, F + 1, z, x, F + 7, z, p["pillar"])
        G.set(x, F + 8, z, p["light"])
    G.fill(C - 2, F + 1, C - 2, C + 2, F + 1, C + 2, p["accent"])  # dais
    G.set(C, F + 1, C, p["light"])
    G.fill(C - 1, F + 1, 0, C + 1, F + 4, C - 8, "air")          # tunnel
    G.fill(C - 2, F + 1, 0, C - 2, F + 4, 3, p["wall"]); G.fill(C + 2, F + 1, 0, C + 2, F + 4, 3, p["wall"])
    G.fill(C - 2, F + 5, 0, C + 2, F + 5, 3, p["wall"])


def build_lair(boss):
    template, pal = LAIR_THEMES[boss]
    G = Grid(L, 24, L)  # tall enough that nothing is clipped; all empty space is cleared to air
    rnd = random.Random(boss)
    if template == "arena": lair_arena(G, pal)
    elif template == "ship": lair_ship(G, pal)
    elif template == "temple": lair_temple(G, pal, rnd)
    elif template == "citadel": lair_citadel(G, pal)
    else: lair_dome(G, pal)
    G.set(C, F - 1, C, f"dbz:core_{boss}")  # hidden marker just under the floor centre
    return G


# =============================================================================
# NPC homes (15 x 16 x 15 with a yard, centre at x=z=7, front on the z=0 side)
# =============================================================================
HS, H = 15, 7


def yard(G, fence, rnd, gate=True):
    foundation(G, "dirt")
    G.fill(0, F, 0, HS - 1, F, HS - 1, "grass_block")
    for i in range(HS):                                          # fence round the yard
        for (x, z) in ((i, 0), (i, HS - 1), (0, i), (HS - 1, i)):
            G.set(x, F + 1, z, fence)
    if gate:
        G.fill(H - 1, F + 1, 0, H + 1, F + 1, 0, "air")
        G.fill(H - 1, F, 0, H + 1, F, 3, "grass_path")
    for _ in range(10):                                          # flowers
        x, z = rnd.randint(1, HS - 2), rnd.randint(1, HS - 2)
        if x in (1, 2, HS - 3, HS - 2) or z in (1, HS - 2):
            G.set(x, F + 1, z, rnd.choice(["poppy", "dandelion", "cornflower", "azure_bluet"]))


def home_cottage():
    rnd = random.Random("cottage")
    G = Grid(HS, 22, HS)
    yard(G, "oak_fence", rnd)
    x0, x1, z0, z1 = 3, 11, 3, 11
    G.fill(x0, F, z0, x1, F, z1, "oak_planks")
    G.fill(x0, F + 1, z0, x1, F + 7, z1, "oak_planks")           # two storeys
    G.fill(x0 + 1, F + 1, z0 + 1, x1 - 1, F + 7, z1 - 1, "air")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        G.fill(x, F + 1, z, x, F + 7, z, "oak_log")
    G.fill(x0 + 1, F + 4, z0 + 1, x1 - 1, F + 4, z1 - 1, "spruce_planks")  # upper floor
    # Staircase along the west wall: 4 steps that land level with the upper floor,
    # an opening above the lower steps for headroom, and a railing round the opening.
    zs = z0 + 2
    for i in range(4):
        G.set(x0 + 1, F + 1 + i, zs + i, stairs("oak_stairs", "south"))
        G.fill(x0 + 1, F + 2 + i, zs + i, x0 + 1, F + 3 + i, zs + i, "air") if i < 3 else None
    for i in range(3):
        G.set(x0 + 1, F + 4, zs + i, "air")                      # opening in the upper floor
        G.set(x0 + 2, F + 5, zs + i, "oak_fence")                # railing
    G.set(x0 + 1, F + 5, zs - 1, "oak_fence")
    G.fill(H, F + 1, z0, H, F + 2, z0, "air")                    # front door
    for y in (F + 2, F + 6):                                     # windows both floors
        for z in (z0 + 2, z1 - 2):
            G.set(x0, y, z, "glass_pane"); G.set(x1, y, z, "glass_pane")
        G.set(H - 2, y, z0, "glass_pane"); G.set(H + 2, y, z0, "glass_pane"); G.set(H, y, z1, "glass_pane")
    for i in range(6):                                           # gable roof (ridge along z)
        y = F + 8 + i
        G.fill(x0 - 1 + i, y, z0 - 1, x1 + 1 - i, y, z1 + 1, "spruce_planks")
        if x0 + i <= x1 - i:
            G.fill(x0 + i, y, z0, x1 - i, y, z1, "air") if i < 5 else None
    G.fill(x1 - 1, F + 1, z1 - 1, x1 - 1, F + 14, z1 - 1, "cobblestone")  # chimney
    G.set(x1 - 1, F + 15, z1 - 1, "campfire")
    G.set(x1 - 1, F + 1, z1 - 1, "furnace")
    G.set(x0 + 2, F + 1, z1 - 1, "crafting_table")
    G.fill(H - 1, F + 1, z1 - 1, H + 1, F + 1, z1 - 1, "bookshelf")
    G.fill(x1 - 3, F + 5, z1 - 3, x1 - 2, F + 5, z1 - 2, "red_carpet")   # bed mat upstairs
    bed(G, x1 - 2, F + 5, z1 - 3, "red")                         # the resident's bed
    G.set(H, F + 3, H, "lantern"); G.set(H, F + 7, H, "lantern")
    G.fill(H - 2, F + 1, z0 - 1, H + 2, F + 1, z0 - 1, "air")    # porch clear
    door(G, H, F + 1, z0, "spruce_door")                         # front door
    G.set(H - 2, F + 1, z0 - 1, "oak_fence"); G.set(H + 2, F + 1, z0 - 1, "oak_fence")
    return G


def home_dome():
    rnd = random.Random("dome")
    G = Grid(HS, 22, HS)
    yard(G, "white_concrete", rnd)
    disc(G, H, H, 6.4, F, "white_concrete")
    band = lambda x, y, z: y == 1
    win = lambda x, y, z: y == 3 and (abs(x) >= 5 and abs(z) <= 1 or abs(z) >= 5 and abs(x) <= 1 and z > 0)
    G.hemisphere(H, F + 1, H, 6, "white_concrete", keep=lambda x, y, z: not band(x, y, z) and not win(x, y, z))
    G.hemisphere(H, F + 1, H, 6, "light_blue_concrete", keep=band)
    G.hemisphere(H, F + 1, H, 6, "light_blue_stained_glass", keep=win)
    G.fill(H - 1, F + 1, 0, H + 1, F + 3, H - 4, "air")          # entrance
    G.fill(H - 1, F + 4, 1, H + 1, F + 4, 2, "light_blue_concrete")  # canopy
    # (v1.32) No loft or stairs: one open room under the dome.
    G.set(H, F + 8, H, "sea_lantern")
    G.fill(H - 3, F + 1, H + 2, H - 2, F + 1, H + 3, "light_blue_carpet")
    bed(G, H - 2, F + 1, H + 2, "light_blue")
    G.set(H + 3, F + 1, H + 3, "bookshelf"); G.set(H - 4, F + 1, H, "crafting_table")
    return G


def home_hut():
    """Training dojo with a pagoda roof and a training yard."""
    rnd = random.Random("dojo")
    G = Grid(HS, 22, HS)
    foundation(G, "stone_bricks")
    G.fill(0, F, 0, HS - 1, F, HS - 1, "packed_mud")
    for i in range(HS):
        for (x, z) in ((i, 0), (i, HS - 1), (0, i), (HS - 1, i)):
            G.set(x, F + 1, z, "spruce_fence")
    G.fill(H - 1, F + 1, 0, H + 1, F + 1, 0, "air")
    G.fill(H - 1, F, 0, H + 1, F, 4, "gravel")
    x0, x1, z0, z1 = 4, 12, 5, 13
    G.fill(x0, F, z0, x1, F, z1, "spruce_planks")
    G.fill(x0, F + 1, z0, x1, F + 4, z1, "spruce_planks")
    G.fill(x0 + 1, F + 1, z0 + 1, x1 - 1, F + 4, z1 - 1, "air")
    for (x, z) in ((x0, z0), (x1, z0), (x0, z1), (x1, z1)):
        G.fill(x, F + 1, z, x, F + 4, z, "dark_oak_log")
    G.fill(H, F + 1, z0, H + 1, F + 3, z0, "air")                # wide door
    door(G, H, F + 1, z0, "dark_oak_door", hinge=False)          # double doors
    door(G, H + 1, F + 1, z0, "dark_oak_door", hinge=True)
    G.fill(H, F + 3, z0, H + 1, F + 3, z0, "spruce_planks")      # wall above the doors
    for z in (z0 + 2, z1 - 2):
        G.set(x0, F + 3, z, "glass_pane"); G.set(x1, F + 3, z, "glass_pane")
    for i, (pad, b) in enumerate(((1, "dark_oak_planks"), (0, "red_concrete"), (-1, "dark_oak_planks"), (-2, "red_concrete"), (-3, "gold_block"))):
        y = F + 5 + i                                            # pagoda roof tiers
        G.fill(x0 - pad, y, z0 - pad, x1 + pad, y, z1 + pad, b)
    G.fill(x0 + 1, F + 1, z0 + 1, x1 - 1, F + 1, z1 - 1, "lime_carpet")    # tatami
    G.fill(x0 + 2, F + 1, z1 - 1, x1 - 2, F + 1, z1 - 1, "spruce_fence")   # weapon rack
    bed(G, x0 + 1, F + 1, z0 + 4, "orange")                      # sleeping mat corner
    G.set(H, F + 4, H + 4, "lantern")
    # Training yard: dummies, targets, hay bales.
    for x in (2, 4):
        G.set(x, F + 1, 3, "oak_fence"); G.set(x, F + 2, 3, "hay_block")
    G.set(12, F + 1, 2, "target"); G.set(12, F + 2, 2, "target")
    G.fill(1, F + 1, 11, 2, F + 2, 12, "hay_block")
    G.set(2, F + 1, 8, "anvil")
    return G


HOMES = {"cottage": home_cottage, "dome": home_dome, "hut": home_hut}


# =============================================================================
# Z Town pieces (15 x 22 x 15, no core blocks: the town script places residents)
# =============================================================================
def town_plaza():
    """Central plaza: fountain with a golden orb, benches, flower beds, lamps."""
    G = Grid(HS, 22, HS)
    foundation(G, "stone")
    G.fill(0, F, 0, HS - 1, F, HS - 1, "smooth_stone")
    for x in range(HS):                                          # checker paving
        for z in range(HS):
            if (x + z) % 2 == 0:
                G.set(x, F, z, "polished_andesite")
    disc(G, H, H, 4.6, F + 1, "stone_bricks")                    # fountain rim
    disc(G, H, H, 3.6, F + 1, "water")
    disc(G, H, H, 3.6, F, "stone_bricks")
    G.fill(H, F + 1, H, H, F + 4, H, "quartz_pillar")            # centre column
    G.set(H, F + 5, H, "gold_block"); G.set(H, F + 6, H, "glowstone")
    for (x, z) in ((H, H - 1), (H, H + 1), (H - 1, H), (H + 1, H)):
        G.set(x, F + 5, z, "gold_block")
    for (x0, z0, f) in ((1, 3, "east"), (1, 9, "east"), (13, 3, "west"), (13, 9, "west")):  # benches
        G.fill(x0, F + 1, z0, x0, F + 1, z0 + 2, stairs("oak_stairs", f))
    for (x, z) in ((1, 1), (13, 1), (1, 13), (13, 13)):          # lamp posts
        G.fill(x, F + 1, z, x, F + 3, z, "dark_oak_fence")
        G.set(x, F + 4, z, "lantern")
    for (x, z) in ((3, 1), (11, 1), (3, 13), (11, 13), (5, 13), (9, 13)):   # flower beds
        G.set(x, F, z, "grass_block")
        G.set(x, F + 1, z, "poppy" if (x + z) % 2 else "dandelion")
    return G


def town_training():
    """Open training ground: sparring ring, targets, dummies, weights."""
    rnd = random.Random("training")
    G = Grid(HS, 22, HS)
    foundation(G, "stone")
    G.fill(0, F, 0, HS - 1, F, HS - 1, "sand")
    G.fill(3, F, 3, 11, F, 11, "smooth_stone")                   # ring floor
    for i in range(3, 12):
        for (x, z) in ((i, 3), (i, 11), (3, i), (11, i)):
            G.set(x, F + 1, z, "polished_andesite")
    G.fill(H - 1, F + 1, 3, H + 1, F + 1, 3, "air")              # ring entrance
    for (x, z) in ((3, 3), (11, 3), (3, 11), (11, 11)):
        G.fill(x, F + 1, z, x, F + 3, z, "spruce_fence"); G.set(x, F + 4, z, "lantern")
    for x in (1, 13):                                            # targets and dummies
        G.set(x, F + 1, 2, "target"); G.set(x, F + 2, 2, "target")
        G.set(x, F + 1, 12, "spruce_fence"); G.set(x, F + 2, 12, "hay_block")
    G.fill(5, F + 1, 13, 9, F + 1, 13, "anvil")                  # "weights"
    return G


def town_park():
    """Small park: trees, pond, hedges and a bench."""
    G = Grid(HS, 22, HS)
    foundation(G, "dirt")
    G.fill(0, F, 0, HS - 1, F, HS - 1, "grass_block")
    leaves = ("minecraft:oak_leaves", {"persistent_bit": True})
    for (tx, tz) in ((3, 3), (11, 4), (4, 11)):                  # trees
        G.fill(tx, F + 1, tz, tx, F + 5, tz, "oak_log")
        for x in range(tx - 2, tx + 3):
            for z in range(tz - 2, tz + 3):
                for y in (F + 4, F + 5):
                    if (x, y, z) != (tx, y, tz) and abs(x - tx) + abs(z - tz) < 4:
                        G.set(x, y, z, leaves)
                if abs(x - tx) + abs(z - tz) <= 1:
                    G.set(x, F + 6, z, leaves)
    disc(G, 10, 10, 2.4, F, "water")                             # pond
    for i in range(1, 14):                                       # hedge edge
        G.set(i, F + 1, 14, leaves)
    G.fill(7, F + 1, 7, 7, F + 1, 8, stairs("oak_stairs", "east"))  # bench
    G.set(7, F + 1, 1, "dark_oak_fence"); G.set(7, F + 2, 1, "dark_oak_fence"); G.set(7, F + 3, 1, "lantern")
    for (x, z) in ((2, 7), (5, 9), (12, 1), (1, 13), (9, 2)):
        G.set(x, F + 1, z, "cornflower" if (x + z) % 2 else "oxeye_daisy")
    return G


TOWN_PIECES = {"town_plaza": town_plaza, "town_training": town_training, "town_park": town_park}


# =============================================================================
# Write everything
# =============================================================================
def write_structure(name, G):
    # Everything inside the volume that isn't set is cleared to air
    # (so trees and terrain inside the footprint don't poke through).
    n = mcstructure.write(f"{BP}/structures/dbz/{name}.mcstructure", G.size, G.g, default="minecraft:air")
    return n


AVOID = [{"test": "has_biome_tag", "operator": "!=", "value": t} for t in ("ocean", "river", "beach", "swamp")]


def feature(ident, structure_name):
    w(f"{BP}/features/{ident}.json", {
        "format_version": "1.13.0",
        "minecraft:structure_template_feature": {
            "description": {"identifier": f"dbz:{ident}"},
            "structure_name": structure_name,
            "adjustment_radius": 0,
            "facing_direction": "north",
            "constraints": {"unburied": {}}
        }
    })


SLOPE_LIMIT = 9  # loose on purpose: heightmap counts treetops, the script check is exact

def slope_y(center):
    e = 2 * center - 2
    pts = [(center, center), (2, 2), (e, 2), (2, e), (e, e)]
    hs = [f"query.heightmap(variable.worldx + {x}, variable.worldz + {z})" for x, z in pts]
    def fold(fn, items):
        out = items[0]
        for h in items[1:]:
            out = f"{fn}({out}, {h})"
        return out
    lo, hi = fold("math.min", hs), fold("math.max", hs)
    return f"(({hi}) - ({lo}) > {SLOPE_LIMIT}) ? -400 : ({lo}) - 1 - {F}"

# ---- Spacing (v1.33) ---------------------------------------------------------
# The world is split into cells of SPACING_CELL x SPACING_CELL chunks. Each cell
# holds at most ONE structure: a hash of the cell's coordinates picks one chunk
# in it (kept away from the cell's far edges) and which structure may go there.
# Every rule computes the same hash, so different structures can't pile up.
SPACING_CELL = 6      # chunks (96 blocks)
SPACING_SLOTS = 3     # the chosen chunk is 0..2 into the cell -> centres >= 64 blocks apart
HOME_SHARE = 0.45     # a bit under half the cells are for homes, the rest for boss lairs

def _cell_hash(k):
    cx = "math.floor(variable.worldx / 16)"
    cz = "math.floor(variable.worldz / 16)"
    gx = f"math.floor({cx} / {SPACING_CELL})"
    gz = f"math.floor({cz} / {SPACING_CELL})"
    v = f"(math.sin({gx} * 12.9898 + {gz} * 78.233 + {k * 37.719:.3f}) * 43758.5453)"
    return f"({v} - math.floor({v}))", cx, cz, gx, gz

def spacing_gate(kind, index, count):
    """Molang condition: true only in this cell's chosen chunk, if the cell belongs to this structure."""
    h1, cx, cz, gx, gz = _cell_hash(1)
    h2 = _cell_hash(2)[0]
    h3 = _cell_hash(3)[0]
    h4 = _cell_hash(4)[0]
    slot = (f"math.abs({cx} - {gx} * {SPACING_CELL} - math.floor({h1} * {SPACING_SLOTS})) < 0.5 && "
            f"math.abs({cz} - {gz} * {SPACING_CELL} - math.floor({h2} * {SPACING_SLOTS})) < 0.5")
    side = f"{h3} < {HOME_SHARE}" if kind == "home" else f"{h3} >= {HOME_SHARE}"
    which = f"math.abs(math.floor({h4} * {count}) - {index}) < 0.5"
    return f"({slot} && {side} && {which})"

def feature_rule(ident, feature_id, chance_den, biome_filter, center, gate=None):
    w(f"{BP}/feature_rules/{ident}.json", {
        "format_version": "1.13.0",
        "minecraft:feature_rules": {
            "description": {"identifier": f"dbz:{ident}", "places_feature": f"dbz:{feature_id}"},
            "conditions": {"placement_pass": "surface_pass", "minecraft:biome_filter": biome_filter},
            "distribution": {
                "iterations": 1,
                "scatter_chance": {"numerator": 1, "denominator": chance_den} if gate is None else {"numerator": 1, "denominator": 1},
                # Anchored at the chunk corner so even 25-block structures stay
                # inside the area the game can write to while generating.
                "x": 0,
                "z": 0,
                # Floor = the ground height at the structure's centre; the deep
                # foundation below fills dips and the cleared space above cuts bumps.
                # Lowest of 5 ground samples (centre + 4 corners). If the samples differ by
                # more than SLOPE_LIMIT the spot is on a hillside: y goes below the world so
                # the structure isn't placed at all (the script also double-checks).
                "y": slope_y(center) if gate is None else f"({gate}) ? ({slope_y(center)}) : -400"
            }
        }
    })


def core_block(ident, texture="dbz_core"):
    w(f"{BP}/blocks/{ident.replace(':', '_')}.json", {
        "format_version": "1.21.60",
        "minecraft:block": {
            "description": {"identifier": ident, "menu_category": {"category": "none"}},
            "components": {
                "minecraft:custom_components": ["dbz:core"],
                "minecraft:tick": {"interval_range": [40, 40], "looping": True},
                "minecraft:geometry": "minecraft:geometry.full_block",
                "minecraft:material_instances": {"*": {"texture": texture, "render_method": "opaque"}},
                "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.75},
                "minecraft:loot": "loot_tables/dbz_empty.json"
            }
        }
    })


# Which biomes each boss's lair generates in (Bedrock biome tags), and how
# rare it is there (1 in N chunks of a matching biome). Rarer biomes get a
# smaller N so their lairs still show up.
LAIR_BIOMES = {
    "frieza":      (["desert"], 1000),                       # spaceship landed in the dunes
    "granolah":    (["desert", "mesa"], 1400),               # sniper's temple in red stone
    "jiren":       (["mesa"], 800),                         # red arena in the badlands
    "cell":        (["plains"], 1200),                       # arena out on the open plains
    "kamin":       (["plains", "meadow"], 1400),
    "toppo":       (["savanna"], 1000),                      # Pride Trooper arena
    "oren":        (["savanna"], 1200),
    "kefla":       (["forest"], 1200),
    "dyspo":       (["birch"], 600),
    "hit":         (["roofed"], 480),                       # assassin's citadel in the dark forest
    "cumber":      (["roofed"], 600),
    "gas":         (["taiga"], 1000),
    "goku_black":  (["extreme_hills"], 800),                # citadel in the windswept hills
    "hearts":      (["extreme_hills", "mountains"], 1000),
    "zamasu":      (["mountains"], 600),                    # gods' temple up on the peaks
    "beerus":      (["jungle"], 600),                       # temple in the jungle
    "fu":          (["mushroom_island", "jungle"], 600),
    "moro":        (["swamp", "mangrove_swamp"], 480),      # mossy citadel in the swamps
    "majin_buu":   (["cherry_grove", "flower_forest"], 250), # pink dome among the blossoms
    "broly":       (["frozen"], 1000),                       # ice arena in snowy lands
}


def lair_biome_filter(tags):
    return {"all_of": [
        {"test": "has_biome_tag", "value": "overworld"},
        {"test": "has_biome_tag", "operator": "!=", "value": "ocean"},
        {"test": "has_biome_tag", "operator": "!=", "value": "river"},
        {"any_of": [{"test": "has_biome_tag", "value": t} for t in tags]}
    ]}


if __name__ == "__main__":
    # Lairs
    for boss in LAIR_THEMES:
        n = write_structure(f"lair_{boss}", build_lair(boss))
        core_block(f"dbz:core_{boss}")
        feature(f"lair_{boss}_feature", f"dbz:lair_{boss}")
        tags, rarity = LAIR_BIOMES[boss]
        feature_rule(f"lair_{boss}_rule", f"lair_{boss}_feature", 1, lair_biome_filter(tags), C,
                     gate=spacing_gate("lair", list(LAIR_BIOMES).index(boss), len(LAIR_BIOMES)))
        print(f"lair_{boss}: {n} block types")
    # Homes
    for name, fn in HOMES.items():
        G = fn()
        G.set(H, F - 1, H, "dbz:home_core")  # just under the floor centre
        n = write_structure(f"home_{name}", G)
        feature(f"home_{name}_feature", f"dbz:home_{name}")
        land = {"all_of": [{"test": "has_biome_tag", "value": "overworld"}] + AVOID + [
            {"test": "has_biome_tag", "operator": "!=", "value": "frozen"}]}
        feature_rule(f"home_{name}_rule", f"home_{name}_feature", 1, land, H,
                     gate=spacing_gate("home", list(HOMES).index(name), len(HOMES)))
        print(f"home_{name}: {n} block types")
    # Z Town pieces (placed by the town script, no world-gen rules)
    for name, fn in TOWN_PIECES.items():
        n = write_structure(name, fn())
        print(f"{name}: {n} block types")
    core_block("dbz:home_core")
    w(f"{BP}/loot_tables/dbz_empty.json", {"pools": []})
    # Texture for the hidden marker blocks (they look like dirt if ever uncovered)
    tt_path = f"{RP}/textures/terrain_texture.json"
    tt = json.load(open(tt_path)) if os.path.exists(tt_path) else {"resource_pack_name": "dbz", "texture_name": "atlas.terrain", "padding": 8, "num_mip_levels": 4, "texture_data": {}}
    tt["texture_data"]["dbz_core"] = {"textures": "textures/blocks/dirt"}
    w(tt_path, tt)
    print("structures, features, rules and core blocks written")
