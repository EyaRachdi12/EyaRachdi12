"""
POST /api/generate-video
Generates an animated walkthrough from a floor plan image.

Strategy (in order of availability):
  1. Replicate SVD — if REPLICATE_API_TOKEN has credit
  2. HuggingFace AnimateDiff — if HF_API_TOKEN is valid
  3. Local GIF generation — always works, no API needed
"""

import io
import os
import time
import base64
import math
import requests
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from dotenv import load_dotenv

router = APIRouter()

REPLICATE_API_URL = "https://api.replicate.com/v1/predictions"
SVD_VERSION       = "3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"


def _get_tokens():
    load_dotenv(override=True)
    return os.getenv("REPLICATE_API_TOKEN", ""), os.getenv("HF_API_TOKEN", "")
SVD_VERSION         = "3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438"


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 1 — Replicate SVD
# ══════════════════════════════════════════════════════════════════════════════
def _try_replicate(image: Image.Image, quality: str) -> dict | None:
    REPLICATE_API_TOKEN, _ = _get_tokens()
    if not REPLICATE_API_TOKEN:
        return None
    try:
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        b64      = base64.b64encode(buf.getvalue()).decode()
        data_uri = f"data:image/png;base64,{b64}"
        motion   = {"draft": 80, "standard": 127, "high": 180}.get(quality, 127)
        headers  = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type":  "application/json",
        }
        payload = {
            "version": SVD_VERSION,
            "input": {
                "input_image":       data_uri,
                "video_length":      "25_frames_with_svd_xt",
                "sizing_strategy":   "maintain_aspect_ratio",
                "frames_per_second": 6,
                "motion_bucket_id":  motion,
                "cond_aug":          0.02,
                "decoding_t":        14,
            },
        }
        r = requests.post(REPLICATE_API_URL, headers=headers, json=payload, timeout=30)
        if r.status_code != 201:
            return None   # no credit or error → fall through

        pred_id = r.json().get("id")
        # Poll
        for _ in range(90):
            time.sleep(4)
            pr = requests.get(f"{REPLICATE_API_URL}/{pred_id}", headers=headers, timeout=15)
            data = pr.json()
            if data.get("status") == "succeeded":
                output = data.get("output")
                url    = (output[0] if isinstance(output, list) else output)
                return {"method": "replicate_svd", "video_url": url, "type": "mp4"}
            if data.get("status") == "failed":
                return None
        return None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 2 — HuggingFace text-to-video (zeroscope)
