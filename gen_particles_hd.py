"""Universe 7 texture pack, category 3: PARTICLES & EFFECTS.
Textures (flipbook strips, frames left->right) + the particle effect JSON files that use them."""
import math, os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageFilter
from pixlib import *

RP = "/home/claude/dbz/DBZ_RP"
TEX = f"{RP}/textures/particle/dbz"
PART = f"{RP}/particles"
os.makedirs(TEX, exist_ok=True)
MADE = []

def save(cv, name):
    p = f"{TEX}/{name}.png"; cv.save(p); MADE.append((p, name))

def strip(frames, fw, fh):
    cv = Canvas(fw * len(frames), fh)
    for i, f in enumerate(frames):
        cv.paste(f, i * fw, 0)
    return cv

def soft(f, r):
    """Soft edges: blur the alpha slightly but keep the bright core."""
    a = f.im.split()[3].filter(ImageFilter.GaussianBlur(r))
    f.im.putalpha(a); f.px = f.im.load()
    return f

def radial(fw, fh, fn):
    """fn(d, x, y) -> (rgb, alpha) with d = distance from centre in 0..1."""
    cv = Canvas(fw, fh); cx, cy = fw / 2, fh / 2; R = min(fw, fh) / 2
    for y in range(fh):
        for x in range(fw):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / R
            r = fn(d, x, y)
            if r:
                cv.put(x, y, r[0], clamp(r[1]))
    return cv

WHITE = (255, 255, 255)

# ------------------------------------------------------------ AURA (8-frame flame flicker)
def aura_frame(i, tint=None):
    f = Canvas(32, 32); rnd = random.Random(100 + i)
    sway = math.sin(i / 8 * 2 * math.pi) * 2.2
    h = 26 + 3 * math.sin(i / 8 * 4 * math.pi + 1)
    for y in range(32):
        for x in range(32):
            t = (31 - y) / h                                            # 0 at base, 1 at tip
            if t < 0 or t > 1:
                continue
            cx = 16 + sway * t ** 1.5
            half = 9 * (1 - t) ** 0.7 * (0.8 + 0.2 * math.sin(t * 9 + i))
            dx = abs(x + 0.5 - cx)
            if dx > half:
                continue
            k = 1 - dx / max(0.5, half)                                 # 1 in the middle of the flame
            v = (0.35 + 0.65 * k) * (1 - t * 0.55)
            a = 255 * min(1, k * 2.2) * (1 - t ** 3)
            g = clamp(150 + 105 * v)
            if tint:
                c = mix(tint[2], mix(tint[1], tint[0], min(1, k * 1.4)), min(1, v * 1.4))
            else:
                c = (g, g, g)
            f.put(x, y, c, a)
    for _ in range(3):                                                  # bright licks inside
        x, y = rnd.randint(12, 20), rnd.randint(10, 26)
        f.put(x, y, WHITE if not tint else tint[0], 200)
    return soft(f, 0.6)

save(strip([aura_frame(i) for i in range(8)], 32, 32), "aura_white")
AURA_COLS = {  # core, mid, edge
    "gold": ((255, 252, 220), (255, 214, 60), (220, 120, 10)),
    "blue": ((230, 250, 255), (80, 190, 255), (20, 70, 200)),
    "red": ((255, 230, 210), (255, 70, 50), (150, 10, 20)),
    "silver": ((255, 255, 255), (210, 220, 240), (120, 130, 170)),
    "purple": ((250, 220, 255), (170, 80, 255), (70, 10, 130)),
    "pink": ((255, 235, 245), (255, 120, 190), (180, 30, 110)),
    "black_purple": ((200, 150, 255), (80, 30, 130), (16, 6, 26)),
}
for name, cols in AURA_COLS.items():
    save(strip([aura_frame(i, cols) for i in range(8)], 32, 32), f"aura_{name}")

# ------------------------------------------------------------ KI / BEAM: core, glow, edge (+ 4-frame pulse)
save(radial(32, 32, lambda d, x, y: (WHITE if d < 0.4 else mix(WHITE, (225, 225, 225), (d - 0.4) / 0.6),
            255 * (1 if d < 0.35 else max(0, 1 - (d - 0.35) / 0.62) ** 1.6)) if d < 0.97 else None), "beam_core")
