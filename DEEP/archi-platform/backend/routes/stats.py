"""
Stats API — Dashboard statistics
GET /api/stats/architect  — architect dashboard stats
GET /api/stats/client     — client dashboard stats
"""

import json
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()
DB_DIR = Path(__file__).parent.parent / "data"


def _load_json(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@router.get("/stats/architect")
def architect_stats(architect_id: str = "arch_1"):
    projects_db = DB_DIR / "projects_db.json"
    clients_db  = DB_DIR / "clients_db.json"

    projects = _load_json(projects_db)
    clients  = _load_json(clients_db)

    arch_projects = [p for p in projects if p.get("architect_id") == architect_id]

    # Count unread messages from clients
    unread = 0
    for f in DB_DIR.glob("messages_*.json"):
        try:
            with open(f, encoding="utf-8") as mf:
                msgs = json.load(mf)
                unread += sum(1 for m in msgs if m.get("sender_role") == "client")
        except Exception:
            pass

    # Count plans analyzed (projects with a plan_caption)
    plans_analyzed = sum(1 for p in arch_projects if p.get("plan_caption"))

    # Count videos generated (projects with plan_style set)
    videos_generated = sum(1 for p in arch_projects if p.get("plan_style"))

    return JSONResponse(content={
        "total_projects":   len(arch_projects),
        "active_projects":  sum(1 for p in arch_projects if p.get("status") == "En cours"),
        "total_clients":    len(clients),
        "plans_analyzed":   plans_analyzed,
        "videos_generated": videos_generated,
        "messages_unread":  unread,
    })


@router.get("/stats/client")
def client_stats(client_id: str = ""):
    projects_db   = DB_DIR / "projects_db.json"
    conversations = DB_DIR / "conversations.json"

    projects = _load_json(projects_db)
    convs    = _load_json(conversations)

    client_projects = [p for p in projects if p.get("client_id") == client_id] if client_id else []

    # Active project = first "En cours" or first project
    active = next((p for p in client_projects if p.get("status") == "En cours"), None)
    if not active and client_projects:
        active = client_projects[0]

    # Unread messages for this client
    unread = 0
    if client_id:
        conv = next((c for c in convs if c.get("client_id") == client_id), None)
        if conv:
            unread = conv.get("unread_client", 0)

    return JSONResponse(content={
        "project_name":     active["name"] if active else None,
        "project_progress": active["progress"] if active else 0,
        "project_status":   active["status"] if active else None,
        "messages_unread":  unread,
    })
