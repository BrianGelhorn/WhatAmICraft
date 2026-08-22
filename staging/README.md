# Entorno de staging aislado

Este compose usa el proyecto `minecraftquizguesser-dev`, los puertos `8788` y `8081`, y el runtime persistente `staging/runtime/` por defecto. Podés definir `STAGING_RUNTIME_DIR` para usar otra carpeta aislada; CI lo ubica debajo de `RUNNER_TEMP` para que Docker no deje archivos con permisos de `root` dentro del checkout. Nunca monta `data/`, `out/` ni `backups/` del proyecto principal.

Preparación y arranque local:

```powershell
$env:PYTHONPATH = "scripts"
python scripts/ci/prepare_staging.py
docker compose -f staging/compose.yaml up -d --build dashboard clues-api analytics-api backup-rollback monitor media
```

Si algún puerto está ocupado, podés cambiar solo los puertos externos con `STAGING_DASHBOARD_PORT`, `STAGING_CLUES_PORT`, `STAGING_ANALYTICS_PORT`, `STAGING_BACKUP_PORT`, `STAGING_MONITOR_PORT` y `STAGING_MEDIA_PORT`; los puertos internos no cambian.

Para descartar solamente el estado de staging y recrearlo desde cero, agregá `--reset` al primer comando. La verificación integral usa el mismo runtime:

```powershell
python scripts/ci/service_smoke.py --dashboard http://127.0.0.1:8788 --media http://127.0.0.1:8081 --analytics http://127.0.0.1:8791 --monitor http://127.0.0.1:8792 --backup http://127.0.0.1:8793 --backup-token <token-local> --runtime-root staging/runtime --fixture mc-ci-test.mp4
```

Incluye la API local de pistas en `8790`. Sus endpoints principales son `GET /api/clues?status=unused|used|all`, `GET /api/clues/<target_id>`, `POST /api/clues` para cargar un paquete validado y `PATCH /api/clues/<target_id>` con `{\"status\":\"used\",\"episodeId\":\"mc-01\",\"videoFile\":\"mc-01-target.mp4\"}` para registrar su uso. Se puede revertir una reserva creada por la API con `status=unused`; los usos provenientes del banco o de videos quedan protegidos. El estado utilizado se calcula desde `data/used-targets.json`; no se mantiene una copia paralela.

Por seguridad, `bot` y `publisher-worker` están detrás del perfil `integrations` y no tienen credenciales. El stack productivo no comparte contenedores, red, puertos, datos ni secretos con este entorno.

`analytics-api` escucha en `8791` y expone `GET /api/analytics`, `GET /api/analytics/sync`, `POST /api/analytics/sync`, `GET /api/analytics/export.json` y `GET /api/analytics/export.md`. El dashboard consume este servicio por HTTP cuando `ANALYTICS_API_URL` está configurada.

`monitor` escucha en `8792`, comprueba dashboard, pistas, analytics y media cada 60 segundos, guarda eventos sanitizados en `out/monitor/events.jsonl` y expone `GET /health`, `GET /api/monitor/status`, `POST /api/monitor/check` y `GET/POST /api/monitor/events`. El dashboard lo proxifica cuando `MONITOR_API_URL` está configurada.

`backup-rollback` escucha en `8793`, crea un backup diario de `data/` y del estado JSON/SQLite relevante de `out/`, conserva los últimos 14 y expone `GET /health` y `GET /api/backups`. Las operaciones de creación manual y rollback requieren `X-Backup-Token`; el rollback además exige `{"confirm":true}`. Antes de restaurar crea automáticamente un backup preventivo. Configurá `BACKUP_ADMIN_TOKEN` solo en el entorno aislado: no se incluye ningún token en el repositorio.
