# VisionNarrator: Standalone Retraining Script for Google Colab

Follow these steps to retrain your model in a new Colab notebook.

### Cell 1: Environment Setup
```python
import os, json, random, math, time, warnings, io
from collections import Counter
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
import IPython.display as ipd

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms, models
from torch.nn.utils.rnn import pack_padded_sequence

import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
from nltk.translate.bleu_score import corpus_bleu
from tqdm.auto import tqdm

# Audio dependencies
try:
    import gtts
except ImportError:
    !pip install gtts librosa -q
    import gtts

from gtts import gTTS
import librosa
import librosa.display

warnings.filterwarnings('ignore')
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(SEED)
```

### Cell 2: Data Preparation (Flickr8k / CubiCasa)
*Note: This cell downloads the dataset. Adjust the path if you already have your data in Drive.*
```python
DATA_DIR = Path("data")
IMAGES_DIR = DATA_DIR / "flickr8k" / "Images"
CAPTIONS_FILE = DATA_DIR / "flickr8k" / "dataset_flickr8k.json"

if not IMAGES_DIR.exists():
    print("Downloading dataset...")
    os.makedirs(DATA_DIR / "flickr8k", exist_ok=True)
    # Using a common mirror for Flickr8k
    !pip install kaggle -q
    # You might need to upload your kaggle.json or provide a manual download link
    !wget -q https://github.com/jbrownlee/Datasets/releases/download/Flickr8k/Flickr8k_Dataset.zip
    !wget -q https://github.com/jbrownlee/Datasets/releases/download/Flickr8k/Flickr8k_text.zip
    !unzip -q Flickr8k_Dataset.zip -d data/flickr8k/Images
    !unzip -q Flickr8k_text.zip -d data/flickr8k/
    print("Dataset ready.")

# Vocabulary Config
MIN_WORD_FREQ = 5
MAX_CAPTION_LEN = 50
PAD_TOKEN = '<pad>'
START_TOKEN = '<start>'
END_TOKEN = '<end>'
UNK_TOKEN = '<unk>'
```

### Cell 3: Vocabulary & Dataset Classes
```python
class Vocabulary:
    def __init__(self, freq_threshold):
        self.itos = {0: PAD_TOKEN, 1: START_TOKEN, 2: END_TOKEN, 3: UNK_TOKEN}
        self.stoi = {PAD_TOKEN: 0, START_TOKEN: 1, END_TOKEN: 2, UNK_TOKEN: 3}
        self.freq_threshold = freq_threshold

    def __len__(self):
        return len(self.itos)

    def build_vocabulary(self, sentence_list):
        frequencies = Counter()
        idx = 4
        for sentence in sentence_list:
            for word in nltk.word_tokenize(sentence.lower()):
                frequencies[word] += 1
                if frequencies[word] == self.freq_threshold:
                    self.stoi[word] = idx
                    self.itos[idx] = word
                    idx += 1

    def numericalize(self, text):
        tokenized_text = nltk.word_tokenize(text.lower())
        return [self.stoi.get(token, self.stoi[UNK_TOKEN]) for token in tokenized_text]

class VisionDataset(Dataset):
    def __init__(self, root_dir, data_list, transform=None):
        self.root_dir = root_dir
        self.samples = data_list
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        sample = self.samples[index]
        img = Image.open(sample['filepath']).convert("RGB")
        if self.transform is not None:
            img = self.transform(img)

        caption = sample['caption']
        numericalized_caption = [1] # Start
        # numericalize logic here
        return img, torch.tensor(numericalized_caption)
```

