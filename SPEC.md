# ТЕХНИЧЕСКОЕ ЗАДАНИЕ

## Система «Scientific Library»

## 1. Архитектурный обзор

### 1.1. Назначение
Приватное мульти-пользовательское хранилище научных PDF с автоматическим извлечением метаданных, гибридным (FTS + векторным) поиском, групповыми коллекциями и доступом ИИ-агентов через MCP.

### 1.2. Компоненты системы

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Docker Compose                              │
│                                                                     │
│   ┌──────────────┐    ┌─────────────────────────────┐               │
│   │   Caddy      │    │   PostgreSQL 16 + pgvector  │               │
│   │  (TLS, rev   │    └─────────────────────────────┘               │
│   │   proxy)     │    ┌─────────────────────────────┐               │
│   └──────┬───────┘    │           Redis             │               │
│          │            │  (queue, locks, rate-limit) │               │
│   ┌──────┴───────┐    └─────────────────────────────┘               │
│   │   Frontend   │    ┌─────────────────────────────┐               │
│   │ (React SPA)  │    │      GROBID (TEI/XML)       │               │
│   └──────┬───────┘    └─────────────────────────────┘               │
│          │            ┌─────────────────────────────┐               │
│   ┌──────┴───────┐    │   Ollama / SentenceTrans.   │               │
│   │   Backend    │◄──►│        (embeddings)         │               │
│   │  (FastAPI)   │    └─────────────────────────────┘               │
│   │  - REST API  │    ┌─────────────────────────────┐               │
│   │  - WebDAV    │    │       Arq Worker            │               │
│   │  - MCP HTTP  │◄──►│  (PDF → GROBID → embed)     │               │
│   └──────────────┘    └─────────────────────────────┘               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
         ▲                                              ▲
         │ HTTPS                                        │ HTTPS + Basic
         │                                              │
   ┌─────┴──────┐                                ┌──────┴──────┐
   │ Browser    │                                │ Zotero Desktop│
   │ (SPA / MCP │                                │  (WebDAV only)│
   │ remote)    │                                └───────────────┘
   └────────────┘
```

### 1.3. Потоки данных

**Поток 1: Импорт PDF через Zotero.**
```
Zotero Desktop ─[PUT <KEY>.zip via WebDAV]──► Backend (Caddy → FastAPI)
   └─► сохранение raw ZIP (для GET обратно)
   └─► enqueue Arq job: process_attachment(zip_path, user_id, zotero_key)
       └─► распаковка → SHA-256 → дедупликация в `attachments`
       └─► GROBID → TEI/XML → метаданные (title, DOI, authors, abstract, sections)
       └─► Crossref by DOI → обогащение (journal, year, references)
       └─► upsert в `items` (по DOI или fingerprint)
       └─► создание `library_items` (link пользователь→item)
       └─► chunking по секциям → embeddings → `document_embeddings`
       └─► extract references → enqueue: resolve_citations(item_id)
```

**Поток 2: Импорт PDF через веб-UI.**
```
SPA ─[POST /api/v1/items/upload]──► Backend
   └─► тот же pipeline, начиная с SHA-256
```

**Поток 3: Импорт по DOI.**
```
SPA ─[POST /api/v1/items/import-by-doi]──► Backend
   └─► Crossref metadata → items upsert
   └─► Unpaywall lookup → если есть open PDF → fetch → pipeline
```

**Поток 4: Поиск.**
```
SPA / MCP-agent ─[query]──► Backend
   └─► embed(query) + tokenize
   └─► параллельно: HNSW vector search + GIN FTS search
   └─► RRF merge → фильтр по user visibility → return
