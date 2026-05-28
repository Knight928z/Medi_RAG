from typing import Any, Dict

from agents.base import BaseAgent


class ParserAgent(BaseAgent):
    name = "parser"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        report_text = state.get("report_text", "")
        return {
            "parsed_report": {
                "raw": report_text,
                "sections": [],
                "entities": [],
            },
            "parser_notes": "占位: 后续接入医学结构化抽取。",
        }
