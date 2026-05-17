"""
Floor Plan VQA Model (Visual Question Answering)
Architecture: ResNet-101 (image) + GRU (question) + Fusion MLP → answer

Supports questions like:
  - "Où est la salle de bain ?"
  - "Quelle est la surface du salon ?"
  - "Combien de fenêtres y a-t-il ?"
  - "Y a-t-il un dressing ?"
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
from PIL import Image
from typing import List, Dict, Tuple
import re

from .vocabulary import vocab


# ── Constants ─────────────────────────────────────────────────────────────────
IMAGE_FEAT_DIM  = 2048
QUESTION_HIDDEN = 512
FUSION_DIM      = 1024
EMBED_DIM       = 256
DROPOUT         = 0.3

# ── Image preprocessing (same as caption model) ───────────────────────────────
VQA_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225],
    ),
])

# ── Answer classes ────────────────────────────────────────────────────────────
# The model predicts one of these answer categories
ANSWER_CLASSES = [
    # Locations
    "nord", "sud", "est", "ouest", "nord-est", "nord-ouest", "sud-est", "sud-ouest",
    "centre", "gauche", "droite", "haut", "bas",
    "adjacent au salon", "adjacent à la cuisine", "adjacent à la chambre",
    "côté nord", "côté sud", "côté est", "côté ouest",

    # Surfaces (m²)
    "moins de 5 m²", "5-8 m²", "8-12 m²", "12-16 m²", "16-20 m²",
    "20-25 m²", "25-30 m²", "30-35 m²", "35-40 m²", "plus de 40 m²",

    # Counts
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10+",

    # Yes/No
    "oui", "non",

    # Room presence
    "présent", "absent", "non disponible",

    # Style
    "contemporain", "classique", "industriel", "minimaliste", "haussmannien",

    # General
    "information non disponible",
]

NUM_ANSWERS = len(ANSWER_CLASSES)
answer2idx  = {a: i for i, a in enumerate(ANSWER_CLASSES)}
idx2answer  = {i: a for i, a in enumerate(ANSWER_CLASSES)}


# ── Question tokenizer ────────────────────────────────────────────────────────
class QuestionTokenizer:
    """Simple word-level tokenizer for French architectural questions."""

    QUESTION_VOCAB = [
        "<PAD>", "<UNK>",
        # Question words
        "où", "quel", "quelle", "quels", "quelles", "combien", "comment",
        "est-ce", "y", "a-t-il", "il", "a", "est", "sont", "se", "trouve",
        "situé", "situés", "sitée",
        # Common words in floor plan questions
        "la", "le", "les", "de", "du", "des", "un", "une", "l", "d",
        "surface", "superficie", "taille", "dimension",
        "fenêtre", "fenêtres", "porte", "portes", "ouverture",
        "salon", "séjour", "cuisine", "chambre", "salle", "bain", "douche",
        "toilettes", "wc", "bureau", "dressing", "placard", "couloir",
        "entrée", "terrasse", "balcon", "garage", "cave",
        "pièce", "pièces", "espace", "zone",
        "?", "m²",
    ]

    def __init__(self):
        self.w2i = {w: i for i, w in enumerate(self.QUESTION_VOCAB)}
        self.vocab_size = len(self.QUESTION_VOCAB)

    def tokenize(self, question: str, max_len: int = 20) -> torch.Tensor:
        tokens = re.findall(r"\w+|[?]", question.lower())
        ids = [self.w2i.get(t, 1) for t in tokens]  # 1 = <UNK>
        # Pad or truncate
        ids = ids[:max_len]
        ids += [0] * (max_len - len(ids))
        return torch.tensor(ids, dtype=torch.long)


question_tokenizer = QuestionTokenizer()


# ── Image Encoder (shared with caption model) ─────────────────────────────────
class VQAImageEncoder(nn.Module):
    """ResNet-101 → global average pooled feature vector (2048-dim)."""

    def __init__(self):
        super().__init__()
        resnet = models.resnet101(weights=models.ResNet101_Weights.DEFAULT)
        # Keep everything except the final fc
        self.features = nn.Sequential(*list(resnet.children())[:-1])
        for p in self.features.parameters():
            p.requires_grad = False  # frozen

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Returns (B, 2048)."""
        out = self.features(x)          # (B, 2048, 1, 1)
        return out.view(out.size(0), -1)  # (B, 2048)


