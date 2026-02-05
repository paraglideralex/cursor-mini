"""
Клиент для создания эмбеддингов.
"""
from typing import List
import sys

from core.interfaces import EmbeddingClient


class LocalSentenceTransformerClient(EmbeddingClient):
    """
    Клиент для создания эмбеддингов через sentence-transformers.
    Работает строго в offline режиме с локальными моделями.
    """
    
    def __init__(self, model_dir: str, use_gpu: bool = False):
        """
        Инициализация клиента.
        
        Args:
            model_dir: Путь к директории с локальной моделью embeddings
            use_gpu: Использовать ли GPU для embeddings
        """
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            raise ImportError(
                "Библиотека sentence-transformers не установлена.\n"
                "Установите: pip install sentence-transformers"
            )
        
        print(f"[EMBEDDINGS] Загрузка модели из {model_dir}...")
        
        # Определение устройства с проверкой доступности CUDA
        if use_gpu:
            try:
                import torch
                if torch.cuda.is_available():
                    device = "cuda"
                    print(f"[EMBEDDINGS] Устройство: cuda (GPU)")
                else:
                    device = "cpu"
                    print(f"[EMBEDDINGS] ⚠️  GPU запрошен, но CUDA недоступна. Используется CPU.")
                    print(f"[EMBEDDINGS] Установите PyTorch с CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu121")
            except ImportError:
                device = "cpu"
                print(f"[EMBEDDINGS] ⚠️  PyTorch не установлен. Используется CPU.")
        else:
            device = "cpu"
            print(f"[EMBEDDINGS] Устройство: cpu")
        
        try:
            self.model = SentenceTransformer(
                model_dir,
                device=device,
                trust_remote_code=False  # Безопасность
            )
            self._dimension = self.model.get_sentence_embedding_dimension()
            print(f"[EMBEDDINGS] Модель загружена, размерность: {self._dimension}")
        except Exception as e:
            raise RuntimeError(
                f"Ошибка загрузки embeddings модели: {e}\n"
                f"Убедитесь, что модель скачана локально и переменные окружения установлены:\n"
                f"  TRANSFORMERS_OFFLINE=1\n"
                f"  HF_HUB_OFFLINE=1"
            )
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Создание эмбеддингов для списка текстов.
        
        Args:
            texts: Список текстов для эмбеддинга
        
        Returns:
            Список векторов эмбеддингов
        """
        if not texts:
            return []
        
        try:
            # Конвертация в numpy array, затем в список
            embeddings = self.model.encode(
                texts,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # Нормализация для косинусного сходства
            )
            
            # Конвертация в список списков
            return embeddings.tolist()
            
        except Exception as e:
            raise RuntimeError(f"Ошибка создания эмбеддингов: {e}")
    
    def get_dimension(self) -> int:
        """Возвращает размерность эмбеддинга."""
        return self._dimension
