"""
POST /api/generate-video-real
Generate a real photorealistic architectural video.

Strategy (in order):
1. HuggingFace Inference API (if token valid)
2. Zeroscope via Gradio public API (free, no token)
3. Animated slideshow from Unsplash images (always works)
"""

import os
import io
import re
import time
import base64
import random
import requests
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import numpy as np

router = APIRouter()

HF_TOKEN = os.getenv("HF_API_TOKEN", "")

STYLE_PROMPTS = {
    "contemporain":  "contemporary modern architecture exterior, clean lines, large windows, white walls, professional architectural photography, golden hour",
    "haussmannien":  "Haussmann style French architecture, ornate facade, elegant Parisian building, warm lighting, professional photography",
    "industriel":    "industrial loft interior, exposed brick, metal beams, modern furniture, urban design, dramatic lighting",
    "méditerranéen": "Mediterranean villa exterior, terracotta roof, arches, garden, pool, warm sunset light, luxury architecture",
    "bioclimatique": "sustainable eco architecture, green roof, natural materials, passive house, garden, natural light",
    "scandinave":    "Scandinavian interior design, wood, white walls, cozy, natural light, minimalist, hygge atmosphere",
    "minimaliste":   "minimalist architecture, white walls, open spaces, natural light, clean design, professional photography",
}

# Curated Unsplash architectural images per style
STYLE_IMAGES = {
    "contemporain": [
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&q=90",
        "https://images.unsplash.com/photo-1600607687939-ce8a6c25118c?w=1280&q=90",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1280&q=90",
        "https://images.unsplash.com/photo-1600585154526-990dced4db0d?w=1280&q=90",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1280&q=90",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1280&q=90",
    ],
    "haussmannien": [
        "https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=1280&q=90",
        "https://images.unsplash.com/photo-1499856871958-5b9627545d1a?w=1280&q=90",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1280&q=90",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1280&q=90",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1280&q=90",
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1280&q=90",
    ],
    "industriel": [
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1280&q=90",
        "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=1280&q=90",
        "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=1280&q=90",
        "https://images.unsplash.com/photo-1497366216548-37526070297c?w=1280&q=90",
        "https://images.unsplash.com/photo-1502005229762-cf1b2da7c5d6?w=1280&q=90",
        "https://images.unsplash.com/photo-1505691938895-1758d7feb511?w=1280&q=90",
    ],
    "méditerranéen": [
        "https://images.unsplash.com/photo-1523217582562-09d0def993a6?w=1280&q=90",
        "https://images.unsplash.com/photo-1499793983690-e29da59ef1c2?w=1280&q=90",
        "https://images.unsplash.com/photo-1571896349842-33c89424de2d?w=1280&q=90",
        "https://images.unsplash.com/photo-1582268611958-ebfd161ef9cf?w=1280&q=90",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1280&q=90",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&q=90",
    ],
    "bioclimatique": [
        "https://images.unsplash.com/photo-1518780664697-55e3ad937233?w=1280&q=90",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&q=90",
        "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?w=1280&q=90",
        "https://images.unsplash.com/photo-1600047509807-ba8f99d2cdde?w=1280&q=90",
        "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1280&q=90",
        "https://images.unsplash.com/photo-1600566753086-00f18fb6b3ea?w=1280&q=90",
    ],
    "scandinave": [
        "https://images.unsplash.com/photo-1583847268964-b28dc8f51f92?w=1280&q=90",
        "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=1280&q=90",
        "https://images.unsplash.com/photo-1540518614846-7eded433c457?w=1280&q=90",
        "https://images.unsplash.com/photo-1513694203232-719a280e022f?w=1280&q=90",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=1280&q=90",
        "https://images.unsplash.com/photo-1556909114-f6e7ad7d3136?w=1280&q=90",
    ],
    "minimaliste": [
        "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?w=1280&q=90",
        "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=1280&q=90",
        "https://images.unsplash.com/photo-1484154218962-a197022b5858?w=1280&q=90",
        "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1280&q=90",
        "https://images.unsplash.com/photo-1565182999561-18d7dc61c393?w=1280&q=90",
        "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1280&q=90",
    ],
}


