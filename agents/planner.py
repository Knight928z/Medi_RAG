from typing import Any, Dict

from agents.base import BaseAgent


class PlannerAgent(BaseAgent):
    name = "planner"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "route": [
                "parser",
                "retriever",
                "reasoning",
                "validator",
                "critic",
                "synthesis",
                "memory",
            ],
            "intent": "interpret_report",
            "planner_notes": "占位: 之后接入意图分类与任务拆分。",
        }
