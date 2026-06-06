"""CLI экспортёра: ``python -m mouselogger.export <пути> -o features.csv``."""

from __future__ import annotations

import argparse
from pathlib import Path

from .features import extract_features, iter_log_files, parse_log_file, write_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="mouselogger.export",
        description="Собрать логи динамики мыши в таблицу признаков (CSV).",
    )
    parser.add_argument("paths", nargs="+", type=Path,
                        help="файлы .jsonl или каталоги с ними")
    parser.add_argument("-o", "--out", type=Path, required=True,
                        help="путь к выходному CSV-файлу")
    args = parser.parse_args(argv)

    files = list(iter_log_files(args.paths))
    rows = []
    for path in files:
        meta, events = parse_log_file(path)
        rows.append(extract_features(meta, events))

    written = write_csv(rows, args.out)
    print(f"Экспортировано строк: {written} (файлов: {len(files)}) -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
