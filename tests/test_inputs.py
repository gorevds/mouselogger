import pytest

from mouselogger.inputs import BACKENDS, DEFAULT_BACKEND, create_input_source


class _Cfg:
    capture_scroll = True
    poll_interval = 0.02


def test_default_backend_is_known():
    assert DEFAULT_BACKEND in BACKENDS


def test_unknown_backend_raises_before_touching_winapi():
    # должно упасть ValueError, не пытаясь импортировать windll
    with pytest.raises(ValueError):
        create_input_source(_Cfg(), "does-not-exist")
