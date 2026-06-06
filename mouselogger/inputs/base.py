"""Интерфейс источника ввода.

Источник захватывает активность мыши и для каждого события вызывает колбэк
``on_event``. Это отделяет способ захвата (поллинг или системный хук) от
логики записи: recorder одинаково работает с любым источником.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from ..event import Event

# колбэк, вызываемый на каждое событие
OnEvent = Callable[[Event], None]
# предикат остановки: пока возвращает False, захват продолжается
ShouldStop = Callable[[], bool]


class InputSource(ABC):
    """Источник событий мыши."""

    @abstractmethod
    def run(self, on_event: OnEvent, should_stop: ShouldStop) -> None:
        """Блокирующе захватывать ввод, вызывая ``on_event`` на каждое событие,
        пока ``should_stop()`` не вернёт ``True``."""
