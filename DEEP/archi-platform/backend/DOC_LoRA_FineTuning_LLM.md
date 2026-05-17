# LoRA Fine-Tuning of Phi-3 Mini — Architectural Brief Analyzer

## Overview

This document explains how we fine-tuned a Large Language Model (LLM) to analyze French architectural client briefs and extract structured JSON data.

**Input (natural language):**
> *"Je veux construire une maison moderne pour ma famille de 4 personnes. Grande cuisine ouverte, 3 chambres, budget 400 000 euros."*

**Output (structured JSON):**
```json
{
  "surface_souhaitee": "120-140 m2",
  "budget": "370000-430000",
  "style": "Contemporain",
  "pieces_souhaitees": [
    {"nom": "Salon/Sejour", "surface": "30-35 m2"},
    {"nom": "Cuisine", "surface": "15-20 m2"},
    {"nom": "Chambre principale", "surface": "20-25 m2"},
    {"nom": "Chambre 2", "surface": "14-16 m2"},
    {"nom": "Chambre 3", "surface": "12-14 m2"}
  ]
}
```

---

## 1. What is LoRA?

**LoRA (Low-Rank Adaptation)** is a technique to fine-tune large language models efficiently without retraining all parameters.

### The Problem with Full Fine-Tuning
A model like Phi-3 Mini has **3.8 billion parameters**. Retraining all of them requires:
- Hundreds of GB of GPU memory
- Weeks of training time
- Massive datasets

### How LoRA Solves This

Instead of modifying all weights, LoRA adds small **adapter matrices** to specific layers:

```
Original weight matrix W (frozen):
W ∈ R^(d × d)   — e.g., 4096 × 4096 = 16M parameters

LoRA adds two small matrices:
A ∈ R^(d × r)   — e.g., 4096 × 16
B ∈ R^(r × d)   — e.g., 16 × 4096

New output = W·x + (B·A)·x × (alpha/r)
```

With rank `r=16`, instead of training 16M parameters, we train only **2 × 4096 × 16 = 131K parameters** — 120x fewer!

### Visual Explanation
```
┌─────────────────────────────────────┐
│         Phi-3 Mini (FROZEN)         │
│  3.8B parameters — NOT modified     │
│                                     │
│  ┌──────────┐    ┌──────────┐       │
│  │  q_proj  │    │  v_proj  │  ...  │
│  └────┬─────┘    └────┬─────┘       │
│       │               │             │
│  ┌────┴─────┐    ┌────┴─────┐       │
│  │  LoRA A  │    │  LoRA A  │       │  ← TRAINABLE
│  │  LoRA B  │    │  LoRA B  │       │  ← TRAINABLE
│  └──────────┘    └──────────┘       │
└─────────────────────────────────────┘
         ↓
   Only ~13M parameters trained
   (0.34% of total model)
```

---

## 2. Base Model — Phi-3 Mini

| Property | Value |
|----------|-------|
| Model | microsoft/Phi-3-mini-4k-instruct |
| Parameters | 3.8 billion |
| Context length | 4,096 tokens |
| Language | Multilingual (French supported) |
| License | MIT (free to use) |
| Precision | FP16 (half precision) |

**Why Phi-3 Mini?**
- Small enough to run on a single GPU (T4 in Colab)
- Strong instruction-following capability
- Good French language understanding
- No authentication token required (unlike Llama)

---

## 3. Training Data

### Dataset Size
**50 diverse examples** covering a wide range of architectural projects.

### Coverage
| Category | Examples |
|----------|----------|
| Budget range | 120k€ → 1.3M€ |
| Surface range | 30m² → 320m² |
| Styles | Moderne, Contemporain, Rustique, Écologique, Industriel, Scandinave, Balnéaire, Chalet, Haussmannien, Bioclimatique, Container, Minimaliste |
| Project types | Studio, T2, T3, T4, T5, Villa, Penthouse, Maison de campagne, Loft |

### Example Training Pair

