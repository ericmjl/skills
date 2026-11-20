# Pronunciation

Technical terms are rewritten before TTS. The written line in `script.md` stays in normal spelling. The line that reaches the model is `audio/beats/NN.spoken.txt`. On-screen words, if any, use the real spelling. The respelling is for the speaker only.

## Lexicon

[lexicon.json](../lexicon.json) is versioned. `add` and `correct` write a new file with `version` incremented by one and `updated` set to the day of the edit. A project can record that version next to a take.

Each entry:

| Field | Role |
| --- | --- |
| `term` | Written form to find. A short phrase is allowed (`git add dot`). |
| `cmu` | Bracketed CMU ARPAbet, spaces allowed in the file. Sent to CosyVoice 3 with the spaces removed. |
| `respelling` | Plain words. Sent to Chatterbox. |
| `ipa` | Reference for a human editor and for the wav2vec2 phoneme check. Not sent to either TTS model. |
| `note` | Why this reading was chosen, and whether anyone has listened. |
| `match` | `insensitive`, or `exact` when the lowercase word is ordinary English (`SMILES`, `Modal`, `Skills`). |
| `verified` | True only after a listen. `pixi` is true. Every other seed is false, including `AI` ("ay eye"), `teammate` ("team mate"; the first render heard "tim mate"), and the build-up seeds (`git add dot` stays as written, `Diataxis` as "dye uh tax iss", `.env`, `pyproject.toml`, `pixi.lock`, `pytest`, `pyds-cli`, `cookiecutter`, `SKILL.md`, `.gitignore`). |
| `misheard` | Optional. A wrong reading used as the forced-decoding competitor (`two-gigabyte` → `toe gigabyte`). |

CMU tokens are `[AA]` through `[ZH]`, with stress `0`, `1`, or `2` on vowels only. `X` is `[EH1] [K] [S]`. A consonant with a stress digit is rejected.

## What each model receives

`cosyvoice3` emits concatenated tokens, matching the pinyin shape in the CosyVoice README (`[j][ǐ]` with no spaces):

```text
The [EH2][L][EH1][N][P][IY1] carries the [EH1][M][AA1][R][EH1][N][EY1].
```

`chatterbox` emits the respelling:

```text
The el en pee carries the em ar en ay.
```

If a CosyVoice entry has no `cmu`, the pass uses the respelling and prints a warning. If a Chatterbox entry has no respelling, the written term is left alone and a warning is printed. Fill both fields.

A second pass is stable. A run of two or more bracket tokens is left untouched, so correcting a line that already contains `[P][AY1]` does not rewrite the tokens.

## Word breaks in a CMU string

Tokens inside one word are concatenated, the same way CosyVoice writes pinyin: `[JH] [AE1] [K] [S]` becomes `[JH][AE1][K][S]`.

A `|` between tokens is a word break, and it is emitted as a space. Without it, a multi-word reading is one blob. `agents dot em dee` was spoken as something like "agent's detemd" because every token was glued together. The stored form is:

```text
[EY1] [JH] [AH0] [N] [T] [S] | [D] [AA1] [T] | [EH1] [M] | [D] [IY1]
```

and the model sees `[EY1][JH][AH0][N][T][S] [D][AA1][T] [EH1][M] [D][IY1]`. A one-word entry has no bar.

## Matching

The boundary is a non-word character on each side. A hyphen counts as a boundary, so `pre-mRNA` still corrects `mRNA`.

When two entries overlap, the longer term wins. `scikit-learn` is replaced as a whole and the inner `learn` is not rewritten again.

`SMILES` and `Modal` are `exact`. The words "smiles" and "modal" stay as English.

## Import a previous project

`pronounce.py import` merges a `pronunciations.json` from an earlier video. Three shapes work: a map of term to respelling, a list of entry objects, or an object with an `entries` list (the same shape as `lexicon.json`).

```bash
uv run skills/explainer-video/scripts/pronounce.py import PROJECT/pronunciations.json
```

