# VoxCPM2 Voiceover Workflow (OpenBMB, Apache-2.0)

VoxCPM2 is a tokenizer-free speech-generation model. This skill drives it for
**voice-clone** (reference sample) and **voice-design** (text description) TTS,
producing clean 口播 (voiceover) audio from a Markdown script.

> Full official API surface (install variants, model versions + repo IDs, `from_pretrained` /
> `generate` with all parameters, `generate_streaming`, CLI, web demo, server engines, supported
> languages, fine-tune) is in **`references/api.md`**. This file focuses on the local/offline
> workflow and hard-won pitfalls.

## 1. Environment

- Interpreter: `/Users/halt_cat/.pyenv/versions/3.12.12/bin/python3`
  (voxcpm 2.0.3 + torch installed here; MPS works on Apple Silicon).
- Install once if missing: `pip install voxcpm==2.0.3` (pulls torch, transformers,
  einops, pydantic, tqdm, safetensors; ensure `soundfile` and `librosa` present).
- Run with `optimize=False` (torch.compile is CUDA-only) and `load_denoiser=False`
  (the 16k denoiser is unnecessary for clean synthesis).

## 2. Model weights — LOCAL ONLY

The model is large (~4.6 GB `model.safetensors` + `audiovae.pth` + tokenizer).
**Never rely on HF Hub / hf-mirror** — they are blocked on this machine.

Canonical weights dir (verified present):
```
/Users/halt_cat/huff/social-media/content/d1-20260721/交付物/04_工程文件/day1-douyin/voxcpm_weights
```
A duplicate copy also exists at `/Users/halt_cat/dev/short-drama/.cache_voxcpm/VoxCPM2`.

Load with the local dir directly:
```python
from voxcpm import VoxCPM
model = VoxCPM.from_pretrained(WEIGHTS, load_denoiser=False, device="mps", optimize=False)
```
Output sample rate: `model.tts_model.sample_rate`.

## 3. Reference audio prep (CLONE mode)

- Convert the reference sample to **16k mono WAV** before use (avoids m4a/audioread
  decode issues, though `librosa.load` would resample anyway):
  ```bash
  ffmpeg -y -i ref.m4a -ar 16000 -ac 1 -c:a pcm_s16le ref_16k_mono.wav
  ```
- Ideal reference: 10–60 s of clean, single-speaker, low-noise speech.
- The reference is re-encoded per generation call; keep it in `02_参考音/`.

## 4. Script prep

- Source: a cleaned Markdown script (e.g. `Day5-录音稿-清洗版.md`).
- Strip before generating: `#` headers, `>` blockquotes, `---` separators, and any
  `## 清洗注记` / notes section (not spoken). Remove `**bold**` and `` `code` `` markup,
  decode HTML entities (`&#x20;` → space). Keep quoted phrases ("时序AI", `wiki-setup`)
  as-is — they are spoken.
- Split into paragraphs (blank-line separated). Each paragraph = one `generate()` call.
  This keeps each generation within model limits and bounds memory.

## 5. Generation

```python
wav = model.generate(
    text=paragraph,
    reference_wav_path=REF,        # CLONE mode; omit + use "(desc)" prefix for DESIGN
    cfg_value=1.8,                 # clone: 1.8; design: 2.0
    inference_timesteps=30,        # higher = better fidelity, slower (12 for design drafts)
)
sf.write(out, np.asarray(wav).reshape(-1), sr)
```
- Concatenate paragraph wavs with `np.concatenate` and write once.
- DESIGN mode: prefix each paragraph with `(a young woman, warm mezzo-soprano, ...)`.

## 6. Pitfalls / hard-won lessons

- **HF blocked** → always pass the local weights dir; do not let it fall back to Hub.
- **librosa cache** → set `LIBROSA_CACHE_DIR=/tmp` and `librosa.cache_ = None`, else
  safe-delete hooks may kill the background process.
- **MPS dtype** → auto-adjusts bfloat16→float32 on MPS; that is expected, not an error.
- **Long-form** → split per paragraph; do NOT feed the entire script in one call
  (stop-predictor + max_len can truncate). Per-paragraph also stabilizes voice.
- **Voice drift** → for very long pieces, optionally chain via
  `build_prompt_cache` + `merge_prompt_cache` (ref_continuation mode) for smoother
  cross-segment consistency. Per-paragraph clone mode is usually sufficient.
- **Per-segment time** → ~1–3 s per short paragraph on MPS; a full ~8-min script is
  a few-minute job — run in background and poll the log.

## 7. Output layout (project convention)

```
口播/
  02_参考音/        reference samples (e.g. lexi_0_16k_mono.wav)
  04_成品干音/      final concatenated voiceover (e.g. Day5-voxcpm2-lexi.wav)
                     plus <out>.paras/para_NNN.wav per-paragraph files (for resume/inspect)
  07_工程脚本/      the generation script + run log
```

## 8. Official model variants & languages (summary; full detail in api.md)

- **Versions**: VoxCPM2 = 48 kHz (recommended; used here), VoxCPM1.5 = 44.1 kHz,
  VoxCPM-0.5B = 16 kHz. Repo IDs: `openbmb/VoxCPM2` (HF) / `OpenBMB/VoxCPM2` (ModelScope).
- **Install**: `pip install voxcpm` (Python ≥3.10,<3.13; torch ≥2.5.0). `pip install "voxcpm[timestamps]"`
  adds word/char timestamp export; `pip install modelscope` enables ModelScope weight download.
- **Languages**: 30 languages incl. Chinese; Chinese dialects: 四川话 / 粤语 / 吴语 / 东北话 /
  河南话 / 陕西话 / 山东话 / 天津话 / 闽南话. `generate()` accepts the language natively via the
  input text (no extra flag for most setups).
- **CLI also exists** (`voxcpm design|clone|batch`), but the Python API + local weights is the
  offline-safe path used by this skill's script.
