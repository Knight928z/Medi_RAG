from typing import Any, Dict, Optional

import httpx


class OllamaClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"model": model, "prompt": prompt, "stream": False}
        if options:
            payload["options"] = options
        response = httpx.post(f"{self.base_url}/api/generate", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
