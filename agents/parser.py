import re
from typing import Any, Dict

import orjson

from agents.base import BaseAgent
from agents.parser_schema import ParserOutput
from core.telemetry import trace_event
from llm.router import LLMRouter


class ParserAgent(BaseAgent):
    name = "parser"

    def __init__(self) -> None:
        self.llm_router = LLMRouter()

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _build_prompt(text: str) -> str:
        return (
            "你是医学报告结构化抽取器，仅输出JSON。"
            "字段必须匹配以下结构："
            "{parsed_report:{schema_version,language,report_type,source_text,biomarkers:[{name,value,unit,abnormal_flag,reference_range,raw_snippet,confidence,valid,errors}],notes,extraction_confidence,ocr_noise,invalid_fields},"
            "parser_notes,parser_confidence,parser_errors}."
            "不允许输出额外字段，不允许解释。"
            "若某字段无效，设valid=false并填写errors。"
            "报告文本：" + text
        )

    def _parse_llm_output(self, raw: str, source_text: str) -> ParserOutput:
        try:
            payload = orjson.loads(raw)
            if "parsed_report" in payload:
                payload["parsed_report"]["source_text"] = source_text
            return ParserOutput.model_validate(payload)
        except Exception as exc:  # noqa: BLE001
            trace_event("parser:invalid_output", {"error": str(exc)})
            fallback = {
                "parsed_report": {
                    "schema_version": "v1",
                    "language": "unknown",
                    "report_type": None,
                    "source_text": source_text,
                    "biomarkers": [],
                    "notes": [],
                    "extraction_confidence": 0.0,
                    "ocr_noise": True,
                    "invalid_fields": ["llm_output"],
                },
                "parser_notes": "解析失败，已回退为空结果。",
                "parser_confidence": 0.0,
                "parser_errors": [str(exc)],
            }
            return ParserOutput.model_validate(fallback)

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        normalized = self._normalize_text(report_text)
        prompt = self._build_prompt(normalized)
        try:
            response = self.llm_router.generate(prompt)
            raw_output = response.get("response", "")
            parsed = self._parse_llm_output(raw_output, normalized)
        except Exception as exc:  # noqa: BLE001
            trace_event("parser:failed", {"error": str(exc)})
            parsed = self._parse_llm_output("{}", normalized)

        trace_event("parser:completed", {"confidence": parsed.parser_confidence})
        return parsed.model_dump()
