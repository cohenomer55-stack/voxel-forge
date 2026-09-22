from __future__ import annotations
import os, re, uuid
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from planner import plan
from generator import build, to_litematic, preview

BASE=Path(__file__).parent; OUT=BASE/'generated'; OUT.mkdir(exist_ok=True)
app=FastAPI(title='VoxelForge Litematica Builder')
app.mount('/static',StaticFiles(directory=BASE/'static'),name='static')

@app.get('/')
def home(): return FileResponse(BASE/'static'/'index.html')
@app.get('/health')
def health(): return {'ok':True}

@app.post('/api/build')
async def make_build(description:str=Form(...), image:UploadFile|None=File(None)):
    description=description.strip()
    if not description: raise HTTPException(400,'נא לכתוב תיאור.')
    max_mb=int(os.getenv('MAX_UPLOAD_MB','8'))
    image_bytes=None
    if image:
        image_bytes=await image.read()
        if len(image_bytes)>max_mb*1024*1024: raise HTTPException(413,f'התמונה גדולה מדי. המגבלה היא {max_mb}MB.')
    p=plan(description,image_bytes)
    w=build(p); rid=uuid.uuid4().hex[:10]; safe=re.sub(r'[^a-zA-Z0-9_-]+','_',p.get('name','build'))[:50]
    lp=OUT/f'{rid}_{safe}.litematic'; pp=OUT/f'{rid}_{safe}.png'
    stats=to_litematic(w,lp,p.get('name','Generated Build')); preview(w,pp,scale=max(3,min(8,720//max(w.sx,w.sz))))
    return {'name':p.get('name','Generated Build'),'size':p['size'],'stats':stats,'preview':f'/api/file/{pp.name}','litematic':f'/api/file/{lp.name}','plan':p}

@app.get('/api/file/{filename}')
def file(filename:str):
    p=OUT/filename
    if not p.exists() or p.parent!=OUT: raise HTTPException(404,'קובץ לא נמצא')
    media='image/png' if p.suffix.lower()=='.png' else 'application/octet-stream'
    return FileResponse(p,media_type=media,filename=p.name)
