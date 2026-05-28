from typing import Any, Dict

from agents.base import BaseAgent


class MemoryAgent(BaseAgent):
    name = "memory"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "memory_context": [],
            "memory_notes": "占位: 后续接入长期记忆检索。",
        }
