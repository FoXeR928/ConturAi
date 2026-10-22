#!/usr/bin/env python3
"""ConturAI — единый .env + docker-compose переключатель. Только stdlib."""
import argparse
import secrets
import string
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"
COMPOSE_FILE = ROOT / "docker-compose.yml"
COMPOSE_TEMPLATE = ROOT / "scripts" / "templates"


PLATFORMS = {
    "nvidia": {
        "VLLM_IMAGE": "vllm/vllm-openai:latest",
        "VLLM_DTYPE": "auto",
        "VLLM_CPU_KVCACHE_SPACE": "",
        "VLLM_MAX_MODEL_LEN": "4096",
        "VLLM_MEM_LIMIT": "12g",
        "PG_MEM_LIMIT": "1g",
        "BACKEND_MEM_LIMIT": "2g",
        "FRONTEND_MEM_LIMIT": "256m",
        "PYTORCH_INDEX": "https://download.pytorch.org/whl/cu121",
        "EMBEDDING_MODEL_PATH": "/models/multilingual-e5-large",
        "EMBEDDING_DIM": "1024",
        "MODELS_TO_DOWNLOAD": (
            "intfloat/multilingual-e5-large:multilingual-e5-large,"
            "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
        ),
    },
    "amd": {
        "VLLM_IMAGE": "rocm/vllm:latest",
        "VLLM_DTYPE": "auto",
        "VLLM_CPU_KVCACHE_SPACE": "",
        "VLLM_MAX_MODEL_LEN": "4096",
        "VLLM_MEM_LIMIT": "12g",
        "PG_MEM_LIMIT": "1g",
        "BACKEND_MEM_LIMIT": "2g",
        "FRONTEND_MEM_LIMIT": "256m",
        "PYTORCH_INDEX": "https://download.pytorch.org/whl/rocm6.1",
        "EMBEDDING_MODEL_PATH": "/models/multilingual-e5-large",
        "EMBEDDING_DIM": "1024",
        "MODELS_TO_DOWNLOAD": (
            "intfloat/multilingual-e5-large:multilingual-e5-large,"
            "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
        ),
    },
    "cpu": {
        "VLLM_IMAGE": "vllm/vllm-openai-cpu:latest",
        "VLLM_DTYPE": "float32",
        "VLLM_CPU_KVCACHE_SPACE": "4",
        "VLLM_MAX_MODEL_LEN": "2048",
        "VLLM_MEM_LIMIT": "8g",
        "PG_MEM_LIMIT": "1g",
        "BACKEND_MEM_LIMIT": "2g",
        "FRONTEND_MEM_LIMIT": "256m",
        "PYTORCH_INDEX": "https://download.pytorch.org/whl/cpu",
        "EMBEDDING_MODEL_PATH": "/models/multilingual-e5-large",
        "EMBEDDING_DIM": "1024",
        "MODELS_TO_DOWNLOAD": (
            "intfloat/multilingual-e5-large:multilingual-e5-large,"
            "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
        ),
    },
    "dev": {
        "VLLM_IMAGE": "vllm/vllm-openai-cpu:latest",
        "VLLM_DTYPE": "float32",
        "VLLM_CPU_KVCACHE_SPACE": "1",
        "VLLM_MAX_MODEL_LEN": "1024",
        "VLLM_MEM_LIMIT": "3g",
        "PG_MEM_LIMIT": "1g",
        "BACKEND_MEM_LIMIT": "1g",
        "FRONTEND_MEM_LIMIT": "256m",
        "PYTORCH_INDEX": "https://download.pytorch.org/whl/cpu",
        "EMBEDDING_MODEL_PATH": "/models/granite-embedding-97m-multilingual-r2",
        "EMBEDDING_DIM": "384",
        "MODELS_TO_DOWNLOAD": (
            "ibm-granite/granite-embedding-97m-multilingual-r2:"
            "granite-embedding-97m-multilingual-r2,"
            "Qwen/Qwen2.5-0.5B-Instruct:Qwen2.5-0.5B-Instruct"
        ),
    },
}


def _generate_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def _update_env(updates: dict[str, str]) -> None:
    if not ENV_FILE.exists():
        print(f"[ERROR] Не найден {ENV_FILE}. Сначала: env_tool.py setup-env")
        raise SystemExit(1)
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    seen: set[str] = set()
    out: list[str] = []
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                out.append(f"{key}={updates[key]}")
                seen.add(key)
                continue
        out.append(line)
    for key, value in updates.items():
        if key not in seen:
            out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"[OK] .env обновлён: {', '.join(updates.keys())}")


def _write_compose(platform: str) -> None:
    src = COMPOSE_TEMPLATE / f"docker-compose.{platform}.yml"
    if not src.exists():
        print(f"[ERROR] Не найден шаблон {src}")
        raise SystemExit(1)
    COMPOSE_FILE.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[OK] docker-compose.yml перезаписан ({platform})")


def cmd_setup_env() -> None:
    if ENV_FILE.exists():
        print(f"[INFO] {ENV_FILE} уже существует. Пропускаем.")
        return
    if not ENV_EXAMPLE.exists():
        print(f"[ERROR] Не найден {ENV_EXAMPLE}")
        raise SystemExit(1)
    db_user = "conturai_user"
    db_password = _generate_password(32)
    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    content = content.replace("DB_USER=conturai_user", f"DB_USER={db_user}")
    content = content.replace("DB_PASSWORD=conturai", f"DB_PASSWORD={db_password}")
    ENV_FILE.write_text(content, encoding="utf-8")
    print(f"[OK] Создан {ENV_FILE}")
    print(f"  DB_USER={db_user}")
    print(f"  DB_PASSWORD={db_password}")


def cmd_use_platform(args: argparse.Namespace) -> None:
    if args.platform not in PLATFORMS:
        print(f"[ERROR] Неизвестная платформа: {args.platform}")
        raise SystemExit(1)
    _update_env(PLATFORMS[args.platform])
    _write_compose(args.platform)
    print(f"[OK] Платформа: {args.platform}")


def main() -> None:
    parser = argparse.ArgumentParser(description="ConturAI env/compose tool")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("setup-env", help="Создать .env с паролями")
    p = sub.add_parser("use-platform", help="Переключить .env и docker-compose.yml")
    p.add_argument("platform", choices=list(PLATFORMS.keys()))
    args = parser.parse_args()

    if args.command == "setup-env":
        cmd_setup_env()
    elif args.command == "use-platform":
        cmd_use_platform(args)


if __name__ == "__main__":
    main()