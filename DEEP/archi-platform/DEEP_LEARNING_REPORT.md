# ArchiGuide — Deep Learning Components Report

---

## Overview

ArchiGuide uses two custom-trained deep learning models and integrates two external AI APIs. This document covers the deep learning work done from scratch, followed by a brief mention of the external services used.

---

## Part 1 — Floor Plan Captioning Model

### Task

Given a 2D floor plan image, automatically generate a structured text description of the rooms it contains.

**Input:** Floor plan image (384×384 pixels)
**Output:** `"apartment floorplan containing 2 bedrooms, 1 kitchen, 1 bathroom, 1 living room"`

---

### Dataset — CubicASA5K

- 5,000 annotated floor plan images from real architectural projects
- Each image comes with an SVG file containing room labels and positions
- The SVG files are parsed to extract room types, which are then converted into structured captions
- Split: 90% training (4,500 images) / 10% validation (500 images)

Caption format used:
> *"apartment floorplan containing 2 bedrooms, 1 kitchen, 1 bathroom, 1 living room, 1 closet"*

Room types covered: bedroom, bathroom, kitchen, living room, dining room, balcony, closet, storage, toilet, terrace, garage, office, room.

---

### Architecture — Dual Encoder + Transformer Decoder

The model is composed of three main blocks:

---

#### Block 1 — Spatial Encoder (ResNet-101)

ResNet-101 is a deep convolutional neural network with 101 layers, pre-trained on ImageNet. It is used here to extract **spatial features** from the floor plan — the geometry of walls, the shape and position of rooms, the overall layout structure.

The network produces a feature map of shape **(B, 2048, H, W)** which is then flattened into a sequence of spatial tokens **(B, N, 2048)** and projected down to **(B, N, 512)** via a linear layer.

**Fine-tuning strategy:** The early layers (layers 0–2) are frozen to preserve low-level feature detectors. Only layers 3 and 4 are fine-tuned to adapt to the floor plan domain.

| Property | Value |
|----------|-------|
| Architecture | ResNet-101 |
| Pre-training | ImageNet |
| Output channels | 2048 |
| Projection | Linear(2048 → 512) |
| Frozen | layers 0, 1, 2 |
| Fine-tuned | layers 3, 4 |

---

#### Block 2 — Semantic Encoder (EfficientNetV2-S)

EfficientNetV2-S is a more recent and efficient convolutional network, also pre-trained on ImageNet. It is used to extract **semantic features** — what type of room is this based on its visual appearance, what fixtures or furniture are visible, what textures and colors are present.

The network produces a feature map of shape **(B, 1280, H, W)**, flattened to **(B, M, 1280)** and projected to **(B, M, 512)**.

**Fine-tuning strategy:** Blocks 0–3 are frozen. Blocks 4, 5, and 6 are fine-tuned.

| Property | Value |
|----------|-------|
| Architecture | EfficientNetV2-S |
| Pre-training | ImageNet |
| Output channels | 1280 |
| Projection | Linear(1280 → 512) |
| Frozen | blocks 0–3 |
| Fine-tuned | blocks 4, 5, 6 |

---

#### Block 3 — Cross-Attention Fusion

The spatial features (from ResNet-101) and semantic features (from EfficientNetV2) are merged using a **Cross-Attention** mechanism.

The spatial features act as the **Query** — they ask: *"Given what I know about the geometry here, what semantic information is relevant?"*
The semantic features act as the **Key** and **Value** — they answer: *"Here is what this region looks like semantically."*

The fusion block also includes:
- Layer normalization with residual connections
- A Feed-Forward Network (FFN) with GELU activation
- Dropout (0.1) for regularization

Output shape: **(B, N, 512)** — a unified representation combining spatial and semantic understanding.

---

#### Block 4 — Transformer Decoder

The decoder generates the caption token by token, attending to the fused visual features at each step.

**Components:**
- **Embedding layer:** converts token IDs to 512-dimensional vectors
- **Positional encoding:** adds position information (sinusoidal, max length 5000)
- **Dropout:** applied after positional encoding (rate 0.1)
- **6 TransformerDecoderLayers**, each containing:
  - Masked self-attention (causal — each token only sees previous tokens)
  - Cross-attention over the visual memory
  - Feed-forward network
  - Layer normalization
- **Output projection:** Linear(512 → vocab_size)

**Tokenizer:** BERT (bert-base-uncased), vocabulary size 30,522.

| Property | Value |
|----------|-------|
| Layers | 6 |
| Attention heads | 8 |
| Embedding dimension | 512 |
| Max caption length | 64 tokens |
| Dropout | 0.1 |
| Tokenizer | BERT (bert-base-uncased) |

---

### Training Details

