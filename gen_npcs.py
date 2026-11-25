import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hairlib
from PIL import Image, ImageDraw
BP="/home/claude/dbz/DBZ_BP"; RP="/home/claude/dbz/DBZ_RP"
for d in [f"{BP}/entities/npcs",f"{BP}/spawn_rules",f"{RP}/entity/npcs",f"{RP}/textures/entity/npc",f"{RP}/render_controllers"]:
    os.makedirs(d,exist_ok=True)
def w(p,o): open(p,"w").write(json.dumps(o,indent=2)+"\n")

SKIN=(236,190,150); BLACK=(25,25,30); GOLD=(255,214,60); BLUEH=(70,190,255)
# id: hp, melee, speed, role, skin per form, hair per form (None=bald), body, pants, belt, wrist, boots, egg colors, spawn
NPCS={
 "master_roshi":dict(hp=100,dmg=0,spd=0.22,role="trainer",skin=[SKIN],hair=[None],body=(240,130,60),pants=(210,180,120),belt=(120,60,140),wrist=SKIN,boots=(120,80,40),beard=True,egg=("#F08A3C","#D2B478"),spawn="beach"),
 "king_kai":dict(hp=100,dmg=0,spd=0.2,role="trainer",skin=[(60,90,200)],hair=[None],body=(40,40,45),pants=(40,40,45),belt=(200,200,200),wrist=(60,90,200),boots=(30,30,30),egg=("#3C5AC8","#28282D")),
 "whis":dict(hp=100,dmg=0,spd=0.25,role="trainer",skin=[(150,190,230)],hair=[(235,235,245)],body=(120,30,60),pants=(120,30,60),belt=(40,40,40),wrist=(150,190,230),boots=(40,40,40),egg=("#96BEE6","#781E3C")),
 "goku":dict(hp=200,dmg=8,spd=0.32,role="ally",skin=[SKIN],hair=[BLACK,GOLD,BLUEH],body=(240,120,30),pants=(240,120,30),belt=(40,60,160),wrist=(40,60,160),boots=(40,60,160),egg=("#F0781E","#283CA0")),
 "vegeta":dict(hp=200,dmg=8,spd=0.32,role="ally",skin=[SKIN],hair=[BLACK,GOLD,BLUEH],body=(40,60,150),pants=(40,60,150),belt=(240,240,240),wrist=(240,240,240),boots=(240,240,240),egg=("#283C96","#F0F0F0")),
 "gohan":dict(hp=170,dmg=7,spd=0.31,role="ally",skin=[SKIN],hair=[BLACK,GOLD,(225,230,240)],body=(90,50,140),pants=(90,50,140),belt=(200,40,40),wrist=(200,40,40),boots=(120,80,40),egg=("#5A328C","#C82828")),
 "piccolo":dict(hp=180,dmg=7,spd=0.31,role="ally",skin=[(90,170,80),(240,140,50)],hair=[None,None],body=(70,40,110),pants=(70,40,110),belt=(120,190,230),wrist=(200,60,60),boots=(120,80,40),egg=("#5AAA50","#46286E"),spawn="mountain"),
 "krillin":dict(hp=120,dmg=5,spd=0.3,role="ally",skin=[SKIN],hair=[None],body=(240,120,30),pants=(240,120,30),belt=(40,60,160),wrist=(40,60,160),boots=(40,60,160),egg=("#F0781E","#ECBE96"),spawn="plains"),
 "trunks":dict(hp=160,dmg=7,spd=0.32,role="ally",skin=[SKIN],hair=[(190,160,220),GOLD],body=(60,70,90),pants=(110,110,120),belt=(200,170,60),wrist=(60,70,90),boots=(230,200,60),egg=("#3C465A","#BEA0DC")),
 "goten":dict(hp=130,dmg=5,spd=0.3,role="ally",skin=[SKIN],hair=[BLACK,GOLD],body=(240,120,30),pants=(40,60,160),belt=(40,60,160),wrist=(40,60,160),boots=(120,80,40),egg=("#F0781E","#191919")),
 "android_17":dict(hp=190,dmg=7,spd=0.32,role="ally",skin=[SKIN],hair=[BLACK],body=(40,90,60),pants=(60,60,70),belt=(230,120,40),wrist=(30,30,30),boots=(70,50,30),egg=("#285A3C","#191919"),spawn="forest"),
 "android_18":dict(hp=170,dmg=7,spd=0.32,role="ally",skin=[SKIN],hair=[(240,220,140)],body=(60,90,160),pants=(70,100,170),belt=(30,30,30),wrist=(30,30,30),boots=(30,30,30),egg=("#3C5AA0","#F0DC8C")),
}
# ---- Bosses (Phase 6a) ----
PINKS=(250,160,200)
NPCS.update({
 "frieza":dict(hp=400,dmg=10,spd=0.32,role="boss",hostile=True,skin=[(240,240,250),(245,205,60),(45,35,60)],hair=[None],crown=[(140,60,170),(140,60,170),(120,40,150)],body=None,pants=None,belt=(140,60,170),wrist=None,boots=None,egg=("#F0F0FA","#8C3CAA"),spawn="mesa",loot=[("minecraft:diamond",2,4),("minecraft:gold_ingot",4,8)]),
 "cell":dict(hp=450,dmg=11,spd=0.32,role="boss",hostile=True,skin=[(90,170,90),(110,200,110)],hair=[None],crown=[(30,30,30)],body=(40,40,40),pants=(90,170,90),belt=(30,30,30),wrist=(30,30,30),boots=(240,240,240),spots=True,egg=("#5AAA5A","#1E1E1E"),spawn="swamp",loot=[("minecraft:emerald",3,6),("minecraft:golden_apple",1,2)]),
 "majin_buu":dict(hp=500,dmg=10,spd=0.3,role="boss",hostile=True,skin=[PINKS,PINKS,PINKS],hair=[None],crown=[PINKS],body=(110,40,140),pants=(240,240,240),belt=(230,200,40),wrist=(230,200,40),boots=(230,200,40),egg=("#FAA0C8","#6E288C"),loot=[("minecraft:cake",1,1),("minecraft:cookie",8,16),("minecraft:diamond",2,4)]),
 "broly":dict(hp=600,dmg=14,spd=0.33,role="boss",hostile=True,skin=[(225,175,130)],hair=[BLACK,GOLD,(185,240,90)],body=(225,175,130),pants=(240,240,240),belt=(200,40,40),wrist=(230,190,50),boots=(230,190,50),egg=("#E1AF82","#B9F05A"),spawn="frozen",loot=[("minecraft:diamond",3,6),("minecraft:iron_block",1,3)]),
 "beerus":dict(hp=700,dmg=16,spd=0.33,role="boss",hostile=False,skin=[(120,80,160)],hair=[None],crown=[(120,80,160)],body=(30,30,30),pants=(240,240,240),belt=(220,180,50),wrist=(220,180,50),boots=(220,180,50),egg=("#7850A0","#DCB432"),loot=[("minecraft:nether_star",1,1),("minecraft:enchanted_golden_apple",1,1)]),
 "jiren":dict(hp=650,dmg=15,spd=0.33,role="boss",hostile=True,skin=[(200,100,100)],hair=[None],crown=[(60,40,50)],body=(180,40,40),pants=(30,30,30),belt=(240,240,240),wrist=(30,30,30),boots=(30,30,30),egg=("#B42828","#1E1E1E"),loot=[("minecraft:diamond",4,8),("minecraft:netherite_scrap",1,2)]),
 "hit":dict(hp=400,dmg=12,spd=0.34,role="boss",hostile=True,skin=[(120,110,180)],hair=[None],crown=[(60,50,90)],body=(110,60,140),pants=(80,40,110),belt=(40,40,40),wrist=(40,40,40),boots=(40,40,40),egg=("#786EB4","#6E3C8C"),loot=[("minecraft:emerald",4,8),("minecraft:ender_pearl",4,8)]),
 "goku_black":dict(hp=450,dmg=12,spd=0.33,role="boss",hostile=True,skin=[SKIN],hair=[BLACK,(240,120,170)],body=(60,60,70),pants=(60,60,70),belt=(200,40,40),wrist=(60,60,70),boots=(200,40,40),egg=("#3C3C46","#F078AA"),loot=[("minecraft:diamond",3,5),("minecraft:amethyst_shard",6,12)]),
 "zamasu":dict(hp=400,dmg=11,spd=0.32,role="boss",hostile=True,skin=[(100,170,110),(150,180,120)],hair=[(240,240,240)],body=(60,140,140),pants=(240,240,240),belt=(200,170,60),wrist=(200,170,60),boots=(200,170,60),egg=("#64AA6E","#3C8C8C"),loot=[("minecraft:totem_of_undying",1,1),("minecraft:diamond",2,4)]),
})
# ---- Phase 6b ----
NPCS.update({
 "toppo":dict(hp=550,dmg=14,spd=0.3,role="boss",hostile=True,skin=[(150,110,90)],hair=[(240,240,240)],body=(190,40,40),pants=(30,30,30),belt=(240,240,240),wrist=(240,240,240),boots=(240,240,240),egg=("#BE2828","#1E1E1E"),loot=[("minecraft:diamond",3,6),("minecraft:gold_block",1,2)]),
 "dyspo":dict(hp=400,dmg=11,spd=0.38,role="boss",hostile=True,skin=[(70,50,90)],hair=[None],crown=[(240,240,240)],body=(190,40,40),pants=(30,30,30),belt=(240,240,240),wrist=(240,240,240),boots=(240,240,240),egg=("#46325A","#BE2828"),loot=[("minecraft:emerald",4,8),("minecraft:rabbit_foot",1,3)]),
 "kefla":dict(hp=520,dmg=13,spd=0.34,role="boss",hostile=True,skin=[SKIN],hair=[(30,30,30),(185,240,90),GOLD],body=(230,60,90),pants=(40,40,40),belt=(230,200,60),wrist=(230,200,60),boots=(40,40,40),egg=("#E63C5A","#B9F05A"),loot=[("minecraft:diamond",3,6),("minecraft:potion",1,2)]),
 "moro":dict(hp=600,dmg=13,spd=0.3,role="boss",hostile=True,skin=[(130,150,130)],hair=[None],crown=[(80,90,80)],body=(110,40,40),pants=(110,110,110),belt=(60,60,60),wrist=(130,150,130),boots=(60,60,60),egg=("#829682","#6E2828"),loot=[("minecraft:lapis_block",2,4),("minecraft:experience_bottle",8,16)]),
 "granolah":dict(hp=520,dmg=12,spd=0.33,role="boss",hostile=True,skin=[(200,80,90)],hair=[(240,240,240)],body=(60,120,70),pants=(40,40,50),belt=(150,110,60),wrist=(60,120,70),boots=(40,40,50),egg=("#C8505A","#3C7846"),loot=[("minecraft:diamond",3,6),("minecraft:spectral_arrow",16,32)]),
 "gas":dict(hp=700,dmg=16,spd=0.33,role="boss",hostile=True,skin=[(160,70,110),(170,60,100),(120,50,90)],hair=[None],crown=[(50,30,40)],body=(50,30,40),pants=(50,30,40),belt=(90,200,90),wrist=(90,200,90),boots=(30,20,30),egg=("#A0466E","#5AC85A"),loot=[("minecraft:netherite_scrap",2,4),("minecraft:diamond",4,8)]),
 "cabba":dict(hp=170,dmg=7,spd=0.32,role="ally",skin=[SKIN],hair=[BLACK,GOLD],body=(40,70,160),pants=(40,70,160),belt=(200,170,60),wrist=(240,240,240),boots=(240,240,240),egg=("#2846A0","#C8AA3C")),
 "caulifla":dict(hp=220,dmg=9,spd=0.33,role="ally",skin=[SKIN],hair=[BLACK,GOLD,GOLD],body=(220,40,60),pants=(110,60,140),belt=(40,40,40),wrist=(220,40,60),boots=(40,40,40),egg=("#DC283C","#6E3C8C")),
 "gogeta":dict(hp=400,dmg=14,spd=0.34,role="ally",skin=[SKIN],hair=[BLACK,BLUEH],body=(30,30,30),pants=(240,240,240),belt=(40,60,160),wrist=(240,140,40),boots=(240,240,240),egg=("#1E1E1E","#F0F0F0")),
 "vegito":dict(hp=400,dmg=14,spd=0.34,role="ally",skin=[SKIN],hair=[BLACK,BLUEH],body=(240,120,30),pants=(40,60,160),belt=(240,200,60),wrist=(240,240,240),boots=(240,240,240),egg=("#F0781E","#283CA0")),
})
# ---- Phase 6c: Heroes ----
NPCS.update({
 "xeno_goku":dict(hp=320,dmg=12,spd=0.34,role="ally",skin=[SKIN],hair=[BLACK,GOLD,BLACK],body=(50,50,70),pants=(50,50,70),belt=(200,40,40),wrist=(200,40,40),boots=(200,40,40),egg=("#323246","#C82828")),
 "xeno_vegeta":dict(hp=320,dmg=12,spd=0.34,role="ally",skin=[SKIN],hair=[BLACK,GOLD,BLACK],body=(90,60,40),pants=(40,60,150),belt=(240,240,240),wrist=(240,240,240),boots=(240,240,240),egg=("#5A3C28","#283C96")),
 "ssj4_gogeta":dict(hp=600,dmg=18,spd=0.35,role="ally",skin=[SKIN],hair=[(200,40,60)],body=(180,40,40),pants=(240,240,240),belt=(40,60,160),wrist=(240,140,40),boots=(240,240,240),egg=("#B42828","#C8283C")),
 "ssj4_vegito":dict(hp=600,dmg=18,spd=0.35,role="ally",skin=[SKIN],hair=[(30,30,30)],body=(180,40,40),pants=(240,140,40),belt=(240,200,60),wrist=(240,240,240),boots=(240,240,240),egg=("#B42828","#F08C28")),
 "cumber":dict(hp=900,dmg=18,spd=0.33,role="boss",hostile=True,skin=[(170,150,140)],hair=[BLACK,GOLD,(90,20,30)],body=(90,20,30),pants=(40,30,30),belt=(30,30,30),wrist=(90,20,30),boots=(30,30,30),egg=("#5A141E","#AA968C"),loot=[("minecraft:diamond",5,10),("minecraft:wither_skeleton_skull",1,1)]),
 "fu":dict(hp=600,dmg=14,spd=0.36,role="boss",hostile=True,skin=[(190,170,220)],hair=[(150,90,200)],body=(230,230,240),pants=(60,60,70),belt=(150,90,200),wrist=(60,60,70),boots=(60,60,70),egg=("#BEAADC","#965AC8"),loot=[("minecraft:emerald",6,12),("minecraft:ender_eye",2,4)]),
 "hearts":dict(hp=1000,dmg=20,spd=0.34,role="boss",hostile=True,skin=[SKIN],hair=[(230,80,120),GOLD],body=(40,40,40),pants=(30,30,30),belt=(230,190,60),wrist=(230,190,60),boots=(30,30,30),egg=("#282828","#E65078"),loot=[("minecraft:netherite_ingot",1,2),("minecraft:diamond",6,12)]),
 "oren":dict(hp=600,dmg=16,spd=0.3,role="boss",hostile=True,skin=[(200,120,80)],hair=[None],crown=[(60,40,30)],body=(60,40,30),pants=(40,30,30),belt=(200,120,80),wrist=(60,40,30),boots=(40,30,30),egg=("#C87850","#3C2818"),loot=[("minecraft:iron_block",2,4),("minecraft:diamond",2,4)]),
 "kamin":dict(hp=500,dmg=13,spd=0.35,role="boss",hostile=True,skin=[SKIN],hair=[(240,240,250)],body=(220,60,100),pants=(40,40,60),belt=(240,240,250),wrist=(220,60,100),boots=(40,40,60),egg=("#DC3C64","#F0F0FA"),loot=[("minecraft:emerald",4,8),("minecraft:diamond",2,4)]),
})
# ---- Hair style per NPC (generic styles from hairlib). Bald NPCs get none. ----
HAIR_STYLE={
 "goku":"spiky","vegeta":"slick","gohan":"spiky","trunks":"flowing","goten":"spiky",
 "android_17":"flowing","android_18":"flowing","whis":"short",
 "broly":"long","beerus":None,"jiren":None,"goku_black":"spiky","zamasu":"short",
 "toppo":"short","kefla":"spiky","granolah":"short","cabba":"slick","caulifla":"spiky",
 "gogeta":"spiky","vegito":"slick","xeno_goku":"long","xeno_vegeta":"slick",
 "ssj4_gogeta":"long","ssj4_vegito":"long","cumber":"long","fu":"flowing","hearts":"flowing","kamin":"flowing",
}
# ---- Tails: style + color ("skin" = matches the current form's skin) ----
TAILS={
 "xeno_goku":("saiyan",(120,70,40)), "xeno_vegeta":("saiyan",(120,70,40)),
 "ssj4_gogeta":("saiyan",(150,60,40)), "ssj4_vegito":("saiyan",(150,60,40)), "cumber":("saiyan",(90,60,40)),
 "frieza":("lizard","skin"), "cell":("lizard","skin"), "beerus":("cat","skin"),
}
def geo_id(nid):
  h=HAIR_STYLE.get(nid) or "bald"; t=TAILS[nid][0] if nid in TAILS else "none"
  return f"geometry.dbz.npc_{h}_{t}"
