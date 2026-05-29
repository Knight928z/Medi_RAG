from datetime import datetime
from typing import Any, Dict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from core.telemetry import trace_event
from workflows.nodes import build_nodes
from workflows.state import WorkflowState


def _run_agent(agent_name: str, state: WorkflowState) -> Dict[str, Any]:
    agents = build_nodes()
    agent = agents[agent_name]
    payload = state.model_dump()
    retry_counts = dict(state.retry_counts)
    errors = list(state.errors)
    attempts = 0
    max_retries = state.max_retries
    output: Dict[str, Any] = {}
    checkpoint_ref = state.checkpoint_ref or state.request_id

    while True:
        try:
            output = agent.run(payload)
            break
        except Exception as exc:  # noqa: BLE001 - 需要捕获并记录
            attempts += 1
            retry_counts[agent_name] = attempts
            error_message = f"{agent_name}_failed:{exc}"
            errors.append(error_message)
            trace_event(
                f"agent:{agent_name}:error",
                {"attempt": attempts, "error": error_message},
            )
            if attempts > max_retries:
                return {
                    "status": "failed",
                    "current_agent": agent_name,
                    "errors": errors,
                    "retry_counts": retry_counts,
                    "last_error": str(exc),
                }

    event = {
        "agent": agent_name,
        "timestamp": datetime.utcnow().isoformat(),
        "output": output,
    }
    trace_event(
        f"agent:{agent_name}",
        {"input": payload, "output": output, "attempts": attempts},
    )
    current_trace = list(state.trace)
    if agent_name in state.route:
        next_index = state.route.index(agent_name) + 1
    else:
        next_index = state.current_step_index
    next_status = output.get("status") or (
        "completed" if state.route and next_index >= len(state.route) else "running"
    )
    return {
        "trace": current_trace + [event],
        "current_agent": agent_name,
        "current_step_index": next_index,
        "retry_counts": retry_counts,
        "errors": errors,
        "status": next_status,
        "checkpoint_ref": checkpoint_ref,
        **output,
    }


def _route_next(state: WorkflowState) -> str:
    if state.status == "failed":
        return END
    if (
        state.current_agent == "critic"
        and state.reflection_retry_requested
        and state.reflection_iterations <= state.max_reflection_iterations
    ):
        trace_event(
            "router:reflection_retry",
            {
                "target": "reasoning",
                "iteration": state.reflection_iterations,
                "reason": state.reflection_retry_reason,
            },
        )
        return "reasoning"
    if not state.route:
        return END
    if state.current_step_index >= len(state.route):
        return END
    next_agent = state.route[state.current_step_index]
    trace_event("router:next", {"next": next_agent, "step": state.current_step_index})
    return next_agent


def build_workflow():
    graph = StateGraph(WorkflowState)

    graph.add_node("planner", lambda state: _run_agent("planner", state))
    graph.add_node("parser", lambda state: _run_agent("parser", state))
    graph.add_node("retriever", lambda state: _run_agent("retriever", state))
    graph.add_node("reasoning", lambda state: _run_agent("reasoning", state))
    graph.add_node("validator", lambda state: _run_agent("validator", state))
    graph.add_node("critic", lambda state: _run_agent("critic", state))
    graph.add_node("synthesis", lambda state: _run_agent("synthesis", state))
    graph.add_node("memory", lambda state: _run_agent("memory", state))
    graph.add_node("router", lambda state: {})

    graph.set_entry_point("planner")
    graph.add_edge("planner", "router")
    graph.add_edge("parser", "router")
    graph.add_edge("retriever", "router")
    graph.add_edge("reasoning", "router")
    graph.add_edge("validator", "router")
    graph.add_edge("critic", "router")
    graph.add_edge("synthesis", "router")
    graph.add_edge("memory", "router")

    graph.add_conditional_edges(
        "router",
        _route_next,
        {
            "planner": "planner",
            "parser": "parser",
            "retriever": "retriever",
            "reasoning": "reasoning",
            "validator": "validator",
            "critic": "critic",
            "synthesis": "synthesis",
            "memory": "memory",
            END: END,
        },
    )

    checkpointer = MemorySaver()
    return graph.compile(checkpointer=checkpointer)
