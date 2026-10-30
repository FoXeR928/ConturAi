"""
Оркестратор локальной разработки ConturAI.
Запускает параллельно:
  - postgres          (в Docker, через docker-compose.dev.yml)
  - conturai-manager  (Python / uvicorn, порт 8080)
  - conturai-backend  (Python / uvicorn, порт 8000)
  - conturai-frontend (npm run dev,   порт 5173)

Останавливает всё по Ctrl+C.

Требования:
  - Python 3.11 с установленными зависимостями в каждом компоненте
  - Node.js + npm (для фронтенда)
  - Docker с доступом к /var/run/docker.sock (или Docker Desktop)
"""
from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

COMPONENTS = {
    "manager":  ROOT / "conturai-manager",
    "backend":  ROOT / "conturai-backend",
    "frontend": ROOT / "conturai-frontend",
}

COLORS = {
    "manager":  "\033[96m",
    "backend":  "\033[92m",
    "frontend": "\033[93m",
    "postgres": "\033[95m",
    "system":   "\033[90m",
    "reset":    "\033[0m",
}


def _log(tag: str, msg: str) -> None:
    c = COLORS.get(tag, "")
    print(f"{c}[{tag}]{COLORS['reset']} {msg}", flush=True)


def _stream(name: str, proc: subprocess.Popen) -> None:
    assert proc.stdout is not None
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            _log(name, line)


def _spawn(name: str, cwd: Path, cmd: list, env_extra: dict | None = None) -> subprocess.Popen:
    env = {**os.environ, **(env_extra or {})}
    env["PYTHONUNBUFFERED"] = "1"
    env["FORCE_COLOR"] = "1"

    shell = os.name == "nt" and name == "frontend"
    p = subprocess.Popen(
        cmd,
        cwd=str(cwd),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        shell=shell,
    )
    threading.Thread(target=_stream, args=(name, p), daemon=True).start()
    return p


def _check_prereqs() -> None:
    missing = []
    if not shutil.which("docker"):
        missing.append("docker")
    if not shutil.which("npm"):
        missing.append("npm")
    if not shutil.which(sys.executable):
        missing.append("python")
    if missing:
        _log("system", f"Не найдены: {', '.join(missing)}. Установите и повторите.")
        sys.exit(1)


def _ensure_component_deps() -> None:
    for name, cwd in COMPONENTS.items():
        if name == "frontend":
            if not (cwd / "node_modules").exists():
                _log("system", f"npm install в {name}…")
                subprocess.run(
                    ["npm", "install"],
                    cwd=str(cwd), check=True,
                    shell=(os.name == "nt"),
                )
        else:
            req = cwd / "requirements.txt"
            if req.exists():
                # наивная проверка — установлены ли пакеты
                _log("system", f"pip install -r requirements.txt в {name}…")
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "-r", str(req)],
                    check=True,
                )


def _prepare_env_files() -> None:
    pairs = [
        (ROOT / "conturai-manager"  / ".env.example", ROOT / "conturai-manager"  / ".env"),
        (ROOT / "conturai-backend"  / ".env.example", ROOT / "conturai-backend"  / ".env"),
    ]
    for src, dst in pairs:
        if src.exists() and not dst.exists():
            shutil.copy(src, dst)
            _log("system", f"создан {dst.relative_to(ROOT)} из .env.example")


def main() -> None:
    _check_prereqs()
    _log("system", f"Корень проекта: {ROOT}")

    _log("system", "Запуск postgres через docker-compose.dev.yml…")
    try:
        subprocess.run(
            ["docker", "compose", "-f", "docker-compose.dev.yml", "up", "-d"],
            cwd=str(ROOT), check=True,
        )
    except subprocess.CalledProcessError:
        _log("system", "Не удалось поднять postgres")
        sys.exit(1)

    _prepare_env_files()
    _ensure_component_deps()

    procs: list[tuple[str, subprocess.Popen]] = []

    _log("manager", "запуск на :8080")
    procs.append(("manager", _spawn(
        "manager",
        COMPONENTS["manager"],
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", "0.0.0.0", "--port", "8080", "--reload"],
    )))

    time.sleep(2)

    _log("backend", "запуск на :8000")
    procs.append(("backend", _spawn(
        "backend",
        COMPONENTS["backend"],
        [sys.executable, "-m", "uvicorn", "src.main:app",
         "--host", "0.0.0.0", "--port", "8000", "--reload"],
    )))

    time.sleep(1)

    _log("frontend", "запуск на :5173")
    npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
    procs.append(("frontend", _spawn(
        "frontend",
        COMPONENTS["frontend"],
        [npm_cmd, "run", "dev"],
    )))

    _log("system", "==========================================")
    _log("system", " Frontend: http://localhost:5173")
    _log("system", " Backend:  http://localhost:8000/api/health")
    _log("system", " Manager:  http://localhost:8080")
    _log("system", " Postgres: localhost:5432")
    _log("system", " Ctrl+C — остановить всё")
    _log("system", "==========================================")

    def _shutdown(*_):
        _log("system", "остановка…")
        for name, p in procs:
            if p.poll() is None:
                try:
                    if os.name == "nt":
                        p.terminate()
                    else:
                        p.send_signal(signal.SIGTERM)
                except Exception:
                    pass
        time.sleep(1)
        for name, p in procs:
            if p.poll() is None:
                try:
                    p.kill()
                except Exception:
                    pass
        try:
            subprocess.run(
                ["docker", "compose", "-f", "docker-compose.dev.yml", "stop"],
                cwd=str(ROOT),
            )
        except Exception:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, _shutdown)
    if os.name != "nt":
        signal.signal(signal.SIGTERM, _shutdown)

    while True:
        time.sleep(1)
        alive = [n for n, p in procs if p.poll() is None]
        if not alive:
            _log("system", "все процессы завершились")
            _shutdown()
        # если упал кто-то один — показываем
        for name, p in procs:
            if p.poll() is not None and p.returncode != 0:
                _log("system", f"{name} завершился с кодом {p.returncode}")


if __name__ == "__main__":
    main()