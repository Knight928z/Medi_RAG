import uuid

from fastapi import APIRouter, Depends

from apps.api.dependencies import get_db_session, get_redis_client
from apps.api.schemas.request import ReportInterpretRequest
from apps.api.schemas.response import ReportInterpretResponse
from cache.redis_client import set_json
from core.config import get_settings
from memory.service import MemoryService, normalize_user_id
from storage.models import Report, ValidationHistory, WorkflowRun
from storage.repositories.report_repo import ReportRepository
from storage.repositories.validation_repo import ValidationHistoryRepository
from storage.repositories.workflow_repo import WorkflowRepository
from workflows.graph import build_workflow
from workflows.state import WorkflowState

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/interpret", response_model=ReportInterpretResponse)
async def interpret_report(
    payload: ReportInterpretRequest,
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> ReportInterpretResponse:
    request_id = str(uuid.uuid4())
    workflow = build_workflow()
    settings = get_settings()
    user_id = payload.user_id or (payload.metadata or {}).get("user_id")
    conversation_id = payload.conversation_id or (payload.metadata or {}).get("conversation_id")
    memory_service = MemoryService(db_session, redis_client)
    memory_payload = {}
    try:
        memory_bundle = await memory_service.retrieve(
            request_id=request_id,
            report_text=payload.report_text,
            user_id=user_id,
            patient_id=payload.patient_id,
        )
        memory_payload = memory_bundle.model_dump()
    except Exception as exc:  # noqa: BLE001
        memory_payload = {
            "memory_context": [],
            "memory_summary": {
                "summary": "记忆检索失败，已跳过历史上下文。",
                "pinned_facts": [],
                "recent_changes": [],
                "item_count": 0,
                "dropped_count": 0,
            },
            "memory_notes": f"memory_retrieval_failed:{exc}",
        }
    initial_state = WorkflowState(
        request_id=request_id,
        report_text=payload.report_text,
        user_id=user_id,
        conversation_id=conversation_id,
        patient_id=payload.patient_id,
        max_reflection_iterations=settings.max_reflection_iterations,
        memory_context=memory_payload.get("memory_context", []),
        memory_summary=memory_payload.get("memory_summary"),
        memory_notes=memory_payload.get("memory_notes"),
    )
    memory_service.store_short_term(request_id, initial_state.model_dump())
    repo = WorkflowRepository(db_session)
    run = await repo.create(
        WorkflowRun(
            request_id=request_id,
            user_id=normalize_user_id(user_id),
            state_snapshot=initial_state.model_dump(),
            status="running",
        )
    )
    result_state = workflow.invoke(
        initial_state,
        config={"configurable": {"thread_id": request_id}},
    )
    result_payload = (
        result_state.model_dump() if hasattr(result_state, "model_dump") else result_state
    )
    try:
        await repo.update(run, status="completed", state_snapshot=result_payload)
    except Exception as exc:
        result_payload.setdefault("errors", []).append(f"db_update_failed:{exc}")
    try:
        set_json(
            redis_client,
            f"workflow:{request_id}",
            result_payload,
            ttl_seconds=settings.workflow_state_ttl_seconds,
        )
    except Exception as exc:
        result_payload.setdefault("errors", []).append(f"redis_cache_failed:{exc}")

    try:
        report_repo = ReportRepository(db_session)
        await report_repo.create(
            Report(
                user_id=normalize_user_id(user_id),
                patient_id=payload.patient_id,
                raw_text=payload.report_text,
                parsed_payload=result_payload.get("parsed_report"),
            )
        )
    except Exception as exc:
        result_payload.setdefault("errors", []).append(f"report_persist_failed:{exc}")
    try:
        await memory_service.persist_workflow_memory(result_payload)
    except Exception as exc:  # noqa: BLE001
        result_payload.setdefault("errors", []).append(f"memory_persist_failed:{exc}")
    try:
        validation_repo = ValidationHistoryRepository(db_session)
        await validation_repo.create_many(
            [
                ValidationHistory(
                    workflow_run_id=run.id,
                    request_id=request_id,
                    user_id=normalize_user_id(user_id),
                    patient_id=payload.patient_id,
                    stage="validator",
                    passed=bool(result_payload.get("validation_passed", False)),
                    score=result_payload.get("validation_score"),
                    issues=result_payload.get("validation_issues", []),
                    output_payload={
                        "validation": result_payload.get("validation"),
                        "validator_notes": result_payload.get("validator_notes"),
                    },
                ),
                ValidationHistory(
                    workflow_run_id=run.id,
                    request_id=request_id,
                    user_id=normalize_user_id(user_id),
                    patient_id=payload.patient_id,
                    stage="critic",
                    passed=not bool(result_payload.get("regeneration_required", False)),
                    score=result_payload.get("critique_score"),
                    issues=result_payload.get("critique_issues", []),
                    output_payload={
                        "critique": result_payload.get("critique"),
                        "critic_notes": result_payload.get("critic_notes"),
                        "reflection_iterations": result_payload.get("reflection_iterations", 0),
                    },
                ),
            ]
        )
    except Exception as exc:  # noqa: BLE001
        result_payload.setdefault("errors", []).append(f"validation_history_failed:{exc}")
    return ReportInterpretResponse(
        request_id=request_id,
        status="completed",
        result=result_payload,
        detail="工作流已同步完成（占位版本）。",
    )
