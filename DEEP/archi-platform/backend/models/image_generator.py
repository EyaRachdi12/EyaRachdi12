"""
Image Generation with Pollinations.ai
Free AI image generation without API key
"""

import os
import io
import base64
import requests
from PIL import Image
from dotenv import load_dotenv
import urllib.parse

load_dotenv()

# Pollinations.ai - Free, no API key needed!
POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt}"


def generate_architectural_image(prompt: str, negative_prompt: str = None) -> dict:
    """
    Generate an architectural image using Pollinations.ai (FREE).
    
    Args:
        prompt: Description of the image to generate
        negative_prompt: What to avoid in the image (not used by Pollinations)
    
    Returns:
        {
            "image_b64": str (base64 encoded image),
            "success": bool,
            "error": str (if failed)
        }
    """
    
    try:
        # Encode prompt for URL
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Add parameters for better quality
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true"
        
        print(f"[Pollinations] Generating: {prompt[:80]}...")
        
        # Request image with longer timeout
        response = requests.get(url, timeout=120)  # Increased to 120 seconds
        
        if response.status_code == 200:
            # Convert image to base64
            image = Image.open(io.BytesIO(response.content))
            
            # Resize to reasonable size
            image = image.resize((768, 768), Image.Resampling.LANCZOS)
            
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            img_b64 = base64.b64encode(buffered.getvalue()).decode()
            
            print(f"[Pollinations] ✅ Success!")
            
            return {
                "success": True,
                "image_b64": f"data:image/png;base64,{img_b64}"
            }
        else:
            return {
                "success": False,
                "error": f"Pollinations API error: {response.status_code}"
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def build_architectural_prompt(
    style: str,
    description: str,
    elements: list,
    view_type: str
) -> str:
    """
    Build a detailed prompt for architectural image generation.
    
    Args:
        style: Architectural style (contemporain, minimaliste, etc.)
        description: User's project description
        elements: List of architectural elements (terrasse, jardin, etc.)
        view_type: Type of view (facade, interior_living, etc.)
    
    Returns:
        Detailed prompt string
    """
    
    # Style mapping
    style_map = {
        "contemporain": "contemporary modern",
        "minimaliste": "minimalist clean",
        "industriel": "industrial loft",
        "scandinave": "scandinavian nordic",
        "mediterraneen": "mediterranean",
        "bioclimatique": "eco-friendly sustainable",
        "classique": "classic traditional",
        "haussmannien": "haussmannian parisian"
    }
    
    style_en = style_map.get(style.lower(), "modern")
    
    # View type mapping
    view_map = {
        "facade": "exterior facade view, front elevation, architectural photography",
        "interior_living": "interior living room, spacious open space, natural light",
        "interior_kitchen": "interior modern kitchen, open plan, island counter",
        "interior_bedroom": "interior bedroom, comfortable, natural light",
        "aerial": "aerial view, bird's eye perspective, architectural site plan",
        "garden": "garden terrace view, outdoor space, landscaping"
    }
    
    view_desc = view_map.get(view_type, "architectural view")
    
    # Elements mapping
    elements_map = {
        "terrasse": "wooden terrace deck",
        "jardin": "landscaped garden",
        "piscine": "swimming pool",
        "garage": "modern garage",
        "grandes_fenetres": "large floor-to-ceiling windows",
        "balcon": "balcony"
    }
    
    elements_desc = ", ".join([elements_map.get(e, e) for e in elements if e in elements_map])
    
    # Build final prompt
    prompt_parts = [
        f"{style_en} architecture",
        view_desc,
        elements_desc if elements_desc else "",
        "high quality, professional architectural photography",
        "8k, detailed, realistic, natural lighting",
        "award winning design"
    ]
    
    # Add user description if provided
    if description and len(description) > 10:
        # Extract key architectural terms from description
        prompt_parts.insert(2, description[:100])
    
    prompt = ", ".join([p for p in prompt_parts if p])
    
    return prompt


def generate_sketch_set(
    style: str,
    description: str,
    elements: list,
    view_types: list,
    n: int = 6
) -> list:
    """
    Generate a set of architectural sketches.
    
    Args:
        style: Architectural style
        description: Project description
        elements: Architectural elements
        view_types: List of view types to generate
        n: Number of images to generate
    
    Returns:
        List of generated images with metadata
    """
    
    import time
    
    sketches = []
    
    # Limit to avoid rate limits
    max_images = min(n, len(view_types), 4)  # Max 4 images to avoid rate limits
    
    # Generate images for each view type
    for i, view_type in enumerate(view_types[:max_images]):
        prompt = build_architectural_prompt(style, description, elements, view_type)
        
        print(f"[ImageGen] Generating {view_type} ({i+1}/{max_images})")
        print(f"[ImageGen] Prompt: {prompt[:100]}...")
        
        result = generate_architectural_image(prompt)
        
        if result["success"]:
            # View type titles
            view_titles = {
                "facade": "Façade principale",
                "interior_living": "Salon / Séjour",
                "interior_kitchen": "Cuisine ouverte",
                "interior_bedroom": "Chambre",
                "aerial": "Vue aérienne",
                "garden": "Jardin / Terrasse"
            }
            
            sketches.append({
                "id": i + 1,
                "title": view_titles.get(view_type, f"Vue {i+1}"),
                "prompt": prompt,
                "image_b64": result["image_b64"],
                "image_url": None,
                "view_type": view_type,
                "liked": False
            })
            
            # Wait between requests to avoid rate limits (except for last image)
            if i < max_images - 1:
                print(f"[ImageGen] Waiting 3 seconds before next generation...")
                time.sleep(3)
        else:
            print(f"[ImageGen] Failed: {result.get('error')}")
    
    return sketches


# Test function
def test_image_generation():
    """Test image generation"""
    prompt = build_architectural_prompt(
        style="contemporain",
        description="Maison moderne pour famille de 4",
        elements=["terrasse", "grandes_fenetres"],
        view_type="facade"
    )
    
    print(f"Prompt: {prompt}\n")
    
    result = generate_architectural_image(prompt)
    
    if result["success"]:
        print("✅ Image generated successfully!")
        print(f"Base64 length: {len(result['image_b64'])}")
    else:
        print(f"❌ Error: {result['error']}")


if __name__ == "__main__":
    test_image_generation()
