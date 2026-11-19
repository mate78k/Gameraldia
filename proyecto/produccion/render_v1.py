#!/usr/bin/env python3
"""Gamer al Día - renderizador de shorts verticales 1080x1920 (material propio + stock Mixkit).
Uso: python3 render.py [id]   (id = 1, 2 o 3; sin id renderiza los tres)
"""
import subprocess, sys, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = "/home/user/gamer-al-dia/videos"
FDIR = os.path.join(BASE, "fuentes")
STOCK = os.path.join(BASE, "stock")
LOGO = "/home/user/gamer-al-dia/logo/logo_opcion_A_mando_rayo_transparente.png"
W, H, FPS = 1080, 1920, 30

INK = (11, 13, 18); INK2 = (22, 26, 35); RED = (255, 46, 77); YEL = (255, 212, 0); WHT = (255, 255, 255)
GREY = (200, 204, 214)

def anton(s): return ImageFont.truetype(os.path.join(FDIR, "anton-latin-400-normal.woff2"), s)
def barlow(s, w=800): return ImageFont.truetype(os.path.join(FDIR, f"barlow-condensed-latin-{w}-normal.woff2"), s)

_logo = Image.open(LOGO).convert("RGBA")
_logo = _logo.crop(_logo.getbbox())

def logo(width):
    r = width / _logo.width
    return _logo.resize((width, int(_logo.height * r)), Image.LANCZOS)

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

def caption(img, text, y_center=1290, size=88, maxw=900):
    """Subtítulo grande; palabras entre *asteriscos* van resaltadas en amarillo."""
    d = ImageDraw.Draw(img)
    f = barlow(size, 800)
    text = text.upper()
    # marcar palabras clave (soporta *dos palabras*)
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
    sp = d.textlength(" ", font=f)
    for words, hls in lines:
        tw = d.textlength(" ".join(words), font=f)
        x = (W - tw) / 2
        for w, h in zip(words, hls):
            ww = d.textlength(w, font=f)
            if h:
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
def panel(d, box, fill=INK, outline=None):
    d.rounded_rectangle(box, 28, fill=fill + (232,), outline=outline, width=6 if outline else 0)

def card_big(img, spec):
    """spec: lines=[(texto, tam, color, fuente)] centrado verticalmente en zona 360-1100."""
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
    for t, f, c, h, off in items:
        center_text(d, y - off, t, f, c, stroke=0)
        y += h + gap

def card_table(img, spec):
    d = ImageDraw.Draw(img)
    rows = spec["rows"]
    title = spec["title"]
    rh = 112
    top = 730 - (130 + rh * len(rows)) // 2
    panel(d, [60, top - 40, W - 60, top + 130 + rh * len(rows) + 30])
    ft = fit_font(d, title, lambda z: barlow(z, 800), 60, 900)
    center_text(d, top, title, ft, YEL)
    y = top + 120
    for i, (a, b, c) in enumerate(rows):
        if i % 2 == 0:
            d.rounded_rectangle([90, y - 6, W - 90, y + rh - 14], 16, fill=INK2)
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
    tag = spec["tag"]
    tw = d.textlength(tag, font=f_t)
    d.rounded_rectangle([(W - tw) / 2 - 24, top - 8, (W + tw) / 2 + 24, top + 78], 12, fill=spec.get("tagcolor", RED))
    center_text(d, top - 4, tag, f_t, WHT if spec.get("tagcolor", RED) == RED else INK)
    y = top + 110
    for l in body:
        center_text(d, y, l, f_b, WHT)
        y += lh

def card_bar(img, spec):
    """Barra de ocupación de disco."""
    d = ImageDraw.Draw(img)
    top = 470
    panel(d, [60, top - 40, W - 60, top + 560])
    center_text(d, top, spec["title"], barlow(62, 800), YEL)
    x0, x1, yb = 110, W - 110, top + 150
    d.rounded_rectangle([x0, yb, x1, yb + 120], 20, fill=INK2, outline=GREY, width=4)
    frac = spec["used"] / spec["total"]
    d.rounded_rectangle([x0, yb, x0 + (x1 - x0) * frac, yb + 120], 20, fill=RED)
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
    d.text((60, 120 + lg.height + 14), label, font=f2, fill=(220, 224, 232))

def scene_layer(sc, label):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    CARDS[sc["card"]["type"]](img, sc["card"])
    caption(img, sc["cap"])
    return img

