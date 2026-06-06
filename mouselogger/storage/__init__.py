"""Хранение собранных данных: интерфейс приёмника, JSONL-приёмник, архивация."""

from .archive import archive_logs
from .base import Sink
from .jsonl_sink import JsonlSink

__all__ = ["Sink", "JsonlSink", "archive_logs"]
