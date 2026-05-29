from typing import Optional

from fastapi import APIRouter, Depends, Query

from apps.api.dependencies import get_db_session, get_redis_client
from memory.service import MemoryService

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/context")
async def get_memory_context(
    query: str = Query("", description="当前报告或问题文本"),
    request_id: str = Query("preview", description="当前请求 ID"),
    user_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> dict:
    service = MemoryService(db_session, redis_client)
    bundle = await service.retrieve(
        request_id=request_id,
        report_text=query,
        user_id=user_id,
        patient_id=patient_id,
    )
    return bundle.model_dump()


@router.get("/semantic")
async def semantic_memory_search(
    query: str,
    user_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    top_k: Optional[int] = Query(None, ge=1, le=20),
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> dict:
    service = MemoryService(db_session, redis_client)
    items = await service.semantic_search(
        query=query,
        user_id=user_id,
        patient_id=patient_id,
        top_k=top_k,
    )
    return {"items": [item.model_dump() for item in items]}


@router.get("/workflows")
async def historical_workflows(
    user_id: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db_session=Depends(get_db_session),
    redis_client=Depends(get_redis_client),
) -> dict:
    service = MemoryService(db_session, redis_client)
    items = await service.historical_workflow_lookup(
        user_id=user_id,
        patient_id=patient_id,
        limit=limit,
    )
    return {"items": [item.model_dump() for item in items]}
