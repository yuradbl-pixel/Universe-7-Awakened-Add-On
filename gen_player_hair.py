# Player transformation hair (attachables worn in the helmet slot).
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hairlib
from PIL import Image, ImageDraw
RP="/home/claude/dbz/DBZ_RP"
def w(p,o): open(p,"w").write(json.dumps(o,indent=2)+"\n")
# Texture layout (64x32 UV space): spikes/panels at (0,0) 16x16, cap/back panel at (16,0).
for style in ("spiky","long","slick"):
    cubes=hairlib.build(style,[0,0],[16,0],[0,0],[16,0])
    w(f"{RP}/models/entity/hair_{style}.geo.json",{"format_version":"1.12.0","minecraft:geometry":[{
      "description":{"identifier":f"geometry.dbz.hair_{style}","texture_width":64,"texture_height":32,
        "visible_bounds_width":3,"visible_bounds_height":4,"visible_bounds_offset":[0,1.5,0]},
      "bones":[{"name":"head","pivot":[0,24,0]},{"name":"dbz_hair","parent":"head","pivot":[0,24,0],"cubes":cubes}]}]})
# Which style each hair piece uses
STYLE={"gold":"spiky","gold_long":"long","black":"spiky","black_long":"long","red":"spiky",
       "blue":"spiky","silver":"spiky","purple":"slick","green":"spiky"}
COLOR={"gold":(255,214,60),"gold_long":(255,214,60),"black":(28,28,34),"black_long":(28,28,34),"red":(220,40,60),
       "blue":(70,190,255),"silver":(225,230,240),"purple":(150,70,220),"green":(185,240,90)}
for key,style in STYLE.items():
    p=f"{RP}/attachables/hair_{key}.json"; a=json.load(open(p))
    a["minecraft:attachable"]["description"]["geometry"]={"default":f"geometry.dbz.hair_{style}"}
    w(p,a)
    # 128x64 HD texture: light roots fading to darker tips, with strand lines
    c=COLOR[key]; lt=tuple(min(255,int(v*1.15)+25) for v in c); dk=tuple(int(v*0.65) for v in c)
    im=Image.new("RGBA",(128,64),c+(255,)); d=ImageDraw.Draw(im)
    for y in range(32):  # spike region rows (0..32 in HD) gradient
        t=y/31; col=tuple(int(lt[k]*(1-t)+dk[k]*t) for k in range(3)); d.line((0,y,31,y),fill=col+(255,))
    for y in range(64):
        t=y/63; col=tuple(int(c[k]*(1-t*0.35)) for k in range(3)); d.line((32,y,127,y),fill=col+(255,))
    for x in range(34,128,5): d.line((x,0,x+2,63),fill=dk+(255,))
    for x in range(2,32,4): d.line((x,0,x,31),fill=tuple(int(v*0.85) for v in c)+(255,))
    d.rectangle((32,0,127,2),fill=lt+(255,))
    im.save(f"{RP}/textures/entity/hair/{key}.png")
print("player hair done")
