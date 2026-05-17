"""
Test script for LoRA Brief Analyzer integration
================================================

This script tests the LoRA model integration without starting the full backend.
Run this to verify the model files are in place and working.

Usage:
    python test_lora_integration.py
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

def test_model_files():
    """Check if model files exist"""
    print("=" * 80)
    print("1. Checking model files...")
    print("=" * 80)
    
    from models.brief_analyzer_lora import get_analyzer
    
    analyzer = get_analyzer()
    lora_path = Path(analyzer.lora_path)
    
    print(f"LoRA path: {lora_path}")
    print(f"Exists: {lora_path.exists()}")
    
    if lora_path.exists():
        print("\n✅ Model directory found!")
        print("\nFiles in directory:")
        for file in lora_path.iterdir():
            print(f"  - {file.name} ({file.stat().st_size / 1024 / 1024:.2f} MB)")
        return True
    else:
        print("\n❌ Model directory NOT found!")
        print("\n📥 You need to download the model from Colab:")
        print("   1. In Colab, run the zip command:")
        print("      !cd /content && zip -r phi3-brief-lora.zip phi3-brief-lora/")
        print("   2. Download phi3-brief-lora.zip from Colab Files panel")
        print("   3. Extract to: DEEP/archi-platform/backend/models/phi3-brief-lora/")
        return False


def test_model_loading():
    """Test loading the model"""
    print("\n" + "=" * 80)
    print("2. Testing model loading...")
    print("=" * 80)
    
    try:
        from models.brief_analyzer_lora import get_analyzer
        
        analyzer = get_analyzer()
        print(f"Base model: {analyzer.base_model_name}")
        print(f"Device: {analyzer.device}")
        print(f"Loaded: {analyzer._loaded}")
        
        print("\n⏳ Loading model (this may take 1-2 minutes)...")
        analyzer.load()
        
        print("✅ Model loaded successfully!")
        return True
        
    except FileNotFoundError as e:
        print(f"❌ Model files not found: {e}")
        return False
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_inference():
    """Test model inference"""
    print("\n" + "=" * 80)
    print("3. Testing inference...")
    print("=" * 80)
    
    try:
        from models.brief_analyzer_lora import get_analyzer
        import json
        
        analyzer = get_analyzer()
        
        test_briefs = [
            "Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€",
            "Petite maison 80m² pour couple, 2 chambres, budget 250k€, style moderne",
        ]
        
        for i, brief in enumerate(test_briefs, 1):
            print(f"\n📝 Test {i}: {brief}")
            print("-" * 80)
            
            result = analyzer.analyze(brief, temperature=0.7)
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print("✅ Success!")
                print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return True
        
    except Exception as e:
        print(f"❌ Inference failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("🧪 Testing LoRA Brief Analyzer Integration")
    print("=" * 80)
    
    # Test 1: Check files
    files_ok = test_model_files()
    
    if not files_ok:
        print("\n" + "=" * 80)
        print("⚠️  Cannot proceed without model files")
        print("=" * 80)
        return
    
    # Test 2: Load model
    loading_ok = test_model_loading()
    
    if not loading_ok:
        print("\n" + "=" * 80)
        print("⚠️  Cannot proceed - model loading failed")
        print("=" * 80)
        return
    
    # Test 3: Test inference
    inference_ok = test_inference()
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 Test Summary")
    print("=" * 80)
    print(f"Model files: {'✅' if files_ok else '❌'}")
    print(f"Model loading: {'✅' if loading_ok else '❌'}")
    print(f"Inference: {'✅' if inference_ok else '❌'}")
    
    if files_ok and loading_ok and inference_ok:
        print("\n🎉 All tests passed! The integration is working.")
        print("\n📝 Next steps:")
        print("   1. Start the backend: python main.py")
        print("   2. Test the API endpoint:")
        print("      curl -X POST http://localhost:8000/api/analyze-brief-lora \\")
        print("           -H 'Content-Type: application/json' \\")
        print("           -d '{\"description\": \"Maison 120m², 3 chambres, budget 400k€\"}'")
    else:
        print("\n⚠️  Some tests failed. Please fix the issues above.")


if __name__ == "__main__":
    main()
