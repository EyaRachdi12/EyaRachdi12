"""
Google Gemini Flash 2.0 Client for Architectural VQA
Analyzes floor plan images directly with vision capabilities
"""

import os
import base64
from io import BytesIO
from PIL import Image
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# Use Gemini 2.5 Flash (stable, multimodal, free tier)
model = genai.GenerativeModel('gemini-2.5-flash')

SYSTEM_PROMPT = """Tu es un assistant architectural expert spécialisé dans l'analyse de plans d'architecture.

Quand on te montre un plan architectural, tu dois:
1. Analyser visuellement le plan (pièces, surfaces, disposition)
2. Répondre de manière professionnelle et précise en français
3. Donner des détails techniques basés sur ce que tu vois
4. Si on te demande de visualiser ou montrer quelque chose, indique que tu vas générer une image

Sois précis, professionnel et utilise tes capacités de vision pour analyser le plan."""


def analyze_plan_with_gemini(image: Image.Image, question: str) -> dict:
    """
    Analyze a floor plan image and answer questions using Gemini Flash 2.0.
    
    Args:
        image: PIL Image of the floor plan
        question: User's question about the plan
    
    Returns:
        {
            "answer": str,
            "needs_image": bool,
            "image_prompt": str (if needs_image),
            "model": str
        }
    """
    
    if not GEMINI_API_KEY:
        return {
            "answer": "Erreur: GEMINI_API_KEY non configurée. Veuillez ajouter votre clé API Google Gemini dans le fichier .env",
            "needs_image": False,
            "error": "missing_api_key"
        }
    
    try:
        # Build the prompt
        prompt = f"""{SYSTEM_PROMPT}

Question du client: {question}

Analyse le plan architectural fourni et réponds à la question de manière détaillée et professionnelle."""

        # Call Gemini with image + text
        response = model.generate_content([prompt, image])
        
        answer = response.text
        
        # Detect if user wants visualization
        needs_image = detect_visualization_request(question, answer)
        
        result = {
            "answer": answer,
            "needs_image": needs_image,
            "model": "gemini-2.5-flash",
        }
        
        # Generate image prompt if needed
        if needs_image:
            result["image_prompt"] = generate_image_prompt(question, answer)
        
        return result
        
    except Exception as e:
        print(f"[Gemini] Error: {e}")
        return {
            "answer": f"Désolé, je ne peux pas analyser ce plan pour le moment. Erreur: {str(e)}",
            "needs_image": False,
            "error": str(e)
        }


def detect_visualization_request(question: str, answer: str) -> bool:
    """Detect if user wants to see an image"""
    visualization_keywords = [
        "montre", "visualise", "voir", "image", "photo", "rendu",
        "à quoi ressemble", "comment serait", "peux-tu montrer",
        "génère", "crée une image", "dessine"
    ]
    
    question_lower = question.lower()
    answer_lower = answer.lower()
    
    # Check question
    for keyword in visualization_keywords:
        if keyword in question_lower:
            return True
    
    # Check if LLM suggests showing something
    if any(phrase in answer_lower for phrase in ["voici une visualisation", "je vais générer", "voici un rendu"]):
        return True
    
    return False


def generate_image_prompt(question: str, llm_answer: str) -> str:
    """
    Generate a prompt for Stable Diffusion based on the question and context.
    """
    
    # Extract room type from question
    room_keywords = {
        "salle de bain": "modern bathroom",
        "cuisine": "modern kitchen",
        "salon": "modern living room",
        "séjour": "modern living room",
        "chambre": "modern bedroom",
        "terrasse": "modern terrace",
        "façade": "modern house facade",
        "bureau": "modern home office"
    }
    
    room_type = "modern interior"
    for french, english in room_keywords.items():
        if french in question.lower():
            room_type = english
            break
    
    # Extract style from question or use default
    style_keywords = {
        "contemporain": "contemporary",
        "minimaliste": "minimalist",
        "moderne": "modern",
        "industriel": "industrial",
        "scandinave": "scandinavian",
        "classique": "classic"
    }
    
    style = "contemporary"
    for french, english in style_keywords.items():
        if french in question.lower() or french in llm_answer.lower():
            style = english
            break
    
    # Build prompt
    prompt = f"{style} {room_type}, architectural photography, high quality, natural light, professional interior design, clean lines, elegant, realistic, 8k"
    
    return prompt


# Test function
def test_gemini():
    """Test Gemini with a sample floor plan"""
    from PIL import Image
    
    # Load a test image
    test_image_path = "DEEP/archi-platform/backend/test/sample_plans/test_T3_simple.png"
    image = Image.open(test_image_path)
    
    questions = [
        "Combien de pièces y a-t-il dans ce plan?",
        "Où est la cuisine?",
        "Quelle est la surface approximative du salon?"
    ]
    
    for question in questions:
        print(f"\nQuestion: {question}")
        result = analyze_plan_with_gemini(image, question)
        print(f"Réponse: {result['answer']}")
        print(f"Modèle: {result.get('model', 'N/A')}")
        print("-" * 60)


if __name__ == "__main__":
    test_gemini()
