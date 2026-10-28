import os
import secrets
import shutil
import subprocess
import time
from pathlib import Path

# ==============================================================================
# БЛОК 1: ИНИЦИАЛИЗАЦИЯ ПУТЕЙ (КРИТИЧЕСКИ ВАЖНО ДЛЯ WINDOWS)
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.resolve()
COMPOSE_FILE = PROJECT_ROOT / "docker-compose.yml"

# ==============================================================================
# БЛОК 2: УТИЛИТЫ
# ==============================================================================

def run_cmd(cmd, check=True):
    print(f"\n[RUN] {' '.join(cmd)}")
    try:
        subprocess.run(cmd, check=check, cwd=PROJECT_ROOT)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Команда завершилась с ошибкой: {e}")
        return False
    return True

def dc(*args, check=True):
    return run_cmd(["docker", "compose", "-f", str(COMPOSE_FILE)] + list(args), check=check)

def regen_lock():
    print("\n[INFO] Пересборка uv.lock (обновление зависимостей)...")
    backend_path = PROJECT_ROOT / "backend"
    if not (backend_path / "pyproject.toml").exists():
        print("[WARN] Не найден backend/pyproject.toml, пропускаю.")
        return

    cmd = [
        "docker", "run", "--rm",
        "-v", f"{backend_path}:/app",
        "-w", "/app",
        "-e", "UV_PROJECT_ENVIRONMENT=/tmp/uv-venv",
        "python:3.12-slim",
        "sh", "-c", "pip install --quiet uv==0.5.11 && uv lock"
    ]
    if run_cmd(cmd):
        print("[OK] uv.lock успешно обновлен.")
    else:
        print("[WARN] Не удалось обновить uv.lock. Сборка может упасть.")

def update_env(file_path: Path, updates: dict):
    if not file_path.exists():
        return
    lines = file_path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    updated_keys = set()
    for line in lines:
        if "=" in line and not line.strip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}")
                updated_keys.add(key)
                continue
        new_lines.append(line)
    for key, val in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={val}")
    file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


# ==============================================================================
# БЛОК 3: УСТАНОВКА И НАСТРОЙКА
# ==============================================================================

def setup_env():
    env_path = PROJECT_ROOT / ".env"
    example_path = PROJECT_ROOT / ".env.example"
    
    if env_path.exists():
        print("[INFO] Файл .env уже существует. Сохраняю текущие настройки.")
        return False
        
    print("[INFO] Создание нового .env с безопасным паролем...")
    password = secrets.token_urlsafe(16)
    content = example_path.read_text(encoding="utf-8")
    content = content.replace("DB_USER=", "DB_USER=conturai_user")
    content = content.replace("DB_PASSWORD=", f"DB_PASSWORD={password}")
    env_path.write_text(content, encoding="utf-8")
    return True

def pick_platform():
    print("\nВыберите платформу:")
    print("  1) NVIDIA (CUDA)")
    print("  2) AMD (ROCm)")
    print("  3) CPU")
    choice = input("Номер [1]: ").strip() or "1"
    
    mode = "nvidia"
    if choice == "2": mode = "amd"
    if choice == "3": mode = "cpu"
    
    src = PROJECT_ROOT / f"templates/docker-compose.{mode}.yml"
    if src.exists():
        shutil.copy(src, COMPOSE_FILE)
        print(f"[OK] Конфигурация Docker настроена для {mode}")
    else:
        print(f"[ERROR] Не найден шаблон {src}")
    
    env_path = PROJECT_ROOT / ".env"
    if mode == "nvidia":
        update_env(env_path, {"PYTORCH_INDEX": "https://download.pytorch.org/whl/cu121", "VLLM_IMAGE": "vllm/vllm-openai:latest"})
    elif mode == "amd":
        update_env(env_path, {"PYTORCH_INDEX": "https://download.pytorch.org/whl/rocm6.1", "VLLM_IMAGE": "rocm/vllm:latest"})
    else:
        update_env(env_path, {"PYTORCH_INDEX": "https://download.pytorch.org/whl/cpu", "VLLM_IMAGE": "vllm/vllm-openai-cpu:latest"})

