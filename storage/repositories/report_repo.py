from typing import Optional

from storage.models import Report


class ReportRepository:
    def __init__(self, session):
        self.session = session

    def create(self, report: Report) -> Report:
        self.session.add(report)
        self.session.commit()
        self.session.refresh(report)
        return report

    def get(self, report_id) -> Optional[Report]:
        return self.session.get(Report, report_id)
