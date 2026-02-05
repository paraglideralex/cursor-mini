"""
Загрузка и валидация конфигурации.
"""
import json
import os
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Config:
    """Конфигурация ассистента."""
    
    # Пути
    repo_root: str
    storage_dir: str
    llm_model_path: str
    embedding_model_dir: str
    
    # Фильтрация файлов
    include_extensions: List[str]
    exclude_dirs: List[str]
    max_file_size_kb: int
    
    # Чанкинг
    chunk_size_lines: int
    chunk_overlap_lines: int
    
    # RAG параметры
    top_k: int
    max_context_chars: int
    
    # LLM параметры
    llm_ctx_size: int
    llm_max_new_tokens: int
    llm_temperature: float
    llm_seed: int
    
    # GPU параметры
    use_gpu: bool
    gpu_layers: int
    
    @staticmethod
    def load(config_path: str = ".assistant/config.json") -> "Config":
        """Загрузка конфигурации из JSON файла."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Файл конфигурации не найден: {config_path}\n"
                f"Создайте файл конфигурации по примеру из README.md"
            )
        
        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Валидация обязательных полей
        required_fields = [
            "repo_root", "storage_dir", "llm_model_path", "embedding_model_dir",
            "include_extensions", "exclude_dirs", "max_file_size_kb",
            "chunk_size_lines", "chunk_overlap_lines",
            "top_k", "max_context_chars",
            "llm_ctx_size", "llm_max_new_tokens", "llm_temperature", "llm_seed"
        ]
        
        # GPU параметры опциональные
        use_gpu = data.get("use_gpu", False)
        gpu_layers = data.get("gpu_layers", 0)
        
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise ValueError(f"В конфигурации отсутствуют обязательные поля: {missing}")
        
        # Создание объекта конфигурации
        config = Config(
            repo_root=data["repo_root"],
            storage_dir=data["storage_dir"],
            llm_model_path=data["llm_model_path"],
            embedding_model_dir=data["embedding_model_dir"],
            include_extensions=data["include_extensions"],
            exclude_dirs=data["exclude_dirs"],
            max_file_size_kb=data["max_file_size_kb"],
            chunk_size_lines=data["chunk_size_lines"],
            chunk_overlap_lines=data["chunk_overlap_lines"],
            top_k=data["top_k"],
            max_context_chars=data["max_context_chars"],
            llm_ctx_size=data["llm_ctx_size"],
            llm_max_new_tokens=data["llm_max_new_tokens"],
            llm_temperature=data["llm_temperature"],
            llm_seed=data["llm_seed"],
            use_gpu=use_gpu,
            gpu_layers=gpu_layers
        )
        
        # Валидация путей
        config._validate()
        
        return config
    
    def _validate(self) -> None:
        """Валидация конфигурации."""
        # Проверка существования репозитория
        if not os.path.isdir(self.repo_root):
            raise ValueError(f"Директория репозитория не найдена: {self.repo_root}")
        
        # Проверка существования модели LLM
        if not os.path.isfile(self.llm_model_path):
            raise FileNotFoundError(
                f"Файл модели LLM не найден: {self.llm_model_path}\n"
                f"Скачайте модель Qwen2.5-Coder 7B Instruct в формате GGUF и укажите путь в конфиге."
            )
        
        # Проверка существования директории embeddings
        if not os.path.isdir(self.embedding_model_dir):
            raise FileNotFoundError(
                f"Директория embeddings модели не найдена: {self.embedding_model_dir}\n"
                f"Скачайте мультиязычную модель embeddings и укажите путь в конфиге."
            )
        
        # Создание storage_dir если не существует
        os.makedirs(self.storage_dir, exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "docstore"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "vectorstore"), exist_ok=True)
        os.makedirs(os.path.join(self.storage_dir, "meta"), exist_ok=True)
