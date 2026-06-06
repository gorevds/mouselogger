"""Конфигурация MouseLogger: пути хранения, идентификатор участника и параметры сбора.

Источники значений (по убыванию приоритета):

1. Переменные окружения с префиксом ``MOUSELOGGER_``.
2. Сохранённый ранее идентификатор участника (файл в каталоге данных).
3. Встроенные значения по умолчанию, зависящие от ОС.

Модуль намеренно не тянет ``ctypes``/``winreg`` на этапе импорта, чтобы его
можно было импортировать и тестировать на любой платформе.
"""

from __future__ import annotations

import os
import sys
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

APP_NAME = "MouseLogger"
ENV_PREFIX = "MOUSELOGGER_"

DEFAULT_SAMPLE_HZ = 50
# разумные границы частоты опроса: ниже 1 Гц смысла нет, выше 1 кГц — это
# уже не поведенческие данные, а шум планировщика ОС
MIN_SAMPLE_HZ = 1
MAX_SAMPLE_HZ = 1000

PARTICIPANT_FILE_NAME = "participant_id.txt"
CONSENT_FILE_NAME = "consent.txt"

_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})


def _consent_file_exists(data_dir: Path) -> bool:
    return (data_dir / CONSENT_FILE_NAME).exists()


def record_consent(data_dir: Path) -> Path:
    """Зафиксировать факт согласия участника (файл-маркер с отметкой времени).

    Согласие, данное один раз, сохраняется, чтобы автозапуск в следующих
    сессиях видел его без повторного флага.
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    consent_file = data_dir / CONSENT_FILE_NAME
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    consent_file.write_text(f"consented_at={stamp}\n", encoding="utf-8")
    return consent_file


def _as_bool(value: str | None, default: bool = False) -> bool:
    """Привести строковое значение окружения к bool."""
    if value is None:
        return default
    return value.strip().lower() in _TRUE_VALUES


def _default_data_dir() -> Path:
    """Каталог данных по умолчанию для текущей ОС.

    Windows — ``%LOCALAPPDATA%\\MouseLogger`` (не требует прав на корень диска,
    в отличие от прежнего ``C:\\MouseLog``). На прочих ОС (разработка, тесты) —
    каталог в духе XDG.
    """
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
        return Path(base) / APP_NAME
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg) if xdg else Path(os.path.expanduser("~")) / ".local" / "share"
    return base / "mouselogger"


def _resolve_participant_id(data_dir: Path, env_value: str | None) -> str:
    """Определить псевдонимный идентификатор участника.

    Реальный логин (PII) не используется. Приоритет: явное значение из
    окружения → ранее сохранённый файл → новый сгенерированный идентификатор,
    который тут же сохраняется, чтобы оставаться стабильным между сессиями.
    """
    if env_value:
        return env_value.strip()

    participant_file = data_dir / PARTICIPANT_FILE_NAME
    if participant_file.exists():
        stored = participant_file.read_text(encoding="utf-8").strip()
        if stored:
            return stored

    participant_id = "P-" + uuid.uuid4().hex[:12]
    data_dir.mkdir(parents=True, exist_ok=True)
    participant_file.write_text(participant_id, encoding="utf-8")
    return participant_id


@dataclass(frozen=True)
class Config:
    """Неизменяемый снимок конфигурации сбора данных."""

    data_dir: Path
    participant_id: str
    sample_hz: int = DEFAULT_SAMPLE_HZ
    capture_scroll: bool = True
    consent: bool = False

    @property
    def log_dir(self) -> Path:
        """Каталог с текущими (незаархивированными) лог-файлами."""
        return self.data_dir / "logs"

    @property
    def archive_dir(self) -> Path:
        """Каталог с архивами логов."""
        return self.data_dir / "archive"

    @property
    def poll_interval(self) -> float:
        """Интервал опроса в секундах (для поллингового бэкенда ввода)."""
        return 1.0 / self.sample_hz

    @classmethod
    def load(cls, environ: Mapping[str, str] | None = None) -> Config:
        """Собрать конфигурацию из окружения и значений по умолчанию.

        :param environ: подменяемое отображение окружения (для тестов);
            по умолчанию используется ``os.environ``.
        """
        env = os.environ if environ is None else environ

        raw_dir = env.get(ENV_PREFIX + "DIR")
        data_dir = Path(raw_dir) if raw_dir else _default_data_dir()

        participant_id = _resolve_participant_id(
            data_dir, env.get(ENV_PREFIX + "PARTICIPANT")
        )

        sample_hz = _clamp_sample_hz(env.get(ENV_PREFIX + "SAMPLE_HZ"))
        capture_scroll = _as_bool(env.get(ENV_PREFIX + "SCROLL"), default=True)
        # согласие действует, если задано в окружении ИЛИ сохранён файл-маркер
        consent = _as_bool(env.get(ENV_PREFIX + "CONSENT"), default=False) or (
            _consent_file_exists(data_dir)
        )

        return cls(
            data_dir=data_dir,
            participant_id=participant_id,
            sample_hz=sample_hz,
            capture_scroll=capture_scroll,
            consent=consent,
        )


def _clamp_sample_hz(raw: str | None) -> int:
    """Разобрать и ограничить частоту опроса; некорректный ввод → значение по умолчанию."""
    if raw is None or raw.strip() == "":
        return DEFAULT_SAMPLE_HZ
    try:
        value = int(raw)
    except ValueError:
        return DEFAULT_SAMPLE_HZ
    return max(MIN_SAMPLE_HZ, min(MAX_SAMPLE_HZ, value))
