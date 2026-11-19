import sherpa_onnx as s, subprocess, numpy as np, glob, re, unicodedata, sys
D="/tmp/claude-0/tts/asr/sherpa-onnx-whisper-small/"
r=s.OfflineRecognizer.from_whisper(encoder=D+"small-encoder.int8.onnx",decoder=D+"small-decoder.int8.onnx",tokens=D+"small-tokens.txt",language="es",task="transcribe",num_threads=4)
REF="ya puedes jugar gta 6 si se desbloqueo a las doce de la noche hora local del 19 de noviembre en ps5 y xbox series pero ojo no fue a la vez nueva zelanda abrio primero casi diecinueve horas antes que ciudad de mexico"
def norm(t):
    t=unicodedata.normalize("NFD",t.lower()); t="".join(c for c in t if unicodedata.category(c)!="Mn")
    t=t.replace("diecinueve de noviembre","19 de noviembre").replace("doce","doce")
    t=re.sub(r"\bgta\s*(6|seis|vi)\b","gta 6",t); t=re.sub(r"\bps\s*5\b|\bps5\b|\bpe ese cinco\b|\bpsp? ?5\b","ps5",t)
    t=re.sub(r"\b19\b(?! de)","diecinueve",t); t=t.replace("x box","xbox").replace("equis box","xbox")
    t=re.sub(r"\b12\b","doce",t)
    return re.sub(r"[^a-z0-9 ]"," ",t).split()
def wer(a,b):
    d=np.arange(len(b)+1)
    for i,x in enumerate(a,1):
        p=d.copy(); d[0]=i
        for j,y in enumerate(b,1): d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(x!=y))
    return d[-1]/len(a)
for f in sorted(glob.glob("/home/user/gamer-al-dia/voz/muestras/*.mp3")):
    pcm=subprocess.run(["ffmpeg","-v","error","-i",f,"-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
    st=r.create_stream(); st.accept_waveform(16000,np.frombuffer(pcm,dtype=np.float32)); r.decode_stream(st)
    t=st.result.text.strip()
    print(f.split("/")[-1], "WER=%.0f%%"%(100*wer(norm(REF),norm(t))), "|", t)
