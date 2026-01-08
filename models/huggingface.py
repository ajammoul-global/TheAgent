import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from models.base import BaseModel
from typing import Optional, Dict, Any

class HuggingFaceModel(BaseModel):
    def __init__(self, model_id: str):
        self._model_id = model_id
        
        # Force use_fast=False to avoid TokenizersBackend crashes in Kaggle/Colab
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            use_fast=False,
            trust_remote_code=True
        )
        
        # Set padding token if not already set
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load as CausalLM (Llama-based fine-tuned model)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True,
            load_in_8bit=True
        )

    # --- REQUIRED ABSTRACT METHODS ---
    @property
    def name(self) -> str:
        """Returns the name of the model."""
        return self._model_id

    @property
    def provider(self) -> str:
        """Identifies the model provider."""
        return "huggingface"

    def get_info(self) -> Dict[str, Any]:
        """Returns metadata about the model for the system logs."""
        return {
            "model_id": self._model_id,
            "device": str(self.model.device),
            "task": "text-classification"
        }

    def generate(
        self, 
        prompt: str, 
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate a fake news detection verdict using the fine-tuned Causal LM.
        
        Args:
            prompt: The news text to analyze
            temperature: Controls randomness of generation (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 50)
            
        Returns:
            str: The model's verdict (REAL or FAKE)
        """
        # Create prompt template for the model
        prompt_template = f"""Instruction: Analyze the news and provide a verdict (REAL or FAKE).
News: {prompt}
Verdict:"""
        
        # Set default max_tokens if not provided
        if max_tokens is None:
            max_tokens = 50
        
        try:
            # Tokenize input
            inputs = self.tokenizer(
                prompt_template,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )
            
            # Move to same device as model
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
            
            # Generate output
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                do_sample=True if temperature > 0 else False,
                top_p=0.9,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode the generated tokens
            generated_text = self.tokenizer.decode(
                outputs[0],
                skip_special_tokens=True
            )
            
            # Extract only the verdict part (after "Verdict:")
            if "Verdict:" in generated_text:
                verdict = generated_text.split("Verdict:")[-1].strip()
            else:
                verdict = generated_text.strip()
            
            return verdict
            
        except Exception as e:
            return f"Error in generation: {str(e)}"
    # ----------------------------------