save(radial(32, 32, lambda d, x, y: ((255, 255, 255), 255 * max(0, 1 - d) ** 2.2) if d < 1 else None), "beam_glow")
save(radial(32, 32, lambda d, x, y: (WHITE, 255 * math.exp(-((d - 0.78) / 0.09) ** 2)) if d < 1 else None), "beam_edge")
pulse = []
for i in range(4):
    k = 0.85 + 0.15 * math.sin(i / 4 * 2 * math.pi)
    pulse.append(radial(32, 32, lambda d, x, y, k=k: (WHITE, 255 * max(0, 1 - d / k) ** 1.4) if d < k else None))
save(strip(pulse, 32, 32), "ki_pulse")

# ------------------------------------------------------------ LIGHTNING (4 frames)
def bolt_frame(i):
    f = Canvas(32, 32); rnd = random.Random(300 + i)
    def bolt(x, y, ang, L, w):
        base = ang
        pts = [(x, y)]
        for _ in range(L):
            ang += rnd.uniform(-0.8, 0.8)
            ang = ang * 0.6 + base * 0.4                                # stay roughly on course
            x = min(29, max(2, x + 3.0 * math.cos(ang))); y = min(30, max(1, y + 3.0 * math.sin(ang)))
            pts.append((x, y))
        d = f.draw()
        d.line(pts, fill=(180, 180, 180, 150), width=w + 2)
        d.line(pts, fill=(255, 255, 255, 255), width=w)
        return pts
    main = bolt(16, 2, math.pi / 2, 9, 1)
    for k in (3, 6):                                                    # forks
        x, y = main[k]; bolt(x, y, math.pi / 2 + rnd.choice((-0.9, 0.9)), 3, 1)
    return f

save(strip([bolt_frame(i) for i in range(4)], 32, 32), "lightning")

# ------------------------------------------------------------ IMPACT FLASH (4 frames, expanding star)
def flash_frame(i):
    s = (i + 1) / 4
    def fn(d, x, y):
        a = math.atan2(y + 0.5 - 16, x + 0.5 - 16)
        spike = 0.25 + 0.75 * abs(math.cos(a * 4)) ** 6
        lim = s * (0.35 + 0.65 * spike)
        if d > lim:
            return None
        return (WHITE, 255 * (1 - d / lim) ** 0.6 * (1 - 0.5 * s ** 2))
    return radial(32, 32, fn)

save(strip([flash_frame(i) for i in range(4)], 32, 32), "impact_flash")

# ------------------------------------------------------------ EXPLOSION (8 frames, full colour)
FIRE = [(255, 255, 230), (255, 230, 120), (255, 160, 40), (230, 80, 20), (130, 40, 30), (60, 50, 50)]
def explosion_frame(i):
    t = i / 7; rnd = random.Random(500)
    f = Canvas(32, 32)
    blobs = [(16 + rnd.uniform(-6, 6), 16 + rnd.uniform(-6, 6), rnd.uniform(4, 8)) for _ in range(9)]
    for y in range(32):
        for x in range(32):
            best = 0
            for bx, by, br in blobs:
                R = br * (0.5 + 1.3 * t ** 0.6)
                dd = math.hypot(x + 0.5 - (16 + (bx - 16) * (1 + t)), y + 0.5 - (by - 6 * t))
                best = max(best, 1 - dd / R)
            if best <= 0:
                continue
            heat = best * (1 - t) * 1.8                                   # hot centre, cooling to smoke
            if heat > 0.25:
                c = FIRE[int(min(3, max(0, (1 - min(1, heat)) * 4)))]
            else:
                g = clamp(70 + 90 * best - 40 * t)                        # shaded grey smoke
                c = mix((g, g, g), FIRE[3], heat * 2)
            f.put(x, y, c, 255 * min(1, best * 3) * (1 - t ** 1.5 * 0.7))
    return soft(f, 0.5)

save(strip([explosion_frame(i) for i in range(8)], 32, 32), "explosion")