NAMES={"master_roshi":"Master Roshi","king_kai":"King Kai","whis":"Whis","goku":"Goku","vegeta":"Vegeta","gohan":"Gohan","piccolo":"Piccolo","krillin":"Krillin","trunks":"Trunks","goten":"Goten","android_17":"Android 17","android_18":"Android 18",
 "frieza":"Frieza","cell":"Cell","majin_buu":"Majin Buu","broly":"Broly","beerus":"Beerus","jiren":"Jiren","hit":"Hit","goku_black":"Goku Black","zamasu":"Zamasu",
 "toppo":"Toppo","dyspo":"Dyspo","kefla":"Kefla","moro":"Moro","granolah":"Granolah","gas":"Gas","cabba":"Cabba","caulifla":"Caulifla","gogeta":"Gogeta","vegito":"Vegito",
 "xeno_goku":"Xeno Goku","xeno_vegeta":"Xeno Vegeta","ssj4_gogeta":"SSJ4 Gogeta","ssj4_vegito":"SSJ4 Vegito","cumber":"Cumber","fu":"Fu","hearts":"Hearts","oren":"Oren","kamin":"Kamin"}

def paint(spec, form):
    skin=spec["skin"][min(form,len(spec["skin"])-1)]; hair=spec["hair"][min(form,len(spec["hair"])-1)]
    spec=dict(spec)
    for k in ("body","pants","wrist","boots"):
        if spec.get(k) is None: spec[k]=skin
    crown=spec.get("crown")
    crown=crown[min(form,len(crown)-1)] if crown else None
    im=Image.new("RGBA",(64,64),(0,0,0,0)); d=ImageDraw.Draw(im)
    R=lambda x0,y0,x1,y1,c: d.rectangle((x0,y0,x1-1,y1-1),fill=c+(255,))
    # head (uv 0,0): 32x16 block
    R(0,0,32,16,skin)
    if hair:
        R(8,0,16,8,hair)                       # top
        for x0 in (0,8,16,24): R(x0,8,x0+8,10,hair)  # upper rows of each side
        R(24,8,32,15,hair)                     # back of head
    if crown:
        R(8,0,16,8,crown); R(8,8,16,9,crown); R(24,8,32,10,crown)
    if spec.get("spots"):
        for (x,y) in ((2,10),(18,11),(26,12),(22,20),(34,24),(4,20),(44,22),(20,52)):
            R(x,y,x+2,y+1,(30,60,30))
    # face (front 8..16, 8..16)
    R(9,12,11,13,(255,255,255)); R(13,12,15,13,(255,255,255))
    R(10,12,11,13,(20,20,20)); R(13,12,14,13,(20,20,20))
    R(11,14,13,15,tuple(int(c*0.75) for c in skin))
    if spec.get("beard"): R(9,14,15,16,(240,240,240)); R(9,9,15,10,(240,240,240))
    # body uv 16,16 (region 16..40, 16..32)
    R(16,16,40,32,spec["body"]); R(16,28,40,30,spec["belt"])
    R(20,20,28,23,tuple(min(255,int(c*1.15)+10) for c in spec["body"]))  # chest highlight
    # arms: right uv 40,16 (40..56,16..32); left uv 32,48 (32..48,48..64)
    for (x0,y0) in ((40,16),(32,48)):
        R(x0,y0,x0+16,y0+16,skin); R(x0,y0+4,x0+16,y0+7,spec["body"]); R(x0,y0+12,x0+16,y0+15,spec["wrist"])
        R(x0+4,y0,x0+8,y0+4,spec["body"])  # shoulder top
    # legs: right uv 0,16 (0..16,16..32); left uv 16,48 (16..32,48..64)
    for (x0,y0) in ((0,16),(16,48)):
        R(x0,y0,x0+16,y0+16,spec["pants"]); R(x0,y0+12,x0+16,y0+16,spec["boots"]); R(x0+8,y0,x0+12,y0+4,spec["boots"])
    # hair pieces: spikes uv 0,32 (8x8) and cap uv 16,32 (36x11)
    if hair:
        # Spike/panel region (0,32)-(16,48) and cap/back-panel region (16,32)-(52,43).
        lt=tuple(min(255,int(c*1.15)+20) for c in hair); dk=tuple(int(c*0.72) for c in hair)
        R(0,32,16,48,hair); R(16,32,52,43,hair)
        for y in range(32,48):  # vertical gradient: light near the roots of spikes
            t=(y-32)/15
            col=tuple(int(lt[k]*(1-t)+dk[k]*t) for k in range(3))
            d.line((0,y,15,y),fill=col+(255,))
        for x in range(16,52,3): d.line((x,32,x,42),fill=dk+(255,))
        d.line((16,32,51,32),fill=lt+(255,))
    t=TAILS.get(spec.get("_id"))
    if t:
        tc=skin if t[1]=="skin" else t[1]
        R(48,48,64,56,tc)
        dk=tuple(int(c*0.8) for c in tc)
        for x in range(48,64,3): d.line((x,48,x,55),fill=dk+(255,))
    return im

