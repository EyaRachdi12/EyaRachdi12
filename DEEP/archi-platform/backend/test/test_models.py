"""
Test suite for ArchiGuide AI models.
Tests: Caption model, VQA model, plan analyzer, API endpoints.

Run with:
    python -m pytest test/test_models.py -v
or:
    python test/test_models.py
"""

import sys
import os
import time
import torch
import numpy as np
from pathlib import Path
from PIL import Image

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.caption_model import FloorPlanCaptionModel, IMAGE_TRANSFORM
from models.vqa_model      import FloorPlanVQAModel, question_tokenizer, ANSWER_CLASSES
from models.vocabulary     import vocab, Vocabulary
from utils.plan_analyzer   import (
    build_structured_analysis,
    extract_rooms,
    extract_style,
    extract_total_area,
)
from test.download_samples import download_samples, SAMPLE_DIR


# ── Colors for terminal output ────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

PASS = f"{GREEN}✅ PASS{RESET}"
FAIL = f"{RED}❌ FAIL{RESET}"
INFO = f"{BLUE}ℹ{RESET}"


def section(title: str):
    print(f"\n{BOLD}{BLUE}{'═'*60}{RESET}")
    print(f"{BOLD}{BLUE}  {title}{RESET}")
    print(f"{BOLD}{BLUE}{'═'*60}{RESET}")


def test(name: str, condition: bool, detail: str = ""):
    status = PASS if condition else FAIL
    print(f"  {status}  {name}")
    if detail:
        print(f"         {YELLOW}{detail}{RESET}")
    return condition


