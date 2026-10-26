# Requirements Analysis

> No detailed specification was provided. The following requirements were
> derived through structured analysis, prioritisation (MoSCoW), and
> engineering judgement.

---

## 1. Functional Requirements

| ID   | Requirement                                                                 | Priority |
|------|-----------------------------------------------------------------------------|----------|
| FR-1 | User can set an alarm by specifying a time (HH:MM, 24-hour format)          | Must     |
| FR-2 | Application continuously checks current time against alarm time             | Must     |
| FR-3 | When alarm triggers, application produces an audible/visual alert           | Must     |
| FR-4 | User can snooze a triggered alarm (default: 5 minutes)                      | Should   |
| FR-5 | User can cancel/dismiss a triggered alarm                                   | Must     |
| FR-6 | User can set multiple alarms in a single session                            | Should   |
| FR-7 | Application displays time remaining until the next alarm                    | Should   |
| FR-8 | User can set alarms via command-line arguments for quick use                | Could    |
| FR-9 | User can configure snooze duration                                          | Could    |

## 2. Non-Functional Requirements

| ID    | Requirement                                                                  |
|-------|------------------------------------------------------------------------------|
| NFR-1 | **Responsiveness** — Alarm triggers within 1 second of target time           |
| NFR-2 | **Resource efficiency** — Polling interval minimizes CPU usage (≤1% idle)    |
| NFR-3 | **Portability** — Runs on Python 3.11+ with no external dependencies         |
| NFR-4 | **Usability** — Clear prompts, input validation, helpful error messages      |
| NFR-5 | **Graceful shutdown** — Handle Ctrl+C cleanly without stack traces           |
| NFR-6 | **Testability** — Core logic separated from I/O for unit testing             |
| NFR-7 | **Code quality** — PEP 8, type hints, docstrings on all public functions     |

## 3. Assumptions

1. **Single-user, single-session** — No persistence between runs.
2. **Same-day alarms** — Past times rejected; snooze past midnight prevented.
3. **Local time** — All times use system timezone; no conversion needed.
4. **Terminal capabilities** — Basic Unicode output; audible alert via bell (`\a`).
5. **Foreground process** — User keeps the terminal open.
6. **24-hour format** — Avoids AM/PM ambiguity.

## 4. Out of Scope

| Feature                        | Rationale                                    |
|--------------------------------|----------------------------------------------|
| Recurring/repeating alarms     | Scheduling complexity beyond MVP             |
| Persistent storage (file/DB)   | No cross-session requirement                 |
| Custom alarm sounds            | Requires external libraries                  |
| GUI or TUI framework           | Scope is CLI; stdlib only                    |
| Timezone conversion            | Unnecessary for local-only use               |
| Configuration file             | Over-engineering for a single-session tool    |

## 5. Edge Cases

| #  | Edge Case                               | Expected Behaviour                                        |
|----|----------------------------------------|-----------------------------------------------------------|
| 1  | Time already passed today               | Reject with clear message                                 |
| 2  | Invalid format (`25:99`, `abc`, `3pm`)  | Reject with format guidance                               |
| 3  | Alarm for current minute                | Accept; triggers within 0–59 seconds                      |
| 4  | Ctrl+C during wait                      | Graceful exit: "Goodbye!"                                 |
| 5  | Ctrl+C during snooze prompt             | Graceful exit: "Goodbye!"                                 |
| 6  | Snooze would push past midnight         | Reject snooze, auto-dismiss with explanation              |
| 7  | Empty input                             | Re-prompt without crash                                   |
| 8  | Multiple alarms at same time            | Process sequentially                                      |
| 9  | System clock changes (NTP sync)         | Self-corrects — wall-clock comparison each tick            |
| 10 | Alarm time exactly midnight (`00:00`)   | Valid if app started before midnight                       |
