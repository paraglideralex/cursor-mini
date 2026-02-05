"""
Оркестратор - главный координатор всех компонентов системы.
"""
from typing import Optional

from app.config import Config
from app.security import enforce_offline_mode, validate_no_network_access

from core.interfaces import LLMClient, EmbeddingClient, VectorStore, DocStore

from llm.client import LocalLlamaCppClient
from embeddings.client import LocalSentenceTransformerClient

from vectorstore.hnsw import HnswVectorStore
from storage.docstore import JsonDocStore
from storage.meta import MetaStore

from indexing.scanner import RepoScanner
from indexing.chunker import FileChunker
from indexing.incremental import IncrementalIndexer

from retrieval.retrieve import Retriever
from retrieval.context_builder import ContextBuilder
from retrieval.citations import CitationManager

from tools.grep import GrepTool
from tools.open_region import FileRegionTool


class Orchestrator:
    """Главный оркестратор системы."""
    
    def __init__(self, config: Config):
        """
        Инициализация оркестратора.
        
        Args:
            config: Конфигурация системы
        """
        self.config = config
        
        # Обеспечение offline режима
        enforce_offline_mode()
        validate_no_network_access()
        
        # Инициализация компонентов
        print("\n[INIT] Инициализация компонентов...")
        
        # Embeddings клиент
        self.embedding_client: EmbeddingClient = LocalSentenceTransformerClient(
            config.embedding_model_dir
        )
        
        # Vector store
        import os
        vectorstore_path = os.path.join(config.storage_dir, "vectorstore")
        self.vector_store: VectorStore = HnswVectorStore(
            storage_path=vectorstore_path,
            dimension=self.embedding_client.get_dimension()
        )
        
        # Doc store
        docstore_path = os.path.join(config.storage_dir, "docstore")
        self.doc_store: DocStore = JsonDocStore(storage_path=docstore_path)
        
        # Meta store
        meta_path = os.path.join(config.storage_dir, "meta")
        self.meta_store = MetaStore(storage_path=meta_path)
        
        # Scanner и chunker
        self.scanner = RepoScanner(
            repo_root=config.repo_root,
            include_extensions=config.include_extensions,
            exclude_dirs=config.exclude_dirs,
            max_file_size_kb=config.max_file_size_kb
        )
        
        self.chunker = FileChunker(
            chunk_size_lines=config.chunk_size_lines,
            chunk_overlap_lines=config.chunk_overlap_lines
        )
        
        # Indexer
        self.indexer = IncrementalIndexer(
            scanner=self.scanner,
            chunker=self.chunker,
            embedding_client=self.embedding_client,
            vector_store=self.vector_store,
            doc_store=self.doc_store,
            meta_store=self.meta_store
        )
        
        # LLM клиент (ленивая инициализация)
        self.llm_client: Optional[LLMClient] = None
        
        # Retriever
        self.retriever = Retriever(
            embedding_client=self.embedding_client,
            vector_store=self.vector_store,
            doc_store=self.doc_store,
            top_k=config.top_k
        )
        
        # Context builder
        self.context_builder = ContextBuilder(
            max_context_chars=config.max_context_chars
        )
        
        # Citation manager
        self.citation_manager = CitationManager()
        
        # Tools
        self.grep_tool = GrepTool(
            repo_root=config.repo_root,
            include_extensions=config.include_extensions,
            exclude_dirs=config.exclude_dirs
        )
        
        self.file_region_tool = FileRegionTool(repo_root=config.repo_root)
        
        print("[INIT] Инициализация завершена\n")
    
    def _ensure_llm(self) -> None:
        """Ленивая инициализация LLM клиента."""
        if self.llm_client is None:
            self.llm_client = LocalLlamaCppClient(
                model_path=self.config.llm_model_path,
                ctx_size=self.config.llm_ctx_size
            )
    
    def cmd_index(self) -> str:
        """Выполнение индексации."""
        stats = self.indexer.index()
        return f"\n✓ Индексация завершена\n  Файлов: {stats['total_files']}\n  Чанков: {stats['total_indexed_chunks']}"
    
    def cmd_ask(self, query: str) -> str:
        """
        Ответ на вопрос пользователя.
        
        Args:
            query: Вопрос пользователя
        
        Returns:
            Ответ ассистента
        """
        if not query.strip():
            return "\nОшибка: вопрос не может быть пустым"
        
        # Инициализация LLM
        self._ensure_llm()
        
        # Поиск релевантных чанков
        print("\n[ASK] Поиск релевантных фрагментов...")
        results = self.retriever.retrieve(query)
        
        if not results:
            return "\nНе найдено релевантных фрагментов кода для ответа на вопрос."
        
        print(f"[ASK] Найдено фрагментов: {len(results)}")
        
        # Сохранение источников
        self.citation_manager.set_sources(results)
        
        # Построение контекста
        context = self.context_builder.build_context(results)
        prompt = self.context_builder.build_prompt(query, context)
        
        print("[ASK] Генерация ответа...")
        
        # Генерация ответа
        answer = self.llm_client.generate(
            prompt=prompt,
            max_new_tokens=self.config.llm_max_new_tokens,
            temperature=self.config.llm_temperature,
            seed=self.config.llm_seed
        )
        
        # Добавление источников
        sources_section = self.citation_manager.format_sources_section(results)
        
        return f"\n{answer}{sources_section}\n"
    
    def cmd_sources(self) -> str:
        """Показать источники последнего ответа."""
        return self.citation_manager.format_sources_detail()
    
    def cmd_open(self, reference: str) -> str:
        """
        Открыть регион файла.
        
        Args:
            reference: Ссылка формата "path:start-end"
        
        Returns:
            Содержимое региона
        """
        path, start, end = self.file_region_tool.parse_reference(reference)
        
        if path is None:
            return f"\nОшибка: неверный формат ссылки. Используйте: path:start-end"
        
        return self.file_region_tool.open_region(path, start, end)
    
    def cmd_grep(self, pattern: str) -> str:
        """
        Поиск по паттерну.
        
        Args:
            pattern: Паттерн для поиска
        
        Returns:
            Результаты поиска
        """
        if not pattern.strip():
            return "\nОшибка: паттерн не может быть пустым"
        
        results = self.grep_tool.search(pattern)
        return self.grep_tool.format_results(results)
    
    def cmd_status(self) -> str:
        """Показать статус индекса."""
        num_files = len(self.meta_store.get_all_indexed_files())
        num_chunks = self.doc_store.count()
        num_vectors = self.vector_store.count()
        last_index = self.meta_store.get_last_index_time()
        
        lines = [
            "\n=== Статус индекса ===",
            f"Файлов проиндексировано: {num_files}",
            f"Чанков в индексе: {num_chunks}",
            f"Векторов в индексе: {num_vectors}",
            f"Последняя индексация: {last_index or 'никогда'}",
            ""
        ]
        
        return "\n".join(lines)
