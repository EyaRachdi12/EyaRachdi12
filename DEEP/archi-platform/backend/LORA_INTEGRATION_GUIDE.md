# LoRA Brief Analyzer - Integration Guide

## 🎯 Overview

The LoRA Brief Analyzer is now integrated into the ArchiGuide backend! This guide will help you complete the setup and test the integration.

## 📁 What Was Created

### 1. **Model Wrapper** (`models/brief_analyzer_lora.py`)
- `BriefAnalyzerLoRA` class for model inference
- Lazy loading pattern (model loads on first use)
- Singleton pattern (reuses model across requests)
- JSON extraction from model output
- Error handling for missing files

### 2. **API Endpoints** (`routes/analyze_brief_lora.py`)
- `POST /api/analyze-brief-lora` - Analyze a brief
- `GET /api/analyze-brief-lora/health` - Check model status
- `POST /api/analyze-brief-lora/preload` - Warm up the model

### 3. **Backend Integration** (`main.py`)
- Router registered and ready to use
- CORS configured for frontend access

### 4. **Test Script** (`test_lora_integration.py`)
- Standalone test without starting full backend
- Checks model files, loading, and inference

---

## 🚀 Setup Instructions

### Step 1: Download Model from Colab

Your trained model is still in Google Colab. You need to download it:

#### In Colab (Cell 12):
```bash
# Create zip file
!cd /content && zip -r phi3-brief-lora.zip phi3-brief-lora/
```

#### Download the file:
1. In Colab, click the **Files** icon (📁) in the left sidebar
2. Find `phi3-brief-lora.zip` (should be ~40 MB)
3. Right-click → **Download**

### Step 2: Extract Model Files

Extract the downloaded zip to your backend:

```bash
# Navigate to backend models directory
cd DEEP/archi-platform/backend/models/

# Extract the zip (Windows)
# Use 7-Zip, WinRAR, or built-in Windows extraction
# Extract to: DEEP/archi-platform/backend/models/phi3-brief-lora/

# The directory structure should be:
# models/
#   phi3-brief-lora/
#     adapter_config.json
#     adapter_model.safetensors
#     special_tokens_map.json
#     tokenizer.json
#     tokenizer_config.json
#     (and other tokenizer files)
```

### Step 3: Verify Installation

Run the test script:

```bash
cd DEEP/archi-platform/backend
python test_lora_integration.py
```

**Expected output:**
```
🧪 Testing LoRA Brief Analyzer Integration
================================================================================
1. Checking model files...
================================================================================
LoRA path: models/phi3-brief-lora
Exists: True

✅ Model directory found!

Files in directory:
  - adapter_config.json (0.XX MB)
  - adapter_model.safetensors (38.XX MB)
  - tokenizer.json (X.XX MB)
  ...

================================================================================
2. Testing model loading...
================================================================================
Base model: microsoft/Phi-3-mini-4k-instruct
Device: cuda (or cpu)
Loaded: False

⏳ Loading model (this may take 1-2 minutes)...
✅ Model loaded successfully!

================================================================================
3. Testing inference...
================================================================================

📝 Test 1: Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€
--------------------------------------------------------------------------------
✅ Success!
{
  "surface": "120-140 m²",
  "budget": "350000-450000",
  ...
}

🎉 All tests passed! The integration is working.
```

---

## 🧪 Testing the API

### Start the Backend

```bash
cd DEEP/archi-platform/backend
python main.py
```

The server will start on `http://localhost:8000`

### Test Endpoints

#### 1. Health Check
```bash
curl http://localhost:8000/api/analyze-brief-lora/health
```

**Expected response:**
```json
{
  "status": "not_loaded",
  "message": "Model files found but not loaded yet. Will load on first request.",
  "base_model": "microsoft/Phi-3-mini-4k-instruct",
  "lora_path": "models/phi3-brief-lora",
  "device": "cuda",
  "model_loaded": false
}
```

