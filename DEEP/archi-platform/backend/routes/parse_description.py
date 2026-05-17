"""
POST /api/parse-description
Parses a French architectural text description into structured room data
for the 3D floor plan viewer. Optionally accepts a floor plan image to
extract real room positions using computer vision.
"""

import re
import math
import base64
import traceback
from io import BytesIO
from fastapi import APIRouter, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from PIL import Image
import cv2
import numpy as np

router = APIRouter()


class DescriptionRequest(BaseModel):
    description: str
    style: str = "contemporain"


class RoomOut(BaseModel):
    name: str
    area: float
    windows: int
    color: Optional[str] = None
    # Optional coordinates from CV analysis
    x: Optional[float] = None
    z: Optional[float] = None
    w: Optional[float] = None
    d: Optional[float] = None


class ParseResult(BaseModel):
    rooms: List[RoomOut]
    total_area: float
    style: str
    n_floors: int
    has_garden: bool
    has_garage: bool
    has_pool: bool
    has_terrace: bool


# ── Room detection patterns (French) ─────────────────────────────────────────
ROOM_PATTERNS = [
    # (regex, canonical name, default area, default windows)
    (r"\bsalon\b",                    "Salon / Séjour",      28.0, 2),
    (r"\bséjour\b",                   "Salon / Séjour",      28.0, 2),
    (r"\bsejour\b",                   "Salon / Séjour",      28.0, 2),
    (r"\bliving\b",                   "Salon / Séjour",      28.0, 2),
    (r"\bcuisine\b",                  "Cuisine",             12.0, 1),
    (r"\bsuite\s+parentale\b",        "Chambre principale",  20.0, 1),
    (r"\bchambre\s+principale\b",     "Chambre principale",  20.0, 1),
    (r"\bmaster\b",                   "Chambre principale",  20.0, 1),
    (r"\bchambre\b",                  "Chambre",             14.0, 1),
    (r"\bsalle\s+de\s+bain\b",        "Salle de bain",        7.0, 1),
    (r"\bsdb\b",                      "Salle de bain",        7.0, 1),
    (r"\bsalle\s+d.eau\b",            "Salle d'eau",          5.0, 0),
    (r"\bdouche\b",                   "Salle d'eau",          5.0, 0),
    (r"\bwc\b",                       "WC",                   3.0, 0),
    (r"\btoilettes?\b",               "WC",                   3.0, 0),
    (r"\bbureau\b",                   "Bureau",              12.0, 1),
    (r"\bdressing\b",                 "Dressing",             6.0, 0),
    (r"\bcouloir\b",                  "Couloir / Entrée",     6.0, 0),
    (r"\bentrée\b",                   "Couloir / Entrée",     6.0, 0),
    (r"\bhall\b",                     "Couloir / Entrée",     6.0, 0),
    (r"\bterrasse\b",                 "Terrasse",            15.0, 0),
    (r"\bbalcon\b",                   "Balcon",               6.0, 0),
    (r"\bgarage\b",                   "Garage",              20.0, 0),
    (r"\bbuanderie\b",                "Buanderie",            5.0, 0),
    (r"\bcave\b",                     "Cave",                10.0, 0),
    (r"\bcellier\b",                  "Cellier",              6.0, 0),
    (r"\bvéranda\b",                  "Véranda",             12.0, 2),
    (r"\bpiscine\b",                  "Piscine",             30.0, 0),
    (r"\bjardin\b",                   "Jardin",              50.0, 0),
    (r"\bsalle\s+à\s+manger\b",       "Salle à manger",      16.0, 1),
    (r"\bsalle\s+de\s+jeux?\b",       "Salle de jeux",       14.0, 1),
    (r"\bbibliothèque\b",             "Bibliothèque",        10.0, 1),
]

SURFACE_RE = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*m[²2]",
    re.IGNORECASE
)

CHAMBRE_COUNT_RE = re.compile(
    r"(\d+)\s+chambres?",
    re.IGNORECASE
)

FLOOR_RE = re.compile(
    r"(\d+)\s+(?:étages?|niveaux?)",
    re.IGNORECASE
)


def _find_area_near(text: str, match_start: int, match_end: int) -> Optional[float]:
    """Look for a surface value within 50 chars AFTER a room mention only."""
    # Only look forward (after the room name), not before
    window = text[match_end: min(len(text), match_end + 50)]
    hits = SURFACE_RE.findall(window)
    if hits:
        return float(hits[0].replace(",", "."))
    return None