forms_count={k:max(len(v["hair"]),len(v["skin"]),len(v.get("crown") or [0])) for k,v in NPCS.items()}
os.makedirs(f"{BP}/loot_tables/entities/dbz",exist_ok=True)
lang=["pack.name=Dragon Ball Add-On (Resources)","pack.description=Textures, particles and sounds for the Dragon Ball add-on.","entity.dbz:ki_blast.name=Ki Blast"]
for nid,spec in NPCS.items():
    spec["_id"]=nid
    role=spec["role"]; trainer=role=="trainer"
    fam=["dbz_npc",f"dbz_{role}","mob"]
    comps={
     "minecraft:type_family":{"family":fam},
     "minecraft:health":{"value":spec["hp"],"max":spec["hp"]},
     "minecraft:movement.basic":{},
     # Player-like pathing: walk, jump, swim, climb ladders/vines, open doors,
     # walk through doorways, avoid lava/fire/cactus, prefer village paths.
     "minecraft:navigation.walk":{"can_path_over_water":True,"can_swim":True,"can_walk":True,"can_breach":True,
        "can_open_doors":True,"can_pass_doors":True,"avoid_damage_blocks":True,"avoid_water":False,"can_sink":False,
        "can_path_from_air":True,"can_walk_in_lava":False},
     "minecraft:jump.static":{},
     "minecraft:can_climb":{},
     "minecraft:underwater_movement":{"value":0.15},
     "minecraft:annotation.open_door":{},
     "minecraft:behavior.open_door":{"priority":5,"close_door_after":True},
     "minecraft:preferred_path":{"max_fall_blocks":3,"jump_cost":3,"default_block_cost":1.5,"preferred_path_blocks":[
        {"cost":0,"blocks":["grass_path","dirt_path"]},
        {"cost":1,"blocks":["cobblestone","stone","stone_bricks","sandstone","planks","oak_planks","gravel","polished_andesite","polished_granite"]},
        {"cost":50,"blocks":["bed","lectern","composter","grindstone","blast_furnace","smoker","fletching_table","cartography_table","brewing_stand","smithing_table","cauldron","barrel","loom","stonecutter_block"]}]},
     "minecraft:collision_box":{"width":0.6,"height":1.9},
     "minecraft:physics":{},
     "minecraft:pushable":{"is_pushable":True,"is_pushable_by_piston":True},
     "minecraft:nameable":{"always_show":False,"allow_name_tag_renaming":True},
     "minecraft:persistent":{},
     "minecraft:knockback_resistance":{"value":0.4},
     "minecraft:damage_sensor":{"triggers":[{"cause":"all","deals_damage":"no"}] if trainer else [{"cause":"fall","deals_damage":"no"}]},
     "minecraft:interact":{"interactions":[{"on_interact":{"filters":{"all_of":[{"test":"is_family","subject":"other","value":"player"}]},"event":"dbz:talked"},"interact_text":"Talk"}]},
     "minecraft:behavior.float":{"priority":0},
     # Home = where the NPC first appeared (its house, lair or spawn egg spot).
     # It stays within this radius, so residents live at home and bosses guard lairs.
     "minecraft:home":{"restriction_radius":20 if role!="boss" else 16},
     "minecraft:conditional_bandwidth_optimization":{}
    }
    boss = role=="boss"
    if boss:
        fam=["dbz_npc","dbz_boss","mob"]+(["monster"] if spec.get("hostile") else [])
        comps["minecraft:type_family"]={"family":fam}
        comps["minecraft:boss"]={"hud_range":48,"name":NAMES[nid],"should_darken_sky":False}
        comps["minecraft:knockback_resistance"]={"value":0.9}
        comps["minecraft:fire_immune"]={}
        comps["minecraft:loot"]={"table":f"loot_tables/entities/dbz/{nid}.json"}
        if spec.get("hostile"):
            del comps["minecraft:interact"]
        pools=[{"rolls":1,"entries":[{"type":"item","name":it,"weight":1,"functions":[{"function":"set_count","count":{"min":a,"max":b}}]}]} for it,a,b in spec["loot"]]
        pools.append({"rolls":1,"conditions":[{"condition":"random_chance","chance":0.1}],"entries":[{"type":"item","name":"dbz:race_reset_token","weight":1}]})
        # Phase 7: a random Dragon Ball (35%) and Senzu Beans (50%)
        pools.append({"rolls":1,"conditions":[{"condition":"random_chance","chance":0.35}],"entries":[{"type":"item","name":f"dbz:dragon_ball_{n}","weight":1} for n in range(1,8)]})
        pools.append({"rolls":1,"conditions":[{"condition":"random_chance","chance":0.5}],"entries":[{"type":"item","name":"dbz:senzu_bean","weight":1,"functions":[{"function":"set_count","count":{"min":1,"max":3}}]}]})
        w(f"{BP}/loot_tables/entities/dbz/{nid}.json",{"pools":pools})
    if not trainer:
        comps.update({
         "minecraft:attack":{"damage":spec["dmg"]},
         "minecraft:behavior.hurt_by_target":{"priority":1},
         "minecraft:behavior.melee_attack":{"priority":2,"speed_multiplier":1.25,"track_target":True},
         "minecraft:behavior.nearest_attackable_target":{"priority":3,"must_see":True,"reselect_targets":True,"within_radius":16,
            "entity_types":[{"filters":{"test":"is_family","subject":"other","value":"monster"},"max_dist":16}]}
        })
    if boss:
        if spec.get("hostile"):
            comps["minecraft:behavior.nearest_attackable_target"]={"priority":3,"must_see":True,"reselect_targets":True,"within_radius":24,
              "entity_types":[{"filters":{"test":"is_family","subject":"other","value":"player"},"max_dist":24},
                              {"filters":{"test":"is_family","subject":"other","value":"dbz_ally"},"max_dist":16}]}
        else:
            del comps["minecraft:behavior.nearest_attackable_target"]
    # Movement + wandering live in "awake"; "asleep" stands still (sleep pose on the client).
    AI_KEYS=["minecraft:behavior.melee_attack","minecraft:behavior.nearest_attackable_target"]
    awake={"minecraft:movement":{"value":spec["spd"]},
           "minecraft:behavior.random_stroll":{"priority":6,"speed_multiplier":0.8,"xz_dist":16,"y_dist":7},
           "minecraft:behavior.look_at_player":{"priority":7,"look_distance":8,"probability":0.02},
           "minecraft:behavior.random_look_around":{"priority":8}}
    for k in AI_KEYS:
        if k in comps: awake[k]=comps.pop(k)
    asleep={"minecraft:movement":{"value":0}}
    w(f"{BP}/entities/npcs/{nid}.json",{"format_version":"1.21.50","minecraft:entity":{
      "description":{"identifier":f"dbz:{nid}","is_spawnable":True,"is_summonable":True,
        "properties":{"dbz:form":{"type":"int","range":[0,3],"default":0,"client_sync":True},
                      "dbz:sleeping":{"type":"bool","default":False,"client_sync":True}}},
      "component_groups":{"dbz:awake":awake,"dbz:asleep":asleep},
      "components":comps,
      "events":{"dbz:talked":{},
        "minecraft:entity_spawned":{"add":{"component_groups":["dbz:awake"]}},
        "dbz:sleep":{"remove":{"component_groups":["dbz:awake"]},"add":{"component_groups":["dbz:asleep"]}},
        "dbz:wake":{"remove":{"component_groups":["dbz:asleep"]},"add":{"component_groups":["dbz:awake"]}}}}})
    n=forms_count[nid]; tex={}
    for f in range(4):
        src=f if f<n else 0
        key="default" if f==0 else f"form{f}"
        tex[key]=f"textures/entity/npc/{nid}" + ("" if src==0 else f"_form{src}")
    for f in range(n):
        paint(spec,f).save(f"{RP}/textures/entity/npc/{nid}"+("" if f==0 else f"_form{f}")+".png")
    w(f"{RP}/entity/npcs/{nid}.entity.json",{"format_version":"1.10.0","minecraft:client_entity":{"description":{
      "identifier":f"dbz:{nid}","materials":{"default":"entity_alphatest"},"textures":tex,
      "geometry":{"default":geo_id(nid)},
      "animations":{"walk":"animation.dbz.npc.walk","look":"animation.dbz.npc.look","tail":"animation.dbz.npc.tail","sleep":"animation.dbz.npc.sleep"},
      "scripts":{"animate":(["walk","look","tail"] if nid in TAILS else ["walk","look"])+[{"sleep":"q.property('dbz:sleeping')"}]},
      "render_controllers":["controller.render.dbz_npc"],
      "spawn_egg":{"base_color":spec["egg"][0],"overlay_color":spec["egg"][1]}}}})
    lang.append(f"entity.dbz:{nid}.name={NAMES[nid]}")
    lang.append(f"item.spawn_egg.entity.dbz:{nid}.name={NAMES[nid]} Spawn Egg")
    if spec.get("spawn"):
        tags={"beach":{"test":"has_biome_tag","value":"beach"},
              "plains":{"test":"has_biome_tag","value":"plains"},
              "forest":{"test":"has_biome_tag","value":"forest"},
              "mountain":{"any_of":[{"test":"has_biome_tag","value":"extreme_hills"},{"test":"has_biome_tag","value":"mountains"}]},
              "mesa":{"test":"has_biome_tag","value":"mesa"},
              "swamp":{"test":"has_biome_tag","value":"swamp"},
              "frozen":{"test":"has_biome_tag","value":"frozen"}}[spec["spawn"]]
        hostile=spec.get("hostile")
        w(f"{BP}/spawn_rules/{nid}.json",{"format_version":"1.8.0","minecraft:spawn_rules":{
          "description":{"identifier":f"dbz:{nid}","population_control":"monster" if hostile else "animal"},
          "conditions":[{"minecraft:spawns_on_surface":{},"minecraft:brightness_filter":({"min":0,"max":7,"adjust_for_weather":True} if hostile else {"min":7,"max":15,"adjust_for_weather":False}),
            **({"minecraft:difficulty_filter":{"min":"normal","max":"hard"}} if hostile else {}),
            "minecraft:weight":{"default":1},"minecraft:density_limit":{"surface":1},
            "minecraft:herd":{"min_size":1,"max_size":1},"minecraft:biome_filter":tags}]}})