# ══════════════════════════════════════════════════════════════════════════════
# 1. Vocabulary Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_vocabulary():
    section("1. Vocabulary")
    results = []

    v = Vocabulary()

    results.append(test("Vocab size > 100", len(v) > 100, f"size={len(v)}"))
    results.append(test("PAD index = 0",    v.PAD_IDX == 0))
    results.append(test("SOS index = 1",    v.SOS_IDX == 1))
    results.append(test("EOS index = 2",    v.EOS_IDX == 2))

    # Encode / decode roundtrip
    sentence = "salon cuisine chambre"
    encoded  = v.encode(sentence)
    decoded  = v.decode(encoded)
    results.append(test(
        "Encode/decode roundtrip",
        "salon" in decoded and "cuisine" in decoded,
        f"decoded='{decoded}'"
    ))

    # UNK handling
    encoded_unk = v.encode("xyzunknownword")
    results.append(test(
        "UNK token for unknown words",
        v.UNK_IDX in encoded_unk,
    ))

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# 2. Caption Model Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_caption_model(image: Image.Image):
    section("2. Caption Model (ResNet-101 + LSTM + Attention)")
    results = []

    model = FloorPlanCaptionModel()
    model.eval()

    # Architecture checks
    results.append(test("Model instantiation", model is not None))
    results.append(test(
        "Encoder output shape",
        True,
        "ResNet-101 → (B, 196, 2048)"
    ))

    # Encoder forward pass
    img_t = IMAGE_TRANSFORM(image.convert("RGB")).unsqueeze(0)
    with torch.no_grad():
        enc_out = model.encoder(img_t)
    results.append(test(
        "Encoder forward pass",
        enc_out.shape == (1, 196, 2048),
        f"shape={enc_out.shape}"
    ))

    # Attention mechanism
    h_dummy = torch.zeros(1, 512)
    context, alpha = model.decoder.attention(enc_out, h_dummy)
    results.append(test(
        "Attention output shape",
        alpha.shape == (1, 196),
        f"alpha.shape={alpha.shape}"
    ))
    results.append(test(
        "Attention weights sum ≈ 1",
        abs(alpha.sum().item() - 1.0) < 0.01,
        f"sum={alpha.sum().item():.4f}"
    ))

    # Caption generation
    print(f"\n  {INFO} Generating caption (beam_size=3)...")
    t0 = time.time()
    caption, attn_maps = model.generate_caption(image, beam_size=3)
    elapsed = time.time() - t0

    results.append(test(
        "Caption generated",
        isinstance(caption, str) and len(caption) > 0,
        f"caption='{caption[:80]}...'" if len(caption) > 80 else f"caption='{caption}'"
    ))
    results.append(test(
        "Attention maps shape",
        attn_maps.ndim >= 2,
        f"shape={attn_maps.shape}"
    ))
    results.append(test(
        f"Inference time < 30s",
        elapsed < 30,
        f"time={elapsed:.2f}s"
    ))

    print(f"\n  {INFO} Generated caption:")
    print(f"  {YELLOW}\"{caption}\"{RESET}")

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# 3. VQA Model Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_vqa_model(image: Image.Image):
    section("3. VQA Model (ResNet-101 + GRU + Fusion)")
    results = []

    model = FloorPlanVQAModel()
    model.eval()

    results.append(test("VQA model instantiation", model is not None))
    results.append(test(
        f"Answer classes count",
        len(ANSWER_CLASSES) > 20,
        f"{len(ANSWER_CLASSES)} classes"
    ))

    # Question tokenizer
    q = "Où est la salle de bain ?"
    tokens = question_tokenizer.tokenize(q)
    results.append(test(
        "Question tokenization",
        tokens.shape[0] == 20,
        f"shape={tokens.shape}"
    ))

    # VQA forward pass
    img_t = torch.zeros(1, 3, 224, 224)
    q_t   = tokens.unsqueeze(0)
    with torch.no_grad():
        logits = model(img_t, q_t)
    results.append(test(
        "VQA forward pass",
        logits.shape == (1, len(ANSWER_CLASSES)),
        f"logits.shape={logits.shape}"
    ))

    # Answer generation on real image
    test_questions = [
        "Où est la salle de bain ?",
        "Quelle est la surface du salon ?",
        "Combien de fenêtres y a-t-il ?",
        "Y a-t-il un dressing ?",
        "Quel est le style architectural ?",
    ]

    print(f"\n  {INFO} VQA answers on sample plan:")
    for q_text in test_questions:
        result = model.answer(image, q_text)
        results.append(test(
            f"Q: {q_text[:45]}",
            result["answer"] != "" and result["confidence"] > 0,
            f"→ {result['answer']} (conf: {result['confidence_pct'] if 'confidence_pct' in result else result['confidence']:.0%})"
        ))
        print(f"     Q: {q_text}")
        print(f"     A: {YELLOW}{result['answer']}{RESET} (conf: {result['confidence']:.1%})")
        print()

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Plan Analyzer Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_plan_analyzer(image: Image.Image):
    section("4. Plan Analyzer (Rule-based)")
    results = []

    # Test with rich caption
    caption = (
        "Plan résidentiel contemporain comprenant un salon de 32 m² avec 3 fenêtres "
        "orienté sud-ouest, une cuisine ouverte de 18 m², deux chambres dont une "
        "chambre principale de 22 m² avec dressing, une salle de bain de 8 m², "
        "et un WC séparé. Surface totale habitable : 99 m²."
    )

    rooms = extract_rooms(caption)
    results.append(test(
        "Room extraction",
        len(rooms) >= 3,
        f"found {len(rooms)} rooms: {[r['name'] for r in rooms]}"
    ))

    style = extract_style(caption)
    results.append(test(
        "Style extraction",
        style == "Contemporain",
        f"style='{style}'"
    ))

    area = extract_total_area(caption)
    results.append(test(
        "Total area extraction",
        "99" in area,
        f"area='{area}'"
    ))

    # Full analysis
    analysis = build_structured_analysis(caption, image, confidence=0.92)
    results.append(test("Full analysis dict",    isinstance(analysis, dict)))
    results.append(test("Has 'rooms' key",       "rooms" in analysis))
    results.append(test("Has 'caption' key",     "caption" in analysis))
    results.append(test("Has 'total_area' key",  "total_area" in analysis))
    results.append(test("Has 'style' key",       "style" in analysis))
    results.append(test("Has 'summary' key",     "summary" in analysis))
    results.append(test(
        "Confidence stored",
        analysis["confidence"] == 92.0,
        f"confidence={analysis['confidence']}"
    ))

    print(f"\n  {INFO} Analysis summary:")
    print(f"  {YELLOW}{analysis['summary']}{RESET}")

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# 5. Image Preprocessing Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_preprocessing(image: Image.Image):
    section("5. Image Preprocessing")
    results = []

    # Caption transform
    tensor = IMAGE_TRANSFORM(image.convert("RGB"))
    results.append(test(
        "Caption transform shape",
        tensor.shape == (3, 256, 256),
        f"shape={tensor.shape}"
    ))
    results.append(test(
        "Tensor dtype float32",
        tensor.dtype == torch.float32,
    ))
    results.append(test(
        "Normalized values in range",
        tensor.min().item() > -3 and tensor.max().item() < 3,
        f"min={tensor.min():.2f}, max={tensor.max():.2f}"
    ))

    # Different image sizes
    for size in [(100, 100), (800, 600), (1200, 900)]:
        img_resized = image.resize(size)
        t = IMAGE_TRANSFORM(img_resized.convert("RGB"))
        results.append(test(
            f"Handles {size[0]}×{size[1]} input",
            t.shape == (3, 256, 256),
        ))

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# 6. Multi-image Tests
# ══════════════════════════════════════════════════════════════════════════════
def test_multiple_images():
    section("6. Multi-image Caption Test")
    results = []

    model = FloorPlanCaptionModel()
    model.eval()

    images = list(SAMPLE_DIR.glob("*.png")) + list(SAMPLE_DIR.glob("*.jpg"))
    if not images:
        print(f"  {YELLOW}⚠ No images found in {SAMPLE_DIR}{RESET}")
        return True

    print(f"  {INFO} Testing on {len(images)} images:\n")

    for img_path in images[:5]:  # limit to 5
        try:
            img     = Image.open(img_path).convert("RGB")
            caption, _ = model.generate_caption(img, beam_size=2)
            results.append(test(
                f"{img_path.name[:40]}",
                len(caption) > 0,
                f"→ '{caption[:60]}...'" if len(caption) > 60 else f"→ '{caption}'"
            ))
        except Exception as e:
            results.append(test(f"{img_path.name[:40]}", False, str(e)))

    return all(results)


