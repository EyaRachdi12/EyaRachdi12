"""
POST /api/generate-video-luma
Generate a photorealistic architectural video using HuggingFace zeroscope_v2_576w.
Free with a HF token — no paid plan needed.
"""

import os
import re
import base64
import requests
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

HF_MODEL_URL = "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w"


def _get_hf_token() -> str:
    load_dotenv(override=True)
    return os.getenv("HF_API_TOKEN", "")


def _check_token() -> str:
    token = _get_hf_token()
    if not token:
        raise HTTPException(
            status_code=503,
            detail="HF_API_TOKEN non configuré. Ajoutez-le dans archi-platform/backend/.env",
        )
    return token


class VideoRequest(BaseModel):
    description: str
    style:       str = "contemporain"
    duration:    str = "5s"


# ── Prompt builder ────────────────────────────────────────────────────────────
STYLE_PROMPTS = {
    "contemporain":  "modern contemporary architecture, clean lines, large windows, concrete and wood",
    "minimaliste":   "minimalist architecture, white walls, open spaces, natural light",
    "haussmannien":  "Haussmann style architecture, ornate facade, stone, classic French",
    "industriel":    "industrial loft architecture, exposed brick, metal beams, urban",
    "scandinave":    "Scandinavian architecture, wood, white, cozy, natural materials",
    "méditerranéen": "Mediterranean architecture, terracotta, arches, warm colors, garden",
    "bioclimatique": "bioclimatic sustainable architecture, green roof, solar panels, nature",
    "villa":         "luxury villa architecture, pool, garden, modern design",
}

ROOM_KEYWORDS = {
    "salon":         "spacious living room",
    "cuisine":       "modern kitchen",
    "chambre":       "bedroom",
    "salle de bain": "bathroom",
    "terrasse":      "terrace with garden view",
    "bureau":        "home office",
    "piscine":       "swimming pool",
    "jardin":        "landscaped garden",
}


def build_prompt(description: str, style: str) -> str:
    desc_lower  = description.lower()
    style_desc  = STYLE_PROMPTS.get(style, STYLE_PROMPTS["contemporain"])
    rooms_en    = [en for fr, en in ROOM_KEYWORDS.items() if fr in desc_lower]
    surfaces    = re.findall(r"(\d+)\s*m²", description)
    surface_str = f"{surfaces[0]}m² total area, " if surfaces else ""
    rooms_str   = ", ".join(rooms_en[:3]) if rooms_en else "living spaces"

    return (
        f"cinematic architectural visualization, {style_desc}, "
        f"featuring {rooms_str}, {surface_str}"
        f"photorealistic rendering, smooth camera walkthrough, "
        f"golden hour lighting, high quality materials, 4K, no people"
    )


@router.post("/generate-video-luma")
async def generate_video_luma(body: VideoRequest):
    token  = _check_token()
    prompt = build_prompt(body.description, body.style)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }
    payload = {
        "inputs": prompt,
        "parameters": {
            "num_frames":          24,
            "num_inference_steps": 25,
            "height":              320,
            "width":               576,
        },
    }

    try:
        r = requests.post(HF_MODEL_URL, headers=headers, json=payload, timeout=180)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Erreur réseau HuggingFace: {e}")

    # Model may be loading — return friendly message
    if r.status_code == 503:
        detail = r.json() if r.headers.get("content-type","").startswith("application/json") else {}
        wait   = detail.get("estimated_time", 30)
        raise HTTPException(
            status_code=503,
            detail=f"Le modèle est en cours de chargement, réessayez dans {int(wait)} secondes.",
        )

    if r.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"HuggingFace API error {r.status_code}: {r.text[:300]}",
        )

    content_type = r.headers.get("content-type", "")
    if "video" in content_type or len(r.content) > 10_000:
        video_b64     = base64.b64encode(r.content).decode()
        video_data_uri = f"data:video/mp4;base64,{video_b64}"
        return JSONResponse(content={
            "status":          "completed",
            "video_url":       video_data_uri,
            "generation_id":   "hf-zeroscope",
            "prompt":          prompt,
            "style":           body.style,
            "provider":        "huggingface_zeroscope",
            "thumbnail_url":   None,
        })

    raise HTTPException(status_code=500, detail=f"Réponse inattendue du modèle: {r.text[:200]}")


@router.get("/video-luma-status/{generation_id}")
async def luma_status(generation_id: str):
    return JSONResponse(content={
        "status":    "completed",
        "video_url": None,
        "progress":  100,
    })


@router.get("/luma-credits")
async def luma_credits():
    token = _get_hf_token()
    return JSONResponse(content={
        "provider": "HuggingFace (free)",
        "model":    "zeroscope_v2_576w",
        "credits":  "unlimited (free tier)",
        "token_set": bool(token),
    })
