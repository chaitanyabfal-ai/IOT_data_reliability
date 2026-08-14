import logging
import os
from pathlib import Path


APP_LOG_FILE = os.getenv("APP_LOG_FILE", "/home/bfa/iot_queuingfix.log")


def configure_logging(log_file: str | None = None) -> logging.Logger:
    target = Path(log_file or APP_LOG_FILE)
    target.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("iot_queuingfix")
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.FileHandler(target)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    logger.addHandler(file_handler)
    return logger


def _get_env(name: str, default: str | None = None, *, cast=str):
    value = os.getenv(name, default)
    if value is None:
        return default
    if cast is bool:
        return str(value).strip().lower() in {"1", "true", "yes", "on"}
    if cast is int:
        return int(value)
    return value


def _build_redis_url():
    redis_host = _get_env("REDIS_HOST", "redis")
    redis_port = _get_env("REDIS_PORT", "6379", cast=int)
    redis_db = _get_env("REDIS_DB", "0", cast=int)
    return os.getenv("REDIS_URL", f"redis://{redis_host}:{redis_port}/{redis_db}")


def _build_postgres_url():
    postgres_host = _get_env("POSTGRES_HOST", "postgres")
    postgres_port = _get_env("POSTGRES_PORT", "5432", cast=int)
    postgres_user = _get_env("POSTGRES_USER", "user")
    postgres_password = _get_env("POSTGRES_PASSWORD", "password")
    postgres_db = _get_env("POSTGRES_DB", "iot_db")
    return os.getenv(
        "POSTGRES_URL",
        f"postgresql://{postgres_user}:{postgres_password}@{postgres_host}:{postgres_port}/{postgres_db}",
    )


REDIS_URL = _build_redis_url()
POSTGRES_URL = _build_postgres_url()
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)
CELERY_TASK_SERIALIZER = os.getenv("CELERY_TASK_SERIALIZER", "json")
CELERY_RESULT_SERIALIZER = os.getenv("CELERY_RESULT_SERIALIZER", "json")
CELERY_TIMEZONE = os.getenv("CELERY_TIMEZONE", "UTC")
# Number of readings to group into a single Celery task when sending batches.
# Set via environment variable `BATCH_SIZE`. Defaults to 500.
BATCH_SIZE = _get_env("BATCH_SIZE", "500", cast=int)


def get_on_prem_server_url(
    server_ip: str | None = None,
    server_port: str | int | None = None,
    endpoint: str | None = None,
    protocol: str | None = None,
) -> str:
    base_ip = server_ip or _get_env("ON_PREM_SERVER_IP", "127.0.0.1")
    if base_ip.startswith("http://") or base_ip.startswith("https://"):
        base_url = base_ip.rstrip("/")
    else:
        if ":" in base_ip and not base_ip.startswith("["):
            host, port_hint = base_ip.rsplit(":", 1)
            if port_hint.isdigit():
                base_ip = host
                if server_port is None:
                    server_port = port_hint
        port = server_port if server_port is not None else _get_env("ON_PREM_SERVER_PORT", "8000", cast=int)
        scheme = protocol or _get_env("ON_PREM_PROTOCOL", "http")
        base_url = f"{scheme}://{base_ip}:{port}"

    relative_endpoint = endpoint if endpoint is not None else _get_env("ON_PREM_DATA_ENDPOINT")
    if relative_endpoint is None:
        return base_url
    if relative_endpoint.startswith("http://") or relative_endpoint.startswith("https://"):
        return relative_endpoint
    return f"{base_url.rstrip('/')}/{relative_endpoint.lstrip('/')}"