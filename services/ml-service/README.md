# CodeLens ML Service (FastAPI)

HTTP-сервис для индексации и RAG-запросов по коду. **Поддерживает множество репозиториев.**

## Запуск

Из корня CodeLens:

```bash
# Установка зависимостей (один раз)
pip install -r services/ml-service/requirements.txt

# Запуск
python services/ml-service/run.py
```

Или:

```bash
cd services/ml-service
pip install -r requirements.txt
python run.py
```

Сервис по умолчанию на `http://localhost:8000`. Документация API: `/docs`.

## Архитектура

- **Мультирепозиторность**: Один сервис обслуживает множество репозиториев
- **Изолированное хранилище**: У каждого репозитория своя директория индекса
- **Ленивая инициализация**: Модели загружаются при первом запросе к репозиторию

## Эндпоинты

### Управление репозиториями

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/repositories` | Создать репозиторий |
| GET | `/repositories` | Список репозиториев |
| GET | `/repositories/{repo_id}` | Получить репозиторий |
| DELETE | `/repositories/{repo_id}` | Удалить репозиторий |

### Индексация и запросы

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/repositories/{repo_id}/index/start` | Запуск индексации |
| GET | `/repositories/{repo_id}/index/{job_id}/status` | Статус индексации |
| POST | `/repositories/{repo_id}/query` | Вопрос по коду |
| GET | `/repositories/{repo_id}/query/stream?question=...` | Ответ по SSE |

### Прочее

| Метод | Путь | Описание |
|-------|------|----------|
| GET | `/health` | Проверка доступности |

## Конфигурация

Используется `.assistant/config.json` из корня CodeLens. **Больше не содержит `repo_root`** — репозитории управляются через API.

Переменные окружения для переопределения:

- `CODELENS_CONFIG` — путь к config.json
- `CODELENS_STORAGE_ROOT` — базовая директория хранения индексов (по умолчанию `.codelens_storage`)
- `CODELENS_LLM_MODEL` — путь к GGUF модели
- `CODELENS_EMBEDDING_MODEL` — путь к embeddings модели
- `CODELENS_ML_PORT` — порт (по умолчанию 8000)

## Пример использования

```bash
# 1. Создать репозиторий
curl -X POST http://localhost:8000/repositories \
  -H "Content-Type: application/json" \
  -d '{"name": "MyApp", "path": "C:/projects/MyApp"}'
# Ответ: {"repo_id": "abc-123", ...}

# 2. Запустить индексацию
curl -X POST http://localhost:8000/repositories/abc-123/index/start
# Ответ: {"job_id": "xyz-456"}

# 3. Проверить статус
curl http://localhost:8000/repositories/abc-123/index/xyz-456/status

# 4. Задать вопрос
curl -X POST http://localhost:8000/repositories/abc-123/query \
  -H "Content-Type: application/json" \
  -d '{"question": "Как устроена авторизация?"}'
```
