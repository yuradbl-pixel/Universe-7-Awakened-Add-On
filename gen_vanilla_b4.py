"""Universe 7: Anime Textures - vanilla batch 4: logs (side + top) and planks for all 8 wood types."""
import math, os, sys, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blockkit import *

PACK = "/home/claude/u7_textures/textures/blocks"
DONE = []
def vsave(cv, name):
    cv.save(f"{PACK}/{name}"); DONE.append(name)

# wood type: bark colour, inner wood colour, file names (side, top, planks), bark style
WOODS = {
    "oak":      ((112, 86, 56), (196, 156, 96), ("log_oak.png", "log_oak_top.png", "planks_oak.png"), "ridged"),
    "spruce":   ((70, 50, 34), (132, 96, 58), ("log_spruce.png", "log_spruce_top.png", "planks_spruce.png"), "scaly"),
    "birch":    ((232, 230, 222), (220, 200, 140), ("log_birch.png", "log_birch_top.png", "planks_birch.png"), "birch"),
    "jungle":   ((110, 86, 40), (176, 126, 84), ("log_jungle.png", "log_jungle_top.png", "planks_jungle.png"), "vine"),
    "acacia":   ((110, 104, 94), (200, 100, 56), ("log_acacia.png", "log_acacia_top.png", "planks_acacia.png"), "ridged"),
    "dark_oak": ((64, 46, 28), (90, 60, 34), ("log_big_oak.png", "log_big_oak_top.png", "planks_big_oak.png"), "ridged"),
    "mangrove": ((96, 74, 50), (176, 70, 64), ("mangrove_log_side.png", "mangrove_log_top.png", "mangrove_planks.png"), "scaly"),
    "cherry":   ((54, 34, 44), (230, 176, 172), ("cherry_log_side.png", "cherry_log_top.png", "cherry_planks.png"), "ridged"),
}

