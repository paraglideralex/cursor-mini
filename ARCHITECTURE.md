# Архитектура CodeLens RAG-системы

## Обзор

CodeLens — локальная RAG-система для работы с кодовыми базами. Поддерживает два режима работы:

1. **Консольный (REPL)** — `local_repo_assistant` — интерактивная работа с одним репозиторием
2. **API (FastAPI)** — `ml-service` — HTTP-сервис для работы с множеством репозиториев

Оба варианта используют общий движок RAG из `local_repo_assistant`.

---

## Общая архитектура

### Компонентная диаграмма

```mermaid
graph TB
    subgraph "Консольный режим"
        REPL[REPL Interface]
        REPL --> Orchestrator1[Orchestrator]
    end
    
    subgraph "API режим"
        FastAPI[FastAPI Server]
        FastAPI --> Routers[Routers]
        Routers --> Dependencies[Dependencies]
        Dependencies --> Orchestrator2[Orchestrator]
    end
    
    subgraph "Общий движок RAG"
        Orchestrator1 --> Core[Core Components]
        Orchestrator2 --> Core
        
        Core --> Indexing[Indexing Module]
        Core --> Retrieval[Retrieval Module]
        Core --> LLM[LLM Client]
        Core --> Embeddings[Embeddings Client]
        
        Indexing --> Scanner[RepoScanner]
        Indexing --> Chunker[FileChunker]
        Indexing --> IncrementalIndexer[IncrementalIndexer]
        
        Retrieval --> Retriever[Retriever]
        Retrieval --> ContextBuilder[ContextBuilder]
        Retrieval --> Citations[CitationManager]
    end
    
    subgraph "Хранилище"
        Core --> VectorStore[VectorStore<br/>hnswlib]
        Core --> DocStore[DocStore<br/>JSON]
        Core --> MetaStore[MetaStore<br/>JSON]
    end
    
    subgraph "Модели"
        LLM --> LLMModel["Qwen2.5-Coder 7B<br/>GGUF"]
        Embeddings --> EmbedModel["multilingual-e5-large<br/>sentence-transformers"]
    end
```

### Слои архитектуры

```
┌─────────────────────────────────────────────────────────┐
│  Интерфейсный слой                                       │
│  ┌──────────────┐          ┌──────────────┐             │
│  │ REPL (CLI)   │          │ FastAPI      │             │
│  └──────┬───────┘          └──────┬───────┘             │
└─────────┼──────────────────────────┼─────────────────────┘
          │                          │
┌─────────┼──────────────────────────┼─────────────────────┐
│         │      Оркестратор         │                      │
│         └──────────┬───────────────┘                       │
│                    │                                      │
│  ┌─────────────────┼─────────────────┐                   │
│  │  Индексация     │    Retrieval     │                   │
│  │  - Scanner      │    - Retriever   │                   │
│  │  - Chunker      │    - Context     │                   │
│  │  - Indexer      │    - Citations   │                   │
│  └─────────────────┼─────────────────┘                   │
│                    │                                      │
│  ┌─────────────────┼─────────────────┐                   │
│  │  LLM Client     │  Embeddings     │                   │
│  │  (llama-cpp)    │  (sentence-      │                   │
│  │                 │   transformers)  │                   │
│  └─────────────────┴─────────────────┘                   │
└────────────────────────────────────────────────────────────┘
          │                          │
┌─────────┼──────────────────────────┼─────────────────────┐
│         │      Хранилище           │                      │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐      │
│  │ VectorStore │  │  DocStore   │  │  MetaStore │      │
│  │  (hnswlib)  │  │   (JSON)    │  │   (JSON)    │      │
│  └─────────────┘  └─────────────┘  └─────────────┘      │
└───────────────────────────────────────────────────────────┘
```

---

## Консольный вариант (local_repo_assistant)

### Структура

```
local_repo_assistant/
├── app/
│   ├── main.py          # Точка входа
│   ├── repl.py          # REPL интерфейс
│   ├── orchestrator.py  # Главный координатор
│   └── config.py        # Конфигурация
├── core/
│   └── interfaces.py    # Базовые интерфейсы
├── indexing/            # Модуль индексации
├── retrieval/           # Модуль поиска
├── llm/                 # LLM клиент
├── embeddings/          # Embeddings клиент
└── storage/             # Хранилища
```

