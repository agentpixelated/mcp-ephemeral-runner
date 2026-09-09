import json, re, subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'kokoro-v1.0.int8.onnx'
VOICES = ROOT / 'voices-v1.0.bin'
VOICE = 'am_michael'
TARGET_TOTAL = 1200.0
TARGET_SPOKEN = 1130.0
SR = 24000


def chunks(text, max_chars=420):
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    out, cur = [], ''
    for s in sentences:
        if len(cur) + len(s) + 1 <= max_chars:
            cur = (cur + ' ' + s).strip()
        else:
            if cur:
                out.append(cur)
            while len(s) > max_chars:
                cut = s.rfind(' ', 0, max_chars)
                if cut < 80:
                    cut = max_chars
                out.append(s[:cut].strip())
                s = s[cut:].strip()
            cur = s
    if cur:
        out.append(cur)
    return out


def duration(path):
    info = sf.info(path)
    return info.frames / info.samplerate


def atempo_filter(factor):
    parts=[]
    while factor > 2.0:
        parts.append('atempo=2.0'); factor/=2.0
    while factor < 0.5:
        parts.append('atempo=0.5'); factor/=0.5
    parts.append(f'atempo={factor:.8f}')
    return ','.join(parts)


def main():
    data = json.loads((ROOT/'narration.json').read_text())
    raw_dir = ROOT/'audio_raw'; proc_dir = ROOT/'audio_proc'
    raw_dir.mkdir(exist_ok=True); proc_dir.mkdir(exist_ok=True)
    kokoro = Kokoro(str(MODEL), str(VOICES))

    raw_paths=[]
    for i, seg in enumerate(data):
        parts = chunks(seg['text'])
        pieces=[]
        sample_rate=SR
        for j, part in enumerate(parts):
            samples, sample_rate = kokoro.create(part, voice=VOICE, speed=1.0, lang='en-us')
            samples = np.asarray(samples, dtype=np.float32).reshape(-1)
            pieces.append(samples)
            if j != len(parts)-1:
                pieces.append(np.zeros(int(sample_rate*0.18), dtype=np.float32))
        audio=np.concatenate(pieces) if pieces else np.zeros(1,dtype=np.float32)
        p=raw_dir/f'{i:02d}_{seg["id"]}.wav'
        sf.write(p, audio, sample_rate)
        raw_paths.append(p)
        print(f'raw {i:02d} {seg["id"]}: {len(audio)/sample_rate:.2f}s')

    raw_total=sum(duration(p) for p in raw_paths)
    tempo=max(0.82,min(1.35,raw_total/TARGET_SPOKEN))
    print('raw_total',raw_total,'tempo',tempo)

    proc_paths=[]
    for p in raw_paths:
        q=proc_dir/p.name
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(p),'-af',atempo_filter(tempo),'-ar',str(SR),'-ac','1',str(q)],check=True)
        proc_paths.append(q)

    spoken=sum(duration(p) for p in proc_paths)
    if spoken >= TARGET_TOTAL-2:
        extra=spoken/(TARGET_TOTAL-8)
        revised=[]
        for p in proc_paths:
            q=proc_dir/(p.stem+'_fit.wav')
            subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(p),'-af',atempo_filter(extra),'-ar',str(SR),'-ac','1',str(q)],check=True)
            revised.append(q)
        proc_paths=revised
        spoken=sum(duration(p) for p in proc_paths)

    gap_total=max(0.0,TARGET_TOTAL-spoken)
    weights=np.ones(len(proc_paths),dtype=float)
    weights[0]=1.5; weights[-1]=2.0
    gaps=gap_total*weights/weights.sum()

    master=[]; timings=[]
    for seg,p,gap in zip(data,proc_paths,gaps):
        audio,sr=sf.read(p,dtype='float32')
        if audio.ndim>1: audio=audio.mean(axis=1)
        if sr!=SR: raise RuntimeError(f'unexpected sample rate {sr}')
        silence=np.zeros(int(round(gap*SR)),dtype=np.float32)
        master += [audio,silence]
        timings.append({'id':seg['id'],'title':seg['title'],'speech_duration':len(audio)/SR,'pause_duration':len(silence)/SR,'duration':(len(audio)+len(silence))/SR})

    out=np.concatenate(master)
    target_frames=int(round(TARGET_TOTAL*SR))
    if len(out)<target_frames: out=np.pad(out,(0,target_frames-len(out)))
    elif len(out)>target_frames: out=out[:target_frames]
    sf.write(ROOT/'narration.wav',out,SR)
    total=sum(x['duration'] for x in timings)
    timings[-1]['duration'] += TARGET_TOTAL-total
    timings[-1]['pause_duration'] += TARGET_TOTAL-total
    (ROOT/'timings.json').write_text(json.dumps(timings,indent=2))
    print('spoken',spoken,'final',len(out)/SR,'timing_sum',sum(x['duration'] for x in timings))

if __name__=='__main__':
    main()
