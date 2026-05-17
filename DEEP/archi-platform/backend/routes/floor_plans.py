"""
Floor Plans Library — Static floor plans serving
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from pathlib import Path

router = APIRouter()

# Path to sample floor plans
SAMPLE_PLANS_DIR = Path(__file__).parent.parent / "test" / "sample_plans"
PEXELS_PLANS_DIR = SAMPLE_PLANS_DIR / "pexels"

# Floor plans metadata - Using real professional plans from Pexels
FLOOR_PLANS_LIBRARY = [
    {
        "id": "studio-compact",
        "title": "Studio Compact Moderne",
        "type": "Studio",
        "rooms": 1,
        "surface": 25,
        "style": "Contemporain",
        "image_file": "pexels/studio_1_pexels_5583253.jpg",
        "description": "Studio optimisé pour étudiant ou jeune actif avec espace bien agencé",
        "features": ["Kitchenette", "Salle d'eau", "Rangements intégrés", "Lumineux"],
        "photographer": "Thirdman",
        "source": "Pexels"
    },
    {
        "id": "studio-elegant",
        "title": "Studio Élégant",
        "type": "Studio",
        "rooms": 1,
        "surface": 28,
        "style": "Contemporain",
        "image_file": "pexels/studio_2_pexels_6615235.jpg",
        "description": "Studio élégant avec design moderne et fonctionnel",
        "features": ["Espace ouvert", "Cuisine équipée", "Salle de bain", "Balcon"],
        "photographer": "Tima Miroshnichenko",
        "source": "Pexels"
    },
    {
        "id": "t2-moderne",
        "title": "Appartement T2 Moderne",
        "type": "T2",
        "rooms": 2,
        "surface": 55,
        "style": "Contemporain",
        "image_file": "pexels/t2_1_pexels_7019026.jpg",
        "description": "Appartement 2 pièces avec salon spacieux et chambre confortable",
        "features": ["Cuisine ouverte", "Balcon", "Salle de bain moderne", "Rangements"],
        "photographer": "Max Vakhtbovych",
        "source": "Pexels"
    },
    {
        "id": "t2-cosy",
        "title": "Appartement T2 Cosy",
        "type": "T2",
        "rooms": 2,
        "surface": 52,
        "style": "Contemporain",
        "image_file": "pexels/t2_2_pexels_9877337.jpg",
        "description": "Appartement 2 pièces chaleureux et bien agencé",
        "features": ["Salon lumineux", "Chambre spacieuse", "Cuisine équipée", "Terrasse"],
        "photographer": "Nguyễn Thị Minh Nghi",
        "source": "Pexels"
    },
    {
        "id": "t3-familial",
        "title": "Maison T3 Familiale",
        "type": "T3",
        "rooms": 3,
        "surface": 75,
        "style": "Contemporain",
        "image_file": "pexels/t3_1_pexels_7937331.jpg",
        "description": "Maison 3 pièces idéale pour petite famille avec jardin",
        "features": ["2 chambres", "Salon spacieux", "Cuisine équipée", "Jardin"],
        "photographer": "Pavel Danilyuk",
        "source": "Pexels"
    },
    {
        "id": "t3-confort",
        "title": "Appartement T3 Confort",
        "type": "T3",
        "rooms": 3,
        "surface": 72,
        "style": "Contemporain",
        "image_file": "pexels/t3_2_pexels_7937668.jpg",
        "description": "Appartement 3 pièces confortable avec balcon et vue dégagée",
        "features": ["2 chambres", "Grand salon", "Cuisine moderne", "Balcon"],
        "photographer": "Pavel Danilyuk",
        "source": "Pexels"
    },
    {
        "id": "t4-villa",
        "title": "Villa T4 Luxe",
        "type": "T4",
        "rooms": 4,
        "surface": 120,
        "style": "Contemporain",
        "image_file": "pexels/t4_1_pexels_31817156.jpg",
        "description": "Villa moderne 4 pièces avec piscine et jardin paysager",
        "features": ["3 chambres", "Suite parentale", "Piscine", "Terrasse", "Garage"],
        "photographer": "Ahmet ÇÖTÜR",
        "source": "Pexels"
    },
    {
        "id": "t4-prestige",
        "title": "Villa T4 Prestige",
        "type": "T4",
        "rooms": 4,
        "surface": 135,
        "style": "Contemporain",
        "image_file": "pexels/t4_2_pexels_19075389.jpg",
        "description": "Villa de prestige avec piscine, jacuzzi et vue panoramique",
        "features": ["3 chambres", "Piscine", "Jacuzzi", "Terrasse", "Jardin"],
        "photographer": "Ahmet ÇÖTÜR",
        "source": "Pexels"
    },
    {
        "id": "loft-moderne",
        "title": "Loft Moderne",
        "type": "Loft",
        "rooms": 3,
        "surface": 110,
        "style": "Contemporain",
        "image_file": "pexels/loft_1_pexels_7031402.jpg",
        "description": "Loft moderne avec double hauteur et mezzanine",
        "features": ["Mezzanine", "Espace ouvert", "Cuisine américaine", "Lumineux"],
        "photographer": "Max Vakhtbovych",
        "source": "Pexels"
    },
    {
        "id": "loft-spacieux",
        "title": "Loft Spacieux",
        "type": "Loft",
        "rooms": 3,
        "surface": 115,
        "style": "Contemporain",
        "image_file": "pexels/loft_2_pexels_7031590.jpg",
        "description": "Grand loft avec escalier design et volumes généreux",
        "features": ["Escalier design", "Espace ouvert", "Hauteur sous plafond", "Moderne"],
        "photographer": "Max Vakhtbovych",
        "source": "Pexels"
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
        media_type="image/png" if image_path.suffix == ".png" else "image/jpeg",
        filename=plan["image_file"]
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
    download_name = f"{plan['title'].replace(' ', '_')}.{image_path.suffix[1:]}"
    
    return FileResponse(
        path=image_path,
        media_type="image/png" if image_path.suffix == ".png" else "image/jpeg",
        filename=download_name,
        headers={"Content-Disposition": f"attachment; filename={download_name}"}
    )