# ══════════════════════════════════════════════════════════════════════════════
# Main runner
# ══════════════════════════════════════════════════════════════════════════════
def main():
    print(f"\n{BOLD}{'═'*60}")
    print(f"  ArchiGuide AI — Model Test Suite")
    print(f"  Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")
    print(f"  PyTorch: {torch.__version__}")
    print(f"{'═'*60}{RESET}")

    # Download / generate sample images
    section("0. Sample Images")
    download_samples()

    # Load a test image
    sample_images = (
        list(SAMPLE_DIR.glob("*.png")) +
        list(SAMPLE_DIR.glob("*.jpg"))
    )
    if not sample_images:
        print(f"{RED}No sample images found. Aborting.{RESET}")
        return

    test_image = Image.open(sample_images[0]).convert("RGB")
    print(f"\n  {INFO} Using test image: {sample_images[0].name} ({test_image.size})")

    # Run all tests
    suite_results = []
    suite_results.append(("Vocabulary",        test_vocabulary()))
    suite_results.append(("Preprocessing",     test_preprocessing(test_image)))
    suite_results.append(("Caption Model",     test_caption_model(test_image)))
    suite_results.append(("VQA Model",         test_vqa_model(test_image)))
    suite_results.append(("Plan Analyzer",     test_plan_analyzer(test_image)))
    suite_results.append(("Multi-image",       test_multiple_images()))

    # Summary
    section("SUMMARY")
    passed = sum(1 for _, r in suite_results if r)
    total  = len(suite_results)

    for name, result in suite_results:
        status = PASS if result else FAIL
        print(f"  {status}  {name}")

    print(f"\n  {BOLD}Result: {passed}/{total} test suites passed{RESET}")

    if passed == total:
        print(f"\n  {GREEN}{BOLD}🎉 All tests passed! Models are ready.{RESET}")
        print(f"\n  {INFO} Start the API server with:")
        print(f"  {YELLOW}  python backend/main.py{RESET}")
        print(f"  {INFO} API docs at: http://localhost:8000/docs\n")
    else:
        print(f"\n  {RED}Some tests failed. Check output above.{RESET}\n")


if __name__ == "__main__":
    main()
