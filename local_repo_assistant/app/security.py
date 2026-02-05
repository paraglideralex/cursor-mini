"""
Модуль безопасности и обеспечения локальности.
"""
import os
import sys


def enforce_offline_mode():
    """
    Устанавливает переменные окружения для обеспечения offline режима.
    Должно быть вызвано в самом начале работы приложения.
    """
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    
    print("[SECURITY] Offline режим активирован:")
    print("  - TRANSFORMERS_OFFLINE=1")
    print("  - HF_HUB_OFFLINE=1")
    print("  - HF_DATASETS_OFFLINE=1")


def validate_no_network_access():
    """
    Проверяет, что критичные библиотеки не пытаются делать сетевые запросы.
    В продакшн-версии можно добавить мониторинг сетевых соединений.
    """
    # Проверка переменных окружения
    required_vars = {
        "TRANSFORMERS_OFFLINE": "1",
        "HF_HUB_OFFLINE": "1"
    }
    
    for var, expected_value in required_vars.items():
        actual_value = os.environ.get(var)
        if actual_value != expected_value:
            raise RuntimeError(
                f"[SECURITY ERROR] Переменная окружения {var} должна быть установлена в {expected_value}, "
                f"но имеет значение: {actual_value}"
            )
    
    print("[SECURITY] Валидация offline режима успешна")