# ------------------------------------------------------------ DUST (4 frames, grey, tinted brown in the effect)
def dust_frame(i):
    t = i / 3; rnd = random.Random(700)
    f = Canvas(32, 32)
    puffs = [(16 + rnd.uniform(-8, 8), 18 + rnd.uniform(-5, 5), rnd.uniform(5, 8)) for _ in range(6)]
    for y in range(32):
        for x in range(32):
            best = 0
            for px_, py_, r in puffs:
                R = r * (0.7 + 0.6 * t)
                best = max(best, 1 - math.hypot(x + 0.5 - px_, y + 0.5 - (py_ - 3 * t)) / R)
            if best > 0:
                g = clamp(170 + 70 * best - 30 * t)
                f.put(x, y, (g, g, g), 230 * min(1, best * 2.5) * (1 - t * 0.6))
    return soft(f, 0.7)

save(strip([dust_frame(i) for i in range(4)], 32, 32), "dust")

# ------------------------------------------------------------ ROCK DEBRIS (4 variants, 16x16)
ROCK = ramp((128, 110, 94), 5, hi=(230, 220, 200), lo=(30, 24, 26))
def rock(i):
    f = Canvas(16, 16); rnd = random.Random(900 + i)
    pts = [(8 + (4 + rnd.uniform(0, 3)) * math.cos(a), 8 + (4 + rnd.uniform(0, 3)) * math.sin(a))
           for a in [k * 2 * math.pi / 6 + rnd.uniform(-0.3, 0.3) for k in range(6)]]
    ins = poly_inside(pts)
    shade_shape(f, lambda x, y: ins(x, y), lambda x, y: ((x - 8) / 8, (y - 8) / 8, 0.7), ROCK)
    for _ in range(3):
        f.put(rnd.randint(5, 10), rnd.randint(5, 10), ROCK[3])            # cracks / pits
    if i % 2:
        for x in range(4, 12):
            if f.get(x, 5)[3]: f.put(x, 5, (90, 140, 60))                 # grass on top of some chunks
    outline(f, color=(20, 16, 14))
    return f

save(strip([rock(i) for i in range(4)], 16, 16), "rock_debris")

# ------------------------------------------------------------ SPIRIT BOMB (4 frames, 64x64)
def spirit_frame(i):
    f = Canvas(64, 64)
    E = ramp((120, 190, 255), 6, hi=(255, 255, 255), lo=(30, 60, 160))
    sphere(f, 32, 32, 26, E, gamma=0.6)
    for k in range(5):                                                   # swirling energy bands across the surface
        for a in range(0, 360, 3):
            ang = math.radians(a + i * 22 + k * 40)
            r = 8 + k * 4
            x, y = 32 + r * math.cos(ang), 32 + r * 0.45 * math.sin(ang) + (k - 2) * 3
            f.put(int(x), int(y), (235, 248, 255), 150)
    soft_spot(f, 24, 22, 9, 7, WHITE, 220)
    arc_light(f, 32, 32, 26, 0, 360, (200, 235, 255), 220, 2)
    glow(f, (140, 200, 255), 3, 0.9)
    rnd = random.Random(40 + i)
    for _ in range(8):                                                   # motes flowing in
        a = rnd.uniform(0, 6.28); r = rnd.uniform(28, 31)
        f.put(int(32 + r * math.cos(a)), int(32 + r * math.sin(a)), WHITE, 230)
    return f

save(strip([spirit_frame(i) for i in range(4)], 64, 64), "spirit_bomb")

# ------------------------------------------------------------ DESTRUCTO DISC (4 frames spin, 64x64)
def disc_frame(i):
    f = Canvas(64, 64)
    E = ramp((255, 230, 90), 5, hi=(255, 255, 255), lo=(200, 120, 20))
    for y in range(64):
        for x in range(64):
            dx, dy = x + 0.5 - 32, y + 0.5 - 32
            d = math.hypot(dx, dy); a = math.atan2(dy, dx) + i * (math.pi / 16)
            saw = 26 + 4 * ((a * 16 / (2 * math.pi)) % 1)                 # serrated rim
            if d <= saw:
                k = d / saw
                c = E[0] if k < 0.25 else E[1] if k < 0.6 else E[2] if k < 0.9 else E[3]
                if 0.4 < k < 0.9 and int((a * 6 / math.pi) % 2) == 0:
                    c = mix(c, WHITE, 0.25)                               # spin streaks
                f.put(x, y, c, 255 if k > 0.15 else 255)
    glow(f, (255, 220, 80), 2, 0.8)
    return f

