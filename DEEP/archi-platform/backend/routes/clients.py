"""
GET  /api/clients        — list all clients
POST /api/clients        — create a client
GET  /api/clients/{id}   — get one client
PUT  /api/clients/{id}   — update a client
"""

import json
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Simple JSON file as database (no SQL needed for demo)
DB_PATH = Path(__file__).parent.parent / "data" / "clients_db.json"
DB_PATH.parent.mkdir(exist_ok=True)


def _load() -> list:
    if not DB_PATH.exists():
        # Start with empty list — clients are added when they register
        _save([])
        return []
    with open(DB_PATH, encoding="utf-8") as f:
        return json.load(f)


def _save(data: list):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class ClientCreate(BaseModel):
    name:         str
    email:        str
    project:      Optional[str] = ""
    phone:        Optional[str] = ""
    city:         Optional[str] = ""
    status:       Optional[str] = "Actif"
    project_type: Optional[str] = "Maison individuelle"


class ClientUpdate(BaseModel):
    name:         Optional[str] = None
    email:        Optional[str] = None
    project:      Optional[str] = None
    phone:        Optional[str] = None
    city:         Optional[str] = None
    status:       Optional[str] = None
    project_type: Optional[str] = None


@router.get("/clients")
def list_clients(search: str = "", status: str = ""):
    clients = _load()
    if search:
        s = search.lower()
        clients = [c for c in clients if s in c["name"].lower() or s in c["email"].lower()]
    if status and status != "all":
        clients = [c for c in clients if c["status"] == status]
    return JSONResponse(content={"clients": clients, "total": len(clients)})


@router.post("/clients")
def create_client(body: ClientCreate):
    clients = _load()
    new_id  = str(int(time.time()))
    avatar  = body.name[0].upper() if body.name else "?"
    client  = {
        "id":           new_id,
        "name":         body.name,
        "email":        body.email,
        "project":      body.project or "",
        "phone":        body.phone or "",
        "city":         body.city or "",
        "status":       body.status or "Actif",
        "project_type": body.project_type or "Maison individuelle",
        "since":        _current_month(),
        "projects":     1,
        "avatar":       avatar,
    }
    clients.append(client)
    _save(clients)
    return JSONResponse(content=client, status_code=201)


@router.get("/clients/{client_id}")
def get_client(client_id: str):
    clients = _load()
    client  = next((c for c in clients if c["id"] == client_id), None)
    if not client:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    return JSONResponse(content=client)


@router.put("/clients/{client_id}")
def update_client(client_id: str, body: ClientUpdate):
    clients = _load()
    idx     = next((i for i, c in enumerate(clients) if c["id"] == client_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="Client non trouvé")
    for field, value in body.model_dump(exclude_none=True).items():
        clients[idx][field] = value
    _save(clients)
    return JSONResponse(content=clients[idx])


@router.delete("/clients/{client_id}")
def delete_client(client_id: str):
    clients = _load()
    clients = [c for c in clients if c["id"] != client_id]
    _save(clients)
    return JSONResponse(content={"message": "Client supprimé"})


def _current_month() -> str:
    import datetime
    months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    now = datetime.datetime.now()
    return f"{months[now.month-1]} {now.year}"