def pick_model():
    print("\nВыберите модель ИИ:")
    print("  1) Qwen2.5-0.5B (CPU / слабый ПК)")
    print("  2) Qwen2.5-1.5B (8-12 ГБ VRAM)")
    print("  3) Qwen2.5-3B   (16 ГБ VRAM)")
    print("  4) Qwen2.5-7B   (24+ ГБ VRAM)")
    print("  5) Своя модель (ввести HuggingFace ID)")
    choice = input("Номер [2]: ").strip() or "2"
    
    if choice == "5":
        repo_id = input("Введите HuggingFace repo_id (например, Qwen/Qwen2.5-14B-Instruct): ").strip()
        if not repo_id or "/" not in repo_id:
            print("[ERROR] Неверный ID. Должен быть формата 'Автор/Название'.")
            return pick_model()
        
        m_file = repo_id.split("/")[-1]
        max_len = input("Максимальная длина контекста (токенов) [4096]: ").strip() or "4096"
        m_name = repo_id
    else:
        models = {
            "1": ("Qwen/Qwen2.5-0.5B-Instruct", "Qwen2.5-0.5B-Instruct", "2048"),
            "2": ("Qwen/Qwen2.5-1.5B-Instruct", "Qwen2.5-1.5B-Instruct", "2048"),
            "3": ("Qwen/Qwen2.5-3B-Instruct", "Qwen2.5-3B-Instruct", "4096"),
            "4": ("Qwen/Qwen2.5-7B-Instruct", "Qwen2.5-7B-Instruct", "8192")
        }
        m_name, m_file, max_len = models.get(choice, models["2"])
    
    update_env(PROJECT_ROOT / ".env", {
        "VLLM_MODEL_PATH": f"/models/{m_file}",
        "VLLM_MAX_MODEL_LEN": max_len,
        "MODELS_TO_DOWNLOAD": f"intfloat/multilingual-e5-large:multilingual-e5-large,BAAI/bge-reranker-v2-m3:bge-reranker-v2-m3,{m_name}:{m_file}"
    })
    print(f"[OK] Выбрана модель: {m_file} (контекст: {max_len})")


# ==============================================================================
# БЛОК 4: БИЗНЕС-ЛОГИКА
# ==============================================================================

def do_install():
    is_new = setup_env()
    if is_new:
        pick_platform()
        pick_model()
        
    regen_lock()
        
    print("\n[INFO] Запуск сборки контейнеров (это может занять время)...")
    dc("down", "--remove-orphans", check=False)
    dc("up", "-d", "--build")
    
    print("\n[INFO] Ожидание инициализации базы данных (15 секунд)...")
    time.sleep(15)
    
    print("\n[INFO] Инициализация схемы БД...")
    dc("exec", "-T", "backend", "python", "scripts/manage.py", "init-db", check=False)
    print("\n[INFO] Создание администратора...")
    dc("exec", "-T", "backend", "python", "scripts/manage.py", "reset-admin", check=False)
        
    print("\n[SUCCESS] Установка завершена! Откройте http://localhost:3000")

def do_update():
    if not (PROJECT_ROOT / ".env").exists():
        print("[ERROR] Файл .env не найден. Сначала выполните Установку.")
        return

    print("\n[INFO] Обновление сервера и базы данных (данные сохраняются)...")
    
    regen_lock()
    
    print("[INFO] Пересборка контейнеров...")
    dc("down", "--remove-orphans", check=False)
    dc("up", "-d", "--build")
    
    print("\n[INFO] Ожидание запуска БД...")
    time.sleep(15)
    
    print("\n[INFO] Применение миграций БД...")
    dc("exec", "-T", "backend", "python", "scripts/manage.py", "migrate", check=False)
    
    print("\n[SUCCESS] Обновление завершено! Сервер перезапущен с новыми настройками.")

