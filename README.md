# ConturAI

**ConturAI** — полностью локальный AI-ассистент с поддержкой RAG (Retrieval-Augmented Generation) для работы с корпоративными документами. Система объединяет современный веб-интерфейс, высокопроизводительный инференс больших языковых моделей через **vLLM** и продвинутый гибридный поиск на базе **PostgreSQL (pgvector)**.

Работает автономно, без доступа к интернету (после скачивания моделей). Поддерживает извлечение таблиц из PDF, DOCX и XLSX.

## Ключевые возможности

### Инфраструктура и Бэкенд
- **Единая база данных:** PostgreSQL с расширением `pgvector` (HNSW-индекс) используется как для хранения бизнес-данных, так и для векторного поиска. Отдельные NoSQL-сервисы не требуются.
- **vLLM:** Высокопроизводительный инференс LLM с OpenAI-совместимым API. Поддержка GPU NVIDIA (CUDA), AMD (ROCm) и CPU.
- **Асинхронность:** FastAPI + SQLAlchemy async + asyncpg для высокой пропускной способности.
- **Гибридный поиск (RAG):** Комбинация векторного поиска (по смыслу) и полнотекстового поиска (BM25 по `tsvector`). Результаты объединяются через Reciprocal Rank Fusion (RRF) и пересортировываются Cross-Encoder'ом (Reranker) для максимальной точности.
- **Умный парсинг:** Извлечение текста и таблиц из PDF/DOCX/XLSX (с фолбэком на OCR).
- **Динамические настройки:** Параметры генерации, RAG и системные промты хранятся в БД и меняются на лету.

### Фронтенд и UX
- **Современный интерфейс:** React, TypeScript, Vite, Tailwind CSS.
- **Стриминг ответов (SSE):** Нейросеть отвечает в режиме реального времени, как в ChatGPT.
- **Модульный API-клиент** и обработка ошибок (Toast-уведомления вместо `alert`).
- **Рендеринг Markdown:** Полная поддержка таблиц (`remark-gfm`).

### Безопасность и Администрирование
- **RBAC (Ролевая модель):** Разделение прав на `admin`, `editor` и `user`.
- **Журнал аудита:** Логирование всех критичных действий (входы, загрузка/удаление файлов, смена настроек) с указанием IP.
- **Шифрование секретов:** API-ключи и чувствительные настройки в БД хранятся в зашифрованном виде (Fernet).
- **Управление доступом к файлам:** Заявки на скачивание документов, требующие одобрения администратора.
- **Мониторинг:** Встроенная панель отслеживания нагрузки на CPU, RAM, диск и GPU (NVIDIA/AMD).
- **База знаний (Few-Shot):** Добавление эталонных пар «Вопрос-Ответ» для повышения качества ответов без дообучения модели.
- **Бэкапы:** Управление резервными копиями БД и файлов прямо из веб-интерфейса.
- **Теги:** Фильтрация поиска по категориям документов.

## Технологический стек

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), uv.
- **Frontend:** React 18, TypeScript, Vite, Tailwind CSS.
- **БД:** PostgreSQL 16 + pgvector (HNSW).
- **LLM:** vLLM (NVIDIA / AMD / CPU).
- **Embeddings & Reranker:** SentenceTransformers (`multilingual-e5-large`, `bge-reranker-v2-m3`).
- **Инфраструктура:** Docker, Docker Compose.

## Архитектура
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