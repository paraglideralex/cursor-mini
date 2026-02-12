"""
Pydantic схемы для API.
"""
from typing import Any

from pydantic import BaseModel, Field, field_validator


# --- Repository ---

class RepositoryCreate(BaseModel):
    """Запрос на создание репозитория."""
    name: str = Field(..., min_length=1, max_length=255, description="Название репозитория")
    path: str = Field(..., min_length=1, description="Путь к репозиторию")
    include_extensions: list[str] | None = Field(
        default=None, 
        description="Расширения файлов для индексации (например, ['.cs', '.py'])"
    )
    exclude_dirs: list[str] | None = Field(
        default=None,
        description="Директории для исключения (например, ['bin', 'obj'])"
    )
    max_file_size_kb: int = Field(default=500, ge=1, le=10000, description="Максимальный размер файла в КБ")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        return v.strip()

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: str) -> str:
        return v.strip()


class RepositoryResponse(BaseModel):
    """Ответ с данными репозитория."""
    repo_id: str
    name: str
    path: str
    storage_dir: str
    include_extensions: list[str]
    exclude_dirs: list[str]
    max_file_size_kb: int
    created_at: str
    last_indexed_at: str | None = None

    class Config:
        from_attributes = True


# --- Indexing ---

class IndexStartResponse(BaseModel):
    """Ответ на запуск индексации."""
    job_id: str
    repo_id: str
    message: str = "Индексация запущена"


class IndexStatusResponse(BaseModel):
    """Статус задачи индексации."""
    job_id: str
    status: str = Field(..., description="queued | running | completed | failed")
    progress: int = Field(..., ge=0, le=100, description="Прогресс 0-100%")
    message: str
    stats: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


# --- Query ---

class Citation(BaseModel):
    """Источник (цитата из кода)."""
    path: str
    start_line: int
    end_line: int
    score: float = Field(..., ge=0, le=1, description="Релевантность 0-1")
    preview: str = ""


class QueryRequest(BaseModel):
    """Запрос по коду."""
    question: str = Field(..., min_length=1, max_length=10000, description="Вопрос по коду")
    top_k: int | None = Field(default=None, ge=1, le=50, description="Количество фрагментов для контекста")
    max_new_tokens: int | None = Field(default=None, ge=1, le=4096, description="Максимум токенов в ответе")
    temperature: float | None = Field(default=None, ge=0, le=2, description="Температура генерации")

    @field_validator("question")
    @classmethod
    def validate_question(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Вопрос не может быть пустым")
        return v


class QueryResponse(BaseModel):
    """Ответ на запрос по коду."""
    answer: str
    sources: list[Citation]
    timings: dict[str, float] = Field(
        ..., 
        description="Временные метрики: retrieval_sec, generation_sec, total_sec"
    )


class QueryStreamEvent(BaseModel):
    """Событие стриминга ответа."""
    type: str = Field(..., description="token | done | error")
    text: str | None = None
    answer: str | None = None
    sources: list[dict] | None = None
    message: str | None = None


# --- Health ---

class HealthResponse(BaseModel):
    """Ответ проверки здоровья сервиса."""
    status: str
    config_loaded: bool
    repositories_count: int
    version: str = "0.1.0"
