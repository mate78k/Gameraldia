#!/usr/bin/env python3
"""Gamer al Día - renderizador de shorts verticales 1080x1920 · VERSIÓN 2 (identidad "atardecer neón").

Uso:
  python3 render.py                 # renderiza los 3 videos v2 + miniaturas v2
  python3 render.py 1 3             # solo los videos 1 y 3
  python3 render.py 2 --capturas    # incluye las capturas oficiales definidas en guiones_data.py
                                    # (CAPTURAS) que existan en imagenes_oficiales/. Ver LEEME_imagenes.md
  python3 render.py --solo-miniaturas
  python3 render.py --voz           # versión con voz generada (antes: python3 -I voz_v2.py) -> *_v2_voz.mp4
  python3 render.py --voz3          # v3: voz Supertonic 3 hombre (antes: python3 -I voz_v3.py) -> *_v3.mp4 + *_v3_miniatura.png

Cambios frente a v1 (render_v1.py se conserva intacto):
  * Fondo 100 % dibujado por código: degradado atardecer neón, sol retro, rejilla, palmeras vectoriales.
    No se usa metraje ni arte del juego.
  * Música como cama suave: se normaliza a MUSIC_LUFS (-29 LUFS integrados) con pyloudnorm,
    con limitación de pico a -3 dBTP aprox.
  * Soporte opcional para capturas oficiales (zoom lento, encuadre propio, crédito en pantalla, sin audio).
"""
import subprocess, sys, os, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "/home/user/gamer-al-dia/videos"
FDIR = os.path.join(BASE, "fuentes")
STOCK = os.path.join(BASE, "stock")
IMG_OFICIALES = os.path.join(BASE, "imagenes_oficiales")
LOGO = "/home/user/gamer-al-dia/logo/logo_opcion_A_mando_rayo_transparente.png"
W, H, FPS = 1080, 1920, 30
SUFIJO = "_v2"
MUSIC_LUFS = -29.0          # cama musical para poner voz encima a -14 LUFS (15 dB por debajo)
CREDITO_CAPTURAS = "Imágenes: Rockstar Games"
LABEL_V2 = "FONDO: GRÁFICOS PROPIOS · NO ES IMAGEN DEL JUEGO"

# marca Gamer al Día
INK = (11, 13, 18); INK2 = (22, 26, 35); RED = (255, 46, 77); YEL = (255, 212, 0); WHT = (255, 255, 255)
GREY = (200, 204, 214)
# paleta atardecer neón (v2)
NOCHE = (0x1B, 0x1F, 0x5E); PURP = (0x7A, 0x2B, 0xB8); MAG = (0xEE, 0x00, 0xDD)
ROSA = (0xFF, 0x5F, 0xA2); NAR = (0xFF, 0x8A, 0x3D); ORO = (0xFF, 0xC8, 0x57)
PANEL = (16, 12, 44)        # azul noche muy oscuro para paneles
SILUETA = (14, 8, 34)       # color de las palmeras
HORIZ = 1580                # línea del horizonte

def anton(s): return ImageFont.truetype(os.path.join(FDIR, "anton-latin-400-normal.woff2"), s)
def barlow(s, w=800): return ImageFont.truetype(os.path.join(FDIR, f"barlow-condensed-latin-{w}-normal.woff2"), s)

_logo = Image.open(LOGO).convert("RGBA")
_logo = _logo.crop(_logo.getbbox())

def logo(width):
    r = width / _logo.width
    return _logo.resize((width, int(_logo.height * r)), Image.LANCZOS)

# ---------------------------------------------------------------- utilidades gráficas
def lerp(a, b, t): return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))

def gradient_stops(n, stops):
    """stops = [(pos 0..1, (r,g,b)), ...] -> array (n,3) float"""
    pos = np.array([s[0] for s in stops]); cols = np.array([s[1] for s in stops], float)
    x = np.linspace(0, 1, n)
    return np.stack([np.interp(x, pos, cols[:, c]) for c in range(3)], 1)

SUNSET = [(0.00, NOCHE), (0.42, PURP), (0.64, MAG), (0.78, ROSA), (0.90, NAR), (1.00, ORO)]

def glow(layer, radius=18, strength=2):
    """Devuelve una capa RGBA con el resplandor (blur) de 'layer' debajo de la propia capa."""
    g = layer.filter(ImageFilter.GaussianBlur(radius))
    out = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    for _ in range(strength):
        out = Image.alpha_composite(out, g)
    return Image.alpha_composite(out, layer)

def bezier(p0, p1, p2, n=24):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in np.linspace(0, 1, n)]

