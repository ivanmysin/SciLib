.PHONY: up down restart logs migrate smoke-test test lint format clean

# Docker Compose commands
up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart

logs:
	docker compose logs -f

# Database migrations
migrate:
	docker compose run --rm backend alembic upgrade head

migrate-create:
	docker compose run --rm backend alembic revision --autogenerate -m "$(MESSAGE)"

# Testing
test:
	docker compose run --rm backend pytest

test-unit:
	docker compose run --rm backend pytest tests/unit

test-integration:
	docker compose run --rm backend pytest tests/integration

test-e2e:
	docker compose run --rm frontend npm run test:e2e

# Smoke tests
smoke-test:
	@echo "Running smoke tests..."
	@echo "1. Checking infrastructure services..."
	@docker compose ps db redis grobid | grep -q "running" || (echo "❌ Infrastructure services not running" && exit 1)
	@echo "✅ Infrastructure services OK"
	
	@echo "2. Checking backend (via Caddy HTTPS)..."
	@curl -skf https://localhost/docs > /dev/null || (echo "❌ Backend not responding" && exit 1)
	@echo "✅ Backend OK"
	
	@echo "3. Checking frontend (via Caddy HTTPS)..."
	@curl -skf https://localhost/ > /dev/null || (echo "❌ Frontend not responding" && exit 1)
	@echo "✅ Frontend OK"
	
	@echo "4. Checking API health (via Caddy HTTPS)..."
	@curl -skf https://localhost/api/v1/admin/status > /dev/null || (echo "❌ Health endpoint not responding" && exit 1)
	@echo "✅ Health endpoint OK"
	
	@echo "5. Checking worker..."
	@docker compose ps worker | grep -q "running" || (echo "❌ Worker not running" && exit 1)
	@echo "✅ Worker OK"
	
	@echo ""
	@echo "🎉 All smoke tests passed!"

# Linting and formatting
lint:
	docker compose run --rm backend poetry run ruff check .
	docker compose run --rm backend poetry run mypy .

format:
	docker compose run --rm backend poetry run ruff format .

# Clean up
clean:
	docker compose down -v
	docker system prune -f

# Development helpers
shell:
	docker compose run --rm backend bash

db-shell:
	docker compose exec db psql -U postgres -d scientific_library

redis-cli:
	docker compose exec redis redis-cli

# Backup
backup:
	docker compose run --rm backup pg_dump -U postgres scientific_library > backups/latest.sql

# Help
help:
	@echo "Available targets:"
	@echo "  up            - Start all services"
	@echo "  down          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  logs          - Show logs"
	@echo "  migrate       - Run database migrations"
	@echo "  migrate-create - Create new migration (use MESSAGE=your_message)"
	@echo "  test          - Run all tests"
	@echo "  smoke-test    - Run smoke tests"
	@echo "  lint          - Run linters"
	@echo "  format        - Format code"
	@echo "  clean         - Remove all containers and volumes"
	@echo "  shell         - Open shell in backend container"
	@echo "  db-shell      - Open psql shell"
	@echo "  redis-cli     - Open redis CLI"
