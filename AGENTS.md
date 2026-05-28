# AGENTS.md — Руководство для AI-агентов

Этот документ предназначен для AI-агентов (Opencode, Hermes, Cursor, Cline и других), работающих с кодовой базой **Scientific Library**.

---

## 📋 О Проекте

**Scientific Library** — приватная мульти-пользовательская система хранения научных PDF с:
- Автоматическим извлечением метаданных (GROBID)
- Гибридным поиском (FTS + векторный через pgvector)
- Интеграцией с Zotero через WebDAV
- MCP-сервером для LLM-агентов
- Групповыми коллекциями и RBAC

### Архитектура

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Compose                          │
│                                                             │
│   ┌──────────────┐    ┌─────────────────────────────┐       │
│   │   Caddy      │    │   PostgreSQL 16 + pgvector  │       │
│   │  (TLS, rev   │    └─────────────────────────────┘       │
│   │   proxy)     │    ┌─────────────────────────────┐       │
│   └──────┬───────┘    │           Redis             │       │
│          │            │  (queue, locks, rate-limit) │       │
│   ┌──────┴───────┐    └─────────────────────────────┘       │
│   │   Frontend   │    ┌─────────────────────────────┐       │
│   │ (React SPA)  │    │      GROBID (TEI/XML)       │       │
│   └──────┬───────┘    └─────────────────────────────┘       │
│          │            ┌─────────────────────────────┐       │
│   ┌──────┴───────┐    │   SentenceTransformers      │       │
│   │   Backend    │◄──►│        (embeddings)         │       │
│   │  (FastAPI)   │    └─────────────────────────────┘       │
│   │  - REST API  │    ┌─────────────────────────────┐       │
│   │  - WebDAV    │    │       Arq Worker            │       │
│   │  - MCP HTTP  │◄──►│  (PDF → GROBID → embed)     │       │
│   └──────────────┘    └─────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Структура Кода

### Backend (`/backend/app/`)

```
backend/app/
├── main.py              # Точка входа FastAPI, роуты, middleware
├── config.py            # Pydantic Settings (env variables)
├── db.py                # AsyncSession factory, engine
├── models/              # SQLAlchemy ORM модели
│   ├── __init__.py
│   ├── user.py          # users, user_sync_keys, mcp_tokens, refresh_tokens
│   ├── group.py         # groups, group_members
│   ├── item.py          # items (глобальный каталог)
│   ├── attachment.py    # attachments, user_attachment_blobs
│   ├── library_item.py  # library_items (user/group ownership)
│   ├── collection.py    # collections, library_item_collections
│   ├── tag.py           # tags, library_item_tags
│   ├── embedding.py     # document_embeddings (pgvector)
│   ├── citation.py      # citations
│   └── audit.py         # mcp_audit_log, processing_jobs
├── schemas/             # Pydantic схемы для API
│   ├── __init__.py
│   ├── auth.py
│   ├── user.py
│   ├── item.py
│   ├── collection.py
│   └── ...
├── api/v1/              # FastAPI routers
│   ├── auth.py          # /api/v1/auth/* (login, refresh, logout, me)
│   ├── users.py         # /api/v1/admin/users/*
│   ├── items.py         # /api/v1/items/* (upload, import-by-doi, CRUD)
│   ├── collections.py   # /api/v1/collections/*
│   ├── tags.py          # /api/v1/tags/*
│   ├── groups.py        # /api/v1/groups/*
│   ├── search.py        # /api/v1/search?q=...
│   ├── sync_keys.py     # /api/v1/me/sync-keys/*
│   ├── mcp_tokens.py    # /api/v1/me/mcp-tokens/*
│   └── admin.py         # /api/v1/admin/jobs/*, /stats
├── webdav/              # WebDAV сервер для Zotero
│   ├── provider.py      # DAVProvider (virtual FS mapping)
│   ├── auth.py          # DomainController (Basic Auth via sync_keys)
│   └── lock_redis.py    # LockManager (Redis TTL locks)
├── mcp/                 # MCP Server (Model Context Protocol)
│   ├── server.py        # Streamable HTTP mount, MCP app
│   ├── tools.py         # Tool handlers (search_papers, get_paper_details...)
│   └── auth.py          # Middleware для MCP token валидации
├── services/            # Бизнес-логика
│   ├── embeddings/
│   │   ├── base.py      # EmbeddingProvider Protocol
│   │   ├── specter2.py  # Specter2Provider (sentence-transformers)
│   │   └── ollama.py    # OllamaProvider (альтернатива)
│   ├── grobid.py        # GROBID client (processFulltextDocument)
│   ├── crossref.py      # Crossref API client (metadata enrichment)
│   ├── storage.py       # AbstractStorage + LocalStorage + S3Storage
│   ├── search.py        # Hybrid search (vector + FTS + RRF merge)
│   ├── auth.py          # JWT, bcrypt hash/verify
│   └── quota.py         # Storage quota checks
├── workers/             # Arq background jobs
│   ├── settings.py      # WorkerSettings (Redis, functions)
│   ├── pdf_pipeline.py  # process_zotero_upload, process_uploaded_pdf
│   ├── crossref.py      # crossref_enrich
│   └── citations.py     # resolve_citations
└── cli.py               # CLI команды (create-admin, reindex)
```

