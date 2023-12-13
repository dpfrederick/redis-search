import os
from collections import namedtuple

import redis

Section = namedtuple("Section", ["title", "content"])


def ingest_markdown(file_path):
    """Read a Markdown file and return its content."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def break_into_sections(markdown_content):
    """Break markdown content into sections and return a list of Section objects."""
    sections = []
    lines = markdown_content.split("\n")
    current_title = ""
    current_content = []

    for line in lines:
        if line.startswith("#"):  # Assuming '#' is used for section titles
            if current_content:
                sections.append(Section(current_title, "\n".join(current_content)))
                current_content = []
            current_title = line.strip("# ")
        else:
            current_content.append(line)

    if current_content:  # Add the last section
        sections.append(Section(current_title, "\n".join(current_content)))

    return sections


redis_client = redis.Redis(host="localhost", port=6379, db=0, password="foobar")
redis_client.flushdb()

sources = []

for root, dirs, files in os.walk(
    "/Users/dpfrederick/code/ai-consortium/redis-search/inputs"
):
    for file in files:
        if file.endswith(".md"):
            file_path = os.path.join(root, file)
            sources.append(os.path.join(root, file))
            content = ingest_markdown(file_path)
            sections = break_into_sections(content)

            for section in sections:
                # Key: File path + Section title, Value: Section content
                redis_client.set(f"{file_path}:{section.title}", section.content)

print(f"Found {len(sources)} sources")
