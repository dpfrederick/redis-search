import json
import os
from datetime import datetime
from typing import List

import numpy as np
import redis
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter
from redis.commands.search.field import VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from .types import Source, SourceDocument, Team

embeddings_model = OpenAIEmbeddings(openai_api_key=os.environ.get("OPENAI_API_KEY"))


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


def initialize_redis_search_index(redis_client: redis.Redis, dim: int) -> None:
    schema = [
        VectorField(
            "$.embedding",
            "FLAT",
            {
                "TYPE": "FLOAT32",
                "DIM": dim,
                "DISTANCE_METRIC": "COSINE",
            },
            as_name="vector",
        ),
    ]

    definition = IndexDefinition(prefix=["documents:"], index_type=IndexType.JSON)

    res = redis_client.ft("idx:documents_vss").create_index(
        fields=schema, definition=definition
    )


def check_redis_search_index(redis_client: redis.Redis) -> None:
    info = redis_client.ft("idx:documents_vss").info()
    num_docs = info["num_docs"]
    indexing_failures = info["hash_indexing_failures"]
    print(f"{num_docs} documents indexed with {indexing_failures} failures.")


def store_source_documents_in_redis(
    source_documents: List[SourceDocument], redis_client: redis.Redis
) -> None:
    pipeline = redis_client.pipeline()
    for document in source_documents:
        redis_key = f"documents:{document.source.id}:{document.id}"
        document_json = json.loads(document.json())
        document_json["embedding"] = embeddings_model.embed_query(
            document.document.page_content
        )
        pipeline.json().set(
            redis_key,
            "$",
            document_json,
        )
    res = pipeline.execute()


def main():
    load_dotenv(".env")

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password=os.environ.get("REDIS_PASSWORD"),
    )
    redis_client.flushdb()
    initialize_redis_search_index(redis_client, 1536)

    sources: List[Source] = []
    source_documents: List[SourceDocument] = []

    for root, dirs, files in os.walk(os.environ.get("INPUT_FILES_DIRECTORY")):
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

        check_redis_search_index(redis_client)

        input_text = "Redis is a key-value in-memory data structure store."
        query_embedding = embeddings_model.embed_query(input_text)

        query = (
            Query("(*)=>[KNN 3 @vector $query_vector AS vector_score]")
            .sort_by("vector_score")
            .return_fields("vector_score", "document")
            .dialect(2)
        )

        result_docs = (
            redis_client.ft("idx:documents_vss")
            .search(
                query,
                {"query_vector": np.array(query_embedding, dtype=np.float32).tobytes()},
            )
            .docs
        )

        print(result_docs)


if __name__ == "__main__":
    main()
