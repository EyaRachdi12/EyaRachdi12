# ArchiGuide — Platform Documentation

---

## What is ArchiGuide?

ArchiGuide is an AI-powered web platform designed to bridge the gap between architects and their clients. It automates the most time-consuming parts of the architectural design process — analyzing floor plans, understanding client needs, generating visual concepts, and enabling smooth collaboration — all through artificial intelligence.

The platform serves two types of users: **architects** who design and manage projects, and **clients** who describe their needs and follow the progress of their project.

---

## The Two Dashboards

### Architect Dashboard

The architect's workspace is built around four core activities:

**1. Analyzing Floor Plans**
The architect uploads a 2D floor plan image. The AI automatically reads the image and produces a complete description: which rooms are present, their approximate sizes, the architectural style, the orientation, and the number of windows and doors. This saves the architect from manually documenting every plan they work with. The analysis takes about 5 seconds and achieves 85–95% accuracy.

**2. 3D Visualization**
The architect enters a text description of a project (or uses the analyzed plan) and the platform generates an interactive 3D model of the floor plan. The architect can navigate through the rooms, rotate the view, and enable an automatic tour. This helps communicate spatial concepts to clients who struggle to read 2D plans.

**3. Managing Projects and Clients**
The architect has a full client management system — adding clients, tracking project status (pending, in progress, AI analysis, completed), monitoring progress percentages, and viewing analytics about AI usage and project activity over time.

**4. Collaboration**
A built-in messaging system allows the architect to communicate directly with each client, share images of plans and sketches, and keep all project communication in one place.

---

### Client Dashboard

The client's experience is designed to be simple and guided, even for people with no architectural background.

**1. Describing the Project (Brief)**
The client writes a free-text description of what they want — in plain French, as if talking to a friend. For example: *"I want a modern house for my family of 4, with a large open kitchen, 3 bedrooms including a master suite, lots of natural light, and a terrace for barbecues. Budget around 400,000 euros."*

The AI reads this description and automatically structures it into a professional brief with: the desired surface area, the budget range, the architectural style, and a detailed list of rooms with their estimated sizes. This structured brief is then shared with the architect.

**2. Asking Questions About Plans**
Once the architect shares a floor plan, the client can ask questions about it in natural language: *"Where is the bathroom?"*, *"How many windows does the living room have?"*, *"What is the approximate area of the kitchen?"* The AI analyzes the image and answers in French, with a confidence percentage.

**3. Generating Architectural Sketches**
The client can generate visual mood boards and architectural sketches based on their brief. They choose a style (modern, contemporary, minimalist, industrial, Scandinavian, Mediterranean), select elements they want (terrace, pool, garden, garage), and choose the type of view (facade, interior, aerial, garden). The AI generates photorealistic images in seconds.

**4. Following the Project**
The client can track the progress of their project, download documents (brief, sketches, plans), and communicate with their architect through the messaging system.

---

## The AI Models

ArchiGuide uses four distinct AI systems, each specialized for a different task.

---

### Model 1 — Floor Plan Captioning (EfficientNetV2 + Transformer)

**What it does:** Takes a floor plan image as input and outputs a text description of what it sees.

**How it works:**

The model uses two "eyes" to look at the floor plan simultaneously:

- The first eye (**ResNet-101**) focuses on the *spatial structure* — the geometry of walls, the shape and position of rooms, the overall layout. ResNet-101 is a deep neural network originally trained on millions of everyday photos. It has learned to detect shapes, edges, and spatial relationships, which makes it excellent at understanding the geometric structure of floor plans.

- The second eye (**EfficientNetV2**) focuses on the *semantic content* — what type of room is this based on its visual appearance, what furniture or fixtures are visible, what textures and colors are present. EfficientNetV2 is a more modern and efficient network that excels at recognizing what things *are*, not just where they are.

These two sets of features are then merged through a **Cross-Attention Fusion** mechanism. This is a mathematical operation where the spatial features "ask questions" of the semantic features — essentially: *"I see a rectangular region here, what type of room does it look like?"* The result is a rich, combined understanding of the floor plan.

Finally, a **Transformer Decoder** generates the caption word by word. At each step, it looks at the combined visual features and decides what word comes next. It uses a technique called **beam search** — instead of committing to one word at a time, it keeps track of the 3 most promising caption sequences simultaneously and picks the best one at the end.

**Training:**
The model was trained on the **CubicASA5K dataset** — 5,000 annotated floor plan images from real architectural projects. Each image was paired with a structured caption describing the rooms it contains. Training took approximately 1.5 hours on a GPU. The model achieved a validation loss of 0.1328, with near-perfect predictions on many test cases.

**Example output:**
> *"apartment floorplan containing 2 bedrooms, 1 closet, 1 kitchen, 1 living room, 1 bathroom, 1 toilet"*

---

### Model 2 — Brief Analyzer (Phi-3 Mini + LoRA Fine-Tuning)

**What it does:** Takes a free-text description from a client and extracts structured information — surface area, budget, style, and list of desired rooms.

**How it works:**

This model is based on **Phi-3 Mini**, a Large Language Model (LLM) developed by Microsoft with 3.8 billion parameters. LLMs are trained on enormous amounts of text and develop a deep understanding of language — they can read, understand, and generate text in many languages including French.

