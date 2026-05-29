from typing import List

from storage.models import Document


class DocumentRepository:
    def __init__(self, session):
        self.session = session

    def bulk_create(self, documents: List[Document]) -> None:
        self.session.add_all(documents)
        self.session.commit()