lang.append("entity.dbz:shenron.name=Shenron")
open(f"{RP}/texts/en_US.lang","w").write("\n".join(lang)+"\n")

# shared geometry (original humanoid rig, standard 64x64 skin layout, spiky hair bone)
spikes=[(-3,-2,-25,20),(0,-2.5,-30,0),(3,-2,-25,-20),(-2.5,1.5,22,25),(2.5,1.5,22,-25),(0,2.5,32,0),(0,0,0,0)]
hair=[{"origin":[-4.5,31.5,-4.5],"size":[9,2,9],"uv":[16,32]}]+[
  {"origin":[x-1,32.5,z-1],"size":[2,6,2],"pivot":[x,32.5,z],"rotation":[rx,0,rz],"uv":[0,32]} for x,z,rx,rz in spikes]
def base_bones(hair_style="spiky"):
  hair=hairlib.build(hair_style,[0,32],[16,32],[0,32],[16,32]) if hair_style else []
  return [
   {"name":"root","pivot":[0,0,0]},
   {"name":"body","parent":"root","pivot":[0,24,0],"cubes":[{"origin":[-4,12,-2],"size":[8,12,4],"uv":[16,16]}]},
   {"name":"head","parent":"body","pivot":[0,24,0],"cubes":[{"origin":[-4,24,-4],"size":[8,8,8],"uv":[0,0]}]},
   {"name":"hair","parent":"head","pivot":[0,24,0],"cubes":hair},
   {"name":"rightArm","parent":"body","pivot":[-5,22,0],"cubes":[{"origin":[-8,12,-2],"size":[4,12,4],"uv":[40,16]}]},
   {"name":"leftArm","parent":"body","pivot":[5,22,0],"cubes":[{"origin":[4,12,-2],"size":[4,12,4],"uv":[32,48]}]},
   {"name":"rightLeg","parent":"root","pivot":[-1.9,12,0],"cubes":[{"origin":[-3.9,0,-2],"size":[4,12,4],"uv":[0,16]}]},
   {"name":"leftLeg","parent":"root","pivot":[1.9,12,0],"cubes":[{"origin":[-0.1,0,-2],"size":[4,12,4],"uv":[16,48]}]}]

