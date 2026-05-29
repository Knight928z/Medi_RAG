from fastapi import APIRouter, Depends, HTTPException

from apps.api.dependencies import get_db_session, get_redis_client
from cache.redis_client import get_json
from storage.repositories.workflow_repo import WorkflowRepository

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/{request_id}")
def get_workflow_status(
    request_id: str,
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> dict:
    try:
        cached = get_json(redis_client, f"workflow:{request_id}")
    except Exception:
        cached = None
    if cached is not None:
        return {"request_id": request_id, "status": "cached", "state": cached}

    repo = WorkflowRepository(db_session)
    run = repo.get_by_request_id(request_id)
    if run is None:
        raise HTTPException(status_code=404, detail="未找到对应的工作流记录")
    return {
        "request_id": request_id,
        "status": run.status,
        "state": run.state_snapshot,
    }
