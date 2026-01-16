"""
Markdown parser provider.
"""

import re
from pathlib import Path

from .base import ParserProvider, ParsedDocument, Chunk


class MarkdownParser(ParserProvider):
    """
    Parser for Markdown content.

    Preserves document structure by splitting on headers and sections.
    Falls back to text chunking for sections that are too large.
    """

    def parse(self, content: str, metadata: dict | None = None) -> ParsedDocument:
        """Parse markdown content into chunks."""
        if not content or not content.strip():
            return ParsedDocument(chunks=[], metadata=metadata or {})

        content = content.strip()

        # Extract title from first H1 if exists
        title_match = re.match(r"^#\s+(.+?)$", content, re.MULTILINE)
        doc_title = title_match.group(1) if title_match else None

        # Split by headers (##, ###, etc.)
        sections = self._split_by_headers(content)

        chunks = []
        chunk_index = 0

        for section in sections:
            section_chunks = self._chunk_section(section)
            for chunk_content in section_chunks:
                chunks.append(
                    Chunk(
                        content=chunk_content,
                        index=chunk_index,
                        metadata={"section": section.get("header", "")},
                    )
                )
                chunk_index += 1

        doc_metadata = metadata or {}
        if doc_title:
            doc_metadata["title"] = doc_title

        return ParsedDocument(chunks=chunks, metadata=doc_metadata)

    def parse_file(self, file_path: str) -> ParsedDocument:
        """Parse a markdown file into chunks."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        metadata = {
            "source": str(path),
            "filename": path.name,
            "file_type": "markdown",
        }

        return self.parse(content, metadata)

    def _split_by_headers(self, content: str) -> list[dict]:
        """Split content by markdown headers."""
        # Pattern to match headers (## or ### or ####)
        header_pattern = re.compile(r"^(#{2,6})\s+(.+?)$", re.MULTILINE)

        sections = []
        last_end = 0
        current_header = ""

        for match in header_pattern.finditer(content):
            # Add previous section
            if match.start() > last_end:
                section_content = content[last_end : match.start()].strip()
                if section_content:
                    sections.append(
                        {
                            "header": current_header,
                            "content": section_content,
                        }
                    )

            current_header = match.group(2)
            last_end = match.end()

        # Add final section
        if last_end < len(content):
            section_content = content[last_end:].strip()
            if section_content:
                sections.append(
                    {
                        "header": current_header,
                        "content": section_content,
                    }
                )

        # If no headers found, treat entire content as one section
        if not sections:
            sections.append({"header": "", "content": content})

        return sections

    def _chunk_section(self, section: dict) -> list[str]:
        """Chunk a section, preserving header if present."""
        content = section["content"]
        header = section["header"]

        # If section is small enough, return as is
        if len(content) <= self.chunk_size:
            return [content]

        # Otherwise, chunk the content
        chunks = []
        start = 0

        while start < len(content):
            end = start + self.chunk_size
            chunk = content[start:end]

            # Add header context to first chunk of each section
            if start == 0 and header:
                chunk = f"## {header}\n\n{chunk}"

            chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks
