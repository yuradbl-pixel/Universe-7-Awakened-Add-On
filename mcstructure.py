# mcstructure.py
# Minimal writer (and reader, for testing) for Bedrock .mcstructure files
# (little-endian NBT).
import struct

END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE, BYTEARR, STRING, LIST, COMPOUND, INTARR = range(12)
BLOCK_VERSION = 18168865  # 1.21.60.33


class Tag:
    def __init__(self, t, v):
        self.t, self.v = t, v


def _str(s):
    b = s.encode("utf-8")
    return struct.pack("<H", len(b)) + b


def _payload(t, v):
    if t == BYTE:
        return struct.pack("<b", v)
    if t == SHORT:
        return struct.pack("<h", v)
    if t == INT:
        return struct.pack("<i", v)
    if t == LONG:
        return struct.pack("<q", v)
    if t == FLOAT:
        return struct.pack("<f", v)
    if t == STRING:
        return _str(v)
    if t == LIST:
        et, items = v
        return struct.pack("<bi", et, len(items)) + b"".join(_payload(et, i) for i in items)
    if t == COMPOUND:
        out = b""
        for name, tag in v.items():
            out += struct.pack("<b", tag.t) + _str(name) + _payload(tag.t, tag.v)
        return out + struct.pack("<b", END)
    raise ValueError(t)


# Block states every block of these kinds must have in 1.21.60. A palette entry
# with missing states isn't recognised by the game and the block is dropped.
def default_states(name):
    n = name.replace("minecraft:", "")
    if n.endswith("_log") or n.endswith("_wood") or n.endswith("_pillar") or n in ("basalt", "bone_block"):
        return {"pillar_axis": "y"}
    if n == "hay_block":
        return {"deprecated": 0, "pillar_axis": "y"}
    if n.endswith("_leaves"):
        return {"persistent_bit": True, "update_bit": False}
    if n in ("furnace", "blast_furnace", "smoker", "anvil", "chipped_anvil", "damaged_anvil",
             "carved_pumpkin", "lit_pumpkin", "loom", "stonecutter_block", "grindstone_block"):
        return {"minecraft:cardinal_direction": "north"}
    if n in ("campfire", "soul_campfire"):
        return {"extinguished": False, "minecraft:cardinal_direction": "north"}
    if n in ("lantern", "soul_lantern"):
        return {"hanging": False}
    if n in ("water", "lava", "flowing_water", "flowing_lava"):
        return {"liquid_depth": 0}
    if n.endswith("_door"):
        return {"direction": 0, "door_hinge_bit": False, "open_bit": False, "upper_block_bit": False}
    if n == "bed":
        return {"direction": 0, "head_piece_bit": False, "occupied_bit": False}
    if n in ("torch", "soul_torch"):
        return {"torch_facing_direction": "top"}
    if n.endswith("_stairs"):
        return {"upside_down_bit": False, "weirdo_direction": 0}
    return {}


def _state_tag(val, key=""):
    if key.endswith("_bit") or isinstance(val, bool):
        return Tag(BYTE, 1 if val else 0)
    if isinstance(val, int):
        return Tag(INT, val)
    return Tag(STRING, str(val))


def write(path, size, grid, default=None):
    """grid: dict (x,y,z) -> block name or (name, {states}). Cells not in grid use
    `default` (a block name) or are left untouched (-1) if default is None."""
    sx, sy, sz = size
    palette, index = [], {}
    indices = []
    pos_data = {}
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                b = grid.get((x, y, z), default)
                if b is None:
                    indices.append(-1)
                    continue
                # Cell: name | (name, states) | (name, states, block_entity_data)
                if isinstance(b, str):
                    name, given, be = b, {}, None
                else:
                    name, given, be = b[0], b[1], (b[2] if len(b) > 2 else None)
                states = {**default_states(name), **given}
                key = (name, tuple(sorted((k, int(v) if isinstance(v, bool) else v) for k, v in states.items())))
                if key not in index:
                    index[key] = len(palette)
                    palette.append({
                        "name": Tag(STRING, name),
                        "states": Tag(COMPOUND, {k: _state_tag(v, k) for k, v in states.items()}),
                        "version": Tag(INT, BLOCK_VERSION),
                    })
                if be is not None:
                    pos_data[str(len(indices))] = Tag(COMPOUND, {"block_entity_data": Tag(COMPOUND, {
                        **{k: v for k, v in be.items()},
                        "x": Tag(INT, x), "y": Tag(INT, y), "z": Tag(INT, z),
                    })})
                indices.append(index[key])
    root = {
        "format_version": Tag(INT, 1),
        "size": Tag(LIST, (INT, list(size))),
        "structure_world_origin": Tag(LIST, (INT, [0, 0, 0])),
        "structure": Tag(COMPOUND, {
            "block_indices": Tag(LIST, (LIST, [(INT, indices), (INT, [-1] * len(indices))])),
            "entities": Tag(LIST, (COMPOUND, [])),
            "palette": Tag(COMPOUND, {"default": Tag(COMPOUND, {
                "block_palette": Tag(LIST, (COMPOUND, palette)),
                "block_position_data": Tag(COMPOUND, pos_data),
            })}),
        }),
    }
    data = struct.pack("<b", COMPOUND) + _str("") + _payload(COMPOUND, root)
    with open(path, "wb") as f:
        f.write(data)
    return len(palette)


# ---- reader (round-trip test) ------------------------------------------------
def read(path):
    buf = open(path, "rb").read()
    pos = [0]

    def take(fmt):
        n = struct.calcsize(fmt)
        v = struct.unpack_from(fmt, buf, pos[0])
        pos[0] += n
        return v[0]

    def rstr():
        n = take("<H")
        s = buf[pos[0]:pos[0] + n].decode()
        pos[0] += n
        return s

    def rpay(t):
        if t == BYTE: return take("<b")
        if t == SHORT: return take("<h")
        if t == INT: return take("<i")
        if t == LONG: return take("<q")
        if t == FLOAT: return take("<f")
        if t == STRING: return rstr()
        if t == LIST:
            et = take("<b"); n = take("<i")
            return [rpay(et) for _ in range(n)]
        if t == COMPOUND:
            d = {}
            while True:
                tt = take("<b")
                if tt == END:
                    return d
                name = rstr()
                d[name] = rpay(tt)
        raise ValueError(t)

    assert take("<b") == COMPOUND
    rstr()
    return rpay(COMPOUND)
