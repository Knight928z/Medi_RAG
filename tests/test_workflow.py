from workflows.graph import build_workflow
from workflows.state import WorkflowState


def test_state_serialization():
    state = WorkflowState(request_id="req-1", report_text="test")
    payload = state.model_dump()
    assert payload["request_id"] == "req-1"


def test_workflow_runs():
    workflow = build_workflow()
    state = WorkflowState(request_id="req-2", report_text="血常规正常")
    result = workflow.invoke(state)
    payload = result.model_dump() if hasattr(result, "model_dump") else result
    assert payload["intent"] == "interpret_report"
