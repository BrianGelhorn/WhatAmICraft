# Flujo pre-main

`pre-main` es la rama de integración para cambios normales. Se prueba en una
instancia aislada en esta notebook y recién después se promueve a `main`.

## Entorno local

El stack usa `staging/runtime/pre-main/`, no `data/`, `out/` ni `backups/` de
producción. Escucha solamente en localhost:

- Dashboard: http://127.0.0.1:8878
- Media: http://127.0.0.1:8088

No inicia Telegram, publisher-worker ni ningún proveedor externo. Las pruebas
de publicación siguen usando fakes en CI.

Desde PowerShell:

```powershell
git switch pre-main
.\scripts\pre_main.ps1 -Reset
.\scripts\pre_main.ps1
.\scripts\pre_main.ps1 -Logs
.\scripts\pre_main.ps1 -Down
```

Para probar el productor manualmente, sin dejarlo corriendo como servicio:

```powershell
docker compose -p whatamicraft-pre-main --project-directory . -f compose.pre-main.yaml run --rm producer --episode mc-03 --dry-run
```

## Flujo de ramas

1. Crear la rama de trabajo desde `pre-main`.
2. Abrir el PR normal hacia `pre-main`.
3. Mergear a `pre-main` y ejecutar la prueba local del stack.
4. Cuando el comportamiento esté validado, abrir un PR separado de `pre-main` hacia `main`.
5. Sólo `main` se considera candidato para producción en el mini PC.

Para un fix hay que decidir explícitamente el destino: por defecto va a
`pre-main`; sólo un incidente urgente de producción puede justificar un PR
directo a `main`. En ese caso, luego debe sincronizarse `pre-main` con `main`.

Cuando la rama exista en GitHub, proteger `pre-main` y `main` con los checks
requeridos de CI y exigir PR para ambos destinos.
