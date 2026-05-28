from typing import Optional

from storage.models import WorkflowRun


class WorkflowRepository:
    def __init__(self, session):
        self.session = session

    def create(self, run: WorkflowRun) -> WorkflowRun:
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def get_by_request_id(self, request_id: str) -> Optional[WorkflowRun]:
        return (
            self.session.query(WorkflowRun)
            .filter(WorkflowRun.request_id == request_id)
            .one_or_none()
        )
