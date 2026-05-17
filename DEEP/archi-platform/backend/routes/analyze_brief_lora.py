"""
POST /api/analyze-brief-lora
Analyzes architectural briefs using fine-tuned LoRA model.

This endpoint uses a fine-tuned Phi-3 model with LoRA adapters
to extract structured information from natural language briefs.

More accurate than regex-based parsing, especially for:
- Complex descriptions
- Budget extraction
- Style identification
- Room specifications
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
import time

router = APIRouter()


class BriefAnalysisRequest(BaseModel):
    """Request body for brief analysis"""
    description: str
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024


class BriefAnalysisResponse(BaseModel):
    """Response with extracted information"""
    surface_souhaitee: Optional[str] = None
    budget: Optional[str] = None
    style: Optional[str] = None
    pieces_souhaitees: Optional[list] = None
    raw_response: Optional[str] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None


@router.post("/analyze-brief-lora")
async def analyze_brief_lora(body: BriefAnalysisRequest):
    """
    Analyze an architectural brief using the fine-tuned LoRA model.
    
    Example request:
    ```json
    {
        "description": "Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€",
        "temperature": 0.7,
        "max_tokens": 1024
    }
    ```
    
    Example response:
    ```json
    {
        "surface_souhaitee": "120-140 m²",
        "budget": "350000-450000",
        "style": "Contemporain",
        "pieces_souhaitees": [
            {
                "nom": "Salon / Séjour",
                "surface": "30-35 m²",
                "details": "Lumineux"
            },
            ...
        ],
        "processing_time_ms": 1234
    }
    ```
    """
    start_time = time.time()
    
    try:
        # Import analyzer (lazy import to avoid loading model at startup)
        from models.brief_analyzer_lora import get_analyzer
        
        # Get analyzer instance
        analyzer = get_analyzer()
        
        # Analyze brief
        result = analyzer.analyze(
            brief_text=body.description,
            max_tokens=body.max_tokens,
            temperature=body.temperature
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        result["processing_time_ms"] = processing_time_ms
        
        # Check for errors
        if "error" in result:
            return JSONResponse(
                content={
                    "error": result["error"],
                    "raw_response": result.get("raw_response", ""),
                    "processing_time_ms": processing_time_ms
                },
                status_code=500
            )
        
        return JSONResponse(content=result)
        
    except FileNotFoundError as e:
        # Model not found
        return JSONResponse(
            content={
                "error": "Model not found. Please train the model first or download the adapters.",
                "details": str(e),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            },
            status_code=503
        )
    
    except Exception as e:
        # Other errors
        import traceback
        return JSONResponse(
            content={
                "error": f"Analysis failed: {str(e)}",
                "traceback": traceback.format_exc(),
                "processing_time_ms": int((time.time() - start_time) * 1000)
            },
            status_code=500
        )


@router.get("/analyze-brief-lora/health")
async def health_check():
    """
    Check if the LoRA model is available and loaded.
    
    Returns:
        - status: "ready" if model is loaded, "not_loaded" if available but not loaded, "unavailable" if not found
        - model_info: Information about the model
    """
    try:
        from models.brief_analyzer_lora import get_analyzer
        from pathlib import Path
        
        analyzer = get_analyzer()
        
        # Check if model files exist
        lora_path = Path(analyzer.lora_path)
        model_exists = lora_path.exists()
        
        if not model_exists:
            return JSONResponse(
                content={
                    "status": "unavailable",
                    "message": "LoRA adapters not found. Please train the model first.",
                    "lora_path": str(lora_path),
                    "model_loaded": False
                }
            )
        
        # Check if model is loaded
        if analyzer._loaded:
            return JSONResponse(
                content={
                    "status": "ready",
                    "message": "Model is loaded and ready",
                    "base_model": analyzer.base_model_name,
                    "lora_path": str(lora_path),
                    "device": analyzer.device,
                    "model_loaded": True
                }
            )
        else:
            return JSONResponse(
                content={
                    "status": "not_loaded",
                    "message": "Model files found but not loaded yet. Will load on first request.",
                    "base_model": analyzer.base_model_name,
                    "lora_path": str(lora_path),
                    "device": analyzer.device,
                    "model_loaded": False
                }
            )
    
    except Exception as e:
        return JSONResponse(
            content={
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "model_loaded": False
            },
            status_code=500
        )


@router.post("/analyze-brief-lora/preload")
async def preload_model():
    """
    Preload the model into memory.
    Useful for warming up the service before handling requests.
    """
    try:
        from models.brief_analyzer_lora import get_analyzer
        
        analyzer = get_analyzer()
        
        if analyzer._loaded:
            return JSONResponse(
                content={
                    "message": "Model already loaded",
                    "status": "ready"
                }
            )
        
        # Load model
        start_time = time.time()
        analyzer.load()
        load_time_ms = int((time.time() - start_time) * 1000)
        
        return JSONResponse(
            content={
                "message": "Model loaded successfully",
                "status": "ready",
                "load_time_ms": load_time_ms,
                "base_model": analyzer.base_model_name,
                "device": analyzer.device
            }
        )
    
    except Exception as e:
        import traceback
        return JSONResponse(
            content={
                "error": f"Failed to load model: {str(e)}",
                "traceback": traceback.format_exc()
            },
            status_code=500
        )
