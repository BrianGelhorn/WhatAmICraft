---
name: whatamicraft-repo-workflow
description: "Change the WhatAmICraft repository safely: select the correct branch, preserve product and production contracts, validate, create focused commits, manage PRs, and require explicit confirmation before every push. Use for any WhatAmICraft code, dashboard, generation, media, publishing, Telegram, analytics, thumbnail, service, mini-PC, documentation, or CI/CD task."
---

# WhatAmICraft repository workflow

Work in `C:\Users\Brian\Documents\MinecraftQuizGuesser`; remote: `BrianGelhorn/WhatAmICraft`.

For product behavior, data, services, media, generation, publishing, analytics, thumbnails, or production, read [references/project-contract.md](references/project-contract.md) before editing. Skip it only for isolated Git or documentation mechanics.

## Hard boundaries

- Treat the mini PC as the only production host. Treat Windows/local as development and explicit one-off rendering only.
- Treat `pre-main` as the notebook integration branch and `main` as the production promotion branch.
- Never touch production, publish, restart services, merge `main`, or alter remote settings unless requested.
- Never read or stage secrets, `.env*`, `.secrets/`, databases, backups, runtime state, dependencies, or generated/media files.
- Never force-push, rewrite history, discard user changes, or mix unrelated work.
- Keep `main` releasable; use a work branch.

## Pre-main integration flow

- Ordinary feature PRs target `pre-main`, never `main` directly.
- Start the notebook stack only through `scripts/pre_main.ps1`; it uses the isolated `staging/runtime/pre-main/` tree and localhost ports, with integrations disabled.
- After merging to `pre-main`, run the local smoke test and relevant CI checks before opening a separate promotion PR from `pre-main` to `main`.
- For a reported fix, ask whether it should target `pre-main` first or bypass it. Bypass is reserved for an explicitly authorized urgent production fix; sync the result back to `pre-main` afterward.
- Before any push or PR claim, verify the branch ancestry and current GitHub PR state. Do not reuse a merged or closed PR branch.

## Branch routing

Use the narrowest existing branch; create it from updated `main` when absent.

| Area | Branch |
| --- | --- |
| dashboard | `feature/dashboard` |
| generation, Remotion, voices | `feature/generation` |
| media | `feature/media` |
| publishing | `feature/publishing` |
| Telegram | `feature/telegram-bot` |
| analytics | `feature/analytics` |
| vertical thumbnails | `feature/thumbnails` |
| services/APIs/compose | `feature/service-separation` |
| mini PC/network/Docker | `chore/mini-pc-infra` |
| tests/Actions/CD | `chore/ci-cd` |
| docs | `docs/project` |
| urgent authorized production fix | `hotfix/production` |
| cross-feature integration | `develop` |
| ordinary integration and notebook validation | `pre-main` |

Continue the current focused branch when the task is a direct follow-up. Stop before mixing unrelated changes.

## Execution algorithm

1. Inspect `git status --short --branch`, remote relation, relevant callers, data flow, and existing tests.
2. Preserve user changes. Make the smallest complete change at the shared owner of the behavior.
3. Add one meaningful regression for changed behavior. Run focused checks, then relevant compile/lint/build/integration checks.
4. Review the diff for secrets, media/state, weakened tests, hidden failures, and accidental production changes.
5. Create one focused local commit. Report branch, hash, subject, behavior changed, and checks.
6. Before pushing or claiming a PR is updated, fetch the intended base (`pre-main` for ordinary work, `main` for a promotion or explicitly authorized urgent fix) and query GitHub for the current PR associated with the branch. Compare the candidate commit with the base using ancestry or the PR head SHA.
   - If the PR is open, update that PR only when its head is this branch.
   - If the PR is merged or closed, never reuse it for follow-up commits: create a new branch from updated `origin/main`, carry only commits not already in `main`, push that branch, and open a new PR.
   - If the candidate commit is already in `main`, do not create or claim another PR.
7. Ask before every push. Push only the confirmed branch after the PR-state check.
8. If rejected as non-fast-forward: fetch, rebase onto the remote branch, rerun focused checks, then push normally. Never force-push.
9. Open/merge a PR only when requested and required checks pass. Resolve conflicts without discarding either side silently.

## Production release

`main` is the release source. A successful merge to `main` is expected to trigger the self-hosted mini-PC deployment; do not manually copy the checkout. `pre-main` deploys only to the isolated Windows notebook environment through `scripts/pre_main.ps1`; it must never use production data/secrets or contact real providers. Verify required checks, backup/rollback readiness, deployment conclusion, service health, and version after a `main` merge.

Production secrets stay at `/etc/whatamicraft/production.env`. Never read them. Start/rebuild only through the root-owned no-argument launcher:

```bash
sudo /usr/local/sbin/whatamicraft-up
```

If it is missing or asks for unsupported access, stop and ask the operator. Never broaden sudo permissions.

## Report

End with branch, intended base, commit(s), checks, push/PR status, deployment status, and any unverified boundary.

