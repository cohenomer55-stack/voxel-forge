from __future__ import annotations
import uuid, traceback
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from planner import make_plan
from generator import build, to_litematic, preview

BASE = Path(__file__).parent
OUT = BASE / 'generated'
OUT.mkdir(exist_ok=True)

app = FastAPI(title='VoxelForge Free', version='2.0.0')
app.mount('/static', StaticFiles(directory=BASE/'static'), name='static')

@app.get('/')
def home():
    return FileResponse(BASE/'static'/'index.html')

@app.post('/api/build')
async def build(description: str = Form(...), image: UploadFile|None = File(default=None)):
    description = description.strip()
    if not description:
        raise HTTPException(400, 'נא לכתוב תיאור של הבנייה.')
    try:
        # The image is optional high-level inspiration. This free version does not call an external vision API.
        plan = make_plan(description)
        world = build(plan)
        build_id = uuid.uuid4().hex[:12]
        safe_name = ''.join(c if c.isalnum() or c in '-_' else '_' for c in plan.get('name','build'))[:60] or 'build'
        litematic_path = OUT / f'{build_id}_{safe_name}.litematic'
        preview_path = OUT / f'{build_id}_{safe_name}.png'
        stats = to_litematic(world, litematic_path, plan.get('name','Generated Build'))
        preview(world, preview_path, scale=max(3, min(10, 720//max(world.sx, world.sz))))
        return {
            'id': build_id,
            'name': plan.get('name','Generated Build'),
            'size': plan['size'],
            'stats': stats,
            'preview': f'/api/file/{preview_path.name}',
            'litematic': f'/api/file/{litematic_path.name}',
            'plan': plan,
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, f'שגיאה ביצירת המבנה: {e}')

@app.get('/health')
def health():
    return {'ok': True, 'mode': 'free-local-planner'}

@app.get('/api/file/{filename}')
def get_file(filename: str):
    p = OUT / filename
    if not p.exists() or p.parent != OUT:
        raise HTTPException(404, 'קובץ לא נמצא')
    media = 'image/png' if p.suffix.lower()=='.png' else 'application/octet-stream'
    return FileResponse(p, media_type=media, filename=p.name)
