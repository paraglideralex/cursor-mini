"""
Инкрементальная индексация репозитория.
"""
import os
import hashlib
from typing import List, Set

from core.interfaces import Chunk, EmbeddingClient, VectorStore, DocStore
from indexing.scanner import RepoScanner
from indexing.chunker import FileChunker
from storage.meta import MetaStore


class IncrementalIndexer:
    """Инкрементальная индексация с отслеживанием изменений."""
    
    def __init__(
        self,
        scanner: RepoScanner,
        chunker: FileChunker,
        embedding_client: EmbeddingClient,
        vector_store: VectorStore,
        doc_store: DocStore,
        meta_store: MetaStore
    ):
        """
        Инициализация индексатора.
        
        Args:
            scanner: Сканер файлов
            chunker: Чанкер
            embedding_client: Клиент для эмбеддингов
            vector_store: Хранилище векторов
            doc_store: Хранилище документов
            meta_store: Хранилище метаданных
        """
        self.scanner = scanner
        self.chunker = chunker
        self.embedding_client = embedding_client
        self.vector_store = vector_store
        self.doc_store = doc_store
        self.meta_store = meta_store
    
    def index(self) -> dict:
        """
        Выполнение индексации.
        
        Returns:
            Статистика индексации
        """
        print("\n[INDEX] Начало индексации...")
        
        # Сканирование файлов
        print("[INDEX] Сканирование файлов...")
        all_files = set(self.scanner.scan())
        print(f"[INDEX] Найдено файлов: {len(all_files)}")
        
        # Определение файлов для обработки
        indexed_files = set(self.meta_store.get_all_indexed_files())
        
        files_to_process = []
        files_to_delete = []
        
        # Проверка новых и измененных файлов
        for file_path in all_files:
            if self._should_reindex(file_path):
                files_to_process.append(file_path)
        
        # Проверка удаленных файлов
        for file_path in indexed_files:
            if file_path not in all_files:
                files_to_delete.append(file_path)
        
        print(f"[INDEX] Файлов для обработки: {len(files_to_process)}")
        print(f"[INDEX] Файлов для удаления: {len(files_to_delete)}")
        
        # Удаление старых чанков
        for file_path in files_to_delete:
            self._delete_file_chunks(file_path)
        
        # Обработка файлов
        total_chunks = 0
        for i, file_path in enumerate(files_to_process, 1):
            if i % 10 == 0 or i == len(files_to_process):
                print(f"[INDEX] Обработка файла {i}/{len(files_to_process)}: {file_path}")
            
            try:
                chunks_count = self._process_file(file_path)
                total_chunks += chunks_count
            except Exception as e:
                print(f"[INDEX] Ошибка при обработке {file_path}: {e}")
        
        # Обновление времени индексации
        self.meta_store.update_index_time()
        
        stats = {
            "files_processed": len(files_to_process),
            "files_deleted": len(files_to_delete),
            "total_chunks": total_chunks,
            "total_files": len(all_files),
            "total_indexed_chunks": self.doc_store.count()
        }
        
        print(f"[INDEX] Индексация завершена!")
        print(f"[INDEX] Обработано файлов: {stats['files_processed']}")
        print(f"[INDEX] Удалено файлов: {stats['files_deleted']}")
        print(f"[INDEX] Создано чанков: {stats['total_chunks']}")
        print(f"[INDEX] Всего чанков в индексе: {stats['total_indexed_chunks']}")
        
        return stats
    
    def _should_reindex(self, file_path: str) -> bool:
        """
        Проверка, нужно ли переиндексировать файл.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            True если нужно переиндексировать
        """
        meta = self.meta_store.get_file_meta(file_path)
        
        if meta is None:
            # Файл новый
            return True
        
        # Проверка mtime
        current_mtime = self.scanner.get_file_mtime(file_path)
        if current_mtime != meta.get("mtime"):
            return True
        
        return False
    
    def _process_file(self, file_path: str) -> int:
        """
        Обработка файла: чанкинг и создание эмбеддингов.
        
        Args:
            file_path: Путь к файлу
        
        Returns:
            Количество созданных чанков
        """
        # Удаление старых чанков для этого файла
        self._delete_file_chunks(file_path)
        
        # Чтение файла
        content = self.scanner.read_file(file_path)
        if not content:
            return 0
        
        # Получение mtime
        mtime = self.scanner.get_file_mtime(file_path)
        
        # Чанкинг
        chunks = self.chunker.chunk_file(file_path, content, mtime)
        
        if not chunks:
            return 0
        
        # Создание эмбеддингов
        chunk_contents = [chunk.content for chunk in chunks]
        embeddings = self.embedding_client.embed_texts(chunk_contents)
        
        # Сохранение чанков и векторов
        chunk_ids = [chunk.chunk_id for chunk in chunks]
        
        for chunk in chunks:
            self.doc_store.put_chunk(chunk)
        
        self.vector_store.upsert(chunk_ids, embeddings)
        
        # Обновление метаданных файла
        file_hash = self._compute_file_hash(content)
        self.meta_store.set_file_meta(file_path, mtime, file_hash)
        
        return len(chunks)
    
    def _delete_file_chunks(self, file_path: str) -> None:
        """
        Удаление всех чанков файла.
        
        Args:
            file_path: Путь к файлу
        """
        # Получение всех чанков файла
        all_chunks = self.doc_store.get_all_chunks()
        chunk_ids = [chunk.chunk_id for chunk in all_chunks if chunk.path == file_path]
        
        if chunk_ids:
            # Удаление из vector store
            self.vector_store.delete(chunk_ids)
            
            # Удаление из doc store
            self.doc_store.delete_chunks_by_path(file_path)
        
        # Удаление метаданных файла
        self.meta_store.delete_file_meta(file_path)
    
    @staticmethod
    def _compute_file_hash(content: str) -> str:
        """
        Вычисление хеша файла.
        
        Args:
            content: Содержимое файла
        
        Returns:
            Хеш строка
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
