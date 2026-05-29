from datetime import datetime
from typing import Any, Dict

from langgraph.graph import END, StateGraph

from core.telemetry import trace_event
from workflows.nodes import build_nodes
from workflows.state import WorkflowState


def _run_agent(agent_name: str, state: WorkflowState) -> Dict[str, Any]:
    agents = build_nodes()
    agent = agents[agent_name]
    payload = state.model_dump()
    output = agent.run(payload)
    event = {
        "agent": agent_name,
        "timestamp": datetime.utcnow().isoformat(),
        "output": output,
    }
    trace_event(f"agent:{agent_name}", {"input": payload, "output": output})
    current_trace = list(state.trace) if hasattr(state, "trace") else []
    return {"trace": current_trace + [event], **output}


def build_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", lambda state: _run_agent("planner", state))
    graph.add_node("parser", lambda state: _run_agent("parser", state))
    graph.add_node("retriever", lambda state: _run_agent("retriever", state))
    graph.add_node("reasoning", lambda state: _run_agent("reasoning", state))
    graph.add_node("validator", lambda state: _run_agent("validator", state))
    graph.add_node("memory", lambda state: _run_agent("memory", state))

    graph.set_entry_point("planner")
    graph.add_edge("planner", "parser")
    graph.add_edge("parser", "retriever")
    graph.add_edge("retriever", "reasoning")
    graph.add_edge("reasoning", "validator")
    graph.add_edge("validator", "memory")
    graph.add_edge("memory", END)

    return graph.compile()
