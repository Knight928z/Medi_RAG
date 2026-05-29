from typing import Any, Dict

from agents.base import BaseAgent


class SynthesisAgent(BaseAgent):
    name = "synthesis"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        reasoning = state.get("reasoning") or {}
        validation = state.get("validation") or {}
        critique = state.get("critique") or {}
        final_synthesis = {
            "summary": reasoning.get("summary") or "未生成可用推理摘要。",
            "findings": reasoning.get("findings") or [],
            "quality": {
                "validation_passed": state.get("validation_passed", False),
                "validation_score": state.get("validation_score"),
                "critique_score": state.get("critique_score"),
                "regeneration_required": state.get("regeneration_required", False),
                "reflection_iterations": state.get("reflection_iterations", 0),
            },
            "limitations": self._limitations(validation, critique, state),
        }
        return {
            "final_synthesis": final_synthesis,
            "synthesis_notes": "已基于 Reasoning/Validator/Critic 输出生成最终综合。",
            "status": "completed",
        }

    @staticmethod
    def _limitations(
        validation: Dict[str, Any],
        critique: Dict[str, Any],
        state: Dict[str, Any],
    ):
        limitations = []
        if not validation.get("citations_ok", False):
            limitations.append("引用支持不足或无法完全验证。")
        if validation.get("hallucination", False):
            limitations.append("存在无依据陈述风险，需人工复核。")
        if critique.get("missing_context_detected", False):
            limitations.append("Critic 检测到上下文缺失。")
        if state.get("regeneration_required") and not state.get("reflection_retry_requested"):
            limitations.append("已达到自反思重试上限，保留失败原因。")
        return limitations
