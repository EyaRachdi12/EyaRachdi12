"""
Pexels API Client - Fetch professional floor plans
"""

import requests
from typing import List, Dict, Optional
import os
from pathlib import Path

class PexelsClient:
    """
    Client for Pexels API to fetch professional architectural floor plans
    API is 100% free: 200 requests/hour, 20,000/month
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PEXELS_API_KEY", "")
        self.base_url = "https://api.pexels.com/v1"
        self.headers = {
            "Authorization": self.api_key
        }
    
    def search_photos(self, query: str, per_page: int = 15, page: int = 1) -> Dict:
        """
        Search for photos on Pexels
        
        Args:
            query: Search query (e.g., "floor plan", "architectural blueprint")
            per_page: Number of results per page (max 80)
            page: Page number
            
        Returns:
            Dictionary with photos data
        """
        url = f"{self.base_url}/search"
        params = {
            "query": query,
            "per_page": per_page,
            "page": page,
            "orientation": "landscape"  # Better for floor plans
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching from Pexels: {e}")
            return {"photos": []}
    
    def get_floor_plans(self, count: int = 10) -> List[Dict]:
        """
        Get professional floor plan images from Pexels
        
        Args:
            count: Number of floor plans to fetch
            
        Returns:
            List of floor plan data with URLs
        """
        queries = [
            "architectural floor plan",
            "house blueprint",
            "apartment floor plan",
            "architectural drawing",
            "building plan"
        ]
        
        all_plans = []
        
        for query in queries:
            if len(all_plans) >= count:
                break
                
            result = self.search_photos(query, per_page=5)
            photos = result.get("photos", [])
            
            for photo in photos:
                if len(all_plans) >= count:
                    break
                    
                plan_data = {
                    "id": photo["id"],
                    "photographer": photo["photographer"],
                    "photographer_url": photo["photographer_url"],
                    "url": photo["url"],
                    "src": {
                        "original": photo["src"]["original"],
                        "large2x": photo["src"]["large2x"],
                        "large": photo["src"]["large"],
                        "medium": photo["src"]["medium"],
                    },
                    "alt": photo.get("alt", "Floor plan"),
                    "width": photo["width"],
                    "height": photo["height"],
                }
                all_plans.append(plan_data)
        
        return all_plans
    
    def download_image(self, url: str, save_path: Path) -> bool:
        """
        Download an image from URL to local path
        
        Args:
            url: Image URL
            save_path: Path to save the image
            
        Returns:
            True if successful, False otherwise
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            save_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(save_path, 'wb') as f:
                f.write(response.content)
            
            print(f"✅ Downloaded: {save_path.name}")
            return True
            
        except Exception as e:
            print(f"❌ Error downloading {url}: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # You need to get a free API key from: https://www.pexels.com/api/
    client = PexelsClient()
    
    # Search for floor plans
    plans = client.get_floor_plans(count=8)
    
    print(f"Found {len(plans)} floor plans:")
    for i, plan in enumerate(plans, 1):
        print(f"{i}. {plan['alt']} by {plan['photographer']}")
        print(f"   URL: {plan['url']}")
        print(f"   Image: {plan['src']['large']}")
        print()
