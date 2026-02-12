"""
Загрузчик компонентов из local_repo_assistant.
Решает проблему конфликта имён пакетов app между ml-service и local_repo_assistant.
"""
import sys
from contextlib import contextmanager
from typing import Any

from app.context import _ASSISTANT_PATH, _REPO_ROOT


@contextmanager
def assistant_import_context():
    """
    Контекстный менеджер для безопасного импорта из local_repo_assistant.
    
    Временно изменяет sys.path так, чтобы local_repo_assistant имел приоритет
    перед ml-service, и очищает кеш модулей.
    
    Usage:
        with assistant_import_context():
            from app.orchestrator import Orchestrator
            # Orchestrator будет из local_repo_assistant, а не ml-service
    """
    # Сохраняем текущий sys.path
    old_sys_path = sys.path.copy()
    
    # Сохраняем закешированные модули app.*
    cached_app_modules = {}
    for key in list(sys.modules.keys()):
        if key.startswith('app.') or key == 'app':
            cached_app_modules[key] = sys.modules[key]
            del sys.modules[key]
    
    try:
        # Удаляем ml-service из начала пути
        sys.path = [p for p in sys.path if 'ml-service' not in p]
        
        # Добавляем local_repo_assistant в начало
        sys.path.insert(0, str(_ASSISTANT_PATH))
        sys.path.insert(0, str(_REPO_ROOT))
        
        yield
        
    finally:
        # Восстанавливаем sys.path
        sys.path = old_sys_path
        
        # Удаляем импортированные модули из local_repo_assistant
        for key in list(sys.modules.keys()):
            if key.startswith('app.') or key == 'app':
                if key not in cached_app_modules:
                    del sys.modules[key]
        
        # Восстанавливаем закешированные модули ml-service
        for key, module in cached_app_modules.items():
            sys.modules[key] = module


def load_orchestrator_class() -> Any:
    """
    Загружает класс Orchestrator из local_repo_assistant.
    
    Returns:
        Класс Orchestrator из local_repo_assistant
    """
    with assistant_import_context():
        from app.orchestrator import Orchestrator
        return Orchestrator
