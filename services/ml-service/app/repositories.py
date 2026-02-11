"""
Управление репозиториями.
"""
import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class Repository:
    """Метаданные репозитория."""
    repo_id: str
    name: str
    path: str  # Абсолютный путь к репозиторию
    storage_dir: str  # Абсолютный путь к директории хранения индекса
    
    # Настройки (могут переопределять глобальные)
    include_extensions: list[str] = field(default_factory=list)
    exclude_dirs: list[str] = field(default_factory=list)
    max_file_size_kb: int = 500
    
    created_at: str = ""
    last_indexed_at: str | None = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()


class RepositoryStore:
    """Хранилище репозиториев (in-memory + JSON для персистентности)."""
    
    def __init__(self, storage_file: str):
        self.storage_file = storage_file
        self._repos: dict[str, Repository] = {}
        self._lock = threading.Lock()
        self._load()
    
    def _load(self):
        """Загрузка из JSON."""
        if not os.path.exists(self.storage_file):
            return
        with open(self.storage_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        with self._lock:
            for repo_data in data.get("repositories", []):
                repo = Repository(**repo_data)
                self._repos[repo.repo_id] = repo
    
    def _save(self):
        """Сохранение в JSON."""
        os.makedirs(os.path.dirname(self.storage_file), exist_ok=True)
        with self._lock:
            data = {"repositories": [asdict(r) for r in self._repos.values()]}
        with open(self.storage_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def create(
        self,
        name: str,
        path: str,
        storage_root: str,
        include_extensions: list[str] | None = None,
        exclude_dirs: list[str] | None = None,
        max_file_size_kb: int = 500,
    ) -> Repository:
        """Создание нового репозитория."""
        path = os.path.abspath(path)
        if not os.path.isdir(path):
            raise ValueError(f"Путь не существует или не является директорией: {path}")
        
        repo_id = str(uuid.uuid4())
        storage_dir = os.path.join(storage_root, repo_id)
        
        repo = Repository(
            repo_id=repo_id,
            name=name,
            path=path,
            storage_dir=storage_dir,
            include_extensions=include_extensions or [],
            exclude_dirs=exclude_dirs or [],
            max_file_size_kb=max_file_size_kb,
        )
        
        with self._lock:
            self._repos[repo_id] = repo
        self._save()
        return repo
    
    def get(self, repo_id: str) -> Repository | None:
        """Получение репозитория по ID."""
        with self._lock:
            return self._repos.get(repo_id)
    
    def list_all(self) -> list[Repository]:
        """Список всех репозиториев."""
        with self._lock:
            return list(self._repos.values())
    
    def delete(self, repo_id: str) -> bool:
        """Удаление репозитория."""
        with self._lock:
            if repo_id not in self._repos:
                return False
            del self._repos[repo_id]
        self._save()
        return True
    
    def update_last_indexed(self, repo_id: str) -> None:
        """Обновление времени последней индексации."""
        with self._lock:
            if repo_id in self._repos:
                self._repos[repo_id].last_indexed_at = datetime.now().isoformat()
        self._save()
