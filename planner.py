from __future__ import annotations
import re


def _num(text, patterns, default):
    for p in patterns:
        m = re.search(p, text, re.I)
        if m:
            try:
                return int(m.group(1))
            except Exception:
                pass
    return default


def _has(t, *words):
    return any(w in t for w in words)


def safe_int(v, default):
    try:
        return int(v)
    except Exception:
        return default


def _chest(x, y, z, items):
    return {
        "type": "chest", "x": x, "y": y, "z": z, "facing": "north",
        "items": [{"id": item, "count": count} for item, count in items]
    }


def make_plan(description: str, size=(64, 40, 64), seed=42):
    """Local, no-API natural-language planner. It uses keywords/dimensions to build a varied map."""
    t = description.lower()
    sx = _num(t, [r'(?:^|\s)(\d{2,3})\s*[x×]\s*(\d{2,3})', r'(?)(\d{2,3})\s*(?:על|x|×)\s*(\d{2,3})'], size[0])
    sz = _num(t, [r'(?:^|\s)(\d{2,3})\s*[x×]\s*(\d{2,3})'], size[2])
    # Prefer explicit "100x70" dimensions.
    m = re.search(r'(\d{2,3})\s*[x×]\s*(\d{2,3})', t)
    if m:
        sx, sz = int(m.group(1)), int(m.group(2))
    sx = max(24, min(140, sx))
    sz = max(24, min(140, sz))

    sy = _num(t, [r'(?:גובה|height)\s*(\d{2,3})'], size[1])
    sy = max(28, min(70, sy))
    surface = _num(t, [r'(?:surface|surface_y|גובה פני השטח|מתחת לפני השטח)[^\d]{0,12}(\d{1,2})'], min(20, sy - 12))
    surface = max(8, min(sy - 8, surface))

    coastal = _has(t, 'חוף', 'ים', 'לגונה', 'אי', 'coast', 'beach', 'sea', 'island', 'lagoon')
    desert = _has(t, 'מדבר', 'desert', 'sand')
    mesa = _has(t, 'mesa', 'badlands', 'אדום', 'מסלע', 'קניון')
    forest = _has(t, 'יער', 'forest', 'עצים')
    village = _has(t, 'כפר', 'village', 'town', 'יישוב')
    tower = _has(t, 'מגדל', 'tower', 'מגדלור', 'lighthouse')
    caves = _has(t, 'מערה', 'מערות', 'מנהרה', 'מנהרות', 'underground', 'cave', 'tunnel')
    bridge = _has(t, 'גשר', 'bridge')
    large = _has(t, 'גדול', 'ענק', 'massive', 'large')

    features=[]
    underground=[]
    loot=[]

    wall = 'minecraft:sandstone' if desert else ('minecraft:red_sandstone' if mesa else 'minecraft:cobblestone')
    roof = 'minecraft:red_sandstone' if mesa else ('minecraft:spruce_planks' if forest else 'minecraft:oak_planks')
    tree_kind = 'spruce' if forest else 'oak'

    # Settlement layout.
    if village or not any((village, tower, mesa, desert)):
        for i, (x, z) in enumerate([
            (8,8), (24,10), (42,7), (12,31), (34,29), (54,35),
        ]):
            x = min(max(3, x), sx-9); z=min(max(3,z),sz-9)
            w, d = 6 + (i%3), 6 + ((i+1)%3)
            features.append({'type':'hollow_box','x':x,'y':surface+1,'z':z,'width':w,'height':5,'depth':d,'block':wall})
            features.append({'type':'roof_pyramid','x':x-1,'y':surface+6,'z':z-1,'width':w+2,'depth':d+2,'height':2,'block':roof})
    else:
        for x,z in [(10,10),(28,14),(46,9)]:
            if x<sx-8 and z<sz-8:
                features.append({'type':'hollow_box','x':x,'y':surface+1,'z':z,'width':7,'height':5,'depth':7,'block':wall})
                features.append({'type':'roof_pyramid','x':x-1,'y':surface+6,'z':z-1,'width':9,'depth':9,'height':2,'block':roof})

    # Trees.
    tree_count = 30 if large else 18
    if forest or not desert:
        for i in range(tree_count):
            x = 5 + (i*17 + 11) % max(8, sx-10)
            z = 6 + (i*23 + 7) % max(8, sz-12)
            if coastal and z < sz//5:
                z += sz//4
            features.append({'type':'tree','x':min(sx-4,x),'y':surface+1,'z':min(sz-4,z),'kind':tree_kind,'height':5+(i%4)})

    # Roads/paths.
    features.append({'type':'path','points':[[4,4],[sx//4,sz//5],[sx//2,sz//2],[sx*3//4,sz*3//5],[sx-5,sz-6]],'width':1,'block':'minecraft:dirt'})
    if bridge:
        features.append({'type':'bridge','x':sx//3,'y':surface+1,'z':sz//2,'length':max(8,sx//3),'width':3,'block':'minecraft:oak_planks'})

    # Tower / lighthouse.
    if tower or coastal:
        tx, tz = sx-10, sz-10
        features.append({'type':'tower','x':tx,'y':surface+1,'z':tz,'width':5,'depth':5,'height':14 if large else 11,'wall':wall})
        features.append({'type':'roof_pyramid','x':tx-1,'y':surface+15 if large else surface+12,'z':tz-1,'width':7,'depth':7,'height':3,'block':roof})

    # Mesa-ish area.
    if mesa:
        for i in range(6):
            x = sx*2//3 + (i*7)%max(5,sx//3-4)
            z = sz//3 + (i*11)%max(5,sz//2-5)
            features.append({'type':'cylinder','x':min(sx-6,x),'y':surface+1,'z':min(sz-6,z),'radius':3+(i%3),'height':3+(i%5),'block':'minecraft:red_sandstone'})

    # Water pools/shore emphasis.
    if coastal:
        water_level = max(3, surface-2)
    else:
        water_level = max(0, surface-4)

    # Underground system.
    if caves or True:
        cy = max(5, surface-10)
        underground += [
            {'type':'mine_room','x':sx//2,'y':cy,'z':sz//2,'rx':6,'ry':3,'rz':5,'wall':'minecraft:deepslate'},
            {'type':'tunnel','points':[[sx//2,cy,sz//2],[sx//2-14,cy-1,sz//2-6],[10,max(5,cy-1),sz*2//3]],'radius':2,'wall':'minecraft:deepslate','supports':True},
            {'type':'tunnel','points':[[sx//2,cy+1,sz//2],[sx//2+16,cy-1,sz//2+9],[sx-9,max(5,cy),12]],'radius':2,'wall':'minecraft:deepslate','supports':True},
            {'type':'ore_patch','x':max(4,sx//3),'y':max(4,cy-1),'z':max(4,sz//2+4),'count':10,'radius':4,'block':'minecraft:iron_ore','seed':seed+11},
            {'type':'ore_patch','x':max(4,sx//2+9),'y':max(4,cy-1),'z':max(4,sz//3),'count':8,'radius':4,'block':'minecraft:coal_ore','seed':seed+19},
        ]

    # Loot chests.
    chest_positions=[
        (min(12,sx-3), surface+1, min(12,sz-3)),
        (min(30,sx-3), surface+1, min(12,sz-3)),
        (min(48,sx-3), surface+1, min(11,sz-3)),
        (min(18,sx-3), surface+1, min(31,sz-3)),
        (min(40,sx-3), surface+1, min(29,sz-3)),
        (sx//2, max(5,cy), sz//2),
    ]
    loot_sets=[
        [('minecraft:iron_sword',1),('minecraft:bread',8),('minecraft:torch',12)],
        [('minecraft:iron_helmet',1),('minecraft:iron_chestplate',1),('minecraft:cooked_beef',10)],
        [('minecraft:iron_leggings',1),('minecraft:iron_boots',1),('minecraft:shield',1)],
        [('minecraft:golden_apple',1),('minecraft:bread',12),('minecraft:arrow',16)],
        [('minecraft:bow',1),('minecraft:cooked_beef',12),('minecraft:torch',16)],
        [('minecraft:iron_sword',1),('minecraft:shield',1),('minecraft:golden_apple',1)],
    ]
    for p, items in zip(chest_positions, loot_sets):
        if 0<=p[0]<sx and 0<=p[1]<sy and 0<=p[2]<sz:
            loot.append(_chest(*p,items))

    name = 'VoxelForge Adventure Map'
    if coastal: name='Coastal Adventure Map'
    if desert: name='Desert Adventure Map'
    if mesa: name='Badlands Adventure Map'
    return {
        'name':name,
        'size':{'x':sx,'y':sy,'z':sz},
        'terrain':{'surface_y':surface,'water_level':water_level,'seed':seed,'biomes':['grass','sand','stone','red_sand'] if mesa else ['grass','sand','stone']},
        'features':features,
        'underground':underground,
        'loot':loot,
    }


def fallback_plan(description: str, size=(64,40,64)):
    return make_plan(description, size=size)


def plan_with_openai(description: str, image_bytes=None, model=None):
    # Intentionally local: no API key, account, or paid service is required.
    return make_plan(description)
