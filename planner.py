from __future__ import annotations
import base64, json, os, re
from generator import default_plan

SCHEMA='''Return ONLY JSON with keys name, size, terrain, features, underground, paths, loot. Size is {x,y,z}. Use primitives: hollow_box, tower, roof, tree, bridge, mine_room, tunnel, ore. Use Minecraft Java 1.21.x block and item IDs. All coordinates must fit the size. Underground should use y values around 1..surface_y-1. Loot should be a modest set of chests containing basic iron gear, shields, golden apples, food, torches, bows and arrows. Use an inspiration image only for high-level mood/composition; do not copy distinctive architecture or exact layout.'''

def clamp_plan(p:dict)->dict:
    s=p.get('size',{}); sx=max(16,min(160,int(s.get('x',100)))); sy=max(16,min(80,int(s.get('y',50)))); sz=max(16,min(160,int(s.get('z',70)))); p['size']={'x':sx,'y':sy,'z':sz}
    p.setdefault('terrain',{}); p['terrain']['surface_y']=max(3,min(sy-5,int(p['terrain'].get('surface_y',min(20,sy-8)))))
    p['terrain']['water_level']=max(0,min(sy-3,int(p['terrain'].get('water_level',p['terrain']['surface_y']-2))))
    p.setdefault('features',[]); p.setdefault('underground',[]); p.setdefault('paths',[]); p.setdefault('loot',[])
    return p

def plan(description:str,image_bytes:bytes|None=None)->dict:
    key=os.getenv('OPENAI_API_KEY')
    if not key: return default_plan(description)
    from openai import OpenAI
    client=OpenAI(api_key=key); model=os.getenv('OPENAI_MODEL','gpt-5.6-luna')
    content=[{'type':'input_text','text':SCHEMA+'\nUSER REQUEST:\n'+description}]
    if image_bytes:
        b64=base64.b64encode(image_bytes).decode('ascii'); content.append({'type':'input_image','image_url':f'data:image/png;base64,{b64}'})
    r=client.responses.create(model=model,input=[{'role':'user','content':content}])
    text=r.output_text.strip(); text=re.sub(r'^```json\s*|\s*```$','',text,flags=re.I); a=text.find('{'); b=text.rfind('}')
    if a<0 or b<0: raise ValueError('Planner returned invalid JSON')
    return clamp_plan(json.loads(text[a:b+1]))
