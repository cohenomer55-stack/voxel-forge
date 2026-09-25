from __future__ import annotations
import math, random
from pathlib import Path
from typing import Any
from PIL import Image, ImageDraw
from nbt_writer import Int, Long, Byte, IntArray, LongArray, dump_gzip

COLORS={
'air':(0,0,0,255),'grass_block':(91,144,67,255),'dirt':(126,84,47,255),'stone':(122,122,122,255),'sand':(224,203,126,255),'sandstone':(205,183,108,255),'water':(54,133,193,255),'oak_planks':(176,129,67,255),'oak_log':(119,86,49,255),'oak_leaves':(55,118,55,255),'spruce_planks':(103,74,45,255),'spruce_log':(78,56,40,255),'spruce_leaves':(45,92,54,255),'cobblestone':(99,99,99,255),'brick':(145,76,58,255),'glass':(165,211,221,255),'red_sand':(190,96,54,255),'red_sandstone':(161,80,53,255),'terracotta':(149,84,67,255),'deepslate':(58,61,65,255),'coal_ore':(63,66,68,255),'iron_ore':(177,146,114,255),'gold_ore':(203,175,59,255),'torch':(244,188,70,255),'lantern':(225,177,85,255),'chest':(166,104,41,255),'barrel':(142,88,45,255),'bookshelf':(136,95,51,255),'gravel':(129,126,119,255)}

def bs(name:str,props:dict|None=None)->dict:
    d={'Name': name if name.startswith('minecraft:') else 'minecraft:'+name}
    if props: d['Properties']={str(k):str(v) for k,v in props.items()}
    return d

def key(s:dict)->str: return s['Name']+'|'+str(sorted(s.get('Properties',{}).items()))

class World:
    def __init__(self,size:dict): self.sx=int(size['x']); self.sy=int(size['y']); self.sz=int(size['z']); self.blocks={}; self.tiles=[]
    def inside(self,x,y,z): return 0<=x<self.sx and 0<=y<self.sy and 0<=z<self.sz
    def set(self,x,y,z,name,props=None):
        x,y,z=int(x),int(y),int(z)
        if self.inside(x,y,z): self.blocks[(x,y,z)]=bs(name,props) if name!='minecraft:air' and name!='air' else None; self.blocks.pop((x,y,z),None) if self.blocks[(x,y,z)] is None else None
    def get(self,x,y,z):
        v=self.blocks.get((x,y,z)); return v['Name'].split(':',1)[-1] if v else 'air'
    def fill(self,x1,y1,z1,x2,y2,z2,name):
        for y in range(max(0,y1),min(self.sy-1,y2)+1):
            for z in range(max(0,z1),min(self.sz-1,z2)+1):
                for x in range(max(0,x1),min(self.sx-1,x2)+1): self.set(x,y,z,name)
    def hollow(self,x1,y1,z1,x2,y2,z2,name):
        for y in range(y1,y2+1):
            for z in range(z1,z2+1):
                for x in range(x1,x2+1):
                    if x in (x1,x2) or z in (z1,z2) or y in (y1,y2): self.set(x,y,z,name)
    def sphere_air(self,cx,cy,cz,rx,ry,rz):
        for y in range(max(0,int(cy-ry)),min(self.sy-1,int(cy+ry))+1):
            for z in range(max(0,int(cz-rz)),min(self.sz-1,int(cz+rz))+1):
                for x in range(max(0,int(cx-rx)),min(self.sx-1,int(cx+rx))+1):
                    if ((x-cx)/max(rx,.1))**2+((y-cy)/max(ry,.1))**2+((z-cz)/max(rz,.1))**2<=1: self.set(x,y,z,'air')
    def tree(self,x,y,z,kind='oak',height=5):
        trunk='oak_log' if kind=='oak' else 'spruce_log'; leaves='oak_leaves' if kind=='oak' else 'spruce_leaves'
        for yy in range(y,y+height): self.set(x,yy,z,trunk)
        top=y+height-1
        for yy in range(top-2,top+2):
            r=2 if yy<top+1 else 1
            for dx in range(-r,r+1):
                for dz in range(-r,r+1):
                    if dx*dx+dz*dz<=r*r+1: self.set(x+dx,yy,z+dz,leaves)

def surface(w:World,x,z)->int:
    for y in range(w.sy-1,-1,-1):
        if w.get(x,y,z) not in ('air','water'): return y+1
    return 1

