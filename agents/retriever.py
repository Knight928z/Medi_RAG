from typing import Any, Dict

from agents.base import BaseAgent


class RetrieverAgent(BaseAgent):
    name = "retriever"

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "retrieval_results": [],
            "retriever_notes": "占位: 后续接入 pgvector + BM25 混合检索。",
        }
