"""Loads and chunks markdown knowledge-base documents for ingestion."""

from dataclasses import dataclass
from pathlib import Path

from app.config.settings import get_settings


@dataclass
class Chunk:
    id: str
    source: str
    content: str


def _chunk_markdown(text: str, source: str, max_chars: int = 800) -> list[Chunk]:
    """Splits a markdown file into chunks on '##' section boundaries.

    Falls back to fixed-size splitting for sections that are still too long,
    so each chunk stays small enough to be a precise, cheap retrieval unit.
    """
    sections = []
    current: list[str] = []
    for line in text.splitlines():
        if line.startswith("## ") and current:
            sections.append("\n".join(current).strip())
            current = [line]
        else:
            current.append(line)
    if current:
        sections.append("\n".join(current).strip())

    chunks: list[Chunk] = []
    for i, section in enumerate(sections):
        if not section:
            continue
        if len(section) <= max_chars:
            chunks.append(Chunk(id=f"{source}::{i}", source=source, content=section))
        else:
            for j in range(0, len(section), max_chars):
                piece = section[j : j + max_chars]
                chunks.append(
                    Chunk(id=f"{source}::{i}.{j}", source=source, content=piece)
                )
    return chunks


def load_documents(knowledge_base_dir: Path | None = None) -> list[Chunk]:
    """Loads every markdown file in the knowledge base directory as chunks."""
    kb_dir = knowledge_base_dir or get_settings().knowledge_base_dir
    if not kb_dir.exists():
        return []

    all_chunks: list[Chunk] = []
    for file_path in sorted(kb_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        all_chunks.extend(_chunk_markdown(text, source=file_path.name))
    return all_chunks
