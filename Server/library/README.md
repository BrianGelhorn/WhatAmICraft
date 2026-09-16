# Biblioteca de assets

- `bundles/`: ZIP originales con schematics y, a veces, mundos de muestra. No se cargan directamente.
- `worlds/`: mundos de referencia. Nunca se montan sobre `Server/data/world`.
- `datapacks/`: datapacks de referencia; no se cargan porque sus formatos no coinciden con Java 1.21.11 / pack 81.
- `schematics/legacy/`: `.schematic` sueltos todavía incompatibles con la paleta segura.
- `schematics/modern/`: `.schem` Sponge, formato no soportado por el importador actual.
- `duplicates/`: copias verificadas por SHA-256; se conservan pero no entran al catálogo.
- `../uploads/`: única colección activa. Solo los nombres `*-compatible.zip` entran al build; cualquier ZIP crudo copiado manualmente se ignora.

Regenerar las copias activas:

```powershell
docker exec server-dashboard-1 python /studio/curate_assets.py
```

La curación no sustituye bloques desconocidos: omite cada schematic incompatible y cualquiera que supere 48 bloques en un eje o 10.000 bloques colocados. Los originales permanecen intactos.

Esta biblioteca y `Server/uploads` contienen binarios locales ignorados por Git. Un clon nuevo no puede regenerarlos hasta volver a copiar los bundles originales a `library/bundles`; `curate_assets.py` falla con la lista de fuentes ausentes en vez de producir una colección parcial. El dashboard conserva cada carga nueva en `library/bundles` y solo activa su copia curada en `uploads`.

Política de uso: f02 admite roca y vegetación muerta; f03 solo roca pequeña alrededor de la boca; f04 árboles de granja (roble, abedul, cerezo o sauce) y arbustos vivos. La selección es determinista por escena y semilla, limitada a tres assets y fuera de las zonas de acción.
