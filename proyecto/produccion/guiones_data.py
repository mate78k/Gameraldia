# Datos de escenas (texto en pantalla). Ver /home/user/gamer-al-dia/videos/guiones.md y fuentes.md
YEL = (255, 212, 0); WHT = (255, 255, 255); RED = (255, 46, 77); GREY = (200, 204, 214); INK = (11, 13, 18)

def S(t0, t1, card, cap):
    return dict(t0=t0, t1=t1, card=card, cap=cap)

LBL = "IMAGEN DE FONDO: STOCK MIXKIT · NO ES DEL JUEGO"

V1 = dict(
    file="dia1_01_gta6_hora_por_pais.mp4", bg="v1170.mp4", music="m706.mp3", music_ss=0, vol=0.5, label=LBL,
    thumb=[("¿YA SALIÓ", 230, WHT, None), ("GTA 6?", 300, INK, YEL), ("HORA POR PAÍS", 150, WHT, RED)],
    scenes=[
        S(0, 2.6, dict(type="big", lines=[("¿YA PUEDES", 170, WHT, "anton"), ("JUGAR GTA 6?", 190, YEL, "anton")]),
          "¿Ya puedes jugar *GTA 6?*"),
        S(2.6, 6.4, dict(type="big", lines=[("SÍ", 150, WHT, "anton"), ("00:00", 300, YEL, "anton"),
                                              ("19 NOV · HORA LOCAL", 70, WHT, "barlow")]),
          "Sí: se desbloqueó a las *00:00* hora local del 19 de noviembre"),
        S(6.4, 10.0, dict(type="note", tag="DATO OFICIAL", body=["PS5 y Xbox Series X|S", "Medianoche hora local en todas las regiones (soporte de Rockstar)"]),
          "En PS5 y Xbox Series, según *Rockstar*"),
        S(10.0, 15.5, dict(type="table", title="EL MISMO 00:00, EN HORA UTC", hl=0, rows=[
            ("Nueva Zelanda", "11:00", "18 NOV"), ("España (peninsular)", "23:00", "18 NOV"),
            ("Argentina · Chile", "03:00", "19 NOV"), ("Colombia", "05:00", "19 NOV"), ("México (CDMX)", "06:00", "19 NOV")],
            foot="Hora local = medianoche en cada país"),
          "Pero no fue a la vez: *Nueva Zelanda* abrió primero"),
        S(15.5, 20.0, dict(type="big", lines=[("19 HORAS", 230, YEL, "anton"), ("NUEVA ZELANDA VS. CDMX", 70, WHT, "barlow")]),
          "Casi *19 horas* antes que Ciudad de México"),
        S(20.0, 25.0, dict(type="table", title="CUANDO EN MADRID ERAN LAS 00:00...", hl=0, rows=[
            ("Ciudad de México", "17:00", "18 NOV"), ("Bogotá", "18:00", "18 NOV"), ("Buenos Aires · Santiago", "20:00", "18 NOV")],
            foot="Cálculo propio con husos horarios de noviembre"),
          "Cuando España ya jugaba, en México eran las *5 de la tarde*"),
        S(25.0, 29.5, dict(type="note", tag="OJO", body=["En PS5 cuenta la región de tu cuenta, no el país donde estás.", "¿No te abre? Revisa la región y que la descarga terminó."], size=58),
          "En PS5 manda la *región de tu cuenta*"),
        S(29.5, 33.5, dict(type="note", tag="MI CONSEJO", tagcolor=YEL, body=["Fueron años de espera: unas horas de diferencia no cambian nada.", "Juega cuando te toque y silencia spoilers en redes."], size=58),
          "Mi consejo: *silencia spoilers* hoy"),
        S(33.5, 36.0, dict(type="cta", lines=["NOTICIAS GAMER EN 30 SEGUNDOS", "SÍGUENOS PARA MÁS"]),
          "Sigue a *Gamer al Día*"),
    ])

V2 = dict(
    file="dia1_02_gta6_resenas.mp4", bg="v49878.mp4", music="m369.mp3", music_ss=0, vol=0.5, label=LBL,
    thumb=[("GTA 6", 220, WHT, None), ("99", 420, INK, YEL), ("¿Y LO MALO?", 160, WHT, RED)],
    scenes=[
        S(0, 2.6, dict(type="big", lines=[("99", 420, YEL, "anton"), ("EN METACRITIC", 90, WHT, "barlow")]),
          "*GTA 6* ya tiene nota"),
        S(2.6, 6.2, dict(type="big", lines=[("99 / 100", 220, YEL, "anton"), ("UNAS 150 RESEÑAS DE PRENSA (PS5)", 64, WHT, "barlow"), ("DATO DEL 18-19 DE NOVIEMBRE", 48, GREY, "barlow")]),
          "Un *99* en Metacritic con unas 150 reseñas"),
        S(6.2, 10.0, dict(type="big", lines=[("EMPATA EL RÉCORD", 120, WHT, "anton"), ("ZELDA: OCARINA OF TIME", 80, YEL, "barlow"), ("(1998) · TAMBIÉN 99", 60, GREY, "barlow")]),
          "Empata el récord de *Ocarina of Time*"),
        S(10.0, 14.0, dict(type="big", lines=[("LO MALO:", 120, WHT, "anton"), ("30 FPS", 300, RED, "anton"), ("SIN MODO 60 FPS, NI EN PS5 PRO", 62, WHT, "barlow")]),
          "Lo más criticado: va a *30_FPS*"),
        S(14.0, 19.0, dict(type="table", title="RENDIMIENTO SEGÚN PRUEBAS DE PRENSA", hl=0, rows=[
            ("PS5 Pro", "30 ESTABLES", ""), ("PS5 · Series X", "BAJA DE 30", ""), ("Series S", "20 Y PICO", "")],
            foot="En escenas pesadas · Digital Foundry y otros medios"),
          "En *PS5 base* hay bajones en escenas pesadas"),
        S(19.0, 23.0, dict(type="note", tag="OTRA CRÍTICA", body=["Más realismo: coches frágiles, reparaciones y rutinas.", "Varias reseñas avisan de una curva de aprendizaje."], size=58),
          "Su realismo pide *paciencia* si vienes de GTA_5"),
        S(23.0, 28.5, dict(type="note", tag="MI LECTURA", tagcolor=YEL, body=["El 99 mide el juego, no tu consola.", "En PS5 base o Series S, espera tirones en tiroteos y persecuciones grandes."], size=58),
          "Mi lectura: el 99 es real, pero *tu consola* importa"),
        S(28.5, 31.5, dict(type="big", lines=[("LAS NOTAS", 160, WHT, "anton"), ("PUEDEN CAMBIAR", 140, YEL, "anton"), ("LLEGAN MÁS RESEÑAS CADA DÍA", 56, GREY, "barlow")]),
          "Las notas pueden *cambiar* en los próximos días"),
        S(31.5, 35.0, dict(type="cta", lines=["¿LE DAS UN 10 O ES HYPE?", "COMENTA Y SÍGUENOS"]),
          "¿Le das un 10? *Comenta*"),
    ])

