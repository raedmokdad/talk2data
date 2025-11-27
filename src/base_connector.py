# core/base_connector.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseConnector(ABC):
    """
    Abstract base class that defines the common contract
    for all data source connectors.
    """

    @abstractmethod
    def test_connection(self) -> bool:
        """Check connectivity. Raise on error or return False."""

    @abstractmethod
    def run_query(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        """Execute a SELECT-like SQL query and return rows as list of dicts."""

    @abstractmethod
    def execute(
        self,
        sql: str,
        params: Dict[str, Any] | None = None,
    ) -> None:
        """Execute DDL/DML (CREATE, ALTER, INSERT, UPDATE, DELETE...)."""

    @abstractmethod
    def list_tables(self) -> List[str]:
        """Return a list of logical table names."""

    @abstractmethod
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Return column metadata for table_name."""
