"""
Настройка PYTHONPATH и загрузка Orchestrator из local_repo_assistant.
"""
import sys
from pathlib import Path

# Корень репозитория CodeLens (services/ml-service/app -> CodeLens)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ASSISTANT_PATH = _REPO_ROOT / "local_repo_assistant"

if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
if str(_ASSISTANT_PATH) not in sys.path:
    sys.path.insert(0, str(_ASSISTANT_PATH))
