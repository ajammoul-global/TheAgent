import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer, pipeline
from models.base import BaseModel

class HuggingFaceModel(BaseModel):
    def __init__(self, model_id: str):
        self._model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=False)
        # Load the specialized classification model
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_id,
            device_map="auto",
            torch_dtype=torch.float16,
            trust_remote_code=True
        )
        
        # Initialize a pipeline for easy inference
        self.classifier = pipeline(
            "text-classification", 
            model=self.model, 
            tokenizer=self.tokenizer
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

    def get_info(self) -> dict:
        """Returns metadata about the model for the system logs."""
        return {
            "model_id": self._model_id,
            "device": str(self.model.device),
            "task": "text-classification"
        }
    # ----------------------------------

    def generate(self, prompt: str) -> str:
        """
        Since this is a classifier, 'generate' will return the 
        prediction label (FAKE/REAL) instead of generating new text.
        """
        results = self.classifier(prompt, truncation=True, max_length=512)
        label = results[0]['label']
        score = results[0]['score']
        return f"Analysis: {label} (Confidence: {score:.2f})"