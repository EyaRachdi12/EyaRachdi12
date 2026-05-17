"""
POST /api/analyze-plan
Accepts a floor plan image, returns caption + structured analysis.

Model priority:
  1. Trained LSTM (best_model.pth) — if weights available
  2. Rule-based captioner          — fallback
"""

import io
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image

router = APIRouter()

ALLOWED_TYPES = {
    "image/png", "image/jpeg", "image/jpg",
    "image/webp", "image/bmp",
}

# Load model once at startup
_captioner = None

def get_captioner():
    global _captioner
    if _captioner is None:
        try:
            # Try new EfficientNetV2 + Transformer model first
            from models.floorplan_captioner_v2 import floorplan_captioner_v2
            if floorplan_captioner_v2.is_available():
                _captioner = floorplan_captioner_v2
                print("[analyze] ✅ Using EfficientNetV2 + Transformer model (V2)")
                return _captioner
        except Exception as e:
            print(f"[analyze] V2 model unavailable: {e}")

        try:
            # Fallback to trained LSTM model
            from models.trained_captioner import trained_captioner
            if trained_captioner.is_available():
                _captioner = trained_captioner
                print("[analyze] ✅ Using TRAINED LSTM model (ResNet-101 + LSTM + Attention)")
                return _captioner
        except Exception as e:
            print(f"[analyze] Trained model unavailable: {e}")
        
        try:
            from models.blip_remote_captioner import blip_remote_captioner
            _captioner = blip_remote_captioner
            print("[analyze] Using BLIP Remote captioner (Colab API)")
        except Exception as e:
            print(f"[analyze] BLIP Remote unavailable ({e}), using smart CV")
            from models.smart_captioner import smart_captioner
            _captioner = smart_captioner
    return _captioner


@router.post("/analyze-plan")
async def analyze_plan(file: UploadFile = File(...)):
    """
    Analyze a floor plan image and return a structured caption.
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Format non supporté : {file.content_type}. Utilisez PNG ou JPG.",
        )

    try:
        contents = await file.read()
        image    = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Impossible de lire l'image : {e}")

    t0 = time.time()
    try:
        model  = get_captioner()
        result = model.generate(image)
        elapsed = round(time.time() - t0, 3)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse : {e}")

    rooms = result.get("rooms", [])

    return JSONResponse(content={
        "filename":         file.filename,
        "caption":          result.get("caption", ""),
        "summary":          result.get("summary", result.get("caption", "")[:100]),
        "rooms":            rooms,
        "total_area":       result.get("total_area", 0),
        "room_count":       len(rooms),
        "style":            result.get("style", "Contemporain"),
        "orientation":      result.get("orientation", "N/A"),
        "plan_type":        result.get("plan_type", "logement"),
        "n_windows":        result.get("n_windows", 0),
        "n_doors":          result.get("n_doors", 0),
        "confidence":       result.get("confidence", 0.85),
        "confidence_pct":   round(result.get("confidence", 0.85) * 100, 1),
        "inference_time_s": elapsed,
        "method":           result.get("method", "rule_based"),
        "image_metrics":    result.get("metrics", {
            "brightness": 0, "edge_density": 0, "is_floor_plan": True
        }),
    })
