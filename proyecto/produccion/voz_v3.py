#!/usr/bin/env python3
"""Voz v3: Supertonic 3, voz HOMBRE (sid 7), más pausada que la muestra (Mateo: "va muy rápido").
Uso:  python3 -I /home/user/gamer-al-dia/produccion/voz_v3.py [SPEED]        (por defecto SPEED)
Una frase por escena (GUION_V3, abajo). Cada frase se sintetiza N_CAND veces (el modelo no es
determinista) y se guarda la que Whisper-small transcribe con menos errores; se recortan los silencios de los
extremos y las pausas internas largas se acortan (sin tocar el habla). Salida en /home/user/gamer-al-dia/voz/v3/:
video{n}_esc{k}.wav (44,1 kHz mono) + tiempos.json (duración real de cada frase). render.py --voz3 lo usa.
El texto que se lee solo cambia la escritura de siglas, anglicismos y números para que se pronuncien bien.
"""
import re, json, os, sys, wave
import numpy as np, sherpa_onnx as s

M = "/tmp/claude-0/tts/m/sherpa-onnx-supertonic-3-tts-int8-2026-05-11/"
OUTD = "/home/user/gamer-al-dia/voz/v3"
SID = 7                 # Supertonic 3 "M_hombre" elegida por Mateo (muestras/supertonic3_M_hombre.mp3)
SPEED = 0.90            # muestra a 1.10 = 203 palabras/min; barrido 0.88/0.94/1.0 = 166/179/187 ppm -> 0.90 ≈ 170
STEPS = 8
PAUSA_MAX, PAUSA_DEJA = 0.34, 0.28   # pausas internas > 340 ms se dejan en 280 ms (comas/puntos naturales)

# Guion v3 (una línea por escena; mismo orden que guiones_data.VIDEOS). El video 2 se acortó para que
# quepa en 59 s a ritmo más lento (mismos datos).
GUION_V3 = {
    1: ["¿Ya puedes jugar GTA 6?",
        "Sí: se desbloqueó a las doce de la noche, hora local, del 19 de noviembre.",
        "En PS5 y Xbox Series, según el soporte de Rockstar.",
        "Pero no fue a la vez: Nueva Zelanda abrió primero. España, después. Y Latinoamérica, horas más tarde.",
        "Nueva Zelanda jugó casi 19 horas antes que Ciudad de México.",
        "Dato curioso: cuando en España ya jugaban, en México eran las cinco de la tarde del día anterior.",
        "Ojo: en PS5 manda la región de tu cuenta, no el país donde estás. Si no te abre, revisa eso y que la descarga haya terminado.",
        "Mi consejo: fueron años de espera, unas horas no cambian nada. Juega cuando te toque y silencia los spoilers.",
        "Sigue a Gamer al Día: noticias gamer en 30 segundos."],
    2: ["Ya hay nota para GTA 6... y es un 99.",
        "Un 99 en Metacritic, con unas 150 reseñas de prensa.",
        "Así empata el récord de Zelda: Ocarina of Time, de 1998.",
        "¿Lo más criticado? Va a 30 cuadros por segundo, sin modo a 60, ni en PS5 Pro.",
        "En las pruebas de prensa, la PS5 Pro aguanta 30 estables. La PS5 normal y la Series X bajan en escenas pesadas, y la Series S, a ratos, se queda en 20 y pico.",
        "Y su realismo, con coches frágiles y reparaciones, pide paciencia si vienes de GTA 5.",
        "Mi lectura: el 99 es real, pero califica el juego, no tu consola.",
        "Y ojo: siguen llegando reseñas, así que la nota puede moverse.",
        "¿Tú le das un 10 o es puro hype? Te leo en comentarios."],
    3: ["¿Te cabe GTA 6? Porque pide hasta 212 gigas.",
        "Rockstar pide hasta 212 GB libres, según la consola.",
        "Y solo sale en PS5 y Xbox Series X y Series S.",
        "En una Series S, que trae 364 GB útiles, se come más de la mitad del disco. Te quedan unos 152 para todo lo demás.",
        "¿Y en PC? No hay versión anunciada, y Take-Two no da fecha.",
        "En Xbox One, solo por Xbox Cloud Gaming, desde la una de la mañana, hora del Este de Estados Unidos, del 19 de noviembre. El juego se compra aparte.",
        "Mi consejo: revisa tu espacio antes de pagar. En Series S, borra lo que no juegas o usa la tarjeta de expansión oficial.",
        "Y deja margen, porque van a llegar actualizaciones.",
        "Sigue a Gamer al Día."],
}

