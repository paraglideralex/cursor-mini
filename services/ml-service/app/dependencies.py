"""
FastAPI зависимости (Dependency Injection).
"""
from typing import Annotated, Any

from fastapi import Depends

from app.config import ServiceConfig
from app.exceptions import ConfigNotLoadedError, RepositoryNotFoundError
from app.repositories import Repository, RepositoryStore


# Глобальное состояние приложения
class AppState:
    """Состояние приложения (синглтон)."""
    config: ServiceConfig | None = None
    repo_store: RepositoryStore | None = None
    orchestrators: dict[str, Any] = {}  # repo_id -> Orchestrator
    
    @classmethod
    def reset(cls):
        """Сброс состояния (для тестов)."""
        cls.config = None
        cls.repo_store = None
        cls.orchestrators.clear()


def get_config() -> ServiceConfig:
    """Получить конфигурацию сервиса."""
    if AppState.config is None:
        raise ConfigNotLoadedError()
    return AppState.config


def get_repo_store() -> RepositoryStore:
    """Получить хранилище репозиториев."""
    if AppState.repo_store is None:
        raise ConfigNotLoadedError()
    return AppState.repo_store


def get_repository(repo_id: str, store: RepositoryStore = Depends(get_repo_store)) -> Repository:
    """Получить репозиторий по ID."""
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    return repo


def get_orchestrator(
    repo: Repository = Depends(get_repository),
    config: ServiceConfig = Depends(get_config),
):
    """Получить или создать orchestrator для репозитория."""
    if repo.repo_id not in AppState.orchestrators:
        from app.assistant_loader import load_orchestrator_class
        
        Orchestrator = load_orchestrator_class()
        
        legacy = config.to_legacy_config(
            repo_root=repo.path,
            storage_dir=repo.storage_dir,
        )
        
        # Переопределяем настройки репозитория
        if repo.include_extensions:
            legacy.include_extensions = repo.include_extensions
        if repo.exclude_dirs:
            legacy.exclude_dirs = repo.exclude_dirs
        legacy.max_file_size_kb = repo.max_file_size_kb
        
        legacy._validate()
        AppState.orchestrators[repo.repo_id] = Orchestrator(legacy)
    
    return AppState.orchestrators[repo.repo_id]


# Типизированные зависимости для использования в роутерах
ConfigDep = Annotated[ServiceConfig, Depends(get_config)]
RepoStoreDep = Annotated[RepositoryStore, Depends(get_repo_store)]
RepositoryDep = Annotated[Repository, Depends(get_repository)]
OrchestratorDep = Annotated[Any, Depends(get_orchestrator)]
