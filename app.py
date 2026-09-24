from __future__ import annotations

import traceback
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from planner import make_plan
from generator import build as build_world, to_litematic, preview


BASE = Path(__file__).parent
OUT = BASE / "generated"
OUT.mkdir(exist_ok=True)

app = FastAPI(
    title="VoxelForge Free",
    version="2.0.1"
)

app.mount(
    "/static",
    StaticFiles(directory=BASE / "static"),
    name="static"
)


@app.get("/")
def home():
    return FileResponse(BASE / "static" / "index.html")


@app.post("/api/build")
async def build(
    description: str = Form(...),
    image: UploadFile | None = File(default=None)
):
    description = description.strip()

    if not description:
        raise HTTPException(
            status_code=400,
            detail="נא לכתוב תיאור של הבנייה."
        )

    try:
        # תכנון מקומי — ללא OpenAI וללא API Key.
        plan = make_plan(description)

        # חשוב: משתמשים בשם build_world כדי לא להתנגש
        # עם פונקציית ה-API בשם build.
        world = build_world(plan)

        build_id = uuid.uuid4().hex[:12]

        safe_name = "".join(
            c if c.isalnum() or c in "-_"
            else "_"
            for c in plan.get("name", "build")
        )[:60] or "build"

        litematic_path = (
            OUT / f"{build_id}_{safe_name}.litematic"
        )

        preview_path = (
            OUT / f"{build_id}_{safe_name}.png"
        )

        stats = to_litematic(
            world,
            litematic_path,
            plan.get("name", "Generated Build")
        )

        preview(
            world,
            preview_path,
            scale=max(
                3,
                min(
                    10,
                    720 // max(world.sx, world.sz)
                )
            )
        )

        return {
            "id": build_id,
            "name": plan.get(
                "name",
                "Generated Build"
            ),
            "size": plan["size"],
            "stats": stats,
            "preview": (
                f"/api/file/{preview_path.name}"
            ),
            "litematic": (
                f"/api/file/{litematic_path.name}"
            ),
            "plan": plan,
        }

    except Exception as e:
        traceback.print_exc()

        raise HTTPException(
            status_code=500,
            detail=f"שגיאה ביצירת המבנה: {e}"
        )


@app.get("/health")
def health():
    return {
        "ok": True,
        "mode": "free-local-planner"
    }


@app.get("/api/file/{filename}")
def get_file(filename: str):
    p = OUT / filename

    if not p.exists() or p.parent != OUT:
        raise HTTPException(
            status_code=404,
            detail="קובץ לא נמצא"
        )

    media = (
        "image/png"
        if p.suffix.lower() == ".png"
        else "application/octet-stream"
    )

    return FileResponse(
        p,
        media_type=media,
        filename=p.name
    )
