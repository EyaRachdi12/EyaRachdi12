"""
Training Script — Floor Plan Caption Model
==========================================
ResNet-50 (encoder) + LSTM + Soft Attention (decoder)
Trained on CubiCasa5K captions

Optimized for 8GB RAM / CPU training:
  - ResNet-50 instead of ResNet-101 (lighter)
  - batch_size = 4
  - gradient checkpointing
  - mixed precision disabled (CPU)
  - encoder frozen (only LSTM + Attention trained)

Usage:
    python train.py
    python train.py --epochs 10 --batch_size 2 --max_samples 1000
"""

import os
import sys
import json
import time
import argparse
import random
from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from PIL import Image
from tqdm import tqdm

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from models.vocabulary import Vocabulary, ARCHITECTURAL_VOCAB
from data.svg_parser   import build_dataset, CubiCasaCaptionGenerator
from data.download_cubicasa import download_cubicasa

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
CUBICASA_DIR = DATA_DIR / "cubicasa5k"
DATASET_JSON = DATA_DIR / "captions_dataset.json"
WEIGHTS_DIR  = BASE_DIR / "models" / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# ── Hyperparameters ───────────────────────────────────────────────────────────
ENCODER_DIM   = 2048   # ResNet-50 last layer
ATTENTION_DIM = 256
EMBED_DIM     = 256
DECODER_DIM   = 512
DROPOUT       = 0.4
MAX_LEN       = 60
PAD_IDX       = 0


# ── Image transform ───────────────────────────────────────────────────────────
TRAIN_TRANSFORM = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.RandomHorizontalFlip(p=0.3),
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])

VAL_TRANSFORM = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406],
                         [0.229, 0.224, 0.225]),
])


# ══════════════════════════════════════════════════════════════════════════════
# Dataset
# ══════════════════════════════════════════════════════════════════════════════
class FloorPlanDataset(Dataset):
    def __init__(
        self,
        samples:   list,
        vocab:     Vocabulary,
        transform  = None,
        max_len:   int = MAX_LEN,
    ):
        self.samples   = samples
        self.vocab     = vocab
        self.transform = transform or VAL_TRANSFORM
        self.max_len   = max_len

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        sample = self.samples[idx]

        # Load image
        try:
            img = Image.open(sample["image_path"]).convert("RGB")
        except Exception:
            img = Image.new("RGB", (256, 256), color=(240, 238, 234))

        img_tensor = self.transform(img)

        # Encode caption
        caption = sample["caption"]
        tokens  = self.vocab.encode(caption)

        # Pad / truncate to max_len
        tokens = tokens[:self.max_len]
        length = len(tokens)
        tokens += [PAD_IDX] * (self.max_len - length)

        return (
            img_tensor,
            torch.tensor(tokens,  dtype=torch.long),
            torch.tensor(length,  dtype=torch.long),
        )


def collate_fn(batch):
    imgs, caps, lengths = zip(*batch)
    imgs    = torch.stack(imgs)
    caps    = torch.stack(caps)
    lengths = torch.stack(lengths)
    # Sort by length descending (for pack_padded_sequence)
    lengths, sort_idx = lengths.sort(descending=True)
    imgs = imgs[sort_idx]
    caps = caps[sort_idx]
    return imgs, caps, lengths


# ══════════════════════════════════════════════════════════════════════════════
# Model (ResNet-50 + LSTM + Attention) — lighter than ResNet-101
# ══════════════════════════════════════════════════════════════════════════════
class Encoder50(nn.Module):
    """ResNet-50 encoder — lighter than ResNet-101, fits in 8GB RAM."""

    def __init__(self, encoded_size: int = 14):
        super().__init__()
        resnet = models.resnet50(weights=models.ResNet50_Weights.DEFAULT)
        # Remove avgpool + fc
        self.resnet = nn.Sequential(*list(resnet.children())[:-2])
        self.pool   = nn.AdaptiveAvgPool2d((encoded_size, encoded_size))
        # Freeze all layers
        for p in self.resnet.parameters():
            p.requires_grad = False

    def forward(self, x):
        out = self.resnet(x)          # (B, 2048, H/32, W/32)
        out = self.pool(out)          # (B, 2048, 14, 14)
        out = out.permute(0, 2, 3, 1) # (B, 14, 14, 2048)
        B   = out.size(0)
        return out.view(B, -1, 2048)  # (B, 196, 2048)