def draw_palm(d, base, top, ctrl, trunk_w, frond_len, color, s=1.0, seed=0):
    """Palmera vectorial: tronco curvo con anillos + hojas arqueadas. Dibujada a mano por código."""
    rng = np.random.default_rng(seed)
    pts = bezier(base, ctrl, top, 40)
    left, right = [], []
    for i, (x, y) in enumerate(pts):
        t = i / (len(pts) - 1)
        w = trunk_w * (1 - 0.55 * t) / 2
        if i < len(pts) - 1: dx, dy = pts[i + 1][0] - x, pts[i + 1][1] - y
        else: dx, dy = x - pts[i - 1][0], y - pts[i - 1][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        left.append((x + nx * w, y + ny * w)); right.append((x - nx * w, y - ny * w))
    d.polygon(left + right[::-1], fill=color)
    # anillos del tronco (muescas)
    for i in range(2, len(pts) - 2, 3):
        x, y = pts[i]; t = i / (len(pts) - 1); w = trunk_w * (1 - 0.55 * t) / 2
        d.ellipse([x - w - 3 * s, y - 3 * s, x + w + 3 * s, y + 3 * s], fill=color)
    # hojas (pinnadas: nervio central + foliolos finos a ambos lados)
    cx, cy = top
    n = 11
    for k in range(n):
        ang = math.radians(-195 + k * 210 / (n - 1) + rng.uniform(-7, 7))
        L = frond_len * rng.uniform(0.85, 1.1)
        droop = 0.55 + 0.25 * abs(math.cos(ang))
        tip = (cx + math.cos(ang) * L, cy + math.sin(ang) * L * 0.35 + L * droop)
        mid = (cx + math.cos(ang) * L * 0.6, cy + math.sin(ang) * L * 0.6 - L * 0.12)
        spine = bezier((cx, cy), mid, tip, 40)
        up, dn = [], []
        for i, (x, y) in enumerate(spine):
            t = i / (len(spine) - 1)
            wdt = (2.6 * s) * (1 - t) + 0.6 * s
            if i < len(spine) - 1: dx, dy = spine[i + 1][0] - x, spine[i + 1][1] - y
            else: dx, dy = x - spine[i - 1][0], y - spine[i - 1][1]
            Lg = math.hypot(dx, dy) or 1
            nx, ny = -dy / Lg, dx / Lg
            up.append((x + nx * wdt, y + ny * wdt)); dn.append((x - nx * wdt, y - ny * wdt))
        d.polygon(up + dn[::-1], fill=color)
        for i in range(2, len(spine) - 1):
            x, y = spine[i]; t = i / (len(spine) - 1)
            dx, dy = spine[i + 1][0] - x, spine[i + 1][1] - y
            Lg = math.hypot(dx, dy) or 1
            ux, uy = dx / Lg, dy / Lg
            nx, ny = -uy, ux
            ln = frond_len * 0.20 * math.sin(math.pi * (0.15 + 0.85 * t)) * (1.05 - 0.5 * t)
            bw = frond_len * 0.012 + 1.0 * s
            for sg in (1, -1):
                # foliolo: triángulo fino inclinado hacia la punta y algo caído
                ex = x + (nx * sg * 0.8 + ux * 0.55) * ln
                ey = y + (ny * sg * 0.8 + uy * 0.55) * ln + ln * 0.35
                d.polygon([(x - ux * bw, y - uy * bw), (ex, ey), (x + ux * bw, y + uy * bw)], fill=color)
    d.ellipse([cx - trunk_w * 0.5, cy - trunk_w * 0.4, cx + trunk_w * 0.5, cy + trunk_w * 0.4], fill=color)

def palms_layer(variant=0):
    """Capa RGBA con palmeras en silueta + borde neón suave. Se dibuja a 2x y se reduce (antialias)."""
    S = 2
    lay = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    c = SILUETA + (255,)
    sets = [
        # (base, top, ctrl, grosor, hojas)
        [((-40, 1960), (150, 1150), (40, 1500), 58, 300),
         ((110, 1960), (300, 1330), (190, 1650), 40, 210),
         ((1130, 1960), (930, 1220), (1080, 1560), 52, 270),
         ((1010, 1960), (1010, 1420), (1050, 1700), 34, 170)],
        [((1120, 1960), (920, 1140), (1060, 1500), 58, 300),
         ((980, 1960), (790, 1340), (900, 1650), 38, 200),
         ((-50, 1960), (150, 1230), (10, 1560), 52, 270),
         ((80, 1960), (70, 1430), (40, 1700), 34, 170)],
    ][variant % 2]
    for i, (b, t, cc, tw, fl) in enumerate(sets):
        sc = lambda p: (p[0] * S, p[1] * S)
        draw_palm(d, sc(b), sc(t), sc(cc), tw * S, fl * S, c, s=S, seed=7 + i + variant * 10)
    # palmeras pequeñas en el horizonte
    for x, hh, sd in [(330, 120, 1), (390, 90, 2), (700, 105, 3), (760, 80, 4)]:
        draw_palm(d, (x * S, HORIZ * S), ((x + 12) * S, (HORIZ - hh) * S), ((x - 4) * S, (HORIZ - hh / 2) * S),
                  9 * S, hh * 0.55 * S, c, s=S * 0.4, seed=40 + sd)
    lay = lay.resize((W, H), Image.LANCZOS)
    # borde neón rosa por detrás (contraluz)
    a = lay.split()[3]
    rim = Image.new("RGBA", (W, H), ROSA + (0,)); rim.putalpha(a.filter(ImageFilter.MaxFilter(5)))
    rim = rim.filter(ImageFilter.GaussianBlur(6))
    out = Image.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, 0)), rim)
    return Image.alpha_composite(out, lay)

