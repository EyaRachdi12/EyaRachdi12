# 🚀 Open Notebook in Google Colab

## Quick Start

### Option 1: Upload to Google Drive (Recommended)

1. **Upload the notebook:**
   - Go to [Google Drive](https://drive.google.com)
   - Upload `train_brief_analyzer_lora.ipynb`

2. **Open with Colab:**
   - Right-click the file → "Open with" → "Google Colaboratory"
   - If you don't see Colab, click "Connect more apps" and search for "Colaboratory"

3. **Enable GPU:**
   - In Colab: Runtime → Change runtime type → Hardware accelerator → **T4 GPU** → Save

4. **Run the notebook:**
   - Click "Runtime" → "Run all" or run cells one by one

---

### Option 2: Direct Upload to Colab

1. **Go to Colab:**
   - Visit [colab.research.google.com](https://colab.research.google.com)

2. **Upload notebook:**
   - Click "File" → "Upload notebook"
   - Select `train_brief_analyzer_lora.ipynb`

3. **Enable GPU:**
   - Runtime → Change runtime type → Hardware accelerator → **T4 GPU** → Save

4. **Run the notebook:**
   - Click "Runtime" → "Run all"

---

### Option 3: GitHub (If you push to GitHub)

1. **Push notebook to GitHub**

2. **Open in Colab:**
   - Go to [colab.research.google.com](https://colab.research.google.com)
   - Click "GitHub" tab
   - Enter your repository URL
   - Select the notebook

---

## ⚠️ Important Notes

### Before Running:

1. **Free GPU Limits:**
   - Free Colab T4 GPU: ~15GB VRAM
   - Training time: ~25 minutes
   - You may be disconnected after 12 hours of inactivity

2. **Runtime Restart:**
   - After installing packages (Step 1), you may need to restart runtime
   - Runtime → Restart runtime (if you see bitsandbytes errors)

3. **Save Your Work:**
   - Colab auto-saves to Drive if opened from Drive
   - Download the trained model (Step 12) before closing

### During Training:

- **Don't close the browser tab** - training will stop
- **Watch the loss decrease** - should go from ~2.5 to ~0.3
- **GPU memory usage** - should stay under 14GB with 4-bit quantization

### After Training:

- **Download the model** (Step 12) - it will be a ~50MB zip file
- **Extract and copy** to your backend: `backend/models/mistral-brief-lora/`

---

## 🐛 Troubleshooting

### "CUDA out of memory"
- Restart runtime: Runtime → Restart runtime
- Make sure you're using T4 GPU (not CPU)
- The notebook now uses 4-bit quantization (~4GB instead of 14GB)

### "bitsandbytes not found"
- Restart runtime after Step 1
- Runtime → Restart runtime → Run from Step 2

### "Model not found"
- Make sure you have internet connection
- Mistral-7B will be downloaded automatically (~14GB)

### Training is slow
- Check GPU is enabled: Runtime → Change runtime type
- Free T4 GPU should complete in ~25 minutes

---

## 📊 Expected Results

### Training Progress:
```
Step 0:   Loss ~2.5
Step 50:  Loss ~1.8 (warmup done)
Step 200: Loss ~0.8
Step 500: Loss ~0.3 ✓
```

### Model Output Example:
```json
{
  "surface_souhaitee": "120-140 m²",
  "budget": "350000-450000",
  "style": "Contemporain",
  "pieces_souhaitees": [
    {"nom": "Salon", "surface": "30-35 m²", "details": "Lumineux"},
    {"nom": "Cuisine", "surface": "15-20 m²", "details": "Ouverte"}
  ]
}
```

---

## 🎯 Next Steps After Training

1. **Download model** (Step 12 in notebook)
2. **Extract zip file**
3. **Copy to backend:**
   ```bash
   cp -r mistral-brief-lora/ DEEP/archi-platform/backend/models/
   ```
4. **Integrate with API** (see notebook Step 13)

---

**Happy Training! 🎉**