# ---------------------------------------------------------------- render
def render(v):
    dur = v["scenes"][-1]["t1"]
    nframes = int(round(dur * FPS))
    bg_cmd = ["ffmpeg", "-v", "error", "-stream_loop", "-1", "-i", os.path.join(STOCK, v["bg"]),
              "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},"
                     f"gblur=sigma=6,eq=brightness=-0.18:saturation=1.15,fps={FPS}",
              "-frames:v", str(nframes), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    bg = subprocess.Popen(bg_cmd, stdout=subprocess.PIPE)
    out = os.path.join(OUT, v["file"])
    music = os.path.join(STOCK, v["music"])
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                            "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                            "-ss", str(v.get("music_ss", 0)), "-i", music,
                            "-filter_complex", f"[1:a]volume={v.get('vol',0.55)},afade=t=in:d=0.3,afade=t=out:st={dur-1.5}:d=1.5[a]",
                            "-map", "0:v", "-map", "[a]", "-t", f"{dur:.2f}",
                            "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
                            "-profile:v", "high", "-movflags", "+faststart",
                            "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out], stdin=subprocess.PIPE)
    fixed = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # viñeta inferior/superior para legibilidad
    grad = np.zeros((H, W, 4), np.uint8)
    a = np.concatenate([np.linspace(170, 0, 380), np.zeros(H - 380 - 700), np.linspace(0, 200, 700)])
    grad[..., 3] = a[:, None].astype(np.uint8)
    fixed = Image.alpha_composite(fixed, Image.fromarray(grad, "RGBA"))
    chrome(fixed, v["label"])
    layers = [scene_layer(sc, v["label"]) for sc in v["scenes"]]
    fsize = W * H * 3
    for i in range(nframes):
        t = i / FPS
        raw = bg.stdout.read(fsize)
        if len(raw) < fsize: raise SystemExit("fondo corto")
        frame = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1).convert("RGBA")
        frame.alpha_composite(fixed)
        k = next(j for j, sc in enumerate(v["scenes"]) if t < sc["t1"] or j == len(v["scenes"]) - 1)
        sc = v["scenes"][k]
        lt = t - sc["t0"]
        lay = layers[k]
        if k > 0 and lt < 0.2:  # entrada: sube 40 px y aparece
            p = lt / 0.2
            off = int(40 * (1 - p))
            tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            tmp.paste(lay, (0, off))
            arr = np.array(tmp); arr[..., 3] = (arr[..., 3] * p).astype(np.uint8)
            lay = Image.fromarray(arr, "RGBA")
        frame.alpha_composite(lay)
        # barra de progreso
        d = ImageDraw.Draw(frame)
        d.rectangle([0, 0, int(W * (t / dur)), 14], fill=RED)
        enc.stdin.write(frame.convert("RGB").tobytes())
    enc.stdin.close(); enc.wait(); bg.wait()
    print("ok", out, dur)

# ---------------------------------------------------------------- miniatura
def thumb(v):
    th = v["thumb"]
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", "2", "-i", os.path.join(STOCK, v["bg"]), "-frames:v", "1",
                          "-vf", f"scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},gblur=sigma=8,eq=brightness=-0.25",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    img = Image.frombuffer("RGB", (W, H), raw, "raw", "RGB", 0, 1).convert("RGBA")
    d = ImageDraw.Draw(img)
    lg = logo(560)
    img.alpha_composite(lg, ((W - lg.width) // 2, 170))
    y = 560
    for t, s, c, bgc in th:
        f = fit_font(d, t, anton, s, 940)
        bb = d.textbbox((0, 0), t, font=f)
        h = bb[3] - bb[1]
        tw = d.textlength(t, font=f)
        if bgc:
            d.rectangle([(W - tw) / 2 - 30, y - 20, (W + tw) / 2 + 30, y + h + 30], fill=bgc)
        d.text(((W - tw) / 2, y - bb[1]), t, font=f, fill=c, stroke_width=0 if bgc else 6, stroke_fill=INK)
        y += h + 70
    out = os.path.join(OUT, v["file"].replace(".mp4", "_miniatura.png"))
    img.convert("RGB").save(out)
    print("ok", out)

if __name__ == "__main__":
    sys.path.insert(0, BASE)
    from guiones_data import VIDEOS
    sel = sys.argv[1:] or ["1", "2", "3"]
    for s in sel:
        v = VIDEOS[int(s) - 1]
        thumb(v)
        render(v)