def sky_base():
    """Fondo estático: cielo degradado + sol retro + halo + suelo. Devuelve RGB uint8 (H,W,3)."""
    sky = gradient_stops(HORIZ, SUNSET)                     # (HORIZ,3)
    img = np.zeros((H, W, 3), float)
    img[:HORIZ] = sky[:, None, :]
    floor = gradient_stops(H - HORIZ, [(0, (44, 10, 70)), (0.2, (22, 8, 48)), (1, (6, 4, 20))])
    img[HORIZ:] = floor[:, None, :]
    base = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGB").convert("RGBA")
    # halo del sol
    halo = Image.new("RGBA", (W, H), (0, 0, 0, 0)); hd = ImageDraw.Draw(halo)
    hd.ellipse([540 - 560, HORIZ - 560, 540 + 560, HORIZ + 560], fill=ROSA + (120,))
    halo = halo.filter(ImageFilter.GaussianBlur(120))
    ha = np.array(halo); ha[HORIZ:, :, 3] = (ha[HORIZ:, :, 3] * 0.25).astype(np.uint8); halo = Image.fromarray(ha, "RGBA")
    base = Image.alpha_composite(base, halo)
    # sol retro con franjas
    R = 330
    sun = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    col = gradient_stops(2 * R, [(0, ORO), (0.45, NAR), (0.75, ROSA), (1, MAG)])
    arr = np.zeros((H, W, 4), np.uint8)
    yy, xx = np.mgrid[0:H, 0:W]
    inside = (xx - 540) ** 2 + (yy - HORIZ) ** 2 <= R * R
    inside &= yy < HORIZ
    # franjas horizontales que crecen hacia el horizonte
    rel = (yy - (HORIZ - R))
    for k, (y0, gap) in enumerate([(0.52, 6), (0.62, 9), (0.71, 12), (0.80, 15), (0.89, 18)]):
        ys = int(HORIZ - R + y0 * R)
        inside &= ~((yy >= ys) & (yy < ys + gap))
    idx = np.clip(rel, 0, 2 * R - 1)
    arr[..., :3] = col[idx].astype(np.uint8)
    arr[..., 3] = np.where(inside, 255, 0)
    sun = Image.fromarray(arr, "RGBA")
    base = Image.alpha_composite(base, glow(sun, 30, 1))
    # línea de horizonte neón
    ln = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(ln)
    ld.rectangle([0, HORIZ - 2, W, HORIZ + 2], fill=ROSA + (255,))
    base = Image.alpha_composite(base, glow(ln, 10, 2))
    return base

