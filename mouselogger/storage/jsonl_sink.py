"""JSONL-приёмник: одна строка — одно событие, первая строка файла — метаданные.

Лог-файл назван ``<participant_id>-<YYYY-MM-DD>.jsonl``. Дата вычисляется из
времени каждого события в рантайме, поэтому при пересечении полуночи запись
автоматически переходит в файл следующего дня (старый баг с «замёрзшей» датой).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TextIO

from ..event import Event
from ..session import SessionMeta
from .base import Sink

# по умолчанию сбрасываем буфер на диск каждые N событий — компромисс между
# сохранностью данных при внезапном завершении и нагрузкой на диск
DEFAULT_FLUSH_EVERY = 25


def _date_str(timestamp_ms: int) -> str:
    """Локальная дата (YYYY-MM-DD) для Unix-времени в миллисекундах."""
    return datetime.fromtimestamp(timestamp_ms / 1000).strftime("%Y-%m-%d")


class JsonlSink(Sink):
    """Пишет события в посуточные JSONL-файлы с буферизацией и ротацией."""

    def __init__(
        self,
        log_dir: Path,
        participant_id: str,
        flush_every: int = DEFAULT_FLUSH_EVERY,
    ) -> None:
        self._log_dir = Path(log_dir)
        self._participant_id = participant_id
        self._flush_every = max(1, flush_every)
        self._meta_line: str | None = None
        self._file: TextIO | None = None
        self._current_date: str | None = None
        self._since_flush = 0

    def open(self, meta: SessionMeta) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._meta_line = json.dumps(meta.to_dict(), ensure_ascii=False)
        self._rotate_to(_date_str(meta.started_ms))

    def write(self, event: Event) -> None:
        if self._file is None:
            raise RuntimeError("JsonlSink.write() до open()")
        date = _date_str(event.t)
        if date != self._current_date:
            self._rotate_to(date)
        assert self._file is not None  # _rotate_to гарантирует открытый файл
        self._file.write(json.dumps(event.to_dict(), ensure_ascii=False))
        self._file.write("\n")
        self._since_flush += 1
        if self._since_flush >= self._flush_every:
            self._file.flush()
            self._since_flush = 0

    def close(self) -> None:
        if self._file is not None:
            self._file.flush()
            self._file.close()
            self._file = None
            self._current_date = None

    def _rotate_to(self, date: str) -> None:
        """Переключиться на файл указанной даты, дописав мета-строку, если файл новый."""
        if self._file is not None:
            self._file.flush()
            self._file.close()
        self._current_date = date
        path = self._log_dir / f"{self._participant_id}-{date}.jsonl"
        self._file = open(path, "a", encoding="utf-8")
        # мета-строку пишем только в начало нового файла, чтобы при дозаписи
        # (рестарт в тот же день) она не дублировалась
        if self._file.tell() == 0 and self._meta_line is not None:
            self._file.write(self._meta_line + "\n")
        self._since_flush = 0
