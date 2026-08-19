# Entorno de desarrollo aislado

Este compose usa el proyecto `minecraftquizguesser-dev`, los puertos `8788` y `8081`, y volúmenes propios.

Incluye la API local de pistas en `8790`. Sus endpoints principales son `GET /api/clues?status=unused|used|all`, `GET /api/clues/<target_id>` y `POST /api/clues` para cargar un paquete validado. El estado utilizado se calcula desde `data/used-targets.json`; no se mantiene una copia paralela.

Por seguridad, `bot` y `publisher-worker` están detrás del perfil `integrations` y no tienen credenciales. El stack productivo no comparte contenedores, red, puertos, datos ni secretos con este entorno.
