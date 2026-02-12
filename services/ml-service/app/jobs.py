"""
Фоновые задачи индексации.
"""
import logging
import sys
import threading
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Настройка путей перед импортами (если еще не настроено)
_current_file = Path(__file__).resolve()
_ml_service_dir = _current_file.parent.parent  # services/ml-service
_repo_root = _ml_service_dir.parent.parent  # cursor-mini
_assistant_path = _repo_root / "local_repo_assistant"

if str(_ml_service_dir) not in sys.path:
    sys.path.insert(0, str(_ml_service_dir))
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))
if str(_assistant_path) not in sys.path:
    sys.path.insert(0, str(_assistant_path))

# Теперь можно использовать абсолютные импорты
from app.config import ServiceConfig
from app.context import _ASSISTANT_PATH, _REPO_ROOT
from app.repositories import Repository

logger = logging.getLogger(__name__)

# Глобальное хранилище статусов задач
_jobs: dict[str, dict[str, Any]] = {}
_jobs_lock = threading.Lock()


@dataclass
class JobStatus:
    """Статус задачи индексации."""
    job_id: str
    status: str  # queued | running | completed | failed
    progress: int  # 0-100
    message: str = ""
    stats: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


def _run_index(config: ServiceConfig, repo: Repository) -> dict[str, Any]:
    """Выполнение индексации через local_repo_assistant."""
    from app.assistant_loader import load_orchestrator_class
    
    Orchestrator = load_orchestrator_class()
    
    legacy = config.to_legacy_config(
        repo_root=repo.path,
        storage_dir=repo.storage_dir,
    )
    
    # Переопределяем настройки репозитория, если заданы
    if repo.include_extensions:
        legacy.include_extensions = repo.include_extensions
    if repo.exclude_dirs:
        legacy.exclude_dirs = repo.exclude_dirs
    legacy.max_file_size_kb = repo.max_file_size_kb
    
    legacy._validate()
    orch = Orchestrator(legacy)
    stats = orch.indexer.index()
    return stats


def start_index_job(config: ServiceConfig, repo: Repository, on_complete=None) -> str:
    """Запуск фоновой задачи индексации. Возвращает job_id."""
    job_id = str(uuid.uuid4())
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "queued",
            "progress": 0,
            "message": "В очереди",
            "stats": {},
            "error": None,
        }

    def run():
        with _jobs_lock:
            _jobs[job_id]["status"] = "running"
            _jobs[job_id]["progress"] = 0
            _jobs[job_id]["message"] = f"Индексация начата: {repo.name}"
        try:
            stats = _run_index(config, repo)
            with _jobs_lock:
                _jobs[job_id]["status"] = "completed"
                _jobs[job_id]["progress"] = 100
                _jobs[job_id]["message"] = "Индексация завершена"
                _jobs[job_id]["stats"] = stats
            
            # Callback после успешной индексации
            if on_complete:
                on_complete(repo.repo_id)
        except Exception as e:
            logger.exception("Ошибка индексации для %s", repo.repo_id)
            with _jobs_lock:
                _jobs[job_id]["status"] = "failed"
                _jobs[job_id]["progress"] = 0
                _jobs[job_id]["message"] = str(e)
                _jobs[job_id]["error"] = str(e)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    return job_id


def get_job_status(job_id: str) -> JobStatus | None:
    """Получение статуса задачи."""
    with _jobs_lock:
        data = _jobs.get(job_id)
    if not data:
        return None
    return JobStatus(
        job_id=job_id,
        status=data["status"],
        progress=data["progress"],
        message=data["message"],
        stats=data.get("stats", {}),
        error=data.get("error"),
    )
