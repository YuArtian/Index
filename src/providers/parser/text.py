"""
Plain text parser provider.
"""

from pathlib import Path

from .base import ParserProvider, ParsedDocument, Chunk


class TextParser(ParserProvider):
    """
    Parser for plain text content.

    Splits text into overlapping chunks of specified size.
    """

    def parse(self, content: str, metadata: dict | None = None) -> ParsedDocument:
        """Parse text content into chunks."""
        if not content or not content.strip():
            return ParsedDocument(chunks=[], metadata=metadata or {})

        content = content.strip()
        chunks = self._chunk_text(content)

        return ParsedDocument(
            chunks=[
                Chunk(content=chunk, index=i, metadata={})
                for i, chunk in enumerate(chunks)
            ],
            metadata=metadata or {},
        )

    def parse_file(self, file_path: str) -> ParsedDocument:
        """Parse a text file into chunks."""
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        content = path.read_text(encoding="utf-8")
        metadata = {
            "source": str(path),
            "filename": path.name,
            "file_type": "text",
        }

        return self.parse(content, metadata)

    def _chunk_text(self, text: str) -> list[str]:
        """Split text into overlapping chunks."""
        if len(text) <= self.chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - self.chunk_overlap

        return chunks