```

---

## 2. Модель данных (PostgreSQL 16 + pgvector)

### 2.1. Принципы
- **Глобальный каталог `items`** — дедуплицирован по DOI (или fingerprint при отсутствии DOI). Канонические метаданные.
- **Персональные `library_items`** — каждый пользователь/группа имеет свою «копию-ссылку» на item с возможностью override отдельных полей (`title_override`, `notes`, `tags`).
- **Дедуплицированные `attachments`** — PDF хранится один раз по SHA-256, доступ через `library_items`.
- **Raw blobs `user_attachment_blobs`** — оригинальные Zotero ZIP'ы (нужны для отдачи обратно по `GET`, т.к. Zotero ожидает свой content-hash в `.prop`).

### 2.2. DDL

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TYPE user_role AS ENUM ('admin', 'user');
CREATE TYPE item_source AS ENUM ('webdav', 'upload', 'doi_import', 'crossref');
CREATE TYPE processing_status AS ENUM ('pending', 'processing', 'completed', 'failed');

-- ============================================================
-- USERS & AUTH
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified_at TIMESTAMPTZ,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    role user_role NOT NULL DEFAULT 'user',
    is_blocked BOOLEAN NOT NULL DEFAULT FALSE,
    storage_quota_bytes BIGINT NOT NULL DEFAULT 10737418240, -- 10 GB
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- WebDAV sync key (Basic Auth password for Zotero)
CREATE TABLE user_sync_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_value VARCHAR(64) UNIQUE NOT NULL,
    label VARCHAR(100),
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_sync_keys_active ON user_sync_keys(key_value) WHERE revoked_at IS NULL;

-- MCP tokens (only bcrypt hash stored)
CREATE TABLE mcp_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    token_prefix VARCHAR(16) NOT NULL, -- "mcp_live_a8f9" for UI display
    label VARCHAR(100),
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mcp_tokens_lookup ON mcp_tokens(token_hash) WHERE revoked_at IS NULL;

-- JWT refresh tokens (rotation)
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL,
    revoked_at TIMESTAMPTZ,
    user_agent TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ============================================================
-- GROUPS
-- ============================================================

CREATE TABLE groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TYPE group_member_role AS ENUM ('owner', 'editor', 'reader');

CREATE TABLE group_members (
    group_id UUID NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role group_member_role NOT NULL DEFAULT 'reader',
    added_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (group_id, user_id)
);

-- ============================================================
-- GLOBAL CATALOG (deduplicated)
-- ============================================================

CREATE TABLE items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    -- One of these is set, used for deduplication:
    doi VARCHAR(255) UNIQUE,
    fingerprint VARCHAR(64) UNIQUE, -- SHA256(normalize(title)+first_author+year) when DOI absent

    title TEXT NOT NULL,
    authors JSONB NOT NULL DEFAULT '[]'::jsonb, -- [{"given": "John", "family": "Doe", "orcid": null}]
    abstract TEXT,
    publication_type VARCHAR(50) NOT NULL DEFAULT 'journalArticle',
    journal_title TEXT,
    publisher VARCHAR(255),
    publication_year INT,
    volume VARCHAR(50),
    issue VARCHAR(50),
    pages VARCHAR(50),
    url TEXT,

    crossref_data JSONB, -- raw Crossref response for traceability
    metadata_source VARCHAR(50), -- 'grobid', 'crossref', 'manual', 'doi_import'
    metadata_quality SMALLINT DEFAULT 0, -- 0=raw GROBID, 50=crossref verified, 100=manual edit

    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CHECK (doi IS NOT NULL OR fingerprint IS NOT NULL)
);

CREATE INDEX idx_items_year ON items(publication_year);
CREATE INDEX idx_items_authors_gin ON items USING gin(authors);
CREATE INDEX idx_items_title_trgm ON items USING gin(title gin_trgm_ops);

-- ============================================================
-- ATTACHMENTS (deduplicated by SHA-256)
-- ============================================================

CREATE TABLE attachments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sha256 CHAR(64) UNIQUE NOT NULL,
    item_id UUID REFERENCES items(id) ON DELETE SET NULL, -- nullable: orphan PDF allowed temporarily
    file_path TEXT NOT NULL, -- relative path in storage backend
    file_size BIGINT NOT NULL,
    page_count INT,
    mime_type VARCHAR(100) NOT NULL DEFAULT 'application/pdf',

    extracted_text TEXT, -- full plain text (for FTS)
    extracted_text_tsv tsvector GENERATED ALWAYS AS (to_tsvector('english', coalesce(extracted_text, ''))) STORED,
    grobid_tei XML, -- structured GROBID output
    processing_status processing_status NOT NULL DEFAULT 'pending',
    processing_error TEXT,
    processed_at TIMESTAMPTZ,

    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_attachments_item ON attachments(item_id);
CREATE INDEX idx_attachments_fts ON attachments USING gin(extracted_text_tsv);
CREATE INDEX idx_attachments_status ON attachments(processing_status) WHERE processing_status != 'completed';

-- Raw Zotero ZIP blobs (for serving GET <KEY>.zip back to Zotero)
CREATE TABLE user_attachment_blobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    zotero_key VARCHAR(50) NOT NULL,
    blob_path TEXT NOT NULL, -- raw .zip path
    blob_size BIGINT NOT NULL,
    prop_content TEXT, -- raw .prop file content (mtime + hash)
    attachment_id UUID REFERENCES attachments(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id, zotero_key)
);

-- ============================================================
-- LIBRARY ITEMS (user/group ownership + overrides)
-- ============================================================

CREATE TABLE library_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,

    -- Exactly one of these is set:
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,

    -- Optional per-user overrides (NULL = inherit from items)
    title_override TEXT,
    notes TEXT,

    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    added_by item_source NOT NULL DEFAULT 'upload',
    added_by_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),

    CHECK ((user_id IS NOT NULL)::int + (group_id IS NOT NULL)::int = 1),
    UNIQUE(user_id, item_id),
    UNIQUE(group_id, item_id)
);

CREATE INDEX idx_library_user_active ON library_items(user_id) WHERE is_deleted = FALSE AND user_id IS NOT NULL;
CREATE INDEX idx_library_group_active ON library_items(group_id) WHERE is_deleted = FALSE AND group_id IS NOT NULL;
CREATE INDEX idx_library_item ON library_items(item_id);

-- ============================================================
-- COLLECTIONS (tree, per-user or per-group)
-- ============================================================

CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    parent_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    position INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK ((user_id IS NOT NULL)::int + (group_id IS NOT NULL)::int = 1)
);

CREATE INDEX idx_collections_parent ON collections(parent_id);
CREATE INDEX idx_collections_user ON collections(user_id);
CREATE INDEX idx_collections_group ON collections(group_id);

CREATE TABLE library_item_collections (
    library_item_id UUID NOT NULL REFERENCES library_items(id) ON DELETE CASCADE,
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    PRIMARY KEY (library_item_id, collection_id)
);

-- ============================================================
-- TAGS (per library item)
-- ============================================================

CREATE TABLE tags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    group_id UUID REFERENCES groups(id) ON DELETE CASCADE,
    CHECK ((user_id IS NOT NULL)::int + (group_id IS NOT NULL)::int = 1),
    UNIQUE(name, user_id),
    UNIQUE(name, group_id)
);

CREATE TABLE library_item_tags (
    library_item_id UUID NOT NULL REFERENCES library_items(id) ON DELETE CASCADE,
    tag_id UUID NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (library_item_id, tag_id)
);

-- ============================================================
-- EMBEDDINGS (fixed model at deploy time)
-- ============================================================
-- Dimension MUST match the deployed model. Default: 768 for specter2.
-- Changing model requires DB migration + full reindex.

CREATE TABLE document_embeddings (
    id BIGSERIAL PRIMARY KEY,
    attachment_id UUID NOT NULL REFERENCES attachments(id) ON DELETE CASCADE,
    item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE, -- denormalized for fast filter
    chunk_index INT NOT NULL,
    section_name VARCHAR(100), -- e.g. "Abstract", "Methods", from GROBID
    chunk_text TEXT NOT NULL,
    embedding vector(768) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(attachment_id, chunk_index)
);

CREATE INDEX idx_embeddings_hnsw ON document_embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);
CREATE INDEX idx_embeddings_item ON document_embeddings(item_id);

-- ============================================================
-- CITATIONS
-- ============================================================

CREATE TABLE citations (
    citing_item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    cited_item_id UUID NOT NULL REFERENCES items(id) ON DELETE CASCADE,
    source VARCHAR(50) NOT NULL DEFAULT 'crossref',
    raw_reference TEXT, -- when target DOI unknown, store raw text
    PRIMARY KEY (citing_item_id, cited_item_id)
);

CREATE INDEX idx_citations_cited ON citations(cited_item_id);

-- ============================================================
-- EXTERNAL API CACHE & SYSTEM
-- ============================================================

CREATE TABLE external_api_cache (
    query_hash CHAR(64) PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    response_payload JSONB NOT NULL,
    expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_cache_expiry ON external_api_cache(expires_at);

CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- Seeded: {'embedding_model': 'allenai/specter2_base', 'embedding_dim': 768, 'schema_version': '2.0'}

-- ============================================================
-- AUDIT LOGS
-- ============================================================

CREATE TABLE mcp_audit_log (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    mcp_token_id UUID REFERENCES mcp_tokens(id) ON DELETE SET NULL,
    tool_name VARCHAR(100) NOT NULL,
    tool_arguments JSONB,
    result_summary JSONB, -- {"items_returned": 5, "took_ms": 230}
    success BOOLEAN NOT NULL,
    error_message TEXT,
    ip_address INET,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_mcp_audit_user_time ON mcp_audit_log(user_id, created_at DESC);

CREATE TABLE processing_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(50) NOT NULL, -- 'pdf_process', 'crossref_lookup', 'citation_resolve'
    status processing_status NOT NULL DEFAULT 'pending',
    payload JSONB NOT NULL,
    error TEXT,
    attempts INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_jobs_status ON processing_jobs(status, created_at);
```