class Attention(nn.Module):
    def __init__(self, enc_dim, dec_dim, att_dim):
        super().__init__()
        self.enc_att = nn.Linear(enc_dim, att_dim)
        self.dec_att = nn.Linear(dec_dim, att_dim)
        self.full    = nn.Linear(att_dim, 1)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, enc_out, h):
        a1    = self.enc_att(enc_out)
        a2    = self.dec_att(h).unsqueeze(1)
        score = self.full(torch.relu(a1 + a2)).squeeze(2)
        alpha = self.softmax(score)
        ctx   = (enc_out * alpha.unsqueeze(2)).sum(1)
        return ctx, alpha


class DecoderLSTM(nn.Module):
    def __init__(self, att_dim, emb_dim, dec_dim, vocab_size,
                 enc_dim=2048, dropout=0.4):
        super().__init__()
        self.vocab_size = vocab_size
        self.attention  = Attention(enc_dim, dec_dim, att_dim)
        self.embed      = nn.Embedding(vocab_size, emb_dim, padding_idx=0)
        self.dropout    = nn.Dropout(dropout)
        self.init_h     = nn.Linear(enc_dim, dec_dim)
        self.init_c     = nn.Linear(enc_dim, dec_dim)
        self.lstm_cell  = nn.LSTMCell(emb_dim + enc_dim, dec_dim)
        self.f_beta     = nn.Linear(dec_dim, enc_dim)
        self.sigmoid    = nn.Sigmoid()
        self.fc         = nn.Linear(dec_dim, vocab_size)

    def init_hidden(self, enc_out):
        mean = enc_out.mean(1)
        return self.init_h(mean), self.init_c(mean)

    def forward(self, enc_out, captions, lengths):
        B          = enc_out.size(0)
        vocab_size = self.vocab_size
        emb        = self.dropout(self.embed(captions))
        h, c       = self.init_hidden(enc_out)

        decode_lens = (lengths - 1).tolist()
        max_t       = max(int(l) for l in decode_lens)

        preds  = torch.zeros(B, max_t, vocab_size).to(enc_out.device)
        alphas = torch.zeros(B, max_t, enc_out.size(1)).to(enc_out.device)

        for t in range(max_t):
            bt = sum(l > t for l in decode_lens)
            ctx, alpha = self.attention(enc_out[:bt], h[:bt])
            gate = self.sigmoid(self.f_beta(h[:bt]))
            ctx  = gate * ctx

            h_new, c_new = self.lstm_cell(
                torch.cat([emb[:bt, t, :], ctx], dim=1),
                (h[:bt], c[:bt]),
            )
            out = self.fc(self.dropout(h_new))
            preds[:bt, t, :]  = out
            alphas[:bt, t, :] = alpha

            h = h.clone(); c = c.clone()
            h[:bt] = h_new
            c[:bt] = c_new

        return preds, alphas


# ══════════════════════════════════════════════════════════════════════════════
# Training loop
# ══════════════════════════════════════════════════════════════════════════════
def train_epoch(encoder, decoder, loader, optimizer, criterion, device):
    encoder.eval()   # encoder frozen
    decoder.train()
    total_loss = 0.0
    n_batches  = 0

    for imgs, caps, lengths in tqdm(loader, desc="  Train", leave=False):
        imgs    = imgs.to(device)
        caps    = caps.to(device)
        lengths = lengths.to(device)

        with torch.no_grad():
            enc_out = encoder(imgs)

        preds, alphas = decoder(enc_out, caps, lengths)

        # Targets: caps shifted by 1 (remove <SOS>)
        targets = caps[:, 1:]

        # Flatten for cross-entropy
        decode_lens = (lengths - 1).tolist()
        max_t       = max(int(l) for l in decode_lens)
        preds_flat  = preds[:, :max_t, :].reshape(-1, decoder.vocab_size)
        targets_flat = targets[:, :max_t].reshape(-1)

        loss = criterion(preds_flat, targets_flat)

        # Doubly stochastic attention regularization
        loss += 1.0 * ((1.0 - alphas.sum(dim=1)) ** 2).mean()

        optimizer.zero_grad()
        loss.backward()
        nn.utils.clip_grad_norm_(decoder.parameters(), max_norm=5.0)
        optimizer.step()

        total_loss += loss.item()
        n_batches  += 1

    return total_loss / max(n_batches, 1)


