"""Document management API routes."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status, Depends
from pydantic import BaseModel, Field

from app.api.router import APIResponse
from app.core.constants import DocumentType
from app.dependencies import DocumentRepositoryDependency, IngestionServiceDependency, get_vector_store_gateway
from app.rag.vector_store import VectorStoreService

router = APIRouter(tags=["Documents"])


class DocumentResponse(BaseModel):
    id: str = Field(description="Document identifier.")
    project_id: str = Field(description="Owning project identifier.")
    filename: str = Field(description="Uploaded filename.")
    document_type: str = Field(description="Document category.")
    file_path: str = Field(description="Stored file path.")
    created_at: str = Field(description="Upload timestamp.")


class IngestionResponse(BaseModel):
    project_id: str = Field(description="Owning project identifier.")
    filename: str = Field(description="Name of the ingested file.")
    document_type: str = Field(description="Type of the ingested document.")
    source_document_id: str = Field(description="Identifier for the source document.")
    total_chunks: int = Field(ge=0, description="Number of chunks stored.")
    chunk_ids: list[str] = Field(default_factory=list, description="Stored chunk IDs.")
    embedding_model: str | None = Field(default=None, description="Embedding model used.")
    ingested_at: str | None = Field(default=None, description="Ingestion timestamp.")


@router.post(
    "/projects/{project_id}/documents",
    response_model=APIResponse[DocumentResponse],
    summary="Upload a document",
)
async def upload_document(
    project_id: str,
    file: UploadFile,
    document_type: Annotated[DocumentType, Form()] = DocumentType.BUSINESS_REQUIREMENT_DOCUMENT,
    repository: DocumentRepositoryDependency = None,
) -> APIResponse[DocumentResponse]:
    if file.filename is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Filename is required")

    # Ensure temporary upload directory exists
    temp_dir = Path("data/tmp")
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = str(temp_dir / file.filename)
    with open(file_path, "wb") as handle:
        handle.write(await file.read())

    record = repository.create_document(
        project_id=project_id,
        filename=file.filename,
        document_type=document_type.value,
        file_path=file_path,
    )
    return APIResponse[DocumentResponse](message="Document uploaded.", data=DocumentResponse(**record))


@router.get(
    "/projects/{project_id}/documents",
    response_model=APIResponse[list[DocumentResponse]],
    summary="List uploaded documents",
)
async def list_documents(
    project_id: str,
    repository: DocumentRepositoryDependency = None,
) -> APIResponse[list[DocumentResponse]]:
    rows = repository.list_documents(project_id=project_id)
    return APIResponse[list[DocumentResponse]](
        message="Documents retrieved.",
        data=[DocumentResponse(**row) for row in rows],
    )


@router.delete(
    "/projects/{project_id}/documents/{document_id}",
    response_model=APIResponse[dict[str, bool]],
    summary="Delete a document",
)
async def delete_document(
    project_id: str,
    document_id: str,
    repository: DocumentRepositoryDependency = None,
    vector_store: VectorStoreService = Depends(get_vector_store_gateway),
) -> APIResponse[dict[str, bool]]:
    existing = repository.get_document(document_id)
    if existing is None or str(existing["project_id"]) != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    
    # Delete chunks from vector store first
    try:
        vector_store.delete_document_chunks(document_id)
    except Exception as exc:
        # Log error and continue to let SQLite delete happen
        pass

    deleted = repository.delete_document(document_id)
    return APIResponse[dict[str, bool]](message="Document deleted.", data={"deleted": deleted})


@router.post(
    "/projects/{project_id}/documents/{document_id}/ingest",
    response_model=APIResponse[IngestionResponse],
    summary="Trigger ingestion",
)
async def trigger_ingestion(
    project_id: str,
    document_id: str,
    ingestion_service: IngestionServiceDependency = None,
    repository: DocumentRepositoryDependency = None,
) -> APIResponse[IngestionResponse]:
    record = repository.get_document(document_id)
    if record is None or str(record["project_id"]) != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    try:
        result = ingestion_service.ingest_document(
            project_id=project_id,
            file_path=str(record["file_path"]),
            filename=str(record["filename"]),
            document_type=DocumentType(str(record["document_type"])),
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    return APIResponse[IngestionResponse](message="Ingestion completed.", data=IngestionResponse(**result.model_dump()))
