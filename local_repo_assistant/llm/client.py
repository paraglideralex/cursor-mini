"""
LLM клиенты для генерации ответов.
"""
from typing import Optional
import sys

from core.interfaces import LLMClient


class LocalLlamaCppClient(LLMClient):
    """LLM клиент через llama-cpp-python для локальной GGUF модели."""
    
    def __init__(self, model_path: str, ctx_size: int):
        """
        Инициализация клиента.
        
        Args:
            model_path: Путь к GGUF файлу модели
            ctx_size: Размер контекста
        """
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "Библиотека llama-cpp-python не установлена.\n"
                "Установите: pip install llama-cpp-python"
            )
        
        print(f"[LLM] Загрузка модели из {model_path}...")
        print(f"[LLM] Размер контекста: {ctx_size}")
        
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=ctx_size,
                n_threads=8,  # Оптимально для i7-13700H
                n_gpu_layers=0,  # CPU-only
                verbose=False
            )
            print("[LLM] Модель успешно загружена")
        except Exception as e:
            raise RuntimeError(f"Ошибка загрузки модели LLM: {e}")
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        seed: int
    ) -> str:
        """
        Генерация текста по промпту.
        
        Args:
            prompt: Промпт для генерации
            max_new_tokens: Максимальное количество новых токенов
            temperature: Температура генерации
            seed: Seed для воспроизводимости
        
        Returns:
            Сгенерированный текст
        """
        try:
            response = self.model(
                prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                seed=seed,
                echo=False,
                stop=["</s>", "<|endoftext|>", "<|im_end|>"]
            )
            
            generated_text = response["choices"][0]["text"]
            return generated_text.strip()
            
        except Exception as e:
            return f"[ОШИБКА ГЕНЕРАЦИИ]: {str(e)}"


class StubCorporateClient(LLMClient):
    """
    Заготовка для корпоративного LLM клиента.
    Можно использовать для интеграции с внутренними API в будущем.
    """
    
    def __init__(self, api_endpoint: Optional[str] = None):
        """
        Инициализация клиента.
        
        Args:
            api_endpoint: URL корпоративного API (опционально)
        """
        self.api_endpoint = api_endpoint
        print("[LLM] Инициализирован StubCorporateClient (заглушка)")
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        seed: int
    ) -> str:
        """Заглушка для генерации."""
        return (
            "[StubCorporateClient] Этот клиент является заглушкой.\n"
            "Реализуйте интеграцию с вашим корпоративным LLM API."
        )