A missing term is added and the lexicon version increments by one. A verified entry is kept as it is, so a confirmed reading such as pixi → pixie is not overwritten by an older file. An unverified entry keeps a respelling or CMU string it already has. An empty field is filled from the import. When both sides have a respelling and they differ, the current one stays and the command prints a conflict.

## CLI

Run from the repo root. PEP 723 metadata on the script pulls `typer`, `pyyaml`, and `loguru`. Do not install them globally.

```bash
uv run skills/explainer-video/scripts/pronounce.py list
uv run skills/explainer-video/scripts/pronounce.py apply "llamabot writes the test." --target chatterbox
uv run skills/explainer-video/scripts/pronounce.py add TERM --cmu "[...]" --respelling "..." --note "..."
uv run skills/explainer-video/scripts/pronounce.py correct TERM --cmu "[...]" --verified
uv run skills/explainer-video/scripts/pronounce.py resynth PROJECT --term TERM
uv run skills/explainer-video/scripts/pronounce.py resynth PROJECT --beat 2 --text-only
uv run skills/explainer-video/scripts/pronounce.py listen audio/beats/02.prev.wav audio/beats/02.wav
```

`resynth` keeps the previous spoken file as `NN.spoken.prev.txt`. When it synthesizes, it also copies the previous WAV to `NN.prev.wav`. `listen` prints both durations and plays them with `ffplay` when that binary exists.

`resynth` and `synthesize_beat.py` read the voice from the script's `# Voice` section unless `--voice` is set. The voice's `model` field selects the target: `cosyvoice3` or `chatterbox-turbo` / `chatterbox-tts`. `kokoro` raises, because that voice is not a clone and is not wired.

## Pronunciation QA

`pronunciation_qa.py` scores each take. It is a signal, not proof. An ear check is still required: in v1 a phoneme pass on "live" still sounded wrong to Eric.

```bash
uv run --with openai-whisper --with transformers --with torch \
  skills/explainer-video/scripts/pronunciation_qa.py PROJECT --beat 0
```

The voicing loop calls the same checks. Retry is first word, last word (including the last 2–3 words squashed), and whole-line ratio against both the spoken line and the respelled line. Default 4 takes, min ratio 0.9. Forced decoding against `misheard` and the wav2vec2 phoneme check are reported; they do not decide keep or retry. torch, whisper, and transformers are optional and lazy-loaded. Do not `pip install` them globally.

## A/B loop

1. Listen to the beat. Write down the word that broke.
2. `correct` the entry. Say in `--note` what you heard and what you changed.
3. `resynth` that beat only.
4. `listen` the previous WAV and the new WAV.
5. If the new take is right, `correct TERM --verified`.

Chatterbox's generator always runs Whisper after the WAV. There is no skip flag in `generate_narration.py`. One beat is cheap enough. A full script on the Mac is slower for that reason.

`[pause:Xs]` in a spoken line is not a Chatterbox tag. Chatterbox Turbo will try to speak the brackets. Do not put pause markup in the script. Silence between beats is the gap `align_music.py` inserts.

## Native control, and why the lexicon still exists

Fun-CosyVoice3 registers English CMU tokens in `cosyvoice/tokenizer/tokenizer.py` and the README says the model accepts CMU plus Chinese pinyin. That is the native path, and it is what `--target cosyvoice3` emits. The paper's pronunciation-correction table is Chinese-focused, and `example.py` demonstrates pinyin inpainting rather than an English CMU sentence. English CMU on this voice has not been listened to. If a take speaks the brackets as the word "bracket", keep the CMU in the lexicon, write what you heard in the note, and synthesize that video with `eric-mac` so the respelling is what the model receives. Clearing `cmu` would throw away the native path for the next CosyVoice attempt.

Chatterbox has no IPA, phoneme, or SSML input. Resemble issue 550 was still open as of 2026-09. The respelling is the whole control surface. This skill applies the respelling before the Chatterbox helper script sees the line.

Kokoro's Misaki gold lexicon (`pipeline.g2p.lexicon.golds[word] = phonemes`) is the cleanest English phoneme editor in the survey. It is also a preset voice. It stays in `voices.yaml` as a reminder, and synthesis refuses it.
