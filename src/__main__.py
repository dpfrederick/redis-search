import os
from datetime import datetime
from typing import List

import redis
from langchain.docstore.document import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter

from .types import Source, SourceDocument, Team


def create_source_documents_from_markdown_file(
    file_path: str, filename: str
) -> List[SourceDocument]:
    """Read a Markdown file and return source documents."""
    team = Team(id="foo", title="Foo", url="https://google.com")
    source = Source(
        team=team,
        title=filename,
        path=file_path,
        last_updated=datetime.now(),
        url="https://google.com",
        file_type="md",
    )
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
        headers_to_split_on = [("#", "Header")]
        markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
        documents = markdown_splitter.split_text(content)

    return [SourceDocument(document=doc, source=source) for doc in documents]


def main():
    redis_client = redis.Redis(host="localhost", port=6379, db=0, password="foobar")
    redis_client.flushdb()

    sources = []

    for root, dirs, files in os.walk(
        "/Users/dpfrederick/code/ai-consortium/redis-search/inputs"
    ):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                sources.append(file_path)
                source_documents = create_source_documents_from_markdown_file(
                    file_path, file
                )

                for document in source_documents:
                    # Key: File path + Section title, Value: Section content
                    # redis_client.set(f"{file_path}:{section['title']}", section["content"])
                    print(f"Setting {document.source.path}:{document.source.title}")


if __name__ == "__main__":
    main()
