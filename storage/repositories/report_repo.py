from typing import Optional

from sqlalchemy import select

from storage.models import Report


class ReportRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, report: Report) -> Report:
        self.session.add(report)
        await self.session.commit()
        await self.session.refresh(report)
        return report

    async def get(self, report_id) -> Optional[Report]:
        result = await self.session.execute(select(Report).where(Report.id == report_id))
        return result.scalar_one_or_none()
