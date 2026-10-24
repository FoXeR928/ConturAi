# ConturAI v2.0.0

**ConturAI** — полностью локальный AI-ассистент с поддержкой RAG (Retrieval-Augmented Generation) для работы с корпоративными документами. Система объединяет современный веб-интерфейс, высокопроизводительный инференс больших языковых моделей через **vLLM** и векторный поиск на базе **PostgreSQL (pgvector)**.

Работает автономно, без доступа к интернету (после скачивания моделей). Поддерживает извлечение таблиц из PDF, DOCX и XLSX.

## Что нового в версии 2.0.0

Эта версия знаменует **полную смену инфраструктуры** по сравнению с версией 1.x (Ragi_AI). Проект переработан с нуля.

### Миграция с Qdrant на PostgreSQL + pgvector

- **Векторная база теперь живёт в PostgreSQL.** Отдельный сервис Qdrant больше не нужен.
- Один контейнер БД вместо двух (PostgreSQL + Qdrant) — проще бэкапить и мониторить.
- HNSW-индекс для cosine-поиска работает напрямую через расширение `pgvector`.
- Все данные (пользователи, чаты, документы, эмбеддинги) теперь в единой транзакционной БД.

### Миграция с Ollama на vLLM

- **LLM инференс переехал на vLLM** — в 5–10 раз быстрее за счёт PagedAttention.
- vLLM предоставляет OpenAI-совместимый API (`/v1/chat/completions`), поэтому бэкенд не зависит от реализации LLM.
- Поддержка GPU NVIDIA (CUDA), AMD (ROCm) и CPU через разные образы.
- Модели скачиваются локально в `./models/`, vLLM работает полностью offline.

### Прочие улучшения

- **Асинхронный бэкенд** (FastAPI + SQLAlchemy async + asyncpg).
- **Динамические параметры** генерации, RAG и промтов хранятся в БД — меняются без перезапуска.
- **UUID** для всех идентификаторов (защита от перебора).
- **Умный парсинг** PDF/DOCX/XLSX с извлечением таблиц в Markdown.
- **Хранение оригиналов** загруженных файлов с возможностью скачать.
- **Гибкая установка**: одна команда выбирает платформу (NVIDIA / AMD / CPU) и модель.
- **Полное покрытие тестами** (pytest + vitest).

## Технологический стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), uv.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS.
- **БД:** PostgreSQL 16 + pgvector (HNSW).
- **LLM:** vLLM (NVIDIA / AMD / CPU).
- **Embeddings:** SentenceTransformers (`multilingual-e5-large`).
- **Инфраструктура:** Docker, Docker Compose.

## Архитектура

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Frontend   │────▶│   Backend    │────▶│    vLLM      │
│  (React/TS)  │     │  (FastAPI)   │     │ (OpenAI API) │
└──────────────┘     └──────┬───────┘     └──────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │  PostgreSQL  │
                     │  + pgvector  │
                     │ (users, docs,│
                     │  embeddings) │
                     └──────────────┘
```

## Требования

- **Docker** (версия 24+) и **Docker Compose** (v2).
- **Python 3.12+** (только для генерации `.env` и тестов).
- Оборудование:
  - **NVIDIA GPU** (≥8 ГБ VRAM для 1.5B модели).
  - **AMD GPU** с установленным ROCm 6.1+ (≥16 ГБ VRAM для 3B модели).
  - **CPU** (≥8 ГБ ОЗУ, медленно, только для тестов).

## Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/FoXeR928/ConturAi.git
cd ConturAi
```

### 2. Запуск установки

