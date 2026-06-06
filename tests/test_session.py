import json

from mouselogger.event import SCHEMA_VERSION
from mouselogger.session import SessionMeta


def _meta(**overrides):
    base = {
        "participant_id": "P-abc",
        "started_ms": 1733500000000,
        "os_name": "Windows 10",
        "screen": (2560, 1440),
        "dpi": 96,
        "sample_hz": 50,
        "consent": True,
        "app_version": "0.2.0",
    }
    base.update(overrides)
    return SessionMeta.create(**base)


def test_create_generates_session_id():
    a, b = _meta(), _meta()
    assert a.session_id and b.session_id
    assert a.session_id != b.session_id


def test_default_schema_version():
    assert _meta().schema_version == SCHEMA_VERSION


def test_round_trip():
    meta = _meta()
    restored = SessionMeta.from_dict(json.loads(json.dumps(meta.to_dict())))
    assert restored == meta


def test_meta_dict_has_type_marker():
    assert _meta().to_dict()["type"] == "meta"
    assert _meta().to_dict()["screen"] == [2560, 1440]
