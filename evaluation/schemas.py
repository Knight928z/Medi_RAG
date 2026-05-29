from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class EvaluationIssue(BaseModel):
    code: str
    severity: str = Field(..., description="info/warning/error/critical")
    reason: str
    evidence: Optional[Dict[str, Any]] = None
    suggested_action: Optional[str] = None


class EvaluationScore(BaseModel):
    hallucination_risk: float = Field(0.0, ge=0.0, le=1.0)
    citation_support: float = Field(0.0, ge=0.0, le=1.0)
    logical_consistency: float = Field(0.0, ge=0.0, le=1.0)
    schema_validity: float = Field(0.0, ge=0.0, le=1.0)
    evidence_strength: float = Field(0.0, ge=0.0, le=1.0)
    overall: float = Field(0.0, ge=0.0, le=1.0)


class ValidationOutput(BaseModel):
    validation: Dict[str, Any]
    validation_score: EvaluationScore
    validation_issues: List[EvaluationIssue] = Field(default_factory=list)
    validation_passed: bool = False
    validator_notes: str


class CritiqueOutput(BaseModel):
    critique: Dict[str, Any]
    critique_score: EvaluationScore
    critique_issues: List[EvaluationIssue] = Field(default_factory=list)
    regeneration_required: bool = False
    retry_target: Optional[str] = None
    critic_notes: str
