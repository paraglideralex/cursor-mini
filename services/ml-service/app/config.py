"""
Конфигурация ML Service.
Читает из переменных окружения и/или config.json.
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class ServiceConfig:
    """Конфигурация ML Service (общие настройки, без конкретного репозитория)."""
    
    # Модели
    llm_model_path: str
    embedding_model_dir: str
    
    # Хранилище (базовая директория для всех репозиториев)
    storage_root: str
    
    # Фильтрация файлов
    include_extensions: List[str]
    exclude_dirs: List[str]
    max_file_size_kb: int
    
    # Чанкинг
    chunk_size_lines: int
    chunk_overlap_lines: int
    
    # RAG
    top_k: int
    max_context_chars: int
    
    # LLM
    llm_ctx_size: int
    llm_max_new_tokens: int
    llm_temperature: float
    llm_seed: int
    
    # GPU
    use_gpu: bool
    gpu_layers: int
    
    @classmethod
    def load(cls, config_path: str | None = None) -> "ServiceConfig":
        """Загрузка из env + config.json."""
        path = config_path or os.environ.get("CODELENS_CONFIG", ".assistant/config.json")
        path = Path(path)
        
        if not path.is_absolute():
            # Корень CodeLens (parent of services/ml-service/app)
            root = Path(__file__).resolve().parent.parent.parent.parent
            path = root / path
        
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(f"Конфиг не найден: {path}")
        
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # env переопределяет config
        llm_model_path = os.environ.get("CODELENS_LLM_MODEL") or data["llm_model_path"]
        embedding_model_dir = os.environ.get("CODELENS_EMBEDDING_MODEL") or data["embedding_model_dir"]
        storage_root = os.environ.get("CODELENS_STORAGE_ROOT") or data.get("storage_root", ".codelens_storage")
        
        # Абсолютные пути относительно корня CodeLens
        base = path.parent.parent if "assistant" in str(path) else path.parent
        def resolve(p: str) -> str:
            if not p or os.path.isabs(p):
                return p
            return str(Path(base) / p)
        
        return cls(
            llm_model_path=resolve(llm_model_path),
            embedding_model_dir=resolve(embedding_model_dir),
            storage_root=resolve(storage_root),
            include_extensions=data.get("include_extensions", [".cs", ".py", ".js", ".ts"]),
            exclude_dirs=data.get("exclude_dirs", ["bin", "obj", "node_modules", ".git"]),
            max_file_size_kb=data.get("max_file_size_kb", 500),
            chunk_size_lines=data.get("chunk_size_lines", 250),
            chunk_overlap_lines=data.get("chunk_overlap_lines", 30),
            top_k=data.get("top_k", 12),
            max_context_chars=data.get("max_context_chars", 60000),
            llm_ctx_size=data.get("llm_ctx_size", 8192),
            llm_max_new_tokens=data.get("llm_max_new_tokens", 700),
            llm_temperature=data.get("llm_temperature", 0.2),
            llm_seed=data.get("llm_seed", 42),
            use_gpu=data.get("use_gpu", False),
            gpu_layers=data.get("gpu_layers", 0),
        )
    
    def to_legacy_config(self, repo_root: str, storage_dir: str) -> "LegacyConfig":
        """Преобразование в формат local_repo_assistant.app.config.Config для конкретного репозитория."""
        return LegacyConfig(
            repo_root=repo_root,
            storage_dir=storage_dir,
            llm_model_path=self.llm_model_path,
            embedding_model_dir=self.embedding_model_dir,
            include_extensions=self.include_extensions,
            exclude_dirs=self.exclude_dirs,
            max_file_size_kb=self.max_file_size_kb,
            chunk_size_lines=self.chunk_size_lines,
            chunk_overlap_lines=self.chunk_overlap_lines,
            top_k=self.top_k,
            max_context_chars=self.max_context_chars,
            llm_ctx_size=self.llm_ctx_size,
            llm_max_new_tokens=self.llm_max_new_tokens,
            llm_temperature=self.llm_temperature,
            llm_seed=self.llm_seed,
            use_gpu=self.use_gpu,
            gpu_layers=self.gpu_layers,
        )


class LegacyConfig:
    """Совместимость с Config из local_repo_assistant."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
    
    def _validate(self) -> None:
        """Создание директорий storage."""
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "docstore"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "vectorstore"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "meta"), exist_ok=True)