@torch.no_grad()
def val_epoch(encoder, decoder, loader, criterion, device):
    encoder.eval()
    decoder.eval()
    total_loss = 0.0
    n_batches  = 0

    for imgs, caps, lengths in tqdm(loader, desc="  Val  ", leave=False):
        imgs    = imgs.to(device)
        caps    = caps.to(device)
        lengths = lengths.to(device)

        enc_out       = encoder(imgs)
        preds, alphas = decoder(enc_out, caps, lengths)

        targets     = caps[:, 1:]
        decode_lens = (lengths - 1).tolist()
        max_t       = max(int(l) for l in decode_lens)
        preds_flat  = preds[:, :max_t, :].reshape(-1, decoder.vocab_size)
        targets_flat = targets[:, :max_t].reshape(-1)

        loss = criterion(preds_flat, targets_flat)
        total_loss += loss.item()
        n_batches  += 1

    return total_loss / max(n_batches, 1)


# ══════════════════════════════════════════════════════════════════════════════
# Inference helper
# ══════════════════════════════════════════════════════════════════════════════
@torch.no_grad()
def generate_caption(encoder, decoder, image: Image.Image,
                     vocab: Vocabulary, device: str,
                     max_len: int = 60, beam_size: int = 3) -> str:
    """Generate caption for a single image using beam search."""
    encoder.eval()
    decoder.eval()

    img_t   = VAL_TRANSFORM(image.convert("RGB")).unsqueeze(0).to(device)
    enc_out = encoder(img_t)                    # (1, 196, 2048)
    num_px  = enc_out.size(1)

    enc_out = enc_out.expand(beam_size, num_px, 2048)

    k_words  = torch.full((beam_size, 1), vocab.SOS_IDX, dtype=torch.long).to(device)
    seqs     = k_words
    scores   = torch.zeros(beam_size, 1).to(device)

    complete_seqs, complete_scores = [], []

    h, c = decoder.init_hidden(enc_out)

    for step in range(max_len):
        emb = decoder.embed(k_words.squeeze(1))
        ctx, alpha = decoder.attention(enc_out, h)
        gate = decoder.sigmoid(decoder.f_beta(h))
        ctx  = gate * ctx

        h, c = decoder.lstm_cell(
            torch.cat([emb, ctx], dim=1), (h, c)
        )
        logits = decoder.fc(h)
        log_p  = torch.log_softmax(logits, dim=1)
        log_p  = scores.expand_as(log_p) + log_p

        if step == 0:
            top_scores, top_words = log_p[0].topk(beam_size)
        else:
            top_scores, top_words = log_p.view(-1).topk(beam_size)

        prev_idx = top_words // len(vocab)
        next_idx = top_words  % len(vocab)

        seqs   = torch.cat([seqs[prev_idx], next_idx.unsqueeze(1)], dim=1)
        scores = top_scores.unsqueeze(1)

        done       = [i for i, w in enumerate(next_idx) if w == vocab.EOS_IDX]
        incomplete = [i for i, w in enumerate(next_idx) if w != vocab.EOS_IDX]

        if done:
            complete_seqs.extend(seqs[done].tolist())
            complete_scores.extend(scores[done].squeeze(1).tolist())
            beam_size -= len(done)

        if beam_size == 0:
            break

        seqs    = seqs[incomplete]
        scores  = scores[incomplete]
        h       = h[prev_idx[incomplete]]
        c       = c[prev_idx[incomplete]]
        enc_out = enc_out[prev_idx[incomplete]]
        k_words = next_idx[incomplete].unsqueeze(1)

    if complete_seqs:
        best = complete_seqs[complete_scores.index(max(complete_scores))]
    else:
        best = seqs[0].tolist()

    return vocab.decode(best)


