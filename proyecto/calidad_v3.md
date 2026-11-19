# Control de calidad: versión 3 (voz Supertonic 3, hombre)

Revisado el 19-11-2026. Herramientas: `produccion/qc_v3.py` (mediciones, fotogramas y Whisper por escena), `produccion/asr_v3.py` (Whisper-small int8 vía sherpa-onnx 1.12.40, normalización y WER), `produccion/voz_v3.py` (voz). Datos en bruto: `videos/qc_v3/qc_v3.json`. Fotogramas: `videos/qc_v3/video{1,2,3}/` y hojas de contacto `videos/qc_v3/video{N}_hoja{1-3}.jpg`.

## Resumen

| Video | Duración | Ritmo (mientras habla / con pausas) | Sonoridad total · pico real | Música bajo la voz | WER Whisper | Resultado |
|---|---|---|---|---|---|---|
| `dia1_01_gta6_hora_por_pais_v3.mp4` | 50,2 s | 171 / 159 ppm | −14,0 LUFS · −1,5 dBTP | −32,7 LUFS (18,7 dB debajo) | 3,8 % | **PASA** |
| `dia1_02_gta6_resenas_v3.mp4` | 50,9 s | 170 / 159 ppm | −13,9 LUFS · −1,6 dBTP | −32,8 LUFS (18,8 dB debajo) | 1,4 % | **PASA** |
| `dia1_03_gta6_espacio_y_consolas_v3.mp4` | 50,4 s | 173 / 162 ppm | −14,2 LUFS · −1,5 dBTP | −33,0 LUFS (19,0 dB debajo) | 4,3 % | **PASA** |

**Criterios para PASA:** dura 59 s o menos; vídeo H.264 1080x1920 a 30 fps; audio AAC estéreo; voz a −14 LUFS (±1); pico real ≤ −1 dBTP; música entre 15 y 20 dB por debajo de la voz; ritmo de 165 a 175 palabras/min mientras habla; ninguna pausa de más de 1 s dentro de la narración; WER ≤ 10 % sin palabras clave mal dichas; texto legible y con tildes, nada cortado; cada escena se oye dentro de su propio tramo de tiempo.

**Sin comprobar (necesita oído humano):** si la voz suena natural, si la entonación es buena y si las pausas se sienten naturales y no robóticas. No puedo escuchar audio. Solo medí duración, pausas, ritmo y lo que entiende Whisper. Antes de subir, Mateo debería escuchar al menos los primeros 10 s de cada video. Tampoco pude comprobar la nota de Metacritic en la propia web (dominio bloqueado aquí); se verificó con varias fuentes de prensa del 18-19-11 (ver fuentes.md, sección 6).

## Cómo se hizo la voz y el ritmo

- Supertonic 3 int8, voz hombre sid 7, 8 pasos, `silence_scale` 0,2. Las pausas internas de más de 340 ms se recortan a 280 ms y los silencios de los extremos se quitan. Entre frases quedan unos 0,4 s de respiro: la escena dura 0,15 s + la frase + 0,25 s.
- **Barrido de velocidad** con el guion real del video 2 (palabras escritas del guion por minuto de voz): 0,88 → 166 ppm · 0,90 → ≈ 170 ppm · 0,94 → 179 ppm · 1,00 → 187 ppm. La muestra que Mateo encontró rápida iba a 1,10 → 203 ppm. **Elegida: 0,90.**
- Cómo se cuenta el ritmo: palabras escritas del guion ("GTA 6" y "PS5" cuentan como una palabra cada una). Si se cuentan las palabras tal como se pronuncian, sale más alto (≈ 182-201 ppm), porque "99" se dice "noventa y nueve", "PS5" se dice "pe ese cinco", etc. "Con pausas" mide desde la primera hasta la última palabra, incluidos los respiros entre frases.
- El modelo no da siempre el mismo resultado, así que cada frase se generó 6 veces y se guardó la que Whisper transcribía con menos errores. Así se evitaron tomas en las que "GTA 6" sonaba como "GT6" o "PS5" como "PC5".

## Video 1: `dia1_01_gta6_hora_por_pais_v3.mp4`: PASA

- **Formato:** h264 1080x1920 30 fps · AAC estéreo 48 kHz 199 kb/s · 50,18 s.
- **Sonoridad:** total −14,0 LUFS, LRA 2,5, pico real −1,5 dBTP. Voz −14,0 LUFS (pico de muestra −2,1 dBFS); música −32,6 LUFS en total y −32,7 LUFS mientras hay voz (ducking de 4 dB).
- **Pausas** (silencedetect sobre la pista de voz, −40 dB, ≥ 0,12 s): 23 pausas, de media 0,56 s entre escenas. La más larga dura 0,74 s (en 1,45 s), justo después del gancho "¿Ya puedes jugar GTA 6?", porque la escena mínima dura 2 s. Es un silencio buscado tras la pregunta; ninguna pasa de 1 s.
- **Ritmo:** 130 palabras · 171 ppm mientras habla · 159 ppm con pausas.
- **Whisper (audio final con música, escena por escena):** WER 3,8 % (131 palabras). 7 de 9 escenas al 0 %. Diferencias:
  - Escena 7 (29,1-38,0): "en PSC en comanda... revisa, revisa eso". Al transcribir la misma frase sin música, sale perfecta ("en PS5 manda... revisa eso"), y la voz no tiene nada duplicado (la frase dura 8,44 s y ocupa exactamente su tramo). Por eso lo atribuyo a un error de Whisper con música de fondo, no de la voz. Esta toma usa la variante "PS cinco"; conviene escucharla.
  - Escena 8: "silencian los spoilers" en vez de "silencia" (con la "s" de "los" pegada; normal en habla fluida).
