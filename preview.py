import math, sys
from PIL import Image, ImageDraw
sys.path.insert(0,"/home/claude/tools")
import hairlib

def rot(v, rx, ry, rz):
    x,y,z=v
    a=math.radians(rx); c,s=math.cos(a),math.sin(a); y,z = c*y+s*z, -s*y+c*z      # +rx: +y -> -z
    a=math.radians(ry); c,s=math.cos(a),math.sin(a); x,z = c*x-s*z, s*x+c*z
    a=math.radians(rz); c,s=math.cos(a),math.sin(a); x,y = c*x+s*y, -s*x+c*y      # +rz: +y -> +x
    return (x,y,z)

def cube_faces(cb):
    ox,oy,oz=cb["origin"]; sx,sy,sz=cb["size"]; inf=cb.get("inflate",0)
    ox-=inf; oy-=inf; oz-=inf; sx+=2*inf; sy+=2*inf; sz+=2*inf
    P=[(ox+dx*sx,oy+dy*sy,oz+dz*sz) for dx in (0,1) for dy in (0,1) for dz in (0,1)]
    piv=cb.get("pivot",[0,0,0]); r=cb.get("rotation",[0,0,0])
    P=[tuple(a+b for a,b in zip(rot(tuple(p[i]-piv[i] for i in range(3)),*r),piv)) for p in P]
    idx=[(0,1,3,2),(4,6,7,5),(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3)]
    return [[P[i] for i in f] for f in idx]

def render(cubes_colored, yaw, size=300, scale=9, cy=28, pitch=-15):
    im=Image.new("RGB",(size,size),(46,48,54)); d=ImageDraw.Draw(im)
    faces=[]
    L=(0.4,0.8,-0.45)
    for cubes,col in cubes_colored:
        for cb in cubes:
            for f in cube_faces(cb):
                f2=[rot((p[0],p[1]-cy,p[2]),pitch,yaw,0) for p in f]
                # normal
                a=[f2[1][i]-f2[0][i] for i in range(3)]; b=[f2[2][i]-f2[0][i] for i in range(3)]
                n=(a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]); ln=math.sqrt(sum(v*v for v in n)) or 1
                n=[v/ln for v in n]
                shade=0.55+0.45*abs(n[0]*L[0]+n[1]*L[1]+n[2]*L[2])
                depth=sum(p[2] for p in f2)/4
                faces.append((depth,[(size/2+p[0]*scale,size/2-p[1]*scale) for p in f2],tuple(int(c*shade) for c in col)))
    for dp,poly,c in sorted(faces,key=lambda t:-t[0]):
        d.polygon(poly,fill=c,outline=tuple(int(v*0.7) for v in c))
    return im

head=[{"origin":[-4,24,-4],"size":[8,8,8]}]
rows=[]
for st in hairlib.HAIR_STYLE_NAMES:
    hc=hairlib.build(st,[0,32],[16,32],[0,32],[16,32])
    row=Image.new("RGB",(900,300))
    for i,yaw in enumerate((25,100,180)):
        row.paste(render([(head,(236,190,150)),(hc,(255,205,60))],yaw),(i*300,0))
    ImageDraw.Draw(row).text((8,8),st,fill=(255,255,255))
    rows.append(row)
out=Image.new("RGB",(900,300*len(rows)))
for i,r in enumerate(rows): out.paste(r,(0,i*300))
out=out.resize((675,225*len(rows)))
out.save("/tmp/hair_preview.png")
print("cubes per style:",{s:len(hairlib.build(s,[0,32],[16,32],[0,32],[16,32])) for s in hairlib.HAIR_STYLE_NAMES})
