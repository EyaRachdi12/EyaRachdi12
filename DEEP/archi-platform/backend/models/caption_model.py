"""
Floor Plan Caption Model
Architecture: ResNet-101 (CNN encoder) + LSTM + Soft Attention (decoder)

Based on:
- "Show, Attend and Tell" (Xu et al., 2015)
- Adapted for architectural floor plan images
- Trained on CubiCasa5K-style captions
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.models as models
from torchvision import transforms
from PIL import Image
from typing import Tuple, List
import numpy as np
from pathlib import Path

from .vocabulary import vocab, Vocabulary

# Path to trained model weights
WEIGHTS_DIR = Path(__file__).parent / "weights"
BEST_MODEL_PATH = WEIGHTS_DIR / "best_model.pth"


# ── Constants ─────────────────────────────────────────────────────────────────
ENCODER_DIM    = 2048   # ResNet-101 last conv output channels
ATTENTION_DIM  = 512    # attention layer size
EMBED_DIM      = 256    # word embedding size
DECODER_DIM    = 512    # LSTM hidden size
DROPOUT        = 0.5
MAX_CAPTION_LEN = 80


# ── Image preprocessing ───────────────────────────────────────────────────────
IMAGE_TRANSFORM = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],   # ImageNet stats
        std=[0.229, 0.224, 0.225],
    ),
])


# ── Encoder: ResNet-101 ───────────────────────────────────────────────────────
class Encoder(nn.Module):
    """
    ResNet-101 encoder.
    Removes the final avgpool + fc layers to keep spatial feature maps.
    Output: (batch, 14*14, 2048) — 196 spatial locations, each 2048-dim.
    """

    def __init__(self, encoded_image_size: int = 14):
        super().__init__()
        self.enc_image_size = encoded_image_size

        resnet = models.resnet101(weights=models.ResNet101_Weights.DEFAULT)

        # Remove avgpool and fc — keep up to layer4
        modules = list(resnet.children())[:-2]
        self.resnet = nn.Sequential(*modules)

        # Adaptive pool to fixed spatial size
        self.adaptive_pool = nn.AdaptiveAvgPool2d(
            (encoded_image_size, encoded_image_size)
        )

        self.fine_tune(fine_tune=False)  # freeze by default

    def forward(self, images: torch.Tensor) -> torch.Tensor:
        """
        Args:
            images: (batch, 3, H, W)
        Returns:
            features: (batch, num_pixels, encoder_dim)
                      num_pixels = encoded_image_size²
        """
        out = self.resnet(images)                    # (B, 2048, H/32, W/32)
        out = self.adaptive_pool(out)                # (B, 2048, 14, 14)
        out = out.permute(0, 2, 3, 1)               # (B, 14, 14, 2048)
        batch = out.size(0)
        out = out.view(batch, -1, ENCODER_DIM)       # (B, 196, 2048)
        return out

    def fine_tune(self, fine_tune: bool = True):
        """Allow or prevent gradients on ResNet layers 2-4."""
        for p in self.resnet.parameters():
            p.requires_grad = False
        if fine_tune:
            for child in list(self.resnet.children())[5:]:
                for p in child.parameters():
                    p.requires_grad = True


# ── Soft Attention ────────────────────────────────────────────────────────────
class SoftAttention(nn.Module):
    """
    Soft (deterministic) attention mechanism.
    Computes a weighted sum over encoder spatial features,
    conditioned on the current LSTM hidden state.
    """

    def __init__(self, encoder_dim: int, decoder_dim: int, attention_dim: int):
        super().__init__()
        self.encoder_att = nn.Linear(encoder_dim, attention_dim)
        self.decoder_att = nn.Linear(decoder_dim, attention_dim)
        self.full_att    = nn.Linear(attention_dim, 1)
        self.relu        = nn.ReLU()
        self.softmax     = nn.Softmax(dim=1)

    def forward(
        self,
        encoder_out: torch.Tensor,   # (B, num_pixels, encoder_dim)
        decoder_hidden: torch.Tensor # (B, decoder_dim)
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            context:  (B, encoder_dim)  — weighted encoder output
            alpha:    (B, num_pixels)   — attention weights
        """
        att1 = self.encoder_att(encoder_out)          # (B, num_pixels, att_dim)
        att2 = self.decoder_att(decoder_hidden)        # (B, att_dim)
        att  = self.full_att(
            self.relu(att1 + att2.unsqueeze(1))
        ).squeeze(2)                                   # (B, num_pixels)
        alpha   = self.softmax(att)                    # (B, num_pixels)
        context = (encoder_out * alpha.unsqueeze(2)).sum(dim=1)  # (B, enc_dim)
        return context, alpha