- **Palabras clave:** GTA ✔ · PS5 ✔ (en la escena 7 solo sin música, ver arriba) · Xbox ✔ · spoilers ✔.
- **Fotogramas** (17, cada 3 s desde 1,5 s): tildes correctas (SÍ, DESBLOQUEÓ, MÉXICO, REGIÓN, DÍA, ESPAÑA), nada cortado, la tabla UTC y la de Madrid se leen enteras. El subtítulo de cada fotograma corresponde a la frase que suena en ese momento: cada escena se transcribió dentro de su propio tramo con su frase. El resaltado amarillo se enciende mientras la voz dice la palabra (comprobado en las 9 escenas).
- **Corregido durante la revisión:** la tarjeta de la escena 8 decía "MI LECTURA", pero la voz dice "Mi consejo". Cambiada a "MI CONSEJO" y vuelto a renderizar.

## Video 2: `dia1_02_gta6_resenas_v3.mp4`: PASA

- **Formato:** h264 1080x1920 30 fps · AAC estéreo 48 kHz 206 kb/s · 50,91 s.
- **Sonoridad:** total −13,9 LUFS, LRA 2,4, pico real −1,6 dBTP. Voz −14,0 LUFS; música −32,5 LUFS (−32,8 LUFS bajo la voz).
- **Pausas:** 28, la más larga de 0,54 s; ninguna de más de 0,6 s.
- **Ritmo:** 132 palabras · 170 ppm mientras habla · 159 ppm con pausas.
- **Whisper:** WER 1,4 % (145 palabras). Diferencias: "segundos" en vez de "segundo" (escena 4) y una "X" repetida en "Series X" (escena 5). Son cosas de Whisper que no cambian el sentido. "Metacritic", "Ocarina of Time", "1998", "150" y "99" se entienden bien.
- **Palabras clave:** GTA ✔ (2/2) · PS5 ✔ (3/3).
- **Fotogramas:** "99 / 100", "UNAS 150 RESEÑAS DE PRENSA (PS5)", "DATO DEL 18-19 DE NOVIEMBRE" (sigue siendo cierto: la nota se volvió a comprobar hoy y no ha cambiado), la tabla de rendimiento y "LAS NOTAS PUEDEN CAMBIAR" se leen bien, con tildes (RÉCORD, CRÍTICA, PRÓXIMOS DÍAS, SÍGUENOS). El fotograma de 46,5 s cae justo en el fundido de entrada de la última escena (0,2 s), que es lo esperado.
- **Diferencias aceptadas entre tarjeta y voz:** la tarjeta "Mi lectura" dice "El 99 mide el juego..." y la voz dice "califica el juego". Se cambió el verbo de la voz porque Whisper oía "mide el" como "mí del". El sentido es el mismo.

## Video 3: `dia1_03_gta6_espacio_y_consolas_v3.mp4`: PASA

- **Formato:** h264 1080x1920 30 fps · AAC estéreo 48 kHz 202 kb/s · 50,44 s.
- **Sonoridad:** total −14,2 LUFS, LRA 2,2, pico real −1,5 dBTP. Voz −14,0 LUFS; música −32,5 LUFS (−33,0 LUFS bajo la voz).
- **Pausas:** 22, la más larga de 0,54 s.
- **Ritmo:** 132 palabras · 173 ppm mientras habla · 162 ppm con pausas.
- **Whisper:** WER 4,3 % (141 palabras). Diferencias: "salen PS5" en vez de "sale en PS5" (es la misma secuencia de sonidos), "serie CES" en vez de "Series S" (escena 4), "1" en vez de "una" (de la mañana) y una "es" de más tras "Series S". "Take-Two" sale como "Take 2" (correcto), y "Xbox Cloud Gaming" y "212 gigas" se entienden bien.
- **Palabras clave:** GTA ✔ · PS5 ✔ · Take-Two ✔ · Cloud Gaming ✔ · Xbox ✔ (3/3).
- **Fotogramas:** la barra "58 %", "Te quedan unos 152 GB", "¿EN PC? SIN VERSIÓN ANUNCIADA · TAKE-TWO NO DA FECHA" y la nota de Xbox One (con "1:00 a. m." y "EE. UU.") se leen enteras, sin cortes y con tildes.
- **Corregido durante la revisión:** en la escena "En Xbox One, solo por la *nube*", el resaltado se encendía unos 6 s tarde, porque la voz dice "Cloud Gaming" y no "nube". Se añadió la equivalencia nube = cloud en `render.py` y se volvió a renderizar: ahora se enciende en 27,5 s, cuando la voz dice "Cloud Gaming".

## Comprobaciones comunes

- **Contenido de terceros:** ningún fotograma tiene metraje, capturas, logos ni arte de GTA o Rockstar. El fondo está dibujado por código y en pantalla dice "FONDO: GRÁFICOS PROPIOS · NO ES IMAGEN DEL JUEGO".
- **Datos:** se re-verificaron hoy con WebSearch (Metacritic 99, medianoche hora local, 212 GB, 30 FPS, PC sin anunciar, Xbox One por la nube). **No cambió nada**; detalle en fuentes.md, sección 6.
- **Miniaturas v3:** `*_v3_miniatura.png` salen del mismo código y con el mismo diseño que las v2 (el "99" sigue siendo válido).
- **Cómo se midió la sincronía:** Whisper transcribió el audio final en la ventana de cada escena, y en todas las escenas salió la frase de esa escena, sin pedazos de la anterior ni de la siguiente. Además, el instante del resaltado amarillo cae dentro de la frase hablada en las 27 escenas.