---

## 3. WebDAV Server

### 3.1. Конфигурация
- Используется `wsgidav` ≥ 4.3, обёрнутый в FastAPI через ASGI mount: `app.mount("/dav", WsgiToAsgi(wsgidav_app))`.
- Корневой URL: `https://<domain>/dav/zotero/`
- LOCK storage: Redis (custom `LockManager`), TTL = 10 минут.
- PROPFIND/PUT/GET/DELETE/MKCOL/LOCK/UNLOCK — все обязательны.

### 3.2. Аутентификация
- HTTP Basic Auth.
- Username = `users.email`, Password = валидный `user_sync_keys.key_value` (не пароль аккаунта!).
- Проверка через custom `DomainController` для `wsgidav`.
- При успехе `last_used_at` обновляется (async, без блокировки).

### 3.3. Virtual File System
Каждый пользователь видит изолированный namespace:
```
/dav/zotero/
  ├── <ITEM_KEY>.zip       ← read/write через user_attachment_blobs
  ├── <ITEM_KEY>.prop      ← read/write
  └── lastsync             ← Zotero touch file
```

Реализуется через custom `DAVProvider`, который маппит виртуальные пути на записи `user_attachment_blobs(user_id, zotero_key)`.

### 3.4. Обработка `PUT <KEY>.zip`
```python
async def on_put_zip(user_id: UUID, zotero_key: str, body: bytes):
    # 1. Quota check
    if not await check_quota(user_id, len(body)):
        raise HTTPException(507, "Insufficient Storage")

    # 2. Save raw blob
    blob_path = f"blobs/{user_id}/{zotero_key}.zip"
    await storage.write(blob_path, body)
    await db.upsert_blob(user_id, zotero_key, blob_path, len(body))

    # 3. Enqueue processing
    await arq.enqueue("process_zotero_upload",
                      user_id=user_id, zotero_key=zotero_key)
    return 201
```

