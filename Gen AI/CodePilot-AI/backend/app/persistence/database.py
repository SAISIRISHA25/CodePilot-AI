"""SQLite database management helpers."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.core.config import get_settings

logger = logging.getLogger("codepilot.persistence.database")


class DatabaseManager:
    """Small SQLite connection manager for repository usage."""

    def __init__(self, database_path: str | None = None) -> None:
        resolved_settings = get_settings()
        self.database_path = database_path or resolved_settings.sqlite.database_path
        self._ensure_parent_directory()
        self._initialize_schema()

    def _ensure_parent_directory(self) -> None:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_schema(self) -> None:
        with self.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get_connection(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection


def initialize_database(database_path: str | None = None) -> DatabaseManager:
    """Create and return a database manager with the schema initialized."""
    return DatabaseManager(database_path=database_path)
