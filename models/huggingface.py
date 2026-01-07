import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from models.base import BaseModel

class HuggingFaceModel(BaseModel):
    def __init__(self, model_id: str):
        self.model_id = model_id
        
        # 4-bit configuration to save memory
        quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4"
        )
        
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            quantization_config=quant_config,
            device_map="auto",
            trust_remote_code=True
        )

    def generate(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        outputs = self.model.generate(
            **inputs, 
            max_new_tokens=512, 
            temperature=0.7, 
            do_sample=True
        )
        # Decode and remove the initial prompt from the output
        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return full_text[len(prompt):].strip()