#### 2. Preload Model (Optional)
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora/preload
```

This warms up the model (takes 1-2 minutes). Useful before handling real requests.

#### 3. Analyze a Brief
```bash
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d "{\"description\": \"Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€\"}"
```

**Expected response:**
```json
{
  "surface": "120-140 m²",
  "budget": "350000-450000",
  "style": "Contemporain",
  "pieces_souhaitees": [
    {
      "nom": "Salon / Séjour",
      "surface": "30-35 m²"
    },
    ...
  ],
  "processing_time_ms": 1234
}
```

#### 4. Test with Different Briefs
```bash
# Small house
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d "{\"description\": \"Petite maison 80m² pour couple, 2 chambres, budget 250k€, style moderne\"}"

# Luxury villa
curl -X POST http://localhost:8000/api/analyze-brief-lora \
  -H "Content-Type: application/json" \
  -d "{\"description\": \"Villa luxe 200m², 5 chambres, piscine, style contemporain, budget 800k€\"}"
```

---

## 🌐 Frontend Integration (Optional)

If you want to use this in your Next.js frontend:

### Example API Call
```typescript
// In your client brief form component
async function analyzeBrief(description: string) {
  const response = await fetch('http://localhost:8000/api/analyze-brief-lora', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      description: description,
      temperature: 0.7,
      max_tokens: 1024
    })
  });
  
  const result = await response.json();
  
  if (result.error) {
    console.error('Analysis failed:', result.error);
    return null;
  }
  
  return result;
}

// Usage in form submit
const handleSubmit = async (e) => {
  e.preventDefault();
  
  const briefText = "Maison moderne 120m², 3 chambres, budget 400k€";
  const analysis = await analyzeBrief(briefText);
  
  if (analysis) {
    console.log('Extracted data:', analysis);
    // Use the structured data to pre-fill form fields
    setSurface(analysis.surface_souhaitee);
    setBudget(analysis.budget);
    setStyle(analysis.style);
    // etc.
  }
};
```

---

## 📊 API Documentation

### POST `/api/analyze-brief-lora`

Analyze an architectural brief using the fine-tuned LoRA model.

**Request Body:**
```typescript
{
  description: string;      // The brief text to analyze
  temperature?: number;     // Sampling temperature (default: 0.7)
  max_tokens?: number;      // Max tokens to generate (default: 1024)
}
```

**Response:**
```typescript
{
  surface_souhaitee?: string;     // e.g., "120-140 m²"
  budget?: string;                // e.g., "350000-450000"
  style?: string;                 // e.g., "Contemporain"
  pieces_souhaitees?: Array<{     // List of rooms
    nom: string;                  // Room name
    surface?: string;             // Room size
    details?: string;             // Additional details
  }>;
  processing_time_ms?: number;    // Time taken
  error?: string;                 // Error message if failed
  raw_response?: string;          // Raw model output (if error)
}
```

**Status Codes:**
- `200` - Success
- `500` - Analysis failed (check error field)
- `503` - Model not found (need to download model files)

---

## ⚠️ Known Limitations

### 1. **Overfitting**
The current model was trained on only 3 examples, so it will:
- Work well for similar briefs
- May produce inconsistent results for very different briefs
- Sometimes use English units instead of metric

**Solution:** Retrain with more diverse data (see next section)

### 2. **Inconsistent JSON Format**
The model sometimes generates different JSON keys or structures.

**Solution:** Add post-processing to normalize the output

### 3. **Performance**
- First request takes 1-2 minutes (model loading)
- Subsequent requests take 1-5 seconds
- GPU recommended for faster inference

---

## 🔄 Improving the Model (Next Steps)

### Option 1: Generate More Training Data

Create `generate_training_data.py`:

```python
"""
Generate diverse training examples for LoRA fine-tuning
"""

import json
import random