def bark(base, style, seed):
    R = ramp(base, 5, hi=mix(base, (255, 246, 220), 0.6), lo=mix(base, (10, 6, 12), 0.7))
    cv = Canvas(); rnd = random.Random(seed); n = fbm(seed)
    if style == "birch":
        for y in range(S):
            for x in range(S):
                v = n(x, y)
                cv.put(x, y, R[0] if v > 0.6 else R[1] if v > 0.4 else R[2])
        for _ in range(26):                                               # black lenticel streaks and patches
            x, y = rnd.randrange(S), rnd.randrange(S); w = rnd.randint(4, 14)
            for dx in range(w):
                wput(cv, x + dx, y, (40, 36, 40)); wput(cv, x + dx, y + 1, (90, 86, 86) if dx % 3 else (40, 36, 40))
            wput(cv, x - 1, y, R[3])
        for _ in range(4):
            x, y = rnd.randrange(S), rnd.randrange(S)
            for dy in range(-3, 4):
                for dx in range(-5, 6):
                    if (dx / 5) ** 2 + (dy / 3) ** 2 <= 1: wput(cv, x + dx, y + dy, (54, 50, 54))
        return cv
    ridges = 10 if style != "scaly" else 14
    for y in range(S):
        for x in range(S):
            wob = 4 * (n(x, y) - 0.5) * 2
            u = ((x + wob) / S * ridges) % 1                             # position across one ridge
            if style == "scaly":
                u = ((x + wob + (y // 12) * 5) / S * ridges) % 1
            c = R[1] if u < 0.25 else R[2] if u < 0.62 else R[3] if u < 0.82 else R[4]   # lit ridge -> groove
            if style == "scaly" and y % 12 == 0: c = R[4]
            cv.put(x, y, c)
    for _ in range(3):                                                    # knots
        kx, ky = rnd.randrange(S), rnd.randrange(S)
        for dy in range(-5, 6):
            for dx in range(-4, 5):
                d = (dx / 4) ** 2 + (dy / 5) ** 2
                if d <= 1: wput(cv, kx + dx, ky + dy, R[4] if d < 0.3 else R[3] if d < 0.7 else R[1])
    if style == "vine":                                                   # jungle: moss and little vines
        for _ in range(6):
            x, y = rnd.uniform(0, S), rnd.uniform(0, S)
            for _ in range(rnd.randint(10, 24)):
                y += 1; x += rnd.uniform(-0.7, 0.7)
                wput(cv, x, y, (70, 150, 60)); wput(cv, x + 1, y, (40, 100, 40))
                if rnd.random() < 0.2: wput(cv, x + 2, y, (110, 190, 80))
    for _ in range(90):
        x, y = rnd.randrange(S), rnd.randrange(S)
        wput(cv, x, y, R[0] if rnd.random() < 0.3 else R[4])
    return cv

def log_top(bark_col, wood_col, seed):
    BR = ramp(bark_col, 5, hi=mix(bark_col, (255, 246, 220), 0.6), lo=mix(bark_col, (10, 6, 12), 0.7))
    W = ramp(wood_col, 5, hi=mix(wood_col, (255, 248, 226), 0.6), lo=mix(wood_col, (30, 14, 10), 0.65))
    cv = Canvas(); rnd = random.Random(seed); n = fbm(seed)
    for y in range(S):
        for x in range(S):
            d = max(abs(x + 0.5 - 64), abs(y + 0.5 - 64)) * 0.55 + math.hypot(x + 0.5 - 64, y + 0.5 - 64) * 0.45
            if d > 58:
                c = BR[1] if (x + y) % 5 else BR[3]                       # bark rim
                if d > 61: c = BR[3]
            elif d > 56:
                c = W[4]                                                   # cambium line
            else:
                ring = (d + n(x, y) * 4) % 7
                c = W[1] if ring < 2.5 else W[2] if ring < 5.5 else W[3]   # growth rings
                if d < 4: c = W[3]
            cv.put(x, y, c)
    for k in range(5):                                                     # drying cracks from the centre
        a = rnd.uniform(0, 6.28); x, y = 64.0, 64.0
        for i in range(rnd.randint(18, 34)):
            a += rnd.uniform(-0.15, 0.15); x += math.cos(a); y += math.sin(a)
            cv.put(int(x), int(y), W[4])
    soft_spot(cv, 46, 44, 18, 14, (255, 255, 240), 60)
    return cv

def planks(wood_col, seed):
    R = ramp(wood_col, 5, hi=mix(wood_col, (255, 248, 226), 0.6), lo=mix(wood_col, (30, 14, 10), 0.65))
    cv = Canvas(); rnd = random.Random(seed); gn = fbm(seed + 10, ((2, 0.5), (16, 0.5)))
    for row in range(4):                                                   # 4 boards per block, like vanilla
        y0 = row * 32; cut = rnd.randrange(S); tone = rnd.uniform(-0.2, 0.2)
        for y in range(32):
            for x in range(S):
                if y == 0: c = R[4]
                elif y in (1, 2): c = R[0] if y == 1 else R[1]
                elif y >= 29: c = R[3]
                else:
                    c = mix(R[2], R[1] if tone > 0 else R[3], abs(tone))
                    gv = math.sin(y * 0.9 + gn(x, row * 32) * 10 + row * 2)
                    if abs(gv) < 0.2: c = mix(c, R[3], 0.6)
                    elif gv > 0.92: c = mix(c, R[1], 0.4)
                if (x - cut) % S == 0: c = R[4]
                elif (x - cut) % S == 1 and 2 < y < 29: c = R[0]
                cv.put(x, y0 + y, c)
        for nx in ((cut + 5) % S, (cut - 6) % S):
            for ny in (y0 + 9, y0 + 22):
                cv.put(nx, ny, (60, 60, 70)); cv.put(nx, ny - 1, (190, 190, 200))
    return cv

for i, (wid, (bk, wd, (fside, ftop, fpl), style)) in enumerate(WOODS.items()):
    vsave(bark(bk, style, 700 + i), fside)
    vsave(log_top(bk, wd, 720 + i), ftop)
    vsave(planks(wd, 740 + i), fpl)
print("vanilla batch 4:", len(DONE), "textures")
