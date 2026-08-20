# Entorno de desarrollo aislado

La API importa los JSON existentes solo al crear una base nueva en `data/clues.sqlite3`; después SQLite es la fuente única y la operación normal no vuelve a leer ni modificar esos JSON.

Este compose usa el proyecto `minecraftquizguesser-dev`, los puertos `8788` y `8081`, y volúmenes propios.

Incluye la API local de pistas en `8790`. Sus endpoints principales son `GET /api/clues?status=unused|used|all`, `GET /api/clues/<target_id>`, `POST /api/clues` para cargar un paquete validado y `PATCH /api/clues/<target_id>` para registrar su uso. Se puede revertir una reserva creada por la API con `status=unused`; los usos provenientes del banco o de videos quedan protegidos. El estado utilizado se guarda en SQLite.

Por seguridad, `bot` y `publisher-worker` están detrás del perfil `integrations` y no tienen credenciales. El stack productivo no comparte contenedores, red, puertos, datos ni secretos con este entorno.

`analytics-api` escucha en `8791` y expone `GET /api/analytics`, `GET /api/analytics/sync`, `POST /api/analytics/sync`, `GET /api/analytics/export.json` y `GET /api/analytics/export.md`. El dashboard consume este servicio por HTTP cuando `ANALYTICS_API_URL` está configurada.

`monitor` escucha en `8792`, comprueba dashboard, pistas, analytics y media cada 60 segundos, guarda eventos sanitizados en `out/monitor/events.jsonl` y expone `GET /health`, `GET /api/monitor/status`, `POST /api/monitor/check` y `GET/POST /api/monitor/events`. El dashboard lo proxifica cuando `MONITOR_API_URL` está configurada.
