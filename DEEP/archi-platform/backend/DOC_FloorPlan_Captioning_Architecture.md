# Floor Plan Captioning Model — Architecture & Training Guide

## Overview

This document explains the deep learning model used to automatically generate text descriptions from floor plan images. The model takes a floor plan image as input and outputs a structured caption like:

> *"apartment floorplan containing 2 bedrooms, 1 kitchen, 1 bathroom, 1 living room"*

---

## 1. The Problem

Given a floor plan image (PNG/JPG), the model must:
1. **Understand the visual structure** — detect rooms, walls, spatial layout
2. **Generate natural language** — produce a structured text description

This is an **Image Captioning** task, combining Computer Vision and Natural Language Processing.

---

## 2. Dataset — CubicASA5K

- **Source:** [Zenodo](https://zenodo.org/record/2613548) — open academic dataset
- **Size:** 5,000 annotated floor plan images (5.09 GB)
- **Format:** PNG images + SVG annotations (room labels, positions)
- **Split:** 90% training (4,500 images) / 10% validation (500 images)

### Caption Generation
Each floor plan SVG is parsed to extract room types, then a structured caption is generated:

```python
def make_semantic_caption(rooms):
    # Example output:
    # "apartment floorplan containing 2 bedrooms, 1 kitchen, 1 bathroom"
    caption = 'apartment floorplan containing ' + ', '.join(parts)
    return caption
```

Room types detected: bedroom, bathroom, kitchen, living room, balcony, closet, storage, toilet, terrace, garage, office, dining room.

---

## 3. Model Architecture — Dual Encoder + Transformer Decoder

The architecture combines **two encoders** and **one decoder**:

```
Floor Plan Image (384×384×3)
         │
    ┌────┴────┐
    │         │
ResNet-101   EfficientNetV2-S
(Spatial)    (Semantic)
    │         │
2048-dim    1280-dim
    │         │
Linear(2048→512)  Linear(1280→512)
    │         │
    └────┬────┘
         │
  Cross-Attention Fusion
  (Spatial attends to Semantic)
         │
    (B, N, 512)
         │
  Transformer Decoder
  (6 layers, 8 heads)
         │
  Linear(512 → vocab_size)
         │
  "apartment floorplan containing
   2 bedrooms, 1 kitchen..."
```

### 3.1 Spatial Encoder — ResNet-101

**Purpose:** Captures the geometric structure of the floor plan (walls, room boundaries, spatial layout).

| Property | Value |
|----------|-------|
| Architecture | ResNet-101 (pretrained on ImageNet) |
| Output dimension | 2048 channels |
| Frozen layers | layers 0, 1, 2 (early features) |
| Fine-tuned layers | layer3, layer4 (high-level spatial features) |
| Projection | Linear(2048 → 512) |

```python
class SpatialEncoder(nn.Module):
    def __init__(self):
        self.backbone = timm.create_model('resnet101', pretrained=True)
        self.proj = nn.Linear(2048, EMBED_DIM)  # 2048 → 512
```

### 3.2 Semantic Encoder — EfficientNetV2-S

**Purpose:** Captures semantic content (room types, textures, colors, furniture patterns).

| Property | Value |
|----------|-------|
| Architecture | EfficientNetV2-S (pretrained on ImageNet) |
| Output dimension | 1280 channels |
| Frozen layers | blocks 0-3 (early features) |
| Fine-tuned layers | blocks 4, 5, 6 (semantic features) |
| Projection | Linear(1280 → 512) |

```python
class SemanticEncoder(nn.Module):
    def __init__(self):
        self.backbone = timm.create_model('tf_efficientnetv2_s', pretrained=True)
        self.proj = nn.Linear(1280, EMBED_DIM)  # 1280 → 512
```

### 3.3 Cross-Attention Fusion

**Purpose:** Intelligently merges spatial and semantic features. The spatial features (ResNet) attend to semantic features (EfficientNet) to enrich themselves.

```
Spatial features  →  Query
Semantic features →  Key, Value
         ↓
   MultiheadAttention (8 heads)
         ↓
   LayerNorm + Residual
         ↓
   Feed-Forward Network (GELU)
         ↓
   LayerNorm + Residual
         ↓
   Fused features (B, N, 512)
```

```python
class CrossAttentionFusion(nn.Module):
    def __init__(self):
        self.cross_attn = nn.MultiheadAttention(embed_dim=512, num_heads=8)
        self.norm1 = nn.LayerNorm(512)
        self.norm2 = nn.LayerNorm(512)
        self.ffn = nn.Sequential(
            nn.Linear(512, 2048), nn.GELU(),
            nn.Dropout(0.1), nn.Linear(2048, 512)
        )
```

### 3.4 Transformer Decoder

**Purpose:** Generates the caption word by word, attending to the visual features at each step.

| Property | Value |
|----------|-------|
| Layers | 6 TransformerDecoderLayer |
| Attention heads | 8 |
| Embedding dimension | 512 |
| Tokenizer | BERT (bert-base-uncased, vocab=30,522) |
| Max caption length | 64 tokens |
| Dropout | 0.1 |

**Key mechanisms:**
- **Self-attention with causal mask:** Each token can only attend to previous tokens (autoregressive generation)
- **Padding mask:** Ignores padding tokens during training
- **Cross-attention:** Each generated token attends to all visual features
- **Dropout after embeddings:** Reduces overfitting

```python
class CaptionTransformer(nn.Module):
    def forward(self, memory, tokens):
        x = self.embedding(tokens)    # token → 512-dim vector
        x = self.positional(x)        # add position information
        x = self.dropout(x)           # regularization
        # causal mask: token i cannot see token j > i
        out = self.decoder(tgt=x, memory=memory,
                          tgt_mask=mask,
                          tgt_key_padding_mask=padding_mask)
        return self.fc(out)           # 512 → vocab_size
```

---

## 4. Training Configuration

| Hyperparameter | Value | Reason |
|----------------|-------|--------|
| Image size | 384×384 | High resolution for detail |
| Batch size | 8 | GPU memory constraint |
| Epochs | 30 (max) | With early stopping |
| Learning rate | 2e-4 | AdamW optimizer |
| Weight decay | 1e-4 | L2 regularization |
| Gradient clipping | 1.0 | Prevent exploding gradients |
| Dropout | 0.1 | Prevent overfitting |
| Label smoothing | 0.1 | Reduce overconfidence |
| Scheduler | CosineAnnealingLR | Smooth LR decay |
| Early stopping | patience=5 | Stop when val loss plateaus |

### Data Augmentation (Training only)
```python
train_transform = T.Compose([
    T.Resize((384, 384)),
    T.RandomRotation(3),           # small rotations
    T.RandomHorizontalFlip(0.5),   # mirror floor plans
    T.ColorJitter(0.1, 0.1, 0.1), # slight color variation
    T.ToTensor(),
    T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])
```

### Loss Function
```python
criterion = nn.CrossEntropyLoss(
    ignore_index=tokenizer.pad_token_id,  # ignore padding
    label_smoothing=0.1                    # soft targets
)
```

### Training Strategy — Teacher Forcing
During training, the model receives the correct previous token at each step (not its own prediction). This speeds up convergence significantly.

```python
# Input:  [CLS, "apartment", "floorplan", "containing"]
# Target: ["apartment", "floorplan", "containing", "2"]
outputs = model(images, input_ids[:, :-1])  # input without last token
targets = input_ids[:, 1:]                  # target without first token
```

---

## 5. Inference — Beam Search

During inference, the model generates captions using **Beam Search** (beam size = 3):

```
Step 1: Start with [CLS] token
Step 2: Generate top-3 next tokens
Step 3: For each candidate, generate top-3 next tokens → 9 candidates
Step 4: Keep top-3 by score (length-normalized)
Step 5: Repeat until [SEP] token or max length
Step 6: Return best sequence
```

**Length normalization** prevents the model from preferring short captions:
```python
score = total_log_prob / len(sequence)  # normalize by length
```

---

## 6. Training Results

| Epoch | Train Loss | Val Loss |
|-------|-----------|---------|
| 1 | 0.3918 | 0.1698 |
| 4 | 0.1540 | 0.1474 |
| 6 | 0.1448 | 0.1402 |
| 9 | 0.1239 | **0.1328** ← Best |
| 14 | 0.0919 | 0.1405 |
| — | ⛔ Early stopping | — |

**Best model:** Epoch 9, Val Loss = 0.1328

### Sample Predictions
```
Ground Truth: apartment floorplan containing 1 bedroom, 1 closet,
              1 kitchen, 1 living room, 1 room, 1 toilet

Prediction:   apartment floorplan containing 1 bedroom, 1 closet,
              1 kitchen, 1 living room, 1 room, 1 toilet  ✅ Perfect
```

---

## 7. Why Dual Encoder?

| Single Encoder | Dual Encoder |
|----------------|--------------|
| Only EfficientNetV2 | ResNet-101 + EfficientNetV2 |
| Misses spatial layout | Captures both layout AND semantics |
| Val loss: 0.1326 | Val loss: 0.1328 (similar, more robust) |
| Simpler | More powerful for complex plans |

ResNet-101 excels at detecting **geometric structures** (straight lines, rectangles = rooms). EfficientNetV2 excels at **semantic recognition** (what type of room based on content). Together they give a more complete understanding.

---

## 8. Integration in ArchiGuide Dashboard

The trained model is integrated at:
- **Endpoint:** `POST /api/analyze-plan`
- **Model file:** `backend/models/weights/best_floorplan_model.pth`
- **Wrapper:** `backend/models/floorplan_captioner_v2.py`
- **Frontend:** `app/architect/upload/page.tsx`

When an architect uploads a floor plan, the model automatically generates a structured description in ~5 seconds.
