"""
Открытие и отображение региона файла.
"""
import os


class FileRegionTool:
    """Инструмент для отображения региона файла."""
    
    def __init__(self, repo_root: str):
        """
        Инициализация инструмента.
        
        Args:
            repo_root: Корневая директория репозитория
        """
        self.repo_root = os.path.abspath(repo_root)
    
    def open_region(self, path: str, start_line: int, end_line: int) -> str:
        """
        Открытие региона файла.
        
        Args:
            path: Относительный путь к файлу
            start_line: Начальная строка (1-based)
            end_line: Конечная строка (включительно)
        
        Returns:
            Содержимое региона или сообщение об ошибке
        """
        full_path = os.path.join(self.repo_root, path)
        
        if not os.path.exists(full_path):
            return f"\nОшибка: файл не найден: {path}"
        
        if not os.path.isfile(full_path):
            return f"\nОшибка: {path} не является файлом"
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
            try:
                with open(full_path, 'r', encoding='cp1251') as f:
                    lines = f.readlines()
            except:
                return f"\nОшибка: не удалось прочитать файл {path}"
        except Exception as e:
            return f"\nОшибка при чтении файла: {e}"
        
        total_lines = len(lines)
        
        # Валидация диапазона
        if start_line < 1:
            start_line = 1
        if end_line > total_lines:
            end_line = total_lines
        if start_line > end_line:
            return f"\nОшибка: начальная строка {start_line} больше конечной {end_line}"
        
        # Извлечение региона
        region_lines = lines[start_line - 1:end_line]
        
        # Форматирование вывода
        result_lines = [
            f"\n{'=' * 60}",
            f"Файл: {path}",
            f"Строки: {start_line}-{end_line} (всего в файле: {total_lines})",
            f"{'=' * 60}\n"
        ]
        
        for i, line in enumerate(region_lines, start_line):
            result_lines.append(f"{i:5d} | {line.rstrip()}")
        
        result_lines.append(f"\n{'=' * 60}")
        
        return "\n".join(result_lines)
    
    def parse_reference(self, ref: str) -> tuple:
        """
        Парсинг ссылки формата "path:start-end".
        
        Args:
            ref: Ссылка
        
        Returns:
            Кортеж (path, start_line, end_line) или (None, None, None) при ошибке
        """
        try:
            # Разделение по последнему двоеточию
            parts = ref.rsplit(':', 1)
            if len(parts) != 2:
                return None, None, None
            
            path = parts[0]
            range_part = parts[1]
            
            # Парсинг диапазона
            if '-' in range_part:
                start_str, end_str = range_part.split('-', 1)
                start_line = int(start_str)
                end_line = int(end_str)
            else:
                # Если указана только одна строка
                start_line = end_line = int(range_part)
            
            return path, start_line, end_line
        
        except (ValueError, IndexError):
            return None, None, None