def grid_frames(n=30):
    """Rejilla en perspectiva que avanza (ciclo de n fotogramas). Capas RGBA solo de la zona del suelo."""
    hh = H - HORIZ
    frames = []
    for f in range(n):
        lay = Image.new("RGBA", (W, hh), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        # líneas que fugan al centro
        for k in range(-14, 15):
            x_far = 540 + k * 26; x_near = 540 + k * 210
            d.line([(x_far, 0), (x_near, hh)], fill=MAG + (170,), width=2)
        # líneas horizontales con perspectiva
        ph = f / n
        for j in range(12):
            z = (j + 1 - ph)
            if z <= 0: continue
            y = hh * (1 - 1 / (1 + z * 0.45)) * 1.55
            y = hh - y if False else (hh * ((z / 12) ** 2.2))
            if 0 < y < hh:
                d.line([(0, y), (W, y)], fill=MAG + (int(90 + 130 * y / hh),), width=3)
        frames.append(glow(lay, 5, 1))
    return frames

def stars(seed=3, n=70):
    rng = np.random.default_rng(seed)
    return [(rng.uniform(0, W), rng.uniform(40, 820), rng.uniform(1.2, 3.2), rng.uniform(0, 6.28), rng.uniform(0.6, 1.8))
            for _ in range(n)]

class Fondo:
    """Genera el fondo animado: estrellas que titilan, rejilla que avanza, palmeras con leve vaivén."""
    def __init__(self, variant=0):
        self.base = sky_base()
        self.grid = grid_frames(30)
        self.palms = palms_layer(variant)
        self.stars = stars(3 + variant)

    def frame(self, t, i):
        img = self.base.copy()
        d = ImageDraw.Draw(img)
        for x, y, r, ph, sp in self.stars:
            a = 0.55 + 0.45 * math.sin(t * sp * 2 + ph)
            c = lerp(PURP, WHT, a)
            d.ellipse([x - r, y - r, x + r, y + r], fill=c + (255,))
        img.alpha_composite(self.grid[i % len(self.grid)], (0, HORIZ))
        dx = int(round(4 * math.sin(t * 0.9)))
        img.alpha_composite(self.palms, (dx, 0)) if dx >= 0 else img.alpha_composite(self.palms.crop((-dx, 0, W, H)), (0, 0))
        return img

# ---------------------------------------------------------------- texto
def wrap(draw, text, font, maxw):
    words, lines, cur = text.split(), [], []
    for w in words:
        t = " ".join(cur + [w])
        if cur and draw.textlength(t.replace("*", ""), font=font) > maxw:
            lines.append(cur); cur = [w]
        else:
            cur.append(w)
    if cur: lines.append(cur)
    return lines

def caption(img, text, y_center=1290, size=88, maxw=900, hl_on=True):
    """Subtítulo grande; palabras entre *asteriscos* van resaltadas en amarillo (color de marca)."""
    d = ImageDraw.Draw(img)
    f = barlow(size, 800)
    text = text.upper()
    toks, hl, inside = [], [], False
    for w in text.split():
        start = w.startswith("*"); end = w.endswith("*") or w.endswith("*?") or w.endswith("*,") or w.endswith("*.")
        if start: inside = True
        toks.append(w.replace("*", "").replace("_", " ")); hl.append(inside)
        if end: inside = False
    lines, cur, curhl = [], [], []
    for w, h in zip(toks, hl):
        t = " ".join(cur + [w])
        if cur and d.textlength(t, font=f) > maxw:
            lines.append((cur, curhl)); cur, curhl = [w], [h]
        else:
            cur.append(w); curhl.append(h)
    if cur: lines.append((cur, curhl))
    lh = int(size * 1.12)
    y = y_center - lh * len(lines) // 2
    # banda oscura suave detrás del subtítulo (legibilidad sobre el sol)
    band = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.rounded_rectangle([40, y - 30, W - 40, y + lh * len(lines) + 24], 40, fill=PANEL + (150,))
    img.alpha_composite(band.filter(ImageFilter.GaussianBlur(14)))
    d = ImageDraw.Draw(img)
    sp = d.textlength(" ", font=f)
    for words, hls in lines:
        tw = d.textlength(" ".join(words), font=f)
        x = (W - tw) / 2
        for w, h in zip(words, hls):
            ww = d.textlength(w, font=f)
            if h and hl_on:
                d.rounded_rectangle([x - 12, y + 6, x + ww + 12, y + lh - 2], 10, fill=YEL)
                d.text((x, y), w, font=f, fill=INK)
            else:
                d.text((x, y), w, font=f, fill=WHT, stroke_width=7, stroke_fill=INK)
            x += ww + sp
        y += lh

def center_text(d, y, text, font, fill, stroke=0, sfill=INK):
    tw = d.textlength(text, font=font)
    d.text(((W - tw) / 2, y), text, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)

def fit_font(d, text, mk, size, maxw):
    while size > 20:
        f = mk(size)
        if d.textlength(text, font=f) <= maxw: return f
        size -= 4
    return mk(size)

# ---------------------------------------------------------------- tarjetas
def panel(d, box, fill=PANEL, outline=None):
    """Panel azul noche translúcido con borde neón magenta→rosa y resplandor."""
    img = d._image
    x0, y0, x1, y1 = [int(v) for v in box]
    neon = Image.new("RGBA", (W, H), (0, 0, 0, 0)); nd = ImageDraw.Draw(neon)
    nd.rounded_rectangle([x0, y0, x1, y1], 28, outline=(outline or MAG) + (255,), width=5)
    img.alpha_composite(neon.filter(ImageFilter.GaussianBlur(16)))
    img.alpha_composite(neon.filter(ImageFilter.GaussianBlur(6)))
    body = Image.new("RGBA", (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(body)
    bd.rounded_rectangle([x0, y0, x1, y1], 28, fill=fill + (226,))
    img.alpha_composite(body)
    # borde fino con degradado vertical magenta→rosa→naranja
    edge = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ed = ImageDraw.Draw(edge)
    ed.rounded_rectangle([x0, y0, x1, y1], 28, outline=(255, 255, 255, 255), width=4)
    g = gradient_stops(y1 - y0 + 1, [(0, MAG), (0.6, ROSA), (1, NAR)])
    col = np.zeros((H, W, 4), np.uint8)
    col[y0:y1 + 1, :, :3] = g[:, None, :].astype(np.uint8)
    col[..., 3] = np.array(edge.split()[3])
    img.alpha_composite(Image.fromarray(col, "RGBA"))

def card_big(img, spec):
    d = ImageDraw.Draw(img)
    items = []
    for t, s, c, fnt in spec["lines"]:
        mk = anton if fnt == "anton" else (lambda z: barlow(z, 800))
        f = fit_font(d, t, mk, s, 900)
        bb = d.textbbox((0, 0), t, font=f)
        items.append((t, f, c, bb[3] - bb[1], bb[1]))
    gap = 26
    total = sum(i[3] for i in items) + gap * (len(items) - 1)
    y = 730 - total // 2
    if spec.get("panel", True):
        panel(d, [70, y - 60, W - 70, y + total + 60], outline=spec.get("outline"))
        d = ImageDraw.Draw(img)
    for t, f, c, h, off in items:
        center_text(d, y - off, t, f, c, stroke=0)
        y += h + gap

def card_table(img, spec):
    d = ImageDraw.Draw(img)
    rows = spec["rows"]
    title = spec["title"]
    rh = 112
    top = 715 - (130 + rh * len(rows)) // 2
    panel(d, [60, top - 40, W - 60, top + 130 + rh * len(rows) + (60 if spec.get("foot") else 30)])
    d = ImageDraw.Draw(img)
    ft = fit_font(d, title, lambda z: barlow(z, 800), 60, 900)
    center_text(d, top, title, ft, YEL)
    y = top + 120
    for i, (a, b, c) in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([90, y - 6, W - 90, y + rh - 14], 16, fill=(40, 22, 78))
        fa = fit_font(d, a, lambda z: barlow(z, 800), 56, 520)
        d.text((120, y + 14), a, font=fa, fill=WHT)
        fb = anton(64)
        tb = d.textlength(b, font=fb)
        hl = spec.get("hl") == i
        d.text((W - 120 - tb, y + 2), b, font=fb, fill=(YEL if hl else WHT))
        if c:
            fc = barlow(30, 700)
            tc = d.textlength(c, font=fc)
            d.text((W - 120 - tb - tc - 22, y + 36), c, font=fc, fill=GREY)
        y += rh
    if spec.get("foot"):
        ff = barlow(34, 700)
        center_text(d, y + 4, spec["foot"], ff, GREY)

def card_note(img, spec):
    d = ImageDraw.Draw(img)
    f_t = barlow(64, 800)
    f_b = barlow(spec.get("size", 62), 700)
    body = []
    for para in spec["body"]:
        body += [" ".join(l).replace("_", " ") for l in wrap(d, para, f_b, 860)]
    lh = int(spec.get("size", 62) * 1.18)
    total = 100 + lh * len(body)
    top = 730 - total // 2
    panel(d, [70, top - 50, W - 70, top + total + 40], outline=spec.get("outline"))
    d = ImageDraw.Draw(img)
    tag = spec["tag"]
    tw = d.textlength(tag, font=f_t)
    d.rounded_rectangle([(W - tw) / 2 - 24, top - 8, (W + tw) / 2 + 24, top + 78], 12, fill=spec.get("tagcolor", RED))
    center_text(d, top - 4, tag, f_t, WHT if spec.get("tagcolor", RED) == RED else INK)
    y = top + 110
    for l in body:
        center_text(d, y, l, f_b, WHT)
        y += lh

def card_bar(img, spec):
    d = ImageDraw.Draw(img)
    top = 470
    panel(d, [60, top - 40, W - 60, top + 560])
    d = ImageDraw.Draw(img)
    center_text(d, top, spec["title"], barlow(62, 800), YEL)
    x0, x1, yb = 110, W - 110, top + 150
    d.rounded_rectangle([x0, yb, x1, yb + 120], 20, fill=(40, 22, 78), outline=GREY, width=4)
    frac = spec["used"] / spec["total"]
    # barra con degradado magenta→naranja
    bw = int((x1 - x0) * frac)
    g = gradient_stops(bw, [(0, MAG), (0.6, ROSA), (1, NAR)]).astype(np.uint8)
    bar = np.zeros((120, bw, 4), np.uint8); bar[..., :3] = g[None, :, :]
    m = Image.new("L", (bw, 120), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, bw - 1, 119], 20, fill=255)
    bar[..., 3] = np.array(m)
    img.alpha_composite(Image.fromarray(bar, "RGBA"), (x0, yb))
    d = ImageDraw.Draw(img)
    pct = f"{round(frac*100)} %"
    d.text((x0 + 30, yb + 14), pct, font=anton(84), fill=WHT)
    d.text((x0, yb + 150), spec["l1"], font=barlow(50, 800), fill=WHT)
    d.text((x0, yb + 215), spec["l2"], font=barlow(50, 800), fill=GREY)
    ff = barlow(34, 700)
    center_text(d, yb + 310, spec["foot"], ff, GREY)

def card_cta(img, spec):
    d = ImageDraw.Draw(img)
    panel(d, [70, 420, W - 70, 1060])
    lg = logo(820)
    img.alpha_composite(lg, ((W - lg.width) // 2, 500))
    d = ImageDraw.Draw(img)
    y = 500 + lg.height + 50
    for t in spec["lines"]:
        f = fit_font(d, t, lambda z: barlow(z, 800), 64, 880)
        center_text(d, y, t, f, YEL if t is spec["lines"][0] else WHT)
        y += 84

CARDS = dict(big=card_big, table=card_table, note=card_note, bar=card_bar, cta=card_cta)

# ---------------------------------------------------------------- capa fija
def chrome(img, label):
    d = ImageDraw.Draw(img)
    lg = logo(330)
    img.alpha_composite(lg, (60, 120))
    f = barlow(30, 700)
    tag = "HOY · 19 NOV 2026"
    tw = d.textlength(tag, font=f)
    d.rounded_rectangle([W - 60 - tw - 32, 150, W - 60, 200], 10, fill=RED)
    d.text((W - 60 - tw - 16, 154), tag, font=f, fill=WHT)
    f2 = barlow(26, 700)
    d.text((60, 120 + lg.height + 14), label, font=f2, fill=(232, 226, 245))

def scene_layer(sc, hl_on=True, card=True):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    if card:
        CARDS[sc["card"]["type"]](img, sc["card"])
    caption(img, sc["cap"], hl_on=hl_on)
    return img

# ---------------------------------------------------------------- versión con voz
VOZ_DIR = "/home/user/gamer-al-dia/voz/v2"
VOZ_LUFS = -14.0
DUCK_DB = 4.0               # la música baja 4 dB extra mientras habla la voz
PRE, POST, MIN_ESC = 0.15, 0.25, 2.0

def _norm(w):
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", w.lower()) if unicodedata.category(c)[0] in "LN" or c == " ")

# v3: subtítulos que cambian porque cambió la frase dicha (clave = (video, escena))
SINONIMOS = {"nube": "cloud"}
CAP_V3 = {(2, 0): "Ya hay nota para *GTA 6*", (3, 4): "¿Y en PC? *No hay* versión anunciada"}

def retime(v, n):
    """Ajusta cada escena a la duración real de su frase: PRE + voz + POST (mín. MIN_ESC).
    Añade a cada escena voz_t (inicio de la frase) y kw_t (momento estimado en que se dice la palabra clave)."""
    import json, copy
    info = json.load(open(os.path.join(VOZ_DIR, "tiempos.json"), encoding="utf8"))
    info = info.get("videos", info)[str(n)]
    v2 = copy.deepcopy(v); t = 0.0; old = []
    for k, (sc, fr) in enumerate(zip(v2["scenes"], info)):
        if SUFIJO == "_v3" and (n, k) in CAP_V3: sc["cap"] = CAP_V3[(n, k)]
        d = max(PRE + fr["dur"] + POST, MIN_ESC)
        if k == len(info) - 1: d += 0.8                                  # cierre con el logo
        old.append((sc["t0"], sc["t1"], t, t + d))
        sc["t0"], sc["t1"] = round(t, 3), round(t + d, 3)
        sc["voz_t"], sc["voz_dur"], sc["voz_wav"], sc["voz_texto"] = t + PRE, fr["dur"], fr["wav"], fr["texto"]
        # palabra clave = primer tramo entre *asteriscos* del subtítulo; se busca en la frase dicha
        m = re.search(r"\*([^*]+)\*", sc["cap"])
        frac = 0.0
        if m:
            kw = _norm(m.group(1).replace("_", " ")).split()
            kw = [SINONIMOS.get(w, w) for w in kw]                       # p. ej. subtítulo "nube" / voz "Cloud"
            txt = _norm(fr["texto"])
            pos = txt.find(kw[0]) if kw else -1
            if pos >= 0: frac = pos / max(len(txt), 1)
            else: frac = 0.8 * m.start() / max(len(sc["cap"]), 1)
        sc["kw_t"] = sc["voz_t"] + frac * fr["dur"] - 0.05
        t += d
    v2["_map"] = old
    return v2

def map_t(v, t_old):
    """Convierte un tiempo de la línea temporal v1 a la nueva (lineal dentro de cada escena)."""
    for a, b, na, nb in v.get("_map", []):
        if a <= t_old <= b: return na + (t_old - a) * (nb - na) / (b - a)
    return t_old

def voz_mix(v, dur, wav):
    """Mezcla voz (-14 LUFS) + música (cama -29 LUFS con ducking de DUCK_DB). Devuelve mediciones."""
    import pyloudnorm as pyln, wave as wv
    w = wv.open(v["scenes"][0]["voz_wav"], "rb"); SRv = w.getframerate(); w.close()   # 22,05 kHz (v2) o 44,1 kHz (v3)
    vt = np.zeros(int((dur + 1) * SRv), np.float32)
    for sc in v["scenes"]:
        w = wv.open(sc["voz_wav"], "rb"); assert w.getframerate() == SRv; s = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767; w.close()
        st = int(sc["voz_t"] * SRv); vt[st:st + len(s)] += s[:len(vt) - st]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ac", "1", "-ar", str(SRv), "-i", "-",
                          "-af", "aresample=48000:resampler=soxr", "-f", "f32le", "-ac", "1", "-ar", "48000", "-"],
                         input=vt.tobytes(), capture_output=True, check=True).stdout
    voice = np.frombuffer(raw, np.float32).astype(np.float64)
    N = int(dur * 48000); voice = np.pad(voice, (0, max(0, N - len(voice))))[:N]
    meter = pyln.Meter(48000)
    st2 = lambda x: np.stack([x, x], 1)                     # la voz va igual en L y R: se mide en estéreo
    def limitar(x):                                          # limitador de picos a -2 dBFS
        r = subprocess.run(["ffmpeg", "-v", "error", "-f", "f64le", "-ac", "1", "-ar", "48000", "-i", "-", "-af",
                            "alimiter=limit=0.79:attack=2:release=60:level=disabled",
                            "-f", "f64le", "-ac", "1", "-ar", "48000", "-"], input=x.tobytes(), capture_output=True, check=True).stdout
        return np.frombuffer(r, np.float64)[:len(x)]
    for _ in range(3):
        voice = voice * 10 ** ((VOZ_LUFS - meter.integrated_loudness(st2(voice))) / 20)
        voice = limitar(voice)
    # música (ya normalizada a MUSIC_LUFS)
    mus = music_array(v, dur)[:N]
    mus = np.pad(mus, ((0, max(0, N - len(mus))), (0, 0)))
    # ducking suave: envolvente de la voz (ventanas de 10 ms), ataque 120 ms, relajación 450 ms
    hop = 480
    env = np.sqrt(np.convolve(voice ** 2, np.ones(hop) / hop, "same"))[::hop]
    act = (20 * np.log10(env + 1e-9) > -45).astype(float)
    g = np.zeros_like(act); cur = 0.0
    for i, a_ in enumerate(act):
        c = 1 - math.exp(-1 / (12 if a_ > cur else 45)); cur += (a_ - cur) * c; g[i] = cur
    gain = 10 ** (-DUCK_DB * np.repeat(g, hop)[:N] / 20)
    mus = mus * gain[:, None]
    mix = mus + voice[:, None]
    pk = np.abs(mix).max()
    if pk > 10 ** (-1.5 / 20): mix *= 10 ** (-1.5 / 20) / pk           # seguridad (no debería actuar)
    speech = np.repeat(act, hop)[:N] > 0.5
    res = dict(voz=meter.integrated_loudness(st2(voice)), voz_pico=20 * np.log10(np.abs(voice).max()),
               musica=meter.integrated_loudness(mus),
               musica_bajo_voz=meter.integrated_loudness(mus[speech]) if speech.sum() > 48000 else float("nan"),
               mezcla=meter.integrated_loudness(mix), pico=20 * np.log10(np.abs(mix).max()))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ac", "2", "-ar", "48000", "-i", "-",
                    "-c:a", "pcm_s24le", wav], input=mix.tobytes(), check=True)
    return res