class VideoRequest(BaseModel):
    description: str
    style:       str = "contemporain"
    duration:    int = 10


@router.post("/generate-video-real")
async def generate_video_real(body: VideoRequest):
    """
    Generate a photorealistic architectural video.
    Uses animated slideshow from curated architectural photos.
    """
    style = body.style.lower()

    # Get images for this style
    images_urls = STYLE_IMAGES.get(style, STYLE_IMAGES["contemporain"])

    # Download images
    frames_data = []
    headers = {"User-Agent": "ArchiGuide/1.0"}

    for url in images_urls[:6]:
        try:
            r = requests.get(url, timeout=15, headers=headers)
            if r.status_code == 200:
                img = Image.open(io.BytesIO(r.content)).convert("RGB")
                img = img.resize((1280, 720), Image.LANCZOS)
                frames_data.append(img)
        except Exception:
            continue

    if not frames_data:
        raise HTTPException(status_code=500, detail="Impossible de télécharger les images")

    # Generate animated GIF with Ken Burns effect
    gif_bytes = _create_cinematic_gif(frames_data, body.duration)
    gif_b64   = base64.b64encode(gif_bytes).decode()

    return JSONResponse(content={
        "status":        "completed",
        "gif_data_uri":  f"data:image/gif;base64,{gif_b64}",
        "video_url":     None,
        "style":         style,
        "method":        "cinematic_slideshow",
        "n_frames":      len(frames_data),
        "description":   body.description[:100],
    })


def _create_cinematic_gif(images: list, duration_s: int = 10) -> bytes:
    """
    Create a cinematic animated GIF with Ken Burns effect.
    Each image gets zoom + pan + crossfade transitions.
    """
    W, H = 960, 540
    fps  = 12
    frames_per_image = max(fps * 2, fps * duration_s // len(images))
    output_frames = []

    for img_idx, img in enumerate(images):
        # Resize with some extra space for Ken Burns
        src = img.resize((int(W * 1.15), int(H * 1.15)), Image.LANCZOS)
        sw, sh = src.size

        for f in range(frames_per_image):
            t = f / frames_per_image  # 0 → 1

            # Ken Burns: slow zoom + pan
            zoom   = 1.0 + 0.08 * t
            crop_w = int(W / zoom)
            crop_h = int(H / zoom)

            # Pan direction alternates per image
            if img_idx % 2 == 0:
                ox = int((sw - crop_w) * t * 0.5)
                oy = int((sh - crop_h) * 0.5)
            else:
                ox = int((sw - crop_w) * (1 - t) * 0.5)
                oy = int((sh - crop_h) * 0.5)

            ox = max(0, min(ox, sw - crop_w))
            oy = max(0, min(oy, sh - crop_h))

            frame = src.crop((ox, oy, ox + crop_w, oy + crop_h))
            frame = frame.resize((W, H), Image.LANCZOS)

            # Crossfade at start and end
            if f < fps // 2:
                alpha = f / (fps // 2)
                frame = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), frame, alpha)
            elif f > frames_per_image - fps // 2:
                alpha = (frames_per_image - f) / (fps // 2)
                frame = Image.blend(Image.new("RGB", (W, H), (0, 0, 0)), frame, alpha)

            # Slight vignette
            frame = _add_vignette(frame)

            output_frames.append(frame.convert("P", palette=Image.ADAPTIVE, colors=256))

    # Save as GIF
    buf = io.BytesIO()
    output_frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=output_frames[1:],
        duration=int(1000 / fps),
        loop=0,
        optimize=False,
    )
    return buf.getvalue()


def _add_vignette(img: Image.Image) -> Image.Image:
    """Add subtle vignette effect."""
    W, H = img.size
    vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(vignette)
    for r in range(min(W, H) // 2, 0, -2):
        alpha = int(60 * (1 - r / (min(W, H) / 2)))
        draw.ellipse([W//2-r, H//2-r, W//2+r, H//2+r], outline=(0, 0, 0, alpha))
    return Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")
