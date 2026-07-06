"""Application service for project management."""

from __future__ import annotations

from app.persistence.repositories import ProjectRepository


class ProjectService:
    """Thin application-layer service for project CRUD operations."""

    def __init__(self, repository: ProjectRepository | None = None) -> None:
        self._repository = repository or ProjectRepository()

    def create_project(self, *, name: str, description: str | None = None) -> dict[str, object]:
        return self._repository.create_project(name=name, description=description)

    def list_projects(self) -> list[dict[str, object]]:
        return self._repository.list_projects()

    def get_project(self, project_id: str) -> dict[str, object] | None:
        return self._repository.get_project(project_id)

    def update_project(
        self, project_id: str, *, name: str | None = None, description: str | None = None
    ) -> dict[str, object] | None:
        return self._repository.update_project(project_id, name=name, description=description)

    def delete_project(self, project_id: str) -> bool:
        return self._repository.delete_project(project_id)