# ══════════════════════════════════════════════════════════════════════════════
def _try_huggingface(image: Image.Image, quality: str) -> dict | None:
    _, HF_API_TOKEN = _get_tokens()
    if not HF_API_TOKEN:
        return None
    try:
        # Use zeroscope_v2_576w — free tier
        API_URL = "https://api-inference.huggingface.co/models/cerspense/zeroscope_v2_576w"
        headers = {"Authorization": f"Bearer {HF_API_TOKEN}"}
        prompt  = (
            "architectural floor plan walkthrough, interior design, "
            "smooth camera movement, professional visualization, "
            "modern architecture, high quality"
        )
        payload = {"inputs": prompt, "parameters": {"num_frames": 16}}
        r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
        if r.status_code == 200 and r.headers.get("content-type", "").startswith("video"):
            video_b64 = base64.b64encode(r.content).decode()
            return {
                "method":    "huggingface_zeroscope",
                "video_b64": video_b64,
                "type":      "mp4",
            }
        return None
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════════════
# Strategy 3 — Local animated GIF (always works)
# ══════════════════════════════════════════════════════════════════════════════
def _generate_local_gif(image: Image.Image, quality: str) -> dict:
    """
    Generate an animated GIF simulating a floor plan walkthrough.
    Uses zoom, pan, and highlight effects — no GPU needed.
    """
    n_frames = {"draft": 16, "standard": 24, "high": 32}.get(quality, 24)
    W, H     = 576, 324   # 16:9

    # Resize source image
    src = image.convert("RGBA").resize((W, H), Image.LANCZOS)
    frames = []

    for i in range(n_frames):
        t      = i / n_frames          # 0 → 1
        frame  = src.copy().convert("RGB")

        # ── Effect 1: Slow zoom in (Ken Burns) ──────────────────────────────
        zoom   = 1.0 + 0.15 * t        # 1.0 → 1.15
        new_w  = int(W / zoom)
        new_h  = int(H / zoom)
        left   = (W - new_w) // 2
        top    = (H - new_h) // 2
        frame  = frame.crop((left, top, left + new_w, top + new_h))
        frame  = frame.resize((W, H), Image.LANCZOS)

        # ── Effect 2: Subtle pan (left → right) ─────────────────────────────
        pan_x  = int(20 * math.sin(t * math.pi))
        if pan_x != 0:
            frame = frame.transform(
                (W, H), Image.AFFINE,
                (1, 0, pan_x, 0, 1, 0),
                resample=Image.BILINEAR,
            )

        # ── Effect 3: Brightness pulse (simulate lighting) ──────────────────
        brightness = 1.0 + 0.08 * math.sin(t * math.pi * 2)
        frame = ImageEnhance.Brightness(frame).enhance(brightness)

        # ── Effect 4: Highlight scan line ───────────────────────────────────
        overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw    = ImageDraw.Draw(overlay)
        scan_y  = int(t * H)
        draw.line([(0, scan_y), (W, scan_y)], fill=(201, 169, 110, 60), width=2)
        frame   = Image.alpha_composite(frame.convert("RGBA"), overlay).convert("RGB")

        # ── Effect 5: Vignette ───────────────────────────────────────────────
        vignette = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        vd       = ImageDraw.Draw(vignette)
        for r in range(min(W, H) // 2, 0, -1):
            alpha = int(80 * (1 - r / (min(W, H) / 2)))
            vd.ellipse(
                [W//2 - r, H//2 - r, W//2 + r, H//2 + r],
                outline=(0, 0, 0, alpha),
            )
        frame = Image.alpha_composite(frame.convert("RGBA"), vignette).convert("RGB")

        frames.append(frame)

    # Save as GIF
    buf = io.BytesIO()
    frames[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=120,    # ms per frame
        loop=0,
        optimize=True,
    )
    gif_bytes = buf.getvalue()
    gif_b64   = base64.b64encode(gif_bytes).decode()

    return {
        "method":    "local_gif",
        "gif_b64":   gif_b64,
        "gif_data_uri": f"data:image/gif;base64,{gif_b64}",
        "type":      "gif",
        "n_frames":  n_frames,
        "size":      f"{W}×{H}",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Route
# ══════════════════════════════════════════════════════════════════════════════
@router.post("/generate-video")
async def generate_video(
    file:     UploadFile = File(...),
    model:    str        = Form("diffusion"),
    duration: int        = Form(25),
    quality:  str        = Form("standard"),
):
    """
    Generate animated visualization from floor plan.
    Tries Replicate → HuggingFace → Local GIF (fallback).
    """
    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")
        image.thumbnail((1024, 576))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible de lire l'image: {e}")

    # Try strategies in order
    result = None

    if model in ("diffusion", "nerf"):
        result = _try_replicate(image, quality)

    if result is None:
        result = _try_huggingface(image, quality)

    if result is None:
        result = _generate_local_gif(image, quality)

    return JSONResponse(content={
        "status":   "succeeded",
        "method":   result["method"],
        "type":     result["type"],
        "video_url":     result.get("video_url"),
        "gif_data_uri":  result.get("gif_data_uri"),
        "quality":  quality,
        "metrics":  {"n_frames": result.get("n_frames", 25)},
    })


@router.get("/video-status/{prediction_id}")
async def video_status(prediction_id: str):
    REPLICATE_API_TOKEN, _ = _get_tokens()
    if not REPLICATE_API_TOKEN:
        raise HTTPException(status_code=503, detail="Replicate non configuré.")
    headers = {"Authorization": f"Token {REPLICATE_API_TOKEN}"}
    r = requests.get(f"{REPLICATE_API_URL}/{prediction_id}", headers=headers, timeout=15)
    r.raise_for_status()
    data      = r.json()
    output    = data.get("output")
    video_url = (output[0] if isinstance(output, list) else output) if output else None
    return JSONResponse(content={
        "status":    data.get("status"),
        "video_url": video_url,
        "error":     data.get("error"),
    })
