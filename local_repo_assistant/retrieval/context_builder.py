"""
Построение контекста для LLM.
"""
from typing import List

from core.interfaces import RetrievalResult


class ContextBuilder:
    """Построение контекста для LLM из релевантных чанков."""
    
    def __init__(self, max_context_chars: int):
        """
        Инициализация builder.
        
        Args:
            max_context_chars: Максимальный размер контекста в символах
        """
        self.max_context_chars = max_context_chars
    
    def build_context(self, results: List[RetrievalResult]) -> str:
        """
        Построение контекста из результатов поиска.
        
        Args:
            results: Список релевантных чанков
        
        Returns:
            Строка контекста для промпта
        """
        if not results:
            return "Релевантных фрагментов кода не найдено."
        
        context_parts = []
        current_chars = 0
        
        for i, result in enumerate(results, 1):
            # Формат: номер, путь, строки, короткий превью
            header = f"\n--- Фрагмент {i} ---\n"
            header += f"Файл: {result.path}\n"
            header += f"Строки: {result.start_line}-{result.end_line}\n"
            header += f"Релевантность: {1.0 - result.score:.3f}\n\n"
            
            content = result.content
            
            # Ограничение размера контекста
            chunk_text = header + content
            if current_chars + len(chunk_text) > self.max_context_chars:
                # Попытка включить хотя бы часть
                remaining = self.max_context_chars - current_chars
                if remaining > 500:  # Минимальный порог
                    truncated = content[:remaining - len(header) - 100]
                    chunk_text = header + truncated + "\n\n[... обрезано ...]"
                    context_parts.append(chunk_text)
                break
            
            context_parts.append(chunk_text)
            current_chars += len(chunk_text)
        
        return "\n".join(context_parts)
    
    def build_prompt(self, query: str, context: str) -> str:
        """
        Построение полного промпта для LLM.
        
        Args:
            query: Вопрос пользователя
            context: Контекст из релевантных чанков
        
        Returns:
            Полный промпт
        """
        prompt = f"""Ты - ассистент по кодовой базе. Твоя задача - отвечать на вопросы о коде, используя предоставленный контекст.

ВАЖНЫЕ ПРАВИЛА:
1. Отвечай ТОЛЬКО на русском языке.
2. Используй ТОЛЬКО информацию из предоставленного контекста.
3. Если информации недостаточно, честно об этом скажи.
4. НЕ выдумывай классы, методы или функции, которых нет в контексте.
5. В конце ответа ОБЯЗАТЕЛЬНО добавь раздел "## Источники" со ссылками в формате "путь:строка_начала-строка_конца".
6. Если нужна диаграмма Mermaid, НЕ используй круглые скобки в именах узлов. Используй квадратные скобки или кавычки.

КОНТЕКСТ:
{context}

ВОПРОС: {query}

ОТВЕТ:"""
        
        return prompt
