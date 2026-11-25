"""Saiyan transformation looks (v1.47): one helmet-slot attachable per look that renders the
detailed 128x128 body overlay AND the 3D hair piece together (two render controllers)."""
import json, os
RP = "/home/claude/dbz/DBZ_RP"; BP = "/home/claude/dbz/DBZ_BP"

# look id -> (display name, body texture id, hair key)
LOOKS = {
    "base":        ("Saiyan: Base", "saiyan_base", "black"),
    "battle":      ("Saiyan: Battle Damaged", "saiyan_battle_damaged", "black"),
    "kaioken":     ("Saiyan: Kaioken", "saiyan_kaioken", "black"),
    "ssj":         ("Super Saiyan", "saiyan_ssj", "gold"),
    "ssj2":        ("Super Saiyan 2", "saiyan_ssj2", "gold_sharp"),
    "ssj3":        ("Super Saiyan 3", "saiyan_ssj3", "gold_long"),
    "lssj":        ("Legendary Super Saiyan", "saiyan_legendary", "green"),
    "ssj4":        ("Super Saiyan 4", "saiyan_ssj4", "black_long"),
    "ssj_god":     ("Super Saiyan God", "saiyan_god", "red"),
    "ssj_blue":    ("Super Saiyan Blue", "saiyan_blue", "blue"),
    "blue_kaioken":("Super Saiyan Blue Kaioken", "saiyan_blue_kaioken", "blue"),
    "divine_bloom":("Divine Bloom", "saiyan_bloom", "pink"),
    "ui_sign":     ("Ultra Instinct -Sign-", "saiyan_ui_sign", "black"),
    "ui_mastered": ("Mastered Ultra Instinct", "saiyan_mui", "silver"),
    "ultra_ego":   ("Ultra Ego", "saiyan_ultra_ego", "purple"),
}

def w(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    json.dump(obj, open(path, "w"), indent=2)

w(f"{RP}/render_controllers/dbz_looks.render_controllers.json", {
    "format_version": "1.8.0",
    "render_controllers": {
        "controller.render.dbz_look_body": {
            "geometry": "Geometry.body", "materials": [{"*": "Material.default"}], "textures": ["Texture.body"]},
        "controller.render.dbz_look_hair": {
            "geometry": "Geometry.hair", "materials": [{"*": "Material.default"}], "textures": ["Texture.hair"]},
    }})

for lid, (name, tex, hair) in LOOKS.items():
    assert os.path.exists(f"{RP}/textures/entity/forms/{tex}.png"), tex
    hatt = json.load(open(f"{RP}/attachables/hair_{hair}.json"))["minecraft:attachable"]["description"]
    w(f"{RP}/attachables/look_saiyan_{lid}.json", {"format_version": "1.10.0", "minecraft:attachable": {"description": {
        "identifier": f"dbz:look_saiyan_{lid}",
        "materials": {"default": "armor", "enchanted": "armor_enchanted"},
        "textures": {"body": f"textures/entity/forms/{tex}", "hair": hatt["textures"]["default"],
                     "enchanted": "textures/misc/enchanted_item_glint"},
        "geometry": {"body": "geometry.dbz.form_overlay", "hair": hatt["geometry"]["default"]},
        "scripts": {"parent_setup": "variable.helmet_layer_visible = 0.0;"},
        "render_controllers": ["controller.render.dbz_look_body", "controller.render.dbz_look_hair"]}}})
    w(f"{BP}/items/look_saiyan_{lid}.json", {"format_version": "1.21.50", "minecraft:item": {
        "description": {"identifier": f"dbz:look_saiyan_{lid}", "menu_category": {"category": "none"}},
        "components": {"minecraft:icon": "dbz_hair", "minecraft:display_name": {"value": f"{name} (Transformation)"},
                       "minecraft:max_stack_size": 1, "minecraft:wearable": {"slot": "slot.armor.head", "protection": 0}}}})
print("saiyan looks:", ", ".join(LOOKS))
