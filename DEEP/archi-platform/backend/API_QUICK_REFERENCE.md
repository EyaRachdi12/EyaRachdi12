# LoRA Brief Analyzer - API Quick Reference

## 🚀 Quick Start

```bash
# 1. Start backend
cd DEEP/archi-platform/backend
python main.py

# 2. Check health
curl http://localhost:8000/api/analyze-brief-lora/health

# 3. Analyze a brief
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d '{"description": "Maison moderne 120m², 3 chambres, budget 400k€"}'
```

---

## 📡 Endpoints

### 1. Health Check
```
GET /api/analyze-brief-lora/health
```

**Response:**
```json
{
  "status": "ready" | "not_loaded" | "unavailable",
  "message": "...",
  "base_model": "microsoft/Phi-3-mini-4k-instruct",
  "device": "cuda" | "cpu",
  "model_loaded": true | false
}
```

---

### 2. Preload Model
```
POST /api/analyze-brief-lora/preload
```

Loads the model into memory (takes 1-2 minutes). Useful for warming up.

**Response:**
```json
{
  "message": "Model loaded successfully",
  "status": "ready",
  "load_time_ms": 120000
}
```

---

### 3. Analyze Brief
```
POST /api/analyze-brief-lora
```

**Request:**
```json
{
  "description": "Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€",
  "temperature": 0.7,
  "max_tokens": 1024
}
```

**Response (Success):**
```json
{
  "surface_souhaitee": "120-140 m²",
  "budget": "350000-450000",
  "style": "Contemporain",
  "pieces_souhaitees": [
    {
      "nom": "Salon / Séjour",
      "surface": "30-35 m²",
      "details": "Lumineux"
    },
    {
      "nom": "Cuisine",
      "surface": "12-15 m²"
    },
    {
      "nom": "Chambre 1",
      "surface": "14-16 m²"
    }
  ],
  "processing_time_ms": 1234
}
```

**Response (Error):**
```json
{
  "error": "Analysis failed: ...",
  "raw_response": "...",
  "processing_time_ms": 123
}
```

---

## 🧪 Test Examples

### Small House
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Petite maison 80m² pour couple, 2 chambres, budget 250k€, style moderne"
  }'
```

### Family House
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Maison familiale 150m², 4 chambres, jardin, garage, budget 500k€, style contemporain"
  }'
```

### Luxury Villa
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Villa luxe 200m², 5 chambres, piscine, style contemporain, budget 800k€"
  }'
```

### Complex Brief
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Grand appartement 180m² pour famille nombreuse, 5 pièces incluant salon spacieux, cuisine ouverte, 3 chambres, bureau, 2 salles de bain, terrasse, budget 600k€, style moderne avec touches traditionnelles"
  }'
```

---

## 🔧 Parameters

### `temperature` (optional, default: 0.7)
Controls randomness in generation:
- `0.0` - Deterministic (always same output)
- `0.3-0.5` - More consistent
- `0.7` - Balanced (recommended)
- `0.9-1.0` - More creative/varied

### `max_tokens` (optional, default: 1024)
Maximum tokens to generate:
- `512` - Short responses
- `1024` - Standard (recommended)
- `2048` - Long responses

---

## 📊 Response Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `surface_souhaitee` | string | Desired surface area | "120-140 m²" |
| `budget` | string | Budget range | "350000-450000" |
| `style` | string | Architectural style | "Contemporain" |
| `pieces_souhaitees` | array | List of rooms | See below |
| `processing_time_ms` | number | Processing time | 1234 |
| `error` | string | Error message (if failed) | "..." |
| `raw_response` | string | Raw model output (if error) | "..." |

### Room Object
```json
{
  "nom": "Salon / Séjour",
  "surface": "30-35 m²",
  "details": "Lumineux, ouvert sur cuisine"
}
```

---

## ⚡ Performance

| Operation | Time | Notes |
|-----------|------|-------|
| First request | 1-2 min | Model loading |
| Subsequent requests | 1-5 sec | GPU recommended |
| Preload | 1-2 min | One-time warmup |

---

## 🐛 Common Errors

### 503 - Model Not Found
```json
{
  "error": "Model not found. Please train the model first or download the adapters."
}
```
**Solution:** Download model files from Colab (see LORA_INTEGRATION_GUIDE.md)

### 500 - Analysis Failed
```json
{
  "error": "Analysis failed: CUDA out of memory"
}
```
**Solution:** Close other GPU apps or use CPU mode

---

## 🌐 Frontend Integration

### JavaScript/TypeScript
```typescript
async function analyzeBrief(description: string) {
  const response = await fetch('http://localhost:8000/api/analyze-brief-lora', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description })
  });
  
  return await response.json();
}

// Usage
const result = await analyzeBrief("Maison 120m², 3 chambres, budget 400k€");
console.log(result.surface_souhaitee); // "120-140 m²"
```

### Python
```python
import requests

def analyze_brief(description: str):
    response = requests.post(
        'http://localhost:8000/api/analyze-brief-lora',
        json={'description': description}
    )
    return response.json()

# Usage
result = analyze_brief("Maison 120m², 3 chambres, budget 400k€")
print(result['surface_souhaitee'])  # "120-140 m²"
```

---

## 📝 Notes

- Model uses Phi-3 Mini (3.8B parameters)
- Trained on French architectural briefs
- Supports metric units (m², €)
- Returns structured JSON data
- Lazy loading (model loads on first use)
- Singleton pattern (reuses model across requests)

---

## 🔗 Related Endpoints

- `POST /api/parse-description` - Regex-based parser (fallback)
- `POST /api/briefs` - Save brief to database
- `GET /api/briefs` - List all briefs

---

**Full documentation:** See `LORA_INTEGRATION_GUIDE.md`
