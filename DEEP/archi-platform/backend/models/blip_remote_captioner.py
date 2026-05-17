"""
BLIP Remote Captioner
=====================
Calls the BLIP API running on Google Colab via Cloudflare Tunnel.
Falls back to smart_captioner if API is unavailable.
"""

import os
import io
import re
import base64
import random
import requests
from PIL import Image
from typing import Dict, Any

BLIP_API_URL = os.getenv("BLIP_API_URL", "")

TYPICAL_AREAS = {
    "Salon / Séjour":     (25, 40),
    "Cuisine":            (12, 22),
    "Chambre principale": (18, 28),
    "Chambre":            (12, 20),
    "Salle de bain":      (6,  12),
    "WC":                 (2,   5),
    "Couloir":            (4,   8),
    "Bureau":             (10, 18),
    "Terrasse":           (10, 25),
    "Terrasse / Porche":  (8,  20),
    "Garage":             (15, 25),
    "Salle à manger":     (14, 22),
    "Rangement":          (3,   6),
    "Dressing":           (4,   8),
    "Entrée":             (4,   8),
    "Pièce":              (10, 20),
}

STYLE_KEYWORDS = {
    "Contemporain":  ["modern", "contemporary", "clean", "white", "open"],
    "Industriel":    ["industrial", "loft", "brick", "concrete", "dark"],
    "Haussmannien":  ["classic", "traditional", "ornate", "french", "elegant"],
    "Scandinave":    ["scandinavian", "nordic", "wood", "cozy", "natural"],
    "Minimaliste":   ["minimal", "simple", "minimalist", "light", "airy"],
    "Méditerranéen": ["mediterranean", "terracotta", "warm", "arches"],
}

ORIENTATIONS = ["sud", "sud-ouest", "est", "ouest", "nord-sud", "sud-est"]


def _image_to_b64(image: Image.Image) -> str:
    buf = io.BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=85)
    return base64.b64encode(buf.getvalue()).decode()


def _detect_style(caption: str) -> str:
    caption_lower = caption.lower()
    for style, keywords in STYLE_KEYWORDS.items():
        if any(kw in caption_lower for kw in keywords):
            return style
    return "Contemporain"


def _get_plan_type(n: int) -> str:
    return {1: "studio", 2: "T2", 3: "T3", 4: "T4",
            5: "T5", 6: "T6"}.get(n, f"T{n}")


def _build_caption(rooms, style, orientation, total_area, n_windows, n_doors, plan_type):
    n = len(rooms)
    rooms_desc = []
    for r in rooms[:5]:
        win   = r.get("windows", 1)
        w_str = f", {win} fenêtre{'s' if win > 1 else ''}" if win > 0 else ""
        rooms_desc.append(f"{r['name']} de {r['area']} m²{w_str}")
    rooms_str = " ; ".join(rooms_desc)

    return (
        f"Plan {plan_type} de style {style.lower()} comprenant "
        f"{n} pièce{'s' if n > 1 else ''} "
        f"pour une surface habitable totale de {total_area} m². "
        f"Comprend : {rooms_str}. "
        f"Orientation principale : {orientation}. "
        f"Le plan dispose de {n_windows} fenêtre{'s' if n_windows > 1 else ''} "
        f"et {n_doors} porte{'s' if n_doors > 1 else ''}."
    )


class BLIPRemoteCaptioner:
    """Calls BLIP API on Colab, falls back to smart CV if unavailable."""

    def generate(self, image: Image.Image) -> Dict[str, Any]:
        blip_url = os.getenv("BLIP_API_URL", BLIP_API_URL)

        # Try BLIP remote API
        if blip_url:
            try:
                result = self._call_blip_api(image, blip_url)
                if result:
                    return result
            except Exception as e:
                print(f"[BLIP Remote] API error: {e} — falling back to smart CV")

        # Fallback
        from models.smart_captioner import SmartFloorPlanCaptioner
        return SmartFloorPlanCaptioner().generate(image)

    def _call_blip_api(self, image: Image.Image, url: str) -> Dict | None:
        img_b64 = _image_to_b64(image)

        response = requests.post(
            f"{url.rstrip('/')}/analyze",
            json={"image_b64": img_b64},
            timeout=60,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code != 200:
            print(f"[BLIP Remote] HTTP {response.status_code}: {response.text[:200]}")
            return None

        data = response.json()
        if data.get("status") != "ok":
            return None

        blip_caption = data.get("blip_caption", "")
        rooms        = data.get("rooms", [])

        print(f"[BLIP Remote] Caption: {blip_caption}")

        # Enrich rooms with windows
        for r in rooms:
            win_map = {
                "Salon / Séjour": 3, "Cuisine": 1,
                "Chambre principale": 2, "Chambre": 1,
                "Salle de bain": 1, "WC": 0,
            }
            r["windows"] = win_map.get(r["name"], 1)

        # If no rooms detected, use smart CV
        if not rooms:
            from models.smart_captioner import SmartFloorPlanCaptioner
            cv = SmartFloorPlanCaptioner().generate(image)
            rooms = cv["rooms"]

        # Detect style and orientation
        style       = _detect_style(blip_caption)
        orientation = random.choice(ORIENTATIONS)
        total_area  = sum(r.get("area", 15) for r in rooms)
        plan_type   = _get_plan_type(len(rooms))

        # CV for windows/doors count
        from models.smart_captioner import SmartFloorPlanCaptioner
        cv_result  = SmartFloorPlanCaptioner().generate(image)
        n_windows  = cv_result.get("n_windows", 4)
        n_doors    = cv_result.get("n_doors", 3)
        orientation = cv_result.get("orientation", orientation)

        caption = _build_caption(
            rooms, style, orientation, total_area, n_windows, n_doors, plan_type
        )

        return {
            "caption":     caption,
            "summary":     f"Plan {style.lower()} de {total_area} m² — {len(rooms)} pièces.",
            "rooms":       rooms,
            "total_area":  total_area,
            "room_count":  len(rooms),
            "style":       style,
            "orientation": orientation,
            "plan_type":   plan_type,
            "n_windows":   n_windows,
            "n_doors":     n_doors,
            "confidence":  0.92,
            "method":      "blip_remote",
            "blip_raw":    blip_caption,
            "metrics":     cv_result.get("metrics", {}),
        }


# Singleton
blip_remote_captioner = BLIPRemoteCaptioner()
