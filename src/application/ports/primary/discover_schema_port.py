from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from src.application.commands.discover_schema_command import DiscoverSchemaCommand
from src.domain.exceptions import DomainException


class InvalidRowFilterError(DomainException):
    """Raised when the provided BigQuery row filter is syntactically invalid."""


@dataclass(frozen=True)
class DiscoveredColumn:
    name: str
    type: str


@dataclass(frozen=True)
class DiscoverSchemaResponse:
    columns: list[DiscoveredColumn]


class DiscoverSchemaPort(ABC):
    @abstractmethod
    def execute(self, command: DiscoverSchemaCommand) -> DiscoverSchemaResponse:
        """Connect to the configured BigQuery table and return its schema."""
