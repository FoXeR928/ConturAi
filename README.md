# ConturAI

**ConturAI** — это полностью локальный AI-ассистент с поддержкой RAG (Retrieval-Augmented Generation). Проект объединяет современный веб-интерфейс, высокопроизводительный инференс больших языковых моделей через **vLLM** и векторный поиск на базе **PostgreSQL (pgvector)**.

Система автономна, не требует доступа к интернету (после скачивания моделей) и поддерживает работу с таблицами, PDF, Word и Excel документами.

## Ключевые возможности

- **Полностью локальная работа:** без внешних API.
- **RAG на базе PostgreSQL + pgvector:** быстрый поиск по векторной базе (HNSW).
- **vLLM для инференса:** OpenAI-совместимый API.
- **Динамические настройки:** параметры генерации, RAG и промты хранятся в БД и меняются на лету без перезапуска.
- **Умный парсинг документов:** извлечение текста и таблиц из PDF, DOCX, XLSX.
- **Хранение оригиналов:** возможность скачать загруженный ранее документ.
- **Современный фронтенд:** React, TypeScript, Vite, Tailwind CSS.
- **Гибкая установка:** Docker Compose с поддержкой NVIDIA, AMD (ROCm) и CPU.

## Технологический стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), uv.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS.
- **База данных:** PostgreSQL 16 + pgvector.
- **AI / LLM:** vLLM, SentenceTransformers (`multilingual-e5-large`).
- **Инфраструктура:** Docker, Docker Compose.

---

## Быстрый старт (Docker)

Для работы потребуется **Docker** и **Docker Compose**.

### 1. Клонирование репозитория

```bash
git clone https://github.com/FoXeR928/ConturAi.git
cd ConturAi
```

### 2. Запуск установки

Проект включает интерактивный скрипт установки, который сам создаст конфиги, скачает модели, поднимет контейнеры и создаст администратора.

**Для Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Для Windows:**
```cmd
install.bat
```

### 3. Выбор платформы

При запуске скрипт спросит, на каком оборудовании вы работаете:
1. **NVIDIA (CUDA)** — для видеокарт NVIDIA (RTX, A100 и т.д.).
2. **AMD (ROCm)** — для видеокарт AMD.
3. **CPU** — для тестирования без GPU (медленно, но работает).
4. **DEV (слабый ПК)** — для ПК с 4–8 ГБ ОЗУ.

Скрипт автоматически пропишет нужные настройки в `.env`, скачает подходящую версию PyTorch и запустит контейнеры.

### 4. Данные для входа

После завершения установки скрипт выведет в консоль логин и **сгенерированный пароль администратора**.
- **Логин:** `admin`
- **Пароль:** *(смотрите в логах `reset-admin` в самом конце установки)*

> Если вы забыли пароль, выполните:
> `docker compose exec backend python scripts/manage.py reset-admin`

---

## Доступ к сервисам

- **Веб-интерфейс:** `http://localhost:3000`
- **Swagger API:** `http://localhost:8000/docs`
- **Статус сервера:** `http://localhost:8000/status`
- **vLLM API:** `http://localhost:8080/v1`

---

## Управление и обслуживание

Все команды выполняются из корня проекта.

### Команды `manage.py` (внутри контейнера)

```bash
# Сбросить пароль администратора
docker compose exec backend python scripts/manage.py reset-admin

# Скачать модели (пропускает уже скачанные)
docker compose exec backend python scripts/manage.py download-models

# Перекачать модели (если что-то сломалось)
docker compose exec backend python scripts/manage.py download-models --force
```

### Полезные команды Docker

```bash
# Пересобрать бэкенд после правок кода
docker compose up -d --build backend

# Посмотреть логи
docker compose logs -f backend vllm

# Полностью остановить и удалить данные (сброс БД)
docker compose down -v
```

---

## Решение проблем

### Ошибка `Read-only file system` при скачивании моделей
В `docker-compose.yml` у сервиса `backend` том `./models` должен быть примонтирован **без** флага `:ro`. Флаг `:ro` оставляем только для сервиса `vllm`.

### Ошибка `password authentication failed`
Если вы удалили `.env` или пересоздали БД, пароли могли разойтись. Выполните полную переустановку:
```bash
docker compose down -v
./install.sh
```

### Ошибка `Connection error` в чате
vLLM не успел загрузить модель. Проверьте статус:
```bash
docker compose ps vllm
docker compose logs --tail=50 vllm
```
Если модель загружается (на CPU это может занять несколько минут) — просто подождите.

### Модель выводит таблицу в виде черного блока кода
Модель обернула таблицу в ```markdown. Убедитесь, что на фронтенде установлен `remark-gfm` (файл `ChatWindow.tsx`), а в промтах добавлен запрет на использование тройных кавычек для таблиц.

---