### 3.5. Обработка `GET <KEY>.zip`
Возвращает байты из `user_attachment_blobs.blob_path`. Если blob отсутствует — `404`.

### 3.6. Обработка `.prop` файлов
Хранятся как text в `user_attachment_blobs.prop_content`. На `PUT` сохраняются, на `GET` отдаются. Zotero использует их для верификации hash/mtime пары к `.zip`.

### 3.7. Quota
- Default: 10 GB на пользователя.
- На `PUT` проверяется `SUM(blob_size) + SUM(attachments.file_size of user's items)`.
- При превышении: `507 Insufficient Storage`.

---

## 4. PDF Processing Pipeline

### 4.1. Этапы (Arq job `process_zotero_upload` или `process_uploaded_pdf`)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Unzip → extract PDF                                      │
│ 2. SHA-256 → check `attachments.sha256`                     │
│    ├─ exists → reuse, link library_item, DONE               │
│    └─ new → continue                                        │
│ 3. Store PDF → `storage/pdf/<sha[:2]>/<sha>.pdf`            │
│ 4. Create `attachments` row (status=processing)             │
│ 5. GROBID processFulltextDocument → TEI/XML                 │
│ 6. Parse TEI → extract: title, authors, abstract, DOI,      │
│    sections, references                                     │
│ 7. If DOI found → enqueue `crossref_enrich(doi)`            │
│ 8. Upsert `items` (by DOI or fingerprint)                   │
│ 9. Create `library_items(user_id, item_id)`                 │
│ 10. Add to user's "Inbox" collection                        │
│ 11. Chunk by sections → call embedding service              │
│ 12. INSERT into `document_embeddings`                       │
│ 13. Extract `extracted_text` → store on `attachments`       │
│ 14. status=completed, processed_at=now()                    │
│ 15. Enqueue `resolve_citations(item_id)`                    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2. Чанкинг
- Источник: GROBID-секции (`<head>` теги в TEI).
- Если секция длиннее 512 токенов — sliding window 512/64.
- Если короче 100 токенов — склеивается со следующей.
- К каждому чанку добавляется префикс:
  ```
  Document: {title}
  Section: {section_name}

  {chunk_text}
  ```

### 4.3. Crossref Enrichment
- Job `crossref_enrich(doi)`.
- GET `https://api.crossref.org/works/{doi}` с `mailto={CONTACT_EMAIL}` (Polite Pool).
- Rate limit: 50 req/s, контролируется через Redis token bucket.
- Кэш в `external_api_cache` на 30 дней.
- Обновляет `items` поля + повышает `metadata_quality` до 50.

### 4.4. Citation Resolution
- Job `resolve_citations(item_id)`.
- Из GROBID TEI извлекаются `<biblStruct>` references.
- Для каждой: если есть `<idno type="DOI">` → ищется в `items.doi`.
  - Найдено → INSERT в `citations(citing, cited)`.
  - Не найдено → INSERT в `citations` с `cited_item_id = NULL`-варианта нет (PK не позволит) → пишем в отдельную таблицу `unresolved_references` (добавить в DDL при кодинге).
- **MVP: без проактивного backfill.** Если позже эта статья появится в БД — отдельный job по запросу пользователя.

### 4.5. Retry & Failure
- Arq retries: 3 раза с exponential backoff (10s, 60s, 300s).
- После 3 fails: status='failed', сообщение в `processing_error`, видно админу.

---

