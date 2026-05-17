# ArchiGuide — AI-Powered Architectural Platform

> An intelligent platform connecting architects and clients through AI-powered floor plan analysis, 3D visualization, brief structuring, and real-time collaboration.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tech Stack](#2-tech-stack)
3. [Architecture Overview](#3-architecture-overview)
4. [AI Models](#4-ai-models)
5. [Frontend Pages](#5-frontend-pages)
6. [Backend API](#6-backend-api)
7. [Data Models](#7-data-models)
8. [Key Workflows](#8-key-workflows)
9. [Setup & Installation](#9-setup--installation)
10. [Project Structure](#10-project-structure)

---

## 1. Project Overview

ArchiGuide is a full-stack web platform that uses multiple AI models to assist architects and their clients throughout the architectural design process.

### What it does

| Feature | Description |
|---------|-------------|
| **Floor Plan Analysis** | Upload a 2D floor plan → AI generates a detailed description |
| **Visual Q&A** | Ask questions about a floor plan in natural language |
| **Brief Structuring** | Client describes project → AI extracts structured requirements |
| **3D Visualization** | Generate interactive 3D floor plan from description |
| **Sketch Generation** | AI generates architectural mood boards and sketches |
| **Collaboration** | Real-time messaging between architect and client |

### User Roles

- **Architect** — uploads plans, analyzes them, manages clients and projects
- **Client** — describes their project, asks questions, views sketches and plans

---

## 2. Tech Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16.2.4 | React framework with App Router |
| React | 19.2.4 | UI library |
| TypeScript | 5 | Type safety |
| Three.js | 0.169.0 | 3D floor plan visualization |
| Tailwind CSS | 4 | Styling |

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI | REST API framework |
| PyTorch | Deep learning inference |
| Transformers (HuggingFace) | LLM and vision models |
| PEFT | LoRA fine-tuning |
| OpenCV | Computer vision |
| Uvicorn | ASGI server |

### AI Services
| Service | Purpose |
|---------|---------|
| Google Gemini Flash 2.0 | Visual Q&A on floor plans |
| Pollinations.ai (FLUX) | Architectural sketch generation |
| HuggingFace | Model hosting |

### Storage
- JSON files (local database)
- File system (images, documents)

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                        │
│                                                              │
│  /architect/*          /client/*           /explorer        │
│  Dashboard             Dashboard           Browse Plans      │
│  Upload Plan           Brief               VQA              │
│  Visualize 3D          Sketches            Analyze          │
│  Analytics             Messages                             │
│  Messages              Projects                             │
│  Clients                                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP REST API
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (FastAPI)                          │
│                                                              │
│  /api/analyze-plan      /api/ask-plan                       │
│  /api/analyze-brief-lora /api/parse-description             │
│  /api/generate-sketches  /api/projects                      │
│  /api/messages           /api/clients                       │
│  /api/briefs             /api/auth                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
   │  AI Models  │  │  JSON Files  │  │ External APIs│
   │             │  │  (Database)  │  │              │
   │ ResNet+LSTM │  │ users.json   │  │ Gemini Flash │
   │ EfficientNet│  │ projects.json│  │ Pollinations │
   │ +Transformer│  │ clients.json │  │              │
   │ Phi-3 LoRA  │  │ messages.json│  │              │
   │ Gemini      │  │ briefs.json  │  │              │
   └─────────────┘  └──────────────┘  └──────────────┘
```

---

## 4. AI Models

### 4.1 Floor Plan Captioning — EfficientNetV2 + Transformer

**Purpose:** Analyze a floor plan image and generate a structured text description.

**Architecture:**
```
Image (384×384)
      │
  ┌───┴───┐
  │       │
ResNet-101  EfficientNetV2-S
(Spatial)   (Semantic)
  │       │
  └───┬───┘
      │
Cross-Attention Fusion
      │
Transformer Decoder (6 layers)
      │
"apartment floorplan containing
 2 bedrooms, 1 kitchen, 1 bathroom"
```

| Property | Value |
|----------|-------|
| Dataset | CubicASA5K (5,000 floor plans) |
| Training | Google Colab T4 GPU, ~1.5 hours |
| Best Val Loss | 0.1328 |
| Inference time | ~5 seconds |
| Model file | `models/weights/best_floorplan_model.pth` |

### 4.2 Brief Analyzer — Phi-3 Mini + LoRA

**Purpose:** Parse a French architectural brief (natural language) into structured JSON.

**Architecture:**
```
"Je veux une maison moderne 120m², 3 chambres, budget 400k€"
                    │
            Phi-3 Mini (3.8B params, frozen)
                    │
            LoRA Adapters (13M params, trained)
                    │
{
  "surface_souhaitee": "115-128 m2",
  "budget": "370000-430000",
  "style": "Moderne contemporain",
  "pieces_souhaitees": [...]
}
```

| Property | Value |
|----------|-------|
| Base model | microsoft/Phi-3-mini-4k-instruct |
| LoRA rank | r=16, alpha=32 |
| Training data | 50 diverse French architectural briefs |
| Trainable params | 13M / 3.8B (0.34%) |
| Model files | `models/phi3-brief-lora/` |

### 4.3 Visual Q&A — Google Gemini Flash 2.0

**Purpose:** Answer natural language questions about floor plan images.

**Examples:**
- "Où est la salle de bain ?" → "La salle de bain se trouve en haut à droite..."
- "Combien de chambres ?" → "Ce plan contient 3 chambres..."
- "Quelle est la surface du salon ?" → "Le salon fait environ 28 m²..."

### 4.4 Sketch Generation — FLUX via Pollinations.ai

**Purpose:** Generate architectural mood boards and sketches from text descriptions.

**Features:**
- 6 architectural styles (Moderne, Contemporain, Minimaliste, Industriel, Scandinave, Méditerranéen)
- 4 view types (Façade, Intérieur, Vue aérienne, Jardin)
- Custom elements (terrasse, piscine, jardin, garage...)
- Free, no API key required

### 4.5 Smart CV Captioner (Fallback)

**Purpose:** Rule-based computer vision analysis when AI models are unavailable.

**Techniques:**
- Adaptive thresholding for wall detection
- Connected components for room detection
- Hough lines for opening detection
- Brightness/contrast analysis for style detection

---

## 5. Frontend Pages

### Architect Dashboard

#### `/architect/dashboard`
Overview of all activity.
- Stats: total projects, active projects, clients, messages
- Recent projects with progress bars
- Quick actions: analyze plan, generate video, create project

#### `/architect/upload` — Analyser Plan
Upload and analyze floor plans with AI.
- Drag-and-drop image upload
- Real-time AI analysis progress
- Results: caption, rooms list, surfaces, style, confidence %
- Actions: share with client, generate 3D

#### `/architect/visualize` — Visualisation 3D
Generate interactive 3D floor plans.
- Upload reference image + enter description
- Three.js 3D viewer with room navigation
- Auto-tour mode, zoom, pan controls
- Room highlighting and info panels

#### `/architect/projects` — Projets
Manage all architectural projects.
- Filter by status (En cours, Analyse IA, Terminé, En attente)
- Search by name or client
- Create new project with client assignment

#### `/architect/analytics` — Analytiques
Track AI usage and project activity.
- Monthly activity bar chart
- AI model usage pie chart
- Top active projects

#### `/architect/messages` — Messages
Real-time chat with clients.
- Conversation list with unread counts
- Image attachment support
- Message timestamps

#### `/architect/clients` — Clients
Manage client database.
- Client cards with contact info and project status
- Add/remove clients
- Direct message from client card

---

### Client Dashboard

#### `/client/dashboard`
Project status overview.
- Active project with progress, dates, budget
- Brief summary with AI-generated caption
- Quick actions: brief, questions, sketches, messages

#### `/client/brief` — Mon Brief
Create and structure project brief with AI.
- Free-text description input
- AI analysis with progress indicators (LoRA Phi-3 Mini)
- Structured result: surface, budget, style, rooms
- Save and modify options

#### `/client/vqa` — Questions sur Plan
Ask questions about floor plans.
- Upload plan or select from library
- Chat interface with AI responses
- Suggested questions for quick access
- Confidence percentage per answer

#### `/client/sketches` — Esquisses IA
Generate architectural sketches.
- Style selector (6 options)
- Element checkboxes (terrasse, piscine, jardin...)
- View type selection
- Gallery of generated images with like/share

#### `/client/projects` — Mes Projets
View project details and documents.
- Project info: status, progress, architect, dates
- Document list: brief, sketches, videos
- Download documents

#### `/client/messages` — Messages
Chat with architect.
- Same interface as architect side
- Image sharing support

---

### Public Pages

#### `/` — Home
Landing page with features showcase, gallery, testimonials.

#### `/explorer` — Explorer
Browse floor plan library.
- Filter by type (Studio, T2, T3, T4, T5, Loft) and style
- Analyze any plan with AI
- Download plans

#### `/auth/login` and `/auth/register`
Authentication with role selection (architect/client).

---

## 6. Backend API

### Base URL
```
http://localhost:8000
```

### Endpoints

#### Floor Plan Analysis
```
POST /api/analyze-plan
Content-Type: multipart/form-data
Body: file (image)

Response:
{
  "caption": "Plan T3 de style contemporain...",
  "rooms": [{"name": "Salon", "area": 28, "windows": 2}],
  "total_area": 95,
  "style": "Contemporain",
  "confidence": 0.92,
  "inference_time_s": 5.2
}
```

#### Brief Analysis (LoRA)
```
POST /api/analyze-brief-lora
Content-Type: application/json
Body: {"description": "Maison 120m², 3 chambres, budget 400k€"}

Response:
{
  "surface_souhaitee": "115-128 m2",
  "budget": "370000-430000",
  "style": "Moderne contemporain",
  "pieces_souhaitees": [...]
}
```

#### Visual Q&A
```
POST /api/ask-plan
Content-Type: multipart/form-data
Body: file (image), question (string)

Response:
{
  "answer": "La salle de bain se trouve...",
  "confidence": 0.92,
  "method": "gemini"
}
```

#### Description Parsing
```
POST /api/parse-description
Content-Type: application/json
Body: {"description": "Maison 3 chambres, salon, cuisine"}

Response:
{
  "rooms": [{"name": "Salon / Séjour", "area": 28}],
  "total_area": 95,
  "style": "contemporain",
  "has_garden": false,
  "has_pool": false
}
```

#### Sketch Generation
```
POST /api/generate-sketches-ai
Content-Type: application/json
Body: {
  "style": "Contemporain",
  "description": "Maison moderne avec terrasse",
  "elements": ["terrasse", "jardin"],
  "view_types": ["facade", "interior"]
}

Response:
{
  "images": [
    {"url": "data:image/png;base64,...", "view": "facade"}
  ]
}
```

#### Projects
```
GET  /api/projects?architect_id=xxx
POST /api/projects
GET  /api/projects/{id}
```

#### Clients
```
GET    /api/clients
POST   /api/clients
DELETE /api/clients/{id}
```

#### Messages
```
GET  /api/conversations
POST /api/conversations
GET  /api/messages/{conv_id}
POST /api/messages/{conv_id}
```

#### Briefs
```
POST /api/briefs
GET  /api/briefs/{client_id}
```

#### Auth
```
POST /api/auth/login
POST /api/auth/register
```

---

## 7. Data Models

### User
```json
{
  "id": "uuid",
  "name": "Mohamed Architect",
  "email": "arch@example.com",
  "role": "architect",
  "specialty": "Résidentiel",
  "city": "Paris",
  "phone": "+33 6 12 34 56 78"
}
```

### Project
```json
{
  "id": "uuid",
  "name": "Villa Moderne",
  "client_id": "uuid",
  "architect_id": "uuid",
  "status": "En cours",
  "progress": 65,
  "type": "Villa",
  "area": 180,
  "budget": "650 000 €",
  "date": "2026-01-15"
}
```

### Brief
```json
{
  "client_id": "uuid",
  "description": "Je veux une maison moderne...",
  "rooms": [{"name": "Salon", "area": "28-32 m²", "notes": "lumineux"}],
  "total_area": 120,
  "style": "Contemporain",
  "budget": "350000-450000",
  "priorities": ["Luminosité", "Espace"],
  "constraints": ["Terrain en pente"]
}
```

### Message
```json
{
  "id": "uuid",
  "sender_role": "architect",
  "sender": "Mohamed",
  "text": "Voici le plan analysé...",
  "time": "14:32",
  "image_url": null,
  "conversation_id": "uuid"
}
```

---

## 8. Key Workflows

### Workflow 1: Architect Analyzes a Floor Plan
```
1. Architect goes to /architect/upload
2. Drags floor plan image onto upload zone
3. Frontend sends POST /api/analyze-plan
4. Backend loads EfficientNetV2 + Transformer model
5. Model generates: caption, rooms, surfaces, style
6. Results displayed: room cards, total area, confidence
7. Architect can share results with client via messages
```

### Workflow 2: Client Creates a Brief
```
1. Client goes to /client/brief
2. Types project description in French
3. Frontend sends POST /api/analyze-brief-lora
4. Backend loads Phi-3 Mini + LoRA adapters
5. Model extracts: surface, budget, style, rooms
6. Structured brief displayed with all fields
7. Client saves brief → stored in briefs.json
```

### Workflow 3: Client Asks Questions About a Plan
```
1. Client goes to /client/vqa
2. Uploads floor plan image
3. Types question: "Où est la cuisine ?"
4. Frontend sends POST /api/ask-plan
5. Backend sends image + question to Gemini Flash 2.0
6. Gemini analyzes image and answers in French
7. Answer displayed with confidence percentage
```

### Workflow 4: Generate 3D Visualization
```
1. Architect goes to /architect/visualize
2. Uploads reference floor plan + enters description
3. Frontend sends POST /api/parse-description-with-image
4. Backend uses CV to extract room positions from image
5. Returns rooms with x/z/w/d coordinates
6. Three.js renders interactive 3D floor plan
7. Architect can navigate rooms, enable auto-tour
```

### Workflow 5: Generate Architectural Sketches
```
1. Client goes to /client/sketches
2. Selects style, elements, view types
3. Frontend sends POST /api/generate-sketches-ai
4. Backend builds architectural prompts
5. Calls Pollinations.ai (FLUX model) for each view
6. Returns base64-encoded images
7. Client views gallery, likes/shares with architect
```

---

## 9. Setup & Installation

### Prerequisites
- Node.js 18+
- Python 3.11+
- GPU recommended (for AI models)

### Frontend Setup
```bash
cd DEEP/archi-platform
npm install
npm run dev
# Runs on http://localhost:3000
```

### Backend Setup
```bash
cd DEEP/archi-platform/backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Start server
python main.py
# Runs on http://localhost:8000
```

### Environment Variables
Create `backend/.env`:
```env
GEMINI_API_KEY=your_gemini_api_key
HF_API_TOKEN=your_huggingface_token  # optional
GROQ_API_KEY=your_groq_key           # optional
LUMA_API_KEY=your_luma_key           # optional
```

### AI Model Files
Place trained model weights in:
```
backend/models/weights/
  best_floorplan_model.pth    ← EfficientNetV2+Transformer (floor plan captioning)
  best_model.pth              ← ResNet-101+LSTM (legacy)

backend/models/phi3-brief-lora/
  adapter_model.safetensors   ← LoRA adapters (brief analysis)
  adapter_config.json
  tokenizer.json
  tokenizer.model
  tokenizer_config.json
```

---

## 10. Project Structure

```
DEEP/archi-platform/
├── app/                          # Next.js frontend
│   ├── architect/                # Architect pages
│   │   ├── dashboard/page.tsx
│   │   ├── upload/page.tsx       # Floor plan analysis
│   │   ├── visualize/page.tsx    # 3D visualization
│   │   ├── projects/page.tsx
│   │   ├── analytics/page.tsx
│   │   ├── messages/page.tsx
│   │   └── clients/page.tsx
│   ├── client/                   # Client pages
│   │   ├── dashboard/page.tsx
│   │   ├── brief/page.tsx        # AI brief structuring
│   │   ├── vqa/page.tsx          # Visual Q&A
│   │   ├── sketches/page.tsx     # AI sketch generation
│   │   ├── projects/page.tsx
│   │   └── messages/page.tsx
│   ├── auth/                     # Authentication
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   ├── explorer/page.tsx         # Floor plan library
│   ├── settings/page.tsx
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Home page
│   └── globals.css
│
├── backend/                      # FastAPI backend
│   ├── main.py                   # App entry point, router registration
│   ├── routes/                   # API endpoints
│   │   ├── analyze.py            # Floor plan analysis
│   │   ├── analyze_brief_lora.py # Brief analysis (LoRA)
│   │   ├── vqa.py                # Visual Q&A
│   │   ├── parse_description.py  # Text parsing
│   │   ├── briefs.py             # Brief storage
│   │   ├── projects.py           # Project management
│   │   ├── clients.py            # Client management
│   │   ├── messages.py           # Messaging
│   │   ├── auth.py               # Authentication
│   │   ├── generate_sketches.py  # Sketch generation
│   │   ├── floor_plans_ai.py     # Floor plan library
│   │   ├── analytics.py          # Analytics
│   │   └── stats.py              # Statistics
│   ├── models/                   # AI model classes
│   │   ├── caption_model.py      # ResNet-101 + LSTM
│   │   ├── floorplan_captioner_v2.py  # EfficientNetV2 + Transformer
│   │   ├── brief_analyzer_lora.py     # Phi-3 Mini + LoRA
│   │   ├── vqa_model.py          # VQA model
│   │   ├── gemini_client.py      # Gemini API
│   │   ├── image_generator.py    # FLUX sketch generation
│   │   ├── smart_captioner.py    # CV-based fallback
│   │   ├── vocabulary.py         # Caption vocabulary
│   │   ├── weights/              # Trained model files
│   │   │   ├── best_floorplan_model.pth
│   │   │   └── best_model.pth
│   │   └── phi3-brief-lora/      # LoRA adapters
│   │       ├── adapter_model.safetensors
│   │       └── ...
│   ├── data/                     # JSON database
│   │   ├── users.json
│   │   ├── projects_db.json
│   │   ├── clients_db.json
│   │   ├── conversations.json
│   │   └── project_documents.json
│   └── requirements.txt
│
├── DOC_FloorPlan_Captioning_Architecture.md  # Model 1 documentation
├── DOC_LoRA_FineTuning_LLM.md               # Model 2 documentation
└── README.md                                 # This file
```

---

## Additional Documentation

- **[Floor Plan Captioning Model](backend/DOC_FloorPlan_Captioning_Architecture.md)** — Detailed explanation of the EfficientNetV2 + Transformer architecture, training process, and results
- **[LoRA Fine-Tuning Guide](backend/DOC_LoRA_FineTuning_LLM.md)** — How Phi-3 Mini was fine-tuned with LoRA for architectural brief analysis
