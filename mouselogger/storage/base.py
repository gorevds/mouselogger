"""Интерфейс приёмника событий.

Отделяет логику записи (формат, ротация, буферизация) от логики сбора, чтобы
формат хранения можно было менять независимо от источника ввода.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..event import Event
from ..session import SessionMeta


class Sink(ABC):
    """Куда recorder складывает события одной сессии."""

    @abstractmethod
    def open(self, meta: SessionMeta) -> None:
        """Начать сессию записи; ``meta`` описывает её для читателя лога."""

    @abstractmethod
    def write(self, event: Event) -> None:
        """Записать одно событие."""

    @abstractmethod
    def close(self) -> None:
        """Завершить сессию записи, сбросив буферы."""

    def __enter__(self) -> Sink:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()
