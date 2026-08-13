#!/usr/bin/env python3
"""
VoxCPM2 voiceover generator (OpenBMB, Apache-2.0).

Modes (official API, see references/api.md):
  * CLONE mode          : --ref <wav>
                          synthesizes in the cloned voice of the reference sample.
  * DESIGN mode         : --voice-desc "<text>"
                          no reference; voice described in natural language, wrapped as
                          "(desc)" prefix on each paragraph.
  * CONTROLLABLE CLONE  : --ref <wav> --style "(slightly faster, cheerful tone)"
                          clone voice + per-paragraph style hint.
  * ULTIMATE CLONE      : --ref <wav> --prompt-wav <wav> --prompt-text "<transcript>"
                          highest similarity (ref-continuation). prompt_wav defaults to --ref.

Reads a Markdown script, strips headers/notes/markdown to plain spoken paragraphs,
generates each paragraph (per-paragraph save + --resume for robustness), concatenates,
and writes one WAV.

Run with the environment that has `voxcpm` installed:
    /Users/halt_cat/.pyenv/versions/3.12.12/bin/python3 gen_voxcpm2_voiceover.py \
        --script script.md --ref reference.wav --out voiceover.wav

Key constraints (see references/workflow.md):
  * Weights MUST be a local dir (HF Hub / mirrors are blocked on this machine).
  * Reference wav: convert to 16k mono wav first (avoids m4a decode issues).
  * Long scripts: split per paragraph (this script does it automatically).
"""
import os
import re
import html
import sys
import time
import argparse
import traceback

import numpy as np
import soundfile as sf

# Disable librosa disk cache (safe-delete hooks may kill background jobs otherwise).
try:
    import librosa
    if hasattr(librosa, "cache_"):
        librosa.cache_ = None
    os.environ.setdefault("LIBROSA_CACHE_DIR", "/tmp")
except Exception:
    pass

from voxcpm import VoxCPM

DEFAULT_WEIGHTS = "/Users/halt_cat/huff/social-media/content/d1-20260721/交付物/04_工程文件/day1-douyin/voxcpm_weights"


def extract_paragraphs(md_path, stop_header="## 清洗注记"):
    paras = []
    cur = []
    stop = False
    with open(md_path, encoding="utf-8") as f:
        for line in f:
            s = line.rstrip("\n")
            if s.startswith(stop_header):
                stop = True
            if stop:
                continue
            if s.startswith("#"):
                if cur:
                    paras.append("\n".join(cur)); cur = []
                continue
            if s.startswith(">"):
                if cur:
                    paras.append("\n".join(cur)); cur = []
                continue
            if re.match(r"^\s*---\s*$", s):
                if cur:
                    paras.append("\n".join(cur)); cur = []
                continue
            if s.strip() == "":
                if cur:
                    paras.append("\n".join(cur)); cur = []
                continue
            t = re.sub(r"^\s*[-*]\s+", "", s)
            cur.append(t)
    if cur:
        paras.append("\n".join(cur))

    cleaned = []
    for p in paras:
        p = html.unescape(p)
        p = p.replace("&#x20;", " ")
        p = re.sub(r"\*\*(.*?)\*\*", r"\1", p)
        p = re.sub(r"`([^`]*)`", r"\1", p)
        p = re.sub(r"\s+", " ", p).strip()
        if p:
            cleaned.append(p)
    return cleaned


