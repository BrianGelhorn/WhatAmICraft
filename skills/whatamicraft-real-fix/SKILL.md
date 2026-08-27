---
name: whatamicraft-real-fix
description: Diagnose and repair WhatAmICraft failures at their root cause, including broken behavior, CI, Docker, paths, dependencies, state, queues, networking, and production regressions. Use whenever the user reports an error or failed run; never accept a test-only bypass or hidden failure as a fix.
---

# WhatAmICraft real-fix protocol

Pair with `whatamicraft-repo-workflow`. For a matching environment/CI symptom, read [references/incidents.md](references/incidents.md); treat it as evidence to verify, not a blind recipe.

## Validity rule

A fix is valid only when it repairs the real owner of the behavior and leaves a regression that fails for the original defect.

Reject any proposal that:

- skips, weakens, deletes, quarantines, or marks a required test `continue-on-error`;
- ignores a required path/asset/dependency or creates it only in the test;
- swallows errors, fakes success, silently resets state, or changes assertions to broken behavior;
- substitutes a mock for the real boundary being tested;
- deletes features/data or hides legacy/current mixing to obtain green CI.

## Algorithm

1. Preserve the exact evidence: workflow/job, commit, command, complete error, environment, path, state, and timestamps.
2. Reproduce the same path from clean isolated state when safe. If not reproducible, gather more evidence before editing.
3. Trace end-to-end and inspect every caller: input/source of truth → shared owner → state/filesystem → process/service/API → cleanup/recovery.
4. State one-sentence root cause. Distinguish the triggering condition from the defect that allowed it.
5. Fix once at the owning boundary:
   - path: owner creates/validates it;
   - dependency: declare/install compatible locked runtime;
   - config: validate early with actionable error;
   - state: migrate/reconcile atomically, never fabricate completion;
   - task failure: log redacted detail, release resources, continue the next independent task;
   - service/network: add bounded retry/recovery and health reporting.
6. Add one regression exercising the real path plus its failure state. Avoid implementation-only assertions when observable behavior is the contract.
7. Run focused, surrounding, and clean-state/CI-equivalent checks. Recheck portability, permissions, secrets, cleanup, and sibling callers.
8. Commit through the repo workflow; push only after confirmation.

## State invariants

- A failed/cancelled generation cannot appear generated, approved, queued, or published.
- Provider failure cannot mark publication complete; retries must be idempotent.
- One failed task cannot block unrelated queued work.
- Generation and publishing cannot cancel, corrupt, or starve each other.
- Logs/Telegram errors must be useful and redacted.
- Recovery after Wi-Fi/service restart must not require a mini-PC reboot.

## Stop

Stop and ask when the correct contract is ambiguous, the fix would destroy/overwrite user data, credentials or production access are required, evidence is insufficient, or only a bypass remains.

## Completion evidence

Report root cause, real boundary changed, regression and why it failed before, checks run, production status, and remaining risk. Never call a test-only change a fix.

