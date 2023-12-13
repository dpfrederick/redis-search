import os
from datetime import datetime
from typing import List

import redis
from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter

from .types import Source, SourceDocument, Team


def create_source_documents_from_markdown_file(
    file_path: str, source: Source
) -> List[SourceDocument]:
    """Read a Markdown file and return source documents."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        headers_to_split_on = [("#", "Header")]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        documents: List[Document] = markdown_splitter.split_text(content)

    return [SourceDocument(document=doc, source=source) for doc in documents]


def store_source_documents_in_redis(
    source_documents: List[SourceDocument], redis_client: redis.Redis
):
    for document in source_documents:
        redis_client.set(
            f"{document.source.id}:{document.id}", document.document.page_content
        )


def main():
    redis_client = redis.Redis(host="localhost", port=6379, db=0, password="foobar")
    redis_client.flushdb()

    sources: List[Source] = []
    source_documents: List[SourceDocument] = []

    for root, dirs, files in os.walk(
        "/Users/dpfrederick/code/ai-consortium/redis-search/inputs"
    ):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)

                team = Team(id="foo", title="Foo", url="https://google.com")
                source = Source(
                    team=team,
                    title=file,
                    path=file_path,
                    last_updated=datetime.now(),
                    url="https://google.com",
                    file_type="md",
                )

                sources.append(source)
                docs = create_source_documents_from_markdown_file(file_path, source)
                for doc in docs:
                    source_documents.append(doc)

        store_source_documents_in_redis(source_documents, redis_client)


if __name__ == "__main__":
    main()
