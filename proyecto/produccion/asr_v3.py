#!/usr/bin/env python3
"""Transcribe con Whisper-small (sherpa-onnx) y compara con el guion v3 (WER + palabras clave).
Uso: python3 -I asr_v3.py frases            # cada frase de voz/v3 por separado
     python3 -I asr_v3.py video N archivo.mp4 # audio final de un video (comparado con el guion completo)
"""
import sys, re, json, subprocess, unicodedata
import numpy as np, sherpa_onnx as s
sys.path.insert(0, "/home/user/gamer-al-dia/produccion")
from voz_v3 import GUION_V3, num

A = "/tmp/claude-0/tts/asr/sherpa-onnx-whisper-small/"
CLAVES = {"gta": r"\bgta\b", "ps5": r"\bps5\b", "take-two": r"\btake two\b", "cloud gaming": r"\bcloud gaming\b",
          "spoilers": r"\bspoilers?\b", "xbox": r"\bxbox\b"}

def rec():
    return s.OfflineRecognizer.from_whisper(encoder=A + "small-encoder.int8.onnx", decoder=A + "small-decoder.int8.onnx",
                                            tokens=A + "small-tokens.txt", language="es", task="transcribe", num_threads=4)

def norm(t):
    t = unicodedata.normalize("NFD", t.lower()); t = "".join(c for c in t if unicodedata.category(c) != "Mn")
    t = t.replace("-", " ")
    t = re.sub(r"\bg\s*t\s*a\b|\bge te a\b|\bgeta\b", "gta", t)
    t = re.sub(r"\b(gta)\s*(vi|seis)\b", r"\1 6", t); t = re.sub(r"\b(gta)\s*(v|cinco)\b", r"\1 5", t)
    t = re.sub(r"\bgta(\d)\b", r"gta \1", t)
    t = re.sub(r"\b(ps|pe ese|play ?station) ?(5|cinco)\b", "ps5", t)
    t = re.sub(r"\b(x ?box|equis ?box)\b", "xbox", t)
    t = re.sub(r"\bseries (x|equis)\b", "series x", t); t = re.sub(r"\bseries (s|ese)\b", "series s", t)
    t = re.sub(r"\btake ?two\b|\bteik tu\b|\btake 2\b", "take two", t)
    t = re.sub(r"\bclaud\b", "cloud", t); t = re.sub(r"\bgu?eiming\b", "gaming", t)
    t = re.sub(r"\bespoilers?\b", "spoilers", t)
    t = re.sub(r"\bgu?eimer\b", "gamer", t)
    t = re.sub(r"(\d+)\s*(gb|gigas|gigabytes)\b", r"\1 gigas", t); t = re.sub(r"\bgb\b", "gigas", t)
    t = re.sub(r"\bpc\b|\bpe ce\b", "pc", t)
    t = re.sub(r"(\d+)\.(\d{3})", r"\1\2", t)
    t = re.sub(r"\b(?<!gta )(?<!ps)\d+\b", lambda m: num(int(m.group())), t)   # números -> palabras
    t = re.sub(r"[^a-z0-9 ]", " ", t)
    return t.split()

def wer_ops(a, b):
    """WER + lista de diferencias (ref -> hyp)."""
    n, m = len(a), len(b); D = np.zeros((n + 1, m + 1), int); D[:, 0] = range(n + 1); D[0, :] = range(m + 1)
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i, j] = min(D[i - 1, j] + 1, D[i, j - 1] + 1, D[i - 1, j - 1] + (a[i - 1] != b[j - 1]))
    i, j, ops = n, m, []
    while i or j:
        if i and j and D[i, j] == D[i - 1, j - 1] + (a[i - 1] != b[j - 1]):
            if a[i - 1] != b[j - 1]: ops.append((a[i - 1], b[j - 1]))
            i, j = i - 1, j - 1
        elif i and D[i, j] == D[i - 1, j] + 1: ops.append((a[i - 1], "")); i -= 1
        else: ops.append(("", b[j - 1])); j -= 1
    return D[n, m] / max(n, 1), ops[::-1]

def transcribe(r, path, ss=None, t=None):
    cmd = ["ffmpeg", "-v", "error"] + (["-ss", str(ss)] if ss is not None else []) + (["-t", str(t)] if t else []) + \
          ["-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"]
    pcm = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.float32)
    st = r.create_stream(); st.accept_waveform(16000, pcm); r.decode_stream(st)
    return st.result.text.strip()

def claves(ref, hyp):
    rj, hj = " ".join(ref), " ".join(hyp)
    return {k: (len(re.findall(p, rj)), len(re.findall(p, hj))) for k, p in CLAVES.items() if re.search(p, rj)}

if __name__ == "__main__":
    r = rec(); res = []
    if sys.argv[1] == "frases":
        info = json.load(open("/home/user/gamer-al-dia/voz/v3/tiempos.json", encoding="utf8"))["videos"]
        for n, fr in info.items():
            for k, f in enumerate(fr):
                hyp = transcribe(r, f["wav"]); w, ops = wer_ops(norm(f["texto"]), norm(hyp))
                print(f"{n}.{k} WER={w:.0%} | {hyp} | {ops}")
                res.append(dict(video=n, esc=k, wer=w, hyp=hyp, ops=ops))
    else:
        n, path = int(sys.argv[2]), sys.argv[3]
        ref = norm(" ".join(GUION_V3[n]))
        # Whisper trabaja en ventanas de 30 s: se transcribe por tramos (cortes en las escenas, pasados por argv)
        cortes = json.loads(sys.argv[4]) if len(sys.argv) > 4 else None
        if cortes:
            hyp = " ".join(transcribe(r, path, a, b - a) for a, b in cortes)
        else:
            hyp = transcribe(r, path)
        h = norm(hyp); w, ops = wer_ops(ref, h)
        print(json.dumps(dict(video=n, wer=round(w, 4), n_ref=len(ref), errores=ops, claves=claves(ref, h), hyp=hyp), ensure_ascii=False))
