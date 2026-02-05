"""
Точка входа в приложение.
"""
import sys
import os

# Добавление корневой директории в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import Config
from app.orchestrator import Orchestrator
from app.repl import REPL


def main():
    """Главная функция."""
    try:
        # Загрузка конфигурации
        print("Загрузка конфигурации...")
        config = Config.load()
        
        # Создание оркестратора
        orchestrator = Orchestrator(config)
        
        # Запуск REPL
        repl = REPL(orchestrator)
        repl.run()
        
    except FileNotFoundError as e:
        print(f"\n[ОШИБКА] {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"\n[ОШИБКА] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nПрограмма прервана пользователем")
        sys.exit(0)
    except Exception as e:
        print(f"\n[КРИТИЧЕСКАЯ ОШИБКА] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
