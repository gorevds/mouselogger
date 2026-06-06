"""Командный интерфейс MouseLogger.

Команды:

* ``start``     — начать сбор (без установки в автозапуск);
* ``install``   — прописать автозапуск и начать сбор;
* ``uninstall`` — убрать автозапуск, остановить сбор, заархивировать логи;
* ``status``    — показать состояние сбора и данных;
* ``purge``     — удалить все собранные данные (право быть забытым).

``start`` и ``install`` требуют зафиксированного согласия участника.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from . import __version__, app, autostart
from .config import Config, record_consent
from .inputs import BACKENDS, DEFAULT_BACKEND
from .storage import archive_logs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="mouselogger",
        description="Сбор данных динамики мыши для исследования аутентификации.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    for name, help_text in (("start", "начать сбор"), ("install", "автозапуск + сбор")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("--backend", choices=BACKENDS, default=DEFAULT_BACKEND,
                       help="бэкенд захвата (по умолчанию: %(default)s)")
        p.add_argument("--consent", action="store_true",
                       help="зафиксировать согласие участника на сбор данных")

    sub.add_parser("uninstall", help="убрать автозапуск, остановить сбор, заархивировать логи")
    sub.add_parser("status", help="показать состояние сбора и данных")

    p_purge = sub.add_parser("purge", help="удалить все собранные данные")
    p_purge.add_argument("--yes", action="store_true", help="не спрашивать подтверждение")

    return parser


def _ensure_consent(config: Config, record: bool) -> Config | None:
    """Проверить (и при необходимости зафиксировать) согласие участника."""
    if record:
        record_consent(config.data_dir)
        config = Config.load()  # перечитать, чтобы учесть свежий маркер согласия
    if not config.consent:
        print(
            "Сбор данных требует согласия участника.\n"
            "Запустите с флагом --consent или задайте MOUSELOGGER_CONSENT=1.",
            file=sys.stderr,
        )
        return None
    return config


def _cmd_start(args: argparse.Namespace, config: Config) -> int:
    config = _ensure_consent(config, args.consent)
    if config is None:
        return 2
    print(f"MouseLogger: сбор начат (бэкенд: {args.backend}). Ctrl+C — остановить.")
    app.run_capture(config, args.backend)
    return 0


def _cmd_install(args: argparse.Namespace, config: Config) -> int:
    config = _ensure_consent(config, args.consent)
    if config is None:
        return 2
    autostart.enable()
    print("MouseLogger: добавлен в автозапуск; сбор начат.")
    app.run_capture(config, args.backend)
    return 0


def _stop_running_instances() -> None:
    """Остановить фоновые экземпляры собранного exe (Windows), не трогая себя."""
    if sys.platform != "win32" or not getattr(sys, "frozen", False):
        return
    import subprocess

    image_name = os.path.basename(sys.executable)
    subprocess.run(
        ["taskkill", "/f", "/im", image_name, "/fi", f"PID ne {os.getpid()}"],
        capture_output=True,
    )


def _cmd_uninstall(_args: argparse.Namespace, config: Config) -> int:
    autostart.disable()
    _stop_running_instances()
    archive_path = archive_logs(config.log_dir, config.archive_dir)
    if archive_path is not None:
        print(f"MouseLogger: автозапуск снят, логи заархивированы в {archive_path}")
    else:
        print("MouseLogger: автозапуск снят; логов для архивации не было.")
    return 0


def _dir_summary(directory: Path, pattern: str) -> tuple[int, int]:
    """Количество файлов по шаблону и их суммарный размер в байтах."""
    files = list(directory.glob(pattern)) if directory.exists() else []
    total = sum(f.stat().st_size for f in files)
    return len(files), total


def _cmd_status(_args: argparse.Namespace, config: Config) -> int:
    log_count, log_bytes = _dir_summary(config.log_dir, "*.jsonl")
    arch_count, arch_bytes = _dir_summary(config.archive_dir, "*.zip")
    print(f"MouseLogger {__version__}")
    print(f"  участник:    {config.participant_id}")
    print(f"  согласие:    {'да' if config.consent else 'нет'}")
    print(f"  автозапуск:  {'включён' if autostart.is_enabled() else 'выключен'}")
    print(f"  каталог:     {config.data_dir}")
    print(f"  логи:        {log_count} файл(ов), {log_bytes} байт")
    print(f"  архивы:      {arch_count} файл(ов), {arch_bytes} байт")
    return 0


def _cmd_purge(args: argparse.Namespace, config: Config) -> int:
    if not args.yes:
        answer = input(f"Удалить все данные в {config.data_dir}? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("Отменено.")
            return 1
    import shutil

    if config.data_dir.exists():
        shutil.rmtree(config.data_dir)
    print(f"MouseLogger: данные удалены ({config.data_dir}).")
    return 0


_COMMANDS = {
    "start": _cmd_start,
    "install": _cmd_install,
    "uninstall": _cmd_uninstall,
    "status": _cmd_status,
    "purge": _cmd_purge,
}


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    config = Config.load()
    return _COMMANDS[args.command](args, config)


if __name__ == "__main__":
    raise SystemExit(main())
