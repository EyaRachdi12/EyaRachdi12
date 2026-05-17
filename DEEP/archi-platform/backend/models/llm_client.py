"""
LLM Client for Architectural VQA
Uses Groq LLaMA 3.1 70B for intelligent responses
"""

import os
import json
from groq import Groq
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

# Initialize Groq client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Tu es un assistant architectural expert spécialisé dans l'analyse de plans d'architecture.

Tu réponds aux questions sur les plans de manière:
- Professionnelle et précise
- En français naturel
- Avec des détails techniques quand nécessaire
- En utilisant les données d'analyse fournies

Si on te demande de visualiser ou montrer quelque chose, indique clairement que tu vas générer une image."""


def call_groq_llm(
    question: str,
    analysis_data: Dict,
    conversation_history: Optional[list] = None
) -> Dict:
    """
    Call Groq LLaMA 3.1 70B with architectural context.
    
    Args:
        question: User's question
        analysis_data: Structured data from OpenCV analysis
        conversation_history: Previous messages for context
    
    Returns:
        {
            "answer": str,
            "needs_image": bool,
            "image_prompt": str (if needs_image)
        }
    """
    
    # Build context from analysis
    context = f"""Données du plan architectural analysé:

Nombre de pièces: {analysis_data.get('n_rooms', 'N/A')}
Surface totale estimée: {analysis_data.get('total_area', 'N/A')} m²
Orientation: {analysis_data.get('orientation', 'N/A')}
Nombre de fenêtres: {analysis_data.get('n_windows', 'N/A')}
Nombre de portes: {analysis_data.get('n_doors', 'N/A')}

Pièces détectées:
{json.dumps(analysis_data.get('room_types', []), indent=2, ensure_ascii=False)}

Détails des pièces:
"""
    
    # Add room details
    for i, room in enumerate(analysis_data.get('rooms', [])[:8]):
        room_type = analysis_data.get('room_types', [])[i] if i < len(analysis_data.get('room_types', [])) else f"Pièce {i+1}"
        area_m2 = estimate_room_area(room, analysis_data)
        position = get_room_position(room, analysis_data)
        context += f"\n- {room_type}: ~{area_m2} m², position {position}"
    
    # Build messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"{context}\n\nQuestion du client: {question}"}
    ]
    
    # Add conversation history if provided
    if conversation_history:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history + [messages[-1]]
    
    try:
        # Call Groq API
        response = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",  # Updated model
            messages=messages,
            temperature=0.7,
            max_tokens=800,
            top_p=0.9,
        )
        
        answer = response.choices[0].message.content
        
        # Detect if user wants visualization
        needs_image = detect_visualization_request(question, answer)
        
        result = {
            "answer": answer,
            "needs_image": needs_image,
            "model": "llama-3.3-70b-versatile",
            "tokens_used": response.usage.total_tokens if hasattr(response, 'usage') else 0
        }
        
        # Generate image prompt if needed
        if needs_image:
            result["image_prompt"] = generate_image_prompt(question, answer, analysis_data)
        
        return result
        
    except Exception as e:
        print(f"[LLM] Error calling Groq: {e}")
        return {
            "answer": f"Désolé, je ne peux pas répondre pour le moment. Erreur: {str(e)}",
            "needs_image": False,
            "error": str(e)
        }


def estimate_room_area(room: Dict, analysis_data: Dict) -> int:
    """Estimate room area in m²"""
    total_area = analysis_data.get('total_area', 80)
    total_px = analysis_data.get('width', 1000) * analysis_data.get('height', 1000)
    room_px = room.get('area_px', 0)
    
    if total_px == 0:
        return 15
    
    fraction = room_px / total_px
    area = max(4, min(60, round(total_area * fraction)))
    return area


def get_room_position(room: Dict, analysis_data: Dict) -> str:
    """Get human-readable position"""
    img_w = analysis_data.get('width', 1000)
    img_h = analysis_data.get('height', 1000)
    cx = room.get('cx', img_w // 2)
    cy = room.get('cy', img_h // 2)
    
    h_pos = "gauche" if cx < img_w / 3 else ("droite" if cx > 2 * img_w / 3 else "centre")
    v_pos = "haut" if cy < img_h / 3 else ("bas" if cy > 2 * img_h / 3 else "milieu")
    
    # Map to cardinal directions
    position_map = {
        ("haut", "gauche"): "nord-ouest",
        ("haut", "droite"): "nord-est",
        ("haut", "centre"): "nord",
        ("bas", "gauche"): "sud-ouest",
        ("bas", "droite"): "sud-est",
        ("bas", "centre"): "sud",
        ("milieu", "gauche"): "ouest",
        ("milieu", "droite"): "est",
        ("milieu", "centre"): "centre"
    }
    
    return position_map.get((v_pos, h_pos), "centre")


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


def generate_image_prompt(question: str, llm_answer: str, analysis_data: Dict) -> str:
    """
    Generate a prompt for Stable Diffusion based on the question and context.
    """
    
    # Extract room type from question
    room_keywords = {
        "salle de bain": "modern bathroom",
        "cuisine": "modern kitchen",
        "salon": "modern living room",
        "chambre": "modern bedroom",
        "terrasse": "modern terrace",
        "façade": "modern house facade"
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
        "scandinave": "scandinavian"
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
def test_llm():
    """Test the LLM with a sample question"""
    test_analysis = {
        "n_rooms": 4,
        "total_area": 85,
        "orientation": "nord-ouest",
        "n_windows": 6,
        "n_doors": 4,
        "room_types": ["Salon / Séjour", "Cuisine", "Chambre principale", "Salle de bain"],
        "rooms": [
            {"area_px": 50000, "cx": 300, "cy": 200},
            {"area_px": 30000, "cx": 600, "cy": 200},
            {"area_px": 40000, "cx": 300, "cy": 500},
            {"area_px": 15000, "cx": 600, "cy": 500},
        ],
        "width": 800,
        "height": 600
    }
    
    result = call_groq_llm("Où est la salle de bain?", test_analysis)
    print("Answer:", result["answer"])
    print("Needs image:", result["needs_image"])
    if result.get("image_prompt"):
        print("Image prompt:", result["image_prompt"])


if __name__ == "__main__":
    test_llm()