# ══════════════════════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(description="Train floor plan caption model")
    parser.add_argument("--epochs",      type=int,   default=15)
    parser.add_argument("--batch_size",  type=int,   default=4)
    parser.add_argument("--lr",          type=float, default=4e-4)
    parser.add_argument("--max_samples", type=int,   default=5000)
    parser.add_argument("--val_split",   type=float, default=0.1)
    parser.add_argument("--workers",     type=int,   default=0)
    args = parser.parse_args()

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\n{'='*60}")
    print(f"  ArchiGuide — Floor Plan Caption Model Training")
    print(f"  Device     : {device.upper()}")
    print(f"  Epochs     : {args.epochs}")
    print(f"  Batch size : {args.batch_size}")
    print(f"  Max samples: {args.max_samples}")
    print(f"{'='*60}\n")

    # ── Step 1: Download CubiCasa5K ───────────────────────────────────────────
    print("📥 Step 1: Checking CubiCasa5K dataset...")
    if not CUBICASA_DIR.exists():
        print("  Dataset not found — downloading...")
        success = download_cubicasa()
        if not success:
            print("\n⚠️  Could not download CubiCasa5K automatically.")
            print("  Generating synthetic dataset instead...")
            _generate_synthetic_dataset(args.max_samples)
    else:
        print(f"  ✓ Found at {CUBICASA_DIR}")

    # ── Step 2: Build caption dataset ────────────────────────────────────────
    print("\n📝 Step 2: Building caption dataset...")
    if not DATASET_JSON.exists():
        if CUBICASA_DIR.exists():
            n = build_dataset(CUBICASA_DIR, DATASET_JSON, args.max_samples)
        else:
            n = _generate_synthetic_dataset(args.max_samples)
        print(f"  ✓ {n} samples generated")
    else:
        print(f"  ✓ Dataset already exists: {DATASET_JSON}")

    with open(DATASET_JSON, encoding="utf-8") as f:
        all_samples = json.load(f)

    all_samples = all_samples[:args.max_samples]
    print(f"  Using {len(all_samples)} samples")

    if len(all_samples) < 10:
        print("❌ Not enough samples. Aborting.")
        return

    # ── Step 3: Build vocabulary ──────────────────────────────────────────────
    print("\n📚 Step 3: Building vocabulary...")
    vocab = Vocabulary()
    print(f"  Vocabulary size: {len(vocab)}")

    # ── Step 4: Split dataset ─────────────────────────────────────────────────
    random.shuffle(all_samples)
    n_val    = max(1, int(len(all_samples) * args.val_split))
    val_data = all_samples[:n_val]
    trn_data = all_samples[n_val:]
    print(f"\n📊 Step 4: Dataset split")
    print(f"  Train : {len(trn_data)}")
    print(f"  Val   : {len(val_data)}")

    # ── Step 5: DataLoaders ───────────────────────────────────────────────────
    trn_ds = FloorPlanDataset(trn_data, vocab, TRAIN_TRANSFORM)
    val_ds = FloorPlanDataset(val_data, vocab, VAL_TRANSFORM)

    trn_loader = DataLoader(
        trn_ds, batch_size=args.batch_size,
        shuffle=True, collate_fn=collate_fn,
        num_workers=args.workers, pin_memory=False,
    )
    val_loader = DataLoader(
        val_ds, batch_size=args.batch_size,
        shuffle=False, collate_fn=collate_fn,
        num_workers=args.workers, pin_memory=False,
    )

    # ── Step 6: Build model ───────────────────────────────────────────────────
    print("\n🏗️  Step 5: Building model (ResNet-50 + LSTM + Attention)...")
    encoder = Encoder50(encoded_size=14).to(device)
    decoder = DecoderLSTM(
        att_dim    = ATTENTION_DIM,
        emb_dim    = EMBED_DIM,
        dec_dim    = DECODER_DIM,
        vocab_size = len(vocab),
        enc_dim    = ENCODER_DIM,
        dropout    = DROPOUT,
    ).to(device)

    n_params = sum(p.numel() for p in decoder.parameters() if p.requires_grad)
    print(f"  Trainable parameters (decoder): {n_params:,}")

    # ── Step 7: Optimizer & Loss ──────────────────────────────────────────────
    optimizer = optim.AdamW(decoder.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=args.epochs, eta_min=1e-5
    )
    criterion = nn.CrossEntropyLoss(ignore_index=PAD_IDX)

    # ── Step 8: Training loop ─────────────────────────────────────────────────
    print(f"\n🚀 Step 6: Training for {args.epochs} epochs...\n")
    best_val_loss = float("inf")
    history       = []

    for epoch in range(1, args.epochs + 1):
        t0 = time.time()

        trn_loss = train_epoch(encoder, decoder, trn_loader, optimizer, criterion, device)
        val_loss = val_epoch(encoder, decoder, val_loader, criterion, device)
        scheduler.step()

        elapsed = time.time() - t0
        lr_now  = optimizer.param_groups[0]["lr"]

        print(
            f"  Epoch {epoch:02d}/{args.epochs} | "
            f"Train: {trn_loss:.4f} | "
            f"Val: {val_loss:.4f} | "
            f"LR: {lr_now:.2e} | "
            f"{elapsed:.0f}s"
        )

        history.append({
            "epoch": epoch, "train_loss": trn_loss,
            "val_loss": val_loss, "lr": lr_now,
        })

        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "epoch":      epoch,
                "encoder":    encoder.state_dict(),
                "decoder":    decoder.state_dict(),
                "optimizer":  optimizer.state_dict(),
                "val_loss":   val_loss,
                "vocab_size": len(vocab),
            }, WEIGHTS_DIR / "best_model.pth")
            print(f"    💾 Saved best model (val_loss={val_loss:.4f})")

        # Sample caption every 5 epochs
        if epoch % 5 == 0:
            _sample_caption(encoder, decoder, vocab, device)

    # ── Step 9: Save final model ──────────────────────────────────────────────
    torch.save({
        "epoch":      args.epochs,
        "encoder":    encoder.state_dict(),
        "decoder":    decoder.state_dict(),
        "val_loss":   best_val_loss,
        "vocab_size": len(vocab),
        "history":    history,
    }, WEIGHTS_DIR / "final_model.pth")

    print(f"\n{'='*60}")
    print(f"  ✅ Training complete!")
    print(f"  Best val loss : {best_val_loss:.4f}")
    print(f"  Weights saved : {WEIGHTS_DIR}/best_model.pth")
    print(f"{'='*60}\n")

    # Final sample
    print("📝 Final caption sample:")
    _sample_caption(encoder, decoder, vocab, device)