def terrain(w:World,t:dict):
    sv=t.get('surface_y',20); ground=int(sv) if isinstance(sv,(int,float)) else min(20,w.sy-8); water=int(t.get('water_level',ground-2)); seed=int(t.get('seed',42)); biomes=t.get('biomes',['grass','sand','stone'])
    for x in range(w.sx):
        for z in range(w.sz):
            h=max(3,min(w.sy-2,round(ground+(math.sin(x/9)+math.cos(z/11))*1.4+math.sin((x+z)/19)*1.0)))
            coast=(z<max(8,int(w.sz*.14)))
            if coast: h=min(h,water+1)
            if h<=water:
                for y in range(h+1): w.set(x,y,z,'sand' if y>=h-2 else 'stone')
                for y in range(h+1,min(w.sy-1,water)+1): w.set(x,y,z,'water')
            else:
                top='grass_block'
                if 'sand' in biomes and (x<18 or coast or (x*7+z*11+seed)%31<2): top='sand'
                if 'red_sand' in biomes and x>w.sx*.62: top='red_sand'
                w.set(x,h,z,top)
                for d in (1,2,3): w.set(x,h-d,z,'dirt' if d<3 else 'stone')

def add_path(w:World,pts:list,width:int=1):
    for x,z in pts:
        y=max(1,surface(w,x,z)-1)
        for dx in range(-width,width+1):
            for dz in range(-width,width+1):
                if dx*dx+dz*dz<=width*width+1: w.set(x+dx,y,z+dz,'dirt')

def tunnel(w:World,points:list,radius:int=2,wall='deepslate'):
    for a,b in zip(points,points[1:]):
        x1,y1,z1=map(int,a); x2,y2,z2=map(int,b); steps=max(abs(x2-x1),abs(y2-y1),abs(z2-z1),1)
        for i in range(steps+1):
            q=i/steps; cx=round(x1+(x2-x1)*q); cy=round(y1+(y2-y1)*q); cz=round(z1+(z2-z1)*q)
            w.sphere_air(cx,cy,cz,radius,radius,radius)
            if i%5==0:
                for dx in (-radius,radius): w.set(cx+dx,cy,cz,'spruce_log')
                for dx in range(-radius,radius+1): w.set(cx+dx,cy+radius,cz,'spruce_log')

def feature(w:World,f:dict):
    t=f.get('type'); x=int(f.get('x',0)); y=int(f.get('y',0)); z=int(f.get('z',0))
    if t=='hollow_box': w.hollow(x,y,z,x+int(f.get('width',7))-1,y+int(f.get('height',5))-1,z+int(f.get('depth',7))-1,f.get('block','cobblestone'))
    elif t=='tower':
        W=int(f.get('width',5)); D=int(f.get('depth',5)); H=int(f.get('height',12)); w.hollow(x,y,z,x+W-1,y+H-1,z+D-1,f.get('wall','stone'))
        for i in range(1,H-1): w.set(x+1,y+i,z+1,'ladder',{'facing':'south'} if i%2==0 else {'facing':'east'})
    elif t=='roof':
        W=int(f.get('width',7)); D=int(f.get('depth',7)); H=int(f.get('height',3)); block=f.get('block','spruce_planks')
        for dy in range(H):
            inset=dy
            for xx in range(inset,W-inset):
                for zz in range(inset,D-inset): w.set(x+xx,y+dy,z+zz,block)
    elif t=='tree': w.tree(x,y,z,f.get('kind','oak'),int(f.get('height',5)))
    elif t=='bridge':
        for i in range(int(f.get('length',10))):
            for dz in range(int(f.get('width',3))): w.set(x+i,y,z+dz,'oak_planks')
    elif t=='mine_room': w.sphere_air(x,y,z,int(f.get('rx',5)),int(f.get('ry',3)),int(f.get('rz',5)))
    elif t=='tunnel': tunnel(w,f.get('points',[]),int(f.get('radius',2)),f.get('wall','deepslate'))
    elif t=='ore':
        rnd=random.Random(int(f.get('seed',1))); n=int(f.get('count',8)); r=int(f.get('radius',3)); ore=f.get('block','iron_ore')
        for _ in range(n): w.set(x+rnd.randint(-r,r),y+rnd.randint(-r,r),z+rnd.randint(-r,r),ore)

