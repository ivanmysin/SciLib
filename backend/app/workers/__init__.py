"""Arq Worker Configuration."""

from arq import cron


class WorkerSettings:
    """Arq worker settings."""

    redis_settings = {
        "host": "redis",
        "port": 6379,
        "db": 0,
    }

    functions = [
        "app.services.embeddings.generate_embedding",
        "app.services.grobid.process_pdf",
        "app.services.crossref.fetch_metadata",
    ]

    cron_jobs = [
        cron("app.services.citations.resolve_references", minute=0),
    ]

    on_startup = None
    on_shutdown = None
    handle_signals = True


settings = WorkerSettings()
