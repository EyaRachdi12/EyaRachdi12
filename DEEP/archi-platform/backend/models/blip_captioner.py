"""
BLIP Floor Plan Captioner
=========================
Uses Salesforce/blip-image-captioning-base locally.
Model size: ~450MB — fits in 2GB RAM.

First run downloads the model from HuggingFace (~450MB).
Subsequent runs load from cache instantly.
"""

import os
import re
import torch
from PIL import Image
from typing import Dict, Any
from pathlib import Path

# Suppress TF warnings
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

MODEL_NAME = "Salesforce/blip-image-captioning-base"

# Room translation: English → French
EN_TO_FR = {
    "living room":    "Salon / Séjour",
    "sitting room":   "Salon / Séjour",
    "lounge":         "Salon / Séjour",
    "kitchen":        "Cuisine",
    "bedroom":        "Chambre",
    "master bedroom": "Chambre principale",
    "bathroom":       "Salle de bain",
    "toilet":         "WC",
    "wc":             "WC",
    "hallway":        "Couloir",
    "corridor":       "Couloir",
    "entrance":       "Entrée",
    "office":         "Bureau",
    "study":          "Bureau",
    "terrace":        "Terrasse",
    "balcony":        "Balcon",
    "porch":          "Terrasse / Porche",
    "garage":         "Garage",
    "dining room":    "Salle à manger",
    "dining":         "Salle à manger",
    "laundry":        "Buanderie",
    "storage":        "Rangement",
    "closet":         "Dressing",
    "dressing":       "Dressing",
    "room":           "Pièce",
}

STYLE_KEYWORDS = {
    "contemporain":  ["modern", "contemporary", "clean", "minimalist", "white"],
    "industriel":    ["industrial", "loft", "brick", "concrete", "dark"],
    "haussmannien":  ["classic", "traditional", "ornate", "french"],
    "scandinave":    ["scandinavian", "nordic", "wood", "cozy"],
    "minimaliste":   ["minimal", "simple", "open", "light"],
}

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
    "Buanderie":          (4,   8),
    "Dressing":           (4,   8),
    "Rangement":          (3,   6),
    "Entrée":             (4,   8),
    "Pièce":              (10, 20),
}


