# Open-weight TTS for a cloned narrator

Survey date: 2026-11-20. Sources are the project README, the model card, or the paper linked in each section. Hub license tags below were read around 2026-11-19 via the AI Wiki roundup at <https://aiwiki.ai/wiki/best_open_weight_tts_models> and then checked against the primary repo where a decision depends on them. Gated license files that require a click-through were not opened. No model in this table was loaded or listened to on the machine that wrote this skill. That machine is x86_64 with no NVIDIA GPU.

Hardware column notes: an NVIDIA GB10 (DGX Spark, aarch64, CUDA, on the order of 121 GB unified memory) and a Mac. That machine is a TTS target here, not a chat-model server. Stock vLLM on the GB10 needs a custom sm_121 build, so this pipeline does not use CosyVoice's optional vLLM path.

## Recommendation

**Primary: Fun-CosyVoice3-0.5B-2512.** It is the candidate that is Apache-2.0 on the model card and the GitHub license, clones from a short reference clip, and registers English CMU tokens for pronunciation inpainting. Voice id `eric` calls it.

**Fallback: Chatterbox Turbo** (`chatterbox-tts` 0.1.7). MIT, already wired for Mac MPS through an optional sibling skill `chatterbox-voice-clone` (set `CHATTERBOX_SCRIPT` if that skill is not installed next to this one). It has no phoneme API, so the lexicon sends it a respelling. Voice id `eric-mac`.

**Phoneme reference, not a narrator: Kokoro.** Apache-2.0, no cloning, and a real English gold lexicon (Misaki). It stays in `voices.yaml` so the slot is visible, and synthesis refuses it. Picking it would narrate the Short in a preset voice.

**Clone-quality alternative, not wired: Qwen3-TTS.** Apache-2.0, clones from about 3 seconds of audio plus a transcript. No documented phoneme API, so it would use the respelling. It is the model to try if CosyVoice's English speaker match is weak once someone listens. Two heavy cloners were not both wired before either one had been heard.

Use the primary on the GB10. Use the fallback on the Mac, or when CUDA is missing. The synthesizer exits in that case. It does not silently swap models.

## How to read the scores

| Column | Meaning here |
| --- | --- |
| Clone | Whether a 10 to 30 second reference is the documented setup. "Short clip" means the card's own number, which is sometimes under 10 seconds. |
| Commercial | Whether the weights' license allows a YouTube Short Eric publishes. Code license and weights license are listed separately when they differ. |
| Phoneme | IPA, CMU, pinyin tokens, SSML, or a user lexicon the model reads at inference. A text respelling we invent does not count as native support. |
| Jargon | Whether that control can force pyjanitor, mRNA, LNP, GxP, SMILES. "Untested" means the mechanism exists and nobody has listened with this lexicon. |
| Speed | What the card or repo claims. Not a measurement from this repo. |
| Hardware | GPU assumption, plus the GB10 and Mac notes that follow from the card. |

## Summary

| Model | Clone | Commercial weights | Native phoneme control | Wired |
| --- | --- | --- | --- | --- |
| Fun-CosyVoice3-0.5B | Zero-shot clip | Apache-2.0, with the README disclaimer below | CMU and pinyin tokens | Primary |
| Chatterbox Turbo | Zero-shot clip | MIT | None | Mac fallback |
| Kokoro 82M | No | Apache-2.0 | Misaki gold lexicon | Refused on purpose |
| Qwen3-TTS | About 3 s plus transcript | Apache-2.0 | Not documented | No |
| F5-TTS | Zero-shot clip | CC-BY-NC-4.0 weights | Not the control we need | No |
| XTTS-v2 | About 6 s | Coqui Public Model License, non-commercial | No user lexicon found | No |
| IndexTTS2 / 2.5 | Zero-shot | Bilibili grant above a size threshold | Not the reason to pick it | No |
| Orpheus | Voice tags, gated | Apache-2.0 plus Llama 3.2 | Not confirmed | No |
| Sesame CSM-1B | Conversational context | Apache-2.0, gated, plus Llama | Context audio, not a lexicon | No |
| Dia / Dia2 | 5 to 10 s | Apache-2.0 | Dialogue tags, not phonemes | No |
| Spark-TTS | Zero-shot | CC-BY-NC-SA-4.0 weights | Not confirmed as a user lexicon | No |
| Fish S1-mini | Zero-shot | CC-BY-NC-SA | Phoneme tags | No, license |
| Fish Drama 3 | Zero-shot | Revenue cap and no hosted service | Phoneme tags | No, license |
| Zonos-v0.1 | 5 to 30 s | Apache-2.0 | User lexicon not confirmed | No |
| Higgs Audio v2 | Zero-shot | Community license, user cap | Not confirmed | No |
| VibeVoice | Long-form | Card says research use | Not a narrator lexicon | No |
| Kyutai TTS 1.6B | Precomputed embeddings | CC-BY 4.0 | Not a raw-clip cloner | No |
| MaskGCT | Research cloning | Confirm the checkpoint card | Not confirmed | No |
| CosyVoice 2 | Zero-shot | Apache-2.0 | No pronunciation inpainting | No |

