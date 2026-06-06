# MouseLogger

[Русский](README.md) | **English**

A data-collection module for the research project
**"User authentication by mouse movement"**.

The tool records mouse dynamics (trajectories, button presses, scrolling, pauses,
timestamps) and stores them in local log files. The collected data is the training
set for building a behavioural-biometric profile of a user from their motor
"handwriting".

> ⚠️ **Data is collected only with the participant's explicit consent.**
> The tool is intended for research collection on your own or controlled machines
> with informed consent. The `start`/`install` commands refuse to run without
> recorded consent. Do not use it for covert surveillance of third parties.

## Installation

No third-party runtime dependencies — only the Python 3.10+ standard library and
WinAPI via `ctypes` (on Windows).

```bash
pip install .
```

After installation the `mouselogger` command is available. Without installing you
can run it via `python -m mouselogger`.

## Usage

```bash
mouselogger start --consent     # record consent and start collecting
mouselogger start               # start collecting (consent already given)
mouselogger install --consent   # register Windows autostart and start collecting
mouselogger uninstall           # remove autostart, stop collecting, archive logs
mouselogger status              # collection state and data volume
mouselogger purge               # delete all collected data (right to be forgotten)
```

Stop collection with `Ctrl+C` (graceful shutdown with buffer flush).

### Capture backends

`start`/`install` accept `--backend`:

* `hook` (default) — low-level `WH_MOUSE_LL` system hook: event-driven, no jitter
  or missed events, captures scrolling. Recommended.
* `poll` — fixed-rate polling (movement and buttons, no scrolling).

### Configuration (environment variables)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MOUSELOGGER_DIR` | data directory | `%LOCALAPPDATA%\MouseLogger` |
| `MOUSELOGGER_PARTICIPANT` | participant identifier | generated and stored |
| `MOUSELOGGER_SAMPLE_HZ` | polling rate (1–1000) | `50` |
| `MOUSELOGGER_SCROLL` | capture scrolling | `1` |
| `MOUSELOGGER_CONSENT` | consent to collection | `0` |

Logs live in `<data dir>/logs`, archives in `<data dir>/archive`. The participant
id is a pseudonym (not the system login), so the data contains no PII.

## Data format

Logs are JSON Lines (`.jsonl`); the first line is the session metadata, the rest
are events. Full schema: [`docs/DATA_FORMAT.md`](docs/DATA_FORMAT.md).

## Feature export

Turn raw logs into a feature table (CSV) for training:

```bash
python -m mouselogger.export <dir-or-files>.jsonl -o features.csv
```

Coordinates are normalized by the screen resolution from the metadata; speed,
acceleration, click durations, pause statistics and straightness are computed. The
row label is `participant`.

## Building the .exe (Windows)

```bat
pyinstaller --onefile --windowed --name MouseLogger main.py
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
mypy mouselogger
pytest
```

The platform-independent core is covered by tests and passes the checks on Linux
CI; the WinAPI code is verified on Windows. Project layout is described in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

## License

[MIT](LICENSE).
