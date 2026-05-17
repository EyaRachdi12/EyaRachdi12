"""
Rule-based floor plan analyzer.
Extracts structured metadata from a generated caption + image analysis.
Used to enrich the API response with structured data.
"""

import re
from typing import Dict, List, Any
from PIL import Image
import numpy as np


# ── Room patterns (French) ────────────────────────────────────────────────────
ROOM_PATTERNS = {
    "Salon / Séjour":       r"\b(salon|séjour|living|open.space)\b",
    "Cuisine":              r"\b(cuisine)\b",
    "Chambre principale":   r"\b(chambre\s+principale|suite\s+parentale|master)\b",
    "Chambre":              r"\b(chambre)\b",
    "Salle de bain":        r"\b(salle\s+de\s+bain|sdb|baignoire)\b",
    "Douche":               r"\b(douche|salle\s+d.eau)\b",
    "WC / Toilettes":       r"\b(wc|toilettes|sanitaires)\b",
    "Bureau":               r"\b(bureau|bibliothèque)\b",
    "Dressing":             r"\b(dressing|placard|rangement)\b",
    "Couloir / Entrée":     r"\b(couloir|entrée|hall|vestibule)\b",
    "Terrasse / Balcon":    r"\b(terrasse|balcon|loggia|véranda)\b",
    "Garage":               r"\b(garage)\b",
    "Cave / Cellier":       r"\b(cave|cellier|buanderie)\b",
}

SURFACE_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*m²")
STYLE_PATTERNS  = {
    "Contemporain":     r"\b(contemporain|moderne|actuel)\b",
    "Minimaliste":      r"\b(minimaliste|épuré|sobre)\b",
    "Haussmannien":     r"\b(haussmannien|classique|traditionnel)\b",
    "Industriel":       r"\b(industriel|loft|brut)\b",
    "Scandinave":       r"\b(scandinave|nordique)\b",
    "Méditerranéen":    r"\b(méditerranéen|provençal)\b",
    "Bioclimatique":    r"\b(bioclimatique|écologique|durable|passif)\b",
}
ORIENTATION_PATTERN = re.compile(
    r"\b(nord|sud|est|ouest|nord-est|nord-ouest|sud-est|sud-ouest)\b", re.I
)
WINDOW_PATTERN = re.compile(r"(\d+)\s*(fenêtre|baie|ouverture)")


def extract_rooms(caption: str) -> List[Dict[str, Any]]:
    """Extract detected rooms from caption text."""
    caption_lower = caption.lower()
    rooms = []
    seen  = set()

    for room_name, pattern in ROOM_PATTERNS.items():
        if re.search(pattern, caption_lower):
            base = room_name.split("/")[0].strip()
            if base not in seen:
                seen.add(base)
                # Try to find associated surface
                area = _find_area_near(caption_lower, pattern)
                rooms.append({
                    "name":    room_name,
                    "area":    area,
                    "windows": _find_windows_near(caption_lower, pattern),
                })

    return rooms if rooms else _default_rooms()


def extract_total_area(caption: str) -> str:
    """Extract total habitable area from caption."""
    matches = SURFACE_PATTERN.findall(caption)
    if matches:
        areas = [float(m) for m in matches]
        # Largest value is likely total area
        total = max(areas)
        return f"{int(total)} m²"
    return "N/A"


def extract_style(caption: str) -> str:
    """Detect architectural style from caption."""
    caption_lower = caption.lower()
    for style, pattern in STYLE_PATTERNS.items():
        if re.search(pattern, caption_lower):
            return style
    return "Contemporain"


def extract_orientation(caption: str) -> str:
    """Extract main orientation from caption."""
    matches = ORIENTATION_PATTERN.findall(caption)
    if matches:
        return matches[0].capitalize()
    return "N/A"


def extract_room_count(caption: str) -> int:
    """Count number of distinct rooms."""
    return len(extract_rooms(caption))


def analyze_image_colors(image: Image.Image) -> Dict[str, Any]:
    """
    Basic image analysis: detect if it's a floor plan
    by checking color distribution (floor plans are mostly white/grey).
    """
    img_array = np.array(image.convert("RGB").resize((64, 64)))
    mean_brightness = img_array.mean()
    is_floor_plan   = mean_brightness > 150  # floor plans are mostly light

    return {
        "mean_brightness": round(float(mean_brightness), 1),
        "is_floor_plan":   bool(is_floor_plan),
        "dominant_color":  "light" if mean_brightness > 200 else
                           "medium" if mean_brightness > 100 else "dark",
    }


def build_structured_analysis(
    caption: str,
    image:   Image.Image,
    confidence: float = 0.0,
) -> Dict[str, Any]:
    """
    Build a complete structured analysis from caption + image.
    This is the main function called by the API.
    """
    rooms      = extract_rooms(caption)
    total_area = extract_total_area(caption)
    style      = extract_style(caption)
    orientation = extract_orientation(caption)
    img_info   = analyze_image_colors(image)

    # Compute total area from rooms if not found in caption
    if total_area == "N/A" and rooms:
        total_area = f"~{len(rooms) * 15} m² (estimé)"

    return {
        "caption":     caption,
        "confidence":  round(confidence * 100, 1),
        "rooms":       rooms,
        "total_area":  total_area,
        "room_count":  len(rooms),
        "style":       style,
        "orientation": orientation,
        "image_info":  img_info,
        "summary": (
            f"Plan {style.lower()} comprenant {len(rooms)} pièce(s) "
            f"pour une surface totale de {total_area}. "
            f"Orientation principale : {orientation}."
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def _find_area_near(text: str, room_pattern: str) -> str:
    """Try to find a surface value near a room mention."""
    match = re.search(room_pattern, text)
    if not match:
        return "N/A"
    start = max(0, match.start() - 30)
    end   = min(len(text), match.end() + 30)
    snippet = text[start:end]
    areas = SURFACE_PATTERN.findall(snippet)
    if areas:
        return f"{areas[0]} m²"
    return "N/A"


def _find_windows_near(text: str, room_pattern: str) -> int:
    """Try to find window count near a room mention."""
    match = re.search(room_pattern, text)
    if not match:
        return 0
    start = max(0, match.start() - 50)
    end   = min(len(text), match.end() + 50)
    snippet = text[start:end]
    w = WINDOW_PATTERN.findall(snippet)
    return int(w[0][0]) if w else 1


def _default_rooms() -> List[Dict[str, Any]]:
    """Return default rooms when caption doesn't contain enough info."""
    return [
        {"name": "Salon / Séjour",   "area": "N/A", "windows": 2},
        {"name": "Cuisine",          "area": "N/A", "windows": 1},
        {"name": "Chambre",          "area": "N/A", "windows": 1},
        {"name": "Salle de bain",    "area": "N/A", "windows": 1},
    ]
