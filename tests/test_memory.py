from agents.memory import MemoryAgent
from memory.compression import MemoryCompressor
from memory.schemas import MemoryItem


def test_memory_compression_strips_expansive_fields():
    compressor = MemoryCompressor(max_items=1, max_text_chars=12)
    items = [
        MemoryItem(
            layer="long_term",
            kind="historical_report",
            source="report:1",
            content={
                "source_text": "x" * 100,
                "summary": "白细胞指标历史偏高，需要对照本次报告。",
            },
            summary="白细胞指标历史偏高，需要对照本次报告。",
        ),
        MemoryItem(
            layer="semantic",
            kind="reasoning_trace",
            source="memory:2",
            content={"summary": "second"},
        ),
    ]

    compact, dropped = compressor.compress_items(items)

    assert dropped == 1
    assert len(compact) == 1
    assert "source_text" not in compact[0]["content"]
    assert compact[0]["summary"].endswith("...")


def test_memory_agent_summarizes_existing_context():
    agent = MemoryAgent()
    result = agent.run(
        {
            "memory_context": [
                {
                    "layer": "long_term",
                    "kind": "workflow_summary",
                    "source": "memory:1",
                    "content": {"summary": "历史报告包含血红蛋白异常。"},
                    "summary": "历史报告包含血红蛋白异常。",
                }
            ]
        }
    )

    assert result["memory_context"]
    assert result["memory_summary"]["item_count"] == 1
    assert "血红蛋白" in result["memory_summary"]["summary"]