# ── Question Encoder: GRU ─────────────────────────────────────────────────────
class QuestionEncoder(nn.Module):
    """Embeds + encodes a tokenized question with a GRU."""

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.gru = nn.GRU(
            embed_dim, hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.3,
            bidirectional=True,
        )
        # Bidirectional → 2 * hidden_dim, project back to hidden_dim
        self.proj = nn.Linear(2 * hidden_dim, hidden_dim)

    def forward(self, tokens: torch.Tensor) -> torch.Tensor:
        """
        Args:
            tokens: (B, seq_len)
        Returns:
            (B, hidden_dim)
        """
        emb = self.embedding(tokens)          # (B, seq, embed)
        _, hidden = self.gru(emb)             # hidden: (4, B, hidden)
        # Concat last forward + backward hidden
        hidden = torch.cat([hidden[-2], hidden[-1]], dim=1)  # (B, 2*hidden)
        return self.proj(hidden)              # (B, hidden_dim)


# ── Fusion + Classifier ───────────────────────────────────────────────────────
class VQAFusion(nn.Module):
    """
    Fuses image and question features with element-wise product + MLP.
    Uses MCB-style fusion (simplified).
    """

    def __init__(
        self,
        img_dim: int,
        q_dim: int,
        fusion_dim: int,
        num_answers: int,
        dropout: float,
    ):
        super().__init__()
        # Project both to same dim
        self.img_proj = nn.Linear(img_dim, fusion_dim)
        self.q_proj   = nn.Linear(q_dim,   fusion_dim)

        self.classifier = nn.Sequential(
            nn.LayerNorm(fusion_dim),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim, fusion_dim // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim // 2, num_answers),
        )

    def forward(
        self,
        img_feat: torch.Tensor,   # (B, img_dim)
        q_feat:   torch.Tensor,   # (B, q_dim)
    ) -> torch.Tensor:
        img_p = F.normalize(self.img_proj(img_feat), dim=-1)
        q_p   = F.normalize(self.q_proj(q_feat),   dim=-1)
        fused = img_p * q_p                          # element-wise product
        return self.classifier(fused)                # (B, num_answers)


# ── Full VQA Model ────────────────────────────────────────────────────────────
class FloorPlanVQAModel(nn.Module):
    """
    End-to-end VQA model for floor plan images.
    Input:  image (PIL) + question (str)
    Output: answer (str) + confidence (float)
    """

    def __init__(self):
        super().__init__()
        self.img_encoder = VQAImageEncoder()
        self.q_encoder   = QuestionEncoder(
            vocab_size  = question_tokenizer.vocab_size,
            embed_dim   = EMBED_DIM,
            hidden_dim  = QUESTION_HIDDEN,
        )
        self.fusion = VQAFusion(
            img_dim     = IMAGE_FEAT_DIM,
            q_dim       = QUESTION_HIDDEN,
            fusion_dim  = FUSION_DIM,
            num_answers = NUM_ANSWERS,
            dropout     = DROPOUT,
        )

    def forward(
        self,
        images:   torch.Tensor,   # (B, 3, 224, 224)
        questions: torch.Tensor,  # (B, seq_len)
    ) -> torch.Tensor:
        img_feat = self.img_encoder(images)
        q_feat   = self.q_encoder(questions)
        logits   = self.fusion(img_feat, q_feat)
        return logits

    @torch.no_grad()
    def answer(
        self,
        image:    Image.Image,
        question: str,
        device:   str = "cpu",
        top_k:    int = 3,
    ) -> Dict:
        """
        Answer a question about a floor plan image.

        Returns:
            {
              "answer":      str,
              "confidence":  float (0-1),
              "top_answers": [(answer, confidence), ...]
            }
        """
        self.eval()
        self.to(device)

        # Preprocess image
        img_t = VQA_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)

        # Tokenize question
        q_t = question_tokenizer.tokenize(question).unsqueeze(0).to(device)

        # Forward
        logits = self.forward(img_t, q_t)           # (1, num_answers)
        probs  = F.softmax(logits, dim=-1)[0]        # (num_answers,)

        top_probs, top_idxs = probs.topk(top_k)

        best_answer = idx2answer[top_idxs[0].item()]
        confidence  = top_probs[0].item()

        top_answers = [
            (idx2answer[i.item()], round(p.item(), 3))
            for i, p in zip(top_idxs, top_probs)
        ]

        return {
            "answer":      best_answer,
            "confidence":  round(confidence, 3),
            "top_answers": top_answers,
        }
