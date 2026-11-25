# Draws 128x128 item icons (supersampled at 512 then downscaled for smooth edges).
# Dragon Ball icons are left as they are.
import math
from PIL import Image, ImageDraw, ImageFilter, ImageFont
RP="/home/claude/dbz/DBZ_RP/textures/items"
S=512
def canvas(): 
    im=Image.new("RGBA",(S,S),(0,0,0,0)); return im, ImageDraw.Draw(im)
def save(im,name):
    im=im.resize((128,128),Image.LANCZOS); im.save(f"{RP}/{name}.png")
def radial(d, box, inner, outer, steps=40):
    x0,y0,x1,y1=box
    for i in range(steps):
        t=i/steps; c=tuple(int(outer[k]+(inner[k]-outer[k])*t) for k in range(4))
        ix=(x1-x0)/2*t*0.92; iy=(y1-y0)/2*t*0.92
        d.ellipse((x0+ix,y0+iy,x1-ix,y1-iy),fill=c)
def shadow(im, offset=10, blur=14, alpha=110):
    a=im.split()[3]; sh=Image.new("RGBA",im.size,(0,0,0,0)); sh.putalpha(a.point(lambda v:min(alpha,v)))
    sh=sh.filter(ImageFilter.GaussianBlur(blur)); base=Image.new("RGBA",im.size,(0,0,0,0)); base.paste(sh,(offset,offset),sh)
    return Image.alpha_composite(base,im)
def font(size):
    for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf","/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"]:
        try: return ImageFont.truetype(f,size)
        except Exception: pass
    return ImageFont.load_default()

# ---- Scouter: handheld scanner with a green screen and antenna ----
im,d=canvas()
d.rounded_rectangle((120,90,392,440),radius=60,fill=(70,74,86,255),outline=(30,32,38,255),width=12)
d.rounded_rectangle((150,130,362,300),radius=26,fill=(20,60,30,255))
radial(d,(160,140,352,290),(140,255,150,255),(30,120,50,255))
for y in range(150,290,18): d.line((165,y,347,y),fill=(20,90,40,120),width=3)
d.line((230,215,300,180),fill=(220,255,220,255),width=8); d.ellipse((295,172,315,192),fill=(255,255,255,255))
d.ellipse((205,330,255,380),fill=(200,60,60,255),outline=(30,30,30,255),width=6)
d.ellipse((265,330,315,380),fill=(230,200,60,255),outline=(30,30,30,255),width=6)
d.rectangle((320,30,336,100),fill=(50,52,60,255)); d.ellipse((310,14,346,50),fill=(140,255,150,255))
save(shadow(im),"dbz_scouter")

# ---- Race Reset Token: violet coin with a circular arrow ----
im,d=canvas()
radial(d,(56,56,456,456),(225,170,255,255),(110,40,170,255))
d.ellipse((56,56,456,456),outline=(60,20,100,255),width=16)
d.ellipse((96,96,416,416),outline=(240,210,255,200),width=8)
d.arc((156,156,356,356),30,320,fill=(255,255,255,255),width=26)
d.polygon([(348,200),(392,236),(330,256)],fill=(255,255,255,255))
d.ellipse((140,120,220,170),fill=(255,255,255,90))
save(shadow(im),"dbz_race_reset_token")

# ---- Move slots 1-6: glowing energy orbs with the slot number ----
cols=[(80,190,255),(255,210,60),(190,90,255),(255,120,60),(90,230,120),(255,90,160)]
for n,c in enumerate(cols,1):
    im,d=canvas()
    glow=Image.new("RGBA",(S,S),(0,0,0,0)); gd=ImageDraw.Draw(glow); gd.ellipse((40,40,472,472),fill=c+(140,))
    glow=glow.filter(ImageFilter.GaussianBlur(30)); im=Image.alpha_composite(im,glow); d=ImageDraw.Draw(im)
    radial(d,(80,80,432,432),(255,255,255,255),c+(255,))
    d.ellipse((80,80,432,432),outline=tuple(int(v*0.6) for v in c)+(255,),width=12)
    f=font(230); txt=str(n); bb=d.textbbox((0,0),txt,font=f)
    tx=(S-(bb[2]-bb[0]))/2-bb[0]; ty=(S-(bb[3]-bb[1]))/2-bb[1]
    d.text((tx+6,ty+6),txt,font=f,fill=(0,0,0,120)); d.text((tx,ty),txt,font=f,fill=(30,30,50,255))
    save(im,f"dbz_move_slot_{n}")

# ---- Hair piece icon: spiky golden tuft ----
im,d=canvas()
pts=[(60,420),(110,180),(170,330),(220,90),(280,320),(330,130),(380,330),(440,200),(460,420)]
d.polygon(pts,fill=(255,214,60,255),outline=(170,120,20,255))
d.polygon([(120,400),(180,300),(240,400)],fill=(255,240,150,255))
d.line(pts,fill=(170,120,20,255),width=10,joint="curve")
save(shadow(im),"dbz_hair")

# ---- Senzu Bean: glossy green bean ----
im,d=canvas()
bean=Image.new("RGBA",(S,S),(0,0,0,0)); bd=ImageDraw.Draw(bean)
radial(bd,(150,90,362,422),(190,240,120,255),(70,140,40,255))
bd.ellipse((150,90,362,422),outline=(40,90,25,255),width=10)
bd.arc((200,120,300,400),100,260,fill=(90,160,50,255),width=10)
bd.ellipse((200,140,250,210),fill=(255,255,255,150))
bean=bean.rotate(-25,resample=Image.BICUBIC)
save(shadow(bean),"dbz_senzu_bean")

# ---- Capsules: rounded pill with a button and band ----
for name,band in [("dbz_capsule_house",(210,60,60)),("dbz_capsule_chamber",(60,140,220))]:
    pill=Image.new("RGBA",(S,S),(0,0,0,0)); pd=ImageDraw.Draw(pill)
    pd.rounded_rectangle((70,190,442,322),radius=66,fill=(235,235,240,255),outline=(110,110,125,255),width=10)
    pd.rectangle((236,192,276,320),fill=band+(255,))
    pd.ellipse((340,220,400,280),fill=(180,180,190,255),outline=(90,90,100,255),width=8)
    pd.rounded_rectangle((100,205,220,232),radius=12,fill=(255,255,255,200))
    f=font(46); pd.text((120,248),"H" if "house" in name else "T",font=f,fill=band+(255,))
    pill=pill.rotate(30,resample=Image.BICUBIC)
    save(shadow(pill),name)
print("icons done")
