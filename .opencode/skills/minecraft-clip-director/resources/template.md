# Asignación posterior y timing

Una familia no lleva episodio, duración, beats ni timing. Solo al asignarla, leer el episodio y calcular cada intervalo real: `start = contentStartFrame + (index - 1) * hintDurationInFrames`; el fin es exclusivo. No asumir 155 frames.

El contrato actual no instala vídeo: tarjeta central opaca y fondo `CanvasImage`; cambiar un MP4 por background no añade soporte. Representación UI Remotion, captura, preview con overlays y render son autorizaciones separadas.

Para una asignación, `clue_index` elige una pista y declarar `M_i` (matches por pista) y `V` (targets compatibles con ese clip). El validador exige solo `M_clue_index ⊆ V` y además que `M_1` sea subconjunto estricto del universo: la pista 1 siempre se lee y debe descartar al menos un candidato declarado. aún comprueba >=2 por cada `M_i`, reducción estricta al acumular las pistas 2 y 3, >=2 tras las dos primeras y un único target tras las tres. Esto comprueba conjuntos declarados, no interpreta el texto ni certifica semántica.
