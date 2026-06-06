import pytest

from mouselogger.cli import main


@pytest.fixture
def data_env(tmp_path, monkeypatch):
    monkeypatch.setenv("MOUSELOGGER_DIR", str(tmp_path))
    monkeypatch.delenv("MOUSELOGGER_CONSENT", raising=False)
    return tmp_path


def test_status_ok(data_env, capsys):
    assert main(["status"]) == 0
    out = capsys.readouterr().out
    assert "участник" in out
    assert "автозапуск" in out


def test_start_without_consent_refuses(data_env, capsys):
    # должно вернуть код 2 и не обращаться к захвату ввода (windll)
    assert main(["start"]) == 2
    assert "согласи" in capsys.readouterr().err.lower()


def test_purge_removes_data(data_env):
    main(["status"])  # создаёт каталог данных и participant-файл
    assert data_env.exists()
    assert main(["purge", "--yes"]) == 0
    assert not data_env.exists()


def test_purge_without_yes_is_cancelled(data_env, monkeypatch):
    main(["status"])
    monkeypatch.setattr("builtins.input", lambda _prompt: "n")
    assert main(["purge"]) == 1
    assert data_env.exists()
