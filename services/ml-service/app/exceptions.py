"""
Кастомные исключения и обработчики ошибок.
"""
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class ServiceException(Exception):
    """Базовое исключение сервиса."""
    def __init__(self, message: str, code: str = "SERVICE_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)


class ConfigNotLoadedError(ServiceException):
    """Конфигурация не загружена."""
    def __init__(self):
        super().__init__("Сервис не инициализирован", "CONFIG_NOT_LOADED")


class RepositoryNotFoundError(ServiceException):
    """Репозиторий не найден."""
    def __init__(self, repo_id: str):
        super().__init__(f"Репозиторий не найден: {repo_id}", "REPOSITORY_NOT_FOUND")
        self.repo_id = repo_id


class RepositoryPathError(ServiceException):
    """Ошибка пути репозитория."""
    def __init__(self, path: str, reason: str = "не существует или не является директорией"):
        super().__init__(f"Путь {path} {reason}", "REPOSITORY_PATH_ERROR")
        self.path = path


class JobNotFoundError(ServiceException):
    """Задача не найдена."""
    def __init__(self, job_id: str):
        super().__init__(f"Задача не найдена: {job_id}", "JOB_NOT_FOUND")
        self.job_id = job_id


class IndexingError(ServiceException):
    """Ошибка индексации."""
    def __init__(self, repo_id: str, message: str):
        super().__init__(f"Ошибка индексации {repo_id}: {message}", "INDEXING_ERROR")
        self.repo_id = repo_id


class QueryError(ServiceException):
    """Ошибка выполнения запроса."""
    def __init__(self, message: str):
        super().__init__(message, "QUERY_ERROR")


# --- HTTP Exception Mapping ---

EXCEPTION_STATUS_CODES = {
    ConfigNotLoadedError: 503,
    RepositoryNotFoundError: 404,
    RepositoryPathError: 400,
    JobNotFoundError: 404,
    IndexingError: 500,
    QueryError: 500,
}


def get_status_code(exc: ServiceException) -> int:
    """Получить HTTP статус код для исключения."""
    return EXCEPTION_STATUS_CODES.get(type(exc), 500)


async def service_exception_handler(request: Request, exc: ServiceException) -> JSONResponse:
    """Обработчик ServiceException для FastAPI."""
    return JSONResponse(
        status_code=get_status_code(exc),
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


def raise_for_repo(repo_id: str, repo) -> None:
    """Проверить, что репозиторий существует, иначе выбросить исключение."""
    if repo is None:
        raise RepositoryNotFoundError(repo_id)