def build(plan:dict)->World:
    w=World(plan['size']); terrain(w,plan.get('terrain',{}))
    for f in plan.get('features',[]): feature(w,f)
    for f in plan.get('underground',[]): feature(w,f)
    for p in plan.get('paths',[]): add_path(w,p.get('points',[]),int(p.get('width',1)))
    for l in plan.get('loot',[]):
        x,y,z=int(l['x']),int(l['y']),int(l['z']); w.set(x,y,z,'chest',{'facing':l.get('facing','north'),'type':'single','waterlogged':'false'})
        items=[]
        slot=0
        for it in l.get('items',[]):
            cnt=int(it.get('count',1))
            if cnt<=0: continue
            items.append({'Slot':Byte(slot%27),'id':it['id'],'Count':Byte(min(cnt,127))}); slot+=1
            if slot>=27: break
        w.tiles.append({'id':'minecraft:chest','x':Int(x),'y':Int(y),'z':Int(z),'Items':items})
    return w

def default_plan(desc:str,size=(100,50,70))->dict:
    sx,sy,sz=size; surface_y=min(20,sy-8); items=[
      [{'id':'minecraft:iron_sword','count':1},{'id':'minecraft:bread','count':8},{'id':'minecraft:torch','count':12}],
      [{'id':'minecraft:iron_helmet','count':1},{'id':'minecraft:iron_chestplate','count':1},{'id':'minecraft:cooked_beef','count':10}],
      [{'id':'minecraft:iron_leggings','count':1},{'id':'minecraft:iron_boots','count':1},{'id':'minecraft:shield','count':1}],
      [{'id':'minecraft:golden_apple','count':1},{'id':'minecraft:bread','count':10},{'id':'minecraft:arrow','count':16}],
      [{'id':'minecraft:bow','count':1},{'id':'minecraft:cooked_beef','count':12},{'id':'minecraft:torch','count':16}],
      [{'id':'minecraft:iron_sword','count':1},{'id':'minecraft:shield','count':1},{'id':'minecraft:golden_apple','count':1}]
    ]
    feats=[]
    coords=[(8,8),(26,10),(44,8),(14,31),(39,30),(59,39)]
    for i,(x,z) in enumerate(coords):
        wall='sandstone' if i<2 else ('red_sandstone' if i>=4 else 'cobblestone')
        feats += [{'type':'hollow_box','x':x,'y':surface_y+1,'z':z,'width':7+(i%2)*2,'height':5,'depth':6+(i%3),'block':wall},
                  {'type':'roof','x':x-1,'y':surface_y+6,'z':z-1,'width':9+(i%2)*2,'height':2,'depth':8+(i%3),'block':'spruce_planks' if i<4 else 'red_sandstone'}]
    for x,z,h,k in [(6,23,6,'oak'),(31,19,8,'spruce'),(49,17,7,'oak'),(74,18,8,'spruce'),(83,48,7,'oak')]:
        if x<sx-2 and z<sz-2: feats.append({'type':'tree','x':x,'y':surface_y+1,'z':z,'kind':k,'height':h})
    feats += [{'type':'tower','x':sx-14,'y':surface_y+1,'z':sz-13,'width':5,'depth':5,'height':13,'wall':'stone'},
              {'type':'roof','x':sx-15,'y':surface_y+14,'z':sz-14,'width':7,'depth':7,'height':3,'block':'spruce_planks'},
              {'type':'bridge','x':60,'y':surface_y+1,'z':20,'length':18,'width':3}]
    underground=[
      {'type':'mine_room','x':sx//2,'y':8,'z':sz//2,'rx':6,'ry':3,'rz':5},
      {'type':'tunnel','points':[[sx//2,8,sz//2],[sx//2-18,7,sz//2-5],[10,8,41]],'radius':2},
      {'type':'tunnel','points':[[sx//2,9,sz//2],[sx//2+18,7,sz//2+10],[90,8,14]],'radius':2},
      {'type':'tunnel','points':[[sx//2,7,sz//2],[sx//2+7,6,sz//2-14],[76,7,55]],'radius':2},
      {'type':'ore','x':20,'y':7,'z':48,'count':10,'radius':4,'block':'iron_ore','seed':7},
      {'type':'ore','x':70,'y':6,'z':25,'count':10,'radius':4,'block':'coal_ore','seed':8},
    ]
    loot=[]
    for (x,z),its in zip([(13,12),(31,13),(49,11),(19,33),(44,33),(sx//2,8)],items): loot.append({'x':x,'y':surface_y+1 if (x,z)!=(sx//2,8) else 8,'z':z,'items':its})
    return {'name':'Coastal Adventure Map','size':{'x':sx,'y':sy,'z':sz},'terrain':{'surface_y':surface_y,'water_level':surface_y-2,'seed':42,'biomes':['grass','sand','stone','red_sand']},'features':feats,'underground':underground,'paths':[{'points':[[3,5],[18,12],[34,20],[49,26],[65,33],[84,40]],'width':1}], 'loot':[{'type':'chest',**c} for c in loot]}

def to_litematic(w:World,path:Path,name:str):
    states={'minecraft:air':{'Name':'minecraft:air'}}
    for s in w.blocks.values(): states[key(s)]=s
    palette=list(states.values()); indices=[]; pidx={key(s):i for i,s in enumerate(palette)}
    for y in range(w.sy):
        for z in range(w.sz):
            for x in range(w.sx): indices.append(pidx[key(w.blocks.get((x,y,z)) or {'Name':'minecraft:air'})])
    bits=max(2,math.ceil(math.log2(len(palette)))) if len(palette)>1 else 1; mask=(1<<bits)-1
    longs=[0]*((len(indices)*bits+63)//64); bp=0
    for v in indices:
        v&=mask; i=bp>>6; off=bp&63; longs[i]|=v<<off
        if off+bits>64: longs[i+1]|=v>>(64-off)
        bp+=bits
    longs=[(x & ((1<<64)-1))-(1<<64) if (x & (1<<63)) else (x & ((1<<64)-1)) for x in longs]
    total=w.sx*w.sy*w.sz
    def triple(x, y, z):
    return {
        'x': Int(x),
        'y': Int(y),
        'z': Int(z)
    }

region = {
    'Position': triple(0, 0, 0),
    'Size': triple(w.sx, w.sy, w.sz),
    'BlockStatePalette': palette,
    'BlockStates': LongArray(longs),
    'TileEntities': w.tiles,
    'Entities': [],
    'PendingBlockTicks': [],
    'PendingFluidTicks': [],
}

root = {
    'Version': Int(6),
    'SubVersion': Int(1),
    'MinecraftDataVersion': Int(3953),
    'Metadata': {
        'Name': name,
        'Author': 'VoxelForge',
        'Description': 'Generated without external AI APIs.',
        'RegionCount': Int(1),
        'TotalVolume': Int(total),
        'TotalBlocks': Int(len(w.blocks)),
        'TimeCreated': Long(0),
        'TimeModified': Long(0),
        'EnclosingSize': triple(w.sx, w.sy, w.sz),
        'ModifiedSinceReplace': Byte(0),
    },
    'Regions': {
        'region': region
    },
}
    ifiedSinceReplace':Byte(0)},'Regions':{'region':region}}
    dump_gzip(root,path,'Litematic')
    return {'blocks':len(w.blocks),'palette_size':len(palette),'volume':total,'bits_per_entry':bits}

def preview(w:World,path:Path,scale=6):
    img=Image.new('RGBA',(w.sx*scale,w.sz*scale),(17,23,27,255)); px=img.load(); d=ImageDraw.Draw(img)
    for z in range(w.sz):
        for x in range(w.sx):
            n='air'
            for y in range(w.sy-1,-1,-1):
                q=w.get(x,y,z)
                if q!='air': n=q; break
            c=COLORS.get(n,(120,120,120,255)); ytop=surface(w,x,z); shade=int((ytop/max(1,w.sy))*35-10); c=tuple(max(0,min(255,k+shade)) for k in c[:3])+(255,)
            for yy in range(z*scale,(z+1)*scale):
                for xx in range(x*scale,(x+1)*scale): px[xx,yy]=c
    for q in range(0,w.sx+1,10): d.line((q*scale,0,q*scale,w.sz*scale),fill=(255,255,255,45),width=1)
    for q in range(0,w.sz+1,10): d.line((0,q*scale,w.sx*scale,q*scale),fill=(255,255,255,45),width=1)
    for t in w.tiles:
        x,z=t['x'],t['z']; cx=x*scale+scale//2; cy=z*scale+scale//2; d.ellipse((cx-4,cy-4,cx+4,cy+4),fill=(232,190,71,255),outline=(70,45,10,255))
    img.save(path); return img.size
