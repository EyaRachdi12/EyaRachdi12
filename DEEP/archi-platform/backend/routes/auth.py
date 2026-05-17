"""
Authentication routes
POST /api/auth/register  — create account
POST /api/auth/login     — login
GET  /api/auth/me        — get current user (by token)
"""

import json
import uuid
import hashlib
import time
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

DB_DIR   = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
USERS_DB = DB_DIR / "users.json"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_users() -> list:
    if not USERS_DB.exists():
        return []
    with open(USERS_DB, encoding="utf-8") as f:
        return json.load(f)


def _save_users(users: list):
    with open(USERS_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _generate_token(user_id: str) -> str:
    return hashlib.sha256(f"{user_id}{time.time()}".encode()).hexdigest()


def _current_month() -> str:
    import datetime
    months = ["Jan","Fév","Mar","Avr","Mai","Jun","Jul","Aoû","Sep","Oct","Nov","Déc"]
    now = datetime.datetime.now()
    return f"{months[now.month-1]} {now.year}"


# ── Models ────────────────────────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    name:       str
    email:      str
    password:   str
    role:       str  # "architect" or "client"
    specialty:  Optional[str] = ""
    city:       Optional[str] = ""
    project_type: Optional[str] = ""


class LoginRequest(BaseModel):
    email:    str
    password: str
    role:     str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/auth/register")
def register(body: RegisterRequest):
    users = _load_users()

    # Check if email already exists
    if any(u["email"] == body.email for u in users):
        raise HTTPException(status_code=409, detail="Email déjà utilisé")

    user_id = str(uuid.uuid4())
    token   = _generate_token(user_id)
    avatar  = body.name[0].upper() if body.name else "?"

    user = {
        "id":           user_id,
        "name":         body.name,
        "email":        body.email,
        "password":     _hash_password(body.password),
        "role":         body.role,
        "specialty":    body.specialty or "",
        "city":         body.city or "",
        "project_type": body.project_type or "",
        "avatar":       avatar,
        "token":        token,
        "created_at":   _current_month(),
        "status":       "Actif",
    }
    users.append(user)
    _save_users(users)

    # If client, also add to clients list for architects
    if body.role == "client":
        _add_to_clients_list(user)
        _create_conversation(user)

    # Return user without password
    safe_user = {k: v for k, v in user.items() if k != "password"}
    return JSONResponse(content=safe_user, status_code=201)


@router.post("/auth/login")
def login(body: LoginRequest):
    users = _load_users()
    user  = next(
        (u for u in users
         if u["email"] == body.email
         and u["password"] == _hash_password(body.password)
         and u["role"] == body.role),
        None
    )
    if not user:
        raise HTTPException(status_code=401, detail="Email, mot de passe ou rôle incorrect")

    # Refresh token
    user["token"] = _generate_token(user["id"])
    _save_users(users)

    safe_user = {k: v for k, v in user.items() if k != "password"}
    return JSONResponse(content=safe_user)


@router.get("/auth/users")
def list_users(role: str = ""):
    users = _load_users()
    if role:
        users = [u for u in users if u["role"] == role]
    safe = [{k: v for k, v in u.items() if k != "password"} for u in users]
    return JSONResponse(content={"users": safe, "total": len(safe)})


# ── Helper: sync client to clients list ──────────────────────────────────────
def _add_to_clients_list(user: dict):
    """When a client registers, add them to the architect's client list."""
    clients_db = DB_DIR / "clients_db.json"
    if clients_db.exists():
        with open(clients_db, encoding="utf-8") as f:
            clients = json.load(f)
    else:
        clients = []

    # Avoid duplicates
    if any(c.get("email") == user["email"] for c in clients):
        return

    clients.append({
        "id":       user["id"],
        "name":     user["name"],
        "email":    user["email"],
        "project":  user.get("project_type", ""),
        "phone":    "",
        "city":     user.get("city", ""),
        "status":   "Actif",
        "since":    user["created_at"],
        "projects": 0,
        "avatar":   user["avatar"],
    })

    with open(clients_db, "w", encoding="utf-8") as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


def _create_conversation(user: dict):
    """Create a conversation between the new client and the architect."""
    conv_db = DB_DIR / "conversations.json"
    if conv_db.exists():
        with open(conv_db, encoding="utf-8") as f:
            convs = json.load(f)
    else:
        convs = []

    # Avoid duplicates
    if any(c.get("client_id") == user["id"] for c in convs):
        return

    conv_id = f"conv_{user['id'][:8]}"
    conv = {
        "id":            conv_id,
        "project":       user.get("project_type", "Nouveau projet"),
        "architect_id":  "arch_1",
        "architect":     "Architecte",
        "client_id":     user["id"],
        "client":        user["name"],
        "last_message":  f"Nouveau client inscrit : {user['name']}",
        "last_time":     "Maintenant",
        "unread_client": 0,
        "unread_arch":   1,
    }
    convs.append(conv)

    with open(conv_db, "w", encoding="utf-8") as f:
        json.dump(convs, f, ensure_ascii=False, indent=2)

    # Add welcome message
    msg_file = DB_DIR / f"messages_{conv_id}.json"
    welcome = [{
        "id":          "msg_welcome",
        "conv_id":     conv_id,
        "sender_role": "architect",
        "sender":      "Architecte",
        "text":        f"Bonjour {user['name']} ! Bienvenue sur ArchiGuide. Je suis votre architecte. N'hésitez pas à me décrire votre projet.",
        "time":        "Maintenant",
        "timestamp":   int(time.time()),
    }]
    with open(msg_file, "w", encoding="utf-8") as f:
        json.dump(welcome, f, ensure_ascii=False, indent=2)