| Hyperparameter | Value |
|----------------|-------|
| Image size | 384 × 384 |
| Batch size | 8 |
| Max epochs | 30 |
| Learning rate | 2 × 10⁻⁴ |
| Optimizer | AdamW |
| Weight decay | 1 × 10⁻⁴ |
| Gradient clipping | 1.0 |
| Label smoothing | 0.1 |
| LR scheduler | CosineAnnealingLR |
| Early stopping | patience = 5 |
| Training method | Teacher forcing |

**Data augmentation (training only):**
- Random rotation (±3°)
- Random horizontal flip (50%)
- Color jitter (brightness, contrast, saturation ±10%)
- ImageNet normalization

**Loss function:** Cross-Entropy with label smoothing (0.1) and padding token ignored.

**Teacher forcing:** During training, the model receives the correct previous token at each step rather than its own prediction. This accelerates convergence significantly.

---

### Inference — Beam Search

At inference time, the model generates captions using beam search with beam size 3:

1. Start with the `[CLS]` token
2. At each step, expand the top-3 sequences by generating the top-3 next tokens for each
3. Keep the top-3 sequences by **length-normalized score** (total log-probability divided by sequence length)
4. Stop when all sequences end with `[SEP]` or reach maximum length
5. Return the highest-scoring complete sequence

Length normalization prevents the model from preferring artificially short captions.

---

### Results

| Epoch | Train Loss | Val Loss |
|-------|-----------|---------|
| 1 | 0.3918 | 0.1698 |
| 4 | 0.1540 | 0.1474 |
| 6 | 0.1448 | 0.1402 |
| **9** | **0.1239** | **0.1328** ← Best |
| 14 | 0.0919 | 0.1405 |
| — | ⛔ Early stopping | — |

**Best model saved at epoch 9, val loss = 0.1328**

**Qualitative results (sample predictions):**

| Ground Truth | Prediction | Result |
|-------------|-----------|--------|
| apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 toilet | apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 toilet | ✅ Perfect |
| apartment floorplan containing 1 balcony, 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 toilet | apartment floorplan containing 1 balcony, 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 toilet | ✅ Perfect |
| apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 storage, 1 toilet | apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 storage, 1 toilet | ✅ Perfect |
| apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 terrace, 1 toilet | apartment floorplan containing 1 bedroom, 1 closet, 1 kitchen, 1 living room, 1 room, 1 toilet | ⚠️ Missed terrace |

---

## Part 2 — Architectural Brief Analyzer (LoRA Fine-Tuning)

### Task

Given a free-text description of an architectural project in French, extract structured information: desired surface area, budget, architectural style, and list of rooms with sizes.

**Input:** *"Je veux une maison moderne pour ma famille de 4 personnes, 3 chambres, budget 400 000 euros."*

**Output:**
```
surface_souhaitee: "115-128 m2"
budget: "370000-430000"
style: "Moderne contemporain"
pieces_souhaitees: [Salon/Séjour, Cuisine, Chambre principale, Chambre 2, Chambre 3, Salle de bain]
```

---

### Base Model — Phi-3 Mini

Phi-3 Mini is a Large Language Model (LLM) developed by Microsoft with **3.8 billion parameters**. It supports a 4,096-token context window and has strong multilingual capabilities including French. It was chosen because:

- Small enough to run on a single T4 GPU (Colab free tier)
- Strong instruction-following capability
- Good French language understanding
- Open license (MIT), no authentication required

---

### Fine-Tuning Method — LoRA

**Why not full fine-tuning?**
Fine-tuning all 3.8 billion parameters would require hundreds of GB of GPU memory and days of training. With only 50 training examples, it would also cause severe overfitting.

**What is LoRA?**
LoRA (Low-Rank Adaptation) adds small trainable matrices to specific layers of the frozen base model. For a weight matrix **W** of shape (d × d), LoRA adds two matrices **A** (d × r) and **B** (r × d) where r is the rank (much smaller than d). The adapted output becomes:

> **output = W·x + (B·A)·x × (α/r)**

With rank r=16 and d=4096, instead of training 16 million parameters per layer, LoRA trains only 2 × 4096 × 16 = **131,072 parameters** — 120× fewer.

**LoRA configuration:**

| Parameter | Value | Meaning |
|-----------|-------|---------|
| Rank (r) | 16 | Bottleneck dimension of adapter matrices |
| Alpha (α) | 32 | Scaling factor (α/r = 2) |
| Target modules | q_proj, k_proj, v_proj, o_proj | All attention projections |
| Dropout | 0.05 | Regularization on adapter layers |
| Trainable params | ~13 million | 0.34% of total model |

---

### Training Data

