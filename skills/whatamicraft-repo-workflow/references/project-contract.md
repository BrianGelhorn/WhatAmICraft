# WhatAmICraft project contract

Use this as the stable intent extracted from production work. Verify names and paths against the current repository before changing them; never invent missing state.

## Architecture and ownership

- Production runs only on the mini PC from `main`; local Windows is for development/tests and an explicitly requested single render.
- Keep services independent: dashboard, producer/generation, publisher-worker, Telegram bot, media, clues API, analytics API, monitoring/errors, and backup/rollback.
- Communicate through documented APIs or durable queues. Do not make the dashboard read service-owned JSON when an API/database owns the data.
- Keep generation and publishing on independent workers/CPU lanes. One may run while the other is busy.
- Isolate failures per task: persist a redacted log, notify Telegram, leave state consistent, and continue with the next safe task.

## Content source of truth

- The newest definitive quiz template is the only active generation/repost format. Treat old templates, videos, clues, and tracks as archive: visible only when explicitly requested and never eligible for automation.
- Deduplicate targets and clue content globally across every historical/current template and video. A template change never resets usage.
- Use the clues API/database as the clue catalog and used/unused authority. Record usage with the episode/video identity; support safe reversal of reservations, not published history.
- Generate voice from the exact finalized clue/reveal strings in the same immutable episode payload used by Remotion. Never select text and voice from different banks.
- Keep Minecraft version migration forward-only: preserve each existing episode's declared version and use Java `26.1` for every new target, clue, episode, and generation input.
- Never mass-rewrite or regenerate historical episodes solely to update their Minecraft version.
- Classify by visible quiz meaning, not a generic asset class: crossbow=`weapon`, lectern=`block`, edible targets=`food`; use `item` only as fallback.
- Keep platform title and description/caption separate for YouTube, Instagram, TikTok, and Facebook.

## Thumbnails and media

- Support vertical thumbnails only. Do not create, route, test, or retain horizontal/square variants.
- Store thumbnail variants by visible kind (`weapon`, `block`, `food`, `item`, etc.). Require the correct kind icon and black unrevealed silhouette.
- Reuse the same approved vertical thumbnail for Instagram and YouTube.
- Thumbnail CI validates existing assets and routing; it does not rerender them.
- Never commit or deploy generated videos, audio, images, thumbnails, fonts, `out/`, backups, or runtime databases through Git.

## Dashboard and automation

- Separate: videos to generate; generated/awaiting review or queued; published/archive. Published items must not appear as pending.
- Expose cancel, retry, revert/unqueue, clear error, clear pending-clue state, inspect clues/voices, and manual generate/publish controls where state allows it.
- Never mark a video published until the provider confirms it. Reconcile stale or corrupt states after interruption.
- Keep automatic generation buffer defaults at low-water `5` and target `8` unless configuration explicitly changes them.
- Telegram must report production state, approval lists/videos, publications, task progress, and redacted errors with actionable controls.
- Analytics must ingest the latest available records from every enabled platform and make sync freshness/errors visible.

## Production state

- Preserve `/etc/whatamicraft/production.env`, root-owned launcher, `data/`, `out/`, backups, media, and service databases across rebuilds.
- Take/verify a backup before production migration and keep rollback operational.
- Network or dependency recovery must not require rebooting the mini PC: watchdogs retry, recover connectivity/services, and report failure.
- Do not restore the deleted Alexa project or a separate Windows production dashboard.

## Verified production lessons

- Production is Debian mini PC only. Windows is a development/test workspace and must never be treated as the production host or receive production-only fixes.
- A successful merge to `main` deploys asynchronously through the self-hosted runner. Confirm the deploy workflow and post-deploy health before claiming production is updated; do not manually copy the checkout.
- The dedicated video volume uses a systemd automount. The deploy path must activate/wait for `/srv/minecraft-videos/episodes` before Docker creates bind mounts, or existing containers can return `Input/output error` while the host remains healthy.
- Recreating project containers is an allowed recovery only after explicit operator authorization and must preserve volumes, runtime data, media, and secrets.

