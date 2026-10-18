"""
Скачивает модели в локальную папку ./models
Запускать на машине с интернетом ОДИН раз:
    uv run python scripts/download_models.py
"""
from pathlib import Path

from huggingface_hub import snapshot_download

ROOT = Path(__file__).resolve().parent.parent / "models"
ROOT.mkdir(exist_ok=True)

MODELS = {
    "multilingual-e5-large": "intfloat/multilingual-e5-large",
    "Qwen2.5-0.5B-Instruct": "Qwen/Qwen2.5-0.5B-Instruct",
}

for local_name, repo_id in MODELS.items():
    target = ROOT / local_name
    if target.exists() and any(target.iterdir()):
        print(f"[skip] {local_name} уже скачана")
        continue
    print(f"[download] {repo_id} → {target}")
    snapshot_download(
        repo_id=repo_id,
        local_dir=str(target),
        local_dir_use_symlinks=False,
        ignore_patterns=["*.msgpack", "*.h5", "*.ot"],
    )
    print(f"[ok] {local_name}")