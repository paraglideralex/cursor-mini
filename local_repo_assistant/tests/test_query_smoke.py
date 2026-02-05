"""
Smoke тест для retrieval компонентов.
"""
import sys
import os

# Добавление корневой директории в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_context_builder():
    """Тест построителя контекста."""
    from retrieval.context_builder import ContextBuilder
    from core.interfaces import RetrievalResult
    
    builder = ContextBuilder(max_context_chars=1000)
    
    results = [
        RetrievalResult(
            chunk_id="test::0",
            path="test.py",
            start_line=1,
            end_line=10,
            content="def hello():\n    print('Hello')",
            score=0.1
        )
    ]
    
    context = builder.build_context(results)
    assert len(context) > 0
    assert "test.py" in context
    print("✓ Context builder test passed")
    
    prompt = builder.build_prompt("test query", context)
    assert "test query" in prompt
    assert len(prompt) > 0
    print("✓ Prompt builder test passed")


def test_citation_manager():
    """Тест менеджера цитат."""
    from retrieval.citations import CitationManager
    from core.interfaces import RetrievalResult
    
    manager = CitationManager()
    
    results = [
        RetrievalResult(
            chunk_id="test::0",
            path="test.py",
            start_line=1,
            end_line=10,
            content="test content",
            score=0.1
        )
    ]
    
    manager.set_sources(results)
    sources = manager.get_sources()
    
    assert len(sources) == 1
    assert sources[0].path == "test.py"
    
    formatted = manager.format_sources_section(results)
    assert "Источники" in formatted
    assert "test.py:1-10" in formatted
    
    print("✓ Citation manager test passed")


if __name__ == "__main__":
    print("Running smoke tests for retrieval...\n")
    test_context_builder()
    test_citation_manager()
    print("\n✓ All retrieval smoke tests passed!")