def tail_chain(style):
  # Chain of bones from the lower back. Each segment extends along +z from its
  # pivot; per-segment rotations make the curve. uv [48,48] in the 64x64 layout.
  if style=="saiyan":   seg=(2,2,5); rots=[[30,0,0],[25,25,0],[20,30,0],[15,35,0]]; infl=0.2
  # Positive X rotation lifts the far (+z) end; negative makes it droop.
  elif style=="lizard": seg=(2,2,6); rots=[[-55,0,0],[20,0,0],[15,10,0],[10,10,0],[5,10,0]]; infl=0.7
  else:                 seg=(1,1,6); rots=[[-20,0,0],[25,0,0],[25,15,0],[25,15,0],[20,10,0]]; infl=0.0
  bones=[]; parent="body"
  for i,rot in enumerate(rots):
    z0=2+i*seg[2]
    name="tail" if i==0 else f"tail{i+1}"
    thin=max(0.0, infl-0.12*i)
    bones.append({"name":name,"parent":parent,"pivot":[0,13,z0],"rotation":rot,
      "cubes":[{"origin":[-seg[0]/2,13-seg[1]/2,z0],"size":list(seg),"inflate":round(thin,2),"uv":[48,48]}]})
    parent=name
  return bones

geos=[]; seen=set()
for nid in NPCS:
  gid=geo_id(nid)
  if gid in seen: continue
  seen.add(gid)
  h=HAIR_STYLE.get(nid); t=TAILS[nid][0] if nid in TAILS else None
  bones=base_bones(h)+(tail_chain(t) if t else [])
  geos.append({"description":{"identifier":gid,"texture_width":64,"texture_height":64,
    "visible_bounds_width":4,"visible_bounds_height":4,"visible_bounds_offset":[0,1.5,0]},"bones":bones})

