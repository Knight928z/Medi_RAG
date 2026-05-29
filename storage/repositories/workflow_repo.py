from typing import Optional

from sqlalchemy import select

from storage.models import WorkflowRun


class WorkflowRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, run: WorkflowRun) -> WorkflowRun:
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def get_by_request_id(self, request_id: str) -> Optional[WorkflowRun]:
        result = await self.session.execute(
            select(WorkflowRun).where(WorkflowRun.request_id == request_id)
        )
        return result.scalar_one_or_none()

    async def update(self, run: WorkflowRun, **fields) -> WorkflowRun:
        for key, value in fields.items():
            setattr(run, key, value)
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run