save(strip([disc_frame(i) for i in range(4)], 64, 64), "destructo_disc")

# ------------------------------------------------------------ HAKAI (8 frames: sigil forms, then crumbles)
def hakai_frame(i):
    t = i / 7; f = Canvas(32, 32); rnd = random.Random(1200)
    P = [(250, 220, 255), (200, 120, 255), (130, 50, 220), (60, 10, 110)]
    ring_r = 6 + 8 * min(1, t * 2)
    for a in range(0, 360, 4):                                           # rotating ring of glyph dashes
        if (a // 20) % 2 == 0:
            x, y = 16 + ring_r * math.cos(math.radians(a + i * 15)), 16 + ring_r * math.sin(math.radians(a + i * 15))
            f.put(int(x), int(y), P[1], 230 * (1 - max(0, t - 0.6) * 2))
    core = 6 * (1 - t) + 1
    sphere(f, 16, 16, core, P, gamma=1.3)
    for k in range(16):                                                  # fragments drifting up and fading
        a = rnd.uniform(0, 6.28); r = rnd.uniform(2, 6) + 10 * t
        x, y = 16 + r * math.cos(a), 16 + r * math.sin(a) - 8 * t * rnd.uniform(0.5, 1)
        s = 2 if k % 3 else 1
        for yy in range(s):
            for xx in range(s):
                f.put(int(x) + xx, int(y) + yy, P[(k % 3)], 255 * (1 - t * 0.8))
    return f

save(strip([hakai_frame(i) for i in range(8)], 32, 32), "hakai")

# ============================================================ PARTICLE EFFECT FILES
def flip(tex_w, tex_h, fw, fh, frames, fps=None, loop=False, stretch=True):
    fb = {"base_UV": [0, 0], "size_UV": [fw, fh], "step_UV": [fw, 0], "max_frame": frames, "loop": loop}
    if stretch:
        fb["stretch_to_lifetime"] = True
    else:
        fb["frames_per_second"] = fps or 12
    return {"texture_width": tex_w, "texture_height": tex_h, "flipbook": fb}

def effect(ident, texture, material, comps):
    json.dump({"format_version": "1.10.0", "particle_effect": {
        "description": {"identifier": ident, "basic_render_parameters": {"material": material, "texture": f"textures/particle/dbz/{texture}"}},
        "components": comps}}, open(f"{PART}/{ident.split(':')[1]}.json", "w"), indent=2)

FADE = "1 - variable.particle_age / variable.particle_lifetime"
TINT = {"color": ["variable.color.r", "variable.color.g", "variable.color.b", f"variable.color.a * ({FADE})"]}

# aura: white flame flipbook tinted with the form/race colour
effect("dbz:aura", "aura_white", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 12},
    "minecraft:emitter_lifetime_once": {"active_time": 0.1},
    "minecraft:emitter_shape_disc": {"offset": [0, 0.1, 0], "radius": 0.6, "plane_normal": "y", "direction": [0, 1, 0]},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "0.5 + math.random(0, 0.35)"},
    "minecraft:particle_initial_speed": "math.random(0.8, 1.6)",
    "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 1.4, 0], "linear_drag_coefficient": 1.6},
    "minecraft:particle_appearance_billboard": {"size": ["0.28 + 0.12 * variable.particle_random_1", "0.42 + 0.16 * variable.particle_random_1"],
        "facing_camera_mode": "lookat_y", "uv": flip(256, 32, 32, 32, 8, loop=True, stretch=False, fps=16)},
    "minecraft:particle_appearance_tinting": TINT})

