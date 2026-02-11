"""
Управление репозиториями.
"""
from fastapi import APIRouter

from app.dependencies import AppState, ConfigDep, RepoStoreDep
from app.exceptions import RepositoryNotFoundError
from app.schemas import RepositoryCreate, RepositoryResponse

router = APIRouter(prefix="/repositories", tags=["Repositories"])


def _to_response(repo) -> RepositoryResponse:
    """Конвертация Repository в RepositoryResponse."""
    return RepositoryResponse(
        repo_id=repo.repo_id,
        name=repo.name,
        path=repo.path,
        storage_dir=repo.storage_dir,
        include_extensions=repo.include_extensions,
        exclude_dirs=repo.exclude_dirs,
        max_file_size_kb=repo.max_file_size_kb,
        created_at=repo.created_at,
        last_indexed_at=repo.last_indexed_at,
    )


@router.post("", response_model=RepositoryResponse, status_code=201)
def create_repository(req: RepositoryCreate, config: ConfigDep, store: RepoStoreDep):
    """Создание нового репозитория."""
    repo = store.create(
        name=req.name,
        path=req.path,
        storage_root=config.storage_root,
        include_extensions=req.include_extensions or config.include_extensions,
        exclude_dirs=req.exclude_dirs or config.exclude_dirs,
        max_file_size_kb=req.max_file_size_kb,
    )
    return _to_response(repo)


@router.get("", response_model=list[RepositoryResponse])
def list_repositories(store: RepoStoreDep):
    """Список всех репозиториев."""
    return [_to_response(r) for r in store.list_all()]


@router.get("/{repo_id}", response_model=RepositoryResponse)
def get_repository(repo_id: str, store: RepoStoreDep):
    """Получение репозитория по ID."""
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    return _to_response(repo)


@router.delete("/{repo_id}", status_code=204)
def delete_repository(repo_id: str, store: RepoStoreDep):
    """Удаление репозитория."""
    if not store.delete(repo_id):
        raise RepositoryNotFoundError(repo_id)
    
    # Удалить orchestrator из кэша
    if repo_id in AppState.orchestrators:
        del AppState.orchestrators[repo_id]
    
    return None
