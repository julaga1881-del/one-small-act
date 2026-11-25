# One Small Act — Production Playbook (v1, 2026-11-23)

Channel: One Small Act (@OneSmallAct2026). Heartwarming TRUE stories (Chicken Soup for the Soul style), told as 2D stick-figure animated dramas: narrator + characters with their own voices. English, global audience, warm and calm but hooky.
Reference episode: "They Returned His Lost Ring... Dressed as Hobbits" (render source in hobbit/out/src, reusable engine).

## FORMAT DECISION (2026-11-23): Shorts only
Owner's call: make only YouTube Shorts (9:16, under 60 s) until the channel gains subscribers; long videos return later.
- GROWTH RULES (2026-11-24, from channel data: the only hit so far — 1.4k views — was "His leg snapped mid-race… then his dad", an iconic, already-famous true moment; obscure local news Shorts got single-digit views):
  - Alternate story sources: odd days = iconic/evergreen true moments many people half-remember (sport, history, famous kindness moments, any year); even days = recent viral news. Same fact rules apply (credible sources, nothing invented).
  - Length 30–45 s (~80–110 spoken words). Shorter = higher completion and replays, which drive Shorts reach.
  - First 1 s: start at the most dramatic moment + a 3–6-word on-screen hook text at the top (e.g. "HIS LEG SNAPPED MID-RACE…"), shown for ~2 s. No scene-setting before the conflict.
  - Title = the hook as a cliffhanger ("His leg snapped mid-race… then his dad…" pattern). Keep it honest.
  - Ending loops into the opening line; no outro.
  - Description ends with one question to spark comments (e.g. "Would you have stopped?").
- Script: hook in the first 1–2 s (no slow intro), 2–4 short character lines.
- 1080x1920; no end card; last beat should loop into the first.
- Captions (owner feedback 2026-11-23: big centred captions were distracting): small-to-medium bold text in the lower third (~74% height, never in the bottom 20%), max ~760 px wide, 3–5 words per chunk, must not cover faces or the main action.
- Mix ~-14 LUFS. Credits per Short: ~1,000 voice + music reused from the library.
Sections below describe the long-form defaults; apply them scaled down to this format.

## Pipeline (one agent, sequential)
1. Find story → 2. Fact sheet → 3. Drama script → 4. Voices + music → 5. Render (reuse engine) → 6. QC checklist → 7. Deliver video + thumbnail + upload text.

## 1. Story rules
- Real, recent (last ~3 months), covered by ≥1 credible outlet; ideally 2+. Open the pages and check dates.
- Needs: a hook, a struggle/turning point, an emotional payoff, 2–4 speaking characters.
- Universal, not region-locked.
- NEVER: anything tied to Nazis, Jewish topics, Israel or Palestine. Avoid graphic violence, abuse, suicide, crime victims, or minors in sensitive situations.
- Don't repeat a story already used (keep a used-stories list).

## 2. Fact sheet
- Every fact with a source URL. Flag disagreements between sources and leave disputed details out.
- Never invent names, dates, weekdays, places. Unknown name → use a role ("the second friend").
- Reported quotes used verbatim (under 15 words each).

## 3. Script
- Length: ~2:30–3:00 spoken (330–400 words). Cold-open hook in first 8 s (start at the most intriguing moment, then "go back").
- Mostly narrator; 6–10 character lines at emotional peaks. Dramatised dialogue must stay faithful to facts.
- eleven_v4 audio tags in [brackets]: 1–3 per line ([softly], [excited], [voice breaking], [laughs], [whispering], [pause], [sighs]).
- Close: one reflective line tying to "one small act" + "If this made you smile, share it with someone who needs it today."
- IP care: no film/book quotes, no copyrighted music imitation, generic costumes, no logos.

## 4. Voices & music (ElevenLabs, model eleven_v4)
- Narrator: Jessica — cgSgspJ2msm6clMCkdW9 (young, warm, playful American female).
- Cast every character by age/gender/accent so voices contrast clearly (old man ≠ young man ≠ narrator). Pick from creative_list_voices; never invent IDs.
  Used before: Irish man eyuCA3LWMylRajljTeOo · Irish woman 1OYA2kgM85gF2eGN8HEp · Italian men TdLuijcBD0rt4beD354g, KlyEVp7Cr4uWil0rM5Lq, kVHl2v7Y1yGWEyAY48K9 · teen boy UgMQ92GJ3C3bUAtHUKyd · old gravelly man Q4oILuo4P8VeXtE6FMLI · calm elderly man k11eEqQB8mytYnx5Rg6O.
- One generation per line (generations_count 1). Never re-run a call to retry — it charges again.
- Download from elevenlabsusercontent.com (allowed domain), loudnorm each line to -16 LUFS, join with short pauses, write timing.json.
- Music: ElevenLabs Music (eleven_music_v2_5, instrumental), from the channel music library once built (warm / tense / joyful / bittersweet / folk). Bed ~-24 LUFS, ducked ~6 dB under speech. Code-made SFX are fine.
- Credit guide: voices ~2,500 credits per 3-min drama; one 3-min music track ~2,600.
- Commercial use needs a paid ElevenLabs plan (Starter or above). Free-plan audio = test only, no monetisation.