**Input:**
```
Petite maison pour couple, environ 80m2. 2 chambres, cuisine 
fonctionnelle, petit jardin. Budget 250 000 euros. Style simple.
```

**Output:**
```json
{
  "surface_souhaitee": "70-90 m2",
  "budget": "220000-280000",
  "style": "Fonctionnel",
  "pieces_souhaitees": [
    {"nom": "Salon/Sejour", "surface": "25-30 m2"},
    {"nom": "Cuisine", "surface": "10-12 m2"},
    {"nom": "Chambre principale", "surface": "14-16 m2"},
    {"nom": "Chambre 2", "surface": "10-12 m2"},
    {"nom": "Salle de bain", "surface": "6-8 m2"},
    {"nom": "Jardin", "surface": "50 m2"}
  ]
}
```

### Data Split
- **80% training** (40 examples)
- **20% validation** (10 examples)

---

## 4. Prompt Format

The model is trained using the **Llama-3 instruction format**:

```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Tu es un expert en architecture specialise dans l'analyse de briefs 
clients. Tu dois extraire et structurer les informations en JSON avec 
EXACTEMENT ces cles:
{
  "surface_souhaitee": "XX-XX m2",
  "budget": "XXXXXX-XXXXXX",
  "style": "...",
  "pieces_souhaitees": [
    {"nom": "...", "surface": "XX-XX m2", "details": "..."}
  ]
}
Ne genere rien d'autre que le JSON.

<|eot_id|><|start_header_id|>user<|end_header_id|>

Brief: [CLIENT DESCRIPTION]

<|eot_id|><|start_header_id|>assistant<|end_header_id|>

[JSON OUTPUT]<|eot_id|>
```

The system prompt explicitly shows the **exact JSON keys** the model must use. This is critical — without it, the model generates inconsistent key names.

---

## 5. LoRA Configuration

```python
lora_config = LoraConfig(
    r=16,                    # Rank — bottleneck dimension
    lora_alpha=32,           # Scaling factor (alpha/r = 2)
    target_modules=[         # Which layers to adapt
        "q_proj",            # Query projection
        "v_proj",            # Value projection
        "k_proj",            # Key projection
        "o_proj"             # Output projection
    ],
    lora_dropout=0.05,       # Regularization
    bias="none",             # Don't adapt bias terms
    task_type=TaskType.CAUSAL_LM
)
```

### Why These Layers?
The attention projections (q, k, v, o) are the most important for learning new patterns. By adapting all 4, the model can fully reconfigure its attention mechanism for the architectural domain.

### Trainable Parameters
```
Total parameters:     3,821,079,552  (3.8B)
Trainable parameters:    13,107,200  (13M)
Trainable percentage:         0.34%
```

---

## 6. Training Configuration

```python
TrainingArguments(
    num_train_epochs=15,              # 15 passes over the data
    per_device_train_batch_size=1,    # 1 example per GPU step
    gradient_accumulation_steps=2,    # Effective batch = 2
    learning_rate=2e-4,               # AdamW optimizer
    warmup_steps=20,                  # Gradual LR warmup
    evaluation_strategy="epoch",      # Evaluate after each epoch
    save_strategy="epoch",            # Save best checkpoint
    load_best_model_at_end=True,      # Auto-load best checkpoint
    fp16=False,                       # FP32 for LoRA gradients
    optim="adamw_torch",              # No bitsandbytes needed
)
```

### Critical Technical Fix
LoRA parameters must be cast to FP32 even when the base model is in FP16:
```python
# Cast LoRA trainable params to fp32 so gradients work correctly
for name, param in model.named_parameters():
    if param.requires_grad:
        param.data = param.data.float()  # fp32 for trainable params
```

Without this, training crashes with `"Attempting to unscale FP16 gradients"`.

---

## 7. Training Results

| Epoch | Train Loss | Val Loss |
|-------|-----------|---------|
| 1 | 0.6783 | 0.4737 |
| 2 | 0.2565 | 0.2266 |
| 3 | 0.1852 | 0.2050 |
| 4 | 0.1789 | **0.2021** ← Best |
| 6 | 0.1404 | 0.2017 |
| 9 | 0.0671 | 0.2456 |
| 15 | 0.0267 | 0.3049 |

