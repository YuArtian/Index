"""
Parser providers package.
"""

from .base import ParserProvider, ParsedDocument, Chunk
from .text import TextParser
from .markdown import MarkdownParser


def create_parser(
    file_type: str = "text",
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> ParserProvider:
    """
    Factory function to create parser provider.

    Args:
        file_type: File type ("text", "markdown", "md")
        chunk_size: Size of each chunk
        chunk_overlap: Overlap between chunks

    Returns:
        ParserProvider instance
    """
    if file_type == "text":
        return TextParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    elif file_type in ("markdown", "md"):
        return MarkdownParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    else:
        # Default to text parser
        return TextParser(chunk_size=chunk_size, chunk_overlap=chunk_overlap)


__all__ = [
    "ParserProvider",
    "ParsedDocument",
    "Chunk",
    "TextParser",
    "MarkdownParser",
    "create_parser",
]