def parse_description(description: str, style: str) -> dict:
    text = description.lower()
    rooms_found: List[dict] = []
    seen_names: set = set()

    # ── Detect rooms ──────────────────────────────────────────────────────────
    for pattern, canonical, default_area, default_windows in ROOM_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            # Avoid duplicates (e.g. "chambre principale" before "chambre")
            if canonical in seen_names:
                continue
            # Skip "chambre" if "chambre principale" already found
            if canonical == "Chambre" and "Chambre principale" in seen_names:
                pass  # allow multiple chambres

            area = _find_area_near(text, m.start(), m.end()) or default_area
            rooms_found.append({
                "name":    canonical,
                "area":    area,
                "windows": default_windows,
            })
            seen_names.add(canonical)
            break  # one match per pattern type (except chambre)

    # ── Handle "X chambres" multiplier ───────────────────────────────────────
    chambre_count_match = CHAMBRE_COUNT_RE.search(text)
    if chambre_count_match:
        count = int(chambre_count_match.group(1))
        # Remove existing chambre entries and re-add correct count
        existing_chambres = [r for r in rooms_found if "Chambre" in r["name"]]
        for r in existing_chambres:
            rooms_found.remove(r)
        seen_names.discard("Chambre")
        seen_names.discard("Chambre principale")

        if count >= 1:
            rooms_found.append({"name": "Chambre principale", "area": 20.0, "windows": 1})
        for i in range(2, count + 1):
            rooms_found.append({"name": f"Chambre {i}", "area": 14.0, "windows": 1})

    # ── Fallback: if nothing detected, use defaults ───────────────────────────
    if not rooms_found:
        rooms_found = [
            {"name": "Salon / Séjour",   "area": 28.0, "windows": 2},
            {"name": "Cuisine",          "area": 12.0, "windows": 1},
            {"name": "Chambre principale","area": 20.0, "windows": 1},
            {"name": "Chambre 2",        "area": 14.0, "windows": 1},
            {"name": "Salle de bain",    "area":  7.0, "windows": 1},
            {"name": "Couloir / Entrée", "area":  6.0, "windows": 0},
        ]

    # ── Ensure at least a salon and cuisine ──────────────────────────────────
    names = [r["name"] for r in rooms_found]
    if not any("Salon" in n or "Séjour" in n for n in names):
        rooms_found.insert(0, {"name": "Salon / Séjour", "area": 28.0, "windows": 2})
    if not any("Cuisine" in n for n in names):
        rooms_found.insert(1, {"name": "Cuisine", "area": 12.0, "windows": 1})

    # ── Compute total area ────────────────────────────────────────────────────
    all_surfaces = SURFACE_RE.findall(text)
    if all_surfaces:
        floats = [float(s.replace(",", ".")) for s in all_surfaces]
        total_area = max(floats)
        # If max surface is smaller than sum of rooms, use sum
        room_sum = sum(r["area"] for r in rooms_found)
        if total_area < room_sum * 0.5:
            total_area = room_sum
    else:
        total_area = sum(r["area"] for r in rooms_found)

    # ── Detect floors ─────────────────────────────────────────────────────────
    floor_match = FLOOR_RE.search(text)
    n_floors = int(floor_match.group(1)) if floor_match else 1

    return {
        "rooms":       rooms_found,
        "total_area":  round(total_area, 1),
        "style":       style,
        "n_floors":    n_floors,
        "has_garden":  bool(re.search(r"\bjardin\b", text)),
        "has_garage":  bool(re.search(r"\bgarage\b", text)),
        "has_pool":    bool(re.search(r"\bpiscine\b", text)),
        "has_terrace": bool(re.search(r"\bterrasse\b|\bbalcon\b", text)),
    }


@router.post("/parse-description")
async def parse_description_endpoint(body: DescriptionRequest):
    result = parse_description(body.description, body.style)
    return JSONResponse(content=result)


