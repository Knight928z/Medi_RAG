from fastapi import APIRouter

router = APIRouter(prefix="/workflows", tags=["workflows"])


@router.get("/{run_id}")
def get_workflow_status(run_id: str) -> dict:
    return {"run_id": run_id, "status": "unknown", "detail": "工作流追踪尚未接入。"}
