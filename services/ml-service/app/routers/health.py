"""
Health check эндпоинт.
"""
from fastapi import APIRouter

from app.dependencies import AppState
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
def health():
    """Проверка доступности сервиса."""
    config_loaded = AppState.config is not None
    repos_count = 0
    
    if AppState.repo_store is not None:
        repos_count = len(AppState.repo_store.list_all())
    
    return HealthResponse(
        status="ok" if config_loaded else "degraded",
        config_loaded=config_loaded,
        repositories_count=repos_count,
    )