def _sample_caption(encoder, decoder, vocab, device):
    """Generate a sample caption from a synthetic image."""
    img = Image.new("RGB", (256, 256), color=(240, 238, 234))
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 236, 236], outline=(40, 40, 40), width=3)
    draw.line([128, 20, 128, 236], fill=(40, 40, 40), width=2)
    draw.line([20, 128, 128, 128], fill=(40, 40, 40), width=2)

    caption = generate_caption(encoder, decoder, img, vocab, device)
    print(f"  → \"{caption}\"")


def _generate_synthetic_dataset(n_samples: int) -> int:
    """Generate a synthetic dataset when CubiCasa5K is not available."""
    from models.rule_based_captioner import RuleBasedCaptioner
    from PIL import ImageDraw
    import json

    print(f"  Generating {n_samples} synthetic samples...")
    captioner = RuleBasedCaptioner()
    dataset   = []

    for i in range(n_samples):
        # Create synthetic floor plan image
        img  = Image.new("RGB", (256, 256), color=(240, 238, 234))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 236, 236], outline=(40, 40, 40), width=3)

        # Random internal walls
        n_walls = random.randint(1, 4)
        for _ in range(n_walls):
            x1 = random.randint(20, 236)
            y1 = random.randint(20, 236)
            x2 = random.randint(20, 236)
            y2 = random.randint(20, 236)
            draw.line([x1, y1, x2, y2], fill=(40, 40, 40), width=2)

        # Save temp image
        img_path = DATA_DIR / f"synthetic_{i:04d}.png"
        img.save(img_path)

        result = captioner.generate(img, seed=i)
        dataset.append({
            "image_path": str(img_path),
            "caption":    result["caption"],
            "rooms":      result["rooms"],
            "total_area": result["total_area"],
            "n_rooms":    len(result["rooms"]),
            "style":      result["style"],
        })

        if (i + 1) % 200 == 0:
            print(f"    [{i+1}/{n_samples}] generated")

    DATASET_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(DATASET_JSON, "w", encoding="utf-8") as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)

    print(f"  ✓ Synthetic dataset saved: {DATASET_JSON}")
    return len(dataset)


if __name__ == "__main__":
    main()
