"""
Download sample floor plan images for testing.
Uses publicly available floor plan images.
"""

import os
import requests
from pathlib import Path

SAMPLE_DIR = Path(__file__).parent / "sample_plans"
SAMPLE_DIR.mkdir(exist_ok=True)

# Public domain floor plan images (Wikimedia Commons + open sources)
SAMPLE_IMAGES = [
    {
        "name": "plan_simple_2pieces.jpg",
        "url":  "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Floorplan_2_room_apartment.jpg/640px-Floorplan_2_room_apartment.jpg",
        "desc": "Appartement 2 pièces simple",
    },
    {
        "name": "plan_maison_4pieces.jpg",
        "url":  "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Sample_floorplan.jpg/640px-Sample_floorplan.jpg",
        "desc": "Maison 4 pièces",
    },
    {
        "name": "plan_appartement_3pieces.png",
        "url":  "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Floorplan_3_room_apartment.jpg/640px-Floorplan_3_room_apartment.jpg",
        "desc": "Appartement 3 pièces",
    },
]

# Fallback: generate synthetic floor plan images if download fails
def generate_synthetic_plan(path: Path, plan_type: str = "simple"):
    """Generate a simple synthetic floor plan image using PIL."""
    from PIL import Image, ImageDraw, ImageFont
    import random

    W, H = 600, 500
    img  = Image.new("RGB", (W, H), color=(245, 242, 238))
    draw = ImageDraw.Draw(img)

    # Outer walls
    draw.rectangle([30, 30, W-30, H-30], outline=(40, 40, 40), width=4)

    if plan_type == "simple":
        # 2-room plan
        draw.line([W//2, 30, W//2, H-30], fill=(40, 40, 40), width=3)
        draw.line([30, H//2, W//2, H//2], fill=(40, 40, 40), width=3)

        # Doors (arcs approximated as lines)
        draw.arc([W//2-20, H//2-20, W//2+20, H//2+20], 0, 90, fill=(80, 80, 80), width=2)

        # Labels
        draw.text((W//4, H//4),   "Salon\n32 m²",   fill=(60, 60, 60))
        draw.text((W//4, 3*H//4), "Cuisine\n18 m²", fill=(60, 60, 60))
        draw.text((3*W//4, H//2), "Chambre\n22 m²", fill=(60, 60, 60))

    elif plan_type == "complex":
        # 4-room plan
        draw.line([W//2, 30, W//2, H-30],       fill=(40, 40, 40), width=3)
        draw.line([30, H//2, W-30, H//2],        fill=(40, 40, 40), width=3)
        draw.line([W//2, H//2, W//2, H-30],      fill=(40, 40, 40), width=2)
        draw.line([30, 2*H//3, W//2, 2*H//3],    fill=(40, 40, 40), width=2)

        draw.text((W//4,   H//4),   "Salon\n30 m²",    fill=(60, 60, 60))
        draw.text((3*W//4, H//4),   "Cuisine\n16 m²",  fill=(60, 60, 60))
        draw.text((W//4,   3*H//5), "Chambre 1\n20 m²",fill=(60, 60, 60))
        draw.text((W//4,   5*H//6), "SDB\n8 m²",       fill=(60, 60, 60))
        draw.text((3*W//4, 3*H//4), "Chambre 2\n16 m²",fill=(60, 60, 60))

    # North arrow
    draw.text((W-60, 40), "N↑", fill=(100, 100, 100))

    # Scale bar
    draw.line([40, H-50, 140, H-50], fill=(80, 80, 80), width=2)
    draw.text((60, H-45), "0    5m", fill=(80, 80, 80))

    img.save(path)
    print(f"  ✅ Synthetic plan generated: {path.name}")


def download_samples():
    print("📥 Downloading sample floor plan images...\n")
    downloaded = 0

    for sample in SAMPLE_IMAGES:
        dest = SAMPLE_DIR / sample["name"]
        if dest.exists():
            print(f"  ✓ Already exists: {sample['name']}")
            downloaded += 1
            continue

        try:
            print(f"  ⬇ Downloading {sample['name']}...")
            r = requests.get(sample["url"], timeout=15, headers={
                "User-Agent": "ArchiGuide-Test/1.0"
            })
            if r.status_code == 200:
                dest.write_bytes(r.content)
                print(f"  ✅ {sample['name']} ({len(r.content)//1024} KB)")
                downloaded += 1
            else:
                print(f"  ⚠ HTTP {r.status_code} — generating synthetic...")
                generate_synthetic_plan(dest, "simple")
                downloaded += 1
        except Exception as e:
            print(f"  ⚠ Download failed ({e}) — generating synthetic...")
            generate_synthetic_plan(dest, "simple")
            downloaded += 1

    # Always generate synthetic plans as guaranteed test data
    for name, ptype in [
        ("synthetic_simple.png",  "simple"),
        ("synthetic_complex.png", "complex"),
    ]:
        path = SAMPLE_DIR / name
        if not path.exists():
            generate_synthetic_plan(path, ptype)
            downloaded += 1

    print(f"\n✅ {downloaded} sample images ready in {SAMPLE_DIR}")
    return downloaded


if __name__ == "__main__":
    download_samples()