However, a general-purpose LLM doesn't automatically know how to extract architectural information in a specific JSON format. This is where **LoRA (Low-Rank Adaptation)** comes in.

**What is LoRA?**

Fine-tuning a 3.8 billion parameter model from scratch would require enormous computing resources. LoRA is a clever shortcut: instead of modifying all the model's parameters, it adds small "adapter" layers to specific parts of the model. These adapters contain only about 13 million parameters (0.34% of the total) and are the only thing that gets trained. The rest of the model stays frozen.

Think of it like this: the base model is a highly educated person who speaks French fluently. LoRA is like giving them a short specialized training course in architectural terminology and JSON formatting — without changing everything they already know.

**Training data:**
50 diverse examples of French architectural briefs were created, covering:
- Budgets from 120,000€ to 1,300,000€
- Surfaces from 30m² to 320m²
- 15+ architectural styles (modern, rustic, ecological, industrial, Scandinavian, seaside, chalet, Haussmann, bioclimatic, container, minimalist...)
- All types of projects (studio, T2 to T5, villa, penthouse, farmhouse, loft)

Each example pairs a natural language description with the correct structured JSON output. The model learned to always produce the same JSON keys: `surface_souhaitee`, `budget`, `style`, and `pieces_souhaitees`.

**Training results:**
The model converged in 6 epochs (about 8 minutes on a GPU), achieving a validation loss of 0.2017. On new briefs never seen during training, it correctly extracts surface, budget, style, and room list.

**Example:**

Input: *"Petite maison pour couple, environ 80m². 2 chambres, cuisine fonctionnelle, petit jardin. Budget 250 000 euros. Style simple."*

Output:
```
Surface: 70-90 m²
Budget: 220,000 – 280,000 €
Style: Fonctionnel
Rooms: Salon/Séjour (25-30 m²), Cuisine (10-12 m²),
       Chambre principale (14-16 m²), Chambre 2 (10-12 m²),
       Salle de bain (6-8 m²), Jardin (50 m²)
```

---

### Model 3 — Visual Q&A (Google Gemini Flash 2.0)

**What it does:** Answers natural language questions about floor plan images.

**How it works:**

Gemini Flash 2.0 is a multimodal AI model from Google — it can process both images and text simultaneously. When a client asks a question about a floor plan, the image and the question are sent together to Gemini, which analyzes the visual content and formulates a relevant answer in French.

This model was not trained by us — it is used as an external API service. Its strength lies in its ability to understand complex visual scenes and answer open-ended questions, which would be extremely difficult to achieve with a custom-trained model.

**Types of questions it handles:**
- Location: *"Where is the bathroom?"*
- Counting: *"How many bedrooms are there?"*
- Surface estimation: *"What is the approximate area of the living room?"*
- Presence: *"Is there a terrace?"*
- Style: *"What architectural style is this plan?"*

---

### Model 4 — Sketch Generation (FLUX via Pollinations.ai)

**What it does:** Generates photorealistic architectural images from text descriptions.

**How it works:**

FLUX is a state-of-the-art text-to-image generation model. The platform constructs a detailed prompt based on the client's choices (style, elements, view type) and sends it to the Pollinations.ai service, which runs FLUX and returns the generated image.

The prompt engineering is done automatically — the platform translates the client's selections into a rich English prompt optimized for architectural photography, such as: *"contemporary house facade, modern architecture, large glass windows, terrace, garden, professional architectural photography, natural light, 8k"*

This service is completely free and requires no API key.

---

## How the Platform Connects Everything

The platform is built as a **web application** with two parts that communicate with each other:

**The frontend** (what users see in their browser) is built with Next.js, a modern React framework. It handles all the visual interface — the dashboards, forms, image uploads, 3D viewer, and chat.

**The backend** (the server that does the heavy work) is built with FastAPI, a Python framework. It receives requests from the frontend, runs the AI models, and returns results. All AI processing happens here.

When a user performs an action — uploading a plan, submitting a brief, asking a question — the frontend sends a request to the backend API. The backend processes it (often using one of the AI models), and sends back the result, which the frontend then displays.

The database is simple: all data (users, projects, clients, messages, briefs) is stored in JSON files on the server. This keeps the system lightweight and easy to understand.

---

## Summary of What Each Part Delivers

| Component | What it delivers to the user |
|-----------|------------------------------|
| Floor Plan Analysis | Automatic room detection and description from any floor plan image |
| Brief Structuring | Converts a casual description into a professional architectural brief |
| Visual Q&A | Instant answers to questions about floor plans |
| 3D Visualization | Interactive 3D model navigable in the browser |
| Sketch Generation | Photorealistic architectural images in seconds |
| Messaging | Direct communication between architect and client |
| Project Management | Full tracking of projects, clients, documents, and progress |
| Analytics | Insights into AI usage and project activity |

---

## The Value Proposition

Before ArchiGuide, an architect would spend significant time:
- Manually documenting floor plans
- Translating vague client descriptions into structured requirements
- Creating 3D models with specialized software
- Generating mood boards with design tools
- Managing client communication across multiple platforms

ArchiGuide automates all of these tasks with AI, allowing architects to focus on what they do best — designing — while giving clients a clear, guided experience to express and visualize their needs.
