from typing import Optional

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_db_session
from memory.service import normalize_user_id
from storage.repositories.validation_repo import ValidationHistoryRepository

router = APIRouter(prefix="/evaluation", tags=["evaluation"])


@router.get("/validation-history/{request_id}")
async def get_validation_history(
    request_id: str,
    db_session=Depends(get_db_session),
) -> dict:
    repo = ValidationHistoryRepository(db_session)
    entries = await repo.list_by_request_id(request_id)
    return {"items": [_serialize(entry) for entry in entries]}


@router.get("/dashboard")
async def evaluation_dashboard(
    user_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db_session=Depends(get_db_session),
) -> dict:
    repo = ValidationHistoryRepository(db_session)
    entries = await repo.list_for_dashboard(
        user_id=normalize_user_id(user_id),
        patient_id=patient_id,
        limit=limit,
    )
    serialized = [_serialize(entry) for entry in entries]
    failures = [item for item in serialized if not item["passed"]]
    return {
        "items": serialized,
        "summary": {
            "total": len(serialized),
            "failed": len(failures),
            "failure_rate": len(failures) / len(serialized) if serialized else 0.0,
        },
    }


def _serialize(entry) -> dict:
    return {
        "id": str(entry.id),
        "workflow_run_id": str(entry.workflow_run_id) if entry.workflow_run_id else None,
        "request_id": entry.request_id,
        "user_id": str(entry.user_id) if entry.user_id else None,
        "patient_id": entry.patient_id,
        "stage": entry.stage,
        "passed": entry.passed,
        "score": entry.score,
        "issues": entry.issues,
        "output_payload": entry.output_payload,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
    }
