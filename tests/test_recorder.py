from mouselogger.event import Action, Event
from mouselogger.recorder import Recorder
from mouselogger.session import SessionMeta
from mouselogger.storage.base import Sink


class FakeSink(Sink):
    def __init__(self):
        self.events = []
        self.opened = False
        self.closed = False

    def open(self, meta):
        self.opened = True

    def write(self, event):
        self.events.append(event)

    def close(self):
        self.closed = True


def _run(seq, idle_threshold_ms=500):
    sink = FakeSink()
    recorder = Recorder(sink, idle_threshold_ms=idle_threshold_ms)
    recorder.open(
        SessionMeta.create(
            participant_id="P", started_ms=0, os_name="t", screen=(1, 1),
            dpi=96, sample_hz=50, consent=True, app_version="0",
        )
    )
    for event in seq:
        recorder.feed(event)
    recorder.close()
    assert sink.opened and sink.closed
    return [(e.action, e.x, e.y, e.t, e.value) for e in sink.events]


def test_stationary_moves_are_deduped():
    out = _run([
        Event(Action.MOVE, 5, 5, 1000),
        Event(Action.MOVE, 5, 5, 1100),
        Event(Action.MOVE, 6, 6, 1200),
    ])
    assert out == [
        (Action.MOVE, 5, 5, 1000, None),
        (Action.MOVE, 6, 6, 1200, None),
    ]


def test_long_dwell_emits_idle():
    out = _run([
        Event(Action.MOVE, 1, 1, 0),
        Event(Action.MOVE, 1, 1, 600),
        Event(Action.MOVE, 2, 2, 620),
    ])
    assert out == [
        (Action.MOVE, 1, 1, 0, None),
        (Action.IDLE, 1, 1, 0, 620),
        (Action.MOVE, 2, 2, 620, None),
    ]


def test_button_closes_dwell_and_passes_through():
    out = _run([
        Event(Action.MOVE, 7, 7, 2000),
        Event(Action.MOVE, 7, 7, 2700),
        Event(Action.LEFT_DOWN, 7, 7, 2800),
    ])
    assert [e[0] for e in out] == [Action.MOVE, Action.IDLE, Action.LEFT_DOWN]


def test_close_flushes_trailing_dwell():
    out = _run([
        Event(Action.MOVE, 8, 8, 3000),
        Event(Action.MOVE, 8, 8, 3600),
    ])
    assert out[-1] == (Action.IDLE, 8, 8, 3000, 600)


def test_scroll_is_not_movement():
    out = _run([
        Event(Action.MOVE, 9, 9, 10),
        Event(Action.SCROLL, 9, 9, 20, -3),
        Event(Action.MOVE, 9, 9, 30),
    ])
    assert [e[0] for e in out] == [Action.MOVE, Action.SCROLL, Action.MOVE]
