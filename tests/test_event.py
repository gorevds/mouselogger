import json

import pytest

from mouselogger.event import SCHEMA_VERSION, Action, Event


@pytest.mark.parametrize(
    "event",
    [
        Event(Action.MOVE, -10, 5, 1733500000020),
        Event(Action.LEFT_DOWN, 100, 200, 1733500000180),
        Event(Action.SCROLL, 100, 200, 1733500000200, value=-3),
        Event(Action.IDLE, 100, 200, 1733500001000, value=800),
        Event(Action.SCROLL, 0, 0, 1, value=0),  # value=0 не должно теряться
    ],
)
def test_event_round_trip(event):
    restored = Event.from_dict(json.loads(json.dumps(event.to_dict())))
    assert restored == event
    assert restored.value == event.value


def test_move_has_no_value_key():
    assert "v" not in Event(Action.MOVE, 1, 2, 3).to_dict()


def test_position_key_ignores_time():
    a = Event(Action.MOVE, 1, 2, 10)
    b = Event(Action.MOVE, 1, 2, 99)
    assert a.position_key == b.position_key
    assert a != b  # полное равенство учитывает время


def test_event_is_hashable():
    assert len({Event(Action.MOVE, 1, 2, 10), Event(Action.MOVE, 1, 2, 10)}) == 1


def test_action_serializes_as_string():
    assert json.dumps({"a": Action.MOVE}) == '{"a": "M"}'


def test_schema_version_positive():
    assert SCHEMA_VERSION >= 1
