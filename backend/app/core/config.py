"""
Application configuration via pydantic-settings.
All values are sourced from environment variables or .env file.
Zero hardcoded secrets.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Literal

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=os.getenv("ENV_FILE", ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_secret_key: str = Field(..., min_length=16)
    log_level: str = "INFO"
    cors_origins: str | list[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = json.loads(v)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed]
                except Exception:
                    pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        if isinstance(v, list):
            return [str(origin).strip() for origin in v]
        return ["http://localhost:3000", "http://localhost:5173"]

    # ── Database ─────────────────────────────────────────────────────
    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "preauth_db"
    postgres_user: str = "preauth_user"
    postgres_password: str = Field(..., min_length=8)

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ─────────────────────────────────────────────────────────
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def celery_broker_url(self) -> str:
        return self.redis_url

    @property
    def celery_result_backend(self) -> str:
        return self.redis_url

    # ── LLM Provider ─────────────────────────────────────────────────
    llm_provider: Literal["openai", "ollama", "stub"] = "stub"
    openai_api_key: str = "sk-placeholder"
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    ollama_base_url: str = "http://ollama:11434"
    ollama_model: str = "mistral:7b-instruct"
    stub_response_delay_ms: int = 500

    # ── Embeddings ───────────────────────────────────────────────────
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_device: str = "cpu"

    # ── Vector Store ─────────────────────────────────────────────────
    vector_store_path: str = "/app/corpus/processed/faiss_index"
    vector_store_type: Literal["faiss", "chroma"] = "faiss"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k_retrieval: int = 6

    # ── Agent Configuration ──────────────────────────────────────────
    agent_max_steps: int = 12
    agent_max_tool_calls: int = 20
    agent_wall_clock_timeout_s: int = 120
    agent_retry_max: int = 3
    agent_retry_backoff_base: float = 2.0

    # ── Circuit Breaker ──────────────────────────────────────────────
    cb_failure_threshold: int = 5
    cb_recovery_timeout_s: int = 60
    cb_half_open_calls: int = 2

    # ── Rate Limiting ────────────────────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500

    # ── Observability ────────────────────────────────────────────────
    otel_exporter_otlp_endpoint: str = "http://jaeger:4317"
    otel_service_name: str = "preauth-backend"
    prometheus_port: int = 9090

    # ── Prompt Versioning ─────────────────────────────────────────────
    active_prompt_version: str = "v1"

    # ── Caching ──────────────────────────────────────────────────────
    cache_embedding_ttl_s: int = 86400
    cache_retrieval_ttl_s: int = 3600
    cache_full_run_ttl_s: int = 300

    # ── Guardrails ───────────────────────────────────────────────────
    enable_injection_defense: bool = True
    enable_toxicity_filter: bool = True
    toxicity_threshold: float = 0.7

    # ── Worker ───────────────────────────────────────────────────────
    celery_concurrency: int = 4
    celery_max_tasks_per_child: int = 100


@lru_cache
def get_settings() -> Settings:
    """Cached singleton settings instance."""
    return Settings()
