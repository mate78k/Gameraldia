#!/usr/bin/env python3
"""Control de calidad de los *_v3.mp4. Uso: python3 -I qc_v3.py [N ...]  -> imprime JSON por video
y guarda fotogramas cada 3 s (y hojas de contacto) en /home/user/gamer-al-dia/videos/qc_v3/.
Mide: formato (ffprobe), sonoridad (ebur128 con true peak), pausas de la voz (silencedetect sobre la pista de
voz reconstruida con los mismos tiempos del render), ritmo, y Whisper por escena sobre el audio FINAL (con
música): compara lo que se oye dentro de la ventana de cada escena con la frase de esa escena (WER + sincronía).
"""
import sys, os, re, json, subprocess, wave
import numpy as np
BASE = "/home/user/gamer-al-dia/produccion"; sys.path.insert(0, BASE)
import render as R
from guiones_data import VIDEOS
import asr_v3 as A
QC = "/home/user/gamer-al-dia/videos/qc_v3"

def run(cmd): return subprocess.run(cmd, capture_output=True, text=True)

def probe(f):
    js = json.loads(run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", f]).stdout)
    v = next(s for s in js["streams"] if s["codec_type"] == "video"); a = next(s for s in js["streams"] if s["codec_type"] == "audio")
    return dict(dur=float(js["format"]["duration"]), v=f'{v["codec_name"]} {v["width"]}x{v["height"]} {v["r_frame_rate"]}',
                a=f'{a["codec_name"]} {a["channels"]}ch {a["sample_rate"]} Hz {int(a.get("bit_rate", 0))//1000} kb/s',
                a_ok=a["codec_name"] == "aac" and a["channels"] == 2)

def loud(f):
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-af", "ebur128=peak=true", "-f", "null", "-"]).stderr
    tail = e[e.rfind("Summary:"):]
    g = lambda k: float(re.search(k + r":\s+(-?[\d.]+|-inf)", tail).group(1))
    return dict(lufs=g("I"), lra=g("LRA"), true_peak=g("Peak"))

def voz_sola(v, dur, path):
    sr = 44100; vt = np.zeros(int((dur + 1) * sr), np.float32)
    for sc in v["scenes"]:
        w = wave.open(sc["voz_wav"], "rb"); s = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32767; w.close()
        st = int(sc["voz_t"] * sr); vt[st:st + len(s)] += s
    w = wave.open(path, "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((vt[:int(dur * sr)] * 32767).astype(np.int16).tobytes()); w.close()

def pausas(path, d=0.12):
    e = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", f"silencedetect=noise=-40dB:d={d}", "-f", "null", "-"]).stderr
    st = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", e)]
    du = [float(x) for x in re.findall(r"silence_duration: ([\d.]+)", e)]
    return list(zip(st, du))

def frames(f, n, dur):
    d = os.path.join(QC, f"video{n}"); os.makedirs(d, exist_ok=True)
    for old in os.listdir(d): os.remove(os.path.join(d, old))
    ts = [round(t, 2) for t in np.arange(1.5, dur, 3.0)]
    for t in ts:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", f, "-frames:v", "1", os.path.join(d, f"t{t:05.1f}.png")])
    from PIL import Image, ImageDraw, ImageFont
    fs = sorted(os.listdir(d)); sheets = []
    for i in range(0, len(fs), 6):
        sh = Image.new("RGB", (3 * 540, 2 * 980), "black"); dr = ImageDraw.Draw(sh)
        for j, fn in enumerate(fs[i:i + 6]):
            im = Image.open(os.path.join(d, fn)).resize((540, 960))
            sh.paste(im, ((j % 3) * 540, (j // 3) * 980 + 20)); dr.text(((j % 3) * 540 + 8, (j // 3) * 980 + 2), fn, fill="yellow")
        p = os.path.join(QC, f"video{n}_hoja{i//6+1}.jpg"); sh.save(p, quality=88); sheets.append(p)
    return ts, sheets

def qc(n):
    v0 = VIDEOS[n - 1]; R.SUFIJO = "_v3"; R.VOZ_DIR = "/home/user/gamer-al-dia/voz/v3"
    v = R.retime(v0, n); dur = v["scenes"][-1]["t1"]
    f = R.out_name(v0); res = dict(video=n, archivo=f)
    res.update(probe(f)); res.update(loud(f))
    vp = os.path.join(QC, f"_voz{n}.wav"); os.makedirs(QC, exist_ok=True); voz_sola(v, dur, vp)
    res["voz_sola"] = loud(vp)
    ps = pausas(vp)
    voz_ini = v["scenes"][0]["voz_t"]; voz_fin = v["scenes"][-1]["voz_t"] + v["scenes"][-1]["voz_dur"]
    internas = [(round(a, 2), round(b, 2)) for a, b in ps if a > voz_ini + 0.05 and a + b < voz_fin - 0.05]
    res["pausas_n"] = len(internas); res["pausa_max"] = max((b for a, b in internas), default=0)
    res["pausas_mayor_600ms"] = [p for p in internas if p[1] > 0.6]
    res["pausas_entre_escenas_media"] = round(float(np.mean([b for a, b in internas if b > 0.35] or [0])), 2)
    os.remove(vp)
    pal = sum(len(re.findall(r"\w+", sc["voz_texto"].replace("GTA 6", "GTA6").replace("GTA 5", "GTA5"))) for sc in v["scenes"])
    habla = sum(sc["voz_dur"] for sc in v["scenes"])
    res.update(palabras=pal, ppm_habla=round(pal / habla * 60, 1), ppm_video=round(pal / (voz_fin - voz_ini) * 60, 1))
    # Whisper por escena sobre el audio final
    r = A.rec(); esc = []; R_all, H_all = [], []
    for k, sc in enumerate(v["scenes"]):
        hyp = A.transcribe(r, f, sc["t0"], sc["t1"] - sc["t0"])
        ref = A.norm(sc["voz_texto"]); h = A.norm(hyp); w, ops = A.wer_ops(ref, h)
        R_all += ref; H_all += h
        esc.append(dict(k=k, t0=sc["t0"], t1=sc["t1"], voz=[round(sc["voz_t"], 2), round(sc["voz_t"] + sc["voz_dur"], 2)],
                        kw_t=round(sc["kw_t"], 2), kw_dentro_de_la_voz=bool(sc["voz_t"] - 0.1 <= sc["kw_t"] <= sc["voz_t"] + sc["voz_dur"]),
                        cap=sc["cap"], ref=sc["voz_texto"], hyp=hyp, wer=round(w, 3), dif=ops))
    w, ops = A.wer_ops(R_all, H_all)
    res.update(wer=round(w, 4), n_ref=len(R_all), errores=ops, claves=A.claves(R_all, H_all), escenas=esc)
    res["fotogramas_t"], res["hojas"] = frames(f, n, dur)
    return res

if __name__ == "__main__":
    out = [qc(int(a)) for a in (sys.argv[1:] or ["1", "2", "3"])]
    json.dump(out, open(os.path.join(QC, "qc_v3.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for r in out:
        print(json.dumps({k: r[k] for k in r if k not in ("escenas",)}, ensure_ascii=False))
        for e in r["escenas"]: print("   ", e["k"], e["t0"], e["t1"], f'WER {e["wer"]:.0%}', "|", e["hyp"], e["dif"] or "")
