import secrets
import string
from pathlib import Path

# Путь к .env файлу (ищем его в корне бэкенда)
ENV_FILE = Path(__file__).resolve().parent.parent / ".env"
ENV_EXAMPLE = Path(__file__).resolve().parent.parent / ".env.example"


def generate_password(length=32) -> str:
    """Генерирует надежный пароль."""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def main():
    if ENV_FILE.exists():
        print(f"Файл {ENV_FILE} уже существует. Пропускаем генерацию.")
        return

    if not ENV_EXAMPLE.exists():
        print(f"Ошибка: Не найден {ENV_EXAMPLE}")
        return

    print("Первый запуск: генерация паролей и создание .env")
    
    # Генерируем логин и пароль для БД
    # Логин начинается с буквы, чтобы избежать проблем в SQL
    db_user = "db_" + generate_password(8).lower() 
    db_password = generate_password(32)

    # Читаем шаблон
    content = ENV_EXAMPLE.read_text(encoding="utf-8")

    # Заменяем плейсхолдеры
    content = content.replace("DB_USER=conturai", f"DB_USER={db_user}")
    content = content.replace("DB_PASSWORD=conturai", f"DB_PASSWORD={db_password}")
    content = content.replace("DB_NAME=conturai", "DB_NAME=conturai")

    # Записываем
    ENV_FILE.write_text(content, encoding="utf-8")
    
    print(f"Создан файл {ENV_FILE}")
    print(f"Пользователь БД: {db_user}")
    print(f"Пароль БД:       {db_password}")
    print("Сохраните эти данные! Они также записаны в .env")


if __name__ == "__main__":
    main()