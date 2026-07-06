from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
from typing import Annotated

from app.api.router import APIResponse
from app.workflows.state import GraphState, WorkflowPhase, UploadedDocument
from app.core.constants import DocumentType
from app.persistence.repositories import WorkflowRunRepository
from app.workflows.executor import WorkflowExecutor
from app.workflows.workflow_factory import WorkflowFactory
from app.dependencies import (
    DocumentRepositoryDependency,
    WorkflowRunRepositoryDependency,
    get_workflow_factory,
    get_workflow_executor,
)

router = APIRouter(tags=["Workflow"])


class WorkflowStartRequest(BaseModel):
    project_id: str = Field(description="Project identifier to run against.")
    prompt: str = Field(min_length=1, description="User prompt for the workflow.")


class WorkflowStatusResponse(BaseModel):
    project_id: str = Field(description="Project identifier.")
    status: str = Field(description="Current workflow status.")
    message: str | None = Field(default=None, description="Status detail.")


class WorkflowHistoryEntryResponse(BaseModel):
    phase: str = Field(description="Workflow phase.")
    summary: str = Field(description="Summary text.")
    occurred_at: str = Field(description="Occurrence timestamp.")


class WorkflowHistoryResponse(BaseModel):
    project_id: str = Field(description="Project identifier.")
    history: list[WorkflowHistoryEntryResponse] = Field(default_factory=list)


@router.post(
    "/projects/{project_id}/workflow",
    response_model=APIResponse[WorkflowStatusResponse],
    summary="Start workflow",
)
async def start_workflow(
    project_id: str,
    request: WorkflowStartRequest,
    document_repository: DocumentRepositoryDependency,
    workflow_run_repository: WorkflowRunRepositoryDependency,
    workflow_factory: Annotated[WorkflowFactory, Depends(get_workflow_factory)],
    workflow_executor: Annotated[WorkflowExecutor, Depends(get_workflow_executor)],
) -> APIResponse[WorkflowStatusResponse]:
    if project_id != request.project_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Project IDs do not match")
    
    # 1. Fetch project documents from DB
    doc_records = document_repository.list_documents(project_id=project_id)
    uploaded_docs = [
        UploadedDocument(
            file_path=str(doc["file_path"]),
            filename=str(doc["filename"]),
            document_type=DocumentType(str(doc["document_type"])),
        )
        for doc in doc_records
    ]

    # 2. Create a database record for this run
    run = workflow_run_repository.create_workflow_run(
        project_id=project_id,
        status="running",
        user_prompt=request.prompt,
        current_phase=WorkflowPhase.PENDING.value,
    )
    run_id = str(run["id"])

    # 3. Create initial GraphState
    state = GraphState(
        project_id=project_id,
        user_prompt=request.prompt,
        uploaded_documents=uploaded_docs,
        current_phase=WorkflowPhase.PENDING,
        metadata={"run_id": run_id},
    )

    # 4. Get Compiled full SDLC Workflow and execute it
    try:
        workflow = workflow_factory.create_full_sdlc_workflow()
        final_state = workflow_executor.execute(workflow, state)
        
        # 5. Determine final phase and status from final state
        final_phase = final_state.current_phase.value
        final_status = final_phase
        errors = final_state.errors
        
        workflow_run_repository.update_workflow_run(
            run_id=run_id,
            status=final_status,
            current_phase=final_phase,
            errors=errors,
        )
        
        message = f"Workflow completed with phase: {final_phase}."
        if errors:
            message = f"Workflow completed with errors: {errors}"
            
        return APIResponse[WorkflowStatusResponse](
            message="Workflow completed.",
            data=WorkflowStatusResponse(
                project_id=project_id,
                status=final_status,
                message=message,
            ),
        )
    except Exception as exc:
        workflow_run_repository.update_workflow_run(
            run_id=run_id,
            status="failed",
            current_phase=WorkflowPhase.FAILED.value,
            errors=[str(exc)],
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {exc}",
        ) from exc


@router.get(
    "/projects/{project_id}/workflow",
    response_model=APIResponse[WorkflowStatusResponse],
    summary="Get workflow status",
)
async def get_workflow_status(
    project_id: str,
    workflow_run_repository: WorkflowRunRepositoryDependency,
) -> APIResponse[WorkflowStatusResponse]:
    runs = workflow_run_repository.list_workflow_runs(project_id=project_id)
    if not runs:
        return APIResponse[WorkflowStatusResponse](
            message="Workflow status retrieved.",
            data=WorkflowStatusResponse(
                project_id=project_id,
                status=WorkflowPhase.PENDING.value,
                message="No workflow run recorded.",
            ),
        )
    
    # Get the latest run
    latest_run = runs[-1]
    errors = latest_run.get("errors")
    message = f"Current phase: {latest_run['current_phase']}."
    if errors:
        message = f"Errors recorded: {errors}"
        
    return APIResponse[WorkflowStatusResponse](
        message="Workflow status retrieved.",
        data=WorkflowStatusResponse(
            project_id=project_id,
            status=str(latest_run["status"]),
            message=message,
        ),
    )


@router.get(
    "/projects/{project_id}/workflow/history",
    response_model=APIResponse[WorkflowHistoryResponse],
    summary="Get workflow execution history",
)
async def get_workflow_history(
    project_id: str,
    workflow_run_repository: WorkflowRunRepositoryDependency,
) -> APIResponse[WorkflowHistoryResponse]:
    runs = workflow_run_repository.list_workflow_runs(project_id=project_id)
    history = [
        WorkflowHistoryEntryResponse(
            phase=str(run["current_phase"]),
            summary=f"Run status is {run['status']}.",
            occurred_at=str(run["updated_at"]),
        )
        for run in runs
    ]
    return APIResponse[WorkflowHistoryResponse](
        message="Workflow history retrieved.",
        data=WorkflowHistoryResponse(project_id=project_id, history=history),
    )


@router.delete(
    "/projects/{project_id}/workflow",
    response_model=APIResponse[dict[str, bool]],
    summary="Cancel workflow",
)
async def cancel_workflow(
    project_id: str,
    workflow_run_repository: WorkflowRunRepositoryDependency,
) -> APIResponse[dict[str, bool]]:
    runs = workflow_run_repository.list_workflow_runs(project_id=project_id)
    if runs:
        latest_run = runs[-1]
        workflow_run_repository.update_workflow_run(
            run_id=str(latest_run["id"]),
            status="cancelled",
            current_phase=latest_run["current_phase"],
            errors=latest_run.get("errors"),
        )
    return APIResponse[dict[str, bool]](
        message="Workflow cancellation requested.",
        data={"cancelled": True},
    )
