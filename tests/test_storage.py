import json
import zipfile

import pytest

from mouselogger.event import Action, Event
from mouselogger.session import SessionMeta
from mouselogger.storage import JsonlSink, archive_logs

DAY_MS = 86_400_000
T0 = 1_733_500_000_000


def _meta(started_ms=T0):
    return SessionMeta.create(
        participant_id="P-x", started_ms=started_ms, os_name="Test",
        screen=(1920, 1080), dpi=96, sample_hz=50, consent=True, app_version="0",
    )


def test_write_before_open_raises(tmp_path):
    sink = JsonlSink(tmp_path / "logs", "P-x")
    with pytest.raises(RuntimeError):
        sink.write(Event(Action.MOVE, 1, 1, T0))


def test_rotation_across_midnight(tmp_path):
    log_dir = tmp_path / "logs"
    sink = JsonlSink(log_dir, "P-x", flush_every=1)
    sink.open(_meta())
    sink.write(Event(Action.MOVE, 1, 2, T0))
    sink.write(Event(Action.MOVE, 9, 9, T0 + DAY_MS))
    sink.close()

    files = sorted(p.name for p in log_dir.glob("*.jsonl"))
    assert len(files) == 2


def test_meta_is_first_line_once(tmp_path):
    log_dir = tmp_path / "logs"
    meta = _meta()

    sink = JsonlSink(log_dir, "P-x", flush_every=1)
    sink.open(meta)
    sink.write(Event(Action.MOVE, 1, 2, T0))
    sink.close()

    # повторное открытие в тот же день дописывает, не дублируя мету
    sink2 = JsonlSink(log_dir, "P-x", flush_every=1)
    sink2.open(meta)
    sink2.write(Event(Action.MOVE, 3, 4, T0 + 1000))
    sink2.close()

    log_file = next(log_dir.glob("*.jsonl"))
    lines = log_file.read_text(encoding="utf-8").splitlines()
    meta_lines = [json.loads(line) for line in lines if json.loads(line).get("type") == "meta"]
    assert len(meta_lines) == 1
    assert meta_lines[0]["session"] == meta.session_id
    assert json.loads(lines[1])["a"] == "M"


def test_archive_uses_bare_arcnames_and_removes_sources(tmp_path):
    log_dir = tmp_path / "logs"
    archive_dir = tmp_path / "archive"
    sink = JsonlSink(log_dir, "P-x", flush_every=1)
    sink.open(_meta())
    sink.write(Event(Action.MOVE, 1, 2, T0))
    sink.close()

    archive_path = archive_logs(log_dir, archive_dir)
    assert archive_path is not None and archive_path.parent == archive_dir
    with zipfile.ZipFile(archive_path) as zf:
        names = zf.namelist()
    assert names and all("/" not in n and "\\" not in n for n in names)
    assert list(log_dir.glob("*.jsonl")) == []


def test_archive_empty_returns_none(tmp_path):
    assert archive_logs(tmp_path / "logs", tmp_path / "archive") is None
