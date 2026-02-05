"""
Smoke тест для индексации.
"""
import sys
import os

# Добавление корневой директории в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_chunker():
    """Тест чанкера."""
    from indexing.chunker import FileChunker
    
    chunker = FileChunker(chunk_size_lines=5, chunk_overlap_lines=1)
    
    content = "\n".join([f"line {i}" for i in range(1, 11)])
    chunks = chunker.chunk_file("test.py", content, 0.0)
    
    assert len(chunks) > 0
    assert chunks[0].path == "test.py"
    assert chunks[0].start_line == 1
    print("✓ Chunker test passed")


def test_scanner():
    """Тест сканера."""
    from indexing.scanner import RepoScanner
    
    # Тест на текущей директории
    scanner = RepoScanner(
        repo_root=".",
        include_extensions=[".py"],
        exclude_dirs=["venv", "__pycache__"],
        max_file_size_kb=1000
    )
    
    files = scanner.scan()
    assert isinstance(files, list)
    print(f"✓ Scanner test passed (found {len(files)} files)")


if __name__ == "__main__":
    print("Running smoke tests for indexing...\n")
    test_chunker()
    test_scanner()
    print("\n✓ All indexing smoke tests passed!")
