"""
Сервис выполнения запросов (RAG).
"""
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Generator

from app.config import ServiceConfig
from app.repositories import Repository
from app.schemas import Citation, QueryResponse

logger = logging.getLogger(__name__)


@dataclass
class QueryResult:
    """Результат выполнения запроса."""
    answer: str
    sources: list[Citation]
    timings: dict[str, float]


class QueryService:
    """Сервис выполнения RAG запросов."""
    
    @staticmethod
    def execute(
        orchestrator: Any,
        config: ServiceConfig,
        question: str,
        top_k: int | None = None,
        max_new_tokens: int | None = None,
        temperature: float | None = None,
    ) -> QueryResult:
        """
        Выполнить RAG запрос.
        
        Args:
            orchestrator: Orchestrator для репозитория
            config: Конфигурация сервиса
            question: Вопрос пользователя
            top_k: Количество фрагментов (опционально)
            max_new_tokens: Макс. токенов (опционально)
            temperature: Температура (опционально)
            
        Returns:
            QueryResult с ответом, источниками и таймингами
        """
        # Параметры с fallback на конфиг
        effective_top_k = top_k or config.top_k
        effective_max_tokens = max_new_tokens or config.llm_max_new_tokens
        effective_temperature = temperature if temperature is not None else config.llm_temperature
        
        total_start = time.perf_counter()
        
        # Поиск релевантных фрагментов
        retrieval_start = time.perf_counter()
        results = orchestrator.retriever.retrieve(question)
        retrieval_time = time.perf_counter() - retrieval_start
        
        if not results:
            return QueryResult(
                answer="Не найдено релевантных фрагментов кода для ответа на вопрос.",
                sources=[],
                timings={
                    "retrieval_sec": round(retrieval_time, 3),
                    "generation_sec": 0,
                    "total_sec": round(time.perf_counter() - total_start, 3),
                },
            )
        
        # Сохранение источников
        orchestrator.citation_manager.set_sources(results)
        
        # Построение контекста и промпта
        context = orchestrator.context_builder.build_context(results)
        prompt = orchestrator.context_builder.build_prompt(question, context)
        
        # Генерация ответа
        orchestrator._ensure_llm()
        gen_start = time.perf_counter()
        answer = orchestrator.llm_client.generate(
            prompt=prompt,
            max_new_tokens=effective_max_tokens,
            temperature=effective_temperature,
            seed=config.llm_seed,
            progress_callback=None,
        )
        gen_time = time.perf_counter() - gen_start
        total_time = time.perf_counter() - total_start
        
        # Форматирование источников
        sources = [
            Citation(
                path=r.path,
                start_line=r.start_line,
                end_line=r.end_line,
                score=round(1.0 - r.score, 4),
                preview=QueryService._make_preview(r.content),
            )
            for r in results
        ]
        
        return QueryResult(
            answer=answer,
            sources=sources,
            timings={
                "retrieval_sec": round(retrieval_time, 3),
                "generation_sec": round(gen_time, 3),
                "total_sec": round(total_time, 3),
            },
        )
    
    @staticmethod
    def execute_stream(
        orchestrator: Any,
        config: ServiceConfig,
        question: str,
    ) -> Generator[str, None, None]:
        """
        Выполнить RAG запрос со стримингом ответа (SSE).
        
        Yields:
            SSE события в формате "data: {...}\\n\\n"
        """
        results = orchestrator.retriever.retrieve(question)
        
        if not results:
            yield QueryService._sse_event({
                "type": "done",
                "answer": "Не найдено релевантных фрагментов.",
                "sources": [],
            })
            return
        
        orchestrator.citation_manager.set_sources(results)
        context = orchestrator.context_builder.build_context(results)
        prompt = orchestrator.context_builder.build_prompt(question, context)
        orchestrator._ensure_llm()
        
        answer = orchestrator.llm_client.generate(
            prompt=prompt,
            max_new_tokens=config.llm_max_new_tokens,
            temperature=config.llm_temperature,
            seed=config.llm_seed,
            progress_callback=None,
        )
        
        sources = [
            {
                "path": r.path,
                "start_line": r.start_line,
                "end_line": r.end_line,
                "score": round(1.0 - r.score, 4),
            }
            for r in results
        ]
        
        yield QueryService._sse_event({
            "type": "done",
            "answer": answer,
            "sources": sources,
        })
    
    @staticmethod
    def _make_preview(content: str, max_len: int = 150) -> str:
        """Создать превью контента."""
        preview = content[:max_len].replace("\n", " ").rstrip()
        if len(content) > max_len:
            preview += "..."
        return preview
    
    @staticmethod
    def _sse_event(data: dict) -> str:
        """Форматировать SSE событие."""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
