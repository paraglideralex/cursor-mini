# Архитектура мультирепозиторности ML Service

## Обзор

ML Service теперь поддерживает работу с множеством репозиториев через единый API. Каждый репозиторий имеет:
- Уникальный `repo_id`
- Изолированное хранилище индекса (`storage_root/{repo_id}/`)
- Собственный Orchestrator (кэшируется в памяти)
- Настройки фильтрации файлов (могут переопределять глобальные)

## Структура данных

### ServiceConfig (глобальный)
Общие настройки сервиса, не зависящие от конкретного репозитория:

```json
{
  "llm_model_path": "models/llm/qwen2.5-coder-7b-instruct-q4_k_m.gguf",
  "embedding_model_dir": "models/embeddings/multilingual-e5-large",
  "storage_root": ".codelens_storage",
  "include_extensions": [".cs", ".py", ".js", ".ts"],
  "exclude_dirs": ["bin", "obj", "node_modules", ".git"],
  "max_file_size_kb": 500,
  "chunk_size_lines": 250,
  "chunk_overlap_lines": 30,
  "top_k": 12,
  "max_context_chars": 60000,
  "llm_ctx_size": 8192,
  "llm_max_new_tokens": 700,
  "llm_temperature": 0.2,
  "llm_seed": 42,
  "use_gpu": false,
  "gpu_layers": 0
}
```

### Repository (per-repo метаданные)
Хранятся в `storage_root/repositories.json`:

```json
{
  "repo_id": "abc-123-def",
  "name": "MyApp",
  "path": "C:/projects/MyApp",
  "storage_dir": ".codelens_storage/abc-123-def",
  "include_extensions": [".cs", ".ts"],
  "exclude_dirs": ["bin", "obj", "node_modules"],
  "max_file_size_kb": 500,
  "created_at": "2026-02-10T12:34:56",
  "last_indexed_at": "2026-02-10T13:00:00"
}
```

## Жизненный цикл репозитория

1. **Создание** (`POST /repositories`)
   - Валидация пути к репозиторию
   - Генерация `repo_id`
   - Создание записи в `repositories.json`
   - Директория индекса создаётся при первой индексации

2. **Индексация** (`POST /repositories/{repo_id}/index/start`)
   - Создание Orchestrator для репозитория (если ещё нет)
   - Запуск фонового job'а индексации
   - Обновление `last_indexed_at` после завершения

3. **Запросы** (`POST /repositories/{repo_id}/query`)
   - Получение/создание Orchestrator для репозитория
   - Поиск по векторному индексу репозитория
   - Генерация ответа через LLM

4. **Удаление** (`DELETE /repositories/{repo_id}`)
   - Удаление записи из `repositories.json`
   - Удаление Orchestrator из кэша
   - Физические файлы индекса остаются (можно удалить вручную)

## Кэширование Orchestrator

```python
_orchestrators: dict[str, Orchestrator] = {}  # repo_id -> Orchestrator

def get_orchestrator(repo: Repository):
    if repo.repo_id not in _orchestrators:
        # Создать новый orchestrator с настройками репозитория
        legacy = config.to_legacy_config(
            repo_root=repo.path,
            storage_dir=repo.storage_dir,
        )
        _orchestrators[repo.repo_id] = Orchestrator(legacy)
    return _orchestrators[repo.repo_id]
```

**Преимущества:**
- Модели (embeddings, LLM) загружаются один раз для всех репозиториев
- Индексы остаются в памяти после первого обращения
- Быстрые повторные запросы к тому же репозиторию

**Недостатки:**
- Память растёт с количеством активных репозиториев
- Для production: добавить LRU cache или TTL для orchestrators

## Изоляция данных

Каждый репозиторий имеет изолированное хранилище:

```
.codelens_storage/
  repositories.json              # Метаданные всех репозиториев
  abc-123-def/                   # Репозиторий 1
    docstore/
      chunks.json
    vectorstore/
      hnsw_index.bin
      id_mapping.pkl
    meta/
      indexing_meta.json
  xyz-456-ghi/                   # Репозиторий 2
    docstore/
    vectorstore/
    meta/
```

## API Endpoints

### Repository Management

```bash
# Создать репозиторий
POST /repositories
{
  "name": "MyApp",
  "path": "C:/projects/MyApp",
  "include_extensions": [".cs", ".ts"],  # optional, override defaults
  "exclude_dirs": ["bin", "obj"],        # optional, override defaults
  "max_file_size_kb": 500                # optional, default from config
}
→ {"repo_id": "abc-123", ...}

# Список репозиториев
GET /repositories
→ [{"repo_id": "...", "name": "...", ...}, ...]

# Получить репозиторий
GET /repositories/{repo_id}
→ {"repo_id": "...", "name": "...", ...}

# Удалить репозиторий
DELETE /repositories/{repo_id}
→ 204 No Content
```

### Indexing

```bash
# Запустить индексацию
POST /repositories/{repo_id}/index/start
→ {"job_id": "xyz-456", "message": "Индексация запущена"}

# Статус индексации
GET /repositories/{repo_id}/index/{job_id}/status
→ {"job_id": "...", "status": "running|completed|failed", "progress": 50, ...}
```

### Query

```bash
# Вопрос по коду
POST /repositories/{repo_id}/query
{
  "question": "Как устроена авторизация?",
  "top_k": 12,              # optional
  "max_new_tokens": 700,    # optional
  "temperature": 0.2        # optional
}
→ {
  "answer": "...",
  "sources": [{"path": "...", "start_line": 10, "end_line": 50, ...}],
  "timings": {"retrieval_sec": 0.5, "generation_sec": 12.3, "total_sec": 12.8}
}

# Стриминг ответа
GET /repositories/{repo_id}/query/stream?question=...
→ Server-Sent Events (SSE)
```

## Миграция существующих данных

Если у вас уже есть `.assistant/storage/` с проиндексированным репозиторием:

1. Создайте репозиторий через API:
   ```bash
   curl -X POST http://localhost:8000/repositories \
     -H "Content-Type: application/json" \
     -d '{"name": "OldRepo", "path": "/path/to/old/repo"}'
   ```
   Получите `repo_id`.

2. Скопируйте старые данные:
   ```bash
   cp -r .assistant/storage/* .codelens_storage/{repo_id}/
   ```

3. Репозиторий готов к использованию без переиндексации.

## Планы на будущее

- [ ] LRU cache для orchestrators (ограничение памяти)
- [ ] Персистентное хранилище репозиториев (PostgreSQL вместо JSON)
- [ ] Пагинация списка репозиториев
- [ ] Поиск репозиториев по имени/пути
- [ ] Batch операции (индексация нескольких репозиториев)
- [ ] Статистика использования по репозиториям
- [ ] Автоматическая переиндексация при изменении файлов
