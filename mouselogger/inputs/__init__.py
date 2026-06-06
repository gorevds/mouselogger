"""Источники ввода и фабрика выбора бэкенда.

Windows-специфичные бэкенды импортируются лениво внутри фабрики, чтобы импорт
самого пакета (и его тестирование) был возможен на любой платформе.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .base import InputSource

if TYPE_CHECKING:
    from ..config import Config

# доступные бэкенды захвата
BACKENDS = ("hook", "poll")
DEFAULT_BACKEND = "hook"


def create_input_source(config: "Config", backend: str = DEFAULT_BACKEND) -> InputSource:
    """Создать источник ввода выбранного бэкенда.

    :param backend: ``"hook"`` — низкоуровневый системный хук (точнее, со
        скроллом) или ``"poll"`` — поллинг с фиксированной частотой.
    """
    if backend == "hook":
        from .win_hook import LowLevelMouseSource

        return LowLevelMouseSource(capture_scroll=config.capture_scroll)
    if backend == "poll":
        from .win_poll import PollingMouseSource

        return PollingMouseSource(poll_interval=config.poll_interval)
    raise ValueError(f"неизвестный бэкенд ввода: {backend!r} (допустимо: {BACKENDS})")


__all__ = ["InputSource", "create_input_source", "BACKENDS", "DEFAULT_BACKEND"]
