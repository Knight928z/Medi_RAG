import uuid

from fastapi import APIRouter

from apps.api.schemas.request import ReportInterpretRequest
from apps.api.schemas.response import ReportInterpretResponse

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/interpret", response_model=ReportInterpretResponse)
def interpret_report(payload: ReportInterpretRequest) -> ReportInterpretResponse:
    request_id = str(uuid.uuid4())
    return ReportInterpretResponse(
        request_id=request_id,
        status="pending",
        result=None,
        detail="工作流尚未接入，此处返回占位响应。",
    )
