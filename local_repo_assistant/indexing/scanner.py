"""
Сканирование файлов репозитория.
"""
import os
from typing import List, Set
from pathlib import Path


class RepoScanner:
    """Сканер файлов репозитория с фильтрацией."""
    
    def __init__(
        self,
        repo_root: str,
        include_extensions: List[str],
        exclude_dirs: List[str],
        max_file_size_kb: int
    ):
        """
        Инициализация сканера.
        
        Args:
            repo_root: Корневая директория репозитория
            include_extensions: Список расширений файлов для включения (например, [".cs", ".py"])
            exclude_dirs: Список директорий для исключения (например, ["bin", "obj", ".git"])
            max_file_size_kb: Максимальный размер файла в КБ
        """
        self.repo_root = os.path.abspath(repo_root)
        self.include_extensions = set(include_extensions)
        self.exclude_dirs = set(exclude_dirs)
        self.max_file_size_bytes = max_file_size_kb * 1024
    
    def scan(self) -> List[str]:
        """
        Сканирование репозитория и возврат списка подходящих файлов.
        
        Returns:
            Список относительных путей к файлам
        """
        result = []
        
        for root, dirs, files in os.walk(self.repo_root):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d, root)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Проверка расширения
                if not self._has_valid_extension(file):
                    continue
                
                # Проверка размера файла
                try:
                    if os.path.getsize(file_path) > self.max_file_size_bytes:
                        continue
                except OSError:
                    continue
                
                # Относительный путь
                rel_path = os.path.relpath(file_path, self.repo_root)
                result.append(rel_path)
        
        return result
    
    def _should_exclude_dir(self, dir_name: str, parent_path: str) -> bool:
        """
        Проверка, нужно ли исключить директорию.
        
        Args:
            dir_name: Имя директории
            parent_path: Путь к родительской директории
        
        Returns:
            True если директорию нужно исключить
        """
        # Исключение скрытых директорий
        if dir_name.startswith('.'):
            return True
        
        # Исключение по списку
        if dir_name in self.exclude_dirs:
            return True
        
        # Исключение директорий из exclude_dirs в любом месте пути
        for exclude_dir in self.exclude_dirs:
            if exclude_dir in dir_name:
                return True
        
        return False
    
    def _has_valid_extension(self, filename: str) -> bool:
        """
        Проверка расширения файла.
        
        Args:
            filename: Имя файла
        
        Returns:
            True если расширение подходит
        """
        if not self.include_extensions:
            return True
        
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.include_extensions
    
    def get_file_mtime(self, rel_path: str) -> float:
        """
        Получение времени модификации файла.
        
        Args:
            rel_path: Относительный путь к файлу
        
        Returns:
            Время модификации (timestamp)
        """
        full_path = os.path.join(self.repo_root, rel_path)
        return os.path.getmtime(full_path)
    
    def read_file(self, rel_path: str) -> str:
        """
        Чтение содержимого файла.
        
        Args:
            rel_path: Относительный путь к файлу
        
        Returns:
            Содержимое файла
        """
        full_path = os.path.join(self.repo_root, rel_path)
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Попытка с другой кодировкой
            try:
                with open(full_path, 'r', encoding='cp1251') as f:
                    return f.read()
            except:
                return ""
        except Exception:
            return ""