# =============================================================================
# Custom player-format skins (user_skins/<id>.png, <id>_form1.png, ...)
# These use a standard 64x64 player layout WITH overlay layers (hat, jacket,
# sleeves, pants) and no generated hair (the skin has its own hair).
# =============================================================================
import glob
from PIL import Image
import skinlib
# Put your skins in a "user_skins" folder next to this script (or one level up).
_here=os.path.dirname(os.path.abspath(__file__))
USER_DIR=next((d for d in [os.path.join(_here,"user_skins"),os.path.join(_here,"..","user_skins"),"/home/claude/user_skins"] if os.path.isdir(d)), os.path.join(_here,"user_skins"))

def skin_bones():
  return [
   {"name":"root","pivot":[0,0,0]},
   {"name":"body","parent":"root","pivot":[0,24,0],"cubes":[
      {"origin":[-4,12,-2],"size":[8,12,4],"uv":[16,16]},
      {"origin":[-4,12,-2],"size":[8,12,4],"uv":[16,32],"inflate":0.25}]},
   {"name":"head","parent":"body","pivot":[0,24,0],"cubes":[
      {"origin":[-4,24,-4],"size":[8,8,8],"uv":[0,0]},
      {"origin":[-4,24,-4],"size":[8,8,8],"uv":[32,0],"inflate":0.5}]},
   {"name":"rightArm","parent":"body","pivot":[-5,22,0],"cubes":[
      {"origin":[-8,12,-2],"size":[4,12,4],"uv":[40,16]},
      {"origin":[-8,12,-2],"size":[4,12,4],"uv":[40,32],"inflate":0.25}]},
   {"name":"leftArm","parent":"body","pivot":[5,22,0],"cubes":[
      {"origin":[4,12,-2],"size":[4,12,4],"uv":[32,48]},
      {"origin":[4,12,-2],"size":[4,12,4],"uv":[48,48],"inflate":0.25}]},
   {"name":"rightLeg","parent":"root","pivot":[-1.9,12,0],"cubes":[
      {"origin":[-3.9,0,-2],"size":[4,12,4],"uv":[0,16]},
      {"origin":[-3.9,0,-2],"size":[4,12,4],"uv":[0,32],"inflate":0.25}]},
   {"name":"leftLeg","parent":"root","pivot":[1.9,12,0],"cubes":[
      {"origin":[-0.1,0,-2],"size":[4,12,4],"uv":[16,48]},
      {"origin":[-0.1,0,-2],"size":[4,12,4],"uv":[0,48],"inflate":0.25}]}]