### Frontend (`/frontend/src/`)

```
frontend/src/
├── main.tsx             # Точка входа React
├── App.tsx              # Роутинг (React Router 6)
├── index.css            # Tailwind CSS imports
├── api/                 # API clients (axios instances)
│   ├── client.ts        # Base axios instance with interceptors
│   ├── auth.ts          # login, refresh, logout, me
│   ├── items.ts         # items CRUD, upload, search
│   ├── collections.ts
│   ├── groups.ts
│   └── ...
├── components/          # UI компоненты (shadcn/ui + custom)
│   ├── ui/              # Базовые компоненты (Button, Input, Dialog...)
│   ├── layout/          # Sidebar, Header, PageLayout
│   ├── items/           # ItemCard, ItemList, ItemDetail, PDFViewer
│   ├── collections/     # CollectionTree, CollectionItem
│   ├── search/          # SearchBar, SearchResults, FilterPanel
│   └── ...
├── pages/               # Страницы
│   ├── Login.tsx
│   ├── Library.tsx      # Основной view (sidebar + items list)
│   ├── ItemDetail.tsx   # /items/:id
│   ├── Search.tsx       # /search?q=...
│   ├── Groups.tsx
│   ├── GroupLibrary.tsx
│   ├── Profile.tsx
│   ├── Integrations.tsx # Sync keys, MCP tokens, Zotero setup
│   └── admin/
│       ├── Users.tsx
│       └── Jobs.tsx
├── hooks/               # Custom React hooks
│   ├── useAuth.ts
│   ├── useItems.ts
│   ├── useCollections.ts
│   └── ...
├── store/               # Zustand stores
│   ├── auth.ts          # Auth state (user, tokens, login/logout)
│   └── ui.ts            # UI state (sidebar open, modals)
├── lib/                 # Utilities
│   ├── utils.ts         # cn() helper, formatters
│   └── validations.ts   # Zod schemas
└── types/               # TypeScript типы
    ├── index.ts
    ├── api.ts
    └── ...
```

---

## 🔑 Ключевые Концепции

### 1. Модель Данных

- **`items`** — глобальный дедуплицированный каталог (по DOI или fingerprint)
- **`library_items`** — персональные/групповые «ссылки» на items с overrides (title, notes)
- **`attachments`** — дедуплицированные PDF по SHA-256
- **`user_attachment_blobs`** — raw Zotero ZIP'ы (для отдачи обратно)
- **`document_embeddings`** — векторные эмбеддинги чанков (pgvector, 768d)

### 2. Аутентификация

