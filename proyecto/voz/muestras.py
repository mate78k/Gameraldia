"""Genera la misma muestra con cada candidato TTS, la post-procesa y mide.
Uso: python3 -I muestras.py [solo_raw]
"""
import sys, os, re, json, subprocess, wave
import numpy as np, sherpa_onnx as s

M = "/tmp/claude-0/tts/m/"
RAW = "/tmp/claude-0/tts/raw/"
OUT = "/home/user/gamer-al-dia/voz/muestras/"
os.makedirs(RAW, exist_ok=True); os.makedirs(OUT, exist_ok=True)

ORIGINAL = ("¿Ya puedes jugar GTA 6? Sí: se desbloqueó a las doce de la noche, hora local, del 19 de "
            "noviembre, en PS5 y Xbox Series. Pero ojo: no fue a la vez, Nueva Zelanda abrió primero, "
            "casi diecinueve horas antes que Ciudad de México.")

# Texto normalizado para TTS: siglas deletreadas, números en letra, puntuación pensada para ritmo
# (comas = respiraciones cortas; un solo punto fuerte en mitad).
TEXTO = ("¿Ya puedes jugar ge te a seis? ¡Sí! Se desbloqueó a las doce de la noche, hora local, "
         "del diecinueve de noviembre, en pe ese cinco y equis box series. Pero ojo, no fue a la vez: "
         "Nueva Zelanda abrió primero, casi diecinueve horas antes que Ciudad de México.")
PALABRAS = len(re.findall(r"\w+", ORIGINAL))  # palabras del guion original (GTA, 6, PS5 cuentan 1)

NT = 4

def piper(name, onnx):
    d = M + name + "/"
    return s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
        vits=s.OfflineTtsVitsModelConfig(model=d + onnx, tokens=d + "tokens.txt", data_dir=d + "espeak-ng-data"),
        num_threads=NT)))

def kokoro():
    d = M + "kokoro-multi-lang-v1_0/"
    return s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
        kokoro=s.OfflineTtsKokoroModelConfig(model=d + "model.onnx", voices=d + "voices.bin", tokens=d + "tokens.txt",
                                            data_dir=d + "espeak-ng-data", dict_dir=d + "dict",
                                            lexicon=d + "lexicon-us-en.txt", lang="es-419"),
        num_threads=NT)))

def supertonic():
    d = M + "sherpa-onnx-supertonic-3-tts-int8-2026-05-11/"
    return s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
        supertonic=s.OfflineTtsSupertonicModelConfig(
            duration_predictor=d + "duration_predictor.int8.onnx", text_encoder=d + "text_encoder.int8.onnx",
            vector_estimator=d + "vector_estimator.int8.onnx", vocoder=d + "vocoder.int8.onnx",
            tts_json=d + "tts.json", unicode_indexer=d + "unicode_indexer.bin", voice_style=d + "voice.bin"),
        num_threads=NT)))

# (archivo, constructor, sid, speed, extra)
CANDIDATOS = [
    ("kokoro_v1_ef_dora_mujer",        kokoro,     28, 1.10, None),
    ("kokoro_v1_em_alex_hombre",       kokoro,     29, 1.10, None),
    ("supertonic3_F_mujer",            supertonic, None, 1.10, {"lang": "es"}),   # sid se fija abajo
    ("supertonic3_M_hombre",           supertonic, None, 1.10, {"lang": "es"}),
    ("piper_es_AR_daniela_mujer",      lambda: piper("vits-piper-es_AR-daniela-high", "es_AR-daniela-high.onnx"), 0, 1.10, None),
    ("piper_es_MX_ald_hombre",         lambda: piper("vits-piper-es_MX-ald-medium", "es_MX-ald-medium.onnx"), 0, 1.10, None),
    ("piper_es_ES_sharvard_mujer",     lambda: piper("vits-piper-es_ES-sharvard-medium", "es_ES-sharvard-medium.onnx"), 1, 1.10, None),
    ("piper_es_ES_sharvard_hombre",    lambda: piper("vits-piper-es_ES-sharvard-medium", "es_ES-sharvard-medium.onnx"), 0, 1.10, None),
    ("piper_es_MX_claude_REFERENCIA_actual", lambda: s.OfflineTts(s.OfflineTtsConfig(model=s.OfflineTtsModelConfig(
        vits=s.OfflineTtsVitsModelConfig(model="/tmp/claude-0/tts/vits-piper-es_MX-claude-high/es_MX-claude-high.onnx",
                                         tokens="/tmp/claude-0/tts/vits-piper-es_MX-claude-high/tokens.txt",
                                         data_dir="/tmp/claude-0/tts/vits-piper-es_MX-claude-high/espeak-ng-data"),
        num_threads=NT))), 0, 1.10, None),
]

def write_wav(path, x, sr):
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((np.clip(x, -1, 1) * 32767).astype(np.int16).tobytes()); w.close()

