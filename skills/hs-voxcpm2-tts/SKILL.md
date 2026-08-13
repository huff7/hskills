---
name: hs-voxcpm2-tts
description: "Generate cloned-voice, designed-voice, or ultimate-clone voiceover audio from a Markdown script using VoxCPM2 (OpenBMB, Apache-2.0). Use when a user wants to turn a 口播稿 or script into spoken audio with a specific reference voice (voice cloning), a natural-language voice description (voice design), or highest-fidelity clone (ultimate cloning), especially for short-drama or social-media content. Covers local-weight loading (HF Hub is blocked here), reference-audio prep, script cleaning, per-paragraph generation with resume, and Apple-Silicon MPS."
agent_created: true
---

# VoxCPM2 Voiceover Generator

## Purpose
Turn a cleaned Markdown script into a single spoken-audio file using VoxCPM2, in one of four
official modes — **voice-design** (describe the voice in text), **voice-clone** (match a
reference sample's timbre), **controllable-clone** (clone + style hint), or **ultimate-clone**
(max similarity via reference audio + transcript). Built for the local, offline setup on this
machine where HuggingFace Hub and mirrors are blocked.

Official API surface is documented in `references/api.md`; environment & local-weight details and
pitfalls are in `references/workflow.md`.

## When to use
- "用 voxcpm2 把这篇稿子生成口播" / "clone 我的声音读这段" / "用 lexi 的声音读"
- Generating short-drama narration, platform hook voiceovers, or any 口播 from a script.
- When a reference voice sample (wav/m4a) or a voice description is available.

## Voice modes (pick one)
| Mode | Required args | Notes |
|------|--------------|-------|
| **DESIGN** | `--voice-desc "a warm young woman, clear mezzo-soprano"` | No reference audio. Description is wrapped as `(desc)` prefix per paragraph. |
| **CLONE** | `--ref ref_16k_mono.wav` | Clones timbre of the reference sample. |
| **CONTROLLABLE CLONE** | `--ref ... --style "(slightly faster, cheerful tone)"` | Clone + per-paragraph style hint. |
| **ULTIMATE CLONE** | `--ref ... --prompt-wav ... --prompt-text "<transcript>"` | Highest similarity (ref-continuation). `--prompt-wav` defaults to `--ref`. |

## How to use (procedure)
1. **Prep the reference** (all clone modes): convert to 16k mono wav —
   `ffmpeg -y -i ref.m4a -ar 16000 -ac 1 -c:a pcm_s16le ref_16k_mono.wav`.
   Skip for DESIGN mode. Ideal reference: 10–60 s clean single-speaker low-noise speech.
2. **Prep the script**: Markdown with spoken paragraphs separated by blank lines. Headers,
   blockquotes (`>`), `---` separators, and a `## 清洗注记` stop-header delimit non-spoken
   notes (stripped automatically). Keep quoted terms ("时序AI", `wiki-setup`) as-is — spoken.
3. **Run the generator** with the voxcpm-enabled interpreter:
   ```bash
   /Users/halt_cat/.pyenv/versions/3.12.12/bin/python3 \
     /Users/halt_cat/huff/hskills/skills/hs-voxcpm2-tts/scripts/gen_voxcpm2_voiceover.py \
     --script script.md --ref ref_16k_mono.wav --out voiceover.wav
   ```
   - DESIGN: `--voice-desc "a warm young woman, clear mezzo-soprano"` (omit `--ref`).
   - ULTIMATE: add `--prompt-wav speaker.wav --prompt-text "the transcript of speaker.wav"`.
4. **Verify**: check output WAV duration vs. expected speech length; listen to first/last
   segments for voice stability. Per-paragraph files are kept in `<out>.paras/` for inspection
   and `--resume`.

## Reusable resources
- `scripts/gen_voxcpm2_voiceover.py` — the generator. Key args:
  - `--script`, `--out` (required)
  - `--ref` (clone/controllable/ultimate), `--voice-desc` (design)
  - `--style` (controllable clone hint), `--prompt-wav` + `--prompt-text` (ultimate clone)
  - `--weights` (default local dir), `--device mps|cpu|cuda|auto`
  - `--cfg` (1.8 clone / 2.0 design), `--steps` (30 quality / 12 draft), `--seed` (reproducible)
  - `--gap` (silence between paragraphs, default 0.30 s), `--resume` + `--start` (skip done paragraphs)
- `references/api.md` — full official API: install variants, model versions + repo IDs,
  `from_pretrained` / `generate` (all params) / `generate_streaming`, CLI (`design`/`clone`/
  `batch`/`timestamps`), web demo, server engines, languages, fine-tune.
- `references/workflow.md` — environment, local-weights path, pitfalls (HF blocked, librosa
  cache, MPS dtype, long-form splitting), and output layout conventions.

## Critical rules
- **Always load weights from the local dir** (see references/workflow.md). Never let the loader
  fall back to HF Hub — it is blocked and will fail or hang.
- **Split long scripts per paragraph**; the script does this automatically. Do not generate the
  whole script in one `generate()` call.
- **Run in background** for full episodes (several minutes) and poll the log; use `--resume` if a
  run dies mid-way (each paragraph is saved immediately).
- **Reference audio = 16k mono wav**; `--seed` for reproducible takes; `model.tts_model.sample_rate`
  is the output rate (48 kHz for VoxCPM2).
