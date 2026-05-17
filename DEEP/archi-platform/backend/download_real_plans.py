"""
Script to download professional floor plans from Pexels API
Run this to populate the library with real architectural plans
"""

import sys
from pathlib import Path
from utils.pexels_client import PexelsClient
import time

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

def main():
    """
    Download professional floor plans from Pexels
    """
    
    print("🏗️  Téléchargement de plans architecturaux professionnels depuis Pexels...")
    print("=" * 70)
    
    # Get API key
    api_key = input("\n📝 Entrez votre clé API Pexels (ou appuyez sur Entrée pour utiliser .env): ").strip()
    
    if not api_key:
        # Try to load from .env
        from dotenv import load_dotenv
        import os
        load_dotenv()
        api_key = os.getenv("PEXELS_API_KEY", "")
    
    if not api_key:
        print("\n❌ Erreur: Clé API Pexels manquante!")
        print("\n📌 Pour obtenir une clé API gratuite:")
        print("   1. Allez sur: https://www.pexels.com/api/")
        print("   2. Créez un compte gratuit")
        print("   3. Copiez votre clé API")
        print("   4. Ajoutez-la dans backend/.env: PEXELS_API_KEY=votre_clé")
        return
    
    # Initialize client
    client = PexelsClient(api_key=api_key)
    
    # Define search queries for different types of plans
    searches = [
        {"query": "architectural floor plan studio", "type": "Studio", "count": 2},
        {"query": "apartment floor plan 2 bedroom", "type": "T2", "count": 2},
        {"query": "house floor plan 3 bedroom", "type": "T3", "count": 2},
        {"query": "villa floor plan 4 bedroom", "type": "T4", "count": 2},
        {"query": "modern loft floor plan", "type": "Loft", "count": 2},
    ]
    
    # Output directory
    output_dir = Path(__file__).parent / "test" / "sample_plans" / "pexels"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Dossier de sortie: {output_dir}")
    print("\n🔍 Recherche de plans professionnels...\n")
    
    downloaded_plans = []
    
    for search in searches:
        print(f"🔎 Recherche: {search['query']} ({search['type']})")
        
        result = client.search_photos(search['query'], per_page=search['count'])
        photos = result.get("photos", [])
        
        if not photos:
            print(f"   ⚠️  Aucun résultat trouvé")
            continue
        
        for i, photo in enumerate(photos[:search['count']], 1):
            # Generate filename
            filename = f"{search['type'].lower()}_{i}_pexels_{photo['id']}.jpg"
            save_path = output_dir / filename
            
            # Download image
            print(f"   📥 Téléchargement: {filename}")
            success = client.download_image(photo['src']['large'], save_path)
            
            if success:
                downloaded_plans.append({
                    "filename": filename,
                    "type": search['type'],
                    "photographer": photo['photographer'],
                    "photographer_url": photo['photographer_url'],
                    "pexels_url": photo['url'],
                    "alt": photo.get('alt', 'Floor plan'),
                })
            
            # Rate limiting: wait 0.5s between downloads
            time.sleep(0.5)
        
        print()
    
    # Summary
    print("=" * 70)
    print(f"\n✅ Téléchargement terminé: {len(downloaded_plans)} plans")
    print(f"\n📋 Plans téléchargés:\n")
    
    for plan in downloaded_plans:
        print(f"   • {plan['filename']} ({plan['type']})")
        print(f"     Photographe: {plan['photographer']}")
        print(f"     Source: {plan['pexels_url']}")
        print()
    
    print("\n💡 Prochaine étape:")
    print("   Mettez à jour routes/floor_plans.py avec ces nouveaux plans!")
    print()

if __name__ == "__main__":
    main()
