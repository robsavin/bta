# TikTok clip renderer (Tier A)

Per clip: `clips/<id>/audio.mp3`, `transcript.txt`, `shots.json`, plus art in `assets/<ID>.jpg`.

    python3 -I placeholders.py           # stand-in art (only needed until real images exist)
    python3 -I align.py clip1            # approximate word timings -> clips/clip1/words.json
    python3 -I render.py clip1 [--preview]   # -> out/clip1.mp4 (1080x1920, 30fps, loudnorm -14 LUFS, 2s end card)

Real art: drop 16:9 Midjourney upscales in `assets/` as A.jpg..H.jpg; the PLACEHOLDER tag disappears per image.
Better caption timing: replace words.json with real word timings (e.g. from a Riverside transcript export).
