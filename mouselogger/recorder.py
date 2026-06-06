"""Recorder — приём потока событий от источника ввода и запись в приёмник.

Логика не зависит от конкретного бэкенда ввода: она принимает уже
типизированные :class:`Event` и применяет к ним сквозную политику записи.

Главная задача политики — компактность лога без потери поведенческого сигнала:

* подряд идущие ``MOVE`` в одной и той же точке (курсор стоит на месте) не
  дублируются;
* но если простой длится дольше порога, он фиксируется отдельным событием
  ``IDLE`` с длительностью паузы — это сохраняет dwell-time/«колебания», один
  из сильнейших признаков для биометрии по динамике мыши.

Координаты пишутся «сырыми»; нормализация по разрешению экрана — на этапе
экспорта признаков, чтобы лог оставался без потерь.
"""

from __future__ import annotations

from .event import Action, Event
from .session import SessionMeta
from .storage.base import Sink

# простой короче порога не выделяется в отдельное событие IDLE (мс)
DEFAULT_IDLE_THRESHOLD_MS = 500


class Recorder:
    """Применяет дедуп-с-сохранением-пауз и пишет события в приёмник."""

    def __init__(self, sink: Sink, idle_threshold_ms: int = DEFAULT_IDLE_THRESHOLD_MS) -> None:
        self._sink = sink
        self._idle_threshold_ms = idle_threshold_ms
        self._last_written: Event | None = None
        self._stationary_since: int | None = None   # время начала простоя, мс
        self._stationary_pos: tuple[int, int] | None = None
        self._last_sample_t: int | None = None

    def open(self, meta: SessionMeta) -> None:
        """Открыть сессию записи."""
        self._sink.open(meta)
        self._last_written = None
        self._stationary_since = None
        self._stationary_pos = None
        self._last_sample_t = None

    def feed(self, event: Event) -> None:
        """Обработать одно событие от источника ввода."""
        self._last_sample_t = event.t

        if event.action == Action.MOVE and self._is_stationary_repeat(event):
            # курсор стоит на месте: запоминаем начало простоя, событие не пишем
            if self._stationary_since is None and self._last_written is not None:
                self._stationary_since = self._last_written.t
                self._stationary_pos = (self._last_written.x, self._last_written.y)
            return

        # любое значимое событие закрывает текущий простой (возможно, событием IDLE)
        self._flush_idle(event.t)
        self._write(event)

    def close(self) -> None:
        """Завершить сессию: зафиксировать незакрытый простой и закрыть приёмник."""
        if self._last_sample_t is not None:
            self._flush_idle(self._last_sample_t)
        self._sink.close()

    def _is_stationary_repeat(self, event: Event) -> bool:
        last = self._last_written
        return (
            last is not None
            and last.action == Action.MOVE
            and last.x == event.x
            and last.y == event.y
        )

    def _flush_idle(self, now_ms: int) -> None:
        """Если был достаточно длинный простой, записать событие IDLE."""
        if self._stationary_since is None or self._stationary_pos is None:
            return
        duration = now_ms - self._stationary_since
        if duration >= self._idle_threshold_ms:
            x, y = self._stationary_pos
            self._write(Event(Action.IDLE, x, y, self._stationary_since, value=duration))
        self._stationary_since = None
        self._stationary_pos = None

    def _write(self, event: Event) -> None:
        self._sink.write(event)
        self._last_written = event
