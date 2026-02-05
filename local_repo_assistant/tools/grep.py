"""
Локальный текстовый поиск по репозиторию.
"""
import os
import re
from typing import List, Tuple


class GrepTool:
    """Инструмент для текстового поиска по файлам."""
    
    def __init__(self, repo_root: str, include_extensions: List[str], exclude_dirs: List[str]):
        """
        Инициализация grep.
        
        Args:
            repo_root: Корневая директория репозитория
            include_extensions: Список расширений для поиска
            exclude_dirs: Список директорий для исключения
        """
        self.repo_root = os.path.abspath(repo_root)
        self.include_extensions = set(include_extensions)
        self.exclude_dirs = set(exclude_dirs)
    
    def search(self, pattern: str, case_sensitive: bool = False) -> List[Tuple[str, int, str]]:
        """
        Поиск паттерна в файлах.
        
        Args:
            pattern: Паттерн для поиска (поддерживает regex)
            case_sensitive: Учитывать регистр
        
        Returns:
            Список кортежей (путь, номер_строки, строка_с_совпадением)
        """
        results = []
        flags = 0 if case_sensitive else re.IGNORECASE
        
        try:
            regex = re.compile(pattern, flags)
        except re.error as e:
            return [("ERROR", 0, f"Неверный regex паттерн: {e}")]
        
        # Обход файлов
        for root, dirs, files in os.walk(self.repo_root):
            # Фильтрация директорий
            dirs[:] = [d for d in dirs if not self._should_exclude_dir(d)]
            
            for file in files:
                if not self._has_valid_extension(file):
                    continue
                
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.repo_root)
                
                # Поиск в файле
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                results.append((rel_path, line_num, line.rstrip()))
                except:
                    # Пропускаем файлы с ошибками чтения
                    continue
        
        return results
    
    def format_results(self, results: List[Tuple[str, int, str]], max_results: int = 50) -> str:
        """
        Форматирование результатов поиска.
        
        Args:
            results: Результаты поиска
            max_results: Максимальное количество результатов для отображения
        
        Returns:
            Отформатированная строка
        """
        if not results:
            return "\nНичего не найдено."
        
        if results[0][0] == "ERROR":
            return f"\n{results[0][2]}"
        
        lines = [f"\nНайдено совпадений: {len(results)}"]
        
        if len(results) > max_results:
            lines.append(f"Показано первых {max_results} результатов:\n")
            results = results[:max_results]
        else:
            lines.append("")
        
        for path, line_num, line in results:
            lines.append(f"{path}:{line_num}: {line}")
        
        return "\n".join(lines)
    
    def _should_exclude_dir(self, dir_name: str) -> bool:
        """Проверка, нужно ли исключить директорию."""
        if dir_name.startswith('.'):
            return True
        if dir_name in self.exclude_dirs:
            return True
        return False
    
    def _has_valid_extension(self, filename: str) -> bool:
        """Проверка расширения файла."""
        if not self.include_extensions:
            return True
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.include_extensions
