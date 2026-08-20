# Entorno de desarrollo aislado

Este compose usa el proyecto `minecraftquizguesser-dev`, los puertos `8788` y `8081`, y volúmenes propios.

Incluye la API local de pistas en `8790`. Sus endpoints principales son `GET /api/clues?status=unused|used|all`, `GET /api/clues/<target_id>`, `POST /api/clues` para cargar un paquete validado y `PATCH /api/clues/<target_id>` con `{\"status\":\"used\",\"episodeId\":\"mc-01\",\"videoFile\":\"mc-01-target.mp4\"}` para registrar su uso. Se puede revertir una reserva creada por la API con `status=unused`; los usos provenientes del banco o de videos quedan protegidos. El estado utilizado se calcula desde `data/used-targets.json`; no se mantiene una copia paralela.

Por seguridad, `bot` y `publisher-worker` están detrás del perfil `integrations` y no tienen credenciales. El stack productivo no comparte contenedores, red, puertos, datos ni secretos con este entorno.

`analytics-api` escucha en `8791` y expone `GET /api/analytics`, `GET /api/analytics/sync`, `POST /api/analytics/sync`, `GET /api/analytics/export.json` y `GET /api/analytics/export.md`. El dashboard consume este servicio por HTTP cuando `ANALYTICS_API_URL` está configurada.

`monitor` escucha en `8792`, comprueba dashboard, pistas, analytics y media cada 60 segundos, guarda eventos sanitizados en `out/monitor/events.jsonl` y expone `GET /health`, `GET /api/monitor/status`, `POST /api/monitor/check` y `GET/POST /api/monitor/events`. El dashboard lo proxifica cuando `MONITOR_API_URL` está configurada.

`backup-rollback` escucha en `8793`, crea un backup diario de `data/` y del estado JSON/SQLite relevante de `out/`, conserva los últimos 14 y expone `GET /health` y `GET /api/backups`. Las operaciones de creación manual y rollback requieren `X-Backup-Token`; el rollback además exige `{"confirm":true}`. Antes de restaurar crea automáticamente un backup preventivo. Configurá `BACKUP_ADMIN_TOKEN` solo en el entorno aislado: no se incluye ningún token en el repositorio.