# beam body: hot core sprite, tinted
effect("dbz:beam", "beam_core", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 1},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.25},
    "minecraft:particle_appearance_billboard": {"size": [f"variable.size * 0.55 * (1 - 0.6 * variable.particle_age / variable.particle_lifetime)"] * 2,
        "facing_camera_mode": "rotate_xyz", "uv": {"texture_width": 32, "texture_height": 32, "uv": [0, 0], "uv_size": [32, 32]}},
    "minecraft:particle_appearance_tinting": {"color": ["variable.color.r", "variable.color.g", "variable.color.b", "1 - 0.5 * variable.particle_age / variable.particle_lifetime"]}})

# charging orb: pulsing ki sprite with an edge ring look
effect("dbz:charge_orb", "ki_pulse", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 1},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.2},
    "minecraft:particle_appearance_billboard": {"size": ["0.12 + variable.size * 0.16"] * 2, "facing_camera_mode": "rotate_xyz",
        "uv": flip(128, 32, 32, 32, 4)},
    "minecraft:particle_appearance_tinting": {"color": ["variable.color.r", "variable.color.g", "variable.color.b", 1.0]}})

# impact: expanding star flash (tinted with the move colour)
effect("dbz:impact", "impact_flash", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 1},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.3},
    "minecraft:particle_appearance_billboard": {"size": ["0.6 + variable.size * 0.8"] * 2, "facing_camera_mode": "rotate_xyz",
        "uv": flip(128, 32, 32, 32, 4)},
    "minecraft:particle_appearance_tinting": {"color": ["variable.color.r", "variable.color.g", "variable.color.b", 1.0]}})

# level up: golden sparks shooting out
effect("dbz:levelup_burst", "lightning", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 14},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_sphere": {"offset": [0, 1, 0], "radius": 0.4, "direction": "outwards"},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "0.4 + math.random(0, 0.3)"},
    "minecraft:particle_initial_speed": "math.random(2, 4)",
    "minecraft:particle_motion_dynamic": {"linear_drag_coefficient": 3},
    "minecraft:particle_appearance_billboard": {"size": [0.22, 0.22], "facing_camera_mode": "rotate_xyz", "uv": flip(128, 32, 32, 32, 4)},
    "minecraft:particle_appearance_tinting": {"color": [1.0, 0.85, 0.25, FADE]}})

# ki trail behind blasts
effect("dbz:ki_trail", "beam_glow", "particles_add", {
    "minecraft:emitter_rate_steady": {"spawn_rate": 30, "max_particles": 40},
    "minecraft:emitter_lifetime_looping": {"active_time": 1},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.35},
    "minecraft:particle_appearance_billboard": {"size": [f"0.35 * ({FADE})"] * 2, "facing_camera_mode": "rotate_xyz",
        "uv": {"texture_width": 32, "texture_height": 32, "uv": [0, 0], "uv_size": [32, 32]}},
    "minecraft:particle_appearance_tinting": {"color": [0.5, 0.9, 1.0, 1.0]}})

# NEW: lightning sparks around a powered-up player (tinted)
effect("dbz:lightning", "lightning", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 2},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_box": {"offset": [0, 1.0, 0], "half_dimensions": [0.5, 0.9, 0.5]},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.18},
    "minecraft:particle_appearance_billboard": {"size": [0.35, 0.35], "facing_camera_mode": "rotate_xyz", "uv": flip(128, 32, 32, 32, 4)},
    "minecraft:particle_appearance_tinting": {"color": ["variable.color.r * 0.5 + 0.5", "variable.color.g * 0.5 + 0.5", "variable.color.b * 0.5 + 0.5", 1.0]}})

