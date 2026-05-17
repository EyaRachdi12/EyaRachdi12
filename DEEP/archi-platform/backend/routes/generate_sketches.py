"""
POST /api/generate-sketches-ai
Generate architectural sketches using AI (Stable Diffusion XL)
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from models.image_generator import generate_sketch_set

router = APIRouter()


class GenerateSketchesRequest(BaseModel):
    style: str
    description: str = ""
    elements: List[str] = []
    view_types: List[str] = []
    n: int = 6


@router.post("/generate-sketches-ai")
async def generate_sketches_ai(request: GenerateSketchesRequest):
    """
    Generate architectural sketches using AI.
    
    Body:
        style: Architectural style (contemporain, minimaliste, etc.)
        description: Project description
        elements: List of elements (terrasse, jardin, piscine, etc.)
        view_types: List of view types (facade, interior_living, etc.)
        n: Number of sketches to generate (default 6)
    
    Returns:
        {
            "sketches": [...],
            "method": "stable_diffusion_xl",
            "count": int
        }
    """
    
    try:
        # Default view types if none provided
        if not request.view_types:
            request.view_types = [
                "facade",
                "interior_living",
                "interior_kitchen",
                "interior_bedroom",
                "aerial",
                "garden"
            ]
        
        # Generate sketches
        sketches = generate_sketch_set(
            style=request.style,
            description=request.description,
            elements=request.elements,
            view_types=request.view_types,
            n=request.n
        )
        
        if not sketches:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate any sketches. Check HuggingFace API token."
            )
        
        return JSONResponse(content={
            "sketches": sketches,
            "method": "pollinations_ai_flux",
            "count": len(sketches),
            "style": request.style
        })
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating sketches: {str(e)}"
        )