### Поток данных: Индексация

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant REPL as REPL
    participant Orch as Orchestrator
    participant Scanner as RepoScanner
    participant Chunker as FileChunker
    participant Embed as EmbeddingsClient
    participant VectorStore as VectorStore
    participant DocStore as DocStore
    participant MetaStore as MetaStore

    User->>REPL: index
    REPL->>Orch: cmd_index()
    Orch->>Scanner: scan()
    Scanner-->>Orch: список файлов
    
    loop Для каждого файла
        Orch->>Scanner: read_file()
        Scanner-->>Orch: содержимое
        Orch->>Chunker: chunk_file()
        Chunker-->>Orch: список чанков
        
        Orch->>Embed: embed_texts()
        Embed-->>Orch: векторы
        
        Orch->>DocStore: put_chunk()
        Orch->>VectorStore: upsert()
        Orch->>MetaStore: set_file_meta()
    end
    
    Orch-->>REPL: статистика
    REPL-->>User: результат
```

### Поток данных: Запрос (RAG)

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant REPL as REPL
    participant Orch as Orchestrator
    participant Embed as EmbeddingsClient
    participant Retriever as Retriever
    participant VectorStore as VectorStore
    participant DocStore as DocStore
    participant Context as ContextBuilder
    participant LLM as LLMClient
    participant Citations as CitationManager

    User->>REPL: ask "Как работает X?"
    REPL->>Orch: cmd_ask(question)
    
    Orch->>Embed: embed_texts([question])
    Embed-->>Orch: query_vector
    
    Orch->>Retriever: retrieve(question)
    Retriever->>VectorStore: query_top_k(query_vector)
    VectorStore-->>Retriever: chunk_ids + scores
    Retriever->>DocStore: list_chunks_by_ids()
    DocStore-->>Retriever: chunks
    Retriever-->>Orch: результаты
    
    Orch->>Context: build_context(results)
    Context-->>Orch: context_string
    Orch->>Context: build_prompt(question, context)
    Context-->>Orch: prompt
    
    Orch->>LLM: generate(prompt)
    LLM-->>Orch: answer
    
    Orch->>Citations: format_sources_section()
    Citations-->>Orch: sources_text
    
    Orch-->>REPL: answer + sources
    REPL-->>User: ответ с цитатами
```

---

## API вариант (ml-service)

### Структура

```
services/ml-service/
├── app/
│   ├── main.py              # FastAPI приложение
│   ├── routers/             # API эндпоинты
│   │   ├── repositories.py  # Управление репозиториями
│   │   ├── indexing.py      # Индексация
│   │   └── query.py         # Запросы
│   ├── dependencies.py       # DI контейнер
│   ├── jobs.py              # Фоновые задачи
│   ├── repositories.py      # Хранилище репозиториев
│   └── assistant_loader.py  # Загрузчик из local_repo_assistant
└── run.py                   # Точка входа
```

### Поток данных: Добавление репозитория

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as FastAPI Router
    participant Store as RepositoryStore
    participant Config as ServiceConfig
    participant FS as File System

    Client->>API: POST /repositories<br/>{name, path, ...}
    API->>Config: get_config()
    Config-->>API: config
    
    API->>Store: create(name, path, ...)
    Store->>Store: generate repo_id
    Store->>FS: validate path exists
    FS-->>Store: ok
    Store->>Store: create storage_dir path
    Store->>Store: save to repositories.json
    Store-->>API: Repository object
    
    API-->>Client: 201 Created<br/>{repo_id, ...}
```

### Поток данных: Индексация (API)

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as Indexing Router
    participant Jobs as Jobs Manager
    participant Thread as Background Thread
    participant Loader as AssistantLoader
    participant Orch as Orchestrator
    participant Indexer as IncrementalIndexer

    Client->>API: POST /repositories/{id}/index/start
    API->>Jobs: start_index_job(config, repo)
    Jobs->>Jobs: generate job_id
    Jobs->>Jobs: create job status "queued"
    Jobs->>Thread: start background thread
    
    Jobs-->>API: job_id
    API-->>Client: 200 OK<br/>{job_id, message}
    
    par Фоновая индексация
        Thread->>Loader: load_orchestrator_class()
        Loader-->>Thread: Orchestrator class
        Thread->>Orch: Orchestrator(legacy_config)
        Thread->>Indexer: index()
        Indexer-->>Thread: stats
        
        Thread->>Jobs: update job status "completed"
        Thread->>Store: update_last_indexed()
    end
    
    Client->>API: GET /repositories/{id}/index/{job_id}/status
    API->>Jobs: get_job_status(job_id)
    Jobs-->>API: JobStatus
    API-->>Client: {status, progress, stats}
```

