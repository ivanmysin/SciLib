# Scientific Library Platform

Modern, self-hosted scientific literature management platform with Zotero integration, MCP server support, and AI-powered search.

## 🚀 Features

- **Zotero Sync**: Bidirectional sync with Zotero libraries via WebDAV and API
- **MCP Server**: Model Context Protocol support for LLM integration
- **AI Search**: Semantic search using sentence-transformers (specter2) with pgvector
- **PDF Pipeline**: Automatic PDF parsing, metadata extraction via GROBID
- **Citation Resolution**: Automatic citation matching via Crossref
- **WebDAV Storage**: Full WebDAV interface for file management
- **Modern UI**: React 18 + TypeScript + Tailwind + shadcn/ui
- **Production Ready**: Docker Compose, Caddy reverse proxy, backup system

## 📋 Prerequisites

- Docker 24+ and Docker Compose 2.20+
- Make (optional, but recommended)
- Git

## 🛠️ Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd scientific-library
```

### 2. Configure Environment

Copy the example environment file and adjust settings:

```bash
cp .env.example .env
```

Edit `.env` with your specific values:

```bash
# Required: Generate a secure secret key
SECRET_KEY=$(openssl rand -hex 32)

# Optional: Add your API keys for enhanced functionality
GROBID_URL=http://grobid:8070
CROSSREF_API_BASE=https://api.crossref.org
OPENAI_API_KEY=your-key-here  # For advanced embeddings
```

**Minimum required variables:**
- `SECRET_KEY` - For JWT signing (generate with `openssl rand -hex 32`)
- `POSTGRES_PASSWORD` - Database password
- `REDIS_PASSWORD` - Redis password (if enabled)

### 3. Start the Stack

#### Option A: Using Make (Recommended)

```bash
# Install all dependencies and start services
make up

# Or step by step:
make install      # Pull images, install frontend deps
make migrate      # Run database migrations
make up           # Start all services
```

#### Option B: Manual Docker Compose

```bash
# Pull all images
docker compose pull

# Start infrastructure services (DB, Redis, GROBID)
docker compose up -d db redis grobid

# Wait for services to be ready (30 seconds)
sleep 30

# Run database migrations
docker compose run --rm backend alembic upgrade head

# Start all services
docker compose up -d
```

### 4. Verify Installation

Run the smoke test suite:

```bash
make smoke-test
```

Or manually check:

```bash
# Check all containers are running
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check WebDAV endpoint
curl -u admin:admin http://localhost:8080/
```

### 5. Access the Application

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | (create account) |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/docs | - |
| WebDAV | http://localhost:8080 | admin/admin |
| PostgreSQL | localhost:5432 | postgres/postgres |
| Redis | localhost:6379 | - |

## 🔧 Development Setup

### Backend Development

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install poetry
poetry install

# Run with hot reload
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
poetry run pytest tests/unit
poetry run pytest tests/integration
```

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Run tests
npm run test
```

### Database Migrations

```bash
# Create new migration
docker compose run --rm backend alembic revision --autogenerate -m "Description"

# Apply migrations
docker compose run --rm backend alembic upgrade head

# Rollback one migration
docker compose run --rm backend alembic downgrade -1

# View migration history
docker compose run --rm backend alembic history
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test suites
make test-unit       # Unit tests
make test-integration # Integration tests (requires testcontainers)
make test-e2e        # E2E tests (requires Playwright)

# Run with coverage
make coverage
```

## 📦 Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Caddy     │────▶│   Backend    │────▶│ PostgreSQL  │
│ (Reverse    │     │   (FastAPI)  │     │  + pgvector │
│  Proxy)     │     │              │     │             │
└─────────────┘     └──────┬───────┘     └─────────────┘
         │                 │                      │
         │                 ▼                      │
         │         ┌──────────────┐               │
         │         │    Redis     │◀──────────────┘
         │         │  (Cache +    │
         │         │   Arq Queue) │
         │         └──────────────┘
         │                 │
         │                 ▼
         │         ┌──────────────┐
         │         │   Workers    │
         │         │   (Arq)      │
         └────────▶└──────────────┘
                  ┌──────────────┐
                  │   Frontend   │
                  │   (React)    │
                  └──────────────┘
```

### Components

- **Caddy**: Reverse proxy with automatic HTTPS
- **Backend**: FastAPI application with async SQLAlchemy
- **PostgreSQL**: Primary database with pgvector for embeddings
- **Redis**: Cache, session storage, and task queue
- **GROBID**: PDF parsing and metadata extraction
- **Workers**: Background task processing (Arq)
- **Frontend**: React SPA with TanStack Query

## 🔐 Security

### Default Credentials

**⚠️ Change these in production!**

- WebDAV: `admin` / `admin`
- PostgreSQL: `postgres` / `postgres`
- Redis: No password by default (set `REDIS_PASSWORD` in `.env`)

### Production Checklist

- [ ] Change all default passwords
- [ ] Set strong `SECRET_KEY` (32+ bytes)
- [ ] Enable HTTPS (Caddy auto-provisions Let's Encrypt)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper CORS origins
- [ ] Enable Redis authentication
- [ ] Set up regular backups (`make backup`)
- [ ] Review firewall rules
- [ ] Enable monitoring and logging

## 🔄 Backup & Restore

### Create Backup

```bash
make backup
# Creates backup in ./backups/YYYY-MM-DD_HH-MM-SS/
```

### Restore from Backup

```bash
make restore BACKUP_DIR=./backups/YYYY-MM-DD_HH-MM-SS
```

### Automated Backups

The backup service runs daily at 3 AM. Configure backup retention in `.env`:

```bash
BACKUP_RETENTION_DAYS=30
BACKUP_SCHEDULE=0 3 * * *
```

## 🤖 MCP Server Usage

The platform includes an MCP server for LLM integration:

```bash
# Test MCP endpoint
curl -X POST http://localhost:8000/mcp/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc": "2.0", "method": "initialize", "params": {...}}'
```

Available tools:
- `search_papers` - Semantic search across library
- `get_paper_details` - Retrieve paper metadata
- `find_citations` - Get citations for a paper
- `resolve_reference` - Resolve citation references
- `sync_zotero` - Trigger Zotero sync
- `get_library_stats` - Library statistics

See `docs/mcp-setup.md` for detailed configuration.

## 📚 Documentation

- [Architecture Overview](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Zotero Integration](docs/zotero-setup.md)
- [MCP Server Setup](docs/mcp-setup.md)
- [Deployment Guide](docs/deployment.md)

## 🛠️ Troubleshooting

### Common Issues

**Database connection errors:**
```bash
# Check if PostgreSQL is running
docker compose ps db

# View logs
docker compose logs db

# Restart database
docker compose restart db
```

**Migration failures:**
```bash
# Reset migrations (⚠️ deletes all data)
docker compose down -v
docker compose up -d db
sleep 10
docker compose run --rm backend alembic upgrade head
```

**Frontend build errors:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**GROBID not responding:**
```bash
# GROBID takes ~30s to start
docker compose logs grobid
docker compose restart grobid
```

### Getting Help

- Check logs: `docker compose logs -f [service]`
- Health checks: `curl http://localhost:8000/health`
- Database status: `docker compose exec db psql -U postgres -c "SELECT version();"`

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read our [Contributing Guide](CONTRIBUTING.md) for details.

---

Built with ❤️ using FastAPI, React, and modern open-source technologies.
