from dataclasses import dataclass
from typing import Final, final

from langchain.docstore.document import Document

from .source import Source


@dataclass
@final
class SourceDocument:
    document: Final[Document]
    source: Final[Source]

    @property
    def id(self) -> int:
        return hash(self.document.page_content)
