"""
Project Documents API
Manages documents shared between architect and client
"""

import json
import base64
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

DATA_DIR = Path(__file__).parent.parent / "data"
DOCUMENTS_DIR = DATA_DIR / "project_documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

DOCUMENTS_DB = DATA_DIR / "project_documents.json"


def _load_documents() -> list:
    """Load documents database."""
    if not DOCUMENTS_DB.exists():
        return []
    try:
        with open(DOCUMENTS_DB, encoding="utf-8") as f:
            return json.load(f)
    except:
        return []


def _save_documents(docs: list):
    """Save documents database."""
    with open(DOCUMENTS_DB, "w", encoding="utf-8") as f:
        json.dump(docs, f, ensure_ascii=False, indent=2)


class DocumentCreate(BaseModel):
    project_id: str
    name: str
    type: str  # PDF, PNG, JPG, ZIP, MP4, DOC
    size: str
    status: str  # Nouveau, Actif, Archivé
    image_data: Optional[str] = None  # Base64 encoded image


@router.get("/projects/{project_id}/documents")
def get_project_documents(project_id: str):
    """Get all documents for a project."""
    docs = _load_documents()
    project_docs = [d for d in docs if d.get("project_id") == project_id]
    return JSONResponse(content={"documents": project_docs})


@router.post("/projects/{project_id}/documents")
def add_project_document(project_id: str, body: DocumentCreate):
    """Add a document to a project."""
    docs = _load_documents()
    
    # Generate document ID
    import time
    doc_id = f"doc_{int(time.time())}"
    
    # Save image data if provided
    file_path = None
    if body.image_data:
        # Extract extension from type
        ext_map = {"PDF": "pdf", "PNG": "png", "JPG": "jpg", "ZIP": "zip", "MP4": "mp4", "DOC": "docx"}
        ext = ext_map.get(body.type, "bin")
        
        file_path = f"{doc_id}.{ext}"
        full_path = DOCUMENTS_DIR / file_path
        
        # Decode and save
        try:
            # Remove data URL prefix if present
            if "," in body.image_data:
                image_data = body.image_data.split(",")[1]
            else:
                image_data = body.image_data
            
            image_bytes = base64.b64decode(image_data)
            with open(full_path, "wb") as f:
                f.write(image_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to save file: {e}")
    
    # Create document record
    from datetime import datetime
    doc = {
        "id": doc_id,
        "project_id": project_id,
        "name": body.name,
        "type": body.type,
        "size": body.size,
        "status": body.status,
        "date": datetime.now().strftime("%d %b"),
        "file_path": file_path,
        "created_at": int(time.time()),
    }
    
    docs.append(doc)
    _save_documents(docs)
    
    return JSONResponse(content=doc, status_code=201)


@router.get("/projects/{project_id}/documents/{doc_id}/download")
def download_document(project_id: str, doc_id: str):
    """Download a project document."""
    print(f"📥 Download request - project_id: {project_id}, doc_id: {doc_id}")
    
    docs = _load_documents()
    print(f"📦 Loaded {len(docs)} documents")
    
    doc = next((d for d in docs if d["id"] == doc_id and d["project_id"] == project_id), None)
    
    if not doc:
        print(f"❌ Document not found: {doc_id}")
        raise HTTPException(status_code=404, detail="Document not found")
    
    print(f"✅ Document found: {doc['name']}")
    
    if not doc.get("file_path"):
        print(f"❌ No file_path for document")
        raise HTTPException(status_code=404, detail="File not available")
    
    file_path = DOCUMENTS_DIR / doc["file_path"]
    print(f"📁 File path: {file_path}")
    print(f"📁 File exists: {file_path.exists()}")
    
    if not file_path.exists():
        print(f"❌ File not found on disk: {file_path}")
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    # Read file
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        print(f"✅ File read successfully: {len(content)} bytes")
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        raise HTTPException(status_code=500, detail=f"Error reading file: {e}")
    
    # Determine content type
    content_type_map = {
        "PDF": "application/pdf",
        "PNG": "image/png",
        "JPG": "image/jpeg",
        "JPEG": "image/jpeg",
        "ZIP": "application/zip",
        "MP4": "video/mp4",
        "DOC": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    content_type = content_type_map.get(doc["type"].upper(), "application/octet-stream")
    
    # Get file extension from file_path
    file_ext = doc["file_path"].split(".")[-1] if "." in doc["file_path"] else doc["type"].lower()
    
    # Clean filename for Content-Disposition header (remove special characters)
    import re
    clean_name = re.sub(r'[^\w\s\-\.]', '_', doc["name"])  # Replace special chars with underscore
    clean_name = clean_name.replace(' ', '_')  # Replace spaces with underscores
    
    print(f"✅ Sending file: {content_type}, {len(content)} bytes")
    
    # Return file with download headers
    return Response(
        content=content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{clean_name}.{file_ext}"'
        }
    )


@router.delete("/projects/{project_id}/documents/{doc_id}")
def delete_document(project_id: str, doc_id: str):
    """Delete a project document."""
    docs = _load_documents()
    doc = next((d for d in docs if d["id"] == doc_id and d["project_id"] == project_id), None)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Delete file if exists
    if doc.get("file_path"):
        file_path = DOCUMENTS_DIR / doc["file_path"]
        if file_path.exists():
            file_path.unlink()
    
    # Remove from database
    docs = [d for d in docs if d["id"] != doc_id]
    _save_documents(docs)
    
    return JSONResponse(content={"message": "Document deleted"})
