#!/usr/bin/env python3
"""Genera la voz (Piper es_MX-claude-high vía sherpa-onnx) frase por frase para la v2 con voz.
Uso: python3 -I /home/user/gamer-al-dia/produccion/voz_v2.py
Lee el guion (columna "Guion para leer") de videos/guiones.md, una frase por escena, y guarda en
/home/user/gamer-al-dia/voz/v2/: video{n}_esc{k}.wav (22,05 kHz mono) + tiempos.json (duración de cada frase).
El texto se adapta solo para la pronunciación (siglas y anglicismos); el contenido no cambia.
"""
import re, json, os, wave
import numpy as np, sherpa_onnx

D = "/tmp/claude-0/tts/vits-piper-es_MX-claude-high/"
OUTD = "/home/user/gamer-al-dia/voz/v2"
GUION = "/home/user/gamer-al-dia/videos/guiones.md"
SPEED = 1.10            # nunca más de ~1.15: si no cabe, se alarga la escena
SR = 22050

# solo pronunciación (orden importa)
FONETICA = [
    (r"\bGTA 6\b", "ge te a seis"), (r"\bGTA 5\b", "ge te a cinco"),
    (r"\bPS5 Pro\b", "pe ese cinco pro"), (r"\bPS5\b", "pe ese cinco"),
    (r"\bXbox Cloud Gaming\b", "equis box claud guéiming"), (r"\bXbox\b", "equis box"),
    (r"\bSeries X\b", "Series equis"), (r"\bSeries S\b", "Series ese"),
    (r"(\d+) GB\b", r"\1 gigas"), (r"\bTake-Two\b", "Téik Tú"), (r"\bRockstar\b", "Rókstar"),
    (r"\bGamer al Día\b", "Guéimer al Día"), (r"\bnoticias gamer\b", "noticias guéimer"),
    (r"\bspoilers\b", "espóilers"), (r"\bhype\b", "jáip"), (r"\bOcarina of Time\b", "Ocarina of Táim"),
    (r"\bMetacritic\b", "Métacritic"),
]

def lineas():
    md = open(GUION, encoding="utf8").read()
    parts = re.split(r"\n## Video (\d): ", md)
    res = {}
    for i in range(1, len(parts), 2):
        n = int(parts[i]); body = parts[i + 1]
        rows = re.findall(r"^\| ([\d,]+)-([\d,]+) \|.*?\| (.*?) \|$", body, re.M)
        res[n] = [re.sub(r"\s*\(gancho\)", "", t.replace("**", "").replace("\\|", "|")).strip() for a, b, t in rows]
    return res

def fonetica(t):
    for a, b in FONETICA:
        t = re.sub(a, b, t)
    return t

def main():
    os.makedirs(OUTD, exist_ok=True)
    cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
        vits=sherpa_onnx.OfflineTtsVitsModelConfig(model=D + "es_MX-claude-high.onnx", tokens=D + "tokens.txt",
                                                   data_dir=D + "espeak-ng-data"), num_threads=4))
    tts = sherpa_onnx.OfflineTts(cfg)
    info = {}
    for n, ls in lineas().items():
        info[n] = []
        for k, t in enumerate(ls):
            s = np.array(tts.generate(fonetica(t), sid=0, speed=SPEED).samples, dtype=np.float32)
            # recorta silencios de los extremos (umbral -45 dBFS)
            idx = np.where(np.abs(s) > 10 ** (-45 / 20))[0]
            s = s[max(idx[0] - 220, 0): idx[-1] + 660]
            p = os.path.join(OUTD, f"video{n}_esc{k}.wav")
            w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
            w.writeframes((np.clip(s, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()
            info[n].append(dict(texto=t, tts=fonetica(t), wav=p, dur=round(len(s) / SR, 3)))
            print(n, k, f"{len(s)/SR:.2f}s", t)
    json.dump(info, open(os.path.join(OUTD, "tiempos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

if __name__ == "__main__":
    main()
