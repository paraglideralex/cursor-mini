"""
Управление цитатами и источниками.
"""
from typing import List
from core.interfaces import RetrievalResult


class CitationManager:
    """Управление цитатами и источниками для ответов."""
    
    def __init__(self):
        """Инициализация менеджера цитат."""
        self.last_sources: List[RetrievalResult] = []
    
    def set_sources(self, sources: List[RetrievalResult]) -> None:
        """
        Сохранение источников последнего ответа.
        
        Args:
            sources: Список использованных источников
        """
        self.last_sources = sources
    
    def get_sources(self) -> List[RetrievalResult]:
        """
        Получение источников последнего ответа.
        
        Returns:
            Список источников
        """
        return self.last_sources
    
    def format_sources_section(self, sources: List[RetrievalResult]) -> str:
        """
        Форматирование раздела источников.
        
        Args:
            sources: Список источников
        
        Returns:
            Отформатированная строка источников
        """
        if not sources:
            return "\n\n## Источники\nИсточники отсутствуют."
        
        lines = ["\n\n## Источники"]
        for i, source in enumerate(sources, 1):
            citation = f"{source.path}:{source.start_line}-{source.end_line}"
            lines.append(f"{i}. {citation}")
        
        return "\n".join(lines)
    
    def format_sources_detail(self) -> str:
        """
        Детальное форматирование источников для команды `sources`.
        
        Returns:
            Отформатированная строка с деталями
        """
        if not self.last_sources:
            return "Источники отсутствуют. Сначала выполните команду 'ask'."
        
        lines = [f"\n=== Использованные источники ({len(self.last_sources)}) ===\n"]
        
        for i, source in enumerate(self.last_sources, 1):
            lines.append(f"[{i}] {source.path}:{source.start_line}-{source.end_line}")
            lines.append(f"    Релевантность: {1.0 - source.score:.3f}")
            
            # Короткий превью (первые 150 символов)
            preview = source.content[:150].replace('\n', ' ')
            if len(source.content) > 150:
                preview += "..."
            lines.append(f"    Превью: {preview}")
            lines.append("")
        
        return "\n".join(lines)
