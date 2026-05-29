from agents.critic import CriticAgent
from agents.validator import ValidatorAgent


def test_validator_reports_schema_and_citation_reasons():
    agent = ValidatorAgent()
    result = agent.run(
        {
            "parsed_report": {"biomarkers": "bad"},
            "reasoning": {
                "summary": "证据显示白细胞升高。",
                "findings": [{"claim": "白细胞升高", "citation": {"chunk_id": "missing"}}],
            },
            "retrieval_results": [{"chunk_id": "known", "content": "血红蛋白正常"}],
        }
    )

    assert result["validation_passed"] is False
    codes = {issue["code"] for issue in result["validation_issues"]}
    assert "schema_missing_fields" in codes
    assert "schema_invalid_biomarkers" in codes
    assert "citation_not_found" in codes


def test_critic_requests_regeneration_for_weak_evidence():
    agent = CriticAgent()
    result = agent.run(
        {
            "reasoning": {"summary": "存在异常风险。", "findings": []},
            "retrieval_results": [],
            "memory_context": [],
            "validation": {"schema_ok": True},
            "validation_score": {
                "hallucination_risk": 0.5,
                "citation_support": 0.4,
                "logical_consistency": 0.8,
                "schema_validity": 1.0,
                "evidence_strength": 0.3,
                "overall": 0.6,
            },
            "validation_issues": [
                {"code": "missing_citation", "severity": "error", "reason": "缺少引用"}
            ],
            "reflection_iterations": 0,
            "max_reflection_iterations": 1,
        }
    )

    assert result["regeneration_required"] is True
    assert result["reflection_retry_requested"] is True
    assert result["retry_target"] == "reasoning"
    assert result["critique_issues"]
