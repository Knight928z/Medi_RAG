from workflows.state import WorkflowState


def test_state_serialization():
    state = WorkflowState(request_id="req-1", report_text="test")
    payload = state.model_dump()
    assert payload["request_id"] == "req-1"
