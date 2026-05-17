"""
POST /api/generate-sketches
Generate architectural sketches using HuggingFace Inference API.
Falls back to Unsplash architectural photos if HF is unavailable.
"""

import os
import io
import base64
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List

router = APIRouter()

HF_TOKEN = os.getenv("HF_API_TOKEN", "")

# Style → English prompt mapping for better image generation
STYLE_PROMPTS = {
    "contemporain":  "contemporary modern architecture, clean lines, large windows, white walls, minimalist interior design, professional architectural rendering",
    "minimaliste":   "minimalist architecture, white walls, open spaces, natural light, simple clean design, architectural photography",
    "industriel":    "industrial loft architecture, exposed brick walls, metal beams, urban design, warehouse conversion, interior design",
    "scandinave":    "Scandinavian architecture, wood materials, cozy interior, white and natural tones, Nordic design, hygge",
    "mediterraneen": "Mediterranean architecture, terracotta tiles, arched windows, warm colors, courtyard, villa design",
    "bioclimatique": "bioclimatic sustainable architecture, green roof, solar panels, natural materials, eco-friendly design, passive house",
}

SKETCH_SUBJECTS = [
    ("Façade principale",    "exterior facade of a {style} house, front view, professional architectural visualization"),
    ("Salon / Séjour",       "interior living room {style} design, comfortable sofa, natural light, architectural photography"),
    ("Cuisine ouverte",      "modern open kitchen {style}, island counter, warm lighting, interior design"),
    ("Chambre principale",   "master bedroom {style} interior, large windows, elegant design, architectural photography"),
    ("Terrasse extérieure",  "outdoor terrace {style}, garden view, evening light, architectural visualization"),
    ("Salle de bain",        "modern bathroom {style}, clean design, natural stone, architectural photography"),
]

# Fallback: Unsplash architectural photos (free, no API key needed)
UNSPLASH_FALLBACKS = {
    "contemporain": [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&q=80",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=600&q=80",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600&q=80",
        "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=600&q=80",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&q=80",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80",
    ],
    "minimaliste": [
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=600&q=80",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=600&q=80",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=600&q=80",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&q=80",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=600&q=80",
        "https://images.unsplash.com/photo-1565182999561-18d7dc61c393?w=600&q=80",
    ],
    "industriel": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=600&q=80",
        "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=600&q=80",
        "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=600&q=80",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=600&q=80",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=600&q=80",
    ],
    "scandinave": [
        "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=600&q=80",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=600&q=80",
        "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=600&q=80",
        "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=600&q=80",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=600&q=80",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=600&q=80",
    ],
    "mediterraneen": [
        "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=600&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&q=80",
        "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=600&q=80",
        "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=600&q=80",
        "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=600&q=80",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=600&q=80",
    ],
    "bioclimatique": [
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=600&q=80",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=600&q=80",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=600&q=80",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=600&q=80",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=600&q=80",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=600&q=80",
    ],
}


class SketchRequest(BaseModel):
    style: str = "contemporain"
    n:     int = 6


@router.post("/generate-sketches")
async def generate_sketches(body: SketchRequest):
    """
    Generate architectural sketches for a given style.
    Uses HuggingFace if token available, otherwise Unsplash fallback.
    """
    style = body.style.lower()
    n     = min(body.n, 6)

    # Try HuggingFace first
    if HF_TOKEN:
        sketches = await _try_huggingface(style, n)
        if sketches:
            return JSONResponse(content={"sketches": sketches, "method": "huggingface"})

    # Fallback: Unsplash architectural photos
    sketches = _unsplash_fallback(style, n)
    return JSONResponse(content={"sketches": sketches, "method": "unsplash"})


async def _try_huggingface(style: str, n: int) -> list:
    """Try to generate images via HuggingFace Inference API."""
    style_prompt = STYLE_PROMPTS.get(style, STYLE_PROMPTS["contemporain"])
    sketches = []

    for i, (title, subject_template) in enumerate(SKETCH_SUBJECTS[:n]):
        subject = subject_template.format(style=style_prompt.split(",")[0])
        prompt  = f"{subject}, {style_prompt}, high quality, 4K, professional photography"

        try:
            headers = {
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type":  "application/json",
            }
            payload = {
                "inputs": prompt,
                "parameters": {"num_inference_steps": 20, "guidance_scale": 7.5},
            }
            r = requests.post(
                "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1",
                headers=headers,
                json=payload,
                timeout=30,
            )
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                img_b64 = base64.b64encode(r.content).decode()
                sketches.append({
                    "id":       i + 1,
                    "title":    title,
                    "prompt":   prompt[:80],
                    "image_b64": f"data:image/jpeg;base64,{img_b64}",
                    "image_url": None,
                    "liked":    False,
                })
            else:
                return []  # HF not available, use fallback
        except Exception:
            return []

    return sketches


def _unsplash_fallback(style: str, n: int) -> list:
    """Return Unsplash architectural photos as fallback."""
    urls = UNSPLASH_FALLBACKS.get(style, UNSPLASH_FALLBACKS["contemporain"])
    sketches = []
    for i, (title, subject) in enumerate(SKETCH_SUBJECTS[:n]):
        url = urls[i % len(urls)]
        sketches.append({
            "id":        i + 1,
            "title":     title,
            "prompt":    subject.replace("{style}", style),
            "image_b64": None,
            "image_url": url,
            "liked":     False,
        })
    return sketches