# ---------------------------------------------------------------- capturas oficiales (opcional)
def cargar_capturas(v):
    """Lee CAPTURAS de guiones_data (si existe) y devuelve las del video v cuya imagen está en imagenes_oficiales/."""
    try:
        from guiones_data import CAPTURAS
    except ImportError:
        return []
    res = []
    for c in CAPTURAS.get(v["file"], []):
        p = os.path.join(IMG_OFICIALES, c["archivo"])
        if not os.path.isfile(p):
            print(f"  [capturas] AVISO: falta {p} -> se omite"); continue
        if os.path.splitext(p)[1].lower() not in (".jpg", ".jpeg", ".png", ".webp"):
            print(f"  [capturas] AVISO: {c['archivo']} no es imagen fija (solo jpg/png/webp) -> se omite"); continue
        if "_map" in v:          # versión con voz: los tiempos de CAPTURAS son de la v1 -> se trasladan
            c = dict(c, t0=map_t(v, c["t0"]), t1=map_t(v, c["t1"]))
            if c["t1"] - c["t0"] > 5.0: c["t1"] = c["t0"] + 5.0
        d = c["t1"] - c["t0"]
        if not (2.0 <= d <= 5.0):
            print(f"  [capturas] AVISO: {c['archivo']} dura {d:.1f} s; debe durar entre 2 y 5 s -> se omite"); continue
        res.append(dict(c, ruta=p, img=Image.open(p).convert("RGB")))
    return res

