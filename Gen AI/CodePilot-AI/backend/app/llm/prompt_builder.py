"""
Prompt construction for the LLM package.

Every function/method here builds ``ChatMessage`` objects - never calls
the OpenAI API, never imports ``llm_service``, and never depends on any
network client. This separation (prompt construction vs. LLM
invocation) is deliberate: it means prompt wording can be reviewed,
versioned, and unit-tested in complete isolation from network calls,
and it means ``LLMService`` never needs to know *why* a particular
message sequence was built - only how to send it.

Design decision:
    ``PromptBuilder`` groups related construction methods as static
    methods on a single class (rather than loose module-level
    functions) purely for discoverability and namespacing at call
    sites (``PromptBuilder.build_rag_qa_prompt(...)``). Each method is
    still a pure function with no shared state, so this is a
    namespace, not a stateful collaborator.
"""

from app.llm.exceptions import InvalidPromptError
from app.llm.models import ChatMessage, MessageRole

# Default system instruction used whenever a caller doesn't supply their
# own agent-specific system prompt. Kept generic and framework-neutral -
# individual agents (in a later module) are expected to supply their own
# role-specific system prompts via `build_system_prompt`.
_DEFAULT_SYSTEM_INSTRUCTION = (
    "You are a precise, professional software engineering assistant. "
    "Answer only using the information provided to you. If the "
    "provided context does not contain enough information to answer "
    "confidently, say so explicitly instead of guessing."
)


class PromptBuilder:
    """Builds reusable, structured chat prompts as ``ChatMessage`` lists.

    Every method returns either a single ``ChatMessage`` or a
    ``list[ChatMessage]`` ready to be placed directly into an
    ``LLMRequest.messages`` field.
    """

    @staticmethod
    def build_system_prompt(role_description: str, instructions: str) -> ChatMessage:
        """Build a system message defining an agent's role and behavior.

        Args:
            role_description: A short description of who the assistant
                is acting as (e.g., ``"a senior solution architect"``).
            instructions: Detailed behavioral instructions for the
                assistant to follow (tone, output format, constraints).

        Returns:
            ChatMessage: A ``system``-role message combining the role
            description and instructions.

        Raises:
            InvalidPromptError: If either argument is empty or
                whitespace-only.
        """
        if not role_description.strip():
            raise InvalidPromptError("role_description must not be empty.")
        if not instructions.strip():
            raise InvalidPromptError("instructions must not be empty.")

        content = f"You are {role_description.strip()}.\n\n{instructions.strip()}"
        return ChatMessage(role=MessageRole.SYSTEM, content=content)

    @staticmethod
    def build_assistant_prompt(content: str) -> ChatMessage:
        """Build an assistant message, typically used for few-shot examples.

        Args:
            content: The assistant-authored text to include in the
                conversation history (e.g., a prior turn's response
                used to steer style or format in a few-shot setup).

        Returns:
            ChatMessage: An ``assistant``-role message.

        Raises:
            InvalidPromptError: If ``content`` is empty or
                whitespace-only.
        """
        if not content.strip():
            raise InvalidPromptError("Assistant prompt content must not be empty.")

        return ChatMessage(role=MessageRole.ASSISTANT, content=content.strip())

    @staticmethod
    def build_rag_qa_prompt(
        question: str,
        context_chunks: list[str],
        system_instruction: str | None = None,
    ) -> list[ChatMessage]:
        """Build a grounded question-answering prompt from retrieved chunks.

        Assembles a system message instructing the model to answer only
        from the supplied context, followed by a user message
        containing the numbered context chunks and the question.
        Intended to consume the output of
        ``app.rag.retriever.RetrieverService.retrieve`` (the caller
        extracts ``.content`` from each ``RetrievalResult`` before
        passing it here - this function has no dependency on the RAG
        package's models, keeping the two packages decoupled).

        Args:
            question: The user's natural-language question.
            context_chunks: Retrieved text chunks to ground the answer
                in, ordered from most to least relevant.
            system_instruction: Optional override for the system
                message's instructions. Defaults to a generic
                grounded-answering instruction when not supplied.

        Returns:
            list[ChatMessage]: A two-message conversation: one
            ``system`` message and one ``user`` message.

        Raises:
            InvalidPromptError: If ``question`` is empty, or
                ``context_chunks`` is empty or contains only blank
                strings.
        """
        if not question.strip():
            raise InvalidPromptError("question must not be empty.")

        non_blank_chunks = [chunk.strip() for chunk in context_chunks if chunk.strip()]
        if not non_blank_chunks:
            raise InvalidPromptError("context_chunks must contain at least one non-empty chunk.")

        system_message = ChatMessage(
            role=MessageRole.SYSTEM,
            content=system_instruction.strip() if system_instruction else _DEFAULT_SYSTEM_INSTRUCTION,
        )

        formatted_context = "\n\n".join(
            f"[Context {index + 1}]\n{chunk}" for index, chunk in enumerate(non_blank_chunks)
        )
        user_content = (
            f"Use the following context to answer the question.\n\n"
            f"{formatted_context}\n\n"
            f"Question: {question.strip()}"
        )
        user_message = ChatMessage(role=MessageRole.USER, content=user_content)

        return [system_message, user_message]

    @staticmethod
    def build_document_grounded_prompt(
        task_instructions: str,
        document_context: str,
        user_request: str,
        system_role_description: str = "an expert software engineering assistant",
    ) -> list[ChatMessage]:
        """Build a prompt for producing output grounded in a source document.

        Distinct from ``build_rag_qa_prompt`` in intent: this is meant
        for generative tasks (e.g., "draft an architecture summary from
        this requirements document") rather than direct question
        answering over retrieved chunks. The document context is framed
        as authoritative source material the response must stay
        faithful to.

        Args:
            task_instructions: What the assistant should produce (e.g.,
                "Summarize the key functional requirements as a bullet
                list.").
            document_context: The source document text (or relevant
                excerpt) the output must be grounded in.
            user_request: The specific user-facing request or question
                driving this generation.
            system_role_description: Role description used to build the
                system message. Defaults to a generic engineering
                assistant role.

        Returns:
            list[ChatMessage]: A two-message conversation: one
            ``system`` message and one ``user`` message.

        Raises:
            InvalidPromptError: If any of ``task_instructions``,
                ``document_context``, or ``user_request`` is empty or
                whitespace-only.
        """
        if not task_instructions.strip():
            raise InvalidPromptError("task_instructions must not be empty.")
        if not document_context.strip():
            raise InvalidPromptError("document_context must not be empty.")
        if not user_request.strip():
            raise InvalidPromptError("user_request must not be empty.")

        system_message = PromptBuilder.build_system_prompt(
            role_description=system_role_description,
            instructions=(
                f"{task_instructions.strip()}\n\n"
                "Base your response strictly on the provided document context. "
                "Do not invent requirements, facts, or details that are not "
                "present in the context."
            ),
        )

        user_content = (
            f"--- Document Context ---\n{document_context.strip()}\n"
            f"--- End Document Context ---\n\n"
            f"{user_request.strip()}"
        )
        user_message = ChatMessage(role=MessageRole.USER, content=user_content)

        return [system_message, user_message]