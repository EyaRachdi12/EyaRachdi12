"""
Generate professional architectural floor plans using Pollinations.ai
Fast and free - generates realistic technical blueprints
"""

import requests
from pathlib import Path
import time
from urllib.parse import quote

def generate_floor_plan(prompt: str, filename: str, output_dir: Path) -> bool:
    """
    Generate a floor plan using Pollinations.ai
    
    Args:
        prompt: Description of the floor plan
        filename: Output filename
        output_dir: Directory to save the image
        
    Returns:
        True if successful
    """
    # Pollinations.ai URL with FLUX model (best for technical drawings)
    base_url = "https://image.pollinations.ai/prompt"
    
    # Encode prompt
    encoded_prompt = quote(prompt)
    
    # Build URL with parameters optimized for floor plans
    url = f"{base_url}/{encoded_prompt}?width=1024&height=1024&model=flux&nologo=true&enhance=true"
    
    print(f"🎨 Génération: {filename}")
    print(f"   Prompt: {prompt[:80]}...")
    
    try:
        # Download image (Pollinations generates on-the-fly)
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        
        # Save image
        output_path = output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"   ✅ Sauvegardé: {filename}\n")
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}\n")
        return False


def main():
    """Generate professional floor plans for the library"""
    
    print("🏗️  Génération de plans architecturaux avec l'IA")
    print("=" * 70)
    print("⚡ Utilisation de Pollinations.ai (gratuit, pas de clé API)")
    print("⏱️  Temps estimé: ~30-60 secondes par plan\n")
    
    # Output directory
    output_dir = Path(__file__).parent / "test" / "sample_plans" / "ai_generated"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Floor plans to generate with optimized prompts
    plans = [
        {
            "filename": "studio_modern_ai.png",
            "prompt": "professional architectural floor plan blueprint of a modern studio apartment, 25m2, technical drawing, top view, black lines on white background, detailed measurements, minimalist layout with kitchenette and bathroom, clean architectural style"
        },
        {
            "filename": "t2_contemporary_ai.png",
            "prompt": "architectural floor plan blueprint of a 2 bedroom apartment 55m2, technical drawing, top view, black and white, detailed layout with living room, kitchen, bathroom, two bedrooms, professional architectural blueprint style with measurements"
        },
        {
            "filename": "t3_family_ai.png",
            "prompt": "professional house floor plan blueprint, 3 bedroom family home 75m2, architectural technical drawing, top view, black lines on white, detailed layout with living room, kitchen, 2 bedrooms, bathroom, hallway, clean architectural blueprint"
        },
        {
            "filename": "t4_villa_ai.png",
            "prompt": "luxury villa floor plan blueprint, 4 bedroom house 120m2, professional architectural drawing, top view, technical blueprint style, detailed layout with master suite, 3 bedrooms, living room, kitchen, 2 bathrooms, terrace, black and white architectural plan"
        },
        {
            "filename": "loft_modern_ai.png",
            "prompt": "modern loft floor plan blueprint, 110m2 open space, architectural technical drawing, top view, black lines on white background, detailed layout with mezzanine, open kitchen, living area, bedroom, bathroom, industrial loft style architectural plan"
        },
    ]
    
    print(f"📁 Dossier de sortie: {output_dir}\n")
    print(f"🎯 Génération de {len(plans)} plans architecturaux...\n")
    
    successful = 0
    
    for i, plan in enumerate(plans, 1):
        print(f"[{i}/{len(plans)}] ", end="")
        
        if generate_floor_plan(plan["prompt"], plan["filename"], output_dir):
            successful += 1
        
        # Small delay between generations to be respectful
        if i < len(plans):
            time.sleep(2)
    
    # Summary
    print("=" * 70)
    print(f"\n✅ Génération terminée: {successful}/{len(plans)} plans créés")
    print(f"📁 Plans sauvegardés dans: {output_dir}\n")
    
    if successful > 0:
        print("💡 Prochaine étape:")
        print("   Mettez à jour routes/floor_plans.py avec ces nouveaux plans!")
    
    print()


if __name__ == "__main__":
    main()
