from typing import Any, Dict

from agents.base import BaseAgent
from core.telemetry import trace_event
from evaluation.validation import ReasoningValidator


class ValidatorAgent(BaseAgent):
    name = "validator"

    def __init__(self) -> None:
        self.validator = ReasoningValidator()

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        result = self.validator.validate(state)
        trace_event(
            "validator:evaluation",
            {
                "request_id": state.get("request_id"),
                "passed": result.validation_passed,
                "score": result.validation_score.model_dump(),
                "issues": [issue.model_dump() for issue in result.validation_issues],
            },
        )
        return result.model_dump()
