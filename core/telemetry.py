import logging
from typing import Any, Dict

logger = logging.getLogger("telemetry")


def trace_event(event: str, payload: Dict[str, Any]) -> None:
    logger.info("%s | payload=%s", event, payload)