## 5. Embeddings

### 5.1. Сервис
- Default: `allenai/specter2_base` (768d), via `sentence-transformers` с adapter `allenai/specter2` (proximity).
- Загружается **в Arq worker** (не в FastAPI) — экономит RAM на API процессах.
- Кэшируется на диск в `/app/models`.

### 5.2. Абстракция
```python
class EmbeddingProvider(Protocol):
    @property
    def dimension(self) -> int: ...
    async def embed_query(self, text: str) -> list[float]: ...
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
```

Реализации:
- `Specter2Provider` (default).
- `OllamaProvider` (для альтернативной деплой-конфигурации, dim передаётся в env).

### 5.3. Запрет на смену модели в runtime
При старте backend:
```python
settings_dim = db.get("embedding_dim")
configured_dim = provider.dimension
if settings_dim and settings_dim != configured_dim:
    sys.exit(f"FATAL: dim mismatch (db={settings_dim}, model={configured_dim}). "
             f"Run: python -m app.cli reindex --confirm")
```

CLI команда `reindex` создаёт новую таблицу `document_embeddings_v2`, перевекторизует, делает swap через ALTER TABLE RENAME.

---

## 6. Hybrid Search

### 6.1. Алгоритм
1. `query_vector = embed_query(q)` (768d).
2. **Vector search** (TopK=100):
   ```sql
   SELECT DISTINCT ON (item_id) item_id, chunk_index,
          1 - (embedding <=> $1) AS sim
   FROM document_embeddings
   WHERE item_id = ANY($visible_item_ids) -- prefilter
   ORDER BY item_id, embedding <=> $1
   LIMIT 100;
   ```
   `visible_item_ids` — set из CTE по `library_items` пользователя (≤ 50k записей — помещается в memory).
3. **FTS search** (TopK=100):
   ```sql
   SELECT a.item_id,
          ts_rank_cd(extracted_text_tsv, plainto_tsquery('english', $1)) AS rank
   FROM attachments a
   WHERE a.item_id = ANY($visible_item_ids)
     AND extracted_text_tsv @@ plainto_tsquery('english', $1)
   ORDER BY rank DESC LIMIT 100;
   ```
4. **RRF merge** (в Python, k=60):
   $$\text{score}(d) = \frac{1}{60 + \text{rank}_{vec}(d)} + \frac{1}{60 + \text{rank}_{fts}(d)}$$
5. Возврат TopN (default 20) с metadata.

### 6.2. Альтернатива при больших библиотеках
Если `visible_item_ids` > 10k — заменяем prefilter на post-filter (`WHERE item_id IN visible` после `LIMIT`). Это менее точно, но позволяет HNSW работать эффективно. Используется автоматически при превышении порога.

---

## 7. Аутентификация и авторизация

### 7.1. JWT
- Access token: 15 минут, в memory SPA, передаётся `Authorization: Bearer`.
- Refresh token: 30 дней, httpOnly+Secure cookie, ротация при каждом use.
- Алгоритм: HS256, секрет в env `JWT_SECRET`.

### 7.2. Эндпоинты auth
| Метод | Путь | Назначение |
|---|---|---|
| POST | `/api/v1/auth/login` | email+password → access+refresh |
| POST | `/api/v1/auth/refresh` | refresh → new access+refresh |
| POST | `/api/v1/auth/logout` | revoke refresh |
| GET | `/api/v1/auth/me` | current user info |

### 7.3. RBAC

| Действие | Условие |
|---|---|
| Чтение `library_item` user | `li.user_id == current_user.id AND NOT is_deleted` |
| Чтение `library_item` group | `EXISTS (group_members WHERE group_id=li.group_id AND user_id=current_user.id)` |
| Запись group library | `group_members.role IN ('owner', 'editor')` |
| Чтение admin | везде, включая `is_deleted=TRUE` |
| Управление пользователями | `current_user.role == 'admin'` |

Реализуется через FastAPI dependency `require_can_read_item(item_id)` и SQL фильтры в каждом query.

---

## 8. REST API (полный список)

### 8.1. Auth (см. §7.2)

### 8.2. Users (admin)
- `GET    /api/v1/admin/users` — список
- `POST   /api/v1/admin/users` — создать (email, password, role)
- `PATCH  /api/v1/admin/users/{id}` — изменить (block, role, quota)
- `DELETE /api/v1/admin/users/{id}` — деактивировать

### 8.3. Personal sync keys
- `GET    /api/v1/me/sync-keys` — список (без значения key_value)
- `POST   /api/v1/me/sync-keys` — создать (возвращает plain key ОДИН РАЗ)
- `DELETE /api/v1/me/sync-keys/{id}` — revoke

