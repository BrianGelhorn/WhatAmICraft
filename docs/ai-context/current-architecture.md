# Current architecture

MinecraftQuizGuesser runs on the Debian mini PC at `/home/brian/MinecraftQuizGuesser`.

## Single production flow

1. `data/quiz-copy-episodes.json` is the only editable episode bank.
2. Every episode has exactly three verified clues and all voice, icon, reveal, timeline, audio, and thumbnail fields.
3. `scripts/produce_quiz_copy.py` validates the episode, prepares audio, writes generated configs, renders `QuizCapasCopy`, and renders all thumbnails.
4. Videos go to `out/episodes`; vertical thumbnails go to `out/thumbnails/<type>/<design-variant>`.
5. The dashboard handles review, queueing, publication, backups, and GPT exports; in staging, analytics is owned by `analytics-api` and health/error monitoring by `monitor`.

## Services and state

- Private dashboard: `https://what-am-i-craft.tail6cc348.ts.net:8443/`
- Public video base: `https://what-am-i-craft.tail6cc348.ts.net/`
- Docker services: `dashboard`, `bot`, `publisher-worker`, `media`; `clues-api`, `analytics-api`, and `monitor` are currently staging-only. The clues API bootstraps `data/clues.sqlite3` once from the legacy clue JSON files, then uses SQLite as its source of truth.
- Operational state: `out/app-state.sqlite3`.
- Target history: `data/used-targets.json`.
- Videos are stored on the USB disk mounted at `/app/out/episodes`.