def credito(img):
    d = ImageDraw.Draw(img)
    f = barlow(34, 700)
    tw = d.textlength(CREDITO_CAPTURAS, font=f)
    x, y = W - 60 - tw - 28, 1500
    d.rounded_rectangle([x, y, W - 60, y + 54], 12, fill=(0, 0, 0, 190))
    d.text((x + 14, y + 6), CREDITO_CAPTURAS, font=f, fill=WHT)

def frame_captura(cap, t):
    """Encuadre propio + zoom lento (Ken Burns). modo 'marco' = recuadro en la zona de tarjeta;
    modo 'fondo' = pantalla completa oscurecida detrás de la tarjeta."""
    src = cap["img"]
    p = (t - cap["t0"]) / (cap["t1"] - cap["t0"])
    p = p * p * (3 - 2 * p)                                        # suavizado
    z0, z1 = cap.get("zoom", (1.05, 1.18))
    z = z0 + (z1 - z0) * p
    fx, fy = cap.get("foco", (0.5, 0.5))                          # punto del encuadre (0..1)
    if cap.get("modo", "marco") == "fondo":
        bw, bh = W, H
    else:
        bw, bh = 940, 720
    r = max(bw / src.width, bh / src.height) * z
    sw, sh = bw / r, bh / r
    cx = min(max(fx * src.width, sw / 2), src.width - sw / 2)
    cy = min(max(fy * src.height, sh / 2), src.height - sh / 2)
    crop = src.crop((int(cx - sw / 2), int(cy - sh / 2), int(cx + sw / 2), int(cy + sh / 2))).resize((bw, bh), Image.LANCZOS)
    return crop.convert("RGBA")