# Templates for different project types
templates = [
    {
        "type": "small_house",
        "surface_range": (50, 100),
        "rooms": ["salon", "cuisine", "chambre", "salle de bain"],
        "budget_range": (150000, 350000),
        "styles": ["moderne", "contemporain", "minimaliste"]
    },
    {
        "type": "family_house",
        "surface_range": (100, 180),
        "rooms": ["salon", "cuisine", "chambre_1", "chambre_2", "chambre_3", "salle de bain", "bureau"],
        "budget_range": (300000, 600000),
        "styles": ["moderne", "contemporain", "traditionnel", "familial"]
    },
    {
        "type": "luxury_villa",
        "surface_range": (180, 350),
        "rooms": ["salon", "salle à manger", "cuisine", "chambre_1", "chambre_2", "chambre_3", "chambre_4", "bureau", "salle de jeux", "piscine"],
        "budget_range": (600000, 1500000),
        "styles": ["contemporain", "luxe", "villa", "moderne"]
    }
]

def generate_brief(template):
    """Generate a random brief from template"""
    surface = random.randint(*template["surface_range"])
    budget = random.randint(*template["budget_range"])
    style = random.choice(template["styles"])
    num_rooms = random.randint(2, len(template["rooms"]))
    
    brief = f"Maison {style} {surface}m², {num_rooms} pièces, budget {budget//1000}k€"
    
    return brief, {
        "surface": f"{surface-10}-{surface+10} m²",
        "budget": f"{budget-50000}-{budget+50000}",
        "style": style.capitalize(),
        "pieces_souhaitees": [
            {"nom": room.replace("_", " ").title()}
            for room in random.sample(template["rooms"], num_rooms)
        ]
    }

# Generate 50 examples
training_data = []
for _ in range(50):
    template = random.choice(templates)
    brief, output = generate_brief(template)
    training_data.append({
        "input": brief,
        "output": output
    })

# Save to file
with open("training_data_augmented.json", "w", encoding="utf-8") as f:
    json.dump(training_data, f, ensure_ascii=False, indent=2)

print(f"✅ Generated {len(training_data)} training examples")
```

Run this, then update your Colab training script to use the new data.

### Option 2: Use GPT/Claude for Data Generation

Ask me to generate 50 diverse training examples with proper JSON format!

---

## 🐛 Troubleshooting

### Model files not found
```
FileNotFoundError: LoRA adapters not found at models/phi3-brief-lora
```

**Solution:** Download and extract the model files (see Step 1-2 above)

### CUDA out of memory
```
RuntimeError: CUDA out of memory
```

**Solution:** 
- Close other GPU applications
- Or use CPU: Set `device="cpu"` in `brief_analyzer_lora.py`
- Or reduce batch size in training

### Model loading takes too long
**Solution:**
- Use the `/preload` endpoint to warm up the model before handling requests
- Consider using a smaller base model (Phi-3 is already quite small)

### Inconsistent JSON output
**Solution:**
- Increase training data diversity
- Add post-processing to normalize output
- Use lower temperature (0.3-0.5) for more deterministic output

---

## 📚 Additional Resources

- **Training Script:** `train_brief_analyzer_lora.py`
- **Existing Regex Parser:** `routes/parse_description.py` (fallback option)
- **Brief Storage API:** `routes/briefs.py`
- **Colab Training Notebook:** (in your Colab session)

---

## ✅ Checklist

- [ ] Downloaded `phi3-brief-lora.zip` from Colab
- [ ] Extracted to `models/phi3-brief-lora/`
- [ ] Ran `test_lora_integration.py` successfully
- [ ] Started backend with `python main.py`
- [ ] Tested health endpoint
- [ ] Tested analysis endpoint with curl
- [ ] (Optional) Integrated with frontend
- [ ] (Optional) Generated more training data
- [ ] (Optional) Retrained model with better data

---

## 🎉 Success!

If all tests pass, your LoRA model is now integrated and ready to use!

The model will:
- ✅ Analyze French architectural briefs
- ✅ Extract structured JSON data
- ✅ Handle complex descriptions better than regex
- ✅ Provide consistent API responses

**Next steps:**
1. Test with real briefs from your users
2. Collect feedback on accuracy
3. Generate more training data if needed
4. Retrain for better performance

---

**Questions?** Check the troubleshooting section or ask for help!
