"""Сборка компонентов и запуск сессии сбора данных.

Связывает конфигурацию, источник ввода, recorder и приёмник, обеспечивает
корректную остановку по сигналу (Ctrl+C / SIGTERM) и гарантированный сброс
буферов при выходе.
"""

from __future__ import annotations

import signal
import threading
from time import time

from . import __version__, sysinfo
from .config import Config
from .inputs import DEFAULT_BACKEND, create_input_source
from .recorder import Recorder
from .session import SessionMeta
from .storage import JsonlSink


def build_session_meta(config: Config) -> SessionMeta:
    """Собрать метаданные сессии из конфигурации и сведений о системе."""
    sysinfo.make_dpi_aware()
    return SessionMeta.create(
        participant_id=config.participant_id,
        started_ms=int(time() * 1000),
        os_name=sysinfo.os_name(),
        screen=sysinfo.screen_size(),
        dpi=sysinfo.dpi(),
        sample_hz=config.sample_hz,
        consent=config.consent,
        app_version=__version__,
    )


def _install_stop_handlers(stop: threading.Event) -> None:
    """Повесить обработчики сигналов завершения на флаг остановки."""
    def _handler(_signum, _frame):
        stop.set()

    for sig_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        sig = getattr(signal, sig_name, None)
        if sig is not None:
            try:
                signal.signal(sig, _handler)
            except (ValueError, OSError):
                # не главный поток или сигнал недоступен — пропускаем
                pass


def run_capture(config: Config, backend: str = DEFAULT_BACKEND) -> None:
    """Запустить сбор до получения сигнала остановки.

    Предполагается, что согласие уже проверено вызывающей стороной (CLI).
    """
    stop = threading.Event()
    _install_stop_handlers(stop)

    meta = build_session_meta(config)
    sink = JsonlSink(config.log_dir, config.participant_id)
    recorder = Recorder(sink)
    source = create_input_source(config, backend)

    recorder.open(meta)
    try:
        source.run(recorder.feed, stop.is_set)
    except KeyboardInterrupt:
        # подстраховка, если прерывание прилетело между проверками флага
        pass
    finally:
        recorder.close()


__all__ = ["build_session_meta", "run_capture"]