@router.post("/parse-description-with-image")
async def parse_description_with_image_endpoint(
    description: str = Form(...),
    style: str = Form("contemporain"),
    image: UploadFile = File(None),
):
    """
    Enhanced endpoint that accepts both description AND floor plan image.
    Uses CV to extract real room positions from the image.
    """
    # Parse text description first
    text_result = parse_description(description, style)
    
    # If no image provided, return text-only result
    if not image:
        return JSONResponse(content=text_result)
    
    # Load and analyze image with smart captioner
    try:
        from models.smart_captioner import SmartFloorPlanCaptioner
        import cv2
        import numpy as np
        
        img_bytes = await image.read()
        img = Image.open(BytesIO(img_bytes))
        
        print(f"[DEBUG] Image size: {img.width}x{img.height}")
        
        # Run CV analysis to get RAW room positions (before processing)
        captioner = SmartFloorPlanCaptioner()
        img_cv = cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)
        
        # Get metrics
        metrics = captioner._compute_metrics(img_cv)
        print(f"[DEBUG] Metrics: {metrics}")
        
        # Get raw CV room detections with coordinates
        rooms_cv_raw = captioner._detect_rooms_cv(img_cv, metrics)
        print(f"[DEBUG] CV detected {len(rooms_cv_raw)} rooms")
        for i, room in enumerate(rooms_cv_raw[:5]):
            print(f"[DEBUG] Room {i}: cx={room.get('cx')}, cy={room.get('cy')}, w={room.get('w')}, h={room.get('h')}, area_px={room.get('area_px')}")
        
        # Match text-parsed rooms with CV-detected positions
        matched_rooms = _match_rooms_with_positions(
            text_result["rooms"],
            rooms_cv_raw,
            img.width,
            img.height
        )
        
        print(f"[DEBUG] Matched {len(matched_rooms)} rooms")
        for i, room in enumerate(matched_rooms[:5]):
            print(f"[DEBUG] Matched room {i}: {room.get('name')} - x={room.get('x')}, z={room.get('z')}, w={room.get('w')}, d={room.get('d')}")
        
        # Update result with positioned rooms
        text_result["rooms"] = matched_rooms
        text_result["layout_source"] = "cv_analysis"
        text_result["cv_rooms_detected"] = len(rooms_cv_raw)
        
        return JSONResponse(content=text_result)
        
    except Exception as e:
        # Fallback to text-only if CV fails
        import traceback
        print(f"CV analysis failed: {e}")
        print(traceback.format_exc())
        text_result["layout_source"] = "text_only"
        return JSONResponse(content=text_result)


def _match_rooms_with_positions(
    text_rooms: List[dict],
    cv_rooms: List[dict],
    img_width: int,
    img_height: int
) -> List[dict]:
    """
    Match text-parsed rooms with CV-detected positions.
    Uses room size and type to find best matches.
    """
    if not cv_rooms:
        return text_rooms
    
    # Convert pixel coordinates to 3D world coordinates
    # Assume image represents ~15m x 15m space
    scale_x = 15.0 / img_width
    scale_z = 15.0 / img_height
    
    # Sort both lists by area (descending)
    text_sorted = sorted(text_rooms, key=lambda r: r["area"], reverse=True)
    cv_sorted = sorted(cv_rooms, key=lambda r: r.get("area", 0), reverse=True)
    
    matched = []
    used_cv_indices = set()
    
    for text_room in text_sorted:
        best_match = None
        best_score = -1
        best_idx = -1
        
        for i, cv_room in enumerate(cv_sorted):
            if i in used_cv_indices:
                continue
            
            # Score based on area similarity
            text_area = text_room["area"]
            cv_area = cv_room.get("area", 15)
            area_diff = abs(text_area - cv_area) / max(text_area, 1)
            score = 1.0 - min(area_diff, 1.0)
            
            if score > best_score:
                best_score = score
                best_match = cv_room
                best_idx = i
        
        if best_match and best_score > 0.3:
            # Convert CV pixel coords to 3D world coords
            # Center the layout around origin
            cx_world = (best_match["cx"] - img_width / 2) * scale_x
            cy_world = (best_match["cy"] - img_height / 2) * scale_z
            w_world = best_match["w"] * scale_x
            h_world = best_match["h"] * scale_z
            
            matched.append({
                **text_room,
                "x": round(cx_world, 2),
                "z": round(cy_world, 2),
                "w": round(w_world, 2),
                "d": round(h_world, 2),
            })
            used_cv_indices.add(best_idx)
        else:
            # No good match, keep text room without position
            matched.append(text_room)
    
    return matched
