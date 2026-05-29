from __future__ import annotations

from typing import Any, Dict, Iterable, List, Set

from evaluation.schemas import EvaluationIssue, EvaluationScore, ValidationOutput


REQUIRED_PARSED_FIELDS = {
    "schema_version",
    "language",
    "report_type",
    "source_text",
    "biomarkers",
    "extraction_confidence",
    "ocr_noise",
    "invalid_fields",
}

REQUIRED_BIOMARKER_FIELDS = {
    "name",
    "value",
    "unit",
    "abnormal_flag",
    "reference_range",
    "raw_snippet",
    "confidence",
    "valid",
    "errors",
}


def _retrieval_ids(retrieval_results: Iterable[Dict[str, Any]]) -> Set[str]:
    ids: Set[str] = set()
    for item in retrieval_results:
        for key in ("id", "chunk_id", "source"):
            value = item.get(key)
            if value:
                ids.add(str(value))
        citation = item.get("citation") or {}
        for key in ("chunk_id", "source"):
            value = citation.get(key)
            if value:
                ids.add(str(value))
    return ids


class ReasoningValidator:
    def validate(self, state: Dict[str, Any]) -> ValidationOutput:
        parsed_report = state.get("parsed_report") or {}
        reasoning = state.get("reasoning") or {}
        retrieval_results = state.get("retrieval_results") or []
        issues: List[EvaluationIssue] = []

        self._validate_schema(parsed_report, issues)
        self._validate_citations(reasoning, retrieval_results, issues)
        self._validate_consistency(reasoning, issues)
        self._validate_supported_claims(reasoning, retrieval_results, issues)

        score = self._score(issues, retrieval_results, reasoning)
        passed = score.overall >= 0.75 and not any(
            issue.severity in {"critical", "error"} for issue in issues
        )
        validation = {
            "hallucination": score.hallucination_risk > 0.35,
            "citations_ok": score.citation_support >= 0.7,
            "consistency": score.logical_consistency >= 0.7,
            "schema_ok": score.schema_validity >= 0.8,
            "unsupported_claims": [
                issue.model_dump()
                for issue in issues
                if issue.code == "unsupported_claim"
            ],
            "explainability": {
                "checked_retrieval_items": len(retrieval_results),
                "checked_reasoning_findings": len(reasoning.get("findings") or []),
                "issue_count": len(issues),
            },
        }
        notes = "验证通过。" if passed else "验证未通过，详见 validation_issues。"
        return ValidationOutput(
            validation=validation,
            validation_score=score,
            validation_issues=issues,
            validation_passed=passed,
            validator_notes=notes,
        )

    @staticmethod
    def _validate_schema(
        parsed_report: Dict[str, Any],
        issues: List[EvaluationIssue],
    ) -> None:
        missing = REQUIRED_PARSED_FIELDS - set(parsed_report.keys())
        if missing:
            issues.append(
                EvaluationIssue(
                    code="schema_missing_fields",
                    severity="error",
                    reason=f"parsed_report 缺少字段: {', '.join(sorted(missing))}",
                    evidence={"missing_fields": sorted(missing)},
                    suggested_action="回退 ParserAgent 或要求结构化修复。",
                )
            )
        biomarkers = parsed_report.get("biomarkers")
        if biomarkers is None:
            return
        if not isinstance(biomarkers, list):
            issues.append(
                EvaluationIssue(
                    code="schema_invalid_biomarkers",
                    severity="error",
                    reason="parsed_report.biomarkers 必须是数组。",
                    suggested_action="重新解析报告结构。",
                )
            )
            return
        for index, item in enumerate(biomarkers):
            if not isinstance(item, dict):
                issues.append(
                    EvaluationIssue(
                        code="schema_invalid_biomarker_item",
                        severity="error",
                        reason=f"第 {index} 个 biomarker 不是对象。",
                        evidence={"index": index},
                    )
                )
                continue
            missing_item = REQUIRED_BIOMARKER_FIELDS - set(item.keys())
            if missing_item:
                issues.append(
                    EvaluationIssue(
                        code="schema_missing_biomarker_fields",
                        severity="warning",
                        reason=f"第 {index} 个 biomarker 缺少字段: {', '.join(sorted(missing_item))}",
                        evidence={"index": index, "missing_fields": sorted(missing_item)},
                    )
                )

    @staticmethod
    def _validate_citations(
        reasoning: Dict[str, Any],
        retrieval_results: List[Dict[str, Any]],
        issues: List[EvaluationIssue],
    ) -> None:
        findings = reasoning.get("findings") or []
        retrieval_ids = _retrieval_ids(retrieval_results)
        if findings and not retrieval_results:
            issues.append(
                EvaluationIssue(
                    code="missing_retrieval_evidence",
                    severity="error",
                    reason="reasoning.findings 存在，但 retrieval_results 为空。",
                    suggested_action="重新检索或降低结论强度。",
                )
            )
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            citation = finding.get("citation") or finding.get("citations")
            if not citation:
                issues.append(
                    EvaluationIssue(
                        code="missing_citation",
                        severity="warning",
                        reason=f"第 {index} 条 finding 没有 citation。",
                        evidence={"finding_index": index},
                    )
                )
                continue
            citation_values = citation if isinstance(citation, list) else [citation]
            flattened = {str(value) for item in citation_values for value in _flatten_citation(item)}
            if retrieval_ids and flattened and not flattened.intersection(retrieval_ids):
                issues.append(
                    EvaluationIssue(
                        code="citation_not_found",
                        severity="error",
                        reason=f"第 {index} 条 finding 的 citation 未出现在检索结果中。",
                        evidence={
                            "finding_index": index,
                            "citation": citation,
                            "known_ids": sorted(retrieval_ids)[:8],
                        },
                    )
                )

    @staticmethod
    def _validate_consistency(
        reasoning: Dict[str, Any],
        issues: List[EvaluationIssue],
    ) -> None:
        findings = reasoning.get("findings") or []
        summary = str(reasoning.get("summary") or "")
        if summary and not findings:
            issues.append(
                EvaluationIssue(
                    code="summary_without_findings",
                    severity="warning",
                    reason="reasoning.summary 存在，但 findings 为空，解释链不充分。",
                    suggested_action="补充证据条目或降低 summary 细节。",
                )
            )
        seen_claims = set()
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            claim = str(finding.get("claim") or finding.get("summary") or finding.get("text") or "")
            normalized = claim.strip().lower()
            if normalized and normalized in seen_claims:
                issues.append(
                    EvaluationIssue(
                        code="duplicate_finding",
                        severity="info",
                        reason=f"第 {index} 条 finding 与前文重复。",
                        evidence={"finding_index": index},
                    )
                )
            seen_claims.add(normalized)

    @staticmethod
    def _validate_supported_claims(
        reasoning: Dict[str, Any],
        retrieval_results: List[Dict[str, Any]],
        issues: List[EvaluationIssue],
    ) -> None:
        evidence_text = "\n".join(str(item.get("content") or "") for item in retrieval_results)
        findings = reasoning.get("findings") or []
        if not evidence_text and findings:
            return
        for index, finding in enumerate(findings):
            if not isinstance(finding, dict):
                continue
            claim = str(finding.get("claim") or finding.get("summary") or finding.get("text") or "")
            if not claim.strip():
                continue
            tokens = [token for token in claim.replace("，", " ").replace("。", " ").split() if len(token) >= 2]
            if tokens and not any(token in evidence_text for token in tokens[:8]):
                issues.append(
                    EvaluationIssue(
                        code="unsupported_claim",
                        severity="warning",
                        reason=f"第 {index} 条 finding 没有可匹配的检索证据片段。",
                        evidence={"finding_index": index, "claim": claim[:160]},
                        suggested_action="要求 ReasoningAgent 引用检索证据重写。",
                    )
                )

    @staticmethod
    def _score(
        issues: List[EvaluationIssue],
        retrieval_results: List[Dict[str, Any]],
        reasoning: Dict[str, Any],
    ) -> EvaluationScore:
        severity_penalty = {
            "critical": 0.35,
            "error": 0.25,
            "warning": 0.10,
            "info": 0.03,
        }
        total_penalty = min(
            0.9,
            sum(severity_penalty.get(issue.severity, 0.05) for issue in issues),
        )
        schema_penalty = sum(0.2 for issue in issues if issue.code.startswith("schema"))
        citation_penalty = sum(
            0.2
            for issue in issues
            if issue.code in {"missing_citation", "citation_not_found", "missing_retrieval_evidence"}
        )
        unsupported_penalty = sum(0.15 for issue in issues if issue.code == "unsupported_claim")
        consistency_penalty = sum(
            0.12
            for issue in issues
            if issue.code in {"summary_without_findings", "duplicate_finding"}
        )
        findings = reasoning.get("findings") or []
        evidence_strength = 0.4
        if retrieval_results and findings:
            evidence_strength = 0.85
        elif retrieval_results:
            evidence_strength = 0.65
        elif not findings:
            evidence_strength = 0.6
        return EvaluationScore(
            hallucination_risk=min(1.0, total_penalty + unsupported_penalty),
            citation_support=max(0.0, 1.0 - citation_penalty),
            logical_consistency=max(0.0, 1.0 - consistency_penalty),
            schema_validity=max(0.0, 1.0 - schema_penalty),
            evidence_strength=max(0.0, evidence_strength - unsupported_penalty),
            overall=max(0.0, 1.0 - total_penalty),
        )


def _flatten_citation(value: Any) -> List[Any]:
    if isinstance(value, dict):
        flattened: List[Any] = []
        for key in ("id", "chunk_id", "source"):
            if value.get(key):
                flattened.append(value[key])
        return flattened
    return [value]
