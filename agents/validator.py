from typing import Any, Dict

from agents.base import BaseAgent


class ValidatorAgent(BaseAgent):
    name = "validator"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "validation": {
                "hallucination": False,
                "consistency": True,
                "citations_ok": False,
            },
            "validator_notes": "占位: 后续接入引用与一致性校验。",
        }
