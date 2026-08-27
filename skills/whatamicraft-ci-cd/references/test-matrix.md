# Real behavior matrix

| Area | Prove success | Prove failure/safety |
| --- | --- | --- |
| dashboard | actual HTTP/UI reads seeded state and performs every visible control | invalid action rejected; error dismiss/cancel/revert restores usable state |
| clues API | load/list/filter/update through API/database; used and unused remain distinct | invalid package/status rejected; reservation reversal cannot erase real usage |
| producer | discovers unused current-template episode; text, voice, type and output agree | failed/cancelled render leaves no completed/corrupt artifact and next task runs |
| publisher-worker | due item creates correct per-platform title/caption/vertical thumbnail request | provider failure is redacted, retried idempotently, never marked published |
| Telegram bot | actual router sends status, approval list/video, buttons, progress and alerts to fake API | timeout/malformed/error response logs safely and remains responsive |
| media | actual service returns exact bytes, MIME, ranges, vertical thumbnail, and discovery | missing/traversal blocked without leaking files; fixture volume isolated |
| analytics API | latest enabled-platform records sync and persist with freshness/error metadata | unavailable/malformed provider preserves prior valid state and reports error |
| monitor | checks dependencies, emits redacted event, detects recovery | dependency loss does not crash monitor or expose secrets |
| backup/rollback | backup contains allowlisted state and restore recovers it | auth/confirmation/corrupt archive rejected; preventive backup retained |
| cross-service | dashboard/API/worker/media exchange real requests and durable state | unavailable dependency gives actionable state and unrelated services continue |
| thumbnails | correct existing vertical asset, kind folder, icon, silhouette, IG/YT reuse | wrong kind/missing silhouette/horizontal-square route fails; no render required |
| scheduler | low-water `5` fills toward `8`; due publication proceeds independently | skipped/interrupted task remains recoverable; generation and publishing do not block each other |

For every row ask: what real code ran, what observable result proves it, and which assertion fails if the feature is removed?

