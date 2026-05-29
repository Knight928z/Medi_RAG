from __future__ import annotations

from typing import Any, Dict, List

from evaluation.schemas import CritiqueOutput, EvaluationIssue, EvaluationScore


class ReasoningCritic:
    def critique(self, state: Dict[str, Any]) -> CritiqueOutput:
        reasoning = state.get("reasoning") or {}
        validation = state.get("validation") or {}
        validation_score = state.get("validation_score") or {}
        validation_issues = state.get("validation_issues") or []
        retrieval_results = state.get("retrieval_results") or []
        memory_context = state.get("memory_context") or []
        issues: List[EvaluationIssue] = []

        self._review_reasoning_chain(reasoning, issues)
        self._review_evidence(validation_score, validation_issues, retrieval_results, issues)
        self._review_context(reasoning, retrieval_results, memory_context, issues)

        score = self._score(issues, validation_score)
        regeneration_required = (
            score.overall < 0.72
            or any(issue.severity in {"critical", "error"} for issue in issues)
            or not validation.get("schema_ok", True)
        )
        retry_target = "reasoning" if regeneration_required else None
        critique = {
            "reasoning_chain_ok": score.logical_consistency >= 0.75,
            "evidence_sufficient": score.evidence_strength >= 0.7,
            "missing_context_detected": any(issue.code == "missing_context" for issue in issues),
            "weak_evidence": [
                issue.model_dump()
                for issue in issues
                if issue.code in {"weak_evidence", "validation_failed"}
            ],
            "regeneration_required": regeneration_required,
            "retry_target": retry_target,
        }
        notes = "Critic 通过。" if not regeneration_required else "Critic 要求基于问题原因重写 reasoning。"
        return CritiqueOutput(
            critique=critique,
            critique_score=score,
            critique_issues=issues,
            regeneration_required=regeneration_required,
            retry_target=retry_target,
            critic_notes=notes,
        )

    @staticmethod
    def _review_reasoning_chain(
        reasoning: Dict[str, Any],
        issues: List[EvaluationIssue],
    ) -> None:
        summary = reasoning.get("summary")
        findings = reasoning.get("findings") or []
        if not summary:
            issues.append(
                EvaluationIssue(
                    code="missing_reasoning_summary",
                    severity="error",
                    reason="reasoning.summary 为空，无法做最终综合。",
                    suggested_action="重新生成 reasoning.summary。",
                )
            )
        if summary and not findings:
            issues.append(
                EvaluationIssue(
                    code="thin_reasoning_chain",
                    severity="warning",
                    reason="存在 summary 但缺少 findings，推理链过薄。",
                    suggested_action="补充分条证据与引用。",
                )
            )
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                issues.append(
                    EvaluationIssue(
                        code="invalid_reasoning_finding",
                        severity="warning",
                        reason=f"第 {index} 条 finding 不是结构化对象。",
                        evidence={"finding_index": index},
                    )
                )

    @staticmethod
    def _review_evidence(
        validation_score: Dict[str, Any],
        validation_issues: List[Dict[str, Any]],
        retrieval_results: List[Dict[str, Any]],
        issues: List[EvaluationIssue],
    ) -> None:
        if validation_score.get("citation_support", 1.0) < 0.7:
            issues.append(
                EvaluationIssue(
                    code="weak_evidence",
                    severity="error",
                    reason="引用支持分低于 0.7。",
                    evidence={"citation_support": validation_score.get("citation_support")},
                    suggested_action="要求 ReasoningAgent 使用有效 citation 重写。",
                )
            )
        if validation_score.get("hallucination_risk", 0.0) > 0.35:
            issues.append(
                EvaluationIssue(
                    code="validation_failed",
                    severity="error",
                    reason="Validator 检测到较高幻觉或无依据陈述风险。",
                    evidence={"hallucination_risk": validation_score.get("hallucination_risk")},
                )
            )
        if not retrieval_results:
            issues.append(
                EvaluationIssue(
                    code="weak_evidence",
                    severity="warning",
                    reason="retrieval_results 为空，无法进行引用交叉验证。",
                    suggested_action="重新检索或将最终综合标记为证据不足。",
                )
            )
        for issue in validation_issues:
            severity = issue.get("severity", "warning")
            if severity in {"error", "critical"}:
                issues.append(
                    EvaluationIssue(
                        code="validation_issue_escalated",
                        severity=severity,
                        reason=f"Validator 问题升级: {issue.get('reason')}",
                        evidence=issue,
                    )
                )

    @staticmethod
    def _review_context(
        reasoning: Dict[str, Any],
        retrieval_results: List[Dict[str, Any]],
        memory_context: List[Dict[str, Any]],
        issues: List[EvaluationIssue],
    ) -> None:
        if not retrieval_results and not memory_context and reasoning.get("summary"):
            issues.append(
                EvaluationIssue(
                    code="missing_context",
                    severity="warning",
                    reason="存在 reasoning.summary，但没有检索证据或历史记忆上下文。",
                    suggested_action="触发检索、记忆查询或降低输出确定性。",
                )
            )

    @staticmethod
    def _score(
        issues: List[EvaluationIssue],
        validation_score: Dict[str, Any],
    ) -> EvaluationScore:
        severity_penalty = {
            "critical": 0.35,
            "error": 0.25,
            "warning": 0.10,
            "info": 0.03,
        }
        penalty = min(
            0.9,
            sum(severity_penalty.get(issue.severity, 0.05) for issue in issues),
        )
        citation_support = float(validation_score.get("citation_support", 1.0))
        logical_consistency = float(validation_score.get("logical_consistency", 1.0))
        schema_validity = float(validation_score.get("schema_validity", 1.0))
        evidence_strength = float(validation_score.get("evidence_strength", 0.6))
        hallucination_risk = max(
            float(validation_score.get("hallucination_risk", 0.0)),
            penalty,
        )
        return EvaluationScore(
            hallucination_risk=min(1.0, hallucination_risk),
            citation_support=max(0.0, citation_support - penalty / 2),
            logical_consistency=max(0.0, logical_consistency - penalty / 2),
            schema_validity=schema_validity,
            evidence_strength=max(0.0, evidence_strength - penalty / 2),
            overall=max(0.0, 1.0 - penalty),
        )
