"""Метаданные сессии сбора данных.

Пишутся первой строкой лог-файла и нужны ML-пайплайну, чтобы интерпретировать
события: нормировать координаты по разрешению экрана, знать частоту опроса,
платформу, версию схемы и факт согласия участника.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import Mapping

from .event import SCHEMA_VERSION

# дискриминатор первой строки лога; события такого ключа не имеют
META_TYPE = "meta"


@dataclass(frozen=True, slots=True)
class SessionMeta:
    """Неизменяемые метаданные одной сессии записи."""

    participant_id: str
    session_id: str
    started_ms: int
    os_name: str
    screen_width: int
    screen_height: int
    dpi: int
    sample_hz: int
    consent: bool
    app_version: str
    schema_version: int = SCHEMA_VERSION

    @classmethod
    def create(
        cls,
        *,
        participant_id: str,
        started_ms: int,
        os_name: str,
        screen: tuple[int, int],
        dpi: int,
        sample_hz: int,
        consent: bool,
        app_version: str,
    ) -> "SessionMeta":
        """Создать метаданные новой сессии со свежим ``session_id``."""
        width, height = screen
        return cls(
            participant_id=participant_id,
            session_id=uuid.uuid4().hex,
            started_ms=started_ms,
            os_name=os_name,
            screen_width=width,
            screen_height=height,
            dpi=dpi,
            sample_hz=sample_hz,
            consent=consent,
            app_version=app_version,
        )

    def to_dict(self) -> dict[str, object]:
        """Представление для первой (мета-)строки JSONL."""
        return {
            "type": META_TYPE,
            "schema": self.schema_version,
            "participant": self.participant_id,
            "session": self.session_id,
            "started_ms": self.started_ms,
            "os": self.os_name,
            "screen": [self.screen_width, self.screen_height],
            "dpi": self.dpi,
            "sample_hz": self.sample_hz,
            "consent": self.consent,
            "app_version": self.app_version,
        }

    @classmethod
    def from_dict(cls, record: Mapping[str, object]) -> "SessionMeta":
        """Восстановить метаданные из мета-строки JSONL."""
        screen = record["screen"]
        width, height = int(screen[0]), int(screen[1])  # type: ignore[index]
        return cls(
            participant_id=str(record["participant"]),
            session_id=str(record["session"]),
            started_ms=int(record["started_ms"]),        # type: ignore[arg-type]
            os_name=str(record["os"]),
            screen_width=width,
            screen_height=height,
            dpi=int(record["dpi"]),                       # type: ignore[arg-type]
            sample_hz=int(record["sample_hz"]),           # type: ignore[arg-type]
            consent=bool(record["consent"]),
            app_version=str(record["app_version"]),
            schema_version=int(record["schema"]),         # type: ignore[arg-type]
        )