def acortar_pausas(x, sr, umbral_db=-40, max_ms=200, deja_ms=170):
    """Acorta silencios internos > max_ms a deja_ms (no toca habla). Recorta silencio inicial/final a 80 ms."""
    win = int(sr * 0.01)
    n = len(x) // win
    rms = np.sqrt(np.mean(x[:n * win].reshape(n, win) ** 2, axis=1) + 1e-12)
    sil = 20 * np.log10(rms / (np.max(np.abs(x)) + 1e-9)) < umbral_db
    segs, i = [], 0
    while i < n:
        j = i
        while j < n and sil[j] == sil[i]: j += 1
        segs.append((sil[i], i * win, j * win)); i = j
    out = []
    for k, (is_sil, a, b) in enumerate(segs):
        seg = x[a:b]
        if is_sil:
            dur = (b - a) / sr * 1000
            if k == 0 or k == len(segs) - 1:
                keep = int(sr * 0.08)
                seg = seg[-keep:] if k == 0 else seg[:keep]
            elif dur > max_ms:
                keep = int(sr * deja_ms / 1000); h = keep // 2
                fade = np.linspace(1, 0, min(h, 64))
                l, r = seg[:h].copy(), seg[-(keep - h):].copy()
                l[-len(fade):] *= fade; r[:len(fade)] *= fade[::-1]
                seg = np.concatenate([l, r])
        out.append(seg)
    out.append(x[n * win:][:0])
    return np.concatenate(out)

def f0_mediana(x, sr):
    fr = int(sr * 0.04); hop = fr // 2; vals = []
    for i in range(0, len(x) - fr, hop):
        f = x[i:i + fr]
        if np.sqrt(np.mean(f ** 2)) < 0.02: continue
        f = f - f.mean(); ac = np.correlate(f, f, "full")[fr - 1:]
        lo, hi = int(sr / 400), int(sr / 70)
        p = lo + np.argmax(ac[lo:hi])
        if ac[p] > 0.4 * ac[0]: vals.append(sr / p)
    return float(np.median(vals)) if vals else 0.0

CADENA = ("highpass=f=80,"
          "equalizer=f=250:t=q:w=1.0:g=-1.5,"      # quita algo de 'caja'
          "equalizer=f=3500:t=q:w=1.2:g=2.5,"      # presencia
          "equalizer=f=9000:t=q:w=1.0:g=1.0,"      # aire suave
          "acompressor=threshold=-20dB:ratio=2.5:attack=12:release=150:makeup=1.5")

def post(wav_in, mp3_out):
    # loudnorm a dos pasadas -> -16 LUFS, TP -1.5
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", wav_in, "-af",
                        CADENA + ",loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1])
    ln = ("loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={input_i}:measured_TP={input_tp}:measured_LRA={input_lra}:"
          "measured_thresh={input_thresh}:offset={target_offset}:linear=true").format(**js)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav_in, "-af", CADENA + "," + ln, "-ar", "44100",
                    "-c:a", "libmp3lame", "-b:a", "192k", mp3_out], check=True)

def metricas(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af",
                        "silencedetect=noise=-35dB:d=0.12,ebur128", "-f", "null", "-"], capture_output=True, text=True)
    pausas = [round(float(v) * 1000) for v in re.findall(r"silence_duration: ([\d.]+)", r.stderr)]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout)
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr)
    return dur, pausas, (lufs[-1] if lufs else "?")

if __name__ == "__main__":
    st_sids = json.loads(os.environ.get("ST_SIDS", '{"F": 0, "M": 5}'))
    cache = {}
    filas = []
    for nombre, ctor, sid, speed, extra in CANDIDATOS:
        if "supertonic" in nombre:
            sid = st_sids["F" if "_F_" in nombre else "M"]
        key = id(ctor) if "supertonic" not in nombre and "kokoro" not in nombre else ctor.__name__
        if key not in cache: cache = {key: ctor()}
        tts = cache[key]
        g = s.GenerationConfig(); g.sid = sid; g.speed = speed; g.silence_scale = 0.1
        if extra: g.extra = extra
        if "supertonic" in nombre: g.num_steps = 8
        a = tts.generate(TEXTO, g)
        x = np.array(a.samples, dtype=np.float32); sr = a.sample_rate
        raw = RAW + nombre + "_raw.wav"; write_wav(raw, x, sr)
        d0, p0, _ = metricas(raw)
        y = acortar_pausas(x, sr)
        fix = RAW + nombre + ".wav"; write_wav(fix, y, sr)
        mp3 = OUT + nombre + ".mp3"; post(fix, mp3)
        d, p, lufs = metricas(mp3)
        fila = dict(archivo=mp3, sid=sid, speed=speed, sr=sr, f0_hz=round(f0_mediana(y, sr)),
                    dur_bruta_s=round(d0, 2), pausas_brutas_ms=p0, dur_final_s=round(d, 2),
                    ppm=round(PALABRAS / d * 60), pausas_final_ms=p,
                    pausa_max_ms=max(p) if p else 0, pausas_mayor_300ms=sum(v > 300 for v in p), lufs=lufs)
        print(json.dumps(fila, ensure_ascii=False), flush=True); filas.append(fila)
    json.dump(filas, open(RAW + "metricas.json", "w"), ensure_ascii=False, indent=1)
