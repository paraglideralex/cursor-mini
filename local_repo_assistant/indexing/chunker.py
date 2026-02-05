"""
Разбиение файлов на чанки.
"""
import hashlib
from typing import List
from core.interfaces import Chunk


class FileChunker:
    """Разбиение файлов на чанки с перекрытием."""
    
    def __init__(self, chunk_size_lines: int, chunk_overlap_lines: int):
        """
        Инициализация чанкера.
        
        Args:
            chunk_size_lines: Размер чанка в строках
            chunk_overlap_lines: Перекрытие между чанками в строках
        """
        self.chunk_size_lines = chunk_size_lines
        self.chunk_overlap_lines = chunk_overlap_lines
    
    def chunk_file(self, path: str, content: str, mtime: float) -> List[Chunk]:
        """
        Разбиение файла на чанки.
        
        Args:
            path: Путь к файлу (относительный)
            content: Содержимое файла
            mtime: Время модификации файла
        
        Returns:
            Список чанков
        """
        lines = content.split('\n')
        total_lines = len(lines)
        
        if total_lines == 0:
            return []
        
        chunks = []
        start_line = 0
        chunk_idx = 0
        
        while start_line < total_lines:
            end_line = min(start_line + self.chunk_size_lines, total_lines)
            
            # Извлечение строк чанка
            chunk_lines = lines[start_line:end_line]
            chunk_content = '\n'.join(chunk_lines)
            
            # Вычисление хеша чанка
            chunk_hash = self._compute_hash(chunk_content)
            
            # Создание chunk_id
            chunk_id = f"{path}::{chunk_idx}"
            
            chunk = Chunk(
                chunk_id=chunk_id,
                path=path,
                start_line=start_line + 1,  # 1-based line numbers
                end_line=end_line,
                content=chunk_content,
                hash_value=chunk_hash,
                mtime=mtime
            )
            
            chunks.append(chunk)
            
            # Переход к следующему чанку с учетом перекрытия
            start_line += self.chunk_size_lines - self.chunk_overlap_lines
            chunk_idx += 1
        
        return chunks
    
    @staticmethod
    def _compute_hash(content: str) -> str:
        """
        Вычисление хеша содержимого.
        
        Args:
            content: Содержимое для хеширования
        
        Returns:
            Хеш строка
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
