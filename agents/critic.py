from typing import Any, Dict

from agents.base import BaseAgent
from core.telemetry import trace_event
from evaluation.critic import ReasoningCritic


class CriticAgent(BaseAgent):
    name = "critic"

    def __init__(self) -> None:
        self.critic = ReasoningCritic()

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        result = self.critic.critique(state)
        reflection_iterations = int(state.get("reflection_iterations") or 0)
        max_iterations = int(state.get("max_reflection_iterations") or 1)
        retry_allowed = result.regeneration_required and reflection_iterations < max_iterations
        next_iterations = reflection_iterations + 1 if retry_allowed else reflection_iterations
        trace_event(
            "critic:evaluation",
            {
                "request_id": state.get("request_id"),
                "regeneration_required": result.regeneration_required,
                "retry_allowed": retry_allowed,
                "score": result.critique_score.model_dump(),
                "issues": [issue.model_dump() for issue in result.critique_issues],
            },
        )
        payload = result.model_dump()
        payload.update(
            {
                "reflection_retry_requested": retry_allowed,
                "reflection_iterations": next_iterations,
                "reflection_retry_reason": (
                    "; ".join(issue.reason for issue in result.critique_issues[:3])
                    if retry_allowed
                    else None
                ),
            }
        )
        return payload