### Поток данных: Запрос (API)

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as Query Router
    participant Deps as Dependencies
    participant Loader as AssistantLoader
    participant Orch as Orchestrator
    participant QuerySvc as QueryService
    participant Retriever as Retriever
    participant LLM as LLMClient

    Client->>API: POST /repositories/{id}/query<br/>{question, ...}
    API->>Deps: get_orchestrator(repo)
    
    alt Orchestrator не в кэше
        Deps->>Loader: load_orchestrator_class()
        Loader-->>Deps: Orchestrator class
        Deps->>Orch: Orchestrator(legacy_config)
        Deps->>Deps: cache orchestrator
    end
    
    Deps-->>API: Orchestrator
    
    API->>QuerySvc: execute(orchestrator, question)
    QuerySvc->>Retriever: retrieve(question)
    Retriever-->>QuerySvc: results
    
    QuerySvc->>Orch: context_builder.build_context()
    Orch-->>QuerySvc: context
    QuerySvc->>Orch: context_builder.build_prompt()
    Orch-->>QuerySvc: prompt
    
    QuerySvc->>LLM: generate(prompt)
    LLM-->>QuerySvc: answer
    
    QuerySvc->>QuerySvc: format sources
    QuerySvc-->>API: QueryResult
    API-->>Client: 200 OK<br/>{answer, sources, timings}
```

### Поток данных: Удаление репозитория

```mermaid
sequenceDiagram
    participant Client as HTTP Client
    participant API as Repositories Router
    participant Store as RepositoryStore
    participant AppState as AppState
    participant FS as File System

    Client->>API: DELETE /repositories/{id}
    API->>Store: delete(repo_id)
    
    alt Репозиторий существует
        Store->>Store: remove from repositories.json
        Store-->>API: true
        
        API->>AppState: remove orchestrator from cache
        AppState->>AppState: del orchestrators[repo_id]
        
        Note over FS: Физические файлы индекса<br/>остаются [можно удалить вручную]
        
        API-->>Client: 204 No Content
    else Репозиторий не найден
        Store-->>API: false
        API-->>Client: 404 Not Found
    end
```

---

## Сравнение вариантов

| Аспект | Консольный (REPL) | API (FastAPI) |
|--------|-------------------|---------------|
| **Интерфейс** | Интерактивная консоль | HTTP REST API |
| **Репозитории** | Один (из config.json) | Множество (через API) |
| **Индексация** | Синхронная | Асинхронная (фоновые задачи) |
| **Запросы** | Интерактивные команды | HTTP POST/GET |
| **Хранилище** | `.assistant/storage/` | `.codelens_storage/{repo_id}/` |
| **Конфигурация** | `.assistant/config.json` | `.assistant/config.json` + per-repo настройки |
| **Использование** | Локальная разработка | Интеграция с другими сервисами |

---

## Жизненный цикл данных

### Индексация

```
┌─────────────────────────────────────────────────────────┐
│ 1. Сканирование                                          │
│    RepoScanner → список файлов                          │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 2. Чанкинг                                               │
│    FileChunker → разбиение на чанки                      │
│    (chunk_size_lines, chunk_overlap_lines)              │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 3. Создание эмбеддингов                                  │
│    EmbeddingsClient → векторы для каждого чанка         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 4. Сохранение                                            │
│    ├─ DocStore → тексты чанков + метаданные             │
│    ├─ VectorStore → векторы (hnswlib индекс)            │
│    └─ MetaStore → метаданные файлов (mtime, hash)        │
└──────────────────────────────────────────────────────────┘
```

### Запрос (RAG)

```
┌─────────────────────────────────────────────────────────┐
│ 1. Вопрос пользователя                                  │
│    "Как работает авторизация?"                         │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 2. Поиск релевантных чанков                              │
│    EmbeddingsClient → embedding вопроса                  │
│    VectorStore → top-K ближайших векторов                │
│    DocStore → получение текстов чанков                   │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 3. Построение контекста                                  │
│    ContextBuilder → объединение чанков                   │
│    → промпт для LLM                                      │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 4. Генерация ответа                                       │
│    LLMClient → генерация текста                          │
│    CitationManager → форматирование источников          │
└──────────────────┬──────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────────┐
│ 5. Ответ пользователю                                    │
│    Текст + источники в формате path:start-end           │
└──────────────────────────────────────────────────────────┘
```

---

## Структура хранилища

### Консольный вариант

```
.assistant/
├── config.json                    # Конфигурация
└── storage/
    ├── docstore/
    │   └── chunks.json           # Тексты чанков
    ├── vectorstore/
    │   ├── hnsw_index.bin        # Векторный индекс
    │   └── id_mapping.pkl        # Маппинг ID
    └── meta/
        └── indexing_meta.json    # Метаданные индексации
