"""Universe 7: Anime Textures - vanilla batch 1: grass, dirt, stone, cobblestone, sand, gravel.
Saved with the vanilla Bedrock file names into the separate resource pack."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *
from PIL import Image

PACK = "/home/claude/u7_textures/textures/blocks"
os.makedirs(PACK, exist_ok=True)
DONE = []
def vsave(cv, name, im=None):
    p = f"{PACK}/{name}"
    (im or cv.im).save(p); DONE.append(name)

# ------------------------------------------------------------ DIRT
DIRT = ramp((150, 104, 66), 5, hi=(236, 200, 150), lo=(50, 30, 24))
DOUT = (46, 28, 20)
def dirt(seed):
    cv = Canvas(); n = fbm(seed); rnd = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, DIRT[1] if v > 0.64 else DIRT[2] if v > 0.42 else DIRT[3])   # flat anime patches
    for _ in range(26):
        pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(2, 4.5), rnd.uniform(1.6, 3.2),
               ramp((170, 150, 130), 4, hi=WHITE, lo=(60, 50, 44)), DOUT)
    for _ in range(10):                                                    # little roots
        x, y, a = rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(0, 6.28)
        for _ in range(rnd.randint(5, 9)):
            a += rnd.uniform(-0.5, 0.5); x += math.cos(a); y += math.sin(a)
            wput(cv, x, y, (196, 160, 110))
    for _ in range(160):
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, DIRT[4] if rnd.random() < 0.55 else DIRT[0])
    return cv
vsave(dirt(200), "dirt.png")

# ------------------------------------------------------------ GRASS (top is greyscale: Minecraft tints it per biome)
GR = ramp((100, 200, 70), 5, hi=(236, 255, 190), lo=(20, 80, 30))
GOUT = (22, 66, 26)
def grass_colour(seed):
    cv = Canvas(); n = fbm(seed); rnd = random.Random(seed + 1)
    for y in range(S):
        for x in range(S):
            v = n(x, y)
            cv.put(x, y, GR[1] if v > 0.62 else GR[2] if v > 0.42 else GR[3])
    for _ in range(90):
        tuft(cv, rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(6, 10), GR, GOUT, rnd, blades=rnd.randint(3, 5), lean=rnd.uniform(-0.4, 0.4))
    return cv

def to_tint_grey(im, lift=1.0):
    """Greyscale for biome tinting: luminance scaled so the plains tint lands on bright anime greens."""
    g = im.convert("L").point(lambda v: min(255, int(v * 1.45 * lift + 30)))
    return Image.merge("RGBA", (g, g, g, im.split()[3]))

top_col = grass_colour(210)
vsave(top_col, "grass_carried.png")                                        # inventory / carried (full colour)
vsave(None, "grass_top.png", to_tint_grey(top_col.im))

def grass_side(colour=True):
    cv = dirt(200); top = grass_colour(210); rnd = random.Random(211)
    mask = Canvas()                                                        # where the grass is (for tinting)
    def mark(x, y):
        mask.put(int(x) % S, int(y) % S, WHITE)
    for x in range(S):
        depth = 18 + int(4 * math.sin(x / S * 2 * math.pi * 2))
        for y in range(depth):
            cv.put(x, y, top.get(x, y)); mark(x, y)
    lay = Canvas()
    for _ in range(36):
        x = rnd.uniform(0, S); d = 18 + 4 * math.sin(x / S * 2 * math.pi * 2)
        tuft(lay, x, d - 3, rnd.uniform(7, 13), GR, GOUT, rnd, blades=rnd.randint(3, 5), lean=math.pi + rnd.uniform(-0.3, 0.3))
    for y in range(S):
        for x in range(S):
            p = lay.get(x, y)
            if p[3]:
                cv.put(x, y, p[:3]); mark(x, y)
    for x in range(S):
        cv.put(x, 0, GR[1])
    return cv, mask

side, mask = grass_side()
vsave(side, "grass_side_carried.png")
# grass_side.tga: dirt stays as-is (alpha 255); grass pixels are greyscale with alpha 0 = biome-tinted overlay
g = to_tint_grey(side.im)
out = side.im.copy(); op = out.load(); gp = g.load(); mp = mask.im.load()
for y in range(S):
    for x in range(S):
        if mp[x, y][3]:
            v = gp[x, y][0]; op[x, y] = (v, v, v, 0)
out.save(f"{PACK}/grass_side.tga"); DONE.append("grass_side.tga")

# ------------------------------------------------------------ STONE (smooth anime rock: big soft facets, few cracks)
ST = ramp((150, 152, 160), 5, hi=(236, 238, 246), lo=(50, 52, 66))
cv, _ = rocks(220, 9, ST, (120, 122, 132), round_=0.35, crack=0.9, jitter=0.35, n=fbm(221), lip=False, lift=0.1)
rnd = random.Random(222)
for _ in range(8):                                                         # hairline cracks with lit lips
    x, y, a = rnd.uniform(0, S), rnd.uniform(0, S), rnd.uniform(0, 6.28)
    for _ in range(rnd.randint(8, 16)):
        a += rnd.uniform(-0.5, 0.5); x += math.cos(a); y += math.sin(a)
        wput(cv, x, y, ST[4]); wput(cv, x + 1, y + 1, ST[0], 150)
for _ in range(120):                                                       # mineral flecks
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, ST[0] if rnd.random() < 0.4 else ST[3])
vsave(cv, "stone.png")

# ------------------------------------------------------------ COBBLESTONE (rounded outlined stones + moss specks)
CB = ramp((140, 140, 148), 5, hi=(236, 236, 244), lo=(40, 40, 52))
cv, _ = rocks(230, 16, CB, (34, 34, 44), round_=1.0, crack=1.9, jitter=0.15, n=fbm(231))
rnd = random.Random(232)
for _ in range(14):
    x, y = rnd.randrange(S), rnd.randrange(S)
    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1)):
        if rnd.random() < 0.8: wput(cv, x + dx, y + dy, (96, 150, 70) if (dx + dy) % 2 else (70, 120, 56))
for _ in range(80):
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, CB[3])
vsave(cv, "cobblestone.png")

# ------------------------------------------------------------ SAND (bright, rippled, sparkly)
SD = ramp((238, 214, 150), 5, hi=(255, 250, 220), lo=(150, 120, 80))
cv = Canvas(); n = fbm(240); rnd = random.Random(241)
for y in range(S):
    for x in range(S):
        rip = math.sin((y + 6 * n(x, y)) / S * 2 * math.pi * 6)            # wind ripples
        c = SD[1] if rip > 0.6 else SD[2] if rip > -0.6 else SD[3]
        if n(x * 3 % S, y * 3 % S) > 0.7: c = mix(c, SD[0], 0.4)
        cv.put(x, y, c)
for _ in range(220):
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, SD[4] if rnd.random() < 0.5 else SD[0])
for _ in range(10):                                                        # little sparkles of quartz
    x, y = rnd.randrange(S), rnd.randrange(S)
    wput(cv, x, y, WHITE); wput(cv, x + 1, y, WHITE, 120); wput(cv, x, y + 1, WHITE, 120)
for _ in range(5):
    pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(1.6, 2.6), rnd.uniform(1.2, 2), ramp((200, 180, 150), 4, hi=WHITE), (110, 90, 60))
vsave(cv, "sand.png")

# ------------------------------------------------------------ GRAVEL (packed mixed pebbles)
GV = [ramp((150, 146, 140), 4, hi=(240, 236, 230), lo=(50, 46, 44)), ramp((128, 116, 104), 4, hi=(220, 206, 190), lo=(40, 34, 30)),
      ramp((170, 170, 176), 4, hi=(250, 250, 255), lo=(60, 60, 70))]
cv = Canvas()
for y in range(S):
    for x in range(S):
        cv.put(x, y, (112, 104, 96) if (x * 7 + y * 13) % 5 else (92, 86, 80))   # packed grit between pebbles
rnd = random.Random(250)
for _ in range(230):
    pebble(cv, rnd.randrange(S), rnd.randrange(S), rnd.uniform(4, 7.5), rnd.uniform(3, 5.5), rnd.choice(GV), (36, 32, 30))
vsave(cv, "gravel.png")

print("vanilla batch 1:", DONE)