## 5. Render
- Reuse the engine (Python + skia-python): rig.py characters, sets.py, scenes.py shot list, analysis.py subtitles/mouths, audio.py mix, render.py, run_render.sh.
- 1920x1080, 30 fps, H.264 yuv420p, -preset veryfast, AAC 192k 48 kHz.
- Every line gets a staged moment; speaking character in frame with mouth moving; camera motion on every shot (no static >4 s).
- Burned subtitles (Poppins Bold, outline, max 2 lines, tint per speaker).
- "Based on a true story · dramatised" top-left for first 4 s.
- End card: "One Small Act" over sunset river.
- Thumbnail 1280x720: key moment, big 2–3 word text, high contrast, expressive face.

## 6. QC checklist (manager pass — must all be true before delivery)
- [ ] Every fact on screen/in narration traceable to the fact sheet; no invented dates/names/text on props (phones, calendars, signs).
- [ ] ≥30 frames reviewed across the video incl. hook, climax, end card, every render join.
- [ ] Mouths move on speech; nobody cut off at frame edge; no floating/overlapping elements; subtitles readable and in sync.
- [ ] Full decode with no errors; video and audio durations match.
- [ ] Final mix ~-16 LUFS integrated, true peak < -1.5 dBFS, voice clearly above music.
- [ ] Nothing from the banned-topics list; IP care respected.

## 7. Delivery
Send MP4 + thumbnail + ready-to-paste: title (<60 chars, curious, honest), description (says "based on a true story, dramatised", credits outlets by name), 5 hashtags incl. #OneSmallAct #TrueStory.
Owner uploads manually.

## Used stories
- 2026-11 — Patrick Mohr's wedding ring found by three Italian friends who returned it dressed as hobbits (GNN 23 Oct 2026, IBTimes 11 Nov 2026).
- 2026-11 — "The Wrong Turn": Casey's GPS wrong turn led him to the Burke foster family's house fire near Lyerly, GA; all 14 got out (WRCB/CNN Newsource 22 Oct 2026, GNN 27 Oct 2026). Short scheduled 24 Nov 2026 07:00 Sydney.
- 2026-11 — "Thanks to Arsenal": Alastair Cass stormed out as Arsenal lost 3-0 to Brighton, found Sallie stuck chest-deep in mud near Chulmleigh, Devon; two-hour rescue (SWNS 2 Oct 2026, Good News Network 3 Oct 2026). Short scheduled 25 Nov 2026 16:00 Sydney (Metricool best-time slot).
- 2026-11 — "Two Golds": Barshim & Tamberi share Olympic high-jump gold, Tokyo 2020 (CBC, ESPN/AP, World Athletics, Sky Sports, NBC Olympics). Short scheduled 26 Nov 2026 16:00 Sydney.
- Also used on the channel (avoid repeating): Derek Redmond's dad helping him finish the 1992 Olympic 400 m; Oseola McCarty, the washerwoman who saved $150,000 and gave it to strangers' scholarships.
- (demo only, not published) Jordan Hope gives his shoes to "Mr. Roy", Maricopa AZ.

## Music library
- assets/music_warm_folk.mp3 — ElevenLabs Music v2.5, 155 s, 72 BPM 4/4 (bar 3.33 s). Sections (track time): tender 0–52 s, suspense 53–66 s, lift 66–91 s, folk 92–131 s, resolve 132–149 s. Reuse with bar-aligned crossfades (see story_wrongturn.py). Made on the free plan: replace with a paid-plan track before monetisation.

## Learnings
- 2026-11-25 (production): check period details in audio too — Tokyo 2020 had no spectators, so crowd SFX had to be removed. build_vo.py's loudnorm outputs 192 kHz and mp3 durations run ~1% long vs timing.json; renderers should re-measure onsets.

- 2026-11-25 (YouTube Studio, last 28 days, owner screenshot): Shorts "His leg snapped mid-race…" 1.4k views, "He Lost His Wedding Ring…" (hobbits) 1.2k, "She saved $150,000…" 444, "His GPS Took a Wrong Turn…" 84 (only ~1.5 days old); long-form "The Washerwoman…" 5. Takeaways: iconic moments AND quirky recent news with a strange, visual twist (hobbit costumes) both work; plain local rescue news is weaker, so on even days favour stories with an odd, picture-able twist. Long-form gets ~nothing, so stay Shorts-only. 99.9% of viewers are new, so returning viewers aren't building yet.
- Metricool's YouTube per-video metrics (YTVP06/08) came back null on 2026-11-25; use owner screenshots/Studio numbers when available.

- 2026-11-25 (Studio, 28 days): Shorts 4.3k views / +5 subs vs long videos 9 views / 0 subs. 95.2% of views come from the Shorts feed, 3.3% from search. Reach depends on the feed, so the first frame, the hook text and retention matter far more than title or SEO; spend effort on the first 2 s and the loop.

## Automation
- Daily scheduled task "One Small Act daily Short" runs 21:43 Sydney and schedules the Short for 07:00 next morning via Metricool (brand 8307078). Owner does not pre-review; they take down anything wrong themselves.