# ---------------------------------------------------------------- audio
def music_array(v, dur):
    return _music(v, dur)[0]

def _music(v, dur):
    import pyloudnorm as pyln
    music = os.path.join(STOCK, v["music"])
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(v.get("music_ss", 0)), "-i", music, "-t", f"{dur:.3f}",
                          "-af", f"afade=t=in:d=0.3,afade=t=out:st={dur-1.5}:d=1.5",
                          "-f", "f32le", "-ac", "2", "-ar", "48000", "-"], capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64)
    meter = pyln.Meter(48000)
    before = meter.integrated_loudness(a)
    a = pyln.normalize.loudness(a, before, MUSIC_LUFS)
    peak = np.abs(a).max()
    if peak > 10 ** (-3 / 20):                                   # nunca debería pasar a -29 LUFS
        a *= 10 ** (-3 / 20) / peak
    after = meter.integrated_loudness(a)
    return a, before, after

def music_track(v, dur, wav):
    """Extrae la música con fundidos, la normaliza a MUSIC_LUFS y limita el pico. Devuelve mediciones."""
    a, before, after = _music(v, dur)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f64le", "-ac", "2", "-ar", "48000", "-i", "-",
                    "-c:a", "pcm_s24le", wav], input=a.astype(np.float64).tobytes(), check=True)
    return before, after, 20 * np.log10(np.abs(a).max())

# ---------------------------------------------------------------- render
def out_name(v, ext=".mp4"):
    return os.path.join(OUT, v["file"].replace(".mp4", SUFIJO + ext))

def render(v, idx, usar_capturas=False, con_voz=False):
    if con_voz:
        v = retime(v, idx + 1)
    dur = v["scenes"][-1]["t1"]
    nframes = int(round(dur * FPS))
    out = out_name(v, "_voz.mp4" if (con_voz and SUFIJO == "_v2") else ".mp4")
    wav = out.replace(".mp4", "_audio_tmp.wav")
    if con_voz:
        m = voz_mix(v, dur, wav)
        print("  mezcla: voz {voz:.1f} LUFS (pico {voz_pico:.1f}) · música {musica:.1f} LUFS (bajo la voz {musica_bajo_voz:.1f}) · "
              "total {mezcla:.1f} LUFS · pico {pico:.1f} dBFS".format(**m))
    else:
        b, a, pk = music_track(v, dur, wav)
        print(f"  música {v['music']}: {b:.1f} LUFS (cruda, con fundidos) -> {a:.1f} LUFS, pico muestra {pk:.1f} dBFS")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                            "-map", "0:v", "-map", "1:a", "-t", f"{dur:.2f}",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-movflags", "+faststart",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], stdin=subprocess.PIPE)
    fondo = Fondo(variant=idx)
    fixed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    grad = np.zeros((H, W, 4), np.uint8)
    grad[..., :3] = PANEL
    al = np.concatenate([np.linspace(190, 0, 420), np.zeros(H - 420)])
    grad[..., 3] = al[:, None].astype(np.uint8)
    fixed = Image.alpha_composite(fixed, Image.fromarray(grad, "RGBA"))
    fixed_cap = fixed.copy()
    chrome(fixed, LABEL_V2)
    chrome(fixed_cap, "")          # durante una captura no se muestra el rótulo "no es imagen del juego"
    layers = [scene_layer(sc) for sc in v["scenes"]]
    # con voz: la palabra clave se resalta cuando se dice (antes va en blanco)
    layers_pre = [scene_layer(sc, hl_on=False) for sc in v["scenes"]] if con_voz else layers
    caps = cargar_capturas(v) if usar_capturas else []
    if caps:
        print(f"  [capturas] se insertan {len(caps)}: " + ", ".join(c["archivo"] for c in caps))
    # capa de subtítulo sola (para modo 'marco': la captura sustituye a la tarjeta, el subtítulo se mantiene)
    cap_layers = []
    for sc in v["scenes"]:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); caption(im, sc["cap"]); cap_layers.append(im)
    cap_layers_pre = [scene_layer(sc, hl_on=False, card=False) for sc in v["scenes"]] if (con_voz and caps) else cap_layers
    bar = gradient_stops(W, [(0, MAG), (0.5, ROSA), (0.8, NAR), (1, ORO)]).astype(np.uint8)
    for i in range(nframes):
        t = i / FPS
        frame = fondo.frame(t, i)
        k = next(j for j, sc in enumerate(v["scenes"]) if t < sc["t1"] or j == len(v["scenes"]) - 1)
        sc = v["scenes"][k]
        cap = next((c for c in caps if c["t0"] <= t < c["t1"]), None)
        if cap is not None and cap.get("modo", "marco") == "fondo":
            ci = frame_captura(cap, t)
            dark = Image.new("RGBA", (W, H), (0, 0, 0, 110))
            frame = Image.alpha_composite(ci, dark)
        frame.alpha_composite(fixed_cap if cap is not None else fixed)
        lt = t - sc["t0"]
        pre = con_voz and t < sc.get("kw_t", 0)
        if cap is not None and cap.get("modo", "marco") == "marco":
            lay = (cap_layers_pre if pre else cap_layers)[k].copy()
            ci = frame_captura(cap, t)
            x0, y0 = (W - ci.width) // 2, 370
            nd = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ImageDraw.Draw(nd).rounded_rectangle(
                [x0 - 6, y0 - 6, x0 + ci.width + 6, y0 + ci.height + 6], 22, outline=MAG + (255,), width=6)
            frame.alpha_composite(glow(nd, 14, 1))
            mask = Image.new("L", ci.size, 0); ImageDraw.Draw(mask).rounded_rectangle([0, 0, ci.width - 1, ci.height - 1], 18, fill=255)
            ci.putalpha(mask)
            frame.alpha_composite(ci, (x0, y0))
        else:
            lay = (layers_pre if pre else layers)[k]
        if k > 0 and lt < 0.2:
            p = lt / 0.2
            off = int(40 * (1 - p))
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            tmp.paste(lay, (0, off))
            arr = np.array(tmp); arr[..., 3] = (arr[..., 3] * p).astype(np.uint8)
            lay = Image.fromarray(arr, "RGBA")
        frame.alpha_composite(lay)
        if cap is not None:
            credito(frame)
        rgb = np.array(frame.convert("RGB"))
        pw = int(W * (t / dur))
        rgb[0:14, :pw] = bar[:pw]
        enc.stdin.write(rgb.tobytes())
    enc.stdin.close(); enc.wait()
    os.remove(wav)
    print("ok", out, dur)

