"""
Messages API — real-time conversation between architect and client.

GET  /api/messages/{conversation_id}     — get messages
POST /api/messages/{conversation_id}     — send a message
GET  /api/conversations                  — list all conversations
POST /api/conversations                  — create a conversation
"""

import json
import time
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

DB_DIR = Path(__file__).parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
CONV_DB = DB_DIR / "conversations.json"
MSG_DB  = DB_DIR / "messages.json"


# ── Helpers ───────────────────────────────────────────────────────────────────
def _load_conversations() -> list:
    if not CONV_DB.exists():
        # Start empty — conversations created when clients register
        _save_conversations([])
        return []
    with open(CONV_DB, encoding="utf-8") as f:
        return json.load(f)


def _save_conversations(data: list):
    with open(CONV_DB, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _load_messages(conv_id: str) -> list:
    msg_file = DB_DIR / f"messages_{conv_id}.json"
    if not msg_file.exists():
        # Seed with demo messages for conv_1
        if conv_id == "conv_1":
            demo = [
                {"id": "m1", "conv_id": conv_id, "sender_role": "architect", "sender": "Jean-Marc Leblanc", "text": "Bonjour ! J'ai bien reçu votre brief. Votre projet est très intéressant. Je commence les premières esquisses.", "time": "28 Avr, 09:15", "timestamp": 1714294500},
                {"id": "m2", "conv_id": conv_id, "sender_role": "client",    "sender": "M. Dupont",         "text": "Merci ! On est très enthousiastes. Est-ce qu'on peut avoir une cuisine vraiment ouverte sur le salon ?", "time": "28 Avr, 10:30", "timestamp": 1714298600},
                {"id": "m3", "conv_id": conv_id, "sender_role": "architect", "sender": "Jean-Marc Leblanc", "text": "Absolument ! C'est même ce que je recommande. Ça va apporter beaucoup de luminosité. Je vous envoie le premier plan demain.", "time": "28 Avr, 11:00", "timestamp": 1714300800},
                {"id": "m4", "conv_id": conv_id, "sender_role": "client",    "sender": "M. Dupont",         "text": "Super ! Et pour la terrasse, on aimerait qu'elle soit accessible directement depuis le salon.", "time": "29 Avr, 14:20", "timestamp": 1714394400},
                {"id": "m5", "conv_id": conv_id, "sender_role": "architect", "sender": "Jean-Marc Leblanc", "text": "J'ai révisé le plan selon vos retours. La cuisine est maintenant ouverte sur le salon. Pouvez-vous valider ?", "time": "1 Mai, 09:00", "timestamp": 1746086400},
            ]
            _save_messages(conv_id, demo)
            return demo
        return []
    with open(msg_file, encoding="utf-8") as f:
        return json.load(f)


def _save_messages(conv_id: str, data: list):
    msg_file = DB_DIR / f"messages_{conv_id}.json"
    with open(msg_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ── Models ────────────────────────────────────────────────────────────────────
class SendMessage(BaseModel):
    text:        str
    sender:      str
    sender_role: str  # "architect" or "client"
    image_url:   Optional[str] = None
    image_name:  Optional[str] = None


class CreateConversation(BaseModel):
    project:      str
    architect_id: str
    architect:    str
    client_id:    str
    client:       str


# ── Routes ────────────────────────────────────────────────────────────────────
@router.get("/conversations")
def list_conversations(role: str = "", user_id: str = ""):
    convs = _load_conversations()
    if role == "architect" and user_id:
        convs = [c for c in convs if c["architect_id"] == user_id]
    elif role == "client" and user_id:
        convs = [c for c in convs if c["client_id"] == user_id]
    return JSONResponse(content={"conversations": convs})


@router.post("/conversations")
def create_conversation(body: CreateConversation):
    convs  = _load_conversations()
    new_id = f"conv_{uuid.uuid4().hex[:8]}"
    conv   = {
        "id":            new_id,
        "project":       body.project,
        "architect_id":  body.architect_id,
        "architect":     body.architect,
        "client_id":     body.client_id,
        "client":        body.client,
        "last_message":  "",
        "last_time":     "Maintenant",
        "unread_client": 0,
        "unread_arch":   0,
    }
    convs.append(conv)
    _save_conversations(convs)
    return JSONResponse(content=conv, status_code=201)


@router.get("/messages/{conv_id}")
def get_messages(conv_id: str):
    convs = _load_conversations()
    conv  = next((c for c in convs if c["id"] == conv_id), None)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation non trouvée")
    messages = _load_messages(conv_id)
    return JSONResponse(content={"messages": messages, "conversation": conv})


@router.post("/messages/{conv_id}")
def send_message(conv_id: str, body: SendMessage):
    if not body.text.strip() and not body.image_url:
        raise HTTPException(status_code=400, detail="Message vide")

    messages = _load_messages(conv_id)
    now      = time.time()
    msg      = {
        "id":          f"msg_{uuid.uuid4().hex[:8]}",
        "conv_id":     conv_id,
        "sender_role": body.sender_role,
        "sender":      body.sender,
        "text":        body.text.strip(),
        "time":        "Maintenant",
        "timestamp":   int(now),
    }
    
    # Add image fields if present
    if body.image_url:
        msg["image_url"] = body.image_url
    if body.image_name:
        msg["image_name"] = body.image_name
    
    messages.append(msg)
    _save_messages(conv_id, messages)

    # Update conversation last message
    convs = _load_conversations()
    for conv in convs:
        if conv["id"] == conv_id:
            # Show image indicator if message has image
            if body.image_url:
                conv["last_message"] = f"📎 {body.image_name or 'Image'}" if not body.text.strip() else body.text[:60]
            else:
                conv["last_message"] = body.text[:60]
            conv["last_time"]    = "Maintenant"
            if body.sender_role == "architect":
                conv["unread_client"] = conv.get("unread_client", 0) + 1
            else:
                conv["unread_arch"] = conv.get("unread_arch", 0) + 1
            break
    _save_conversations(convs)

    return JSONResponse(content=msg, status_code=201)


@router.put("/messages/{conv_id}/read")
def mark_read(conv_id: str, role: str = "client"):
    convs = _load_conversations()
    for conv in convs:
        if conv["id"] == conv_id:
            if role == "client":
                conv["unread_client"] = 0
            else:
                conv["unread_arch"] = 0
            break
    _save_conversations(convs)
    return JSONResponse(content={"status": "ok"})
