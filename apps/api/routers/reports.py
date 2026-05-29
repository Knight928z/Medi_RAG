import uuid

from fastapi import APIRouter

from apps.api.schemas.request import ReportInterpretRequest
from apps.api.schemas.response import ReportInterpretResponse
from workflows.graph import build_workflow
from workflows.state import WorkflowState

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/interpret", response_model=ReportInterpretResponse)
def interpret_report(payload: ReportInterpretRequest) -> ReportInterpretResponse:
    request_id = str(uuid.uuid4())
    workflow = build_workflow()
    initial_state = WorkflowState(
        request_id=request_id,
        report_text=payload.report_text,
        patient_id=payload.patient_id,
    )
    result_state = workflow.invoke(initial_state)
    result_payload = (
        result_state.model_dump() if hasattr(result_state, "model_dump") else result_state
    )
    return ReportInterpretResponse(
        request_id=request_id,
        status="completed",
        result=result_payload,
        detail="工作流已同步完成（占位版本）。",
    )
