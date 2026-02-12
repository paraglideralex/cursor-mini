"""
Запросы по коду (RAG).
"""
from typing import Any

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.dependencies import ConfigDep, RepoStoreDep, get_config, get_repo_store
from app.exceptions import RepositoryNotFoundError
from app.schemas import QueryRequest, QueryResponse
from app.services.query_service import QueryService

router = APIRouter(prefix="/repositories/{repo_id}/query", tags=["Query"])


def _get_orchestrator_for_repo(repo_id: str) -> Any:
    """Получить orchestrator для репозитория (вручную, без Depends цепочки)."""
    from app.dependencies import AppState, get_config
    from app.assistant_loader import load_orchestrator_class
    
    store = get_repo_store()
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    
    config = get_config()
    
    if repo.repo_id not in AppState.orchestrators:
        Orchestrator = load_orchestrator_class()
        
        legacy = config.to_legacy_config(
            repo_root=repo.path,
            storage_dir=repo.storage_dir,
        )
        
        if repo.include_extensions:
            legacy.include_extensions = repo.include_extensions
        if repo.exclude_dirs:
            legacy.exclude_dirs = repo.exclude_dirs
        legacy.max_file_size_kb = repo.max_file_size_kb
        
        legacy._validate()
        AppState.orchestrators[repo.repo_id] = Orchestrator(legacy)
    
    return AppState.orchestrators[repo.repo_id]


@router.post("", response_model=QueryResponse)
def query(repo_id: str, req: QueryRequest, config: ConfigDep, store: RepoStoreDep):
    """Вопрос по коду (RAG) для конкретного репозитория."""
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    
    orch = _get_orchestrator_for_repo(repo_id)
    
    result = QueryService.execute(
        orchestrator=orch,
        config=config,
        question=req.question,
        top_k=req.top_k,
        max_new_tokens=req.max_new_tokens,
        temperature=req.temperature,
    )
    
    return QueryResponse(
        answer=result.answer,
        sources=result.sources,
        timings=result.timings,
    )


@router.get("/stream")
def query_stream(repo_id: str, question: str, config: ConfigDep, store: RepoStoreDep):
    """Стриминг ответа (SSE) для конкретного репозитория."""
    repo = store.get(repo_id)
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
    
    if not question.strip():
        from app.exceptions import QueryError
        raise QueryError("Вопрос не может быть пустым")
    
    orch = _get_orchestrator_for_repo(repo_id)
    
    return StreamingResponse(
        QueryService.execute_stream(orch, config, question.strip()),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
