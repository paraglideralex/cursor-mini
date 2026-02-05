"""
Поиск релевантных чанков.
"""
from typing import List

from core.interfaces import EmbeddingClient, VectorStore, DocStore, RetrievalResult


class Retriever:
    """Поиск релевантных чанков по запросу."""
    
    def __init__(
        self,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        doc_store: DocStore,
        top_k: int
    ):
        """
        Инициализация ретривера.
        
        Args:
            embedding_client: Клиент для эмбеддингов
            vector_store: Хранилище векторов
            doc_store: Хранилище документов
            top_k: Количество результатов
        """
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.top_k = top_k
    
    def retrieve(self, query: str) -> List[RetrievalResult]:
        """
        Поиск релевантных чанков.
        
        Args:
            query: Запрос пользователя
        
        Returns:
            Список релевантных чанков
        """
        # Создание эмбеддинга запроса
        query_embedding = self.embedding_client.embed_texts([query])[0]
        
        # Поиск ближайших векторов
        search_results = self.vector_store.query_top_k(query_embedding, self.top_k)
        
        if not search_results:
            return []
        
        # Получение чанков
        chunk_ids = [chunk_id for chunk_id, _ in search_results]
        chunks = self.doc_store.list_chunks_by_ids(chunk_ids)
        
        # Создание результатов с сохранением score
        chunk_id_to_score = {chunk_id: score for chunk_id, score in search_results}
        
        results = []
        for chunk in chunks:
            score = chunk_id_to_score.get(chunk.chunk_id, 1.0)
            
            result = RetrievalResult(
                chunk_id=chunk.chunk_id,
                path=chunk.path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                content=chunk.content,
                score=score
            )
            results.append(result)
        
        # Сортировка по score (меньше = лучше для cosine distance)
        results.sort(key=lambda r: r.score)
        
        return results
