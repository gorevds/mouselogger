"""Точка входа для сборки PyInstaller.

Вся логика — в пакете :mod:`mouselogger`; этот файл лишь делегирует в CLI,
чтобы оставалась привычная команда сборки exe из ``main.py``.
"""

from mouselogger.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
