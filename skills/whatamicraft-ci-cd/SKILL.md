---
name: whatamicraft-ci-cd
description: Design, extend, and diagnose WhatAmICraft CI/CD with real behavior checks for Python, Remotion, Docker services, APIs, generation, media, Telegram, analytics, publishing, staging, and self-hosted mini-PC deployment. Use for workflows, required checks, runner failures, test coverage, and release verification.
---

# WhatAmICraft CI/CD

Pair with `whatamicraft-repo-workflow`; add `whatamicraft-real-fix` when a check exposes a defect.

- Read [references/test-matrix.md](references/test-matrix.md) when adding or auditing coverage.
- Read [references/self-hosted-runner.md](references/self-hosted-runner.md) for runner, Docker, staging, required-check, or deployment failures.

## Safety

- Never contact production, real social accounts, Telegram, or production databases from ordinary CI.
- Never print or upload secrets, auth headers, provider responses, private URLs, personal data, state databases, `.env`, backups, or media.
- Use provider/Telegram fakes, dry-run publishing, deterministic fixtures, fresh runtime directories, unique compose projects, and cleanup.
- Keep required checks blocking. Never hide a failure with skips, weakened assertions, fake success, or `continue-on-error`.

## Real-test gate

A required behavior test must:

1. create isolated meaningful input;
2. execute the real handler/worker/service boundary;
3. assert an observable response, state transition, persisted artifact, or captured side effect;
4. exercise at least one invalid/unavailable/retry path and assert safe state;
5. prove isolation/cleanup and contain an assertion that fails if core behavior is removed.

Import, compile, lint, schema validation, compose config, readiness, or bare `200` are preflight only.

## Layer by cost

1. Locked/static: `npm ci`, lint, typecheck/build, Python compile, schemas/contracts, secret scan.
2. Pure behavior: queues, status transitions, cancellation, retries, idempotency, scheduling, dedup, template/type, clue/voice identity, text, thumbnail routing.
3. Service integration: actual local HTTP/process/container behavior with isolated state.
4. Cross-service: real requests and resulting durable state/artifact.
5. Bounded generation/media: dry-run or minimal representative artifact; inspect existence/decoding/orientation/discovery and failed cleanup.
6. Provider contracts: local fakes for success, transient/permanent failure, malformed response, retry, and idempotency.

Do not render thumbnails in CI; validate existing vertical assets and routing. Keep full renders and real-provider smoke tests manual/scheduled when cost or side effects demand it.

## Workflow contract

- Run protected checks on every PR/main event that requires them. A required check must always report; never require a context from a skipped workflow.
- Use exact self-hosted labels `[self-hosted, linux, x64]` unless the runner is proven to carry another label.
- Checkout submodules, use locked dependencies, fail closed, emit useful diagnostics on failure, and always tear down isolated services.
- Use `RUNNER_TEMP` for runtime/fixtures; never let containers write into the checkout.
- Preserve production data/secrets/media. Deployment from successful `main` uses the approved launcher, backup/rollback, and post-deploy health/version checks.

## Completion

Report commit, jobs/check names, real behaviors proven, failure paths, isolation, side effects avoided, unverified manual boundaries, and deployment result. Green static checks alone are not full-stack evidence.

