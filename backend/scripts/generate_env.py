import secrets
import string
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT_DIR / ".env"
ENV_EXAMPLE = ROOT_DIR / ".env.example"


def generate_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def main() -> None:
    if ENV_FILE.exists():
        print("[INFO] Файл .env уже существует. Пропускаем генерацию.")
        return
    if not ENV_EXAMPLE.exists():
        print("[ERROR] Не найден .env.example")
        return

    print("[INFO] Генерация паролей и создание .env...")
    db_user = "conturai_user"
    db_password = generate_password(32)

    content = ENV_EXAMPLE.read_text(encoding="utf-8")
    content = content.replace("DB_USER=conturai_user", f"DB_USER={db_user}")
    content = content.replace("DB_PASSWORD=conturai", f"DB_PASSWORD={db_password}")

    ENV_FILE.write_text(content, encoding="utf-8")

    print("[OK] Создан файл .env")
    print(f"     DB_USER:     {db_user}")
    print(f"     DB_PASSWORD: {db_password}")


if __name__ == "__main__":
    main()