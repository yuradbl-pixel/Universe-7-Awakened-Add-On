import sys; sys.path.insert(0,"/home/claude/tools")
import mcstructure, preview
from PIL import Image, ImageDraw
C={"stone":(120,120,120),"stone_bricks":(128,128,128),"mossy_stone_bricks":(110,125,100),"smooth_stone":(165,165,165),"light_gray_concrete":(140,140,135),
"green_concrete":(80,110,40),"sea_lantern":(205,235,230),"glowstone":(245,215,140),"campfire":(230,120,40),"soul_campfire":(80,200,220),
"stone_brick_stairs":(128,128,128),"mossy_stone_brick_stairs":(110,125,100),"red_sandstone":(185,95,40),"red_sandstone_stairs":(185,95,40),
"white_concrete":(235,235,235),"purple_concrete":(110,40,160),"light_blue_stained_glass":(150,200,255),"iron_block":(210,210,210),"quartz_stairs":(235,230,225),
"purpur_block":(170,120,170),"gold_block":(245,205,60),"purpur_pillar":(175,130,175),"purpur_stairs":(170,120,170),"moss_carpet":(90,120,50),
"deepslate_bricks":(70,70,75),"iron_bars":(150,150,150),"pink_concrete":(220,110,150),"pink_stained_glass":(240,160,200),"magenta_concrete":(170,50,160),
"grass_block":(95,160,60),"dirt":(130,90,60),"oak_fence":(160,125,75),"grass_path":(150,130,80),"poppy":(200,30,30),"dandelion":(240,220,40),"cornflower":(80,100,220),"azure_bluet":(220,220,240),
"oak_planks":(170,135,80),"oak_log":(110,85,50),"spruce_planks":(115,85,55),"glass_pane":(170,210,235),"oak_stairs":(170,135,80),"cobblestone":(115,115,115),
"furnace":(100,100,100),"crafting_table":(150,100,60),"bookshelf":(140,100,60),"red_carpet":(170,40,40),"lantern":(80,70,60),
"light_blue_concrete":(60,150,210),"light_blue_carpet":(90,170,220),"packed_mud":(140,105,80),"spruce_fence":(100,75,50),"gravel":(130,125,120),
"dark_oak_log":(65,45,30),"dark_oak_planks":(70,50,30),"red_concrete":(160,40,40),"lime_carpet":(120,190,40),"hay_block":(200,170,50),"target":(230,220,200),"anvil":(70,70,70),"red_nether_brick":(110,25,25),"red_concrete":(160,40,40),"black_concrete":(25,25,30),"packed_ice":(150,180,230),"blue_ice":(110,160,235),"snow":(245,250,250),"quartz_block":(235,230,225),"quartz_pillar":(230,225,220),"chiseled_quartz_block":(225,220,215),"lime_concrete":(110,180,40)}
def render(name,yaw=30,scale=4.2,cy=8):
    d=mcstructure.read(f"/home/claude/dbz/DBZ_BP/structures/dbz/{name}.mcstructure")
    sx,sy,sz=d["size"]; idx=d["structure"]["block_indices"][0]; pal=[p["name"].split(":")[1] for p in d["structure"]["palette"]["default"]["block_palette"]]
    groups={}; i=0; cx,cz=sx//2,sz//2
    for x in range(sx):
        for y in range(sy):
            for z in range(sz):
                b=pal[idx[i]]; i+=1
                if b=="air" or y<3 or b.startswith("core") or b=="home_core": continue
                groups.setdefault(C.get(b,(255,0,255)),[]).append({"origin":[(x-cx)*2,(y-2)*2,(z-cz)*2],"size":[2,2,2]})
    im=preview.render(list((v,k) for k,v in groups.items()),yaw,size=380,scale=scale,cy=cy,pitch=35)
    ImageDraw.Draw(im).text((8,8),name,fill=(255,255,255)); return im
if __name__=="__main__":
    names=sys.argv[1].split(","); out=Image.new("RGB",(380*len(names),380))
    for i,n in enumerate(names): out.paste(render(n,scale=float(sys.argv[3]) if len(sys.argv)>3 else 4.2),(i*380,0))
    out.save(sys.argv[2])