### 8.4. MCP tokens
- `GET    /api/v1/me/mcp-tokens`
- `POST   /api/v1/me/mcp-tokens` — возвращает `mcp_live_...` один раз
- `DELETE /api/v1/me/mcp-tokens/{id}` — revoke

### 8.5. Library items
- `GET    /api/v1/items` — список с фильтрами (`?collection=&tag=&group=&q=&sort=&page=`)
- `GET    /api/v1/items/{id}` — детали
- `POST   /api/v1/items/upload` — multipart PDF upload
- `POST   /api/v1/items/import-by-doi` — `{doi, collection_id?, group_id?}`
- `PATCH  /api/v1/items/{id}` — изменить overrides (`title_override`, `notes`)
- `DELETE /api/v1/items/{id}` — soft delete (is_deleted=true)
- `GET    /api/v1/items/{id}/pdf` — stream PDF (с проверкой visibility)
- `GET    /api/v1/items/{id}/citations` — list of cited & citing

### 8.6. Collections
- `GET    /api/v1/collections?scope=personal|group:{id}` — дерево
- `POST   /api/v1/collections` — `{name, parent_id?, group_id?}`
- `PATCH  /api/v1/collections/{id}` — rename / move
- `DELETE /api/v1/collections/{id}`
- `POST   /api/v1/collections/{id}/items` — `{library_item_ids: []}`
- `DELETE /api/v1/collections/{id}/items/{library_item_id}`

### 8.7. Tags
- `GET    /api/v1/tags?scope=personal|group:{id}`
- `POST   /api/v1/items/{id}/tags` — `{names: []}` (auto-create)
- `DELETE /api/v1/items/{id}/tags/{tag_id}`

### 8.8. Groups
- `GET    /api/v1/groups`
- `POST   /api/v1/groups` — `{name, description}`
- `GET    /api/v1/groups/{id}/members`
- `POST   /api/v1/groups/{id}/members` — `{user_email, role}` (owner only)
- `DELETE /api/v1/groups/{id}/members/{user_id}`
- `DELETE /api/v1/groups/{id}` — owner only

### 8.9. Search
- `GET    /api/v1/search?q=...&limit=20&type=hybrid|vector|fts&scope=personal|all`

### 8.10. External
- `GET    /api/v1/external/crossref?doi=...`
- `POST   /api/v1/external/citations/refresh/{item_id}` — манual re-resolve

### 8.11. Admin
- `GET    /api/v1/admin/jobs?status=failed`
- `POST   /api/v1/admin/jobs/{id}/retry`
- `GET    /api/v1/admin/stats` — counts, storage usage

---

## 9. MCP Server

### 9.1. Транспорт
- **Streamable HTTP** (актуальный MCP transport).
- Endpoint: `https://<domain>/mcp`.
- Реализация: библиотека `mcp` (официальный Python SDK) + FastAPI mount.

### 9.2. Аутентификация
- `Authorization: Bearer mcp_live_...` в каждом запросе.
- Middleware валидирует через `mcp_tokens.token_hash`, обновляет `last_used_at`, выставляет `request.state.user_id`.
- При невалидном токене — `401`.
- Rate limit: 60 req/min per token (Redis).

### 9.3. Tools

| Tool | Args | Returns |
|---|---|---|
| `search_papers` | `query: str, limit: int = 10, scope: "personal"\|"all" = "personal"` | список `{item_id, title, authors, year, doi, abstract, score}` |
| `get_paper_details` | `item_id: str` | full metadata + collections + tags + has_pdf flag |
| `read_paper_chunks` | `item_id: str, query: str, top_k: int = 3` | top relevant chunks `{section, text, score}` |
| `list_collections` | `scope?: str` | tree of collections |
| `list_items_in_collection` | `collection_id: str, limit: int = 50` | list of items |
| `get_citations` | `item_id: str, direction: "cited_by"\|"references"` | list of related items |

### 9.4. Audit
Каждый tool call → INSERT в `mcp_audit_log` с args, result summary, ms.

### 9.5. Тестирование с Opencode и Hermes
В документации проекта (`docs/mcp-setup.md`) — готовые JSON-сниппеты для обоих клиентов.

---

## 10. Frontend (React SPA)

### 10.1. Стек
- React 18 + TypeScript + Vite
- TanStack Query (data fetching)
- React Router 6
- Tailwind CSS + shadcn/ui
- Zustand (auth state)

### 10.2. Маршруты
- `/login`
- `/library` — основной вид (sidebar коллекций + список items)
- `/items/:id` — детальная карточка + PDF viewer (pdf.js)
- `/search?q=...` — результаты поиска
- `/groups` — управление группами
- `/groups/:id` — групповая библиотека
- `/settings/profile`
- `/settings/integrations` — sync keys, MCP tokens, инструкции Zotero
- `/admin/users` — admin only
- `/admin/jobs` — admin only

