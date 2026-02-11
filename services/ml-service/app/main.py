"""
FastAPI ML Service — точка входа.
"""
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Настройка путей до импортов
from app.context import _ASSISTANT_PATH, _REPO_ROOT

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_ASSISTANT_PATH) not in sys.path:
    sys.path.insert(0, str(_ASSISTANT_PATH))

# Offline для transformers/huggingface
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from app.config import ServiceConfig
from app.dependencies import AppState
from app.exceptions import ServiceException, service_exception_handler
from app.repositories import RepositoryStore
from app.routers import health_router, indexing_router, query_router, repositories_router

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Жизненный цикл приложения."""
    # Startup
    try:
        AppState.config = ServiceConfig.load()
        logger.info("Конфигурация загружена: storage_root=%s", AppState.config.storage_root)
        
        # Создаём директорию storage_root если не существует
        os.makedirs(AppState.config.storage_root, exist_ok=True)
        
        # Инициализация хранилища репозиториев
        repos_db = os.path.join(AppState.config.storage_root, "repositories.json")
        AppState.repo_store = RepositoryStore(repos_db)
        logger.info("Репозиториев загружено: %d", len(AppState.repo_store.list_all()))
        
    except Exception as e:
        logger.error("Ошибка инициализации: %s", e)
        AppState.config = None
        AppState.repo_store = None
    
    yield
    
    # Shutdown
    AppState.reset()
    logger.info("Сервис остановлен")


# Создание приложения
app = FastAPI(
    title="CodeLens ML Service",
    description="RAG-сервис для индексации и запросов по коду. Поддерживает множество репозиториев.",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS (для фронтенда)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Обработчик исключений
app.add_exception_handler(ServiceException, service_exception_handler)

# Роутеры
app.include_router(health_router)
app.include_router(repositories_router)
app.include_router(indexing_router)
app.include_router(query_router)


# Точка входа для запуска напрямую
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("CODELENS_ML_PORT", "8000"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