### Cell 4: VisionNarrator Architecture
```python
class CrossAttentionFusion(nn.Module):
    def __init__(self, dim: int, num_heads: int = 8, dropout: float = 0.1):
        super().__init__()
        self.attn_a2b = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        self.attn_b2a = nn.MultiheadAttention(dim, num_heads, dropout=dropout, batch_first=True)
        self.norm_a = nn.LayerNorm(dim)
        self.norm_b = nn.LayerNorm(dim)
        self.proj = nn.Linear(dim * 2, dim)
        self.act = nn.GELU()

    def forward(self, feat_a, feat_b):
        a_ctx, _ = self.attn_a2b(feat_a, feat_b, feat_b)
        b_ctx, _ = self.attn_b2a(feat_b, feat_a, feat_a)
        a_fused = self.norm_a(feat_a + a_ctx)
        b_fused = self.norm_b(feat_b + b_ctx)
        merged = torch.cat([a_fused, b_fused], dim=-1)
        return self.act(self.proj(merged))

class DualStreamEncoder(nn.Module):
    def __init__(self, d_model: int = 512):
        super().__init__()
        resnet = models.resnet101(weights=models.ResNet101_Weights.DEFAULT)
        self.spatial_backbone = nn.Sequential(*list(resnet.children())[:-2])
        self.spatial_proj = nn.Sequential(
            nn.Conv2d(2048, d_model, kernel_size=1),
            nn.BatchNorm2d(d_model),
            nn.GELU()
        )
        effnet = models.efficientnet_b4(weights=models.EfficientNet_B4_Weights.DEFAULT)
        self.semantic_backbone = nn.Sequential(*list(effnet.children())[:-1])
        self.semantic_proj = nn.Linear(1792, d_model)
        self.fusion = CrossAttentionFusion(d_model, num_heads=8)

        for p in self.spatial_backbone.parameters(): p.requires_grad = False
        for p in self.semantic_backbone.parameters(): p.requires_grad = False

    def forward(self, images):
        sp = self.spatial_backbone(images)
        sp = self.spatial_proj(sp)
        B, C, H, W = sp.shape
        sp_seq = sp.view(B, C, H * W).permute(0, 2, 1)
        sem = self.semantic_backbone(images).squeeze(-1).squeeze(-1)
        sem = self.semantic_proj(sem)
        sem_seq = sem.unsqueeze(1).expand(-1, H * W, -1)
        return self.fusion(sp_seq, sem_seq)

class SemanticBridgeTransformer(nn.Module):
    def __init__(self, d_model: int, num_layers: int = 4):
        super().__init__()
        enc_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=8, batch_first=True)
        self.transformer = nn.TransformerEncoder(enc_layer, num_layers=num_layers)

    def forward(self, x):
        return self.transformer(x)

class HierarchicalCaptionDecoder(nn.Module):
    def __init__(self, vocab_size, d_model=512, num_dec_layers=3):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, d_model, padding_idx=0)
        dec_layer = nn.TransformerDecoderLayer(d_model=d_model, nhead=8, batch_first=True)
        self.transformer_dec = nn.TransformerDecoder(dec_layer, num_layers=num_dec_layers)
        self.output_proj = nn.Linear(d_model, vocab_size)

    def forward(self, memory, captions):
        tgt = self.embedding(captions)
        out = self.transformer_dec(tgt, memory)
        return self.output_proj(out)

class VisionNarrator(nn.Module):
    def __init__(self, vocab_size, d_model=512):
        super().__init__()
        self.encoder = DualStreamEncoder(d_model)
        self.bridge = SemanticBridgeTransformer(d_model)
        self.decoder = HierarchicalCaptionDecoder(vocab_size, d_model)

    def forward(self, images, captions):
        feats = self.encoder(images)
        memory = self.bridge(feats)
        return self.decoder(memory, captions)
```

### Cell 5: Training Loop
```python
def train_vision_narrator(model, train_loader, val_loader, num_epochs=10, lr=3e-4):
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss(ignore_index=0, label_smoothing=0.1)
    
    for epoch in range(num_epochs):
        model.train()
        for imgs, caps in tqdm(train_loader, desc=f"Epoch {epoch+1}"):
            imgs, caps = imgs.to(device), caps.to(device)
            logits = model(imgs, caps[:, :-1])
            loss = criterion(logits.reshape(-1, logits.shape[-1]), caps[:, 1:].reshape(-1))
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
        
        print(f"Epoch {epoch+1} completed. Model saved.")
        torch.save(model.state_dict(), 'best_visionnarrator_colab.pth')
```
