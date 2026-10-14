import os
from pathlib import Path

DATA_DIR = Path(os.getenv("RAGI_DATA_DIR", "/app/data"))
LOGS_DIR = DATA_DIR / "logs"
SECRET_DIR = DATA_DIR / "secret"

for _d in (DATA_DIR, LOGS_DIR, SECRET_DIR):
    _d.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOGS_DIR / "app.log"
JWT_KEY_FILE = SECRET_DIR / "jwt.key"