### 10.3. Ключевые UI-элементы
- **Карточка item**: title (с override-индикатором), authors, year, DOI link, abstract, status processing (badge), tags, collections.
- **Search bar**: универсальный, с тогглом «hybrid / vector / fts».
- **Upload zone**: drag-and-drop PDF, прогресс, статус извлечения метаданных.
- **Integrations page**: пошаговая инструкция настройки Zotero WebDAV с готовыми значениями.

---

## 11. Структура проекта

```
scientific-library/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
├── Caddyfile
├── LICENSE              # MIT
├── README.md
├── docs/
│   ├── architecture.md
│   ├── zotero-setup.md
│   ├── mcp-setup.md
│   └── api-reference.md
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── alembic/versions/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── models/         # SQLAlchemy
│   │   ├── schemas/        # Pydantic
│   │   ├── api/v1/         # FastAPI routers
│   │   │   ├── auth.py
│   │   │   ├── items.py
│   │   │   ├── collections.py
│   │   │   ├── groups.py
│   │   │   ├── search.py
│   │   │   ├── admin.py
│   │   │   └── ...
│   │   ├── webdav/
│   │   │   ├── provider.py
│   │   │   ├── auth.py
│   │   │   └── lock_redis.py
│   │   ├── mcp/
│   │   │   ├── server.py
│   │   │   ├── tools.py
│   │   │   └── auth.py
│   │   ├── services/
│   │   │   ├── embeddings/
│   │   │   ├── grobid.py
│   │   │   ├── crossref.py
│   │   │   ├── storage.py    # abstract + local + S3
│   │   │   ├── search.py
│   │   │   └── auth.py
│   │   ├── workers/
│   │   │   ├── settings.py   # Arq WorkerSettings
│   │   │   ├── pdf_pipeline.py
│   │   │   ├── crossref.py
│   │   │   └── citations.py
│   │   └── cli.py            # reindex, create-admin, etc.
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── e2e/
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   │   ├── main.tsx
│   │   ├── api/
│   │   ├── hooks/
│   │   ├── pages/
│   │   ├── components/
│   │   └── store/
│   └── tests/
└── .github/workflows/
    ├── ci.yml
    └── release.yml
```

---

## 12. Docker Compose

```yaml
services:
  caddy:
    image: caddy:2-alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
    depends_on: [backend, frontend]

  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
      - ./backups:/backups
    healthcheck:
      test: ["CMD", "pg_isready", "-U", "${POSTGRES_USER}"]
      interval: 10s

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data

  grobid:
    image: lfoppiano/grobid:0.8.1
    environment:
      JAVA_OPTS: "-Xmx4g"
    deploy:
      resources:
        limits:
          memory: 6G

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      REDIS_URL: redis://redis:6379/0
      GROBID_URL: http://grobid:8070
      JWT_SECRET: ${JWT_SECRET}
      STORAGE_BACKEND: local
      STORAGE_PATH: /app/storage
      EMBEDDING_MODEL: allenai/specter2_base
      EMBEDDING_DIM: 768
      CROSSREF_MAILTO: ${CROSSREF_MAILTO}
    volumes:
      - storage_data:/app/storage
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }

  worker:
    build: ./backend
    command: arq app.workers.settings.WorkerSettings
    environment: *backend-env  # same as backend
    volumes:
      - storage_data:/app/storage
      - model_cache:/app/models
    depends_on:
      db: { condition: service_healthy }
      redis: { condition: service_started }
      grobid: { condition: service_started }

  frontend:
    build: ./frontend
    environment:
      VITE_API_BASE: /api/v1

  backup:
    image: prodrigestivill/postgres-backup-local
    environment:
      POSTGRES_HOST: db
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      SCHEDULE: "0 3 * * *"
      BACKUP_KEEP_DAYS: 14
      BACKUP_KEEP_WEEKS: 4
    volumes:
      - ./backups:/backups
    depends_on: [db]

volumes:
  pg_data:
  redis_data:
  storage_data:
  model_cache:
  caddy_data:
```

`Caddyfile`:
```
{$DOMAIN} {
    handle /api/* {
        reverse_proxy backend:8000
    }
    handle /dav/* {
        reverse_proxy backend:8000
    }
    handle /mcp* {
        reverse_proxy backend:8000
    }
    handle {
        reverse_proxy frontend:80
    }
}
```

---

## 13. Тестирование

### 13.1. Unit
- `services/embeddings`: размерность, форма выхода.
- `services/search`: RRF корректность (assert порядок при mock рангах).
- `services/auth`: hash/verify токенов.
- `webdav/provider`: маппинг путей.

### 13.2. Integration (testcontainers)
- Postgres+Redis+GROBID в test session.
- Full pipeline: upload PDF → assert `items`, `attachments`, `document_embeddings` строки.
- WebDAV PUT через `requests` с Basic Auth → assert blob создан + job в очереди.
- Search returns expected ranking on known corpus.

