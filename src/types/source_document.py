from langchain.docstore.document import Document
from pydantic.v1 import BaseModel

from .source import Source


class SourceDocument(BaseModel):
    document: Document
    source: Source

    @property
    def id(self) -> int:
        return hash(self.document.page_content)