**Best model:** Epoch 6, Val Loss = 0.2017

The model converges quickly (loss drops from 0.67 → 0.14 in 6 epochs) then starts overfitting (train loss keeps dropping but val loss increases). The `load_best_model_at_end=True` setting automatically saves the best checkpoint.

---

## 8. Inference Results

Testing on **new briefs not seen during training**:

### Test 1 — Small House
**Input:** `"Maison moderne 120m2 pour famille de 4, 3 chambres, budget 400k euros"`

**Output:**
```json
{
  "surface_souhaitee": "115-128 m2",
  "budget": "370000-430000",
  "style": "Moderne contemporain",
  "pieces_souhaitees": [
    {"nom": "Salon/Sejour", "surface": "36-40 m2"},
    {"nom": "Cuisine", "surface": "16-18 m2"},
    {"nom": "Chambre principale", "surface": "19-21 m2"},
    {"nom": "Chambre 2", "surface": "14-16 m2"},
    {"nom": "Chambre 3", "surface": "12-14 m2"},
    {"nom": "Salle de bain", "surface": "9-11 m2"}
  ]
}
```
✅ Correct surface, budget, style, and rooms extracted

### Test 2 — Luxury Villa
**Input:** `"Grande villa 250m2, 6 chambres, piscine, tennis, budget 1 500 000 euros"`

**Output:**
```json
{
  "surface_souhaitee": "230-270 m2",
  "budget": "1400000-1800000",
  "style": "Luxe/Grandeur",
  "pieces_souhaitees": [
    {"nom": "Salon/Sejour", "surface": "90-110 m2"},
    {"nom": "Chambre principale", "surface": "35-40 m2"},
    {"nom": "Piscine", "surface": "50 m2"},
    ...
  ]
}
```
✅ Correctly identifies luxury style and scales rooms appropriately

---

## 9. Model Files

After training, the LoRA adapters are saved (only ~14 MB):

```
phi3-brief-lora/
  adapter_model.safetensors   ← trained LoRA weights (12 MB)
  adapter_config.json         ← LoRA configuration
  tokenizer.json              ← tokenizer vocabulary
  tokenizer.model             ← tokenizer model
  tokenizer_config.json       ← tokenizer settings
  special_tokens_map.json     ← special tokens
  added_tokens.json           ← additional tokens
```

The base model (Phi-3 Mini, ~7GB) is downloaded separately from HuggingFace and combined with these adapters at inference time.

---

## 10. Integration in ArchiGuide Dashboard

The LoRA model is integrated in the **"Mon Brief"** page for clients:

```
Client types description
        ↓
POST /api/analyze-brief-lora
        ↓
Load Phi-3 Mini + LoRA adapters
        ↓
Generate JSON response
        ↓
Display structured brief:
  - Surface souhaitée
  - Budget
  - Style architectural
  - Pièces souhaitées
```

- **Endpoint:** `POST /api/analyze-brief-lora`
- **Model files:** `backend/models/phi3-brief-lora/`
- **Wrapper:** `backend/models/brief_analyzer_lora.py`
- **Route:** `backend/routes/analyze_brief_lora.py`
- **Frontend:** `app/client/brief/page.tsx`

---

## 11. Comparison: Fine-Tuning vs Alternatives

| Approach | Accuracy | Speed | Cost | Our Choice |
|----------|----------|-------|------|------------|
| Regex parsing | Low | Instant | Free | Fallback |
| GPT-4 API | Very High | Fast | Expensive | No |
| Full fine-tuning | High | Slow | Very expensive | No |
| **LoRA fine-tuning** | **High** | **Medium** | **Free (Colab)** | **✅ Yes** |
| Gemini API | Very High | Fast | Free tier | Alternative |

LoRA gives us a **custom model trained on architectural French** that understands domain-specific vocabulary (suite parentale, dressing, véranda, etc.) without the cost of a commercial API.
