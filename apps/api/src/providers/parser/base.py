"""
Base class for parser providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Chunk:
    """A chunk of parsed content."""

    content: str
    index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class ParsedDocument:
    """Parsed document with chunks."""

    chunks: list[Chunk]
    metadata: dict = field(default_factory=dict)


class ParserProvider(ABC):
    """
    Abstract base class for parser providers.

    All parser implementations must inherit from this class
    and implement the required methods.
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @abstractmethod
    def parse(self, content: str, metadata: dict | None = None) -> ParsedDocument:
        """
        Parse content into chunks.

        Args:
            content: Raw content to parse
            metadata: Optional metadata to attach to document

        Returns:
            ParsedDocument with chunks
        """
        pass

    @abstractmethod
    def parse_file(self, file_path: str) -> ParsedDocument:
        """
        Parse a file into chunks.

        Args:
            file_path: Path to the file

        Returns:
            ParsedDocument with chunks
        """
        pass
