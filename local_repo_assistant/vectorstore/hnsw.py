"""
Vector store на основе hnswlib.
"""
import os
import pickle
from typing import List, Tuple, Dict

from core.interfaces import VectorStore


class HnswVectorStore(VectorStore):
    """Vector store на основе hnswlib для быстрого ANN поиска."""
    
    def __init__(self, storage_path: str, dimension: int):
        """
        Инициализация vector store.
        
        Args:
            storage_path: Путь к директории для хранения индекса
            dimension: Размерность векторов
        """
        try:
            import hnswlib
        except ImportError:
            raise ImportError(
                "Библиотека hnswlib не установлена.\n"
                "Установите: pip install hnswlib"
            )
        
        self.storage_path = storage_path
        self.dimension = dimension
        self.index_path = os.path.join(storage_path, "hnsw_index.bin")
        self.mapping_path = os.path.join(storage_path, "id_mapping.pkl")
        
        self.index = hnswlib.Index(space='cosine', dim=dimension)
        self.chunk_id_to_idx: Dict[str, int] = {}
        self.idx_to_chunk_id: Dict[int, str] = {}
        self.next_idx = 0
        
        # Загрузка существующего индекса
        if os.path.exists(self.index_path):
            self._load()
        else:
            # Инициализация нового индекса
            self.index.init_index(
                max_elements=100000,  # Начальный размер
                ef_construction=200,
                M=16
            )
            self.index.set_ef(50)  # ef для поиска
    
    def upsert(self, chunk_ids: List[str], vectors: List[List[float]]) -> None:
        """
        Добавление или обновление векторов.
        
        Args:
            chunk_ids: Список ID чанков
            vectors: Список векторов
        """
        if len(chunk_ids) != len(vectors):
            raise ValueError("Количество chunk_ids и vectors должно совпадать")
        
        import numpy as np
        
        for chunk_id, vector in zip(chunk_ids, vectors):
            # Если chunk_id уже существует, удаляем старый вектор
            if chunk_id in self.chunk_id_to_idx:
                # В hnswlib нет прямого удаления, просто перезаписываем
                idx = self.chunk_id_to_idx[chunk_id]
            else:
                # Новый chunk_id
                idx = self.next_idx
                self.chunk_id_to_idx[chunk_id] = idx
                self.idx_to_chunk_id[idx] = chunk_id
                self.next_idx += 1
            
            # Добавление вектора
            vector_np = np.array(vector, dtype=np.float32)
            self.index.add_items(vector_np, idx)
        
        # Сохранение после upsert
        self._save()
    
    def query_top_k(self, query_vector: List[float], k: int) -> List[Tuple[str, float]]:
        """
        Поиск top-K ближайших векторов.
        
        Args:
            query_vector: Вектор запроса
            k: Количество результатов
        
        Returns:
            Список кортежей (chunk_id, distance)
        """
        import numpy as np
        
        if self.index.get_current_count() == 0:
            return []
        
        # Ограничиваем k размером индекса
        k = min(k, self.index.get_current_count())
        
        query_np = np.array(query_vector, dtype=np.float32)
        labels, distances = self.index.knn_query(query_np, k=k)
        
        results = []
        for label, distance in zip(labels[0], distances[0]):
            if int(label) in self.idx_to_chunk_id:
                chunk_id = self.idx_to_chunk_id[int(label)]
                results.append((chunk_id, float(distance)))
        
        return results
    
    def delete(self, chunk_ids: List[str]) -> None:
        """
        Удаление векторов.
        
        Note: hnswlib не поддерживает прямое удаление.
        При необходимости нужна пересборка индекса.
        """
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_id_to_idx:
                idx = self.chunk_id_to_idx[chunk_id]
                del self.chunk_id_to_idx[chunk_id]
                del self.idx_to_chunk_id[idx]
        
        # Для полного удаления требуется пересборка индекса
        # Это можно оптимизировать в будущем
    
    def count(self) -> int:
        """Количество векторов в хранилище."""
        return len(self.chunk_id_to_idx)
    
    def _save(self) -> None:
        """Сохранение индекса на диск."""
        self.index.save_index(self.index_path)
        
        with open(self.mapping_path, "wb") as f:
            pickle.dump({
                "chunk_id_to_idx": self.chunk_id_to_idx,
                "idx_to_chunk_id": self.idx_to_chunk_id,
                "next_idx": self.next_idx
            }, f)
    
    def _load(self) -> None:
        """Загрузка индекса с диска."""
        self.index.load_index(self.index_path, max_elements=100000)
        self.index.set_ef(50)
        
        with open(self.mapping_path, "rb") as f:
            data = pickle.load(f)
            self.chunk_id_to_idx = data["chunk_id_to_idx"]
            self.idx_to_chunk_id = data["idx_to_chunk_id"]
            self.next_idx = data["next_idx"]
