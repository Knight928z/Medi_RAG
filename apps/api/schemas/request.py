from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ReportInterpretRequest(BaseModel):
    report_text: str = Field(..., description="原始医疗报告文本")
    user_id: Optional[str] = Field(None, description="用户唯一标识")
    conversation_id: Optional[str] = Field(None, description="会话唯一标识")
    patient_id: Optional[str] = Field(None, description="患者唯一标识")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