V3 = dict(
    file="dia1_03_gta6_espacio_y_consolas.mp4", bg="v44665.mp4", music="m318.mp3", music_ss=0, vol=0.5, label=LBL,
    thumb=[("GTA 6 PIDE HASTA", 190, WHT, None), ("212 GB", 330, INK, YEL), ("¿Y EN PC?", 170, WHT, RED)],
    scenes=[
        S(0, 2.6, dict(type="big", lines=[("212 GB", 330, YEL, "anton"), ("¿TE CABE GTA 6?", 100, WHT, "barlow")]),
          "¿Te *cabe* GTA 6?"),
        S(2.6, 6.4, dict(type="big", lines=[("HASTA 212 GB", 180, YEL, "anton"), ("LIBRES PARA DESCARGARLO", 70, WHT, "barlow"), ("DATO DE ROCKSTAR · VARÍA SEGÚN CONSOLA", 46, GREY, "barlow")]),
          "Rockstar pide hasta *212_GB* libres"),
        S(6.4, 10.2, dict(type="big", lines=[("SOLO EN", 120, WHT, "anton"), ("PS5", 200, YEL, "anton"), ("XBOX SERIES X|S", 130, YEL, "anton")]),
          "Y solo sale en *PS5* y *Xbox Series*"),
        S(10.2, 15.5, dict(type="bar", title="XBOX SERIES S: 364 GB ÚTILES", used=212, total=364,
                           l1="GTA 6: hasta 212 GB", l2="Te quedan unos 152 GB para todo lo demás", foot="Cálculo propio · 212 / 364"),
          "En *Series S* se come más de la mitad del disco"),
        S(15.5, 19.5, dict(type="big", lines=[("¿EN PC?", 200, WHT, "anton"), ("SIN VERSIÓN ANUNCIADA", 90, RED, "barlow"), ("TAKE-TWO NO DA FECHA", 60, GREY, "barlow")]),
          "¿En PC? *No hay* versión anunciada"),
        S(19.5, 24.5, dict(type="note", tag="¿XBOX ONE?", body=["Solo por Xbox Cloud Gaming, desde la 1:00_a._m. (hora del Este de EE._UU.) del 19 de noviembre.", "El juego se compra aparte."], size=56),
          "En Xbox One, solo por la *nube*"),
        S(24.5, 30.0, dict(type="note", tag="MI CONSEJO", tagcolor=YEL, body=["Revisa tu espacio antes de pagar.", "En Series S: borra lo que no juegas o usa la tarjeta de expansión oficial."], size=58),
          "Mi consejo: *libera espacio* antes de pagar"),
        S(30.0, 33.0, dict(type="big", lines=[("DEJA MARGEN", 170, WHT, "anton"), ("PARA PARCHES", 150, YEL, "anton")]),
          "Y deja *margen* para actualizaciones"),
        S(33.0, 36.0, dict(type="cta", lines=["NOTICIAS GAMER EN 30 SEGUNDOS", "SÍGUENOS PARA MÁS"]),
          "Sigue a *Gamer al Día*"),
    ])

VIDEOS = [V1, V2, V3]

# ---------------------------------------------------------------- v2: capturas oficiales (opcional)
# Solo se usan con:  python3 render.py <id> --capturas   (ver LEEME_imagenes.md)
# Clave = nombre del archivo v1 del video. Cada captura: archivo en imagenes_oficiales/, t0/t1 (2-5 s),
# modo "marco" (recuadro en lugar de la tarjeta; el subtítulo se mantiene) o "fondo" (pantalla completa
# oscurecida detrás de la tarjeta), zoom (inicio, fin) y foco (x, y de 0 a 1) para el encuadre.
CAPTURAS = {
    "dia1_01_gta6_hora_por_pais.mp4": [
        # dict(archivo="captura_01.jpg", t0=15.5, t1=20.0, modo="marco", zoom=(1.05, 1.20), foco=(0.5, 0.45)),
    ],
    "dia1_02_gta6_resenas.mp4": [
        # dict(archivo="captura_02.jpg", t0=19.0, t1=23.0, modo="marco", zoom=(1.0, 1.15), foco=(0.5, 0.5)),
    ],
    "dia1_03_gta6_espacio_y_consolas.mp4": [
        # dict(archivo="captura_03.jpg", t0=6.4, t1=10.2, modo="fondo", zoom=(1.08, 1.0), foco=(0.5, 0.5)),
    ],
}
