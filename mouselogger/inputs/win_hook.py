"""Событийный источник ввода для Windows на основе низкоуровневого хука мыши.

``WH_MOUSE_LL`` через ``SetWindowsHookEx`` доставляет каждое событие мыши
по факту (без поллинга и джиттера), включая прокрутку колеса. Это
предпочтительный бэкенд для качественных биометрических данных.

Хук требует насоса сообщений на потоке, который его установил, поэтому
``run`` крутит лёгкий цикл ``PeekMessage`` до сигнала остановки.

Внимание: код Windows-специфичен и проверяется на Windows; на других ОС модуль
не импортируется (см. фабрику в :mod:`mouselogger.inputs`).
"""

from __future__ import annotations

import ctypes
from ctypes import POINTER, byref, c_int, c_ssize_t, cast, windll
from ctypes import wintypes
from time import sleep, time

from ..event import Action, Event
from .base import InputSource, OnEvent, ShouldStop

WH_MOUSE_LL = 14
HC_ACTION = 0
PM_REMOVE = 0x0001
WHEEL_DELTA = 120

# сообщения мыши -> событие (для колёсика value заполняется отдельно)
_MESSAGES = {
    0x0200: Action.MOVE,         # WM_MOUSEMOVE
    0x0201: Action.LEFT_DOWN,    # WM_LBUTTONDOWN
    0x0202: Action.LEFT_UP,      # WM_LBUTTONUP
    0x0204: Action.RIGHT_DOWN,   # WM_RBUTTONDOWN
    0x0205: Action.RIGHT_UP,     # WM_RBUTTONUP
    0x0207: Action.MIDDLE_DOWN,  # WM_MBUTTONDOWN
    0x0208: Action.MIDDLE_UP,    # WM_MBUTTONUP
}
WM_MOUSEWHEEL = 0x020A


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", POINTER(wintypes.ULONG)),
    ]


# LRESULT CALLBACK proc(int nCode, WPARAM wParam, LPARAM lParam); __stdcall
_HOOKPROC = ctypes.WINFUNCTYPE(c_ssize_t, c_int, wintypes.WPARAM, wintypes.LPARAM)


def _now_ms() -> int:
    return int(time() * 1000)


def _wheel_steps(mouse_data: int) -> int:
    """Знаковое число «щелчков» колеса из старшего слова mouseData."""
    raw = (mouse_data >> 16) & 0xFFFF
    delta = ctypes.c_short(raw).value
    return delta // WHEEL_DELTA


class LowLevelMouseSource(InputSource):
    """Захват мыши через низкоуровневый системный хук."""

    def __init__(self, capture_scroll: bool = True) -> None:
        self._capture_scroll = capture_scroll
        # ссылку на callback держим на экземпляре, иначе его соберёт GC -> падение
        self._proc = None

    def run(self, on_event: OnEvent, should_stop: ShouldStop) -> None:
        user32 = windll.user32
        kernel32 = windll.kernel32

        # хендлы — указатели; без явного restype ctypes вернёт c_int (32 бита)
        # и на 64-битной Windows значение усечётся
        kernel32.GetModuleHandleW.restype = wintypes.HMODULE
        kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        user32.SetWindowsHookExW.restype = wintypes.HHOOK
        user32.SetWindowsHookExW.argtypes = [
            c_int, _HOOKPROC, wintypes.HINSTANCE, wintypes.DWORD,
        ]
        user32.CallNextHookEx.restype = c_ssize_t
        user32.CallNextHookEx.argtypes = [
            wintypes.HHOOK, c_int, wintypes.WPARAM, wintypes.LPARAM,
        ]
        user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        def _callback(n_code, w_param, l_param):
            if n_code == HC_ACTION:
                self._dispatch(int(w_param), l_param, on_event)
            return user32.CallNextHookEx(None, n_code, w_param, l_param)

        self._proc = _HOOKPROC(_callback)
        module_handle = kernel32.GetModuleHandleW(None)
        hook = user32.SetWindowsHookExW(WH_MOUSE_LL, self._proc, module_handle, 0)
        if not hook:
            raise ctypes.WinError()

        try:
            message = wintypes.MSG()
            while not should_stop():
                # прокачиваем очередь, чтобы система вызывала наш хук;
                # PeekMessage не блокирует, поэтому проверяем флаг остановки
                if user32.PeekMessageW(byref(message), None, 0, 0, PM_REMOVE):
                    user32.TranslateMessage(byref(message))
                    user32.DispatchMessageW(byref(message))
                else:
                    sleep(0.005)
        finally:
            user32.UnhookWindowsHookEx(hook)
            self._proc = None

    def _dispatch(self, message_id: int, l_param, on_event: OnEvent) -> None:
        info = cast(l_param, POINTER(MSLLHOOKSTRUCT)).contents
        x, y = info.pt.x, info.pt.y
        timestamp = _now_ms()

        if message_id == WM_MOUSEWHEEL:
            if self._capture_scroll:
                on_event(Event(Action.SCROLL, x, y, timestamp, value=_wheel_steps(info.mouseData)))
            return

        action = _MESSAGES.get(message_id)
        if action is not None:
            on_event(Event(action, x, y, timestamp))