def skin_tail_chain(style):
  # Thin segments that fit the unused (56,16)-(64,20) skin area, thickened with inflate.
  rots={"saiyan":[[30,0,0],[15,12,0],[15,15,0],[12,18,0],[10,18,0],[10,18,0],[8,15,0]],
        "lizard":[[-55,0,0],[20,0,0],[12,6,0],[10,6,0],[8,6,0],[6,6,0],[5,6,0]],
        "cat":[[-20,0,0],[25,0,0],[20,10,0],[20,10,0],[18,10,0],[15,8,0],[12,8,0]]}[style]
  infl={"saiyan":0.55,"lizard":0.9,"cat":0.15}[style]
  bones=[]; parent="body"
  for i,rot in enumerate(rots):
    z0=2+i*3; name="tail" if i==0 else f"tail{i+1}"
    bones.append({"name":name,"parent":parent,"pivot":[0,13,z0],"rotation":rot,
      "cubes":[{"origin":[-0.5,12.5,z0],"size":[1,1,3],"inflate":round(max(0.1,infl-0.06*i),2),"uv":[56,16]}]})
    parent=name
  return bones

# Held props for custom-skin NPCs (painted into the unused (56,16)-(64,32) skin area).
PROPS={"whis":"staff"}

def staff_bones():
  # Held in the right hand (hand ~ y 12 at x -6). Counter-tilted so it stands
  # upright while the arm is held slightly forward (see walk_staff animation).
  cubes=[{"origin":[-6.5,1+i*7,-1.5],"size":[1,7,1],"uv":[56,16]} for i in range(5)]   # rod, y 1..36
  cubes+=[{"origin":[-7,36,-2],"size":[2,1,2],"uv":[56,16]},                            # ring under the orb
          {"origin":[-7,38.2,-2],"size":[2,2,2],"inflate":0.75,"uv":[56,24]},          # orb
          {"origin":[-7,0,-2],"size":[2,1,2],"uv":[56,16]}]                             # foot cap
  return [{"name":"staff","parent":"rightArm","pivot":[-6,12,-1],"rotation":[18,0,0],"cubes":cubes}]

