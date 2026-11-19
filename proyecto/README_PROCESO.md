# Gamer al Día: proceso de producción diaria (3 videos por día)

Canal de noticias y clips gamer en español (YouTube Shorts, TikTok, Instagram Reels). Proyecto de Mateo, SEPARADO de NERO Clothing. Este repositorio es público y solo guarda videos y el código de producción. La memoria y las reglas están en el Drive «Gaming y YouTube» (leer primero «00 LEEME - Índice y reglas»).

## Reconstruir el entorno en una sesión nueva
1. `pip install sherpa-onnx==1.12.40 pyloudnorm pillow numpy` (usar `python3 -I`). La 2.0.x falla.
2. Modelo de voz Supertonic 3 (hombre, sid 7, velocidad 0,90): `https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/sherpa-onnx-supertonic-3-tts-int8-2026-05-11.tar.bz2` (GitHub releases sí se puede descargar; Hugging Face está bloqueado). Whisper-small int8 para control de calidad: buscar en los releases `asr-models` del mismo repositorio.
3. Música y fondos de Mixkit (licencia gratuita): URLs en `fuentes.md`, sección 2. Guardarlas en `proyecto/produccion/stock/` (NO se suben al repositorio).
4. Fuentes Anton y Barlow Condensed (OFL) están en `produccion/fuentes/`.
5. Scripts: `produccion/render.py` (`--voz3` renderiza con la voz), `voz_v3.py`, `qc_v3.py`, `asr_v3.py`. Los datos de cada video están en `guiones_data.py`. Las rutas base están en `render.py` (BASE) y deben ajustarse al entorno nuevo.

## Reglas para publicar solo (autorizado por Mateo el 2026-11-19)
- 3 videos al día, TikTok + YouTube + Instagram, por Metricool (blogId 8094347, zona America/Bogota).
- Horas iniciales (Bogotá): 14:00, 19:00, 21:00; ajustar con datos propios (Cifras) desde la semana 2.
- Solo se programa un video si: datos verificados el mismo día con fuente; Calidad PASA (voz con Whisper vs guion, volumen voz -14 LUFS, música 15-20 dB debajo, 9:16, tildes); Escudo da visto bueno; con marca de contenido generado con IA; sin metraje, música ni arte de editores sin permiso (nada de carátulas ni personajes de GTA).
- Si algo falla: corregir con el equipo; si no se puede, NO publicar y avisar a Mateo.
- Los MP4 se suben a `mate78k/Gameraldia` (carpeta del día, ej. `dia2/`) y se usa la URL `https://raw.githubusercontent.com/mate78k/Gameraldia/main/<carpeta>/<archivo>.mp4` en Metricool.
- Duración (orden de Mateo): 61-75 s en todos los videos (TikTok Creator Rewards exige más de 60 s; necesita 10.000 seguidores). Escudo verifica cada día las duraciones máximas y la que mejor monetiza.
- Nunca pedir ni guardar contraseñas ni cookies.

## Voz oficial desde 2026-11-20 (elegida por Mateo): Nacho (Inworld) vía Speko
- Herramienta: conector Speko, `audio_synthesize` con body: `{"text": ..., "intent": {"language": "es-MX", "optimizeFor": "quality"}, "voice": "Nacho", "instructions": "Voz joven, energética y emocionada, como un streamer gamer narrando noticias de última hora, con ritmo rápido y entusiasmo.", "constraints": {"allowedProviders": {"tts": ["inworld"]}}, "spokenForm": true}`.
- La respuesta es muy grande: el cliente guarda el resultado en un archivo; el texto de ese archivo dice «saved to <ruta>.wav». Convertir con ffmpeg. Máximo ~2.000 caracteres por llamada (Inworld); dividir el guion por frases/párrafos y unir.
- Nacho habla muy rápido (~213 palabras/min): el guion debe ser MÁS LARGO para que el video dure 61-75 s (más datos, comparativas, ejemplos, contexto), nunca estirar con silencios.
- Crédito de Speko: 5 USD gratis al 2026-11-19 (cada minuto de Inworld ~0,0225 USD). Si se acaba, avisar a Mateo.
- Licencia comercial de esta voz: SUPUESTO sin verificar en los términos de Speko/Inworld: Escudo debe revisarla antes de monetizar.
- Voz anterior (Supertonic) queda solo como respaldo si Speko falla.
## Estilo visual
Edición animada tipo motion (plantilla Remotion), con la paleta atardecer neón GTA (azul noche #1B1F5E, púrpura #7A2BB8, magenta #EE00DD, rosa #FF5FA2, naranja #FF8A3D, dorado #FFC857) para que se note que hablamos de GTA 6, sin logo ni arte oficial.

## Cultura de mejora continua (orden de Mateo, 2026-11-19)
Cada puesto (Radar, Escudo, Pluma, Micrófono, Corte, Lienzo, Calidad, Cifras, Eco, Publicador, Planificador) investiga algo nuevo cada día y deja una lección de una línea en la bitácora del Drive; Cifras presenta cada mañana los números de ayer (Metricool) y el jefe (la sesión principal de Claude) consolida y decide. Escudo revisa políticas y licencias cada día. Descripciones: gancho en la primera línea, 3 datos con ✅, pregunta a la audiencia, invitación a seguir, fuentes, aviso de voz generada por IA, 3-8 hashtags (YouTube 3-6, TikTok 4-5, Instagram 6-8).