| Тип | Где используется | Хранение |
|-----|------------------|----------|
| JWT Access | REST API (SPA) | Memory в SPA, `Authorization: Bearer` |
| JWT Refresh | Token rotation | httpOnly Secure cookie |
| Sync Key | WebDAV (Zotero) | `user_sync_keys.key_value`, Basic Auth password |
| MCP Token | MCP Server | `mcp_tokens.token_hash`, `Authorization: Bearer mcp_live_...` |

### 3. PDF Processing Pipeline

```
PUT .zip (WebDAV) / POST /upload (API)
    ↓
Сохранение raw blob
    ↓
Arq job: process_zotero_upload / process_uploaded_pdf
    ↓
1. Unzip → extract PDF
2. SHA-256 → dedup check
3. Store PDF → storage/pdf/<sha[:2]>/<sha>.pdf
4. GROBID → TEI/XML → metadata extraction
5. Crossref enrichment (если DOI найден)
6. Upsert items (by DOI/fingerprint)
7. Create library_items(user_id/group_id, item_id)
8. Chunk by sections → embeddings → document_embeddings
9. Extract text → attachments.extracted_text (FTS)
10. resolve_citations (match references to existing items)
```

### 4. Hybrid Search

```python
# 1. Векторный поиск (HNSW, top 100)
SELECT item_id, 1 - (embedding <=> query_vector) AS sim
FROM document_embeddings
WHERE item_id IN (:visible_item_ids)
ORDER BY embedding <=> query_vector
LIMIT 100

# 2. FTS поиск (GIN, top 100)
SELECT item_id, ts_rank_cd(extracted_text_tsv, query) AS rank
FROM attachments
WHERE item_id IN (:visible_item_ids)
  AND extracted_text_tsv @@ query
ORDER BY rank DESC
LIMIT 100

# 3. RRF merge (в Python, k=60)
score(d) = 1/(60 + rank_vec(d)) + 1/(60 + rank_fts(d))
→ return top 20
```

### 5. MCP Tools

| Tool | Args | Returns |
|------|------|---------|
| `search_papers` | query, limit, scope | [{item_id, title, authors, year, doi, abstract, score}] |
| `get_paper_details` | item_id | Full metadata + collections + tags + has_pdf |
| `read_paper_chunks` | item_id, query, top_k | [{section, text, score}] |
| `list_collections` | scope? | Tree of collections |
| `list_items_in_collection` | collection_id, limit | [items] |
| `get_citations` | item_id, direction | [related items] |

---

## 🛠️ Инструменты Разработчика

### Backend

```bash
# Запустить backend локально
cd backend
poetry install
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Запустить worker
poetry run arq app.workers.settings.WorkerSettings

# Создать миграцию
docker compose run --rm backend alembic revision --autogenerate -m "Description"

# Применить миграции
docker compose run --rm backend alembic upgrade head

# Запустить тесты
poetry run pytest tests/unit
poetry run pytest tests/integration  # требует testcontainers

# Линтинг
poetry run ruff check .
poetry run mypy .
```

### Frontend

```bash
cd frontend
npm install

# Dev server
npm run dev

# Build
npm run build

# Tests
npm run test
npm run test:ui

# Typecheck
npm run typecheck

# Lint
npm run lint
```

### Docker Compose

```bash
# Запустить всё
make up

# Остановить
make down

# Логи
make logs

# Миграции
make migrate

# Smoke tests
make smoke-test

# DB shell
make db-shell

# Redis CLI
make redis-cli
```

---

## 📝 Conventions

### Backend (Python)

- **Type hints**: Обязательно для всех функций
- **Docstrings**: Google style для публичных API
- **Async**: Использовать `async/await` везде, где возможен I/O
- **Dependency Injection**: FastAPI Depends для DI
- **Error Handling**: structlog для логирования, HTTPException для API ошибок
- **Pydantic v2**: `model_validate`, `model_dump` вместо `parse_obj`, `dict`

### Frontend (TypeScript/React)

