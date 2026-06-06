from mouselogger.config import (
    DEFAULT_SAMPLE_HZ,
    MAX_SAMPLE_HZ,
    MIN_SAMPLE_HZ,
    Config,
    record_consent,
)


def _env(tmp_path, **extra):
    return {"MOUSELOGGER_DIR": str(tmp_path), **extra}


def test_data_dir_from_env(tmp_path):
    cfg = Config.load(_env(tmp_path))
    assert cfg.data_dir == tmp_path
    assert cfg.log_dir == tmp_path / "logs"
    assert cfg.archive_dir == tmp_path / "archive"


def test_participant_id_persists(tmp_path):
    first = Config.load(_env(tmp_path)).participant_id
    second = Config.load(_env(tmp_path)).participant_id
    assert first == second
    assert first.startswith("P-")


def test_participant_id_from_env_overrides(tmp_path):
    cfg = Config.load(_env(tmp_path, MOUSELOGGER_PARTICIPANT="P-custom"))
    assert cfg.participant_id == "P-custom"


def test_sample_hz_clamped(tmp_path):
    assert Config.load(_env(tmp_path, MOUSELOGGER_SAMPLE_HZ="0")).sample_hz == MIN_SAMPLE_HZ
    assert Config.load(_env(tmp_path, MOUSELOGGER_SAMPLE_HZ="99999")).sample_hz == MAX_SAMPLE_HZ
    assert Config.load(_env(tmp_path, MOUSELOGGER_SAMPLE_HZ="abc")).sample_hz == DEFAULT_SAMPLE_HZ
    assert Config.load(_env(tmp_path, MOUSELOGGER_SAMPLE_HZ="")).sample_hz == DEFAULT_SAMPLE_HZ


def test_poll_interval(tmp_path):
    cfg = Config.load(_env(tmp_path, MOUSELOGGER_SAMPLE_HZ="100"))
    assert cfg.poll_interval == 0.01


def test_consent_default_false(tmp_path):
    assert Config.load(_env(tmp_path)).consent is False


def test_consent_from_env(tmp_path):
    assert Config.load(_env(tmp_path, MOUSELOGGER_CONSENT="yes")).consent is True


def test_consent_from_marker_file(tmp_path):
    assert Config.load(_env(tmp_path)).consent is False
    record_consent(tmp_path)
    assert Config.load(_env(tmp_path)).consent is True


def test_config_is_frozen(tmp_path):
    import dataclasses

    cfg = Config.load(_env(tmp_path))
    try:
        cfg.sample_hz = 1  # type: ignore[misc]
    except dataclasses.FrozenInstanceError:
        return
    raise AssertionError("Config must be immutable")
