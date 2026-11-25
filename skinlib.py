# skinlib.py
# Helpers for user-supplied player-format skins (64x64 or HD 128x128):
#   * recolor_hair / recolor_dark_hair : make missing forms by recoloring hair
#   * recolor_light                     : recolor white/light body parts (Frieza forms)
#   * slim_to_classic                   : widen 3-px (slim) arms to 4-px (classic)
#   * paint_tail                        : fill the unused (56,16)-(64,24) area for tails
# All coordinates below are in 64x64 units and scaled for HD skins.
import colorsys
from PIL import Image

HEAD_REGIONS = [(0, 0, 32, 16), (32, 0, 64, 16)]  # head + hat layer


def _hsv(p):
    return colorsys.rgb_to_hsv(p[0] / 255, p[1] / 255, p[2] / 255)


def _scale(im):
    return max(1, im.width // 64)


def _pixels(im, box):
    s = _scale(im)
    for y in range(box[1] * s, box[3] * s):
        for x in range(box[0] * s, box[2] * s):
            yield x, y


def hair_reference(im):
    """Median hue/sat/value of saturated pixels on top of the head/hat."""
    px = []
    for box in [(40, 0, 48, 8), (8, 0, 16, 8)]:
        px += [im.getpixel(xy) for xy in _pixels(im, box) if im.getpixel(xy)[3] > 0]
        if len(px) > 20 * _scale(im) ** 2:
            break
    hsvs = [_hsv(p) for p in px if _hsv(p)[1] > 0.35 and _hsv(p)[2] > 0.3]
    if not hsvs:
        return None
    hsvs.sort(key=lambda h: h[0])
    return hsvs[len(hsvs) // 2]


def recolor_hair(src, target_rgb, hue_tol=0.045, min_sat=0.45):
    """Recolor colored hair (e.g. gold) to target_rgb, keeping shading."""
    im = src.copy()
    ref = hair_reference(im)
    if not ref:
        return im
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target_rgb))
    for box in HEAD_REGIONS:
        for xy in _pixels(im, box):
            p = im.getpixel(xy)
            if p[3] == 0:
                continue
            h, s, v = _hsv(p)
            dh = min(abs(h - ref[0]), 1 - abs(h - ref[0]))
            if dh > hue_tol or s < min_sat:
                continue
            nv = max(0.0, min(1.0, tv * (v / max(ref[2], 0.01))))
            r, g, b = colorsys.hsv_to_rgb(th, ts, nv)
            im.putpixel(xy, (int(r * 255), int(g * 255), int(b * 255), p[3]))
    return im


def recolor_dark_hair(src, target_rgb, max_val=0.32):
    """Recolor black/dark hair, skipping the lower face (eyes, mouth)."""
    im = src.copy()
    s = _scale(im)
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target_rgb))
    face_fronts = [(8 * s, 16 * s), (40 * s, 48 * s)]
    for box in HEAD_REGIONS:
        for x, y in _pixels(im, box):
            if y >= 11 * s and any(a <= x < b for a, b in face_fronts):
                continue
            p = im.getpixel((x, y))
            if p[3] == 0:
                continue
            h, sat, v = _hsv(p)
            if v > max_val:
                continue
            nv = max(0.35, min(1.0, tv * (0.65 + v)))
            r, g, b = colorsys.hsv_to_rgb(th, ts, nv)
            im.putpixel((x, y), (int(r * 255), int(g * 255), int(b * 255), p[3]))
    return im


def recolor_light(src, target_rgb, max_sat=0.2, min_val=0.62):
    """Recolor white/light-gray areas anywhere on the skin (body color changes)."""
    im = src.copy()
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target_rgb))
    for xy in _pixels(im, (0, 0, 64, 64)):
        p = im.getpixel(xy)
        if p[3] == 0:
            continue
        h, s, v = _hsv(p)
        if s > max_sat or v < min_val:
            continue
        nv = max(0.0, min(1.0, tv * (0.55 + 0.45 * v)))
        r, g, b = colorsys.hsv_to_rgb(th, ts, nv)
        im.putpixel(xy, (int(r * 255), int(g * 255), int(b * 255), p[3]))
    return im


def _is_slim(im):
    s = _scale(im)
    return all(im.getpixel((x, y))[3] == 0 for x in range(54 * s, 56 * s) for y in range(20 * s, 32 * s))


def _widen(face):
    """Stretch a 3-wide face to 4 wide by repeating its middle column."""
    w, h = face.size
    unit = w // 3
    out = Image.new("RGBA", (unit * 4, h), (0, 0, 0, 0))
    out.paste(face.crop((0, 0, unit * 2, h)), (0, 0))
    out.paste(face.crop((unit, 0, unit * 2, h)), (unit * 2, 0))
    out.paste(face.crop((unit * 2, 0, unit * 3, h)), (unit * 3, 0))
    return out


