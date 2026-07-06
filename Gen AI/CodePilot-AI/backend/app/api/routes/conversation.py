"""Conversation API routes."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.router import APIResponse

router = APIRouter(tags=["Conversation"])


class ConversationCreateRequest(BaseModel):
    project_id: str = Field(min_length=1, description="Project identifier.")
    title: str | None = Field(default=None, description="Conversation title.")


class ConversationResponse(BaseModel):
    id: str = Field(description="Conversation identifier.")
    project_id: str = Field(description="Project identifier.")
    title: str | None = Field(default=None, description="Conversation title.")


class ConversationMessageResponse(BaseModel):
    role: str = Field(description="Message role.")
    content: str = Field(description="Message content.")


class ConversationHistoryResponse(BaseModel):
    conversation_id: str = Field(description="Conversation identifier.")
    messages: list[ConversationMessageResponse] = Field(default_factory=list)


@router.post(
    "/conversations",
    response_model=APIResponse[ConversationResponse],
    summary="Create conversation",
)
async def create_conversation(request: ConversationCreateRequest) -> APIResponse[ConversationResponse]:
    return APIResponse[ConversationResponse](
        message="Conversation created.",
        data=ConversationResponse(id="conv-1", project_id=request.project_id, title=request.title),
    )


@router.post(
    "/conversations/{conversation_id}",
    response_model=APIResponse[ConversationHistoryResponse],
    summary="Continue conversation",
)
async def continue_conversation(conversation_id: str) -> APIResponse[ConversationHistoryResponse]:
    return APIResponse[ConversationHistoryResponse](
        message="Conversation continued.",
        data=ConversationHistoryResponse(conversation_id=conversation_id, messages=[]),
    )


@router.get(
    "/conversations/{conversation_id}",
    response_model=APIResponse[ConversationHistoryResponse],
    summary="Retrieve conversation history",
)
async def get_conversation_history(conversation_id: str) -> APIResponse[ConversationHistoryResponse]:
    return APIResponse[ConversationHistoryResponse](
        message="Conversation history retrieved.",
        data=ConversationHistoryResponse(conversation_id=conversation_id, messages=[]),
    )
