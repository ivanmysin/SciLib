"""Arq Worker Configuration."""

from typing import Any, Dict, List


def get_worker_functions() -> List[str]:
    """Get list of worker function paths.
    
    Returns functions lazily to avoid import errors at module load time.
    """
    return [
        "app.services.embeddings.generate_embedding",
        "app.services.grobid.process_pdf",
        "app.services.crossref.fetch_metadata",
    ]


def get_cron_jobs() -> List[Dict[str, Any]]:
    """Get list of cron jobs.
    
    Returns cron jobs lazily to avoid import errors at module load time.
    """
    # Import arq.cron inside the function to avoid eager import at module load time
    from arq import cron
    return [
        cron("app.services.citations.resolve_references", minute=0),
    ]


class WorkerSettings:
    """Arq worker settings."""

    redis_settings = {
        "host": "redis",
        "port": 6379,
        "db": 0,
    }

    # Use property to lazy-load functions
    @property
    def functions(self) -> List[str]:
        return get_worker_functions()

    @property
    def cron_jobs(self) -> List[Dict[str, Any]]:
        # Lazy-load cron jobs to avoid import at class definition time
        return get_cron_jobs()

    on_startup = None
    on_shutdown = None
    handle_signals = True


settings = WorkerSettings()