# ---- números a palabras (es), para que el modelo no los lea mal
U = "cero uno dos tres cuatro cinco seis siete ocho nueve diez once doce trece catorce quince dieciséis diecisiete dieciocho diecinueve veinte veintiuno veintidós veintitrés veinticuatro veinticinco veintiséis veintisiete veintiocho veintinueve".split()
D = {3: "treinta", 4: "cuarenta", 5: "cincuenta", 6: "sesenta", 7: "setenta", 8: "ochenta", 9: "noventa"}
C = {1: "ciento", 2: "doscientos", 3: "trescientos", 4: "cuatrocientos", 5: "quinientos", 6: "seiscientos",
     7: "setecientos", 8: "ochocientos", 9: "novecientos"}

def num(n):
    if n < 30: return U[n]
    if n < 100: return D[n // 10] + ("" if n % 10 == 0 else " y " + U[n % 10])
    if n == 100: return "cien"
    if n < 1000: return C[n // 100] + ("" if n % 100 == 0 else " " + num(n % 100))
    if n < 2000: return "mil" + ("" if n % 1000 == 0 else " " + num(n % 1000))
    return num(n // 1000) + " mil" + ("" if n % 1000 == 0 else " " + num(n % 1000))

# Cada regla tiene variantes; el candidato i usa la variante i % len (ver main: se elige el mejor por Whisper).
FONETICA = [
    (r"\bGTA 6\b", ["ge te a seis", "gé té á seis", "jeteá seis"]), (r"\bGTA 5\b", ["ge te a cinco", "gé té á cinco"]),
    (r"\bPS5\b", ["pe ese cinco", "PS cinco", "pé ése cinco"]),
    (r"\bXbox Cloud Gaming\b", ["equis box claud guéiming"]), (r"\bSeries X y Series S\b", ["Series equis y Series S"]),
    (r"\bXbox\b", ["equis box"]), (r"\bSeries X\b", ["Series equis"]),
    (r"(\d+) GB\b", [r"\1 gigas"]), (r"\bRockstar\b", ["Rókstar"]),
    (r"\bGamer al Día\b", ["Guéimer al Día"]), (r"\bnoticias gamer\b", ["noticias guéimer"]),
    (r"\bspoilers\b", ["espóilers"]), (r"\bhype\b", ["jáip"]), (r"\bOcarina of Time\b", ["Ocarina of Táim"]),
    (r"\bZelda:", ["Zelda,"]),
]   # "Take-Two", "PC" y "Series S" se dejan tal cual: en las pruebas se entendían mejor así.

def fonetica(t, i=0):
    for a, b in FONETICA:
        t = re.sub(a, b[i % len(b)], t)
    return re.sub(r"\d+", lambda m: num(int(m.group())), t)

def tts():
    return s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
        supertonic=s.OfflineTtsSupertonicModelConfig(
            duration_predictor=M + "duration_predictor.int8.onnx", text_encoder=M + "text_encoder.int8.onnx",
            vector_estimator=M + "vector_estimator.int8.onnx", vocoder=M + "vocoder.int8.onnx",
            tts_json=M + "tts.json", unicode_indexer=M + "unicode_indexer.bin", voice_style=M + "voice.bin"),
        num_threads=4)))

