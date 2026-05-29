from typing import Any, Dict, Optional

from core.config import get_settings
from llm.ollama_client import OllamaClient
from llm.vllm_client import VLLMClient


class LLMRouter:
    def __init__(self):
        settings = get_settings()
        self.provider = settings.llm_provider
        self.ollama = OllamaClient(settings.ollama_base_url)
        self.vllm = VLLMClient(settings.vllm_base_url)
        self.default_model = settings.default_llm_model

    def generate(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        selected_model = model or self.default_model
        if self.provider == "vllm":
            return self.vllm.generate(selected_model, prompt)
        return self.ollama.generate(selected_model, prompt)
