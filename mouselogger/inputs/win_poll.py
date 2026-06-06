"""Поллинговый источник ввода для Windows.

Каждые ``poll_interval`` секунд считывает позицию курсора и физическое
состояние кнопок через ``GetAsyncKeyState`` (а не ``GetKeyState``, который без
насоса сообщений не обновляется). Фиксирует движение и нажатия/отпускания
левой, правой и средней кнопок. Прокрутку колеса поллингом не получить —
для скролла используйте хук-бэкенд (:mod:`mouselogger.inputs.win_hook`).
"""

from __future__ import annotations

from ctypes import Structure, byref, c_long, c_ushort, windll
from time import sleep, time

from ..event import Action, Event
from .base import InputSource, OnEvent, ShouldStop

# виртуальные коды кнопок -> (событие нажатия, событие отпускания)
_BUTTONS = {
    0x01: (Action.LEFT_DOWN, Action.LEFT_UP),
    0x02: (Action.RIGHT_DOWN, Action.RIGHT_UP),
    0x04: (Action.MIDDLE_DOWN, Action.MIDDLE_UP),
}

# старший бит результата GetAsyncKeyState установлен, пока кнопка зажата
_KEY_PRESSED = 0x8000


class POINT(Structure):
    # знаковые LONG: на мультимониторе координаты бывают отрицательными
    _fields_ = [("x", c_long), ("y", c_long)]


def _now_ms() -> int:
    return int(time() * 1000)


class PollingMouseSource(InputSource):
    """Опрашивает мышь с фиксированной частотой."""

    def __init__(self, poll_interval: float) -> None:
        self._poll_interval = poll_interval

    def run(self, on_event: OnEvent, should_stop: ShouldStop) -> None:
        user32 = windll.user32
        user32.GetAsyncKeyState.restype = c_ushort

        point = POINT()
        is_down = dict.fromkeys(_BUTTONS, False)

        while not should_stop():
            timestamp = _now_ms()
            user32.GetCursorPos(byref(point))
            x, y = point.x, point.y

            on_event(Event(Action.MOVE, x, y, timestamp))

            for vk, (down_action, up_action) in _BUTTONS.items():
                pressed = bool(user32.GetAsyncKeyState(vk) & _KEY_PRESSED)
                if pressed and not is_down[vk]:
                    is_down[vk] = True
                    on_event(Event(down_action, x, y, timestamp))
                elif not pressed and is_down[vk]:
                    is_down[vk] = False
                    on_event(Event(up_action, x, y, timestamp))

            sleep(self._poll_interval)
