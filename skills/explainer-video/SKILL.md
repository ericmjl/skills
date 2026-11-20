---
name: explainer-video
description: >-
  Use when asked for a motion-graphics explainer in the problem-chain style:
  a 60 to 90 second vertical Short, or a longer build-up (porch-swing) of a
  few minutes, the viewer as the builder, narration in a cloned voice,
  technical jargon that must be pronounced correctly (pyjanitor, llamabot,
  mRNA, LNP, GxP, SMILES), music-synced cuts, or a HyperFrames render of a
  narrated explainer. Also use when a feature list reads as a sequence of
  "and then" and should become a chain of failures and fixes.
license: MIT
---

# Explainer video

A problem-chain explainer in which the viewer is the builder. The naive version fails, each real feature arrives as the fix, and the pictures move on the music. Two script formats: `short` (60 to 90 seconds) and `build-up` (the porch-swing long form). Narration is a cloned voice from the registry, with a lexicon in front of TTS.

This skill owns that pipeline. Neighboring skills stay where they are. Call them, and do not copy their files into this folder.

| Need | Where |
| --- | --- |
| But/therefore chain, checked numbers, sign-off | [references/problem-chain.md](references/problem-chain.md) |
| Palette, type, 5-second change rule, vertical safe zones | [references/hyperframes.md](references/hyperframes.md) |
| Remotion, only if the user explicitly switches renderer | `remotion-video` |
| Chatterbox fallback | Optional sibling skill `chatterbox-voice-clone`, or `CHATTERBOX_SCRIPT` pointing at its `generate_narration.py` |
| Banned defaults, contact-sheet grading, ACE-Step music | `motion-graphics-video` |
| CUDA / aarch64 CosyVoice install | [references/tts-models.md](references/tts-models.md) |
| Reference Short as a shape, never as a transcript | `youtube` (do not paste a guessed Shorts transcript) |

## Usage

Use this skill when the deliverable is a narrated explainer MP4, or the script and audio that will become one.

Skip it for a blog post, a desktop typing video, or a music video with no narration. Those belong to `writing`, `video-script-writing`, or `motion-graphics-video`.

The reference shape is <https://www.youtube.com/shorts/AvRjarGrmC8>. Paraphrase the chain. Do not ingest that Short and paste its sentences into `script.md`.

## Requirements

- Node.js 22 or newer, ffmpeg, and `uv`.
- HyperFrames: `npx hyperframes --version`. Confirm flags with `npx hyperframes render --help` before a render. Flag names move. See [references/hyperframes.md](references/hyperframes.md).
- A row in [voices.yaml](voices.yaml). Eric's clip is `~/voice/eric-voice-ref.m4a` and is not in git.
- Voice `eric` needs Fun-CosyVoice3 weights and CUDA. The GB10 is the intended GPU.
- Voice `eric-mac` is the Mac path when CosyVoice is not installed.
- A royalty-free music file the user supplies, or a track made with the public skill's audio guide.

