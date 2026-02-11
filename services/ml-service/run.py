#!/usr/bin/env python3
"""
Запуск ML Service.
Из корня CodeLens: python services/ml-service/run.py
Из services/ml-service: python run.py
"""
import os
import sys
from pathlib import Path

# Корень CodeLens
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Рабочая директория = корень CodeLens (для .assistant/config.json)
os.chdir(ROOT)

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("CODELENS_ML_PORT", "8000"))
    # app.main:app требует, чтобы sys.path включал путь к app (ml-service как текущая папка)
    service_dir = Path(__file__).resolve().parent
    if str(service_dir) not in sys.path:
        sys.path.insert(0, str(service_dir))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
    )
