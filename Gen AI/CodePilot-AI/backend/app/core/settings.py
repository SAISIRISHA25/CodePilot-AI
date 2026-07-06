"""
Configuration schema definitions for CodePilot AI.

This module defines the *shape* of application configuration using
Pydantic's ``BaseSettings``. Each concern (application metadata, OpenAI,
LangSmith, ChromaDB, SQLite, logging) is modeled as its own settings
class, then composed into a single top-level ``Settings`` object.

Design decisions:
    1. Separation by concern (SRP): each settings class owns exactly one
       area of configuration. A change to, say, ChromaDB configuration
       never risks touching OpenAI or SQLite settings.
    2. Independent loadability: every sub-settings class declares its
       own ``env_prefix``, so each can technically be instantiated and
       validated on its own (useful for unit testing configuration in
       isolation) even though in practice they are composed together.
    3. No framework leakage: this module only depends on Pydantic and
       the standard library. LangChain, LangGraph, and FastAPI must
       never be imported here — settings are pure configuration data.
    4. Values are read from a ``.env`` file (see ``.env.example``) and/or
       real environment variables, with environment variables always
       taking precedence over ``.env`` file values (Pydantic default
       behavior), which is the correct convention for containerized
       deployments (Docker) where env vars are injected at runtime.
"""

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.constants import Environment


class AppSettings(BaseSettings):
    """Core application metadata and runtime mode.

    Attributes:
        name: Human-readable application name, used in logs, API docs,
            and LangSmith project tagging.
        environment: The deployment environment CodePilot AI is running
            in. Drives conditional behavior such as debug logging.
        debug: Whether verbose debug behavior (e.g., detailed error
            responses) is enabled. Should be False in production.
    """

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    name: str = Field(default="CodePilot AI", description="Application name.")
    environment: Environment = Field(
        default=Environment.DEVELOPMENT,
        description="Current deployment environment.",
    )
    debug: bool = Field(
        default=False,
        description="Enable verbose/debug behavior. Must be False in production.",
    )


class OpenAISettings(BaseSettings):
    """Configuration for the OpenAI LLM provider.

    Attributes:
        api_key: Secret API key for authenticating with OpenAI.
            Wrapped in ``SecretStr`` so it is never accidentally printed
            in logs, tracebacks, or ``repr()`` output.
        chat_model: Default chat completion model used by agents unless
            an agent explicitly overrides it.
        embedding_model: Default embedding model used by the RAG
            ingestion/retrieval pipeline.
        request_timeout_seconds: Timeout applied to outbound OpenAI API
            calls, preventing hung requests from stalling a LangGraph
            node indefinitely.
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="OpenAI API key. Required for any LLM call to succeed.",
    )
    chat_model: str = Field(
        default="gpt-4o-mini",
        description="Default OpenAI chat model used by agents.",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="Default OpenAI embedding model used by the RAG pipeline.",
    )
    request_timeout_seconds: int = Field(
        default=60,
        ge=1,
        description="Timeout, in seconds, for outbound OpenAI API requests.",
    )


class LangSmithSettings(BaseSettings):
    """Configuration for LangSmith observability/tracing.

    Attributes:
        api_key: Secret API key for authenticating with LangSmith.
        project: LangSmith project name under which traces are grouped.
            Distinct trace groups per environment make it easy to
            separate development noise from production traces.
        tracing_enabled: Master switch for tracing. Kept explicit
            (rather than inferring from key presence) so tracing can be
            deliberately disabled in tests without unsetting the key.
        endpoint: LangSmith API endpoint. Overridable for self-hosted or
            regional LangSmith deployments.
    """

    model_config = SettingsConfigDict(
        env_prefix="LANGSMITH_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    api_key: SecretStr = Field(
        default=SecretStr(""),
        description="LangSmith API key for trace ingestion.",
    )
    project: str = Field(
        default="codepilot-ai-dev",
        description="LangSmith project name used to group traces.",
    )
    tracing_enabled: bool = Field(
        default=True,
        description="Master switch to enable/disable LangSmith tracing.",
    )
    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint.",
    )


class ChromaDBSettings(BaseSettings):
    """Configuration for the ChromaDB vector store.

    Per architectural rule, ChromaDB is used strictly for vector
    storage — no project metadata or audit data is ever persisted here.

    Attributes:
        persist_directory: Filesystem path where ChromaDB persists its
            on-disk index. Mounted as a Docker volume in deployment.
        collection_name: Default collection name for embedded document
            chunks. Later modules may namespace this per project.
    """

    model_config = SettingsConfigDict(
        env_prefix="CHROMA_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    persist_directory: str = Field(
        default="./data/chroma",
        description="Filesystem path for ChromaDB's persisted index.",
    )
    collection_name: str = Field(
        default="codepilot_documents",
        description="Default ChromaDB collection name for document chunks.",
    )


class SQLiteSettings(BaseSettings):
    """Configuration for the SQLite relational store.

    Per architectural rule, SQLite is used strictly for project
    metadata, audit logs, session information, and generated artifacts
    — never for vector data.

    Attributes:
        database_path: Filesystem path to the SQLite database file.
        echo: Whether the ORM/engine should echo raw SQL statements.
            Useful for debugging, must be False in production to avoid
            leaking data into logs and to reduce log noise/cost.
    """

    model_config = SettingsConfigDict(
        env_prefix="SQLITE_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_path: str = Field(
        default="./data/codepilot.db",
        description="Filesystem path to the SQLite database file.",
    )
    echo: bool = Field(
        default=False,
        description="Echo raw SQL statements. Keep False in production.",
    )


class LoggingSettings(BaseSettings):
    """Configuration for application logging.

    Attributes:
        level: Minimum log level emitted by the application logger.
        json_format: Whether logs are emitted as structured JSON
            (preferred for production/observability pipelines) or as
            human-readable text (preferred for local development).
    """

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    level: str = Field(
        default="INFO",
        description="Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).",
    )
    json_format: bool = Field(
        default=False,
        description="Emit logs as structured JSON instead of plain text.",
    )


class Settings(BaseSettings):
    """Top-level, composed application settings.

    This class aggregates every domain-specific settings class into a
    single object. Consumers should depend on this composed object
    (via ``core.config.get_settings``) rather than instantiating the
    individual sub-settings classes directly, so that configuration
    always flows through one predictable seam.

    Attributes:
        app: Application metadata and runtime mode.
        openai: OpenAI LLM provider configuration.
        langsmith: LangSmith observability configuration.
        chroma: ChromaDB vector store configuration.
        sqlite: SQLite relational store configuration.
        logging: Logging configuration.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Each sub-settings class independently reads its own prefixed
    # environment variables; default_factory ensures a fresh instance
    # per Settings instantiation rather than a shared mutable default.
    app: AppSettings = Field(default_factory=AppSettings)
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    langsmith: LangSmithSettings = Field(default_factory=LangSmithSettings)
    chroma: ChromaDBSettings = Field(default_factory=ChromaDBSettings)
    sqlite: SQLiteSettings = Field(default_factory=SQLiteSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)