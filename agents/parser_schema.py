from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class BiomarkerResult(BaseModel):
    name: str = Field(..., description="指标名称")
    value: Optional[str] = Field(None, description="指标值（保留原始字符串）")
    unit: Optional[str] = Field(None, description="单位")
    abnormal_flag: Optional[str] = Field(
        None, description="异常标记：H/L/N/UNK"
    )
    reference_range: Optional[str] = Field(None, description="参考范围")
    raw_snippet: Optional[str] = Field(None, description="原始片段")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")
    valid: bool = Field(..., description="字段是否有效")
    errors: List[str] = Field(default_factory=list)


class ParsedReport(BaseModel):
    schema_version: str = "v1"
    language: str = Field("zh", description="报告语言")
    report_type: Optional[str] = Field(None, description="报告类型")
    source_text: str = Field(..., description="原始报告文本")
    biomarkers: List[BiomarkerResult] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)
    extraction_confidence: float = Field(0.0, ge=0.0, le=1.0)
    ocr_noise: bool = False
    invalid_fields: List[str] = Field(default_factory=list)


class ParserOutput(BaseModel):
    parsed_report: ParsedReport
    parser_notes: str
    parser_confidence: float = Field(0.0, ge=0.0, le=1.0)
    parser_errors: List[str] = Field(default_factory=list)
