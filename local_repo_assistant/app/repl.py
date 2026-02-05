"""
REPL интерфейс для взаимодействия с ассистентом.
"""
import sys
from app.orchestrator import Orchestrator


class REPL:
    """Интерактивный REPL для ассистента."""
    
    def __init__(self, orchestrator: Orchestrator):
        """
        Инициализация REPL.
        
        Args:
            orchestrator: Оркестратор системы
        """
        self.orchestrator = orchestrator
        self.running = True
    
    def run(self) -> None:
        """Запуск REPL."""
        self._print_welcome()
        
        while self.running:
            try:
                # Чтение команды
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                # Обработка команды
                self._handle_command(user_input)
                
            except KeyboardInterrupt:
                print("\n\nИспользуйте 'quit' для выхода")
                continue
            except EOFError:
                print("\n")
                break
            except Exception as e:
                print(f"\nОшибка: {e}")
    
    def _handle_command(self, user_input: str) -> None:
        """
        Обработка команды пользователя.
        
        Args:
            user_input: Введенная команда
        """
        parts = user_input.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command == "quit" or command == "exit":
            print("\nДо свидания!")
            self.running = False
        
        elif command == "help":
            self._print_help()
        
        elif command == "index":
            result = self.orchestrator.cmd_index()
            print(result)
        
        elif command == "ask":
            if not args:
                print("\nИспользование: ask <вопрос>")
                return
            result = self.orchestrator.cmd_ask(args)
            print(result)
        
        elif command == "sources":
            result = self.orchestrator.cmd_sources()
            print(result)
        
        elif command == "open":
            if not args:
                print("\nИспользование: open <path:start-end>")
                return
            result = self.orchestrator.cmd_open(args)
            print(result)
        
        elif command == "grep":
            if not args:
                print("\nИспользование: grep <паттерн>")
                return
            result = self.orchestrator.cmd_grep(args)
            print(result)
        
        elif command == "status":
            result = self.orchestrator.cmd_status()
            print(result)
        
        else:
            print(f"\nНеизвестная команда: {command}")
            print("Введите 'help' для списка команд")
    
    def _print_welcome(self) -> None:
        """Вывод приветствия."""
        print("\n" + "=" * 60)
        print(" Локальный RAG-ассистент по репозиторию")
        print("=" * 60)
        print("\nВведите 'help' для списка команд")
        print("Введите 'quit' для выхода")
    
    def _print_help(self) -> None:
        """Вывод справки по командам."""
        help_text = """
=== Доступные команды ===

index
    Выполнить индексацию репозитория.
    При повторном запуске выполняется инкрементальная индексация.

ask <вопрос>
    Задать вопрос по коду. Ответ генерируется на основе RAG.
    Пример: ask Как устроена авторизация?

sources
    Показать чанки, использованные в последнем ответе.

open <path:start-end>
    Открыть и показать указанный регион файла.
    Пример: open src/auth.py:10-50

grep <паттерн>
    Выполнить текстовый поиск по репозиторию.
    Поддерживает regex.
    Пример: grep class.*Controller

status
    Показать статус индекса (количество файлов, чанков, время индексации).

help
    Показать эту справку.

quit / exit
    Выход из программы.
"""
        print(help_text)
