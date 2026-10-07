# Audio

Audio is the difference between a demo and a video. Produce it before
animation and cut every scene boundary to it. Everything here is free and
runs locally; no API keys.

## Order of work

1. Music track chosen and placed at `audio/track.wav`
2. Beat grid measured to `docs/beats.json`
3. Sound effects synthesized into `audio/sfx/`
4. Voiceover generated (optional) into `audio/vo/`
5. Mix target noted: master at -14 LUFS

## Music

### Preferred - ACE-Step 1.5 (local, free)

[ACE-Step 1.5](https://github.com/ace-step/ACE-Step-1.5) is an open-source
music generation model; quality is competitive with commercial services and it
runs on consumer hardware (under 4GB VRAM; about 10GB disk for models;
Python 3.11-3.12).

Install:

```bash
git clone https://github.com/ACE-Step/ACE-Step-1.5.git ~/github/ACE-Step-1.5
cd ~/github/ACE-Step-1.5
uv sync
uv run acestep-download          # pulls default turbo + 1.7B LM models
```

Run (Gradio UI on :7860, REST API on :8001):

```bash
uv run acestep --enable-api      # add --help for ports and backends
```

On Apple Silicon use the MLX backend for native acceleration:
`./start_gradio_ui_macos.sh` (or `start_api_server_macos.sh`). It runs on a
MacBook Air with 16GB RAM. On CUDA GPUs it is faster; pick the model size from
the VRAM table in their README (turbo + 0.6B/1.7B LM covers most laptops).

Generate the track:

- Write a structure-aware prompt: genre, BPM, instruments, mood, and form
  ("intro - build - drop - outro") so the track has moments that can carry
  story beats.
- Generate at least 6 candidates, listen (check durations and energy curve),
  pick the one whose build and drop land where the story needs them.
- Use the chosen track unchanged. Do not time-stretch it; move the cuts.
- Export to `audio/track.wav`.

Fallbacks, in order: free hosted generator (acemusic.ai), MusicGen or Stable
Audio Open locally, or a user-supplied track. If no music is possible, stop
and tell the user; do not ship a silent video.

### Licensing note

ACE-Step model weights and outputs are for the user to clear; if the video is
for a commercial client, confirm the license terms in the ACE-Step repo before
using generated music in the deliverable.

## Beat grid

Measure the track so scene cuts land on beats:

```bash
uv run scripts/beat_grid.py audio/track.wav -o docs/beats.json
```

Output JSON: `bpm`, `duration`, `onsets` (seconds), and `strong_beats`
(highest-energy onsets). When writing the shot list, snap every cut to the
nearest beat or half-beat. Put the biggest cut on the biggest onset (the
drop).

## Sound effects

Synthesize, do not download. `scripts/sfx_synth.py` renders seeded,
deterministic WAVs:

```bash
uv run scripts/sfx_synth.py whoosh  -d 0.6 -o audio/sfx/whoosh_01.wav
uv run scripts/sfx_synth.py impact  -d 1.2 -o audio/sfx/impact_01.wav
uv run scripts/sfx_synth.py riser   -d 2.0 -o audio/sfx/riser_01.wav
uv run scripts/sfx_synth.py sparkle -d 1.0 -o audio/sfx/sparkle_01.wav
uv run scripts/sfx_synth.py tick    -d 0.1 -o audio/sfx/tick_01.wav
```

Rules:

- One SFX per meaningful motion event: an entrance, a hit, a transition, a
  number landing. Never a bed of constant noise.
- Place SFX at shot boundaries and key onsets; a whoosh should END on the cut
  it motivates, an impact should START on it.
- Less is more: if an effect feels loud or unnecessary, remove it.

## Voiceover (optional)

[Kokoro-82M](https://github.com/hexgrad/kokoro) is a free local TTS model
(about 300MB, Apache 2.0):

```bash
pip install kokoro soundfile      # Apple Silicon alternative: mlx-audio
```

Generate per section, not per sentence, split at paragraph breaks, and convert
to MP3/WAV with ffmpeg. `af_heart` is the smoothest default voice. For lyric
or narration sync on screen, generate word timings alongside the audio and put
them in `docs/beats.json` so the shot list can align words to frames.

## Mix

- Music is the bed; VO sits on top; SFX punctuate. Duck music under VO.
- Master the final mix to -14 LUFS integrated (social platform target):

```bash
ffmpeg -i out/final.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy out/final_loud.mp4
```

- Verify with `scripts/verify_render.sh`, which prints measured loudness.
- loudnorm's single-pass dynamic mode is approximate on short clips (can
  land 1-2 LU off). Prefer a measured gain adjustment: render, measure with
  `verify_render.sh`, apply `ffmpeg -af volume=<XdB>` with the signed
  difference, re-verify.
