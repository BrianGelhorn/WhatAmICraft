---
name: minecraft-clip-director
description: Use when creating or adjusting Minecraft scenes, guiones, rodaje, Replay Mod clips or studio datapack scenes. Uses short recipes, structured briefs and local validation to reduce repeated context, including with smaller models.
---

# Minecraft Clip Director

Responde en espanol. Una escena por defecto, una camara, una toma. Respeta cantidades explicitas. No cambies modelo/proveedor/permisos. No prometas igual calidad ni porcentajes de ahorro: las recetas reducen decisiones, no sustituyen ensayo.

## Elegir Ruta

- **Explicar Gxx:** leer solo su ficha en `docs/minecraft-clip-shooting-guide.md`. Responder brevemente; no crear archivos ni cargar recetas/validador.
- **Crear o ajustar guion:** leer `resources/recipes.md` y `resources/scene.example.json` junto a esta skill. Elegir la receta mas cercana. Si ya existe la funcion narrativa, reutilizar antes de proponer nuevo ID.
- **Implementar en servidor:** ademas leer `resources/server.md`. No confundir un guion validado con una funcion instalada.

## Reglas Fijas

- Mismo MP4 para tres categorias de episodios, sin cambiar props por respuesta. Explicar usos narrativos y exclusiones por spoiler. No demuestra propiedades de esos targets.
- Prohibidas como idea central: balde recogiendo agua, esponja absorbiendo, cobre raspado, recetas exactas o mecanicas exclusivas de un mob/item.
- Java 1.21.11, vanilla, vertical 1080x1920, 30 fps, FOV constante. Sin texto/HUD/musica horneados; respuesta independiente en Remotion.
- Accion visible antes de f45. Tres momentos: evento, consecuencia, final limpio. 4/5/6 s por defecto. No coreografiar pulsaciones humanas al frame.
- Replay Mod es del cliente. Distinguir construccion automatica, actuacion manual, camara posterior y exportacion. No inventar APIs ni caminar mediante teleports.
- Camara fija por defecto. No prometer `loop`, `background` ni aprobacion visual sin probarlos. Estado nuevo: `pendiente_de_ensayo`.

## Producir Sin Repetir Contexto

1. Extraer objetivo, ID y restricciones. Preguntar solo si falta una decision que afecte mundo, mecanica o alcance. Usar defaults para lo demas.
2. Leer una receta y solo la ficha/SET relacionado. Usar Grep por encabezado y Read por rango. No leer banco de episodios, PNG, biblioteca completa ni codigo del servidor para escribir un guion.
3. Crear un brief JSON con el ejemplo como contrato. Guardar en `docs/scenes/<ID>.json` si pidio crear, o actualizar solo el solicitado. No sobrescribir otro concepto con ese ID.
4. Ejecutar `scripts/validate_scene.py <archivo>` de esta skill. Corregir errores estructurales localmente.
5. Revisar: tres usos creibles; causa visible; foco unico en telefono; recorrido sin colisiones; automatizacion honesta; reset repetible. Si falla, simplificar. La validacion numerica no evalua estos criterios.
6. Entregar archivo, resumen de accion, tarea manual y ensayo pendiente. No pegar JSON y ficha completos a la vez. No regenerar documentos ajenos al cambio.

Presupuesto orientativo: brief de una escena <=600 palabras. Cargar recursos una sola vez por conversacion. Investigar en web solo mecanicas/versiones inciertas. Tras dos intentos fallidos, informar bloqueo o pedir revision, no encadenar delegaciones.

Uso y pruebas sin Python local: `resources/usage.md`. Cargarlo solo para instalacion o ayuda, no para cada escena.