**Linux / macOS:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
install.bat
```

### 3. Интерактивная настройка

Скрипт спросит:

1. **Платформу**:
   - `1) nvidia` — CUDA (RTX 2070, A100 и т.д.)
   - `2) amd` — ROCm (Radeon RX 7900, W7900, 9070 и т.д.)
   - `3) cpu` — без GPU (медленно, для тестов)

2. **Модель** (влияет на VRAM и качество):

   | № | Модель | VRAM | Рекомендация |
   |---|---|---|---|
   | 1 | Qwen2.5-0.5B | ~1 ГБ | слабый ПК / CPU |
   | 2 | Qwen2.5-1.5B | ~4 ГБ | RTX 2070 (8 ГБ) |
   | 3 | Qwen2.5-3B | ~8 ГБ | AMD 9070 (16 ГБ) |
   | 4 | Qwen2.5-7B | ~16 ГБ | 24+ ГБ VRAM |

### 4. Данные для входа

После установки в консоль выведется:

```
========================================================================
  ДАННЫЕ ДЛЯ ВХОДА
  Логин:  admin
  Пароль: <сгенерированный>
  Пароль показывается один раз — сохраните его!
========================================================================
```

> Если забыли пароль: `docker compose exec backend python scripts/manage.py reset-admin`

## Доступ к сервисам

| Сервис | Адрес |
|---|---|
| Веб-интерфейс | http://localhost:3000 |
| Swagger API | http://localhost:8000/docs |
| Status | http://localhost:8000/status |
| vLLM API | http://localhost:8080/v1 |

## Тестирование

### Backend

```bash
cd backend
uv run pytest -v
```

Покрыто: API, безопасность, RAG, парсеры, сервисы чатов.

### Frontend

```bash
cd frontend
npm install
npm run test
```

Покрыто: рендеринг Markdown-таблиц, форма логина, панель пользователей, API-клиент.

## Управление

Все команды выполняются из корня проекта.

```bash
# Сброс пароля администратора
docker compose exec backend python scripts/manage.py reset-admin

# Скачать модели (пропускает уже скачанные)
docker compose exec backend python scripts/manage.py download-models

# Перекачать модели
docker compose exec backend python scripts/manage.py download-models --force

# Посмотреть логи
docker compose logs -f backend vllm

# Пересобрать после правок кода
docker compose up -d --build backend
```

## Переменные окружения

Все настройки — в `.env` (создаётся скриптом установки автоматически).

| Группа | Переменные |
|---|---|
| Приложение | `APP_NAME`, `APP_PORT`, `DEBUG` |
| База данных | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` |
| Пути | `DATA_DIR`, `MODELS_DIR` |
| Эмбеддинги | `EMBEDDING_MODEL_PATH`, `EMBEDDING_DIM` |
| vLLM | `VLLM_IMAGE`, `VLLM_MODEL_PATH`, `VLLM_MAX_MODEL_LEN` |

Параметры генерации (temperature, top_p, penalties, RAG-размеры) хранятся **в БД** и меняются через админку без перезапуска.

## Динамические параметры

Открыв `http://localhost:3000/admin` → вкладки:

- **Пользователи** — создание, блокировка, смена ролей.
- **Промты** — `system_prompt`, `user_prompt` с подсказками по доступным переменным.
- **Параметры LLM** — temperature, top_p, top_k, penalties, seed, лимиты RAG.
- **Документы** — загрузка (PDF/DOCX/XLSX), скачивание оригиналов, удаление.

Все изменения применяются к следующему запросу в чат без перезапуска контейнеров.

## Troubleshooting

### `Read-only file system` при скачивании моделей

Том `./models` для сервиса `backend` должен быть без `:ro`. Для `vllm` — с `:ro` (он только читает).

### `password authentication failed`

Пароль в `.env` не совпадает с `pgdata`. Полная переустановка:

```bash
docker compose down -v
./install.sh
```

### `Connection error` в чате

vLLM не успел загрузить модель. Проверить:

```bash
docker compose ps vllm
docker compose logs --tail=50 vllm
```

На CPU загрузка занимает 1–3 минуты.

## Миграция с версии 1.x (Ragi_AI)

Версия 2.0 **несовместима** со старой БД. Данные из Qdrant/SQLite не переносятся автоматически.

- Qdrant → pgvector: переиндексируйте все документы через админку.
- Ollama → vLLM: модели Ollama (`.bin`) несовместимы с vLLM (`.safetensors`), скачайте новые через `manage.py download-models`.