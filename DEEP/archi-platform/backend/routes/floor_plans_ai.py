"""
Floor Plans Library — AI Generated professional floor plans
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

router = APIRouter()

# Path to AI generated floor plans
SAMPLE_PLANS_DIR = Path(__file__).parent.parent / "test" / "sample_plans"
AI_PLANS_DIR = SAMPLE_PLANS_DIR / "ai_generated"

# Floor plans metadata - Using AI generated professional plans
FLOOR_PLANS_LIBRARY = [
    {
        "id": "studio-modern",
        "title": "Studio Moderne",
        "type": "Studio",
        "rooms": 1,
        "surface": 25,
        "style": "Contemporain",
        "image_file": "ai_generated/studio_modern_ai.png",
        "description": "Studio moderne optimisé avec kitchenette et salle d'eau",
        "features": ["Kitchenette", "Salle d'eau", "Rangements intégrés", "Lumineux"],
    },
    {
        "id": "t2-contemporary",
        "title": "Appartement T2 Contemporain",
        "type": "T2",
        "rooms": 2,
        "surface": 55,
        "style": "Contemporain",
        "image_file": "ai_generated/t2_contemporary_ai.png",
        "description": "Appartement 2 pièces avec salon spacieux et chambre confortable",
        "features": ["Cuisine ouverte", "Balcon", "Salle de bain moderne", "Rangements"],
    },
    {
        "id": "t3-family",
        "title": "Maison T3 Familiale",
        "type": "T3",
        "rooms": 3,
        "surface": 75,
        "style": "Contemporain",
        "image_file": "ai_generated/t3_family_ai.png",
        "description": "Maison 3 pièces idéale pour famille avec 2 chambres",
        "features": ["2 chambres", "Salon spacieux", "Cuisine équipée", "Salle de bain"],
    },
    {
        "id": "t4-villa",
        "title": "Villa T4 Luxe",
        "type": "T4",
        "rooms": 4,
        "surface": 120,
        "style": "Contemporain",
        "image_file": "ai_generated/t4_villa_ai.png",
        "description": "Villa moderne 4 pièces avec suite parentale et terrasse",
        "features": ["3 chambres", "Suite parentale", "Terrasse", "2 salles de bain"],
    },
    {
        "id": "loft-modern",
        "title": "Loft Moderne",
        "type": "Loft",
        "rooms": 3,
        "surface": 110,
        "style": "Contemporain",
        "image_file": "ai_generated/loft_modern_ai.png",
        "description": "Loft moderne avec mezzanine et espace ouvert",
        "features": ["Mezzanine", "Espace ouvert", "Cuisine américaine", "Lumineux"],
    },
]


@router.get("/floor-plans")
def get_floor_plans():
    """
    Get all available floor plans in the library
    """
    return {
        "plans": FLOOR_PLANS_LIBRARY,
        "total": len(FLOOR_PLANS_LIBRARY)
    }


@router.get("/floor-plans/{plan_id}")
def get_floor_plan(plan_id: str):
    """
    Get a specific floor plan by ID
    """
    plan = next((p for p in FLOOR_PLANS_LIBRARY if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    return plan


@router.get("/floor-plans/{plan_id}/image")
def get_floor_plan_image(plan_id: str):
    """
    Serve the floor plan image file
    """
    plan = next((p for p in FLOOR_PLANS_LIBRARY if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    
    image_path = SAMPLE_PLANS_DIR / plan["image_file"]
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename=plan["image_file"].split("/")[-1]
    )


@router.get("/floor-plans/{plan_id}/download")
def download_floor_plan(plan_id: str):
    """
    Download a floor plan image
    """
    plan = next((p for p in FLOOR_PLANS_LIBRARY if p["id"] == plan_id), None)
    if not plan:
        raise HTTPException(status_code=404, detail="Floor plan not found")
    
    image_path = SAMPLE_PLANS_DIR / plan["image_file"]
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")
    
    # Force download with proper filename
    download_name = f"{plan['title'].replace(' ', '_')}.png"
    
    return FileResponse(
        path=image_path,
        media_type="image/png",
        filename=download_name,
        headers={"Content-Disposition": f"attachment; filename={download_name}"}
    )
