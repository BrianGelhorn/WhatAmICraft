# Verified incident patterns

Reconfirm the current environment before applying a row.

| Symptom | Root cause to verify | Correct repair and proof |
| --- | --- | --- |
| `FileNotFoundError` for output/fixture | path owner never initialized it | create/validate in the real owner; run from empty state and assert the artifact/state |
| Docker socket permission denied | self-hosted runner user lacks Docker group/session | add the runner account to `docker`, restart the runner service, then run a real compose operation |
| checkout `EACCES` on staging files | root containers wrote into the Git checkout | mount staging runtime from `RUNNER_TEMP` via `STAGING_RUNTIME_DIR`; keep reset path allowlisted; repair old ownership once |
| Python 3.12 unavailable on Debian 13 runner | `setup-python` cache lacks that build while system Python is suitable | use the repository composite runner-Python action; assert supported minimum version and execute tests |
| Chrome/Chromium not found | dashboard CI searched only global binaries | run `npx remotion browser ensure`; let `openBrowser(..., browserExecutable: null)` use the locked Headless Shell; execute the real UI test |
| ffmpeg missing while creating media fixture | undeclared runtime dependency | install/check ffmpeg in the owning job/image before fixture creation; verify generated audio decodes |
| nginx traversal returns 400 instead of expected 404 | proxy rejects traversal earlier than application | assert the security contract (request blocked/non-success and no bytes leaked), not an arbitrary equivalent 4xx |
| ESLint/TypeScript crashes during load | incompatible transitive toolchain or stale lockfile | pin a compatible declared set, regenerate lockfile, `npm ci`, load toolchain, then run real lint/typecheck |
| music test rejects an original or selects another track | fixture bypasses library registration/current selection rules | seed through public library behavior; assert valid timestamps/URL guards and observable selection constraints |
| task stuck at 0%, corrupt, or falsely complete | durable job state and process lifecycle diverged | reconcile live process vs state, expose cancel/clear/retry, preserve log, and prove next task continues |
| scheduled publication skipped | scheduler state, clock, guard, queue, or worker unavailable | trace due calculation through provider result; preserve due item and retry idempotently |
| publisher worker is up but repeatedly logs `skip: generation already in progress` | a render child died while durable `generation` state remained `running`; automatic jobs had no `JOB_OWNER`, so stale-state reconciliation skipped them | assign explicit `JOB_OWNER` values (`publisher-worker` and `dashboard`), reconcile legacy ownerless jobs by source without crossing lanes, and prove automatic recovery while manual work remains untouched |
| dashboard says it cannot update and logs `OSError: [Errno 5] Input/output error` for `/app/out/episodes/*.mp4` | Docker containers were created before the Debian `x-systemd.automount` volume `/srv/minecraft-videos` was active; the host and fresh containers could read the files, but existing bind mounts were stale | activate/wait for `/srv/minecraft-videos/episodes` before invoking the production launcher, then recreate affected containers; verify dashboard `/health`, `/api/state`, and reads from dashboard/worker/media |
| mini PC needs reboot after Wi-Fi loss | recovery handles boot but not reconnect | test watchdog DNS/network/service recovery after link restoration with bounded retries |
| Git push rejected non-fast-forward | remote branch advanced | fetch, rebase, rerun focused checks, push normally; never force |

Do not encode one machine's path, version, status code, or selected fixture as a universal assertion unless it is the documented contract.