**50 diverse French architectural briefs** were manually created, covering:

| Dimension | Range |
|-----------|-------|
| Budget | 120,000€ → 1,300,000€ |
| Surface | 30m² → 320m² |
| Styles | Moderne, Contemporain, Rustique, Écologique, Industriel, Scandinave, Balnéaire, Chalet, Haussmannien, Bioclimatique, Container, Minimaliste, Luxe |
| Project types | Studio, T2, T3, T4, T5, Villa, Penthouse, Maison de campagne, Loft, Duplex |

Split: 80% training (40 examples) / 20% validation (10 examples).

**Prompt format (Llama-3 instruction template):**

The system prompt explicitly specifies the exact JSON keys the model must produce. Without this, the model generates inconsistent key names across different requests. The prompt instructs the model to output only valid JSON with the keys: `surface_souhaitee`, `budget`, `style`, and `pieces_souhaitees`.

---

### Training Details

| Hyperparameter | Value |
|----------------|-------|
| Base model | microsoft/Phi-3-mini-4k-instruct |
| Epochs | 15 |
| Batch size | 1 (gradient accumulation × 2 = effective batch 2) |
| Learning rate | 2 × 10⁻⁴ |
| Optimizer | AdamW (no bitsandbytes) |
| LR scheduler | CosineAnnealingLR |
| Warmup steps | 20 |
| Precision | FP32 for LoRA params, FP16 for base model |
| Evaluation | After each epoch |
| Best model | Loaded automatically at end of training |

**Critical technical note:** LoRA adapter parameters must be cast to FP32 even when the base model runs in FP16. Without this, gradient unscaling fails during backpropagation.

---

### Results

| Epoch | Train Loss | Val Loss |
|-------|-----------|---------|
| 1 | 0.6783 | 0.4737 |
| 2 | 0.2565 | 0.2266 |
| 4 | 0.1789 | 0.2021 |
| **6** | **0.1404** | **0.2017** ← Best |
| 9 | 0.0671 | 0.2456 |
| 15 | 0.0267 | 0.3049 |

**Best model at epoch 6, val loss = 0.2017**

The model converges rapidly (loss drops from 0.68 to 0.14 in 6 epochs) then begins to overfit (training loss continues to decrease while validation loss increases). The `load_best_model_at_end` setting automatically recovers the epoch-6 checkpoint.

**Qualitative results:**

Test brief: *"Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k euros"*

Output:
```
surface_souhaitee: "115-128 m2"    ✅ Correct range
budget: "370000-430000"             ✅ Correct range
style: "Moderne contemporain"       ✅ Correct
pieces_souhaitees:
  - Salon/Séjour (36-40 m²)        ✅
  - Cuisine (16-18 m²)             ✅
  - Chambre principale (19-21 m²)  ✅
  - Chambre 2 (14-16 m²)          ✅
  - Chambre 3 (12-14 m²)          ✅
  - Salle de bain (9-11 m²)       ✅
```

**Saved model size:** ~14 MB (LoRA adapters only). The base model (~7 GB) is downloaded separately from HuggingFace at inference time.

---

## Part 3 — External APIs Used in the Dashboard

The following external services are integrated into the platform. They are not trained by us — they are called via API.

---

### Google Gemini Flash 2.0

**Used for:** Visual Question Answering (VQA) on floor plans.

When a client asks a question about a floor plan image, the image and the question are sent to Gemini Flash 2.0 via the Google AI API. Gemini is a multimodal model capable of understanding both images and text simultaneously. It analyzes the floor plan visually and formulates a relevant answer in French.

**Why Gemini and not a custom model?** Open-ended visual question answering over arbitrary floor plans requires a very large and capable model. Training such a model from scratch would require millions of annotated image-question-answer pairs. Gemini provides this capability instantly via API.

---

### Pollinations.ai — FLUX Model

**Used for:** Generating architectural sketches and mood boards.

When a client requests architectural sketches, the platform constructs a detailed text prompt based on their style and element choices, then sends it to Pollinations.ai which runs the FLUX text-to-image model. The generated images are returned as base64-encoded PNG files.

**Why Pollinations.ai?** It provides free access to the FLUX model with no API key required, making it accessible for a student project without cost constraints.

---

### Summary Table

| Component | Type | Task | Where used |
|-----------|------|------|-----------|
| ResNet-101 + EfficientNetV2 + Transformer | Custom trained | Floor plan captioning | Architect upload page |
| Phi-3 Mini + LoRA | Custom fine-tuned | Brief structuring | Client brief page |
| Google Gemini Flash 2.0 | External API | Visual Q&A | Client VQA page |
| Pollinations.ai (FLUX) | External API | Sketch generation | Client sketches page |