def paint_staff(im):
  im=im.copy(); s=max(1,im.width//64)
  rod=(55,75,100); hi=(120,150,180); orb=(150,225,255); orb_hi=(235,250,255)
  for y in range(16*s,24*s):
    for x in range(56*s,64*s):
      im.putpixel((x,y),(hi if (x//s)%4==1 else rod)+(255,))
  for y in range(24*s,32*s):
    for x in range(56*s,64*s):
      c=orb_hi if ((x//s)-56)%4==1 and ((y//s)-24)%4==1 else orb
      im.putpixel((x,y),c+(255,))
  return im

# Missing forms: (source index, recolor kind, color). Anything else missing -> base.
SKIN_FILL={
  "broly":{1:(0,"dark",(255,214,60)),          # SSJ: black hair -> gold
           2:(0,"dark",(185,240,90))},         # Legendary: black hair -> green-gold
  "goku":{0:(1,"hair",(28,28,34))},            # base = SSJ skin with black hair
  "piccolo":{0:(1,"tone",(95,170,80))},        # base = Orange skin turned green
  "majin_buu":{0:(1,None,None)},               # base = Super skin; Kid -> base
  "cell":{0:(1,None,None)},                    # base = Super Perfect skin
  "cumber":{0:(1,"hair",(28,28,34))},          # base = SSJ skin with black hair; Evil -> base
  "frieza":{1:(0,"light",(240,200,60)),        # Golden: white body -> gold
            2:(0,"light",(55,42,70))},         # Black: white body -> near-black
  "vegeta":{0:(1,"hair",(28,28,34))},          # base = SSJ skin with black hair
  "trunks":{0:(1,"hair",(190,160,220))},       # base = SSJ skin with lavender hair
  "zamasu":{0:(1,None,None)},                  # base = provided form skin
  "xeno_goku":{1:(0,"dark",(255,214,60))},     # SSJ3 = base with gold hair; SSJ4 -> base
}
TAIL_COLORS={k:(v[1] if v[1]!="skin" else (200,170,150)) for k,v in TAILS.items()}
# Per-form tail colors for custom skins whose tail should match the body.
TAIL_FORM_COLORS={"frieza":{0:(235,235,242),1:(240,200,60),2:(55,42,70)},
                  "ssj4_vegito":{0:(150,60,40)},
                  "beerus":{0:(120,80,160)},
                  "cell":{0:(95,165,85),1:(95,165,85)},
}

skin_geos=set()
user_npcs=sorted({os.path.basename(f).split("_form")[0].replace(".png","") for f in glob.glob(os.path.join(USER_DIR,"*.png"))})
for nid in user_npcs:
  if nid not in NPCS: 
    print("skipping unknown skin:",nid); continue
  imgs={}
  for f in glob.glob(os.path.join(USER_DIR,f"{nid}*.png")):
    base=os.path.basename(f)[:-4]
    if base==nid: imgs[0]=Image.open(f).convert("RGBA")
    elif base.startswith(nid+"_form"):
      try: imgs[int(base.split("_form")[1])]=Image.open(f).convert("RGBA")
      except ValueError: pass
  # One model per NPC, so slim-armed skins are widened to classic arms.
  imgs={k:skinlib.slim_to_classic(skinlib.legacy_to_64(v)) for k,v in imgs.items()}
  for idx,(src,kind,col) in SKIN_FILL.get(nid,{}).items():
    if idx in imgs or src not in imgs: continue
    s=imgs[src]
    imgs[idx]=(skinlib.recolor_hair(s,col) if kind=="hair" else skinlib.recolor_dark_hair(s,col) if kind=="dark"
               else skinlib.recolor_light(s,col) if kind=="light"
               else skinlib.recolor_skin_tone(s,col) if kind=="tone" else s.copy())
  if 0 not in imgs: imgs[0]=imgs[min(imgs)]
  if nid in TAILS:
    imgs={k:skinlib.paint_tail(v,TAIL_FORM_COLORS.get(nid,{}).get(k,TAIL_COLORS[nid])) for k,v in imgs.items()}
  # Replace placeholder textures.
  for old in glob.glob(f"{RP}/textures/entity/npc/{nid}.png")+glob.glob(f"{RP}/textures/entity/npc/{nid}_form*.png"):
    os.remove(old)
  for k,im in imgs.items():
    im.save(f"{RP}/textures/entity/npc/{nid}"+("" if k==0 else f"_form{k}")+".png")
  prop=PROPS.get(nid)
  if prop=="staff":
    imgs={k:paint_staff(v) for k,v in imgs.items()}
    for k,im in imgs.items():
      im.save(f"{RP}/textures/entity/npc/{nid}"+("" if k==0 else f"_form{k}")+".png")
  tail=TAILS[nid][0] if nid in TAILS else "none"
  gid=f"geometry.dbz.npc_skin_{tail}"+(f"_{prop}" if prop else ""); skin_geos.add((gid,tail))
  ce_path=f"{RP}/entity/npcs/{nid}.entity.json"; ce=json.load(open(ce_path))
  desc=ce["minecraft:client_entity"]["description"]
  desc["geometry"]={"default":gid}
  if prop=="staff":
    desc["animations"]["walk"]="animation.dbz.npc.walk_staff"
  desc["textures"]={("default" if i==0 else f"form{i}"):f"textures/entity/npc/{nid}"+("" if (i==0 or i not in imgs) else f"_form{i}") for i in range(4)}
  w(ce_path,ce)
  print(f"custom skin: {nid} forms={sorted(imgs)}")

for gid,tail in sorted(skin_geos):
  geos.append({"description":{"identifier":gid,"texture_width":64,"texture_height":64,
    "visible_bounds_width":4,"visible_bounds_height":4,"visible_bounds_offset":[0,1.5,0]},
    "bones":skin_bones()+(skin_tail_chain(tail) if tail!="none" else [])+(staff_bones() if gid.endswith("_staff") else [])})
w(f"{RP}/models/entity/dbz_npc.geo.json",{"format_version":"1.12.0","minecraft:geometry":geos})
sw="math.cos(q.modified_distance_moved * 38.17) * 40 * q.modified_move_speed"
w(f"{RP}/animations/dbz_npc.animation.json",{"format_version":"1.8.0","animations":{
  "animation.dbz.npc.walk":{"loop":True,"bones":{
     "rightArm":{"rotation":[sw,0,0]},"leftArm":{"rotation":[f"-{sw}",0,0]},
     "rightLeg":{"rotation":[f"-{sw}",0,0]},"leftLeg":{"rotation":[sw,0,0]}}},
  "animation.dbz.npc.look":{"loop":True,"bones":{"head":{"rotation":["q.target_x_rotation","q.target_y_rotation",0]}}},
  # Walking while holding a staff: staff arm held a bit forward with a small swing.
  "animation.dbz.npc.walk_staff":{"loop":True,"bones":{
     "rightArm":{"rotation":["-18 + math.cos(q.modified_distance_moved * 38.17) * 10 * q.modified_move_speed",0,0]},
     "leftArm":{"rotation":[f"-{sw}",0,0]},
     "rightLeg":{"rotation":[f"-{sw}",0,0]},"leftLeg":{"rotation":[sw,0,0]}}},
  # Lying on the back: tip the whole model over and lift it so it rests on the ground.
  "animation.dbz.npc.sleep":{"loop":True,"bones":{
     "root":{"rotation":[-90,0,0],"position":[0,2,0]},
     "head":{"rotation":[0,0,0]}}},
  "animation.dbz.npc.tail":{"loop":True,"bones":{
     "tail":{"rotation":[0,"math.sin(q.life_time * 100) * 12",0]},
     "tail2":{"rotation":[0,"math.sin(q.life_time * 100 - 40) * 10",0]},
     "tail3":{"rotation":[0,"math.sin(q.life_time * 100 - 80) * 8",0]}}}}})
w(f"{RP}/render_controllers/dbz_npc.render_controllers.json",{"format_version":"1.8.0","render_controllers":{"controller.render.dbz_npc":{
  "arrays":{"textures":{"Array.skins":["Texture.default","Texture.form1","Texture.form2","Texture.form3"]}},
  "geometry":"Geometry.default","materials":[{"*":"Material.default"}],
  "textures":["Array.skins[math.clamp(q.property('dbz:form'), 0, 3)]"]}}})
print("generated", len(NPCS), "npcs")

# ---- Spawn egg icons (128x128) built from the final skins ----
import gen_eggs
gen_eggs.build_all(NPCS)
print("spawn eggs: done")
