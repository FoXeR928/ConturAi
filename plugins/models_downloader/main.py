"""
Плагин управления моделями: скачивание с HF Hub в /models, прогресс, удаление.
Запускается ядром как отдельный subprocess (local plugin).
"""

import os
import shutil
import threading
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

MODELS_DIR = Path(os.environ.get("MODELS_DIR", "/models"))
MODELS_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

_jobs: dict[str, dict] = {}
_lock = threading.Lock()


# ==============================================================================
# Утилиты
# ==============================================================================

def _dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    total = 0
    for p in path.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                total += p.stat().st_size
        except OSError:
            pass
    return total


def _download_worker(job_id: str, repo_id: str, target: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
        with _lock:
            _jobs[job_id]["status"] = "downloading"
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(target),
            resume_download=True,
        )
        with _lock:
            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["finished_at"] = time.time()
    except Exception as e:
        with _lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)[:500]
            _jobs[job_id]["finished_at"] = time.time()


def _progress_worker(job_id: str, target: Path) -> None:
    while True:
        with _lock:
            job = _jobs.get(job_id)
            if not job or job["status"] not in ("pending", "downloading"):
                return
        size = _dir_size(target)
        with _lock:
            if job_id in _jobs:
                _jobs[job_id]["bytes_downloaded"] = size
        time.sleep(2)


# ==============================================================================
# API
# ==============================================================================

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/models")
async def list_models():
    models = []
    for entry in sorted(MODELS_DIR.iterdir()):
        if not entry.is_dir() or entry.name.startswith("."):
            continue
        models.append({
            "name": entry.name,
            "path": str(entry),
            "size_bytes": _dir_size(entry),
            "complete": (entry / "config.json").exists(),
        })
    return {"result": True, "models": models}


class DownloadRequest(BaseModel):
    model_id: str                       # "Qwen/Qwen2.5-1.5B-Instruct"
    target_name: str | None = None      # опциональное имя папки


@app.post("/download")
async def download(req: DownloadRequest):
    target_name = req.target_name or req.model_id.replace("/", "--")
    target = MODELS_DIR / target_name

    if target.exists() and (target / "config.json").exists():
        raise HTTPException(409, f"Модель уже скачана: {target_name}")

    job_id = str(uuid.uuid4())
    with _lock:
        _jobs[job_id] = {
            "job_id": job_id,
            "status": "pending",
            "model_id": req.model_id,
            "target_name": target_name,
            "target_dir": str(target),
            "bytes_downloaded": 0,
            "error": None,
            "started_at": time.time(),
            "finished_at": None,
        }
    threading.Thread(
        target=_download_worker, args=(job_id, req.model_id, target), daemon=True
    ).start()
    threading.Thread(
        target=_progress_worker, args=(job_id, target), daemon=True
    ).start()
    return {"result": True, "job_id": job_id, "target_dir": str(target)}


@app.get("/jobs")
async def list_jobs():
    with _lock:
        return {"result": True, "jobs": list(_jobs.values())}


@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    with _lock:
        job = _jobs.get(job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return {"result": True, "job": job}


@app.delete("/models/{name}")
async def delete_model(name: str):
    target = (MODELS_DIR / name).resolve()
    if target.parent != MODELS_DIR.resolve():
        raise HTTPException(400, "invalid path")
    if not target.is_dir():
        raise HTTPException(404, "model not found")
    shutil.rmtree(target)
    return {"result": True, "message": f"Удалено: {name}"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PLUGIN_PORT", "8000"))
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")