## Primary: Fun-CosyVoice3-0.5B-2512

- Card: <https://huggingface.co/FunAudioLLM/Fun-CosyVoice3-0.5B-2512>
- Code: <https://github.com/FunAudioLLM/CosyVoice>
- Paper: <https://arxiv.org/abs/2505.17589> (arXiv:2505.17589, section 2.3 covers pronunciation inpainting)
- Accessed 2026-11-20

Zero-shot cloning uses a reference clip. When the transcript of that clip is known, `inference_zero_shot` takes the text, the prompt `You are a helpful assistant.<|endofprompt|>` plus the transcript, and the wav path. When the transcript is empty, `inference_cross_lingual` takes the prompt plus the line, and the wav. Voice `eric` follows that split. `reference_transcript` in `voices.yaml` is empty until someone writes down the words in `~/voice/eric-voice-ref.m4a`.

The tokenizer registers CMU tokens from `[AA]` through `[ZH]`, including stress digits. The README describes CMU plus Chinese pinyin. `example.py` shows Chinese pinyin inpainting (`[j][ǐ]`) and the two inference methods. It does not show an English sentence full of CMU tokens. The paper's correction-rate table is the evidence that inpainting works for the languages they measured. English jargon through those tokens is the reason this model is primary, and it is untested by ear.

License: Apache-2.0 on the model card and on the GitHub license. The README also says the page content is for academic demonstration of technical capabilities. That sentence is a disclaimer about the README's examples. It is not a separate weights license that this survey found. Ship the Short under the Apache-2.0 grant, and keep the disclaimer in mind if a later card revision adds a non-commercial file.

Speed: the card describes a 0.5B model with streaming. Treat any tokens-per-second number you have not measured as a claim.

Hardware: CUDA. Mac MPS is not a documented target. Voice `eric` refuses to run when `torch.cuda.is_available()` is false. Do not enable the optional vLLM path. Stock vLLM on the GB10 wants a custom sm_121 build.

The synthesizer adds the CosyVoice repo and `third_party/Matcha-TTS` to `sys.path`, then imports `AutoModel`. Omit `--beat` to synthesize every beat in one process. The weights load once and stay cached for that process. `--dry-run` never imports torch. `torch` and `torchaudio` are in the script's dependency header. CosyVoice itself is the git clone named by `cosyvoice_repo`, not a PyPI package.

### GB10 (aarch64) install

CosyVoice's `requirements.txt` (read 2026-11-20) starts with `--extra-index-url https://download.pytorch.org/whl/cu121` and pins `torch==2.3.1` and `torchaudio==2.3.1`. Those cu121 wheels are x86_64. They do not install on the GB10. The same file pins `onnxruntime-gpu`, `tensorrt-cu12`, and `deepspeed` for Linux. The README's `ttsfrd` wheel is `linux_x86_64` only. Do not run `pip install -r requirements.txt` on aarch64.

Working path, not executed on the machine that wrote this note:

