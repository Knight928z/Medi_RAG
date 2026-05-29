from fastapi import APIRouter, Depends

from apps.api.dependencies import get_db_session, get_redis_client
from core.config import get_settings
from sqlalchemy import text
import httpx

router = APIRouter()


@router.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@router.get("/health/db")
async def health_db(db_session=Depends(get_db_session)) -> dict:
    await db_session.execute(text("SELECT 1"))
    return {"status": "ok", "component": "database"}


@router.get("/health/redis")
async def health_redis(redis_client=Depends(get_redis_client)) -> dict:
    redis_client.ping()
    return {"status": "ok", "component": "redis"}


@router.get("/health/ollama")
async def health_ollama() -> dict:
    settings = get_settings()
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(f"{settings.ollama_base_url}/api/tags")
        response.raise_for_status()
    return {"status": "ok", "component": "ollama"}
