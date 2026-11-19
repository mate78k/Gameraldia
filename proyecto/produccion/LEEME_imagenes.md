# Cómo insertar imágenes oficiales en los videos (versión 2)

Esta carpeta está **vacía a propósito**. El proyecto no trae ninguna imagen de Rockstar: no se descargó nada.
Mateo, tú decides qué imágenes usar después de verificar que tienes permiso.

## 1. Antes de nada: la licencia

- Usa solo imágenes que Rockstar publique para prensa o difusión (por ejemplo, su Newswire o su kit de prensa) y lee sus condiciones de uso. Si dudas, no la uses.
- Nada de filtraciones, capturas de streamers ni arte de fans sin permiso.
- **Solo imágenes fijas** (`.jpg`, `.jpeg`, `.png`, `.webp`). El renderizador **no acepta video** a propósito: la regla del canal sigue siendo no meter metraje de GTA. Así tampoco entra audio original.
- Cada imagen sale en pantalla **entre 2 y 5 segundos** (el renderizador rechaza otros tiempos) con el crédito **"Imágenes: Rockstar Games"** abajo a la derecha.
- Mejor 1 o 2 capturas por video, que acompañen a un dato. El análisis y los gráficos propios deben seguir siendo lo principal.
- Si incluyes capturas, cambia en la descripción la frase "Fondo: gráficos propios" por algo como "Imágenes del juego: Rockstar Games (material de prensa)".

## 2. Pasos

1. Copia la imagen en esta carpeta: `/home/user/gamer-al-dia/produccion/imagenes_oficiales/`
   (nombre sin espacios ni tildes, por ejemplo `captura_01.jpg`; mejor horizontal y de 1920 px de ancho o más).
2. Abre `/home/user/gamer-al-dia/produccion/guiones_data.py`, baja hasta `CAPTURAS` y quita el `#` de la línea de ejemplo del video que quieras (o escribe una nueva):

   ```python
   "dia1_01_gta6_hora_por_pais.mp4": [
       dict(archivo="captura_01.jpg", t0=15.5, t1=20.0, modo="marco", zoom=(1.05, 1.20), foco=(0.5, 0.45)),
   ],
   ```

   | Campo | Qué hace |
   |---|---|
   | `archivo` | Nombre del archivo dentro de esta carpeta. |
   | `t0`, `t1` | Segundo de entrada y de salida. Entre 2 y 5 s de duración. Lo más limpio es hacerlo coincidir con una escena (los tiempos de cada escena están en `guiones.md`). |
   | `modo` | `"marco"`: la captura ocupa el recuadro central en lugar de la tarjeta, con borde neón; el subtítulo se mantiene. `"fondo"`: la captura llena la pantalla, oscurecida, y la tarjeta de datos va encima. |
   | `zoom` | Zoom lento de inicio a fin. `(1.05, 1.20)` acerca; `(1.20, 1.05)` aleja. Entre 1.0 y 1.3 se ve natural. |
   | `foco` | Punto de la imagen donde se centra el encuadre: `(0.5, 0.5)` es el centro, `(0.3, 0.4)` es más a la izquierda y arriba. |

3. Renderiza con la opción `--capturas` (sin ella las capturas se ignoran):

   ```bash
   cd /home/user/gamer-al-dia/produccion
   python3 render.py 1 --capturas        # solo el video 1
   python3 render.py --capturas          # los tres
   ```

   La consola dice qué capturas se insertaron y avisa si falta un archivo, no es imagen o la duración no está entre 2 y 5 s.
   El resultado sobrescribe `videos/dia1_0X_..._v2.mp4`. Si quieres conservar la versión sin capturas, cópiala antes.

4. Revisa el video: que el crédito se lea, que nada importante quede cortado por el encuadre (ajusta `foco` y `zoom`) y que la captura no tape un dato que el subtítulo nombra.

## 3. Lo que hace el renderizador con cada captura

- Recorta la imagen con encuadre propio (vertical, no la imagen tal cual) y aplica un zoom lento y suave.
- Pone el crédito "Imágenes: Rockstar Games" mientras la captura está en pantalla. El texto se cambia en `render.py` (`CREDITO_CAPTURAS`).
- No usa sonido de la imagen (no tiene) y la música sigue igual de baja (−29 LUFS).
- No aplica logos ni tipografía de GTA; la identidad sigue siendo la de Gamer al Día con el atardecer neón.

## 4. Versión con voz (`--voz`)

`python3 -I render.py 1 --voz --capturas` también funciona. Ahí las escenas duran lo que dura cada frase, así que los `t0`/`t1` que escribas (tiempos de la v1, los de `guiones.md`) se trasladan solos a la nueva línea de tiempo, escena por escena. Si al trasladarse una captura pasa de 5 s, se recorta a 5 s.
