import uuid

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_db_session, get_redis_client
from apps.api.schemas.request import ReportInterpretRequest
from apps.api.schemas.response import ReportInterpretResponse
from cache.redis_client import set_json
from core.config import get_settings
from storage.models import WorkflowRun
from storage.repositories.workflow_repo import WorkflowRepository
from workflows.graph import build_workflow
from workflows.state import WorkflowState

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/interpret", response_model=ReportInterpretResponse)
def interpret_report(
    payload: ReportInterpretRequest,
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> ReportInterpretResponse:
    request_id = str(uuid.uuid4())
    workflow = build_workflow()
    initial_state = WorkflowState(
        request_id=request_id,
        report_text=payload.report_text,
        patient_id=payload.patient_id,
    )
    repo = WorkflowRepository(db_session)
    run = repo.create(
        WorkflowRun(
            request_id=request_id,
            state_snapshot=initial_state.model_dump(),
            status="running",
        )
    )
    result_state = workflow.invoke(initial_state)
    result_payload = (
        result_state.model_dump() if hasattr(result_state, "model_dump") else result_state
    )
    try:
        repo.update(run, status="completed", state_snapshot=result_payload)
    except Exception as exc:
        result_payload.setdefault("errors", []).append(f"db_update_failed:{exc}")
    settings = get_settings()
    try:
        set_json(
            redis_client,
            f"workflow:{request_id}",
            result_payload,
            ttl_seconds=settings.workflow_state_ttl_seconds,
        )
    except Exception as exc:
        result_payload.setdefault("errors", []).append(f"redis_cache_failed:{exc}")
    return ReportInterpretResponse(
        request_id=request_id,
        status="completed",
        result=result_payload,
        detail="工作流已同步完成（占位版本）。",
    )
