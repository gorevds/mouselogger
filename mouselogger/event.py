"""Модель одного события мыши и его сериализация.

Координаты хранятся «сырыми», в пикселях экрана. Нормализация в диапазон
``[0, 1]`` по разрешению экрана выполняется не здесь, а на этапе экспорта
признаков, чтобы исходный лог оставался без потерь информации.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping

# Версия схемы лога. Увеличивать при любом несовместимом изменении формата
# событий или метаданных сессии, чтобы старые логи можно было распознать.
SCHEMA_VERSION = 2


class Action(str, Enum):
    """Тип зафиксированного события.

    Наследование от ``str`` делает значения готовыми к JSON-сериализации
    (``Action.MOVE`` сериализуется как ``"M"``).
    """

    SESSION_START = "0"   # маркер начала сессии
    MOVE = "M"            # перемещение курсора
    LEFT_DOWN = "L_D"     # нажатие левой кнопки
    LEFT_UP = "L_U"       # отпускание левой кнопки
    RIGHT_DOWN = "R_D"    # нажатие правой кнопки
    RIGHT_UP = "R_U"      # отпускание правой кнопки
    MIDDLE_DOWN = "M_D"   # нажатие средней кнопки (колесо)
    MIDDLE_UP = "M_U"     # отпускание средней кнопки
    SCROLL = "S"          # прокрутка колеса (величина — в поле value)
    IDLE = "I"            # пауза/простой курсора (длительность в мс — в поле value)


@dataclass(frozen=True, slots=True)
class Event:
    """Неизменяемое событие мыши.

    :param action: тип события.
    :param x: X-координата курсора в пикселях (знаковая: на мультимониторе бывает < 0).
    :param y: Y-координата курсора в пикселях.
    :param t: Unix-время события в миллисекундах.
    :param value: доп. величина — дельта прокрутки (``SCROLL``) или
        длительность паузы в мс (``IDLE``); для остальных событий ``None``.
    """

    action: Action
    x: int
    y: int
    t: int
    value: int | None = None

    @property
    def position_key(self) -> tuple[Action, int, int]:
        """Ключ для дедупликации: тип события и позиция, без учёта времени."""
        return (self.action, self.x, self.y)

    def to_dict(self) -> dict[str, object]:
        """Компактное представление для JSONL-строки."""
        record: dict[str, object] = {
            "a": self.action.value,
            "x": self.x,
            "y": self.y,
            "t": self.t,
        }
        if self.value is not None:
            record["v"] = self.value
        return record

    @classmethod
    def from_dict(cls, record: Mapping[str, object]) -> "Event":
        """Восстановить событие из словаря, полученного из JSONL-строки."""
        value = record.get("v")
        return cls(
            action=Action(record["a"]),
            x=int(record["x"]),          # type: ignore[arg-type]
            y=int(record["y"]),          # type: ignore[arg-type]
            t=int(record["t"]),          # type: ignore[arg-type]
            value=None if value is None else int(value),  # type: ignore[arg-type]
        )
