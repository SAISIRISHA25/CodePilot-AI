from app.agents.base_agent import BaseAgent
from app.agents.planning_agent import PlanningAgent
from app.application.models import AgentRequest, AgentResponse, QueryResponse


def test_core_agent_imports_are_available() -> None:
    assert BaseAgent.__name__ == "BaseAgent"
    assert PlanningAgent.__name__ == "PlanningAgent"


def test_application_models_can_be_instantiated() -> None:
    request = AgentRequest(
        agent_type="requirements",
        task_description="Draft requirements",
        project_id="proj-1",
    )
    response = AgentResponse(
        agent_type="requirements",
        agent_name="Requirements Agent",
        content="Drafted",
    )
    query = QueryResponse(question="What is this?", answer="This is a test.")

    assert request.project_id == "proj-1"
    assert response.agent_name == "Requirements Agent"
    assert query.answer == "This is a test."
