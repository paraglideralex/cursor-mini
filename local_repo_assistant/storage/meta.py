"""
Хранилище метаинформации об индексации.
"""
import os
import json
from typing import Optional
from datetime import datetime


class MetaStore:
    """Хранилище метаинформации об индексации."""
    
    def __init__(self, storage_path: str):
        """
        Инициализация meta store.
        
        Args:
            storage_path: Путь к директории для хранения метаданных
        """
        self.storage_path = storage_path
        self.meta_file = os.path.join(storage_path, "indexing_meta.json")
        self.file_meta: dict[str, dict] = {}
        self.last_index_time: Optional[str] = None
        
        # Загрузка существующих метаданных
        if os.path.exists(self.meta_file):
            self._load()
    
    def get_file_meta(self, path: str) -> Optional[dict]:
        """
        Получение метаданных файла.
        
        Args:
            path: Путь к файлу
        
        Returns:
            Словарь с метаданными или None
        """
        return self.file_meta.get(path)
    
    def set_file_meta(self, path: str, mtime: float, hash_value: str) -> None:
        """
        Установка метаданных файла.
        
        Args:
            path: Путь к файлу
            mtime: Время модификации
            hash_value: Хеш файла
        """
        self.file_meta[path] = {
            "mtime": mtime,
            "hash_value": hash_value
        }
        self._save()
    
    def delete_file_meta(self, path: str) -> None:
        """
        Удаление метаданных файла.
        
        Args:
            path: Путь к файлу
        """
        if path in self.file_meta:
            del self.file_meta[path]
            self._save()
    
    def update_index_time(self) -> None:
        """Обновление времени последней индексации."""
        self.last_index_time = datetime.now().isoformat()
        self._save()
    
    def get_last_index_time(self) -> Optional[str]:
        """
        Получение времени последней индексации.
        
        Returns:
            ISO строка времени или None
        """
        return self.last_index_time
    
    def get_all_indexed_files(self) -> list[str]:
        """
        Получение списка всех проиндексированных файлов.
        
        Returns:
            Список путей к файлам
        """
        return list(self.file_meta.keys())
    
    def _save(self) -> None:
        """Сохранение метаданных на диск."""
        data = {
            "file_meta": self.file_meta,
            "last_index_time": self.last_index_time
        }
        with open(self.meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _load(self) -> None:
        """Загрузка метаданных с диска."""
        with open(self.meta_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.file_meta = data.get("file_meta", {})
            self.last_index_time = data.get("last_index_time")
