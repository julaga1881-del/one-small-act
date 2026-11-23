#!/bin/bash
# renders the full video in 2 parallel halves, joins, muxes audio
cd "$(dirname "$0")"
NF=$(python3 -c "import json;print(json.load(open('timeline.json'))['nframes'])")
H=$((NF/2))
python3 render.py video 0 $H ../part0.mp4 > ../r0.log 2>&1 &
python3 render.py video $H $NF ../part1.mp4 > ../r1.log 2>&1 &
wait
printf "file 'part0.mp4'\nfile 'part1.mp4'\n" > ../parts.txt
cd .. && ffmpeg -y -loglevel error -f concat -safe 0 -i parts.txt -c copy video_only.mp4 && \
ffmpeg -y -loglevel error -i video_only.mp4 -i mix.wav -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart one_small_act_hobbit_ring.mp4
echo done
