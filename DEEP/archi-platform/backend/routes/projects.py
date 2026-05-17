"""
Projects API
GET    /api/projects              — list projects (filter by architect_id or client_id)
POST   /api/projects              — create project
GET    /api/projects/{id}         — get one
PUT    /api/projects/{id}         — update
DELETE /api/projects/{id}         — delete
"""

import json, uuid, time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router   = APIRouter()
DB_DIR   = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
PROJ_DB  = DB_DIR / "projects_db.json"


def _load() -> list:
    if not PROJ_DB.exists():
        _save([])
        return []
    with open(PROJ_DB, encoding="utf-8") as f:
        return json.load(f)

def _save(data: list):
    with open(PROJ_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _month() -> str:
    import datetime
    months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    n = datetime.datetime.now()
    return f"{months[n.month-1]} {n.year}"


class ProjectCreate(BaseModel):
    name:          str
    client_id:     Optional[str] = ""
    client_name:   Optional[str] = ""
    type:          Optional[str] = "Résidentiel"
    area:          Optional[str] = ""
    budget:        Optional[str] = ""
    architect_id:  Optional[str] = "arch_1"
    status:        Optional[str] = "En cours"
    progress:      Optional[int] = 0

class ProjectUpdate(BaseModel):
    name:         Optional[str] = None
    status:       Optional[str] = None
    progress:     Optional[int] = None
    type:         Optional[str] = None
    area:         Optional[str] = None
    budget:       Optional[str] = None
    client_name:  Optional[str] = None
    plan_caption: Optional[str] = None
    plan_style:   Optional[str] = None


@router.get("/projects")
def list_projects(architect_id: str = "", client_id: str = "", status: str = "", limit: int = 0):
    projects = _load()
    if architect_id:
        projects = [p for p in projects if p.get("architect_id") == architect_id]
    if client_id:
        projects = [p for p in projects if p.get("client_id") == client_id]
    if status and status != "all":
        projects = [p for p in projects if p.get("status") == status]
    # Sort by creation date descending
    projects = sorted(projects, key=lambda p: p.get("created_at", ""), reverse=True)
    if limit and limit > 0:
        projects = projects[:limit]
    return JSONResponse(content={"projects": projects, "total": len(projects)})


@router.post("/projects")
def create_project(body: ProjectCreate):
    projects = _load()
    proj = {
        "id":           str(uuid.uuid4())[:8],
        "name":         body.name,
        "client_id":    body.client_id or "",
        "client_name":  body.client_name or "",
        "architect_id": body.architect_id or "arch_1",
        "status":       body.status or "En cours",
        "progress":     body.progress or 0,
        "type":         body.type or "Résidentiel",
        "area":         body.area or "",
        "budget":       body.budget or "",
        "date":         _month(),
        "created_at":   str(int(time.time())),
        "plan_caption": "",
        "plan_style":   "",
    }
    projects.append(proj)
    _save(projects)
    return JSONResponse(content=proj, status_code=201)


@router.get("/projects/{proj_id}")
def get_project(proj_id: str):
    proj = next((p for p in _load() if p["id"] == proj_id), None)
    if not proj:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    return JSONResponse(content=proj)


@router.put("/projects/{proj_id}")
def update_project(proj_id: str, body: ProjectUpdate):
    projects = _load()
    idx = next((i for i, p in enumerate(projects) if p["id"] == proj_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Projet non trouvé")
    for k, v in body.model_dump(exclude_none=True).items():
        projects[idx][k] = v
    _save(projects)
    return JSONResponse(content=projects[idx])


@router.delete("/projects/{proj_id}")
def delete_project(proj_id: str):
    projects = [p for p in _load() if p["id"] != proj_id]
    _save(projects)
    return JSONResponse(content={"message": "Projet supprimé"})
