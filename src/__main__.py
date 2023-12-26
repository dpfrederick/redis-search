import os
import struct
from datetime import datetime
from typing import List

import redis
from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import MarkdownHeaderTextSplitter

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


def initialize_redis_search_index(
    redis_client: redis.Redis, index_name: str, vector_field: str, dim: int
):
    """
    Initialize a RedisSearch index with a vector field.

    :param redis_client: The Redis client connected to your Redis instance.
    :param index_name: The name of the index to create.
    :param vector_field: The name of the vector field for embeddings.
    :param dim: The dimension of the vectors (embeddings).
    """
    try:
        redis_client.execute_command(
            "FT.CREATE",
            index_name,
            "ON",
            "HASH",
            "SCHEMA",
            "page_content",
            "TEXT",
            vector_field,
            "VECTOR",
            "FLAT",
            "DIM",
            dim,
            "TYPE",
            "FLOAT32",
            "DISTANCE",
            "COSINE",
        )
        print(f"Index '{index_name}' created successfully.")
    except Exception as e:
        print(f"Error creating index: {e}")


# def store_source_documents_in_redis(
#     source_documents: List[SourceDocument],
#     redis_client: redis.Redis,
#     embedding_field: str,
# ):
#     for document in source_documents:
#         # Generate the embedding
#         embedding = embeddings_model.embed_query(document.document.page_content)

#         # Convert the embedding to a binary format
#         binary_embedding = struct.pack(f"{len(embedding)}f", *embedding)

#         # Use HSET to store both the document content and its embedding
#         redis_client.hset(
#             f"{document.source.id}:{document.id}",
#             mapping={
#                 "page_content": document.document.page_content,
#                 embedding_field: binary_embedding,
#             },
#         )


def store_source_documents_in_redis(
    source_documents: List[SourceDocument], redis_client: redis.Redis
):
    for document in source_documents:
        embedding = embeddings_model.embed_query(document.document.page_content)
        redis_client.set(
            f"{document.source.id}:{document.id}:page_content",
            document.document.page_content,
        )
        redis_client.set(
            f"{document.source.id}:{document.id}:embedding",
            embedding,
        )


def main():
    load_dotenv(".env")

    redis_client = redis.Redis(
        host="localhost",
        port=6379,
        db=0,
        password=os.environ.get("REDIS_PASSWORD"),
    )
    redis_client.flushdb()
    initialize_redis_search_index(redis_client, "my_index", "embedding", 1536)

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

        store_source_documents_in_redis(source_documents, redis_client, "embedding")


if __name__ == "__main__":
    main()
