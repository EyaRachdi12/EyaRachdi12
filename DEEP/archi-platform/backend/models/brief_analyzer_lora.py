"""
LoRA Brief Analyzer - Inference wrapper for fine-tuned Phi-3 model
===================================================================

This module provides a simple interface to analyze architectural briefs
using the fine-tuned LoRA model.

Usage:
    analyzer = BriefAnalyzerLoRA()
    result = analyzer.analyze("Maison moderne 120m², 3 chambres, budget 400k€")
"""

import json
import torch
from pathlib import Path
from typing import Dict, Optional
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel


class BriefAnalyzerLoRA:
    """
    Wrapper class for the fine-tuned LoRA model.
    Handles model loading, inference, and JSON extraction.
    """
    
    def __init__(
        self,
        base_model_name: str = "microsoft/Phi-3-mini-4k-instruct",
        lora_path: Optional[str] = None,
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        """
        Initialize the analyzer.
        
        Args:
            base_model_name: HuggingFace model ID for base model
            lora_path: Path to LoRA adapters (if None, uses ./models/phi3-brief-lora)
            device: Device to run inference on
        """
        self.device = device
        self.base_model_name = base_model_name
        
        # Default LoRA path (try both names for compatibility)
        if lora_path is None:
            # Try mistral-brief-lora first (actual saved name), then phi3-brief-lora
            mistral_path = Path(__file__).parent / "mistral-brief-lora"
            phi3_path = Path(__file__).parent / "phi3-brief-lora"
            
            if mistral_path.exists():
                lora_path = str(mistral_path)
            elif phi3_path.exists():
                lora_path = str(phi3_path)
            else:
                # Default to mistral-brief-lora (will show proper error message)
                lora_path = str(mistral_path)
        
        self.lora_path = lora_path
        self.model = None
        self.tokenizer = None
        self._loaded = False
        
        print(f"[BriefAnalyzerLoRA] Initialized")
        print(f"  Base model: {base_model_name}")
        print(f"  LoRA path: {lora_path}")
        print(f"  Device: {device}")
    
    def load(self):
        """Load the model and tokenizer (lazy loading)"""
        if self._loaded:
            return
        
        print(f"[BriefAnalyzerLoRA] Loading model...")
        
        try:
            # Check if LoRA adapters exist
            lora_path = Path(self.lora_path)
            if not lora_path.exists():
                raise FileNotFoundError(
                    f"LoRA adapters not found at {lora_path}. "
                    f"Please train the model first or download the adapters."
                )
            
            # Load base model
            print(f"  Loading base model: {self.base_model_name}")
            base_model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map=self.device,
                trust_remote_code=True,
            )
            
            # Load LoRA adapters
            print(f"  Loading LoRA adapters from: {self.lora_path}")
            self.model = PeftModel.from_pretrained(
                base_model,
                self.lora_path,
                device_map=self.device,
            )
            
            # Load tokenizer
            print(f"  Loading tokenizer")
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.lora_path,
                trust_remote_code=True
            )
            
            # Set model to eval mode
            self.model.eval()
            self._loaded = True
            
            print(f"[BriefAnalyzerLoRA] Model loaded successfully!")
            
        except Exception as e:
            print(f"[BriefAnalyzerLoRA] Error loading model: {e}")
            raise
    
    def analyze(
        self,
        brief_text: str,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> Dict:
        """
        Analyze an architectural brief and extract structured data.
        
        Args:
            brief_text: Natural language description of the project
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 = deterministic)
            top_p: Nucleus sampling parameter
        
        Returns:
            Dictionary with extracted information:
            {
                "surface_souhaitee": "120-140 m²",
                "budget": "350000-450000",
                "style": "Contemporain",
                "pieces_souhaitees": [...]
            }
        """
        # Lazy load model
        if not self._loaded:
            self.load()
        
        # Format prompt
        prompt = self._format_prompt(brief_text)
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=temperature > 0,
                top_p=top_p,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract JSON
        result = self._extract_json(response)
        
        return result
    
    def _format_prompt(self, brief_text: str) -> str:
        """Format the input text as a prompt for the model"""
        return f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|>

Tu es un expert en architecture spécialisé dans l'analyse de briefs clients. Tu dois extraire et structurer les informations en JSON.<|eot_id|><|start_header_id|>user<|end_header_id|>

Analyse ce brief client et génère une structure JSON détaillée avec la surface souhaitée, le budget, le style architectural et les pièces souhaitées.

Brief: {brief_text}<|eot_id|><|start_header_id|>assistant<|end_header_id|>

"""
    
    def _extract_json(self, response: str) -> Dict:
        """
        Extract JSON from model response.
        Handles various formats and edge cases.
        """
        try:
            # Try to find JSON in response
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            
            if json_start == -1 or json_end == 0:
                # No JSON found, return error
                return {
                    "error": "No JSON found in response",
                    "raw_response": response
                }
            
            json_str = response[json_start:json_end]
            result = json.loads(json_str)
            
            # Validate structure
            if not isinstance(result, dict):
                return {
                    "error": "Invalid JSON structure",
                    "raw_response": response
                }
            
            return result
            
        except json.JSONDecodeError as e:
            return {
                "error": f"JSON decode error: {str(e)}",
                "raw_response": response
            }
        except Exception as e:
            return {
                "error": f"Unexpected error: {str(e)}",
                "raw_response": response
            }
    
    def unload(self):
        """Unload model from memory"""
        if self._loaded:
            del self.model
            del self.tokenizer
            if self.device == "cuda":
                torch.cuda.empty_cache()
            self._loaded = False
            print("[BriefAnalyzerLoRA] Model unloaded")


# Singleton instance for reuse across requests
_analyzer_instance: Optional[BriefAnalyzerLoRA] = None


def get_analyzer() -> BriefAnalyzerLoRA:
    """
    Get or create the singleton analyzer instance.
    This avoids reloading the model for every request.
    """
    global _analyzer_instance
    
    if _analyzer_instance is None:
        _analyzer_instance = BriefAnalyzerLoRA()
        # Lazy load on first use
    
    return _analyzer_instance


# Example usage
if __name__ == "__main__":
    # Test the analyzer
    analyzer = BriefAnalyzerLoRA()
    
    test_briefs = [
        "Maison moderne 120m² pour famille de 4, 3 chambres, budget 400k€",
        "Petite maison 80m² pour couple, 2 chambres, budget 250k€, style moderne",
        "Villa luxe 200m², 5 chambres, piscine, style contemporain, budget 800k€"
    ]
    
    for brief in test_briefs:
        print(f"\n{'='*80}")
        print(f"Brief: {brief}")
        print(f"{'='*80}")
        
        result = analyzer.analyze(brief)
        print(json.dumps(result, ensure_ascii=False, indent=2))