# ---------------------------------------------------------------- miniatura
def neon_text(img, xy, text, font, fill_grad=None, fill=WHT, glow_col=MAG, stroke=8):
    """Texto con resplandor neón; fill_grad = lista de stops para relleno en degradado vertical."""
    x, y = xy
    d = ImageDraw.Draw(img)
    bb = d.textbbox((x, y), text, font=font, stroke_width=stroke)
    gl = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(gl).text((x, y), text, font=font, fill=glow_col + (255,), stroke_width=stroke + 6, stroke_fill=glow_col + (255,))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(28)))
    img.alpha_composite(gl.filter(ImageFilter.GaussianBlur(10)))
    d = ImageDraw.Draw(img)
    d.text((x, y), text, font=font, fill=INK, stroke_width=stroke, stroke_fill=INK)
    if fill_grad:
        m = Image.new("L", img.size, 0); ImageDraw.Draw(m).text((x, y), text, font=font, fill=255)
        h0, h1 = bb[1], bb[3]
        g = gradient_stops(h1 - h0 + 1, fill_grad).astype(np.uint8)
        col = np.zeros((img.size[1], img.size[0], 4), np.uint8)
        col[h0:h1 + 1, :, :3] = g[:, None, :]
        col[..., 3] = np.array(m)
        img.alpha_composite(Image.fromarray(col, "RGBA"))
    else:
        d.text((x, y), text, font=font, fill=fill)

def thumb(v, idx):
    th = v["thumb"]
    img = Fondo(variant=idx).frame(0.7, 0)
    # oscurecer la zona del texto para que destaque
    sh = np.zeros((H, W, 4), np.uint8); sh[..., :3] = PANEL
    al = np.concatenate([np.linspace(200, 120, 500), np.full(900, 120), np.linspace(120, 0, H - 1400)])
    sh[..., 3] = al[:, None].astype(np.uint8)
    img = Image.alpha_composite(img, Image.fromarray(sh, "RGBA"))
    lg = logo(560)
    img.alpha_composite(lg, ((W - lg.width) // 2, 150))
    d = ImageDraw.Draw(img)
    y = 560
    for t, s, c, bgc in th:
        f = fit_font(d, t, anton, s, 940)
        bb = d.textbbox((0, 0), t, font=f)
        h = bb[3] - bb[1]
        tw = d.textlength(t, font=f)
        x = (W - tw) / 2
        if bgc == YEL:      # línea principal: relleno degradado atardecer + resplandor magenta
            neon_text(img, (x, y - bb[1]), t, f, fill_grad=[(0, ORO), (0.45, NAR), (0.75, ROSA), (1, MAG)], glow_col=MAG, stroke=10)
        elif bgc == RED:    # tercera línea: caja roja de marca con borde neón
            box = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ImageDraw.Draw(box).rectangle([x - 30, y - 20, x + tw + 30, y + h + 30], outline=ROSA + (255,), width=8)
            img.alpha_composite(box.filter(ImageFilter.GaussianBlur(14)))
            d = ImageDraw.Draw(img)
            d.rectangle([x - 30, y - 20, x + tw + 30, y + h + 30], fill=RED)
            d.text((x, y - bb[1]), t, font=f, fill=WHT)
        else:
            neon_text(img, (x, y - bb[1]), t, f, fill=WHT, glow_col=MAG, stroke=7)
        d = ImageDraw.Draw(img)
        y += h + 70
    out = out_name(v, "_miniatura.png")
    img.convert("RGB").save(out)
    print("ok", out)

if __name__ == "__main__":
    sys.path.insert(0, BASE)
    from guiones_data import VIDEOS
    args = sys.argv[1:]
    usar_capturas = "--capturas" in args
    con_voz = "--voz" in args or "--voz3" in args
    if "--voz3" in args:
        SUFIJO = "_v3"; VOZ_DIR = "/home/user/gamer-al-dia/voz/v3"
    solo_thumb = "--solo-miniaturas" in args
    sel = [a for a in args if not a.startswith("--")] or ["1", "2", "3"]
    for s in sel:
        i = int(s) - 1
        v = VIDEOS[i]
        thumb(v, i)
        if not solo_thumb:
            render(v, i, usar_capturas, con_voz)
