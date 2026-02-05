"""
LLM клиенты для генерации ответов.
"""
from typing import Optional
import sys

from core.interfaces import LLMClient


class LocalLlamaCppClient(LLMClient):
    """LLM клиент через llama-cpp-python для локальной GGUF модели."""
    
    def __init__(self, model_path: str, ctx_size: int, use_gpu: bool = False, gpu_layers: int = 0):
        """
        Инициализация клиента.
        
        Args:
            model_path: Путь к GGUF файлу модели
            ctx_size: Размер контекста
            use_gpu: Использовать ли GPU
            gpu_layers: Количество слоёв на GPU (0 = CPU-only, -1 = все слои)
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
        
        # Проверка доступности GPU для llama-cpp-python
        actual_gpu_layers = 0
        if use_gpu and gpu_layers != 0:
            try:
                # llama-cpp-python попытается использовать CUDA автоматически
                actual_gpu_layers = gpu_layers
                print(f"[LLM] Режим: GPU (слоёв на GPU: {gpu_layers})")
                print(f"[LLM] ⚠️  Если CUDA недоступна для llama-cpp-python, автоматически будет использован CPU")
            except:
                actual_gpu_layers = 0
                print(f"[LLM] Режим: CPU-only (fallback)")
        else:
            print(f"[LLM] Режим: CPU-only")
        
        try:
            self.model = Llama(
                model_path=model_path,
                n_ctx=ctx_size,
                n_threads=8,  # Оптимально для многоядерного CPU
                n_gpu_layers=actual_gpu_layers,
                verbose=False
            )
            print("[LLM] Модель успешно загружена")
        except Exception as e:
            # Если ошибка связана с GPU, пробуем fallback на CPU
            if use_gpu and "CUDA" in str(e):
                print(f"[LLM] ⚠️  Ошибка загрузки с GPU, повтор с CPU...")
                try:
                    self.model = Llama(
                        model_path=model_path,
                        n_ctx=ctx_size,
                        n_threads=8,
                        n_gpu_layers=0,
                        verbose=False
                    )
                    print("[LLM] Модель успешно загружена (CPU-only)")
                except Exception as e2:
                    raise RuntimeError(f"Ошибка загрузки модели LLM: {e2}")
            else:
                raise RuntimeError(f"Ошибка загрузки модели LLM: {e}")
    
    def generate(
        self,
        prompt: str,
        max_new_tokens: int,
        temperature: float,
        seed: int,
        progress_callback: callable = None
    ) -> str:
        """
        Генерация текста по промпту.
        
        Args:
            prompt: Промпт для генерации
            max_new_tokens: Максимальное количество новых токенов
            temperature: Температура генерации
            seed: Seed для воспроизводимости
            progress_callback: Callback для обновления прогресса (принимает количество токенов)
        
        Returns:
            Сгенерированный текст
        """
        try:
            # Генерация с потоковым выводом для обновления прогресс-бара
            generated_tokens = []
            token_count = 0
            
            for output in self.model(
                prompt,
                max_tokens=max_new_tokens,
                temperature=temperature,
                seed=seed,
                echo=False,
                stop=["</s>", "<|endoftext|>", "<|im_end|>"],
                stream=True
            ):
                token = output["choices"][0]["text"]
                generated_tokens.append(token)
                token_count += 1
                
                # Обновление прогресса каждые 5 токенов
                if progress_callback and token_count % 5 == 0:
                    try:
                        progress_callback(5)
                    except:
                        pass
            
            generated_text = "".join(generated_tokens)
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
        seed: int,
        progress_callback: callable = None
    ) -> str:
        """Заглушка для генерации."""
        return (
            "[StubCorporateClient] Этот клиент является заглушкой.\n"
            "Реализуйте интеграцию с вашим корпоративным LLM API."
        )
