"""Сведения о системе для метаданных сессии: ОС, разрешение экрана, DPI.

Windows-зависимые вызовы спрятаны внутрь функций, поэтому модуль импортируется
на любой платформе; на не-Windows возвращаются нейтральные значения.
"""

from __future__ import annotations

import platform
import sys

# индексы GetSystemMetrics
_SM_CXSCREEN = 0
_SM_CYSCREEN = 1
# индекс GetDeviceCaps для горизонтального DPI
_LOGPIXELSX = 88


def os_name() -> str:
    """Человекочитаемое название ОС (кросс-платформенно)."""
    return platform.platform()


def make_dpi_aware() -> None:
    """Сделать процесс DPI-aware, чтобы координаты курсора были в реальных
    пикселях. Без этого Windows виртуализирует координаты на HiDPI-экранах.
    Безопасно вызывать повторно и на не-Windows (ничего не делает)."""
    if sys.platform != "win32":
        return
    from ctypes import windll

    try:
        windll.user32.SetProcessDPIAware()
    except Exception:
        # на старых ОС функции может не быть — не критично
        pass


def screen_size() -> tuple[int, int]:
    """Размер основного экрана в пикселях; ``(0, 0)`` на не-Windows."""
    if sys.platform != "win32":
        return (0, 0)
    from ctypes import windll

    user32 = windll.user32
    return (user32.GetSystemMetrics(_SM_CXSCREEN), user32.GetSystemMetrics(_SM_CYSCREEN))


def dpi() -> int:
    """Горизонтальный DPI основного экрана; ``0`` на не-Windows."""
    if sys.platform != "win32":
        return 0
    from ctypes import windll

    user32 = windll.user32
    gdi32 = windll.gdi32
    hdc = user32.GetDC(None)
    if not hdc:
        return 0
    try:
        return gdi32.GetDeviceCaps(hdc, _LOGPIXELSX)
    finally:
        user32.ReleaseDC(None, hdc)
