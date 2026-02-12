"""
Индексация репозиториев.
"""
from fastapi import APIRouter

from app.dependencies import ConfigDep, RepoStoreDep
from app.exceptions import JobNotFoundError, RepositoryNotFoundError
from app.jobs import get_job_status, start_index_job
from app.schemas import IndexStartResponse, IndexStatusResponse

router = APIRouter(prefix="/repositories/{repo_id}/index", tags=["Indexing"])


@router.post("/start", response_model=IndexStartResponse)
def index_start(repo_id: str, config: ConfigDep, store: RepoStoreDep):
    """Запуск фоновой индексации для репозитория."""
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    
    # Callback для обновления времени индексации
    def on_complete(rid: str):
        store.update_last_indexed(rid)
    
    job_id = start_index_job(config, repo, on_complete=on_complete)
    
    return IndexStartResponse(
        job_id=job_id,
        repo_id=repo_id,
        message=f"Индексация запущена: {repo.name}",
    )


@router.get("/{job_id}/status", response_model=IndexStatusResponse)
def index_status(repo_id: str, job_id: str):
    """Статус задачи индексации."""
    status = get_job_status(job_id)
    if status is None:
        raise JobNotFoundError(job_id)
    
    return IndexStatusResponse(
        job_id=status.job_id,
        status=status.status,
        progress=status.progress,
        message=status.message,
        stats=status.stats,
        error=status.error,
    )