```bash
git clone --recursive https://github.com/FunAudioLLM/CosyVoice.git
cd CosyVoice
uv pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

Install the rest of `requirements.txt` after removing the cu121 index line and the packages that have no aarch64 wheel: `torch`, `torchaudio`, `onnxruntime-gpu`, `tensorrt-cu12`, `tensorrt-cu12-bindings`, `tensorrt-cu12-libs`, and `deepspeed`. Skip `ttsfrd`. `wetext==0.0.4` can stay. Point `cosyvoice_repo` in `voices.yaml` at that clone.

PyTorch may warn that the Spark's capability (sm_121) is above the wheel's stated maximum (sm_120). That warning is common on this machine. This note does not claim the kernels were re-checked here.

### Known quirks from the GB10 run

- CosyVoice's English cleanup, `spell_out_number` in `cosyvoice/utils/frontend_utils.py`, spells every digit. The stress digit in `[IH1]` becomes the word "one" with no space, so the model sees `[IHone]` and the audio is garbage. `synthesize_beat.py` patches that function, and the copy the frontend imported, so a sound code is copied through unchanged. Ordinary numbers such as `2` are still spelled out.
- The first GB10 render dropped the first word of a line until the voice reference clip had about 0.8 seconds of trailing silence. `synthesize_beat.py` writes that padded WAV beside the clip (`name.padded.wav`) and passes it to CosyVoice. The original clip is unchanged. Set `COSYVOICE_REFERENCE_PAD=0` to skip it. Never inject a spoken filler such as `Hmm.`; the model will say it out loud. `COSYVOICE_LEAD_IN` prefixes only when it is set to a non-empty string on purpose. `audio/beats/NN.spoken.txt` stays the lexicon line.
- CosyVoice may ask modelscope to download wetext frontend resources. That download can return 403. English still runs: the English path is inflect, which is the cleanup this skill wraps. Installing the `wetext` package is fine. Do not treat the 403 as a failed voice.
- A root-owned `~/.cache/huggingface` can hang the first synthesis. Set `HF_HOME` to a directory you can write. When `HF_HOME` is unset and the default cache is not writable, the synthesizer sets `HF_HOME` to `./.cache/huggingface` and says so. It does not change ownership of the root cache.

## Fallback: Chatterbox Turbo

- Code: <https://github.com/resemble-ai/chatterbox>
- Package: <https://pypi.org/project/chatterbox-tts/> (0.1.7, released 2026-03-26)
- Phoneme request: <https://github.com/resemble-ai/chatterbox/issues/550> (open as of 2026-09)
- Accessed 2026-11-20

MIT license. Zero-shot from a reference clip. The English Turbo model accepts paralinguistic tags. It does not accept IPA, phonemes, or SSML. A `[pause:Xs]` string is spoken as words. This pipeline never emits that string. Silence lives in the timeline gap.

The repo's own status, as of August 2026, is that the project is retired and unmaintained. It remains the fallback because there is a working Mac path: an optional sibling `chatterbox-voice-clone` script (`generate_narration.py`) with `--model turbo` and `--device mps`, or the same script via `CHATTERBOX_SCRIPT`. This skill shells out to that script and copies `narration.wav` onto `audio/beats/NN.wav`. The MPS and Perth patches stay in that helper. Do not copy them here.

The generator always runs Whisper after the WAV. One-beat A/B pays that cost. There is no skip flag.

The respelling pass in this skill runs first, before the helper script sees the line.

Commercial use: MIT allows it. An unmaintained model can still be the wrong voice. If a 2026 listen sounds worse than CosyVoice, keep it as the Mac emergency path.

## Kokoro

- Code: <https://github.com/hexgrad/kokoro>
- G2P: <https://github.com/hexgrad/misaki>
- Lexicon notes: issues 156 and 42 in the Kokoro repo
- Accessed 2026-11-20

Apache-2.0. 82M parameters, fast on CPU and on a Mac. Voices are presets (`af_heart` and the rest). There is no reference-audio cloner. Misaki's gold lexicon is the right tool when the goal is "say this word with these phonemes" and the speaker can be a preset. That is not this skill's goal. `target_for("kokoro")` raises `VoiceError`.

## Qwen3-TTS

- Code: <https://github.com/QwenLM/Qwen3-TTS>
- Paper: <https://arxiv.org/abs/2601.15621>
- License file in that repo is Apache-2.0
- Accessed 2026-11-20

January 2026 release. Zero-shot clone from a short clip (the card's figure is about 3 seconds) plus the reference transcript, with an `x_vector_only_mode` when you have no transcript. No phoneme or IPA API showed up in the README during this pass. Jargon would go through the respelling field. Speed and quality claims are the paper's. Hardware is a CUDA GPU. Not wired, for the reason in the recommendation.

## Models that fail the commercial or the control bar

**F5-TTS.** Code is MIT. Weights are CC-BY-NC-4.0 because of the Emilia training data. A YouTube Short is commercial enough that NC weights stay out. Cloning quality from a short clip is not the question that decides it.

**XTTS-v2 (Coqui).** Coqui Public Model License. Non-commercial, and the restriction covers outputs of the model. About a 6 second clip. Leave it out even as a private draft if the draft might be published.

**IndexTTS2 and IndexTTS 2.5 (Bilibili).** Strong English speaker similarity on CosyVoice's own comparison table, which is a reason to listen later. The Bilibili model-use license asks for a separate grant once monthly active users pass 100 million or annual revenue passes RMB 1 billion. Eric is under that line today. The license is still a grant you must re-read before a product, and the model has no pronunciation-editing story that beats CosyVoice's CMU tokens. Not wired.

**Orpheus.** Apache-2.0 and gated. The Llama 3.2 backbone carries that model's license as well. Emotion tags are the control surface the README emphasizes. A user phoneme lexicon was not confirmed in this pass.

**Sesame CSM-1B.** Apache-2.0, gated, Llama license on the backbone. It is a conversational model: it wants dialogue context, not a 10 to 30 second narrator prompt plus a fresh line. Poor fit for one-voice beats.

**Dia and Dia2.** Apache-2.0. A 5 to 10 second reference. The script format is two-speaker tags (`[S1]`, `[S2]`) and nonverbal tags. No phoneme API found. Useful for a dialogue Short, which this pipeline is not.

**Spark-TTS.** Code Apache-2.0. Weights moved to CC-BY-NC-SA-4.0 on account of the training data. NC-SA weights are out for a published Short.

**Fish Speech / OpenAudio S1-mini.** Weights CC-BY-NC-SA. The interesting technical detail is the phoneme tag, documented at <https://docs.fish.audio/developer-guide/core-features/fine-grained-control>: a span wrapped so the model reads CMU or pinyin inside it. That is a real alternative to CosyVoice's tokenizer. The NC license is why it is not the primary.

**Fish Audio Drama 3.** Fish Audio Community License. Commercial use is allowed under a revenue cap (the figure published with the license is $500k annual revenue) and the license forbids offering it as a hosted service. A phoneme path plus a revenue cap is still a worse default than Apache-2.0. Not wired.

**Zonos-v0.1 (Zyphra).** Apache-2.0. The card and the wiki citing Zyphra describe a 5 to 30 second, or 10 to 30 second, reference. A user lexicon was not confirmed in this pass. ZONOS3-Mini is a later mixture-of-experts model. Re-read that card before treating v0.1's notes as current.

**Higgs Audio v2 / TTS 2 (Boson).** Community license. The published threshold is an expanded license above 100k annual active users. Higgs TTS 3 is non-commercial with a separate creator grant. Under the cap is not the same as Apache-2.0, and no phoneme lexicon was confirmed. Not wired.

**VibeVoice.** The Hub tag says MIT. The model card says research-purpose only. Do not use it for a YouTube narration. The tag and the card disagree, and the card is the restriction you can read without a lawyer.

**Kyutai TTS 1.6B.** CC-BY 4.0. Cloning is from precomputed speaker embeddings, not from an arbitrary wav you drop in a folder. Pocket TTS is the small CPU cloner and it is gated. Neither is the 10 to 30 second clip workflow this skill wants.

**MaskGCT.** Treat it as research. Amphion checkpoints in this family have been CC-BY-NC. Open the checkpoint card and read the license file before any experiment. Not wired.

**CosyVoice 2.** Apache-2.0 and a capable cloner. Pronunciation inpainting is a v3 feature. Prefer v3 so the CMU path exists.

## What a later listen should decide

Run these on the GB10, in this order, and write the result into the lexicon note or a project log. Do not update this file's recommendation from a single word.

1. Voice `eric`, ten seconds of ordinary English, no lexicon tokens. Judge whether the clone is recognizably Eric.
2. The same line with `mRNA`, `LNP`, `pyjanitor`, and `SMILES` left in normal spelling.
3. The same line after `pronounce.py apply --target cosyvoice3`. Judge whether the CMU tokens are spoken as the word or as the names of the letters.
4. If step 3 fails, the same respelling through `eric-mac` on the Mac.
5. Only if step 1 fails, a Qwen3-TTS clone of the same clip, still through the respelling, as an experiment outside this skill.

Until those WAVs exist, the recommendation is a license-and-mechanism choice, not a listening test.
