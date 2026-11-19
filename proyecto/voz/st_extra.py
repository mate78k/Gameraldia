import sys, os; sys.path.insert(0, "/tmp/claude-0/tts/scripts")
import muestras as m, sherpa_onnx as s, numpy as np, json
t = m.supertonic(); outd = m.OUT + "supertonic3_todas_las_voces/"; os.makedirs(outd, exist_ok=True)
names = ["F1","F2","F3","F4","F5","M1","M2","M3","M4","M5"]  # SUPUESTO: orden sid 0-4 = F1..F5, 5-9 = M1..M5 (por tono medido)
jobs = [(f"{outd}supertonic3_sid{sid}_{names[sid]}.mp3", sid, m.TEXTO) for sid in range(10)]
jobs += [(m.OUT + "supertonic3_F_mujer_texto_crudo.mp3", 3, m.ORIGINAL), (m.OUT + "supertonic3_M_hombre_texto_crudo.mp3", 7, m.ORIGINAL)]
for mp3, sid, txt in jobs:
    g = s.GenerationConfig(); g.sid = sid; g.speed = 1.1; g.silence_scale = 0.1; g.extra = {"lang": "es"}; g.num_steps = 8
    a = t.generate(txt, g); x = np.array(a.samples, dtype=np.float32)
    y = m.acortar_pausas(x, a.sample_rate); w = m.RAW + "tmp.wav"; m.write_wav(w, y, a.sample_rate); m.post(w, mp3)
    d, p, l = m.metricas(mp3)
    print(json.dumps(dict(archivo=mp3, sid=sid, f0=round(m.f0_mediana(y, a.sample_rate)), dur=round(d,2), ppm=round(m.PALABRAS/d*60), pausas=p, lufs=l)))
