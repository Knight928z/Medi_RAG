from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class WorkflowState(BaseModel):
    request_id: str
    report_text: str
    patient_id: Optional[str] = None
    parsed_report: Optional[Dict[str, Any]] = None
    retrieval_results: List[Dict[str, Any]] = Field(default_factory=list)
    reasoning: Optional[Dict[str, Any]] = None
    validation: Optional[Dict[str, Any]] = None
    memory_context: List[Dict[str, Any]] = Field(default_factory=list)
    route: List[str] = Field(default_factory=list)
    intent: Optional[str] = None
    errors: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {"_id": str}