def slim_to_classic(src):
    """Convert slim (3-px) arms to classic (4-px) arms. Returns src if already classic."""
    if not _is_slim(src):
        return src
    im = src.copy()
    s = _scale(im)
    for ox, oy in ((40, 16), (40, 32), (32, 48), (48, 48)):  # arm + sleeve areas, both arms
        X, Y = ox * s, oy * s
        area = src.crop((X, Y, X + 16 * s, Y + 16 * s))
        new = Image.new("RGBA", (16 * s, 16 * s), (0, 0, 0, 0))
        top, bottom = area.crop((4 * s, 0, 7 * s, 4 * s)), area.crop((7 * s, 0, 10 * s, 4 * s))
        right = area.crop((0, 4 * s, 4 * s, 16 * s))
        front = area.crop((4 * s, 4 * s, 7 * s, 16 * s))
        left = area.crop((7 * s, 4 * s, 11 * s, 16 * s))
        back = area.crop((11 * s, 4 * s, 14 * s, 16 * s))
        new.paste(_widen(top), (4 * s, 0))
        new.paste(_widen(bottom), (8 * s, 0))
        new.paste(right, (0, 4 * s))
        new.paste(_widen(front), (4 * s, 4 * s))
        new.paste(left, (8 * s, 4 * s))
        new.paste(_widen(back), (12 * s, 4 * s))
        im.paste(Image.new("RGBA", (16 * s, 16 * s), (0, 0, 0, 0)), (X, Y))
        im.paste(new, (X, Y))
    return im


def paint_tail(im, rgb):
    """Paint the tail texture into (56,16)-(64,24). The player model never shows
    this area, so overwriting it doesn't change how the skin looks."""
    im = im.copy()
    pts = list(_pixels(im, (56, 16, 64, 24)))
    s = _scale(im)
    dk = tuple(int(c * 0.78) for c in rgb)
    for x, y in pts:
        im.putpixel((x, y), (dk if ((x // s) + (y // s)) % 3 == 0 else rgb) + (255,))
    return im


def legacy_to_64(src):
    """Convert an old 64x32 skin to 64x64 by mirroring the right arm/leg to the left."""
    if src.height * 2 != src.width:
        return src
    s = _scale(src)
    im = Image.new("RGBA", (64 * s, 64 * s), (0, 0, 0, 0))
    im.paste(src, (0, 0))

    def mirror_limb(ox, oy, nx, ny):
        limb = src.crop((ox * s, oy * s, (ox + 16) * s, (oy + 16) * s))
        out = Image.new("RGBA", limb.size, (0, 0, 0, 0))
        flip = lambda b: limb.crop(tuple(v * s for v in b)).transpose(Image.FLIP_LEFT_RIGHT)
        # top/bottom stay put (mirrored); right<->left side faces swap; front/back mirrored.
        out.paste(flip((4, 0, 8, 4)), (4 * s, 0))
        out.paste(flip((8, 0, 12, 4)), (8 * s, 0))
        out.paste(flip((8, 4, 12, 16)), (0, 4 * s))
        out.paste(flip((4, 4, 8, 16)), (4 * s, 4 * s))
        out.paste(flip((0, 4, 4, 16)), (8 * s, 4 * s))
        out.paste(flip((12, 4, 16, 16)), (12 * s, 4 * s))
        im.paste(out, (nx * s, ny * s))

    mirror_limb(0, 16, 16, 48)   # right leg -> left leg
    mirror_limb(40, 16, 32, 48)  # right arm -> left arm
    return im


def skin_reference(im):
    """Median color of the face (cheeks/chin area) = the character's skin tone."""
    px = [im.getpixel(xy) for xy in _pixels(im, (9, 13, 15, 16)) if im.getpixel(xy)[3] > 0]
    hsvs = sorted((_hsv(p) for p in px), key=lambda h: h[2])
    return hsvs[len(hsvs) // 2] if hsvs else None


def recolor_skin_tone(src, target_rgb, hue_tol=0.05, min_sat=0.3):
    """Recolor the body's skin tone everywhere (e.g. orange -> green)."""
    im = src.copy()
    ref = skin_reference(im)
    if not ref:
        return im
    th, ts, tv = colorsys.rgb_to_hsv(*(c / 255 for c in target_rgb))
    for xy in _pixels(im, (0, 0, 64, 64)):
        p = im.getpixel(xy)
        if p[3] == 0:
            continue
        h, s, v = _hsv(p)
        dh = min(abs(h - ref[0]), 1 - abs(h - ref[0]))
        if dh > hue_tol or s < min_sat:
            continue
        nv = max(0.0, min(1.0, tv * (v / max(ref[2], 0.01))))
        ns = max(0.0, min(1.0, ts * (s / max(ref[1], 0.01))))
        r, g, b = colorsys.hsv_to_rgb(th, ns, nv)
        im.putpixel(xy, (int(r * 255), int(g * 255), int(b * 255), p[3]))
    return im
