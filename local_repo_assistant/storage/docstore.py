"""
Хранилище документов (чанков).
"""
import os
import json
from typing import Optional, List

from core.interfaces import DocStore, Chunk


class JsonDocStore(DocStore):
    """DocStore на основе JSON файлов."""
    
    def __init__(self, storage_path: str):
        """
        Инициализация docstore.
        
        Args:
            storage_path: Путь к директории для хранения чанков
        """
        self.storage_path = storage_path
        self.chunks_file = os.path.join(storage_path, "chunks.json")
        self.chunks: dict[str, dict] = {}
        
        # Загрузка существующих чанков
        if os.path.exists(self.chunks_file):
            self._load()
    
    def put_chunk(self, chunk: Chunk) -> None:
        """
        Сохранение чанка.
        
        Args:
            chunk: Объект чанка для сохранения
        """
        self.chunks[chunk.chunk_id] = {
            "chunk_id": chunk.chunk_id,
            "path": chunk.path,
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "content": chunk.content,
            "hash_value": chunk.hash_value,
            "mtime": chunk.mtime
        }
        self._save()
    
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """
        Получение чанка по ID.
        
        Args:
            chunk_id: ID чанка
        
        Returns:
            Объект Chunk или None
        """
        if chunk_id not in self.chunks:
            return None
        
        data = self.chunks[chunk_id]
        return Chunk(
            chunk_id=data["chunk_id"],
            path=data["path"],
            start_line=data["start_line"],
            end_line=data["end_line"],
            content=data["content"],
            hash_value=data["hash_value"],
            mtime=data["mtime"]
        )
    
    def list_chunks_by_ids(self, chunk_ids: List[str]) -> List[Chunk]:
        """
        Получение списка чанков по ID.
        
        Args:
            chunk_ids: Список ID чанков
        
        Returns:
            Список объектов Chunk
        """
        result = []
        for chunk_id in chunk_ids:
            chunk = self.get_chunk(chunk_id)
            if chunk:
                result.append(chunk)
        return result
    
    def get_all_chunks(self) -> List[Chunk]:
        """
        Получение всех чанков.
        
        Returns:
            Список всех чанков
        """
        return [self.get_chunk(chunk_id) for chunk_id in self.chunks.keys()]
    
    def delete_chunks_by_path(self, path: str) -> None:
        """
        Удаление всех чанков для файла.
        
        Args:
            path: Путь к файлу
        """
        to_delete = [
            chunk_id for chunk_id, data in self.chunks.items()
            if data["path"] == path
        ]
        
        for chunk_id in to_delete:
            del self.chunks[chunk_id]
        
        if to_delete:
            self._save()
    
    def count(self) -> int:
        """
        Количество чанков в хранилище.
        
        Returns:
            Количество чанков
        """
        return len(self.chunks)
    
    def _save(self) -> None:
        """Сохранение чанков на диск."""
        with open(self.chunks_file, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
    
    def _load(self) -> None:
        """Загрузка чанков с диска."""
        with open(self.chunks_file, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)