def load_model(weights, device):
    last_err = None
    devs = [device] if device != "auto" else ("mps", "cpu")
    for dev in devs:
        try:
            print(f"[load] device={dev}", flush=True)
            t0 = time.time()
            m = VoxCPM.from_pretrained(weights, load_denoiser=False, device=dev, optimize=False)
            print(f"[load] ready in {time.time()-t0:.1f}s", flush=True)
            return m
        except Exception as e:
            last_err = e
            print(f"[load] device={dev} failed: {e}", flush=True)
            if dev == "cpu":
                traceback.print_exc()
                raise
    raise RuntimeError(f"model load failed: {last_err}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--script", required=True, help="Markdown script (spoken content)")
    ap.add_argument("--out", required=True, help="Output WAV path")
    ap.add_argument("--ref", help="Reference wav for CLONE / CONTROLLABLE / ULTIMATE mode")
    ap.add_argument("--voice-desc", help="Natural-language voice description for DESIGN mode")
    ap.add_argument("--style", help="Per-paragraph style hint, e.g. '(slightly faster, cheerful)' (controllable clone)")
    ap.add_argument("--prompt-wav", help="Ultimate-clone prompt audio (defaults to --ref)")
    ap.add_argument("--prompt-text", help="Transcript of --prompt-wav (required for ultimate clone)")
    ap.add_argument("--weights", default=DEFAULT_WEIGHTS, help="Local VoxCPM2 weights dir")
    ap.add_argument("--device", default="auto", help="mps / cpu / cuda / auto")
    ap.add_argument("--cfg", type=float, default=1.8, help="Classifier-free guidance (clone 1.8 / design 2.0)")
    ap.add_argument("--steps", type=int, default=30, help="Diffusion timesteps (quality 30 / draft 12)")
    ap.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    ap.add_argument("--gap", type=float, default=0.30, help="Silence gap (s) between paragraphs")
    ap.add_argument("--resume", action="store_true", help="Skip paragraphs already saved in <out>.paras/")
    ap.add_argument("--start", type=int, default=1, help="1-based start paragraph (with --resume)")
    args = ap.parse_args()

    assert os.path.exists(args.weights), f"weights missing: {args.weights}"
    mode = None
    if args.voice_desc:
        mode = "DESIGN"
    elif args.ref:
        mode = "ULTIMATE" if (args.prompt_wav or args.prompt_text) else ("CONTROLLABLE" if args.style else "CLONE")
    else:
        raise SystemExit("Provide --ref (clone) or --voice-desc (design).")

    if args.ref:
        assert os.path.exists(args.ref), f"reference missing: {args.ref}"
    if mode == "ULTIMATE":
        pw = args.prompt_wav or args.ref
        assert os.path.exists(pw), f"prompt_wav missing: {pw}"
        assert args.prompt_text, "--prompt-text is required for ultimate clone"

    paras = extract_paragraphs(args.script)
    print(f"[parse] {len(paras)} spoken paragraphs | mode={mode}", flush=True)

    model = load_model(args.weights, args.device)
    sr = model.tts_model.sample_rate
    print(f"[info] sample_rate={sr}", flush=True)

    import torch
    out_dir = os.path.abspath(args.out)
    para_dir = out_dir + ".paras"
    os.makedirs(os.path.dirname(out_dir), exist_ok=True)
    os.makedirs(para_dir, exist_ok=True)

    gen_kwargs = dict(cfg_value=args.cfg, inference_timesteps=args.steps)
    if args.seed is not None:
        gen_kwargs["seed"] = args.seed

    done = 0
    skipped = 0
    for i, p in enumerate(paras, 1):
        ppath = os.path.join(para_dir, f"para_{i:03d}.wav")
        if args.resume and os.path.exists(ppath) and os.path.getsize(ppath) > 1000 and i >= args.start:
            skipped += 1
            continue
        if args.start and i < args.start:
            continue

        # build text per mode
        if mode == "DESIGN":
            text = f"({args.voice_desc}){p}"
        elif mode == "CONTROLLABLE":
            text = f"({args.style}){p}" if args.style else p
        else:
            text = p

        print(f"[{i}/{len(paras)}] {p[:50]}...", flush=True)
        t0 = time.time()
        try:
            kw = dict(gen_kwargs)
            kw["text"] = text
            if mode in ("CLONE", "CONTROLLABLE", "ULTIMATE"):
                kw["reference_wav_path"] = args.ref
            if mode == "ULTIMATE":
                kw["prompt_wav_path"] = pw
                kw["prompt_text"] = args.prompt_text
            wav = model.generate(**kw)
            if hasattr(wav, "numpy"):
                wav = wav.numpy()
            wav = np.asarray(wav).reshape(-1).astype(np.float32)
            sf.write(ppath, wav, sr)
            print(f"    -> {len(wav)/sr:.2f}s in {time.time()-t0:.1f}s  [{ppath}]", flush=True)
            done += 1
        except Exception as e:
            print(f"    !! paragraph {i} FAILED: {e}", flush=True)
            traceback.print_exc()
            print("[stop] aborting; re-run with --resume to continue", flush=True)
            return
        finally:
            try:
                if torch.backends.mps.is_available():
                    torch.mps.empty_cache()
            except Exception:
                pass
            del wav

    print(f"\n[concat] done={done} skipped={skipped}", flush=True)
    files = sorted(
        os.path.join(para_dir, f) for f in os.listdir(para_dir)
        if f.startswith("para_") and f.endswith(".wav")
    )
    gap = np.zeros(int(args.gap * sr), dtype=np.float32)
    parts = []
    for fp in files:
        d, _ = sf.read(fp, dtype="float32")
        parts.append(d)
        parts.append(gap)
    full = np.concatenate(parts)
    sf.write(out_dir, full, sr)
    print(f"[done] {out_dir}\n  paragraphs={len(files)} total={len(full)/sr:.2f}s sr={sr}", flush=True)


if __name__ == "__main__":
    main()