# NEW: explosion fireball (full colour, alpha blended)
effect("dbz:explosion", "explosion", "particles_blend", {
    "minecraft:emitter_rate_instant": {"num_particles": "2 + variable.size * 2"},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_sphere": {"radius": "0.3 + variable.size * 0.4", "direction": "outwards"},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "0.6 + math.random(0, 0.3)"},
    "minecraft:particle_initial_speed": "math.random(0.5, 1.5)",
    "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.8, 0], "linear_drag_coefficient": 2},
    "minecraft:particle_appearance_billboard": {"size": ["0.8 + variable.size * 0.7"] * 2, "facing_camera_mode": "rotate_xyz", "uv": flip(256, 32, 32, 32, 8)},
    "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, 1]}})

# NEW: dust cloud (grey texture tinted earthy)
effect("dbz:dust", "dust", "particles_blend", {
    "minecraft:emitter_rate_instant": {"num_particles": "4 + variable.size * 3"},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_disc": {"radius": "0.5 + variable.size * 0.5", "plane_normal": "y", "direction": "outwards"},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "1.0 + math.random(0, 0.6)"},
    "minecraft:particle_initial_speed": "math.random(1, 2.5)",
    "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.3, 0], "linear_drag_coefficient": 2.2},
    "minecraft:particle_appearance_billboard": {"size": ["0.7 + variable.particle_random_1 * 0.6"] * 2, "facing_camera_mode": "rotate_xyz", "uv": flip(128, 32, 32, 32, 4)},
    "minecraft:particle_appearance_tinting": {"color": [0.72, 0.62, 0.5, f"0.85 * ({FADE})"]}})

# NEW: rock debris (random chunk per particle, falls with gravity and bounces)
effect("dbz:debris", "rock_debris", "particles_alpha", {
    "minecraft:emitter_rate_instant": {"num_particles": "5 + variable.size * 3"},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_sphere": {"radius": 0.4, "direction": [ "math.random(-1, 1)", "math.random(0.8, 1.6)", "math.random(-1, 1)"]},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "1.2 + math.random(0, 0.6)"},
    "minecraft:particle_initial_speed": "math.random(4, 8)",
    "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, -18, 0], "linear_drag_coefficient": 0.4},
    "minecraft:particle_motion_collision": {"coefficient_of_restitution": 0.3, "collision_radius": 0.1, "collision_drag": 4},
    "minecraft:particle_appearance_billboard": {"size": ["0.12 + variable.particle_random_2 * 0.12"] * 2, "facing_camera_mode": "rotate_xyz",
        "uv": {"texture_width": 64, "texture_height": 16, "uv": ["math.floor(variable.particle_random_1 * 4) * 16", 0], "uv_size": [16, 16]}},
    "minecraft:particle_appearance_lighting": {}})

# NEW: Spirit Bomb sphere (size from the script)
effect("dbz:spirit_bomb", "spirit_bomb", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 1},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.2},
    "minecraft:particle_appearance_billboard": {"size": ["0.4 + variable.size * 1.2"] * 2, "facing_camera_mode": "rotate_xyz", "uv": flip(256, 64, 64, 64, 4, loop=True, stretch=False, fps=10)},
    "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, 1]}})

# NEW: Destructo Disc (spinning saw)
effect("dbz:destructo_disc", "destructo_disc", "particles_add", {
    "minecraft:emitter_rate_instant": {"num_particles": 1},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_point": {},
    "minecraft:particle_lifetime_expression": {"max_lifetime": 0.1},
    "minecraft:particle_appearance_billboard": {"size": ["0.6 + variable.size * 0.8"] * 2, "facing_camera_mode": "rotate_xyz", "uv": flip(256, 64, 64, 64, 4, loop=True, stretch=False, fps=20)},
    "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, 1]}})

# NEW: Hakai (sigil forms, then the target crumbles away)
effect("dbz:hakai", "hakai", "particles_blend", {
    "minecraft:emitter_rate_instant": {"num_particles": 3},
    "minecraft:emitter_lifetime_once": {"active_time": 0},
    "minecraft:emitter_shape_box": {"offset": [0, 0, 0], "half_dimensions": [0.3, 0.6, 0.3], "direction": [0, 1, 0]},
    "minecraft:particle_lifetime_expression": {"max_lifetime": "0.6 + math.random(0, 0.3)"},
    "minecraft:particle_initial_speed": 0.6,
    "minecraft:particle_motion_dynamic": {"linear_acceleration": [0, 0.8, 0]},
    "minecraft:particle_appearance_billboard": {"size": ["0.5 + variable.size * 0.4"] * 2, "facing_camera_mode": "rotate_xyz", "uv": flip(256, 32, 32, 32, 8)},
    "minecraft:particle_appearance_tinting": {"color": [1, 1, 1, 1]}})

print(f"particles: {len(MADE)} textures")