This skill was written on an x86_64 machine with no GPU. No TTS model was loaded, and HyperFrames was not installed. What that means is in [Verification](#verification).

## What It Does

1. Writes a problem-chain script: a spoken line and a visual note on every beat.
2. Picks a voice from `voices.yaml`.
3. Rewrites jargon from `lexicon.json` before TTS.
4. Synthesizes one WAV per beat and times the edit from those files.
5. Finds music beats and snaps the next line onto a beat by lengthening the gap. Speech is never time-stretched.
6. Builds a HyperFrames `index.html` that mixes narration and ducked music. Default frame is 1080x1920. 16:9 is a second pass, not a crop.
7. Checks the render, then loops critique and re-render.

## How It Works

The chain table exists before any polished line. Audio exists before animation code.

### 1. Script

Follow [references/problem-chain.md](references/problem-chain.md). Start from [references/script-template.md](references/script-template.md).

The parser reads `script.md` and these fields: `join`, `spoken`, `visual`, `number`, `source`, `delta`. Beats are numbered `## Beat 0`, `## Beat 1`, with no gaps. An optional `# Format` heading is `short` or `build-up`. Missing means `short`, so older scripts still parse. `join` may be `none`, `but`, `therefore`, or `caveat`. A `therefore` line opens with "So". "Therefore" is allowed; using it on every fix is a warning. `source` is optional free text (`path:line` is the useful form). `delta` is optional. When it is a path such as `data/raw.csv` or `environment.yml`, the composition grows a file tree and marks the new file. Comma-separated paths (`.env, .gitignore`) are separate files. A path that starts with `~/` (such as `~/dotfiles/install.sh`) is a second tree root, next to the project tree. A sentence delta stays a labeled row. Omitted source and delta parse as `none`, so a script written before those fields still loads. The composition carries earlier deltas forward, so the visual line does not restate them.

The spoken field is the only text that is synthesized. Check the budget before you synthesize:

```bash
uv run skills/explainer-video/scripts/check_script.py check PROJECT/script.md
uv run skills/explainer-video/scripts/check_script.py mine PROJECT/docs
```

`check` counts words, checks join order, counts `but` joins (printed as `buts`, not `failures`), and flags banned joins plus jargon missing from the lexicon. A beat outside 15 to 18 words is a warning, not a failure. On `short`, the script still aims at 10 to 12 beats and 150 to 216 words, 4 or 5 `but` failures, and a "Congratulations, you built X" sign-off. On `build-up` those caps do not apply. A build-up script warns above about 650 words (about 4.5 minutes), warns when a `therefore` beat is missing a naming punchline ("That's X." or "Those are X."), and accepts a free-text sign-off. "So" is the recommended therefore opener in both formats. Repeated "Therefore" is a warning. `mine` lists problem and why headings as `path:line` pairs. The rules are in [references/problem-chain.md](references/problem-chain.md).

Put the chain table in `docs/chain.md`. Anything above the first `# Artifact` heading in `script.md` is ignored. A table inside a section becomes part of that section and will confuse the parser.

### 2. Voice

`eric` is Fun-CosyVoice3 on CUDA. `eric-mac` is Chatterbox Turbo. That fallback shells out to an optional sibling `chatterbox-voice-clone` script, or to `CHATTERBOX_SCRIPT` if that environment variable is set. `kokoro-af-heart` is listed and refused on purpose: Kokoro does not clone. The survey and the reason for this pair are in [references/tts-models.md](references/tts-models.md).

### 3. Pronunciation

Read [references/pronunciation.md](references/pronunciation.md). Normalize before every synthesis. Add a miss to the skill lexicon so the next video inherits it.

```bash
uv run skills/explainer-video/scripts/pronounce.py apply "The LNP carries the mRNA." --target cosyvoice3
uv run skills/explainer-video/scripts/pronounce.py add pyjanitor \
  --cmu "[P] [AY1] [JH] [AE1] [N] [IH0] [T] [ER0]" \
  --respelling "pie janitor" \
  --note "listened on take 2"
uv run skills/explainer-video/scripts/pronounce.py resynth PROJECT --term pyjanitor --text-only
uv run skills/explainer-video/scripts/pronounce.py resynth PROJECT --beat 3 --voice eric
uv run skills/explainer-video/scripts/pronounce.py listen audio/beats/03.prev.wav audio/beats/03.wav
```

`add` refuses a term that already exists. Change it with `correct`, which bumps the lexicon version. After a listen, set the flag:

```bash
uv run skills/explainer-video/scripts/pronounce.py correct pyjanitor --verified --note "take 2, 2026-11-20"
```

`pixi` ships as `verified: true` because Eric confirmed "pixie". Every other seed is `verified: false`. That includes the Bootstrap Notes terms (`Git` as "ghit", `CI`, `AGENTS.md`, `pre-commit`, `dotfiles`, `lockfile`), the first-render additions (`AI` as "ay eye", `teammate` as "team mate" after it was heard as "tim mate"), and the build-up seeds (`git add dot` stays as written, `Diataxis` as "dye uh tax iss" — Eric confirmed the reading is dye-a-taxis, still `verified: false` until a take is checked by ear — `.env` as "dot E N V", `pyproject.toml` as "pie project dot toml", `pixi.lock` as "pixie dot lock", `pytest` as "pie test", `pyds-cli` as "pie D S C L I", `cookiecutter` as "cookie cutter", `SKILL.md` as "skill dot em dee", `.gitignore` as "dot git ignore", plus `GitHub`, `CSV`, and `load_customer_data` from that script). The Nov 20, 2026 v2 render also seeded `two-gigabyte`, `hard-codes`, `live in`, `Skills` (exact), `integration runs`, `analysis_final_v3`, `my_env`, `overwrite`, `debugging`, `Constraints`, `reusable`, `.agents/skills/`, and `uv`. Treat unverified readings as guesses until someone listens.

A previous project's `pronunciations.json` merges in with:

```bash
uv run skills/explainer-video/scripts/pronounce.py import PROJECT/pronunciations.json
```

New terms are added. A verified entry is left alone. An unverified entry keeps a respelling it already has. The file may be a term-to-respelling map, a list of entries, or a lexicon-shaped object.

### 4. Synthesize

```bash
uv run skills/explainer-video/scripts/synthesize_beat.py PROJECT --dry-run
uv run skills/explainer-video/scripts/synthesize_beat.py PROJECT --beat 0 --dry-run
uv run skills/explainer-video/scripts/synthesize_beat.py PROJECT --voice eric
```

Omit `--beat` to synthesize every beat in one process. The weights load once. `--dry-run` writes `audio/beats/NN.spoken.txt` and does not import a model. A real `eric` call needs CUDA. If CUDA is missing the script exits. It does not switch models. Switch on purpose with `--voice eric-mac`.

On the GB10, do not `pip install -r` CosyVoice's `requirements.txt`. Those pins are x86 cu121 wheels. The install that works, the reference-clip silence, the sound-code shield, the wetext 403, and `HF_HOME` are in [references/tts-models.md](references/tts-models.md). Skip the optional vLLM path.

Each real take is loudness-normalized (speech to -16 LUFS) and then checked with `pronunciation_qa.py`. That check is a **signal, not proof**. An ear check is still required: in v1 a phoneme pass on "live" still sounded wrong to Eric. Do not skip listening because the JSON says `ok`.

For each take the QA script:

1. Transcribes with Whisper `small.en`, `word_timestamps=True`, `temperature=0`.
2. Scores forced decoding: `sot_sequence_including_notimestamps` plus `encode(' ' + text)` plus `eot`, `log_softmax` of `model.logits(tokens[:-1], embed_audio(mel))`, sum of the text-token log-probs. The target line is compared to a competitor built from the optional lexicon field `misheard` (for example `two-gigabyte` → `toe gigabyte`). The report stores target, competitor, and margin.
3. Runs wav2vec2 phonemes (`facebook/wav2vec2-xlsr-53-espeak-cv-ft`, greedy CTC, pad/s/unk dropped) on each lexicon target word's Whisper span, padded ±0.08 s, and compares that to the entry's `ipa` (`live` should be `l ɪ v`, not `l aɪ v`).
4. Checks the first word, the last word (also matching the last 2–3 words squashed together), and the whole-line difflib ratio, against both the spoken text and the respelled text. Retry until a take passes or tries run out (default 4, min ratio 0.9). Keep the best take, ranked by `(first_ok + last_ok, ratio)`. This replaced the WER-only check, which let 8 beats through with a dropped opening "So" or a cut-off closing "That's X."

A per-beat JSON report is written to `audio/beats/NN.qa.json`. `voice_log.json` still gets a summary. torch, openai-whisper, and transformers are optional and lazy-loaded; missing models skip forced decoding and the phoneme check, and the error tells you to `uv run --with ...`. Do not `pip install` them globally. `--attempts 1` records the check without a retry.

Never inject a spoken filler such as "Hmm." Trailing silence on the reference clip is what stops a dropped first word. If the pad cannot be written, the line is still sent as written.

### 5. Music and cuts

Put a royalty-free track at `PROJECT/audio/music.wav`. When the license is CC BY, also write `PROJECT/audio/credit.json` with `title`, `author`, `source`, and `license`. The build step turns that into `credits.txt`. CC0 does not need the file.

```bash
uv run skills/explainer-video/scripts/align_music.py PROJECT
uv run skills/explainer-video/scripts/align_music.py PROJECT --aspect 16:9
```

`align_music.py` measures each beat WAV, then runs `librosa.beat.beat_track` unless you pass `--beats-json` with `{"bpm": 100, "beats": [0.5, 1.0]}`. It writes `timeline.json`. Before that, it writes `audio/music.norm.wav` at -24 LUFS and uses that file as the bed, so the mux is not sitting on an unleveled track. The original music file is left as you supplied it.

A music beat captures the next clip only when it falls inside the gap window, 0.08 s to 0.55 s after the previous clip ends. Otherwise the clip keeps the minimum gap. The first clip starts at `lead_in` (0.15 s) or the first beat after that. Speech duration is the WAV duration. Do not loop a short bed. The script warns when the music ends before the timeline.

### 6. Render

```bash
uv run skills/explainer-video/scripts/build_composition.py PROJECT
npx hyperframes check .
npx hyperframes render --quality draft -o out/draft.mp4
skills/explainer-video/scripts/verify_render.sh out/draft.mp4 DURATION 1080 1920
```

`build_composition.py` writes `index.html`, and `credits.txt` when `audio/credit.json` names a CC BY license. Narration WAVs are already loudness-normalized by the synthesize step, and the music bed is normalized by align, both before HyperFrames muxes them. Each scene's picture is the cumulative `delta` list. A path delta grows a file tree and marks the new file. A path that ends with `/` is a directory, including empty ones such as `.git/`. Comma-separated paths are separate files. A `~/` path is a second tree root. A sentence delta stays a labeled row. The picture survives from beat to beat. The music element carries a `data-automation` volume lane that dips under each narration clip. HyperFrames does not apply `data-fx-carve` at playback. That attribute stores Studio settings so a carve can be recomputed. The lane is what the player reads. The type stack starts at Berkeley Mono and falls back to DejaVu Sans Mono, Liberation Mono, Nimbus Mono PS, and Noto Sans Mono. On the GB10, point HyperFrames at Playwright's `headless_shell`. Details are in [references/hyperframes.md](references/hyperframes.md).

Vertical is the default. For 16:9, re-run align and build with `--aspect 16:9` as its own timeline. Do not crop a 16:9 master down to 9:16.

`npx hyperframes beats` writes a Studio beat file. It does not place narration. Keep using `align_music.py` for that.

### 7. Review

[references/review.md](references/review.md). Grade, fix the three worst problems, render again. Three draft rounds before a high-quality export. In the final, no beat holds a single entrance longer than 4 seconds.

## Project layout

```text
PROJECT/
  script.md
  docs/chain.md
  audio/music.wav
  audio/credit.json            # CC BY tracks only: title, author, source, license
  credits.txt                  # written by build_composition.py from credit.json
  audio/beats/00.wav
  audio/beats/00.spoken.txt
  audio/beats/00.qa.json           # pronunciation QA: signal, not proof
  audio/beats/00.prev.wav          # previous take, after a resynth
  audio/beats/00.spoken.prev.txt
  timeline.json
  voice_log.json               # per-beat pronunciation QA summary
  index.html
  out/draft.mp4
```

## Verification

Run the unit tests from the repo root:

```bash
uv run --with pytest --with typer --with pyyaml --with loguru \
  python -m pytest skills/explainer-video/tests -q
uv run --with ruff ruff check skills/explainer-video
```

Verified on 2026-11-20, on this machine (x86_64, no NVIDIA GPU, Python 3.12):

- Lexicon matching, CMU validation, CosyVoice token emission with a `|` word break, the sound-code shield, the reference-clip silence, no spoken Hmm filler, the one-load model cache, pronunciation QA (CTC decode, first/last matching, span selection, misheard substitution, report shape, retry ranking) with models mocked, loudness filter parsing, Chatterbox respelling, hyphen boundaries, overlapping terms, and the shipped seed list. The version and verified pins live on `tests/fixtures/lexicon.json`.
- Script parsing, including `caveat`, optional `delta`, free-text `source`, and an optional `# Format` heading (`short` default, `build-up`). A beat outside 15 to 18 words warns. Every therefore opening with "Therefore" warns and does not fail. All-So therefore openers do not warn. Gap snap, ducking gains, WAV duration, and the HTML scaffold (escaped text, cumulative picture, file tree for path deltas including empty directories that keep a trailing `/`, comma-separated paths, a `~/` second tree root, volume lane, monospace fallbacks, 1080x1920 and 1920x1080).
- The build-up example at `examples/ds-bootstrap-build-up/script.md` parses and `check_script.py` accepts it. A missing "That's X." punchline warns. Short budget, failure count, and sign-off defaults stay in force when Format is omitted.
- CC BY attribution written to `credits.txt`, and left unwritten for CC0.
- CLI `add`, `apply`, `import`, duplicate refusal, and `resynth --text-only`.
- `check_script.py`: join order, the 15 to 18 word budget, the short sign-off, build-up punchline warning, Now/Finally recap on a build-up `but`, banned joins, jargon scan, docs mining, and a summary that prints `buts` and `warnings` rather than counting warnings as `failures`.
- `ruff check` with [ruff.toml](ruff.toml), which ignores B008 because Typer options are function calls in defaults.
- `bash -n` on `scripts/verify_render.sh`.

Untested, because the machine cannot run them:

- Fun-CosyVoice3 and Chatterbox inference, including English CMU inpainting. The official CosyVoice example shows Chinese pinyin inpainting, not an English CMU sentence.
- Whether every seed pronunciation sounds right. `pixi` → "pixie" is the one Eric confirmed. The rest are `verified: false`, including the build-up seeds and the extra `GitHub` / `CSV` / `load_customer_data` entries.
- `librosa.beat.beat_track` on a real track. Placement math is tested with a fake beat list.
- HyperFrames `check` and `render`. The CLI was not installed.
- The GB10 install itself, a real CosyVoice load, Whisper `small.en` on a take, wav2vec2 phoneme inference, forced-decoding logits, a modelscope 403, and a HyperFrames render with Playwright's arm64 `headless_shell`. The 0.8 s reference pad is the mitigation the GB10 render used. It was not re-run here. A v1 phoneme pass on "live" still sounded wrong to Eric; that is why the QA JSON is a signal, not proof.
- The file tree from an earlier aarch64 render's `build_visuals.py` and `index.html`. This machine cannot reach that box, so the diagram here is a path tree driven by `delta`. If a later HTML should match that render exactly, those two files are the reference.
- Mac MPS.
- Loudness of a mixed render.

Do not tell Eric a model was listened to unless a WAV from that run is in the project.
