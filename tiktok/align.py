"""Approximate word timings for a clip: speech chunks from silence detection,
transcript words spread across them (char-weighted), chunk boundaries snapped to punctuation.
If you have a real SRT/word timing export (e.g. from Riverside), prefer that."""
import json, re, subprocess, sys
clip = sys.argv[1]
audio = f"clips/{clip}/audio.mp3"
words = open(f"clips/{clip}/transcript.txt").read().split()
dur = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",audio]))
log = subprocess.run(["ffmpeg","-hide_banner","-i",audio,"-af","silencedetect=noise=-35dB:d=0.25","-f","null","-"],capture_output=True,text=True).stderr
starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)",log)]
ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)",log)]
# speech chunks = gaps between silences
chunks=[]; t=0.0
for s,e in zip(starts,ends):
    if s-t>0.15: chunks.append((t,s))
    t=e
if dur-t>0.15: chunks.append((t,dur))
weights=[len(re.sub(r"\W","",w))+2 for w in words]
total_w=sum(weights); total_s=sum(b-a for a,b in chunks)
# ideal cumulative word index at each chunk end, snapped to nearest sentence/clause punctuation
cum=0; bounds=[0]; acc=0
for a,b in chunks[:-1]:
    acc+=b-a; target=acc/total_s*total_w
    run=0; best=None
    for i,w in enumerate(weights):
        run+=w
        if abs(run-target)<=18 and re.search(r"[.,;:?!]$",words[i]):
            if best is None or abs(run-target)<abs(best[1]-target): best=(i+1,run)
    if best is None:
        run=0
        for i,w in enumerate(weights):
            run+=w
            if run>=target: best=(i+1,run); break
    bounds.append(max(best[0],bounds[-1]))
bounds.append(len(words))
out=[]
for (a,b),lo,hi in zip(chunks,bounds,bounds[1:]):
    ws=weights[lo:hi]; tot=sum(ws) or 1; t=a
    for w,wt in zip(words[lo:hi],ws):
        d=(b-a)*wt/tot; out.append({"w":w,"s":round(t,3),"e":round(t+d,3)}); t+=d
json.dump({"duration":dur,"words":out},open(f"clips/{clip}/words.json","w"),indent=1)
print(f"{len(out)}/{len(words)} words, {len(chunks)} speech chunks, {dur:.2f}s")
line=""
for i,x in enumerate(out):
    line+=f"{x['w']} "
    if re.search(r"[.,;:?!]$",x['w']): print(f"{x['s']-0:6.2f}  ...{line[-70:]}"); line=""
