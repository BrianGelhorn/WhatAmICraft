# Releases de plantillas

La plantilla no se cambia directamente en producción. Cada render queda asociado a una release y conserva sus propios props, hashes y manifest junto al video.

## Flujo de una plantilla nueva

1. Trabajar en una rama sobre `src/`, `templates/quiz-copy/` y los assets necesarios.
2. Ejecutar los checks de CI y revisar un render corto representativo.
3. Mergear a `main`; el deploy guarda el commit como `.release-version`. Si no cambiaron archivos de plantilla, promueve automáticamente la plantilla activa; los cambios normales no pausan la generación. Si cambió la plantilla, espera el canary.
4. En el mini PC revisar la release instalada:

   ```bash
   python3 scripts/template_release.py --status
   ```

5. Generar uno o dos episodios canary y revisar video, audio y miniatura.
6. Activar la release solo después del canary:

   ```bash
   python3 scripts/template_release.py --activate <commit>
   ```

Mientras la release instalada no esté activa, el generador automático queda pausado. La cola puede terminar episodios anteriores que tengan un manifest válido; los nuevos episodios no se mezclan con la release anterior.

## Primera migración

Los videos creados antes de este mecanismo no tienen procedencia verificable. Después de un backup, se pueden registrar explícitamente como legado:

```bash
python3 scripts/template_release.py --migrate-legacy
```

Esos manifests solo validan que el video y la miniatura no hayan cambiado; no se presentan como renders de la release nueva.

## Invariantes

- Remotion recibe props por episodio; nunca depende de un JSON global sobrescrito durante el render.
- Un manifest se escribe únicamente después de completar video y miniatura.
- El publisher rechaza videos con manifest ausente, hash cambiado, props distintos o miniatura inválida.
- `out/.active-template-version` se conserva durante el deploy para permitir rollback/promoción controlados.