class BLIPCaptioner:
    """
    BLIP-based floor plan captioner.
    Generates English caption with BLIP, then enriches with CV analysis.
    """

    def __init__(self):
        self._model     = None
        self._processor = None
        self._loaded    = False
        self._loading   = False

    def _load(self):
        if self._loaded or self._loading:
            return
        self._loading = True
        try:
            from transformers import BlipProcessor, BlipForConditionalGeneration
            import warnings
            warnings.filterwarnings("ignore")

            print("[BLIP] Loading model (first run downloads ~450MB)...")
            self._processor = BlipProcessor.from_pretrained(MODEL_NAME)
            self._model     = BlipForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                dtype=torch.float32,
                low_cpu_mem_usage=True,
            )
            self._model.eval()
            self._loaded  = True
            self._loading = False
            print("[BLIP] ✅ Model loaded successfully")
        except Exception as e:
            self._loading = False
            print(f"[BLIP] ❌ Failed to load: {e}")

    def _generate_blip_caption(self, image: Image.Image) -> str:
        """Generate raw English caption using BLIP."""
        if not self._loaded:
            return ""
        try:
            # Conditional captioning — guide BLIP with architectural context
            prompts = [
                "a floor plan showing",
                "an architectural floor plan with",
                "a house floor plan containing",
            ]
            captions = []
            for prompt in prompts:
                inputs = self._processor(
                    image.convert("RGB"),
                    text=prompt,
                    return_tensors="pt",
                )
                with torch.no_grad():
                    out = self._model.generate(
                        **inputs,
                        max_new_tokens=60,
                        num_beams=3,
                        temperature=0.7,
                    )
                cap = self._processor.decode(out[0], skip_special_tokens=True)
                captions.append(cap)

            # Also unconditional
            inputs_unc = self._processor(image.convert("RGB"), return_tensors="pt")
            with torch.no_grad():
                out_unc = self._model.generate(**inputs_unc, max_new_tokens=60, num_beams=3)
            captions.append(self._processor.decode(out_unc[0], skip_special_tokens=True))

            # Pick the most informative caption
            best = max(captions, key=lambda c: len(c))
            return best
        except Exception as e:
            print(f"[BLIP] Inference error: {e}")
            return ""

    def generate(self, image: Image.Image) -> Dict[str, Any]:
        """
        Full pipeline: BLIP caption → room extraction → French caption.
        Falls back to smart_captioner if BLIP unavailable.
        """
        # Ensure model is loaded
        if not self._loaded:
            self._load()

        # Get BLIP caption
        blip_caption = self._generate_blip_caption(image)
        print(f"[BLIP] Raw caption: {blip_caption}")

        # Extract rooms from BLIP caption
        rooms_from_blip = self._extract_rooms_from_caption(blip_caption)

        # CV analysis for additional info
        from models.smart_captioner import SmartFloorPlanCaptioner
        cv_analyzer = SmartFloorPlanCaptioner()
        cv_result   = cv_analyzer.generate(image)

        # Merge: use BLIP rooms if found, else CV rooms
        if len(rooms_from_blip) >= 2:
            rooms = rooms_from_blip
            # Fill areas from CV proportionally
            rooms = self._assign_areas(rooms, cv_result["rooms"])
        else:
            rooms = cv_result["rooms"]

        # Style from BLIP caption
        style = self._detect_style_from_caption(blip_caption) or cv_result["style"]

        # Other metrics from CV
        orientation = cv_result["orientation"]
        n_windows   = cv_result["n_windows"]
        n_doors     = cv_result["n_doors"]
        total_area  = sum(r["area"] for r in rooms)
        plan_type   = self._get_plan_type(len(rooms))

        # Generate final French caption
        caption = self._build_french_caption(
            rooms, style, orientation, total_area,
            n_windows, n_doors, plan_type, blip_caption
        )

        confidence = 0.90 if self._loaded and len(rooms_from_blip) >= 2 else cv_result["confidence"]

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
            "confidence":  confidence,
            "method":      "blip" if self._loaded else "smart_cv",
            "blip_raw":    blip_caption,
            "metrics":     cv_result.get("metrics", {}),
        }

    def _extract_rooms_from_caption(self, caption: str) -> list:
        """Extract room names from BLIP English caption."""
        if not caption:
            return []

        caption_lower = caption.lower()
        found = []
        seen  = set()

        # Sort by length descending to match longer phrases first
        sorted_rooms = sorted(EN_TO_FR.keys(), key=len, reverse=True)

        for en_name in sorted_rooms:
            if en_name in caption_lower:
                fr_name = EN_TO_FR[en_name]
                if fr_name not in seen:
                    seen.add(fr_name)
                    min_a, max_a = TYPICAL_AREAS.get(fr_name, (10, 25))
                    import random
                    area = random.randint(min_a, max_a)
                    windows = {"Salon / Séjour": 3, "Cuisine": 1,
                               "Chambre principale": 2, "Chambre": 1,
                               "Salle de bain": 1}.get(fr_name, 1)
                    found.append({
                        "name":    fr_name,
                        "area":    area,
                        "windows": windows,
                        "notes":   "",
                    })

        # Count bedrooms mentioned
        bedroom_count = len(re.findall(r"bedroom", caption_lower))
        if bedroom_count > 1:
            existing_bedrooms = sum(1 for r in found if "Chambre" in r["name"])
            for i in range(existing_bedrooms, bedroom_count):
                name = "Chambre principale" if i == 0 else f"Chambre {i+1}"
                if name not in seen:
                    seen.add(name)
                    found.append({"name": name, "area": 16, "windows": 1, "notes": ""})

        return found

    def _assign_areas(self, blip_rooms: list, cv_rooms: list) -> list:
        """Assign realistic areas to BLIP-detected rooms using CV proportions."""
        if not cv_rooms:
            return blip_rooms

        total_cv = sum(r["area"] for r in cv_rooms)
        result   = []

        for i, room in enumerate(blip_rooms):
            # Try to find matching CV room
            cv_match = next(
                (r for r in cv_rooms if r["name"] == room["name"]), None
            )
            if cv_match:
                area = cv_match["area"]
            else:
                # Use typical area
                min_a, max_a = TYPICAL_AREAS.get(room["name"], (10, 20))
                area = (min_a + max_a) // 2

            result.append({**room, "area": area})

        return result

    def _detect_style_from_caption(self, caption: str) -> str:
        """Detect architectural style from BLIP caption."""
        if not caption:
            return ""
        caption_lower = caption.lower()
        for style, keywords in STYLE_KEYWORDS.items():
            if any(kw in caption_lower for kw in keywords):
                return style.capitalize()
        return ""

    def _get_plan_type(self, n: int) -> str:
        return {1: "studio", 2: "T2", 3: "T3", 4: "T4",
                5: "T5", 6: "T6"}.get(n, f"T{n}")

    def _build_french_caption(
        self, rooms, style, orientation, total_area,
        n_windows, n_doors, plan_type, blip_raw
    ) -> str:
        n = len(rooms)
        rooms_desc = []
        for r in rooms[:5]:
            note = f", {r['notes']}" if r.get("notes") else ""
            win  = r.get("windows", 0)
            w_str = f", {win} fenêtre{'s' if win > 1 else ''}" if win > 0 else ""
            rooms_desc.append(f"{r['name']} de {r['area']} m²{note}{w_str}")

        rooms_str = " ; ".join(rooms_desc)

        caption = (
            f"Plan {plan_type} de style {style.lower()} comprenant "
            f"{n} pièce{'s' if n > 1 else ''} "
            f"pour une surface habitable totale de {total_area} m². "
            f"Comprend : {rooms_str}. "
            f"Orientation principale : {orientation}. "
            f"Le plan dispose de {n_windows} fenêtre{'s' if n_windows > 1 else ''} "
            f"et {n_doors} porte{'s' if n_doors > 1 else ''}."
        )
        return caption


# Singleton — loaded lazily on first request
blip_captioner = BLIPCaptioner()
