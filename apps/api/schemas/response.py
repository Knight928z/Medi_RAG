from typing import Any, Dict, Optional

from pydantic import BaseModel


class ReportInterpretResponse(BaseModel):
    request_id: str
    status: str
    result: Optional[Dict[str, Any]]
    detail: Optional[str] = None
