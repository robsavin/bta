"""Render a TikTok (1080x1920) from clips/<clip>/{audio.mp3,words.json,shots.json}.
Art: assets/<ID>.(png|jpg|webp); falls back to placeholders.py output (tagged PLACEHOLDER)."""
import json, os, re, subprocess, sys
from PIL import Image, ImageDraw, ImageFont
clip = sys.argv[1]; preview = "--preview" in sys.argv
W, H = 1080, 1920
cfg = json.load(open(f"clips/{clip}/shots.json")); words = json.load(open(f"clips/{clip}/words.json"))
FPS = cfg["fps"]; dur = words["duration"]; end = cfg["end_card_seconds"]; total = dur + end
F = lambda s, w="ExtraBold": ImageFont.truetype(f"/usr/share/fonts/opentype/inter/Inter-{w}.otf", s)
AMBER, CREAM, INK = (242,184,75), (250,243,228), (28,22,18)

def find_art(i):
    for ext in ("png","jpg","jpeg","webp"):
        p = f"assets/{i}.{ext}"
        if os.path.exists(p): return p
imgs = {}
for s in cfg["shots"]:
    if s["img"] not in imgs:
        imgs[s["img"]] = Image.open(find_art(s["img"])).convert("RGB")
# art is "real" once a Midjourney file other than the generated placeholder .png is supplied (.jpg/.jpeg/.webp),
# or you touch assets/<ID>.real next to a replaced .png
real = {k: os.path.exists(f"assets/{k}.real") or any(os.path.exists(f"assets/{k}.{e}") for e in ("jpg","jpeg","webp")) for k in imgs}

def shot_frame(s, t):
    im = imgs[s["img"]]; iw, ih = im.size
    a = min(max((t - s["t"][0]) / (s["t"][1] - s["t"][0]), 0), 1); a = a*a*(3-2*a)
    lerp = lambda p: p[0] + (p[1]-p[0]) * a
    z = lerp(s["zoom"]); ch = ih / z; cw = ch * W / H
    cx = lerp(s["x"]) * iw; cy = lerp(s["y"]) * ih
    cx = min(max(cx, cw/2), iw - cw/2); cy = min(max(cy, ch/2), ih - ch/2)
    return im.resize((W, H), Image.BICUBIC, box=(cx-cw/2, cy-ch/2, cx+cw/2, cy+ch/2))

# vignette so captions stay legible
shade = Image.new("RGBA", (W, H), (0,0,0,0))
for y in range(H):
    a = int(150 * max(0, (y - H*0.45) / (H*0.55))**1.6 + 70 * max(0, (H*0.14 - y) / (H*0.14)))
    ImageDraw.Draw(shade).line([(0, y), (W, y)], fill=(22,16,12,min(a,190)))

# caption pages: up to 4 words, break after punctuation
pages, cur = [], []
for i, w in enumerate(words["words"]):
    cur.append(i)
    if len(cur) >= 4 or re.search(r"[.?!,;:]$", w["w"]) or sum(len(words["words"][j]["w"]) for j in cur) > 22:
        pages.append(cur); cur = []
if cur: pages.append(cur)
cache = {}
def caption(page, active):
    key = (pages.index(page), active)
    if key in cache: return cache[key]
    font = F(86); layer = Image.new("RGBA", (W, H), (0,0,0,0)); d = ImageDraw.Draw(layer)
    toks = [re.sub(r"[.,;:]$", "", words["words"][i]["w"]).upper() for i in page]
    # wrap to two lines if wide
    widths = [d.textlength(t + " ", font=font) for t in toks]
    lines, cur_l, wsum = [], [], 0
    for idx, (t, w) in enumerate(zip(toks, widths)):
        if wsum + w > W - 180 and cur_l: lines.append(cur_l); cur_l, wsum = [], 0
        cur_l.append(idx); wsum += w
    lines.append(cur_l); y = 1180 - (len(lines)-1) * 55
    for ln in lines:
        tw = sum(widths[i] for i in ln); x = (W - tw) / 2
        for i in ln:
            col = AMBER if page[i] == active else CREAM
            d.text((x, y), toks[i], font=font, fill=col, stroke_width=9, stroke_fill=INK)
            x += widths[i]
        y += 112
    cache[key] = layer; return layer

tag_font = F(30, "Bold"); end_big = F(92); end_small = F(40, "SemiBold")
def top_tag(d):
    txt = "N O T E S   F R O M   B I G   T R A I L S"
    d.text(((W - d.textlength(txt, font=tag_font)) / 2, 150), txt, font=tag_font, fill=CREAM, stroke_width=3, stroke_fill=INK)

def end_frame():
    im = Image.new("RGB", (W, H), (36, 28, 22)); d = ImageDraw.Draw(im)
    for i, l in enumerate(["NOTES FROM", "BIG TRAILS"]):
        d.text(((W - d.textlength(l, font=end_big)) / 2, 780 + i * 120), l, font=end_big, fill=AMBER)
    l = "Full episode wherever you listen"
    d.text(((W - d.textlength(l, font=end_small)) / 2, 1080), l, font=end_small, fill=CREAM)
    return im

nframes = int(total * FPS) if not preview else int(12 * FPS)
out = f"out/{clip}{'_preview' if preview else ''}.mp4"; os.makedirs("out", exist_ok=True)
ff = subprocess.Popen(["ffmpeg","-y","-hide_banner","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-",
    "-i",f"clips/{clip}/audio.mp3","-af",f"loudnorm=I=-14:TP=-1.5,apad,afade=t=out:st={total-0.5}:d=0.5","-t",f"{total}",
    "-c:v","libx264","-preset","medium","-crf","18","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-movflags","+faststart",out], stdin=subprocess.PIPE)
for n in range(nframes):
    t = n / FPS
    if t >= dur:
        fr = end_frame()
    else:
        s = next(x for x in cfg["shots"] if x["t"][0] <= t < x["t"][1] or x is cfg["shots"][-1])
        fr = shot_frame(s, t).convert("RGBA"); fr.alpha_composite(shade)
        d = ImageDraw.Draw(fr); top_tag(d)
        if not real[s["img"]]: d.text((W-300, 60), "PLACEHOLDER ART", font=tag_font, fill=(255,120,90), stroke_width=2, stroke_fill=INK)
        pg = next((p for k, p in enumerate(pages) if words["words"][p[0]]["s"] - 0.05 <= t and
                   (k+1 == len(pages) or t < words["words"][pages[k+1][0]]["s"] - 0.05)), None)
        if pg and t < words["words"][pg[-1]]["e"] + 0.25:
            act = max([i for i in pg if words["words"][i]["s"] <= t] or [pg[0]])
            fr.alpha_composite(caption(pg, act))
        fr = fr.convert("RGB")
    ff.stdin.write(fr.tobytes())
ff.stdin.close(); ff.wait(); print("wrote", out)
