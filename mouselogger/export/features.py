"""Извлечение признаков из логов динамики мыши.

Один лог-файл (одна сессия) превращается в одну строку признаков с меткой
участника — это и есть обучающая выборка для задачи аутентификации.

Координаты нормируются в диапазон ``[0, 1]`` по разрешению экрана из
метаданных сессии, поэтому признаки сопоставимы между разными машинами.
Кинематика (скорость/ускорение) считается в нормированных единицах за
миллисекунду.
"""

from __future__ import annotations

import csv
import json
import math
import statistics
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from ..event import Action, Event
from ..session import META_TYPE, SessionMeta

# события, образующие траекторию курсора (есть осмысленная позиция и время)
_TRAJECTORY_ACTIONS = frozenset({
    Action.MOVE,
    Action.LEFT_DOWN, Action.LEFT_UP,
    Action.RIGHT_DOWN, Action.RIGHT_UP,
    Action.MIDDLE_DOWN, Action.MIDDLE_UP,
})

# порядок колонок в выходном CSV
FEATURE_COLUMNS: tuple[str, ...] = (
    "participant", "session", "os", "sample_hz",
    "duration_ms", "n_events", "n_moves",
    "n_left_clicks", "n_right_clicks", "n_middle_clicks", "n_scrolls",
    "n_idle", "idle_total_ms", "idle_mean_ms",
    "path_length", "speed_mean", "speed_std", "speed_max",
    "accel_mean", "accel_std",
    "click_duration_mean", "click_duration_std",
    "straightness_mean",
)


def iter_log_files(paths: Iterable[Path]) -> Iterator[Path]:
    """Развернуть пути (файлы и каталоги) в отдельные ``*.jsonl`` файлы."""
    for path in paths:
        if path.is_dir():
            yield from sorted(path.glob("*.jsonl"))
        elif path.suffix == ".jsonl":
            yield path


def parse_log_file(path: Path) -> tuple[SessionMeta | None, list[Event]]:
    """Прочитать лог: метаданные (если есть) и список событий."""
    meta: SessionMeta | None = None
    events: list[Event] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == META_TYPE:
                meta = SessionMeta.from_dict(record)
            else:
                events.append(Event.from_dict(record))
    return meta, events


def _stats(values: Sequence[float]) -> tuple[float, float, float]:
    """(среднее, выборочное стандартное отклонение, максимум); нули при нехватке данных."""
    if not values:
        return (0.0, 0.0, 0.0)
    mean = statistics.fmean(values)
    std = statistics.stdev(values) if len(values) > 1 else 0.0
    return (mean, std, max(values))


def _normalizer(meta: SessionMeta | None):
    """Функция приведения (x, y) к нормированным координатам по разрешению экрана."""
    if meta is None or meta.screen_width <= 0 or meta.screen_height <= 0:
        return lambda x, y: (float(x), float(y))
    width, height = meta.screen_width, meta.screen_height
    return lambda x, y: (x / width, y / height)


def _click_durations(events: Sequence[Event]) -> list[float]:
    """Длительности удержания левой кнопки (мс): от L_D до следующего L_U."""
    durations: list[float] = []
    pending_down: int | None = None
    for event in events:
        if event.action == Action.LEFT_DOWN:
            pending_down = event.t
        elif event.action == Action.LEFT_UP and pending_down is not None:
            durations.append(event.t - pending_down)
            pending_down = None
    return durations


# действия-разделители сегментов траектории (естественные «остановки»)
_SEGMENT_BOUNDARIES = frozenset({
    Action.LEFT_DOWN, Action.RIGHT_DOWN, Action.MIDDLE_DOWN,
})


def _segment_straightness(segment: Sequence[tuple[float, float]]) -> float | None:
    """Прямолинейность одного сегмента: прямая / длина пути (0..1) или None."""
    if len(segment) < 2:
        return None
    path_len = 0.0
    for (x0, y0), (x1, y1) in zip(segment, segment[1:], strict=False):
        path_len += math.hypot(x1 - x0, y1 - y0)
    if path_len <= 0:
        return None
    straight = math.hypot(segment[-1][0] - segment[0][0], segment[-1][1] - segment[0][1])
    return straight / path_len


