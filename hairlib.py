# hairlib.py
# Builds hair cubes for the NPC model and the player hair attachables.
#
# Rotation conventions (Bedrock geometry):
#   +rx tips a spike's top toward the FRONT (-z); -rx sweeps it BACK (+z)
#   +rz tips a spike's top toward +x;            -rz toward -x
# The head cube spans x,z in [-4, 4] and y in [24, 32].
#
# Every spike is tapered: three stacked boxes (base, middle, tip) sharing one
# pivot and rotation, so they read as sharp points instead of sticks.

def _r(v):
    return round(v, 2)

def spike(x, y, z, rx, rz, L, w, uv, ry=0):
    segs = [(1.0, 0.0, 0.5), (0.68, 0.5, 0.3), (0.34, 0.8, 0.22)]  # (width scale, start, length share)
    cubes = []
    for ws, start, share in segs:
        ww = w * ws
        cubes.append({
            "origin": [_r(x - ww / 2), _r(y + L * start), _r(z - ww / 2)],
            "size": [_r(ww), _r(L * share), _r(ww)],
            "pivot": [_r(x), _r(y), _r(z)],
            "rotation": [rx, ry, rz],
            "uv": list(uv),
        })
    return cubes

def cap(uv_cap):
    # Scalp cover sitting just over the top of the head.
    return [{"origin": [-4.5, 31.2, -4.5], "size": [9, 2, 9], "uv": list(uv_cap)}]

def bangs(uv):
    out = []
    # Hang down over the forehead (rx near 180 = pointing down, a bit forward).
    for x, rz, L in ((-2.6, -8, 2.6), (-0.6, 4, 3.1), (1.6, 10, 2.8), (3.2, 14, 2.2)):
        out += spike(x, 32.2, -4.35, 168, rz, L, 2.0, uv)
    return out

def sides(uv, length=6):
    out = []
    for sx in (-1, 1):
        out += spike(sx * 4.0, 30.2, -0.5, -10, sx * 58, length, 2.6, uv)
        out += spike(sx * 4.0, 28.8, 1.8, -30, sx * 70, length - 1, 2.2, uv)
    return out

def back_tufts(uv):
    out = []
    for x, rz in ((-2.6, -25), (0, 0), (2.6, 25)):
        out += spike(x, 30, 3.8, -62, rz, 7, 2.8, uv)
    return out

STYLES = {}

def style_spiky(uv_spike, uv_cap):
    c = cap(uv_cap) + bangs(uv_spike) + sides(uv_spike) + back_tufts(uv_spike)
    crown = [
        (0, 32.6, 1.2, -18, 0, 11, 3.2),
        (-2.1, 32.6, -0.6, 6, -32, 9.5, 3.0),
        (2.1, 32.6, -0.6, 6, 32, 9.5, 3.0),
        (-2.9, 32.2, 2.2, -32, -46, 9, 3.0),
        (2.9, 32.2, 2.2, -32, 46, 9, 3.0),
        (0, 32.6, -2.1, 26, 0, 8, 2.8),
        (-1.1, 32.6, 0.9, -6, -12, 12, 2.6),
        (1.2, 32.6, 0.4, 0, 16, 11, 2.6),
    ]
    for x, y, z, rx, rz, L, w in crown:
        c += spike(x, y, z, rx, rz, L, w, uv_spike)
    return c

def style_slick(uv_spike, uv_cap):
    # Tall spikes swept up and back.
    c = cap(uv_cap) + back_tufts(uv_spike)
    for x, z, rx, rz, L in ((0, -2.5, -38, 0, 12), (-1.8, -1.5, -42, -10, 11), (1.8, -1.5, -42, 10, 11),
                            (-3, 0, -50, -22, 10), (3, 0, -50, 22, 10), (0, 0.5, -48, 0, 13),
                            (-1.4, 2, -60, -8, 10), (1.4, 2, -60, 8, 10)):
        c += spike(x, 32.6, z, rx, rz, L, 3.0, uv_spike)
    for sx in (-1, 1):
        c += spike(sx * 4.1, 29.5, -1, -70, sx * 30, 6, 2.2, uv_spike)
    c += spike(0, 32.2, -4.35, 170, 0, 2.6, 2.0, uv_spike)  # small front point
    return c

def style_long(uv_spike, uv_cap):
    # Spiky top plus a heavy mane down the back.
    c = style_spiky(uv_spike, uv_cap)
    for x, rz, L in ((-3, -12, 15), (-1, -4, 18), (1, 4, 18), (3, 12, 15)):
        c += spike(x, 30.5, 3.9, -168, rz, L, 3.2, uv_spike)
    for sx in (-1, 1):
        c += spike(sx * 4.1, 29.5, 1.5, -8, sx * 168, 12, 2.6, uv_spike)
    return c

def style_short(uv_spike, uv_cap):
    c = cap(uv_cap)
    pts = [(-3, -3), (-1, -3.3), (1, -3.3), (3, -3), (-3.2, -0.5), (-1, -0.8), (1, -0.6), (3.2, -0.4),
           (-3, 2.2), (-1, 2.5), (1, 2.6), (3, 2.2)]
    for i, (x, z) in enumerate(pts):
        rx = 25 if z < -2 else (-35 if z > 1.5 else (8 if i % 2 else -8))
        rz = int(x * 10)
        c += spike(x, 32.6, z, rx, rz, 3.8, 2.4, uv_spike)
    return c

def style_flowing(uv_spike, uv_cap, uv_panel_side, uv_panel_back):
    # Straight hair falling to the shoulders.
    c = cap(uv_cap) + bangs(uv_spike)
    for sx in (-1, 1):
        x0 = 4.0 if sx > 0 else -5.0
        c.append({"origin": [x0, 23.5, -3.5], "size": [1, 8, 7], "uv": list(uv_panel_side)})
    c.append({"origin": [-4, 21, 4.0], "size": [8, 10, 1], "uv": list(uv_panel_back)})
    for x, rz in ((-2.8, -6), (0, 0), (2.8, 6)):
        c += spike(x, 23, 4.6, -178, rz, 5, 2.4, uv_spike)
    for x, z, rx, rz in ((-2, -1, 10, -20), (2, -1, 10, 20), (0, 1.5, -20, 0)):
        c += spike(x, 32.6, z, rx, rz, 3.2, 2.6, uv_spike)
    return c

def build(style, uv_spike, uv_cap, uv_panel_side=None, uv_panel_back=None):
    if style == "spiky":
        return style_spiky(uv_spike, uv_cap)
    if style == "slick":
        return style_slick(uv_spike, uv_cap)
    if style == "long":
        return style_long(uv_spike, uv_cap)
    if style == "short":
        return style_short(uv_spike, uv_cap)
    if style == "flowing":
        return style_flowing(uv_spike, uv_cap, uv_panel_side, uv_panel_back)
    return []

HAIR_STYLE_NAMES = ["spiky", "slick", "long", "short", "flowing"]
