"""Persistence repositories for the application layer."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import json
from app.persistence.database import DatabaseManager


class ProjectRepository:
    """SQLite-backed repository for project metadata."""

    def __init__(self, database_path: str | None = None) -> None:
        self._database = DatabaseManager(database_path=database_path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._database.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create_project(
        self, *, name: str, description: str | None = None
    ) -> dict[str, object]:
        project_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        updated_at = created_at

        with self._database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO projects (id, name, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (project_id, name, description, created_at, updated_at),
            )
            connection.commit()

        return {
            "id": project_id,
            "name": name,
            "description": description,
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def list_projects(self) -> list[dict[str, object]]:
        with self._database.get_connection() as connection:
            rows = connection.execute(
                "SELECT id, name, description, created_at, updated_at FROM projects ORDER BY created_at"
            ).fetchall()

        return [dict(row) for row in rows]

    def get_project(self, project_id: str) -> dict[str, object] | None:
        with self._database.get_connection() as connection:
            row = connection.execute(
                "SELECT id, name, description, created_at, updated_at FROM projects WHERE id = ?",
                (project_id,),
            ).fetchone()

        return None if row is None else dict(row)

    def update_project(
        self, project_id: str, *, name: str | None = None, description: str | None = None
    ) -> dict[str, object] | None:
        current = self.get_project(project_id)
        if current is None:
            return None

        updated_name = name if name is not None else str(current["name"])
        updated_description = description if description is not None else current["description"]
        updated_at = datetime.now(UTC).isoformat()

        with self._database.get_connection() as connection:
            connection.execute(
                "UPDATE projects SET name = ?, description = ?, updated_at = ? WHERE id = ?",
                (updated_name, updated_description, updated_at, project_id),
            )
            connection.commit()

        return {
            "id": project_id,
            "name": updated_name,
            "description": updated_description,
            "created_at": current["created_at"],
            "updated_at": updated_at,
        }

    def delete_project(self, project_id: str) -> bool:
        with self._database.get_connection() as connection:
            cursor = connection.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            connection.commit()
        return cursor.rowcount > 0


class DocumentRepository:
    """SQLite-backed repository for document metadata."""

    def __init__(self, database_path: str | None = None) -> None:
        self._database = DatabaseManager(database_path=database_path)

    def create_document(
        self,
        *,
        project_id: str,
        filename: str,
        document_type: str,
        file_path: str,
    ) -> dict[str, object]:
        document_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()

        with self._database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, project_id, filename, document_type, file_path, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (document_id, project_id, filename, document_type, file_path, created_at),
            )
            connection.commit()

        return {
            "id": document_id,
            "project_id": project_id,
            "filename": filename,
            "document_type": document_type,
            "file_path": file_path,
            "created_at": created_at,
        }

    def get_document(self, document_id: str) -> dict[str, object] | None:
        with self._database.get_connection() as connection:
            row = connection.execute(
                "SELECT id, project_id, filename, document_type, file_path, created_at FROM documents WHERE id = ?",
                (document_id,),
            ).fetchone()

        if row is None:
            return None
        return dict(row)

    def list_documents(self, *, project_id: str | None = None) -> list[dict[str, object]]:
        query = "SELECT id, project_id, filename, document_type, file_path, created_at FROM documents"
        params: tuple[object, ...] = ()
        if project_id is not None:
            query += " WHERE project_id = ?"
            params = (project_id,)

        with self._database.get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def update_document(self, document_id: str, **updates: object) -> dict[str, object] | None:
        if not updates:
            return self.get_document(document_id)

        allowed_fields = {"filename", "document_type", "file_path"}
        invalid_fields = set(updates) - allowed_fields
        if invalid_fields:
            raise ValueError(f"Unsupported update fields: {sorted(invalid_fields)}")

        assignments = ", ".join(f"{field} = ?" for field in updates)
        values = list(updates.values()) + [document_id]

        with self._database.get_connection() as connection:
            connection.execute(
                f"UPDATE documents SET {assignments} WHERE id = ?",
                values,
            )
            connection.commit()

        return self.get_document(document_id)

    def delete_document(self, document_id: str) -> bool:
        with self._database.get_connection() as connection:
            cursor = connection.execute("DELETE FROM documents WHERE id = ?", (document_id,))
            connection.commit()
        return cursor.rowcount > 0


class WorkflowRunRepository:
    """SQLite-backed repository for workflow execution history and status."""

    def __init__(self, database_path: str | None = None) -> None:
        self._database = DatabaseManager(database_path=database_path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._database.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS workflow_runs (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    user_prompt TEXT,
                    current_phase TEXT,
                    errors TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create_workflow_run(
        self, *, project_id: str, status: str, user_prompt: str, current_phase: str
    ) -> dict[str, object]:
        run_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()
        updated_at = created_at

        with self._database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO workflow_runs (id, project_id, status, user_prompt, current_phase, errors, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, project_id, status, user_prompt, current_phase, "[]", created_at, updated_at),
            )
            connection.commit()

        return {
            "id": run_id,
            "project_id": project_id,
            "status": status,
            "user_prompt": user_prompt,
            "current_phase": current_phase,
            "errors": [],
            "created_at": created_at,
            "updated_at": updated_at,
        }

    def update_workflow_run(
        self, run_id: str, *, status: str | None = None, current_phase: str | None = None, errors: list[str] | None = None
    ) -> dict[str, object] | None:
        current = self.get_workflow_run(run_id)
        if current is None:
            return None

        updated_status = status if status is not None else str(current["status"])
        updated_phase = current_phase if current_phase is not None else current["current_phase"]
        updated_errors = json.dumps(errors) if errors is not None else json.dumps(current["errors"])
        updated_at = datetime.now(UTC).isoformat()

        with self._database.get_connection() as connection:
            connection.execute(
                """
                UPDATE workflow_runs
                SET status = ?, current_phase = ?, errors = ?, updated_at = ?
                WHERE id = ?
                """,
                (updated_status, updated_phase, updated_errors, updated_at, run_id),
            )
            connection.commit()

        return {
            "id": run_id,
            "project_id": current["project_id"],
            "status": updated_status,
            "user_prompt": current["user_prompt"],
            "current_phase": updated_phase,
            "errors": errors if errors is not None else current["errors"],
            "created_at": current["created_at"],
            "updated_at": updated_at,
        }

    def get_workflow_run(self, run_id: str) -> dict[str, object] | None:
        with self._database.get_connection() as connection:
            row = connection.execute(
                "SELECT id, project_id, status, user_prompt, current_phase, errors, created_at, updated_at FROM workflow_runs WHERE id = ?",
                (run_id,),
            ).fetchone()

        if row is None:
            return None
        
        data = dict(row)
        try:
            data["errors"] = json.loads(str(data["errors"]))
        except Exception:
            data["errors"] = []
        return data

    def list_workflow_runs(self, *, project_id: str) -> list[dict[str, object]]:
        with self._database.get_connection() as connection:
            rows = connection.execute(
                "SELECT id, project_id, status, user_prompt, current_phase, errors, created_at, updated_at FROM workflow_runs WHERE project_id = ? ORDER BY created_at",
                (project_id,),
            ).fetchall()

        results = []
        for row in rows:
            data = dict(row)
            try:
                data["errors"] = json.loads(str(data["errors"]))
            except Exception:
                data["errors"] = []
            results.append(data)
        return results


class ArtifactRepository:
    """SQLite-backed repository for generated engineering artifacts."""

    def __init__(self, database_path: str | None = None) -> None:
        self._database = DatabaseManager(database_path=database_path)
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self._database.get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    content_type TEXT,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def create_artifact(
        self, *, project_id: str, name: str, content_type: str | None = None, content: str
    ) -> dict[str, object]:
        artifact_id = str(uuid.uuid4())
        created_at = datetime.now(UTC).isoformat()

        with self._database.get_connection() as connection:
            connection.execute(
                """
                INSERT INTO artifacts (id, project_id, name, content_type, content, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (artifact_id, project_id, name, content_type, content, created_at),
            )
            connection.commit()

        return {
            "id": artifact_id,
            "project_id": project_id,
            "name": name,
            "content_type": content_type,
            "content": content,
            "created_at": created_at,
        }

    def get_artifact(self, artifact_id: str) -> dict[str, object] | None:
        with self._database.get_connection() as connection:
            row = connection.execute(
                "SELECT id, project_id, name, content_type, content, created_at FROM artifacts WHERE id = ?",
                (artifact_id,),
            ).fetchone()

        return None if row is None else dict(row)

    def list_artifacts(self, *, project_id: str | None = None) -> list[dict[str, object]]:
        query = "SELECT id, project_id, name, content_type, content, created_at FROM artifacts"
        params: tuple[object, ...] = ()
        if project_id is not None:
            query += " WHERE project_id = ?"
            params = (project_id,)
        query += " ORDER BY created_at"

        with self._database.get_connection() as connection:
            rows = connection.execute(query, params).fetchall()

        return [dict(row) for row in rows]

    def delete_artifact(self, artifact_id: str) -> bool:
        with self._database.get_connection() as connection:
            cursor = connection.execute("DELETE FROM artifacts WHERE id = ?", (artifact_id,))
            connection.commit()
        return cursor.rowcount > 0
