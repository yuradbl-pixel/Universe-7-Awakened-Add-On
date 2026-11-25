"""Universe 7: Anime Textures - vanilla batch 6: animated water & lava (still + flowing), glass,
16 stained glass colours and their pane edges."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *
from PIL import Image

PACK = "/home/claude/u7_textures/textures/blocks"
DONE = []
TAU = 2 * math.pi
FR = 16                                                                   # animation frames

def strip(frames):
    w, h = frames[0].size
    out = Image.new("RGBA", (w, h * len(frames)))
    for i, f in enumerate(frames):
        out.paste(f, (0, i * h))
    return out

def water_frame(size, t, flow=False):
    """Greyscale anime water (tinted per biome by the game). Seamless in space and time."""
    im = Image.new("RGBA", (size, size)); px = im.load()
    k = TAU / size
    for y in range(size):
        for x in range(size):
            yy = y - (t * size if flow else 0)                             # flowing water slides down
            a = math.sin(k * (x * 2 + yy) + TAU * t) + math.sin(k * (x - yy * 2) * 2 - TAU * t) * 0.6
            b = math.sin(k * (x * 3 - yy) - TAU * t * 2) * 0.5
            v = a + b
            lum = 176 if v < -0.9 else 200 if v < 0.3 else 222               # three flat cel bands
            if abs(math.sin(k * (x * 2 + yy) * 2 + TAU * t + 1.0) + 0.25 * b) < 0.13 and v > -0.2:
                lum = 250                                                  # crisp white ripple line
            if flow and int(yy * 0.5 + x * 0.25) % 23 == 0 and (x * 7) % 11 < 3:
                lum = 240                                                  # streaks in flowing water
            px[x, y] = (lum, lum, lum, 190)
    return im

def lava_frame(size, t, flow=False):
    im = Image.new("RGBA", (size, size)); px = im.load()
    k = TAU / size
    L = [(255, 246, 170), (255, 196, 60), (246, 120, 30), (180, 50, 20), (90, 24, 14)]
    for y in range(size):
        for x in range(size):
            yy = y - (t * size if flow else 0)
            v = (math.sin(k * (x + yy * 2) * 2 + TAU * t) + math.sin(k * (x * 2 - yy) * 3 - TAU * t) * 0.7 +
                 math.sin(k * (x * 4 + yy * 3) + TAU * t * 2) * 0.4)
            c = L[0] if v > 1.5 else L[1] if v > 0.6 else L[2] if v > -0.5 else L[3] if v > -1.4 else L[4]   # cooling crust
            px[x, y] = c + (255,)
    return im

for name, fn, flow, size in (("water_still_grey.png", water_frame, False, 128), ("water_flow_grey.png", water_frame, True, 256),
                             ("lava_still.png", lava_frame, False, 128), ("lava_flow.png", lava_frame, True, 256)):
    frames = [fn(size, i / FR, flow) for i in range(FR)]
    strip(frames).save(f"{PACK}/{name}"); DONE.append(name)

# ------------------------------------------------------------ glass & stained glass
def glass(tint=None):
    cv = Canvas()
    edge = (226, 240, 255) if tint is None else mix(tint, (255, 255, 255), 0.35)
    edge_dk = (150, 180, 210) if tint is None else mix(tint, (10, 10, 30), 0.35)
    for y in range(S):
        for x in range(S):
            e = min(x, y, S - 1 - x, S - 1 - y)
            if e < 3:                                                      # frame: lit top-left, darker bottom-right
                c = edge if (x < y and x == e) or (y <= x and y == e) else edge_dk
                if e == 0: c = mix(c, (60, 80, 110), 0.5)
                cv.put(x, y, c)
            elif tint is not None:
                cv.put(x, y, tint, 120)                                    # tinted pane
    for (x0, w) in ((18, 7), (32, 3), (70, 5)):                            # diagonal anime reflection streaks
        for i in range(S):
            for d in range(w):
                x, y = x0 + i + d, S - 1 - i
                if 3 <= x < S - 3 and 3 <= y < S - 3:
                    cv.put(x, y, (255, 255, 255), 150 if d not in (0, w - 1) else 90)
    for (cx, cy) in ((14, 14),):                                           # corner glint
        sparkle(cv, cx, cy, 3)
    return cv

def pane_top(tint=None):
    cv = Canvas()
    edge = (226, 240, 255) if tint is None else mix(tint, (255, 255, 255), 0.35)
    edge_dk = (150, 180, 210) if tint is None else mix(tint, (10, 10, 30), 0.35)
    for y in range(S):
        for x in range(S):
            cv.put(x, y, edge if (x // 8) % 2 == 0 else edge_dk)
    return cv

glass().save(f"{PACK}/glass.png"); DONE.append("glass.png")
pane_top().save(f"{PACK}/glass_pane_top.png"); DONE.append("glass_pane_top.png")
COLS = {"white": (240, 240, 245), "orange": (240, 130, 40), "magenta": (200, 70, 200), "light_blue": (100, 180, 240),
        "yellow": (250, 214, 50), "lime": (130, 210, 50), "pink": (245, 150, 190), "gray": (90, 94, 104),
        "silver": (160, 162, 168), "cyan": (40, 160, 170), "purple": (130, 60, 190), "blue": (54, 70, 190),
        "brown": (120, 80, 50), "green": (80, 120, 40), "red": (190, 50, 44), "black": (34, 34, 42)}
for name, col in COLS.items():
    glass(col).save(f"{PACK}/glass_{name}.png"); DONE.append(f"glass_{name}.png")
    pane_top(col).save(f"{PACK}/glass_pane_top_{name}.png"); DONE.append(f"glass_pane_top_{name}.png")
print("vanilla batch 6:", len(DONE), "textures")