def extract_features(meta: SessionMeta | None, events: Sequence[Event]) -> dict[str, object]:
    """Посчитать строку признаков для одной сессии."""
    normalize = _normalizer(meta)

    # траектория: нормированные точки с временем, в хронологическом порядке;
    # параллельно режем её на сегменты по кликам для оценки прямолинейности
    points: list[tuple[float, float, int]] = []
    segments: list[list[tuple[float, float]]] = []
    current_segment: list[tuple[float, float]] = []
    for event in events:
        if event.action in _TRAJECTORY_ACTIONS:
            nx, ny = normalize(event.x, event.y)
            points.append((nx, ny, event.t))
            current_segment.append((nx, ny))
            if event.action in _SEGMENT_BOUNDARIES:
                segments.append(current_segment)
                current_segment = []
    if current_segment:
        segments.append(current_segment)

    # скорости и ускорения по сегментам с положительным dt
    speeds: list[float] = []
    seg_times: list[int] = []
    path_length = 0.0
    for (x0, y0, t0), (x1, y1, t1) in zip(points, points[1:], strict=False):
        dist = math.hypot(x1 - x0, y1 - y0)
        path_length += dist
        dt = t1 - t0
        if dt > 0:
            speeds.append(dist / dt)
            seg_times.append(dt)

    accels: list[float] = []
    speed_pairs = zip(speeds, speeds[1:], strict=False)
    time_pairs = zip(seg_times, seg_times[1:], strict=False)
    for (s0, s1), (dt0, dt1) in zip(speed_pairs, time_pairs, strict=False):
        span = (dt0 + dt1) / 2
        if span > 0:
            accels.append((s1 - s0) / span)

    idle_values = [e.value for e in events if e.action == Action.IDLE and e.value is not None]
    click_durations = _click_durations(events)

    speed_mean, speed_std, speed_max = _stats(speeds)
    accel_mean, accel_std, _ = _stats([abs(a) for a in accels])
    click_mean, click_std, _ = _stats([float(d) for d in click_durations])
    straightness = [
        ratio for ratio in (_segment_straightness(seg) for seg in segments)
        if ratio is not None
    ]

    timestamps = [e.t for e in events]
    duration_ms = (max(timestamps) - min(timestamps)) if timestamps else 0

    return {
        "participant": meta.participant_id if meta else "",
        "session": meta.session_id if meta else "",
        "os": meta.os_name if meta else "",
        "sample_hz": meta.sample_hz if meta else 0,
        "duration_ms": duration_ms,
        "n_events": len(events),
        "n_moves": sum(1 for e in events if e.action == Action.MOVE),
        "n_left_clicks": sum(1 for e in events if e.action == Action.LEFT_DOWN),
        "n_right_clicks": sum(1 for e in events if e.action == Action.RIGHT_DOWN),
        "n_middle_clicks": sum(1 for e in events if e.action == Action.MIDDLE_DOWN),
        "n_scrolls": sum(1 for e in events if e.action == Action.SCROLL),
        "n_idle": len(idle_values),
        "idle_total_ms": sum(idle_values),
        "idle_mean_ms": round(statistics.fmean(idle_values), 3) if idle_values else 0.0,
        "path_length": round(path_length, 6),
        "speed_mean": round(speed_mean, 6),
        "speed_std": round(speed_std, 6),
        "speed_max": round(speed_max, 6),
        "accel_mean": round(accel_mean, 6),
        "accel_std": round(accel_std, 6),
        "click_duration_mean": round(click_mean, 3),
        "click_duration_std": round(click_std, 3),
        "straightness_mean": round(statistics.fmean(straightness), 6) if straightness else 0.0,
    }


def write_csv(rows: Iterable[dict[str, object]], out_path: Path) -> int:
    """Записать строки признаков в CSV с фиксированным порядком колонок.

    Возвращает количество записанных строк.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FEATURE_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FEATURE_COLUMNS})
            count += 1
    return count
