"""
Briefs API — store and retrieve client briefs
POST /api/briefs           — save a brief
GET  /api/briefs/{user_id} — get brief for a user
"""

import json, time
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()
DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
BRIEFS_DB = DB_DIR / "briefs_db.json"


def _load() -> list:
    if not BRIEFS_DB.exists():
        return []
    with open(BRIEFS_DB, encoding="utf-8") as f:
        return json.load(f)

def _save(data: list):
    with open(BRIEFS_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class Room(BaseModel):
    name:  str
    area:  Optional[str] = ""
    notes: Optional[str] = ""

class BriefSave(BaseModel):
    client_id:   str
    description: str
    caption:     Optional[str] = ""
    rooms:       Optional[List[Room]] = []
    total_area:  Optional[int] = 0
    style:       Optional[str] = ""
    budget:      Optional[str] = ""
    priorities:  Optional[List[str]] = []
    constraints: Optional[List[str]] = []


@router.post("/briefs")
def save_brief(body: BriefSave):
    briefs = _load()
    # Remove existing brief for this client
    briefs = [b for b in briefs if b.get("client_id") != body.client_id]
    brief = {
        "client_id":   body.client_id,
        "description": body.description,
        "caption":     body.caption or "",
        "rooms":       [r.model_dump() for r in (body.rooms or [])],
        "total_area":  body.total_area or 0,
        "style":       body.style or "",
        "budget":      body.budget or "",
        "priorities":  body.priorities or [],
        "constraints": body.constraints or [],
        "updated_at":  int(time.time()),
    }
    briefs.append(brief)
    _save(briefs)
    return JSONResponse(content=brief, status_code=201)


@router.get("/briefs/{client_id}")
def get_brief(client_id: str):
    brief = next((b for b in _load() if b.get("client_id") == client_id), None)
    if not brief:
        return JSONResponse(content={"brief": None})
    return JSONResponse(content={"brief": brief})
