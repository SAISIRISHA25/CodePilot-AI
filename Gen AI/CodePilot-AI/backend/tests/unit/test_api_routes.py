from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from app.main import create_app
from app.dependencies import (
    get_ingestion_service,
    get_retriever,
    get_agent_router,
    get_workflow_factory,
)


def test_create_project_endpoint() -> None:
    app = create_app()
    client = TestClient(app)

    response = client.post(
        "/api/v1/projects",
        json={"name": "Demo Project", "description": "Created by tests"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["data"]["name"] == "Demo Project"


def test_workflow_execution_happy_path() -> None:
    app = create_app()
    
    # Create mocks
    mock_ingest = MagicMock()
    mock_retriever = MagicMock()
    mock_retriever.retrieve.return_value = []
    
    mock_agent_router = MagicMock()
    mock_agent_response = MagicMock()
    mock_agent_response.agent_name = "RequirementsAgent"
    mock_agent_response.content = "Mocked output content"
    mock_agent_router.dispatch.return_value = mock_agent_response

    # Register dependency overrides
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingest
    app.dependency_overrides[get_retriever] = lambda: mock_retriever
    app.dependency_overrides[get_agent_router] = lambda: mock_agent_router

    from app.dependencies import get_workflow_run_repository, get_artifact_repository
    from app.workflows.workflow_factory import WorkflowFactory
    mock_wf_factory = WorkflowFactory(
        ingestion_service=mock_ingest,
        retriever=mock_retriever,
        agent_router=mock_agent_router,
        workflow_run_repository=get_workflow_run_repository(),
        artifact_repository=get_artifact_repository(),
    )
    app.dependency_overrides[get_workflow_factory] = lambda: mock_wf_factory

    client = TestClient(app)

    # 1. Create a project
    r_proj = client.post("/api/v1/projects", json={"name": "Test Project", "description": "For workflow testing"})
    assert r_proj.status_code == 200
    proj_id = r_proj.json()["data"]["id"]

    # 2. Run the workflow (without documents, so it skips ingestion and proceeds to retrieval + all agents)
    r_wf = client.post(f"/api/v1/projects/{proj_id}/workflow", json={"project_id": proj_id, "prompt": "Verify Happy Path"})
    assert r_wf.status_code == 200
    wf_payload = r_wf.json()
    assert wf_payload["success"] is True
    assert wf_payload["data"]["status"] == "completed"

    # 3. Check workflow history
    r_hist = client.get(f"/api/v1/projects/{proj_id}/workflow/history")
    assert r_hist.status_code == 200
    hist_payload = r_hist.json()
    assert len(hist_payload["data"]["history"]) > 0

    # 4. Check generated artifacts
    r_arts = client.get("/api/v1/artifacts", params={"project_id": proj_id})
    assert r_arts.status_code == 200
    arts_payload = r_arts.json()
    # There should be artifacts from requirements, architecture, planning, coding, testing, documentation, review
    assert len(arts_payload["data"]) == 7
    artifact_names = [a["name"] for a in arts_payload["data"]]
    assert "requirements" in artifact_names
    assert "coding" in artifact_names

    # Clean up overrides
    app.dependency_overrides.clear()