def do_full_reinstall():
    print("\n[WARN] ВНИМАНИЕ! Это удалит все данные, БД и .env!")
    confirm = input("Продолжить? (y/N): ").strip().lower()
    if confirm != "y":
        return
    
    print("[INFO] Удаление контейнеров и томов...")
    dc("down", "-v", "--remove-orphans", check=False)
    
    env_file = PROJECT_ROOT / ".env"
    if env_file.exists():
        env_file.unlink()
        
    do_install()


# ==============================================================================
# БЛОК 5: МЕНЮ
# ==============================================================================

def menu_containers():
    while True:
        print("\n--- Управление контейнерами ---")
        print("  1) Запустить (up -d)")
        print("  2) Остановить (stop)")
        print("  3) Перезапустить (restart)")
        print("  4) Пересобрать (up -d --build)")
        print("  5) Остановить и удалить (down)")
        print("  6) Логи (logs -f)")
        print("  0) Назад")
        c = input("Номер [0]: ").strip() or "0"
        if c == "1": dc("up", "-d")
        elif c == "2": dc("stop")
        elif c == "3": dc("restart")
        elif c == "4": 
            regen_lock()
            dc("up", "-d", "--build")
        elif c == "5": dc("down", "--remove-orphans")
        elif c == "6": 
            print("[INFO] Нажмите Ctrl+C для выхода из логов.")
            dc("logs", "-f", check=False)
        elif c == "0": return

def menu_manage():
    while True:
        print("\n--- Команды manage.py ---")
        print("  1) init-db (Создать таблицы)")
        print("  2) reset-admin (Сбросить пароль админа)")
        print("  3) migrate (Применить миграции)")
        print("  4) download-models (Скачать модели)")
        print("  5) reembed (Переиндексация RAG)")
        print("  6) backup (Резервная копия)")
        print("  0) Назад")
        c = input("Номер [0]: ").strip() or "0"
        
        cmd_prefix = ["exec", "-T", "backend", "python", "scripts/manage.py"]
        if c == "1": dc(*(cmd_prefix + ["init-db"]))
        elif c == "2": dc(*(cmd_prefix + ["reset-admin"]))
        elif c == "3": dc(*(cmd_prefix + ["migrate"]))
        elif c == "4": 
            print("[INFO] Запуск скачивания (через отдельный контейнер)...")
            dc("run", "--rm", "--no-deps", "-e", "HF_HUB_OFFLINE=0", "-e", "TRANSFORMERS_OFFLINE=0", "-e", "HF_DATASETS_OFFLINE=0", "backend", "python", "scripts/manage.py", "download-models")
        elif c == "5": dc(*(cmd_prefix + ["reembed"]))
        elif c == "6": dc(*(cmd_prefix + ["backup"]))
        elif c == "0": return

def main():
    print("==================================================")
    print("  ConturAI - Установщик и Менеджер")
    print("==================================================")
    
    while True:
        try:
            print("\nГлавное меню:")
            print("  1) Установка с нуля")
            print("  2) Обновление (обновить сервер и БД, сохранить данные)")
            print("  3) Полная переустановка (сброс БД и данных)")
            print("  4) Управление контейнерами")
            print("  5) Команды manage.py")
            print("  0) Выход")
            choice = input("Номер [1]: ").strip() or "1"
            
            if choice == "1":
                do_install()
            elif choice == "2":
                do_update()
            elif choice == "3":
                do_full_reinstall()
            elif choice == "4":
                menu_containers()
            elif choice == "5":
                menu_manage()
            elif choice == "0":
                print("До свидания!")
                break
        except EOFError:
            print("\n[ERROR] Ввод прерван. Выход.")
            break
        except KeyboardInterrupt:
            print("\n[ERROR] Выход по Ctrl+C.")
            break

if __name__ == "__main__":
    main()