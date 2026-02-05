"""
Базовые интерфейсы для всех компонентов системы.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Chunk:
    """Представление чанка документа."""
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    content: str
    hash_value: str
    mtime: float


@dataclass
class RetrievalResult:
    """Результат поиска релевантных чанков."""
    chunk_id: str
    path: str
    start_line: int
    end_line: int
    content: str
    score: float


class LLMClient(ABC):
    """Интерфейс для генеративной модели."""
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        seed: int,
        progress_callback: Optional[callable] = None
    ) -> str:
        """
        Генерация текста по промпту.
        
        Args:
            prompt: Промпт для генерации
            max_new_tokens: Максимальное количество новых токенов
            temperature: Температура генерации
            seed: Seed для воспроизводимости
            progress_callback: Опциональный callback для обновления прогресса
        
        Returns:
            Сгенерированный текст
        """
        pass


class EmbeddingClient(ABC):
    """Интерфейс для создания эмбеддингов."""
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Создание эмбеддингов для списка текстов."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Размерность эмбеддинга."""
        pass


class VectorStore(ABC):
    """Интерфейс для хранения и поиска векторов."""
    
    @abstractmethod
    def upsert(self, chunk_ids: List[str], vectors: List[List[float]]) -> None:
        """Добавление или обновление векторов."""
        pass
    
    @abstractmethod
    def query_top_k(self, query_vector: List[float], k: int) -> List[Tuple[str, float]]:
        """Поиск top-K ближайших векторов. Возвращает (chunk_id, distance)."""
        pass
    
    @abstractmethod
    def delete(self, chunk_ids: List[str]) -> None:
        """Удаление векторов."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Количество векторов в хранилище."""
        pass


class DocStore(ABC):
    """Интерфейс для хранения чанков и их метаданных."""
    
    @abstractmethod
    def put_chunk(self, chunk: Chunk) -> None:
        """Сохранение чанка."""
        pass
    
    @abstractmethod
    def get_chunk(self, chunk_id: str) -> Optional[Chunk]:
        """Получение чанка по ID."""
        pass
    
    @abstractmethod
    def list_chunks_by_ids(self, chunk_ids: List[str]) -> List[Chunk]:
        """Получение списка чанков по ID."""
        pass
    
    @abstractmethod
    def get_all_chunks(self) -> List[Chunk]:
        """Получение всех чанков."""
        pass
    
    @abstractmethod
    def delete_chunks_by_path(self, path: str) -> None:
        """Удаление всех чанков для файла."""
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Количество чанков в хранилище."""
        pass
