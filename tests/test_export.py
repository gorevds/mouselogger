import csv

from mouselogger.event import Action, Event
from mouselogger.export import (
    FEATURE_COLUMNS,
    extract_features,
    iter_log_files,
    parse_log_file,
    write_csv,
)
from mouselogger.export.__main__ import main as export_main
from mouselogger.session import SessionMeta
from mouselogger.storage import JsonlSink

T0 = 1_733_500_000_000


def _write_log(tmp_path):
    meta = SessionMeta.create(
        participant_id="P-77", started_ms=T0, os_name="Test",
        screen=(1000, 500), dpi=96, sample_hz=50, consent=True, app_version="0",
    )
    events = [
        Event(Action.MOVE, 0, 0, T0),
        Event(Action.MOVE, 100, 0, T0 + 100),
        Event(Action.LEFT_DOWN, 100, 0, T0 + 150),
        Event(Action.LEFT_UP, 100, 0, T0 + 250),
        Event(Action.MOVE, 100, 100, T0 + 350),
        Event(Action.IDLE, 100, 100, T0 + 350, value=800),
    ]
    sink = JsonlSink(tmp_path / "logs", "P-77", flush_every=1)
    sink.open(meta)
    for event in events:
        sink.write(event)
    sink.close()
    return next((tmp_path / "logs").glob("*.jsonl")), meta, events


def test_parse_round_trip(tmp_path):
    log_file, meta, events = _write_log(tmp_path)
    parsed_meta, parsed_events = parse_log_file(log_file)
    assert parsed_meta == meta
    assert parsed_events == events


def test_extract_features_values(tmp_path):
    log_file, _, _ = _write_log(tmp_path)
    meta, events = parse_log_file(log_file)
    feat = extract_features(meta, events)

    assert feat["participant"] == "P-77"
    assert feat["n_events"] == 6
    assert feat["n_moves"] == 3
    assert feat["n_left_clicks"] == 1
    assert feat["click_duration_mean"] == 100.0
    assert feat["n_idle"] == 1
    assert feat["idle_total_ms"] == 800
    # нормировка: 100px по ширине 1000 за 100мс -> 0.001 норм.ед/мс
    assert feat["speed_max"] == 0.002
    assert 0.0 <= feat["straightness_mean"] <= 1.0
    assert set(feat) == set(FEATURE_COLUMNS)


def test_extract_features_empty():
    feat = extract_features(None, [])
    assert feat["n_events"] == 0
    assert feat["duration_ms"] == 0
    assert feat["speed_mean"] == 0.0


def test_iter_log_files_expands_dir(tmp_path):
    log_file, _, _ = _write_log(tmp_path)
    found = list(iter_log_files([tmp_path / "logs"]))
    assert found == [log_file]


def test_write_csv(tmp_path):
    rows = [extract_features(*parse_log_file(_write_log(tmp_path)[0]))]
    out = tmp_path / "out" / "features.csv"
    assert write_csv(rows, out) == 1
    with out.open(encoding="utf-8") as handle:
        reader = list(csv.DictReader(handle))
    assert len(reader) == 1
    assert reader[0]["participant"] == "P-77"
    assert list(reader[0].keys()) == list(FEATURE_COLUMNS)


def test_export_cli(tmp_path):
    log_file, _, _ = _write_log(tmp_path)
    out = tmp_path / "features.csv"
    assert export_main([str(log_file), "-o", str(out)]) == 0
    assert out.exists()
