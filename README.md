# Universe 7: Awakened Add-On - source (v1.55)

DBZ_BP/                Behavior pack: manifest, items, blocks, entities, recipes, loot tables,
                       and scripts/ (JavaScript, Minecraft Script API - main.js is the entry point)
DBZ_RP/                Resource pack: textures, models, attachables, particles, render controllers,
                       item_texture.json, terrain_texture.json, flipbook_textures.json, blocks.json, texts/
Universe7_Anime_Textures_standalone/
                       The vanilla anime texture pack on its own (for use as a global resource pack)
tools/                 Python generators (need Pillow). pixlib.py and blockkit.py are the shared style
                       helpers; every gen_*.py script redraws one set of textures straight into the packs.

Build: zip the contents of DBZ_BP and DBZ_RP separately as .mcpack files, then zip those two
together and rename the result to .mcaddon.
Scripts in tools/ write to /home/claude/... paths; change the RP / OUT / PACK constants at the top
of each script to your own folders before running them.
