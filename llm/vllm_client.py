from typing import Any, Dict, Optional

import httpx


class VLLMClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def generate(self, model: str, prompt: str, options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"model": model, "prompt": prompt}
        if options:
            payload.update(options)
        response = httpx.post(f"{self.base_url}/v1/completions", json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
