"""
ArchiGuide — FastAPI Backend
Serves the AI models for floor plan analysis and VQA.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
import torch
import os

load_dotenv()  # charge archi-platform/backend/.env

from routes.analyze           import router as analyze_router
from routes.vqa               import router as vqa_router
from routes.video             import router as video_router
from routes.parse_description import router as description_router
from routes.video_luma        import router as luma_router
from routes.clients           import router as clients_router
from routes.messages          import router as messages_router
from routes.auth              import router as auth_router
from routes.projects          import router as projects_router
from routes.briefs            import router as briefs_router
from routes.stats             import router as stats_router
from routes.sketches          import router as sketches_router
from routes.generate_sketches import router as generate_sketches_router
from routes.floor_plans_ai    import router as floor_plans_router
from routes.analytics         import router as analytics_router
from routes.project_documents import router as project_documents_router
from routes.analyze_brief_lora import router as analyze_brief_lora_router

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "ArchiGuide AI Backend",
    description = "Floor plan analysis API — CNN+LSTM+Attention & VQA",
    version     = "1.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

# ── CORS (allow Next.js frontend) ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["http://localhost:3000", "http://192.168.11.100:3000"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(analyze_router,     prefix="/api", tags=["Caption"])
app.include_router(vqa_router,         prefix="/api", tags=["VQA"])
app.include_router(video_router,       prefix="/api", tags=["Video"])
app.include_router(description_router, prefix="/api", tags=["Description"])
app.include_router(luma_router,        prefix="/api", tags=["Luma AI"])
app.include_router(clients_router,     prefix="/api", tags=["Clients"])
app.include_router(messages_router,    prefix="/api", tags=["Messages"])
app.include_router(auth_router,        prefix="/api", tags=["Auth"])
app.include_router(projects_router,    prefix="/api", tags=["Projects"])
app.include_router(briefs_router,      prefix="/api", tags=["Briefs"])
app.include_router(stats_router,       prefix="/api", tags=["Stats"])
app.include_router(sketches_router,    prefix="/api", tags=["Sketches"])
app.include_router(generate_sketches_router, prefix="/api", tags=["AI Generation"])
app.include_router(floor_plans_router, prefix="/api", tags=["Floor Plans Library"])
app.include_router(analytics_router,   prefix="/api", tags=["Analytics"])
app.include_router(project_documents_router, prefix="/api", tags=["Project Documents"])
app.include_router(analyze_brief_lora_router, prefix="/api", tags=["Brief Analysis LoRA"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
def root():
    return {
        "status":  "ok",
        "service": "ArchiGuide AI Backend",
        "device":  "cuda" if torch.cuda.is_available() else "cpu",
        "models":  ["FloorPlanCaptionModel (ResNet101+LSTM+Attention)", "FloorPlanVQAModel"],
    }


@app.get("/health", tags=["Health"])
def health():
    return JSONResponse({"status": "healthy"})


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