```

### API вариант

```
.codelens_storage/
├── repositories.json              # Метаданные всех репозиториев
├── {repo_id_1}/
│   ├── docstore/
│   ├── vectorstore/
│   └── meta/
├── {repo_id_2}/
│   ├── docstore/
│   ├── vectorstore/
│   └── meta/
└── ...
```

---

## Кэширование и производительность

### API вариант: Кэш Orchestrator

```mermaid
graph LR
    A["Первый запрос к repo_id"] --> B{"Orchestrator<br/>в кэше?"}
    B -->|Нет| C[Создать Orchestrator]
    C --> D[Загрузить модели]
    D --> E[Сохранить в кэш]
    E --> F[Использовать]
    B -->|Да| F
    F --> G[Быстрый ответ]
```

**Преимущества:**
- Модели (LLM, Embeddings) загружаются один раз
- Индексы остаются в памяти
- Быстрые повторные запросы

**Ограничения:**
- Память растёт с количеством активных репозиториев
- Для production: добавить LRU cache или TTL

---

## Безопасность и локальность

### Offline режим

```mermaid
graph TB
    A[Запуск приложения] --> B[enforce_offline_mode]
    B --> C[TRANSFORMERS_OFFLINE=1]
    B --> D[HF_HUB_OFFLINE=1]
    C --> E[validate_no_network_access]
    D --> E
    E --> F[Проверка переменных]
    F --> G[Загрузка моделей только из локальных файлов]
```

**Гарантии:**
- ✅ Никаких сетевых запросов в рантайме
- ✅ Все модели локальные
- ✅ Код не покидает локальную машину

---

## Основные компоненты

### Orchestrator

Главный координатор всех компонентов:

- **Инициализация**: загрузка моделей, создание хранилищ
- **Индексация**: координация Scanner → Chunker → Embeddings → Storage
- **Запросы**: координация Retriever → ContextBuilder → LLM → Citations

### Indexing Module

- **RepoScanner**: сканирование файлов репозитория с фильтрацией
- **FileChunker**: разбиение файлов на чанки с перекрытием
- **IncrementalIndexer**: инкрементальная индексация (только изменённые файлы)

### Retrieval Module

- **Retriever**: семантический поиск по векторному индексу
- **ContextBuilder**: построение контекста для LLM из найденных чанков
- **CitationManager**: управление цитатами и источниками

### Storage

- **VectorStore** (hnswlib): быстрый ANN поиск по векторам
- **DocStore** (JSON): хранение текстов чанков и метаданных
- **MetaStore** (JSON): метаданные индексации (mtime, hash файлов)

---

## Технологический стек

| Компонент | Технология |
|-----------|------------|
| **LLM Runtime** | llama-cpp-python (GGUF) |
| **Embeddings** | sentence-transformers |
| **Vector Store** | hnswlib (HNSW алгоритм) |
| **API Framework** | FastAPI |
| **Storage** | JSON файлы |
| **Language** | Python 3.11 |

---

## Масштабирование

### Текущие ограничения

- **Память**: все Orchestrator'ы в памяти (API вариант)
- **Хранилище**: JSON файлы (не подходит для больших объёмов)
- **Индексация**: синхронная (консольный) / фоновая (API)

### Планы на будущее

- [ ] LRU cache для Orchestrator'ов
- [ ] PostgreSQL для метаданных репозиториев
- [ ] Распределённая индексация
- [ ] Кэширование ответов LLM

---

## Диаграмма развёртывания

```mermaid
graph TB
    subgraph Machine["Локальная машина"]
        subgraph Console["Консольный вариант"]
            User1["Пользователь"] --> REPL["REPL"]
            REPL --> LocalOrch["Orchestrator"]
        end
        
        subgraph API["API вариант"]
            Client["HTTP Client"] --> FastAPI["FastAPI Server<br/>порт 8000"]
            FastAPI --> APIOrch["Orchestrator Pool"]
        end
        
        LocalOrch --> Models["Локальные модели"]
        APIOrch --> Models
        
        Models --> LLMFile["Qwen2.5-Coder.gguf"]
        Models --> EmbedDir["multilingual-e5-large"]
        
        LocalOrch --> Storage1["assistant/storage"]
        APIOrch --> Storage2["codelens_storage"]
    end
```

---

## Заключение

Оба варианта (консольный и API) используют единый движок RAG из `local_repo_assistant`, обеспечивая:

- ✅ Полную локальность (offline режим)
- ✅ Быстрый семантический поиск (hnswlib)
- ✅ Качественные ответы (Qwen2.5-Coder)
- ✅ Цитирование источников
- ✅ Инкрементальную индексацию

Выбор варианта зависит от сценария использования:
- **Консольный**: для локальной разработки и экспериментов
- **API**: для интеграции с другими сервисами и работы с множеством репозиториев
