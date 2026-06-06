"""Архивация логов: упаковка всех собранных файлов в один zip.

Архив кладётся в отдельный каталог (не в каталог логов), поэтому при повторной
архивации не пытается включить сам себя.
"""

from __future__ import annotations

import zipfile
from datetime import datetime
from pathlib import Path

LOG_GLOB = "*.jsonl"


def archive_logs(
    log_dir: Path,
    archive_dir: Path,
    archive_name: str | None = None,
) -> Path | None:
    """Упаковать все ``*.jsonl`` из ``log_dir`` в один zip в ``archive_dir``.

    Исходные логи удаляются только после успешной записи архива. Возвращает путь
    к созданному архиву или ``None``, если логов не было.
    """
    log_dir = Path(log_dir)
    archive_dir = Path(archive_dir)

    logs = sorted(log_dir.glob(LOG_GLOB))
    if not logs:
        return None

    archive_dir.mkdir(parents=True, exist_ok=True)
    name = archive_name or "logs-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    archive_path = archive_dir / (name + ".zip")

    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for log in logs:
            # arcname=log.name — иначе внутрь zip попадёт абсолютный путь
            archive.write(log, arcname=log.name)

    for log in logs:
        log.unlink()

    return archive_path
