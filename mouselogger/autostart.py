"""Автозапуск под Windows через реестр (HKCU\\...\\Run).

Запись в ветку ``Run`` надёжнее и чище ``.bat`` в папке «Автозагрузка»: нет
мелькающего окна консоли и предсказуемое удаление. Все функции безопасно
вызываются на не-Windows (``winreg`` импортируется лениво).
"""

from __future__ import annotations

import sys
from os import path

# имя значения в ветке Run и сама ветка
VALUE_NAME = "MouseLogger"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _require_windows() -> None:
    if sys.platform != "win32":
        raise RuntimeError("автозапуск поддерживается только на Windows")


def executable_command() -> str:
    """Команда запуска сбора: путь к exe (или скрипту) плюс аргумент ``start``."""
    if getattr(sys, "frozen", False):
        target = sys.executable
    else:
        target = path.abspath(sys.argv[0])
    return f'"{target}" start'


def enable() -> None:
    """Прописать MouseLogger в автозапуск текущего пользователя."""
    _require_windows()
    import winreg

    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, executable_command())


def disable() -> None:
    """Убрать MouseLogger из автозапуска (повторный вызов не падает)."""
    _require_windows()
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, VALUE_NAME)
    except FileNotFoundError:
        # ветки или значения нет — уже отключено
        pass


def is_enabled() -> bool:
    """Прописан ли автозапуск; на не-Windows всегда ``False``."""
    if sys.platform != "win32":
        return False
    import winreg

    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_QUERY_VALUE
        ) as key:
            winreg.QueryValueEx(key, VALUE_NAME)
            return True
    except FileNotFoundError:
        return False
