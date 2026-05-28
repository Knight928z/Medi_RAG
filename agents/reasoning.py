from typing import Any, Dict

from agents.base import BaseAgent


class ReasoningAgent(BaseAgent):
    name = "reasoning"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "reasoning": {
                "summary": "占位: 后续接入医学推理与长上下文整合。",
                "findings": [],
            },
            "reasoning_notes": "占位: Reasoning Agent 未接入 LLM。",
        }
