"""Download ElevenLabs voice lines, normalise, join with pauses, write timing.json.
Usage: python3 build_vo.py lines.json OUT_DIR
lines.json: [{"url":..., "speaker":..., "text":..., "pause":0.3}, ...]
"""
import json, os, subprocess, sys

lines = json.load(open(sys.argv[1]))
D = sys.argv[2]
os.makedirs(D, exist_ok=True)
LEAD = 0.2
args, filt, timing, t = [], "", [], LEAD
for i, L in enumerate(lines):
    f = f"{D}/line{i+1:02d}.mp3"
    if not os.path.exists(f) or os.path.getsize(f) < 1000:
        subprocess.run(["curl", "-s", "-f", "-o", f, L["url"]], check=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                "-of", "csv=p=0", f], capture_output=True, text=True).stdout)
    pad = L.get("pause", 0.3)
    timing.append({"line": i + 1, "speaker": L["speaker"], "text": L["text"],
                   "start": round(t, 3), "end": round(t + dur, 3), "file": f})
    t += dur + pad
    args += ["-i", f]
    filt += (f"[{i}:a]aresample=48000,aformat=channel_layouts=mono,"
             f"loudnorm=I=-16:TP=-1.5,apad=pad_dur={pad}[a{i}];")
filt += "".join(f"[a{i}]" for i in range(len(lines))) + \
    f"concat=n={len(lines)}:v=0:a=1,adelay={int(LEAD*1000)}[out]"
subprocess.run(["ffmpeg", "-y", "-v", "error", *args, "-filter_complex", filt,
                "-map", "[out]", f"{D}/voiceover_full.wav"], check=True)
json.dump({"total_duration": round(t, 3), "lines": timing},
          open(f"{D}/timing.json", "w"), indent=1, ensure_ascii=False)
print("total", round(t, 2))
for x in timing:
    print(x["line"], x["speaker"], x["start"], x["end"])