def pausas(x, sr, umbral_db=-40):
    """Recorta silencios de los extremos (deja 40/90 ms) y acorta pausas internas largas con fundido."""
    win = int(sr * 0.01); n = len(x) // win
    rms = np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    sil = 20 * np.log10(rms / (np.max(np.abs(x)) + 1e-9)) < umbral_db
    voiced = np.where(~sil)[0]
    a, b = max(voiced[0] * win - int(0.04 * sr), 0), min((voiced[-1] + 1) * win + int(0.09 * sr), len(x))
    x, sil = x[a:b], sil[a // win:(b + win - 1) // win]
    out, i, n = [], 0, len(sil)
    while i < n:
        j = i
        while j < n and sil[j] == sil[i]: j += 1
        seg = x[i * win:(j * win if j < n else len(x))]
        if sil[i] and 0 < i and j < n and len(seg) > PAUSA_MAX * sr:
            keep = int(PAUSA_DEJA * sr); h = keep // 2; f = np.linspace(1, 0, 256)
            l, r = seg[:h].copy(), seg[-(keep - h):].copy(); l[-256:] *= f; r[:256] *= f[::-1]
            seg = np.concatenate([l, r])
        out.append(seg); i = j
    return np.concatenate(out)

N_CAND = 6   # candidatos por frase (el modelo no es determinista): se queda el que Whisper entiende mejor

def main(speed=SPEED, outd=OUTD, videos=(1, 2, 3)):
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import asr_v3 as A
    os.makedirs(outd, exist_ok=True)
    t = tts(); r = A.rec(); info = {}
    tmp = os.path.join(outd, "_cand.wav")
    for n in videos:
        info[n] = []
        for k, txt in enumerate(GUION_V3[n]):
            cands = []
            for i in range(N_CAND):
                g = s.GenerationConfig(); g.sid = SID; g.speed = speed; g.num_steps = STEPS
                g.silence_scale = 0.2; g.extra = {"lang": "es"}
                a = t.generate(fonetica(txt, i), g); sr = a.sample_rate
                x = pausas(np.array(a.samples, dtype=np.float32), sr)
                guardar(tmp, x, sr)
                hyp = A.transcribe(r, tmp); w, ops = A.wer_ops(A.norm(txt), A.norm(hyp))
                cands.append(dict(x=x, sr=sr, wer=w, ops=ops, hyp=hyp, tts=fonetica(txt, i), dur=len(x) / sr))
            med = float(np.median([c["dur"] for c in cands]))
            best = min(cands, key=lambda c: (round(c["wer"], 3), abs(c["dur"] - med)))
            p = os.path.join(outd, f"video{n}_esc{k}.wav"); guardar(p, best["x"], best["sr"])
            pal = len(re.findall(r"\w+", txt.replace("GTA 6", "GTA6").replace("GTA 5", "GTA5")))
            info[n].append(dict(texto=txt, tts=best["tts"], wav=p, sr=best["sr"], dur=round(best["dur"], 3), palabras=pal,
                                asr=best["hyp"], wer=round(best["wer"], 3), dif=best["ops"],
                                wer_candidatos=[round(c["wer"], 3) for c in cands]))
            print(n, k, f"{best['dur']:.2f}s", f"{pal/best['dur']*60:.0f} ppm", f"WER {best['wer']:.0%}",
                  [f"{c['wer']:.0%}" for c in cands], "|", best["hyp"], flush=True)
    os.remove(tmp)
    json.dump(dict(motor="Supertonic 3 int8 (sherpa-onnx 1.12.40)", sid=SID, speed=speed, steps=STEPS, n_cand=N_CAND,
                   videos=info), open(os.path.join(outd, "tiempos.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    return info

def guardar(p, x, sr):
    w = wave.open(p, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

if __name__ == "__main__":
    main(float(sys.argv[1]) if len(sys.argv) > 1 else SPEED)