# ── Decoder: LSTM + Attention ─────────────────────────────────────────────────
class DecoderWithAttention(nn.Module):
    """
    LSTM decoder with soft attention.
    At each step:
      1. Compute attention over encoder features
      2. Concatenate context + word embedding
      3. LSTM step
      4. Project to vocabulary
    """

    def __init__(
        self,
        attention_dim: int,
        embed_dim: int,
        decoder_dim: int,
        vocab_size: int,
        encoder_dim: int = ENCODER_DIM,
        dropout: float = DROPOUT,
    ):
        super().__init__()
        self.vocab_size  = vocab_size
        self.decoder_dim = decoder_dim

        self.attention   = SoftAttention(encoder_dim, decoder_dim, attention_dim)
        self.embedding   = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.dropout     = nn.Dropout(dropout)

        # Initialize LSTM hidden/cell from mean encoder output
        self.init_h = nn.Linear(encoder_dim, decoder_dim)
        self.init_c = nn.Linear(encoder_dim, decoder_dim)

        # LSTM cell (manual step for attention integration)
        self.lstm_cell   = nn.LSTMCell(embed_dim + encoder_dim, decoder_dim)

        # Gating scalar (doubly stochastic attention)
        self.f_beta      = nn.Linear(decoder_dim, encoder_dim)
        self.sigmoid     = nn.Sigmoid()

        # Output projection
        self.fc          = nn.Linear(decoder_dim, vocab_size)

        self._init_weights()

    def _init_weights(self):
        nn.init.uniform_(self.embedding.weight, -0.1, 0.1)
        nn.init.uniform_(self.fc.weight, -0.1, 0.1)
        nn.init.constant_(self.fc.bias, 0)

    def init_hidden_state(
        self, encoder_out: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Initialize LSTM h, c from mean-pooled encoder output."""
        mean_enc = encoder_out.mean(dim=1)   # (B, encoder_dim)
        h = self.init_h(mean_enc)            # (B, decoder_dim)
        c = self.init_c(mean_enc)
        return h, c

    def forward(
        self,
        encoder_out: torch.Tensor,   # (B, num_pixels, encoder_dim)
        captions: torch.Tensor,      # (B, max_len)  — token indices
        caption_lengths: torch.Tensor  # (B,)
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Teacher-forcing forward pass (training).
        Returns:
            predictions: (B, max_len-1, vocab_size)
            alphas:      (B, max_len-1, num_pixels)
        """
        batch_size   = encoder_out.size(0)
        num_pixels   = encoder_out.size(1)
        vocab_size   = self.vocab_size

        embeddings   = self.dropout(self.embedding(captions))  # (B, max_len, embed)
        h, c         = self.init_hidden_state(encoder_out)

        decode_lengths = (caption_lengths - 1).tolist()
        max_t          = max(decode_lengths)

        predictions = torch.zeros(batch_size, max_t, vocab_size).to(encoder_out.device)
        alphas      = torch.zeros(batch_size, max_t, num_pixels).to(encoder_out.device)

        for t in range(max_t):
            batch_t = sum([l > t for l in decode_lengths])
            context, alpha = self.attention(
                encoder_out[:batch_t], h[:batch_t]
            )
            gate    = self.sigmoid(self.f_beta(h[:batch_t]))
            context = gate * context

            h_new, c_new = self.lstm_cell(
                torch.cat([embeddings[:batch_t, t, :], context], dim=1),
                (h[:batch_t], c[:batch_t]),
            )
            preds = self.fc(self.dropout(h_new))   # (batch_t, vocab_size)

            predictions[:batch_t, t, :] = preds
            alphas[:batch_t, t, :]      = alpha

            h = h.clone(); c = c.clone()
            h[:batch_t] = h_new
            c[:batch_t] = c_new

        return predictions, alphas


# ── Full Caption Model ────────────────────────────────────────────────────────
class FloorPlanCaptionModel(nn.Module):
    """
    End-to-end floor plan captioning model.
    Wraps Encoder + DecoderWithAttention.
    """

    def __init__(self, vocabulary: Vocabulary = None, load_weights: bool = True):
        super().__init__()
        self.vocabulary = vocabulary or vocab
        self.encoder    = Encoder(encoded_image_size=14)
        self.decoder    = DecoderWithAttention(
            attention_dim = ATTENTION_DIM,
            embed_dim     = EMBED_DIM,
            decoder_dim   = DECODER_DIM,
            vocab_size    = len(self.vocabulary),
            encoder_dim   = ENCODER_DIM,
            dropout       = DROPOUT,
        )
        
        # Load trained weights if available
        if load_weights and BEST_MODEL_PATH.exists():
            self._load_trained_weights()
    
    def _load_trained_weights(self):
        """Load trained model weights from best_model.pth"""
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            checkpoint = torch.load(BEST_MODEL_PATH, map_location=device)
            
            # Load encoder weights
            if "encoder" in checkpoint:
                self.encoder.load_state_dict(checkpoint["encoder"])
                print(f"✅ Loaded trained encoder weights from {BEST_MODEL_PATH}")
            
            # Load decoder weights
            if "decoder" in checkpoint:
                self.decoder.load_state_dict(checkpoint["decoder"])
                print(f"✅ Loaded trained decoder weights from {BEST_MODEL_PATH}")
            
            # Print training info if available
            if "epoch" in checkpoint:
                print(f"   Model trained for {checkpoint['epoch']} epochs")
            if "val_loss" in checkpoint:
                print(f"   Validation loss: {checkpoint['val_loss']:.4f}")
                
        except Exception as e:
            print(f"⚠️  Could not load trained weights: {e}")
            print(f"   Using randomly initialized weights instead")

    def forward(self, images, captions, lengths):
        features = self.encoder(images)
        return self.decoder(features, captions, lengths)

    @torch.no_grad()
    def generate_caption(
        self,
        image: Image.Image,
        max_len: int = MAX_CAPTION_LEN,
        beam_size: int = 3,
        device: str = "cpu",
    ) -> Tuple[str, np.ndarray]:
        """
        Generate a caption for a single floor plan image using beam search.

        Args:
            image:     PIL Image
            max_len:   maximum caption length
            beam_size: beam search width
            device:    'cpu' or 'cuda'

        Returns:
            caption:   generated text
            attention: (max_len, 14, 14) attention maps
        """
        self.eval()
        self.to(device)

        # Preprocess
        img_tensor = IMAGE_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)

        # Encode
        encoder_out = self.encoder(img_tensor)   # (1, 196, 2048)
        enc_dim     = encoder_out.size(-1)
        num_pixels  = encoder_out.size(1)

        # Expand for beam search
        encoder_out = encoder_out.expand(beam_size, num_pixels, enc_dim)

        # Initialize beams: (score, token_sequence)
        k_prev_words = torch.full(
            (beam_size, 1), self.vocabulary.SOS_IDX, dtype=torch.long
        ).to(device)

        seqs        = k_prev_words                          # (k, 1)
        top_k_scores = torch.zeros(beam_size, 1).to(device) # (k, 1)
        seqs_alpha  = torch.ones(beam_size, 1, num_pixels).to(device)

        complete_seqs       = []
        complete_seqs_alpha = []
        complete_seqs_scores = []

        h, c = self.decoder.init_hidden_state(encoder_out)

        step = 1
        while True:
            embeddings = self.decoder.embedding(
                k_prev_words.squeeze(1)
            )                                               # (k, embed_dim)
            context, alpha = self.decoder.attention(encoder_out, h)
            gate    = self.decoder.sigmoid(self.decoder.f_beta(h))
            context = gate * context

            h, c = self.decoder.lstm_cell(
                torch.cat([embeddings, context], dim=1), (h, c)
            )
            scores = self.decoder.fc(h)                    # (k, vocab_size)
            scores = F.log_softmax(scores, dim=1)
            scores = top_k_scores.expand_as(scores) + scores

            if step == 1:
                top_k_scores, top_k_words = scores[0].topk(beam_size, dim=0)
            else:
                top_k_scores, top_k_words = scores.view(-1).topk(beam_size, dim=0)

            prev_word_inds = top_k_words // len(self.vocabulary)
            next_word_inds = top_k_words  % len(self.vocabulary)

            seqs       = torch.cat([seqs[prev_word_inds], next_word_inds.unsqueeze(1)], dim=1)
            seqs_alpha = torch.cat(
                [seqs_alpha[prev_word_inds], alpha[prev_word_inds].unsqueeze(1)], dim=1
            )

            incomplete = [i for i, w in enumerate(next_word_inds)
                          if w != self.vocabulary.EOS_IDX]
            complete   = [i for i, w in enumerate(next_word_inds)
                          if w == self.vocabulary.EOS_IDX]

            if complete:
                complete_seqs.extend(seqs[complete].tolist())
                complete_seqs_alpha.extend(seqs_alpha[complete].tolist())
                complete_seqs_scores.extend(top_k_scores[complete].tolist())
                beam_size -= len(complete)

            if beam_size == 0 or step >= max_len:
                break

            seqs        = seqs[incomplete]
            seqs_alpha  = seqs_alpha[incomplete]
            h           = h[prev_word_inds[incomplete]]
            c           = c[prev_word_inds[incomplete]]
            encoder_out = encoder_out[prev_word_inds[incomplete]]
            top_k_scores = top_k_scores[incomplete].unsqueeze(1)
            k_prev_words = next_word_inds[incomplete].unsqueeze(1)
            step += 1

        # Pick best complete sequence
        if complete_seqs_scores:
            best_idx   = complete_seqs_scores.index(max(complete_seqs_scores))
            best_seq   = complete_seqs[best_idx]
            best_alpha = complete_seqs_alpha[best_idx]
        else:
            # Fallback: take best incomplete
            best_seq   = seqs[0].tolist()
            best_alpha = seqs_alpha[0].tolist()

        caption = self.vocabulary.decode(best_seq)

        # Reshape attention maps to (steps, 14, 14)
        enc_size = self.encoder.enc_image_size
        attn_maps = np.array(best_alpha)
        if attn_maps.ndim == 2:
            attn_maps = attn_maps.reshape(-1, enc_size, enc_size)

        return caption, attn_maps