- **Functional Components**: Только функциональные компоненты с hooks
- **TanStack Query**: Для server state management
- **Zustand**: Для client state (auth, UI)
- **shadcn/ui**: Базовые UI компоненты
- **Tailwind**: Стилизация через utility classes
- **Zod**: Валидация форм

### Git

- **Branch naming**: `feature/description`, `fix/description`, `chore/description`
- **Commits**: Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- **PR**: Один PR — одна фича/фикс

---

## 🔍 Поиск по Кодавой Базе

### Найти модель
```bash
grep -r "class.*BaseModel" backend/app/models/
```

### Найти API endpoint
```bash
grep -r "@router\.(get|post|put|delete)" backend/app/api/
```

### Найти worker функцию
```bash
grep -r "async def.*worker" backend/app/workers/
```

### Найти MCP tool
```bash
grep -r "@mcp.tool" backend/app/mcp/
```

### Найти SQL query
```bash
grep -r "select\|insert\|update\|delete" backend/app/services/ -i
```

---

## 🧪 Тестирование

### Backend Tests

```python
# Unit test example
def test_embedding_dimension():
    provider = Specter2Provider()
    assert provider.dimension == 768

# Integration test example (testcontainers)
async def test_pdf_pipeline():
    async with PostgresContainer() as db:
        async with RedisContainer() as redis:
            # Setup
            # Run pipeline
            # Assert items, attachments, embeddings created
```

### Frontend Tests

```typescript
// Component test example
test('renders item card', () => {
  render(<ItemCard item={mockItem} />)
  expect(screen.getByText('Test Title')).toBeInTheDocument()
})

// E2E test example (Playwright)
test('login and upload', async ({ page }) => {
  await page.goto('/login')
  await page.fill('[name=email]', 'test@example.com')
  await page.fill('[name=password]', 'password')
  await page.click('button[type=submit]')
  // ... upload flow
})
```

---

## 🚨 Common Pitfalls

### 1. Dimension Mismatch Embeddings

При смене модели эмбеддингов:
```bash
# Проверить текущую размерность
docker compose run --rm backend python -c "from app.config import settings; print(settings.EMBEDDING_DIM)"

# Если mismatch — нужен reindex
docker compose run --rm backend python -m app.cli reindex --confirm
```

### 2. WebDAV LOCK/UNLOCK

- LOCK хранится в Redis с TTL 10 минут
- При ошибках — проверить `docker compose logs redis`

### 3. GROBID Timeout

- GROBID стартует ~30 секунд
- При timeout — увеличить таймаут в `services/grobid.py`

### 4. Quota Exceeded

- Проверяется на PUT через `services/quota.py`
- Ошибка: `507 Insufficient Storage`

### 5. MCP Token Rate Limit

- 60 запросов в минуту на токен
- Реализовано через Redis token bucket в `mcp/auth.py`

---

## 📚 Дополнительные Ресурсы

- **SPEC.md** — Полное техническое задание (архитектура, DDL, API, acceptance criteria)
- **README.md** — Quick start guide
- **docs/** — Дополнительная документация (zotero-setup.md, mcp-setup.md, api-reference.md)
- **Alembic migrations** — `backend/alembic/versions/` для истории схемы БД

---

## 💡 Советы для AI-Агентов

1. **Всегда проверяй SPEC.md** перед изменением архитектуры или модели данных
2. **Используй существующие patterns** — не изобретай велосипеды
3. **Пиши тесты** — особенно integration тесты для новых фич
4. **Следи за типами** — mypy strict mode должен проходить
5. **Логируй через structlog** — не используй `print`
6. **Проверяй migration** — любое изменение модели → новая миграция
7. **MCP audit** — все MCP tool calls логируются в `mcp_audit_log`

---

## 🔗 Контакты и Поддержка

- GitHub Issues: [repository]/issues
- Документация: `/docs` директория
- MCP Setup Guide: `docs/mcp-setup.md`
- Zotero Integration: `docs/zotero-setup.md`