### 13.3. E2E (Playwright)
- Login → upload PDF → wait for processing → search → open item → see PDF.
- Admin creates user → user logs in → generates sync key.
- Group: owner adds member → member sees group library.

### 13.4. MCP test
- Mock MCP client (Python SDK) с тестовым токеном → вызов `search_papers` → assert audit log entry.

---

## 14. CI/CD

`.github/workflows/ci.yml`:
1. `lint`: ruff, mypy, eslint, prettier.
2. `test-backend`: pytest с testcontainers (Postgres, Redis, GROBID image pulled).
3. `test-frontend`: vitest.
4. `build`: docker build обоих образов.
5. `e2e`: docker compose up → playwright run → down.

`release.yml` (по тегу `v*`):
- Build & push to GHCR.
- Generate release notes from conventional commits.

---

## 15. MVP Acceptance Checklist

### Развёртывание
- [ ] `docker compose up -d` поднимает всё за < 3 минут (после pull образов).
- [ ] Caddy выдаёт TLS-сертификат через Let's Encrypt при наличии `DOMAIN` env.
- [ ] Alembic миграции применяются автоматически при старте backend.
- [ ] CLI `python -m app.cli create-admin` создаёт первого админа.

### Auth
- [ ] Админ через `/admin/users` создаёт пользователя.
- [ ] Пользователь логинится email+password, получает JWT.
- [ ] Refresh token ротируется, отозванный не работает.

### WebDAV
- [ ] Пользователь генерирует `sync_key` в `/settings/integrations`.
- [ ] Zotero verify server успешно проходит на `https://<domain>/dav/zotero/`.
- [ ] PUT `.zip` сохраняет blob, не превышает quota.
- [ ] GET `.zip` возвращает тот же blob.
- [ ] LOCK/UNLOCK работают через Redis.

### PDF Pipeline
- [ ] PDF с DOI: метаданные извлекаются из GROBID, обогащаются Crossref, `metadata_quality=50`.
- [ ] Дедупликация: повторный upload того же PDF не создаёт новых `attachments`.
- [ ] Дедупликация по DOI: два пользователя загрузили одну статью → одна запись в `items`, две в `library_items`.
- [ ] Извлечённый text доступен для FTS.
- [ ] Эмбеддинги созданы для всех чанков.
- [ ] Failed jobs видны админу с error message.

### Search
- [ ] FTS-only поиск находит точное совпадение слова.
- [ ] Vector-only поиск находит семантически близкое.
- [ ] Hybrid через RRF возвращает релевантный результат при mixed query.
- [ ] Не показываются items других пользователей (RBAC).
- [ ] Показываются items групп, в которых пользователь состоит.

### Groups
- [ ] Owner создаёт группу, добавляет members с разными ролями.
- [ ] Editor может добавлять items в групповую библиотеку.
- [ ] Reader — только чтение.
- [ ] Удаление группы каскадно удаляет library_items группы.

### MCP
- [ ] Пользователь генерирует `mcp_live_...` токен, показывается ОДИН раз.
- [ ] Opencode и Hermes подключаются к `https://<domain>/mcp` с этим токеном.
- [ ] Все 6 tools работают и возвращают корректные данные.
- [ ] Audit log пишется на каждый вызов.
- [ ] Rate limit срабатывает на 61-м запросе в минуту.

### Citations
- [ ] Для статьи с references из Crossref создаются записи в `citations` для тех cited, чьи DOI есть в БД.
- [ ] `GET /items/{id}/citations` возвращает оба направления.

### Backup
- [ ] Cron-контейнер делает `pg_dump` в `./backups` ежедневно.

### Performance (на dataset 1000 PDF)
- [ ] Hybrid search возвращает результат < 500 ms (p95).
- [ ] Upload + processing одной PDF (10 MB, 20 pages) < 60 s.
- [ ] HNSW индекс собирается за разумное время (< 5 мин на 1000 items × ~50 chunks).

---

## 16. Roadmap

### MVP (этот документ)
Всё выше.

### Phase 2 (после MVP)
- Email сервис + публичная регистрация + verification.
- Annotations / highlights (отдельная таблица).
- Citation backfill (job, который при появлении нового item в БД проходит по `unresolved_references` и линкует).
- S3 backend для storage.
- Export BibTeX/RIS.
- WebDAV → обратная синхронизация: если пользователь правит item в SPA, генерируется новый ZIP и обновляется `user_attachment_blobs`, Zotero на следующем sync скачает его.

### Phase 3
- Cross-encoder reranker (опциональный).
- Мультиязычность.
- Browser extension / Tauri для tight Zotero integration.
- OCR для сканов.
- ML рекомендации «похожие статьи».
