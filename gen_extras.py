import json, math, os
from PIL import Image, ImageDraw
BP="/home/claude/dbz/DBZ_BP"; RP="/home/claude/dbz/DBZ_RP"
def w(p,o): open(p,"w").write(json.dumps(o,indent=2)+"\n")
def item(ident, icon, name, extra):
    comps={"minecraft:icon":icon,"minecraft:display_name":{"value":name}}; comps.update(extra)
    w(f"{BP}/items/{ident}.json",{"format_version":"1.21.50","minecraft:item":{"description":{"identifier":f"dbz:{ident}","menu_category":{"category":"items"}},"components":comps}})
tex={}
# ---- Dragon Balls ----
for n in range(1,8):
    item(f"dragon_ball_{n}", f"dbz_dragon_ball_{n}", f"{n}-Star Dragon Ball", {"minecraft:max_stack_size":1,"minecraft:glint":False,"minecraft:rarity":"epic"})
    im=Image.new("RGBA",(16,16),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.ellipse((1,1,14,14),fill=(255,150,30,255),outline=(200,90,10,255)); d.ellipse((3,3,6,6),fill=(255,230,170,200))
    pts=[(5,8),(10,8),(7,5),(7,11),(9,5),(5,11),(10,11)][:n]
    for (x,y) in pts: d.rectangle((x,y,x,y),fill=(210,20,20,255))
    im.save(f"{RP}/textures/items/dbz_dragon_ball_{n}.png"); tex[f"dbz_dragon_ball_{n}"]=f"textures/items/dbz_dragon_ball_{n}"
# ---- Senzu ----
item("senzu_bean","dbz_senzu_bean","Senzu Bean",{"minecraft:max_stack_size":16,
  "minecraft:food":{"nutrition":6,"saturation_modifier":1.2,"can_always_eat":True},
  "minecraft:use_modifiers":{"use_duration":0.8,"movement_modifier":0.35},
  "minecraft:use_animation":"eat",
  "minecraft:cooldown":{"category":"dbz_senzu","duration":5}})
im=Image.new("RGBA",(16,16),(0,0,0,0)); d=ImageDraw.Draw(im)
d.ellipse((4,3,11,12),fill=(120,200,70,255),outline=(60,130,40,255)); d.line((7,4,7,11),fill=(90,160,50,255)); d.point((6,5),fill=(220,255,190,255))
im.save(f"{RP}/textures/items/dbz_senzu_bean.png"); tex["dbz_senzu_bean"]="textures/items/dbz_senzu_bean"
# ---- Capsules ----
for ident,name,col in [("capsule_house","Capsule: House",(230,230,235)),("capsule_chamber","Capsule: Time Chamber",(245,245,250))]:
    item(ident,f"dbz_{ident}",name,{"minecraft:max_stack_size":1})
    im=Image.new("RGBA",(16,16),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle((3,5,12,10),radius=2,fill=col+(255,),outline=(120,120,130,255))
    d.rectangle((7,5,8,10),fill=(200,60,60,255) if "house" in ident else (60,140,220,255))
    d.point((4,6),fill=(255,255,255,255))
    im.save(f"{RP}/textures/items/dbz_{ident}.png"); tex[f"dbz_{ident}"]=f"textures/items/dbz_{ident}"
it=json.load(open(f"{RP}/textures/item_texture.json"))
for k,v in tex.items(): it["texture_data"][k]={"textures":v}
w(f"{RP}/textures/item_texture.json",it)
# ---- Recipes ----
w(f"{BP}/recipes/senzu_bean.json",{"format_version":"1.20.10","minecraft:recipe_shapeless":{"description":{"identifier":"dbz:senzu_bean"},"tags":["crafting_table"],
  "ingredients":[{"item":"minecraft:wheat_seeds"},{"item":"minecraft:golden_carrot"},{"item":"minecraft:glow_berries"}],"unlock":[{"item":"minecraft:golden_carrot"}],
  "result":{"item":"dbz:senzu_bean","count":2}}})
w(f"{BP}/recipes/capsule_house.json",{"format_version":"1.20.10","minecraft:recipe_shaped":{"description":{"identifier":"dbz:capsule_house"},"tags":["crafting_table"],
  "pattern":[" I ","ICI"," I "],"key":{"I":{"item":"minecraft:iron_ingot"},"C":{"item":"minecraft:chest"}},"unlock":[{"item":"minecraft:iron_ingot"}],
  "result":{"item":"dbz:capsule_house","count":1}}})
w(f"{BP}/recipes/capsule_chamber.json",{"format_version":"1.20.10","minecraft:recipe_shaped":{"description":{"identifier":"dbz:capsule_chamber"},"tags":["crafting_table"],
  "pattern":["QDQ","DCD","QDQ"],"key":{"Q":{"item":"minecraft:quartz_block"},"D":{"item":"minecraft:diamond"},"C":{"item":"minecraft:clock"}},"unlock":[{"item":"minecraft:clock"}],
  "result":{"item":"dbz:capsule_chamber","count":1}}})
# ---- Shenron (behavior) ----
w(f"{BP}/entities/shenron.json",{"format_version":"1.21.50","minecraft:entity":{
  "description":{"identifier":"dbz:shenron","is_spawnable":False,"is_summonable":True},
  "component_groups":{"dbz:despawn":{"minecraft:instant_despawn":{}}},
  "components":{
    "minecraft:type_family":{"family":["dbz_shenron","inanimate"]},
    "minecraft:health":{"value":1000,"max":1000},
    "minecraft:damage_sensor":{"triggers":[{"cause":"all","deals_damage":"no"}]},
    "minecraft:collision_box":{"width":3,"height":12},
    "minecraft:physics":{"has_gravity":False,"has_collision":True},
    "minecraft:pushable":{"is_pushable":False,"is_pushable_by_piston":False},
    "minecraft:knockback_resistance":{"value":1},
    "minecraft:fire_immune":{},
    "minecraft:nameable":{"always_show":True},
    "minecraft:interact":{"interactions":[{"on_interact":{"filters":{"test":"is_family","subject":"other","value":"player"},"event":"dbz:wish"},"interact_text":"Make a Wish"}]},
    "minecraft:timer":{"looping":False,"time":180,"time_down_event":{"event":"dbz:despawn"}}
  },
  "events":{"dbz:wish":{},"dbz:despawn":{"add":{"component_groups":["dbz:despawn"]}}}}})
# ---- Shenron (resources): original coiled-serpent placeholder ----
bones=[{"name":"root","pivot":[0,0,0]}]
cubes=[]
for i in range(16):
    a=i*0.55; r=max(10,52-i*3); y=i*11
    x=round(r*math.cos(a)); z=round(r*math.sin(a))
    cubes.append({"origin":[x-10,y,z-10],"size":[20,20,20],"uv":[0,0]})
bones.append({"name":"body","parent":"root","pivot":[0,0,0],"cubes":cubes})
hy=16*11+10
bones.append({"name":"head","parent":"body","pivot":[0,hy,0],"cubes":[
  {"origin":[-14,hy,-20],"size":[28,22,40],"uv":[0,48]},
  {"origin":[-12,hy+22,8],"size":[4,22,4],"pivot":[-10,hy+22,10],"rotation":[-25,0,-10],"uv":[0,0]},
  {"origin":[8,hy+22,8],"size":[4,22,4],"pivot":[10,hy+22,10],"rotation":[-25,0,10],"uv":[0,0]},
  {"origin":[-22,hy+6,-26],"size":[8,2,2],"uv":[0,0]},
  {"origin":[14,hy+6,-26],"size":[8,2,2],"uv":[0,0]}]})
w(f"{RP}/models/entity/shenron.geo.json",{"format_version":"1.12.0","minecraft:geometry":[{"description":{
  "identifier":"geometry.dbz.shenron","texture_width":256,"texture_height":128,
  "visible_bounds_width":14,"visible_bounds_height":18,"visible_bounds_offset":[0,8,0]},"bones":bones}]})
w(f"{RP}/animations/shenron.animation.json",{"format_version":"1.8.0","animations":{
  "animation.dbz.shenron.idle":{"loop":True,"bones":{
    "body":{"rotation":[0,"math.sin(q.life_time * 30) * 6",0]},
    "head":{"rotation":["math.sin(q.life_time * 50) * 5","math.sin(q.life_time * 35) * 8",0]}}}}})
w(f"{RP}/entity/shenron.entity.json",{"format_version":"1.10.0","minecraft:client_entity":{"description":{
  "identifier":"dbz:shenron","materials":{"default":"entity_alphatest"},"textures":{"default":"textures/entity/shenron"},
  "geometry":{"default":"geometry.dbz.shenron"},"animations":{"idle":"animation.dbz.shenron.idle"},
  "scripts":{"animate":["idle"]},"render_controllers":["controller.render.default"]}}})
im=Image.new("RGBA",(256,128),(40,150,60,255)); d=ImageDraw.Draw(im)
for y in range(0,128,6):
    for x in range((y//6)%2*6,256,12): d.arc((x,y,x+10,y+8),0,180,fill=(25,110,40,255))
d.rectangle((0,0,255,3),fill=(240,200,80,255))  # belly stripe
# head region (uv 0,48): eyes and teeth on the front face area
d.rectangle((40,48+40,68,48+62),fill=(50,160,70,255))
d.rectangle((44,48+44,48,48+47),fill=(230,30,30,255)); d.rectangle((60,48+44,64,48+47),fill=(230,30,30,255))
d.rectangle((44,48+56,64,48+58),fill=(245,245,245,255))
im.save(f"{RP}/textures/entity/shenron.png")
# ---- sounds + lang ----
sd=json.load(open(f"{RP}/sounds/sound_definitions.json"))
sd["sound_definitions"].update({
 "dbz.shenron":{"category":"neutral","sounds":[{"name":"sounds/mob/enderdragon/growl3","volume":1.0,"pitch":0.6}]},
 "dbz.scouter":{"category":"ui","sounds":[{"name":"sounds/random/click","volume":0.8,"pitch":1.8}]},
 "dbz.senzu":{"category":"player","sounds":[{"name":"sounds/random/burp","volume":0.8,"pitch":1.2}]},
 "dbz.capsule":{"category":"player","sounds":[{"name":"sounds/random/pop","volume":1.0,"pitch":0.8}]}})
w(f"{RP}/sounds/sound_definitions.json",sd)
print("extras generated")
